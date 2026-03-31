import cv2

cap = cv2.VideoCapture(0)

ret, frame = cap.read()

if ret:
    cv2.imwrite("usb_test.jpg", frame)
    print("Camera working — image saved")
else:
    print("Camera failed")

cap.release()
