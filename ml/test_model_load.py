import cv2
import os

MODEL_DIR = "backend/ml/models"

prototxt = os.path.join(MODEL_DIR, "MobileNetSSD_deploy.prototxt")
weights = os.path.join(MODEL_DIR, "MobileNetSSD_deploy.caffemodel")

print("Prototxt exists:", os.path.exists(prototxt))
print("Caffemodel exists:", os.path.exists(weights))

net = cv2.dnn.readNetFromCaffe(prototxt, weights)
print("✅ MobileNet-SSD loaded successfully")
