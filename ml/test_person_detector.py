import cv2
from person_detector import PersonDetector

cap = cv2.VideoCapture(0)  # change index if needed
detector = PersonDetector()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    detected, boxes = detector.detect(frame)

    for (x1, y1, x2, y2, conf) in boxes:
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, f"Person {conf:.2f}", (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    cv2.imshow("Person Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
