import cv2
import numpy as np

def multiscale_retinex(L):
    scales = [31, 101, 301]
    retinex = np.zeros_like(L, dtype=np.float32)
    for k in scales:
        blur = cv2.GaussianBlur(L, (k, k), 0)
        retinex += np.log(L + 1) - np.log(blur + 1)
    retinex /= len(scales)
    retinex = cv2.normalize(retinex, None, 0, 255, cv2.NORM_MINMAX)
    return retinex
 
# Adaptive Shadow Mask
def compute_shadow_mask_adaptive(L, S, sensitivity=1.0, mask_blur=21):
    shadow_cond = (L < 0.5 * sensitivity) & (S < 0.5)
    mask = shadow_cond.astype(np.float32)
    mask_blur = mask_blur if mask_blur % 2 == 1 else mask_blur + 1
    mask = cv2.GaussianBlur(mask, (mask_blur, mask_blur), 0)
    return mask
 
#  Shadow Removal 
def remove_shadows_adaptive_v3(L, A, B, L_retinex, strength=0.9, mask=None, mask_blur=31):
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    shadow_mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    shadow_mask = cv2.morphologyEx(shadow_mask, cv2.MORPH_OPEN, kernel)
    shadow_mask = cv2.dilate(shadow_mask, kernel, iterations=1)
    shadow_mask = cv2.GaussianBlur(shadow_mask, (mask_blur, mask_blur), 0)
    mask_smooth = np.power(shadow_mask, 1.5)
 
    L_final = (1 - strength * mask_smooth) * L + (strength * mask_smooth) * L_retinex
    L_final = np.clip(L_final, 0, 255)
 
    mask_inv = 1 - mask_smooth
    A_bg = np.sum(A * mask_inv) / (np.sum(mask_inv) + 1e-6)
    B_bg = np.sum(B * mask_inv) / (np.sum(mask_inv) + 1e-6)
 
    A_final = (1 - strength * mask_smooth) * A + (strength * mask_smooth) * A_bg
    B_final = (1 - strength * mask_smooth) * B + (strength * mask_smooth) * B_bg
 
    return L_final, A_final, B_final
 
def nothing(x):
    pass

def detect_red_ball_on_frame(frame, min_radius=10, max_radius=400, param1=50, param2=30, min_dist=20):
    """
    Detects only red circular or circle-like objects in a video frame.
    Args:
        frame (numpy.ndarray): The video frame (BGR image).
        min_radius (int): Minimum radius of detected circles.
        max_radius (int): Maximum radius of detected circles.
        param1 (int): Upper threshold for the internal Canny edge detector.
        param2 (int): Threshold for center detection.
        min_dist (int): Minimum distance between detected circle centers.
    Returns:
        tuple: (circles_list, hsv, mask, gray, gray_blurred)
    """
    if frame is None or frame.size == 0:
        print("Error: Empty frame.")
        return None, None, None, None, None

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Define the lower and upper bounds for red color in HSV
    lower_red1 = np.array([6, 90, 130])
    upper_red1 = np.array([40, 255, 255])
    lower_red2 = np.array([160, 100, 100])
    upper_red2 = np.array([180, 255, 255])

    # Create masks for the two ranges of red
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = cv2.bitwise_or(mask1, mask2)

    # Apply morphological operations to reduce noise
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)

    # Apply the mask to the grayscale image
    gray = cv2.bitwise_and(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), mask=mask)
    gray_blurred = cv2.GaussianBlur(gray, (9, 9), 2)

    circles = cv2.HoughCircles(
        gray_blurred,
        cv2.HOUGH_GRADIENT,
        1,
        min_dist,
        param1=param1,
        param2=param2,
        minRadius=min_radius,
        maxRadius=max_radius,
    )

    if circles is not None:
        circles = np.uint16(np.around(circles[0, :]))
        return circles.tolist(), hsv, mask, gray, gray_blurred
    else:
        return None, hsv, mask, gray, gray_blurred

def draw_circles_on_frame(frame, circles):
    """Draws circles on the frame.
    Args:
        frame (numpy.ndarray): The video frame (BGR image).
        circles (list): List of circles (x, y, radius).
    """
    if frame is None or frame.size == 0:
        print("Error: Empty frame.")
        return

    if circles is not None:
        for x, y, r in circles:
            cv2.circle(frame, (x, y), r, (0, 255, 0), 2)
            cv2.circle(frame, (x, y), 2, (0, 0, 255), 3)  # Draw center
    cv2.imshow("Detected Red Ball", frame)

# Se connecter à la caméra
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()
    
if __name__ == "__main__":
    while True:
        ret,img = cap.read()
        if img is None:
            raise IOError("Image not found")
     
        scale = 0.5
        img_preview = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
     
        lab = cv2.cvtColor(img_preview, cv2.COLOR_BGR2LAB).astype(np.float32)
        L, A, B = cv2.split(lab)
        L_retinex = multiscale_retinex(L)
     
        hsv = cv2.cvtColor(img_preview, cv2.COLOR_BGR2HSV).astype(np.float32)
        S = hsv[:, :, 1] / 255.0
     
        cv2.namedWindow("Shadow Removal", cv2.WINDOW_NORMAL)
        cv2.createTrackbar("Strength", "Shadow Removal", 70, 200, nothing)
        cv2.createTrackbar("Sensitivity", "Shadow Removal", 100, 200, nothing)
        cv2.createTrackbar("MaskBlur", "Shadow Removal", 50, 101, nothing)
     
       
        strength = cv2.getTrackbarPos("Strength", "Shadow Removal") / 100.0
        sensitivity = cv2.getTrackbarPos("Sensitivity", "Shadow Removal") / 100.0
        mask_blur = cv2.getTrackbarPos("MaskBlur", "Shadow Removal")
        mask_blur = max(3, mask_blur)
        mask_blur = mask_blur if mask_blur % 2 == 1 else mask_blur + 1

        mask = compute_shadow_mask_adaptive(L / 255.0, S, sensitivity, mask_blur)

        L_final, A_final, B_final = remove_shadows_adaptive_v3(
            L, A, B, L_retinex, strength, mask, mask_blur
        )

        lab_out = cv2.merge([L_final, A_final, B_final]).astype(np.uint8)
        result = cv2.cvtColor(lab_out, cv2.COLOR_LAB2BGR)

        #  BUILD RGB VIEW 
        orig_rgb = cv2.cvtColor(img_preview, cv2.COLOR_BGR2RGB)
        mask_rgb = cv2.cvtColor((mask * 255).astype(np.uint8), cv2.COLOR_GRAY2RGB)
        result_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)

        combined_rgb = np.hstack([orig_rgb, mask_rgb, result_rgb])

        # Convert back so OpenCV shows correct colors
        combined_bgr = cv2.cvtColor(combined_rgb, cv2.COLOR_RGB2BGR)

        cv2.imshow("Shadow Removal", combined_bgr)
        
            # ret will return a true value if the frame exists otherwise False
        into_hsv =cv2.cvtColor(combined_bgr,cv2.COLOR_BGR2HSV)
        # changing the color format from BGr to HSV 
        # This will be used to create the mask
        L_limit=np.array([6,90,100]) # setting the blue lower limit
        U_limit=np.array([60,255,255]) # setting the blue upper limit
           

        b_mask=cv2.inRange(into_hsv,L_limit,U_limit)
        # creating the mask using inRange() function
        # this will produce an image where the color of the objects
        # falling in the range will turn white and rest will be black
        blue=cv2.bitwise_and(combined_bgr,combined_bgr,mask=b_mask)
        # this will give the color to mask.
        #cv2.imshow('Original',combined_bgr) # to display the original frame
        cv2.imshow('Blue Detector',blue) # to display the blue object output
        
        key = cv2.waitKey(30) & 0xFF
        
        
        
        
            

        # Prendre une image de la caméra
        ret, frame = cap.read()

            # Trouver une balle rouge sur l'image
        circles, hsv, mask, gray, gray_blurred = detect_red_ball_on_frame(combined_bgr)

            # Mettre un cercle vert autour de la ball trouvée pour debug
        draw_circles_on_frame(combined_bgr.copy(), circles)

            # Montrer d'autres les étapes de la detection de la balle rouge pour debug
        if hsv is not None:
            cv2.imshow("HSV", hsv)
        if gray is not None:
            cv2.imshow("Gray", gray)
        #    if gray_blurred is not None:
        #        cv2.imshow("Gray Blurred", gray_blurred)
        #    if mask is not None:
        #        cv2.imshow("Mask", mask)

            # Si le script est lancé en ligne de commande, on peut quitter avec 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
                break


 

cap.release()
cv2.destroyAllWindows()
