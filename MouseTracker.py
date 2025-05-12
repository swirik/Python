import cv2
import numpy as np
from pynput.mouse import Controller, Button
from cvzone.HandTrackingModule import HandDetector

# Initialize external webcam (change index if needed)
cap = cv2.VideoCapture(1)  # Change to 0 if the external cam is not detected
cap.set(3, 640)  # Camera resolution width
cap.set(4, 480)  # Camera resolution height

# Initialize Hand Detector
detector = HandDetector(detectionCon=0.8, maxHands=1)

# Mouse Controller
mouse = Controller()
screen_w, screen_h = 1920, 1080  # Adjust based on screen resolution

# Smoothing factor
smoothening = 4
prevX, prevY = 0, 0

while cap.isOpened():
    success, img = cap.read()
    if not success:
        break

    img = cv2.flip(img, 1)  # Mirror effect

    # Detect hands and draw landmarks
    hands, img = detector.findHands(img, draw=True)

    if hands:
        hand = hands[0]
        lmList = hand["lmList"]

        if lmList:
            x1, y1 = lmList[8][:2]  # Index finger tip

            # Map webcam coordinates to screen coordinates
            x3 = np.interp(x1, (0, 640), (0, screen_w))
            y3 = np.interp(y1, (0, 480), (0, screen_h))

            # Apply smoothing
            currX = prevX + (x3 - prevX) / smoothening
            currY = prevY + (y3 - prevY) / smoothening

            mouse.position = (currX, currY)
            prevX, prevY = currX, currY

            # Click when thumb and index finger are close
            length, _, _ = detector.findDistance(lmList[8][:2], lmList[4][:2], img)
            if length < 40:
                mouse.click(Button.left, 1)

    cv2.imshow("Virtual Mouse", img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
