import cv2
import numpy as np

# --- Improved HSV Color Ranges ---
orange_lower = np.array([5, 120, 120])
orange_upper = np.array([25, 255, 255])

green_lower = np.array([45, 60, 60])
green_upper = np.array([75, 255, 255])

blue_lower = np.array([100, 120, 80])
blue_upper = np.array([130, 255, 255])

# --- Distance Measurement Parameters ---
KNOWN_WIDTH_ORANGE = 3.0   # cm (ball diameter)
KNOWN_WIDTH_GREEN = 2.2    # cm (cube width)  <-- change to your real size
KNOWN_WIDTH_BLUE = 5.0     # cm (triangle base) <-- change to your real size

FOCAL_LENGTH = 500.0       # replace with your calibrated value

def detect_shape(contour):
    peri = cv2.arcLength(contour, True)
    area = cv2.contourArea(contour)

    if peri == 0:
        return "object"

    circularity = 4 * np.pi * (area / (peri * peri))
    if circularity > 0.75:
        return "ball"

    approx = cv2.approxPolyDP(contour, 0.04 * peri, True)
    sides = len(approx)

    if sides == 3:
        return "triangle"
    elif 4 <= sides <= 6:
        return "cube"
    else:
        return "object"

def distance_to_camera(known_width, focal_length, pixel_width):
    return (known_width * focal_length) / pixel_width

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    blurred = cv2.GaussianBlur(frame, (7, 7), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

    # Masks
    mask_orange = cv2.inRange(hsv, orange_lower, orange_upper)
    mask_green = cv2.inRange(hsv, green_lower, green_upper)
    mask_blue = cv2.inRange(hsv, blue_lower, blue_upper)

    # Clean masks
    kernel = np.ones((5, 5), np.uint8)
    mask_orange = cv2.morphologyEx(mask_orange, cv2.MORPH_OPEN, kernel)
    mask_orange = cv2.dilate(mask_orange, kernel, iterations=2)

    mask_green = cv2.morphologyEx(mask_green, cv2.MORPH_OPEN, kernel)
    mask_green = cv2.dilate(mask_green, kernel, iterations=2)

    mask_blue = cv2.morphologyEx(mask_blue, cv2.MORPH_OPEN, kernel)
    mask_blue = cv2.dilate(mask_blue, kernel, iterations=2)

    # Find contours
    contours_orange, _ = cv2.findContours(mask_orange, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours_green, _ = cv2.findContours(mask_green, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours_blue, _ = cv2.findContours(mask_blue, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # --- Detect Orange Ball + Distance ---
    for cnt in contours_orange:
        area = cv2.contourArea(cnt)
        if area > 500:
            shape = detect_shape(cnt)
            x, y, w, h = cv2.boundingRect(cnt)

            if shape == "ball":
                distance = distance_to_camera(KNOWN_WIDTH_ORANGE, FOCAL_LENGTH, w)

                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 140, 255), 2)
                cv2.putText(frame, "Orange Ball", (x, y - 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 140, 255), 2)
                cv2.putText(frame, f"{distance:.1f} cm", (x, y - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 140, 255), 2)

    # --- Detect Green Cube + Distance ---
    for cnt in contours_green:
        area = cv2.contourArea(cnt)
        if area > 500:
            shape = detect_shape(cnt)
            x, y, w, h = cv2.boundingRect(cnt)

            distance = distance_to_camera(KNOWN_WIDTH_GREEN, FOCAL_LENGTH, w)

            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, f"Green {shape}", (x, y - 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f"{distance:.1f} cm", (x, y - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    # --- Detect Blue Triangle + Distance ---
    for cnt in contours_blue:
        area = cv2.contourArea(cnt)
        if area > 400:
            shape = detect_shape(cnt)
            if shape == "triangle":
                x, y, w, h = cv2.boundingRect(cnt)

                distance = distance_to_camera(KNOWN_WIDTH_BLUE, FOCAL_LENGTH, w)

                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                cv2.putText(frame, "Blue Triangle", (x, y - 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                cv2.putText(frame, f"{distance:.1f} cm", (x, y - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

    cv2.imshow("Detection", frame)
    cv2.imshow("Orange Mask", mask_orange)
    cv2.imshow("Green Mask", mask_green)
    cv2.imshow("Blue Mask", mask_blue)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
