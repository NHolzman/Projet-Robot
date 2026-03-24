import cv2 as cv
import numpy as np

cap = cv.VideoCapture(0)

# Retinex (compute once) 
def multiscale_retinex(L):
    scales = [31, 101, 301]
    retinex = np.zeros_like(L, dtype=np.float32)
    for k in scales:
        blur = cv.GaussianBlur(L, (k, k), 0)
        retinex += np.log(L + 1) - np.log(blur + 1)
    retinex /= len(scales)
    retinex = cv.normalize(retinex, None, 0, 255, cv.NORM_MINMAX)
    return retinex
 
# Adaptive Shadow Mask
def compute_shadow_mask_adaptive(L, S, sensitivity=1.0, mask_blur=21):
    shadow_cond = (L < 0.5 * sensitivity) & (S < 0.5)
    mask = shadow_cond.astype(np.float32)
    mask_blur = mask_blur if mask_blur % 2 == 1 else mask_blur + 1
    mask = cv.GaussianBlur(mask, (mask_blur, mask_blur), 0)
    return mask
 
#  Shadow Removal 
def remove_shadows_adaptive_v3(L, A, B, L_retinex, strength=0.9, mask=None, mask_blur=31):
    kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, (7, 7))
    shadow_mask = cv.morphologyEx(mask, cv.MORPH_CLOSE, kernel)
    shadow_mask = cv.morphologyEx(shadow_mask, cv.MORPH_OPEN, kernel)
    shadow_mask = cv.dilate(shadow_mask, kernel, iterations=1)
    shadow_mask = cv.GaussianBlur(shadow_mask, (mask_blur, mask_blur), 0)
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
 
#  Main

if __name__ == "__main__":
    while True:
        ret,img = cap.read()
        if img is None:
            raise IOError("Image not found")
     
        scale = 0.5
        img_preview = cv.resize(img, None, fx=scale, fy=scale, interpolation=cv.INTER_AREA)
     
        lab = cv.cvtColor(img_preview, cv.COLOR_BGR2LAB).astype(np.float32)
        L, A, B = cv.split(lab)
        L_retinex = multiscale_retinex(L)
     
        hsv = cv.cvtColor(img_preview, cv.COLOR_BGR2HSV).astype(np.float32)
        S = hsv[:, :, 1] / 255.0
     
        cv.namedWindow("Shadow Removal", cv.WINDOW_NORMAL)
        cv.createTrackbar("Strength", "Shadow Removal", 80, 200, nothing)
        cv.createTrackbar("Sensitivity", "Shadow Removal", 115, 200, nothing)
        cv.createTrackbar("MaskBlur", "Shadow Removal", 50, 101, nothing)
     
       
        strength = cv.getTrackbarPos("Strength", "Shadow Removal") / 100.0
        sensitivity = cv.getTrackbarPos("Sensitivity", "Shadow Removal") / 100.0
        mask_blur = cv.getTrackbarPos("MaskBlur", "Shadow Removal")
        mask_blur = max(3, mask_blur)
        mask_blur = mask_blur if mask_blur % 2 == 1 else mask_blur + 1

        mask = compute_shadow_mask_adaptive(L / 255.0, S, sensitivity, mask_blur)

        L_final, A_final, B_final = remove_shadows_adaptive_v3(
            L, A, B, L_retinex, strength, mask, mask_blur
        )

        lab_out = cv.merge([L_final, A_final, B_final]).astype(np.uint8)
        result = cv.cvtColor(lab_out, cv.COLOR_LAB2BGR)

        #  BUILD RGB VIEW 
        orig_rgb = cv.cvtColor(img_preview, cv.COLOR_BGR2RGB)
        mask_rgb = cv.cvtColor((mask * 255).astype(np.uint8), cv.COLOR_GRAY2RGB)
        result_rgb = cv.cvtColor(result, cv.COLOR_BGR2RGB)

        combined_rgb = np.hstack([orig_rgb, mask_rgb, result_rgb])

        # Convert back so OpenCV shows correct colors
        combined_bgr = cv.cvtColor(combined_rgb, cv.COLOR_RGB2BGR)

        cv.imshow("Shadow Removal", combined_bgr)
        
            # ret will return a true value if the frame exists otherwise False
        into_hsv =cv.cvtColor(combined_bgr,cv.COLOR_BGR2HSV)
        # changing the color format from BGr to HSV 
        # This will be used to create the mask
        L_limit=np.array([6,100,130]) # setting the blue lower limit
        U_limit=np.array([60,255,255]) # setting the blue upper limit
           

        b_mask=cv.inRange(into_hsv,L_limit,U_limit)
        # creating the mask using inRange() function
        # this will produce an image where the color of the objects
        # falling in the range will turn white and rest will be black
        blue=cv.bitwise_and(combined_bgr,combined_bgr,mask=b_mask)
        # this will give the color to mask.
        cv.imshow('Original',combined_bgr) # to display the original frame
        cv.imshow('Blue Detector',blue) # to display the blue object output
        
        key = cv.waitKey(30) & 0xFF
        if key == 27 or cv.getWindowProperty("Shadow Removal", cv.WND_PROP_VISIBLE) < 1:
            break
 
     
    cap.release()
    cv.destroyAllWindows()