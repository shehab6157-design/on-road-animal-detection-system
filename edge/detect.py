"""
Real-time animal detection on Raspberry Pi 5 (YOLOv5).

Transcribed from Figure 4-1 of the project report. The model-loading lines
and imports were not shown in the report and are added here so the script runs.
"""
import cv2
import torch

# Load the custom-trained YOLOv5 model (weights are not included in this repo)
model = torch.hub.load("ultralytics/yolov5", "custom", path="best.pt")

# Define target classes
target_classes = ["sheep", "cow", "horse", "dog"]

# Set confidence threshold
CONFIDENCE_THRESHOLD = 0.75

# Initialize video capture (0 = default webcam; change if using Pi camera or USB cam)
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Cannot open camera")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Cannot read frame")
        break

    # Run YOLOv5 inference
    results = model(frame)

    # Convert to pandas dataframe
    detections = results.pandas().xyxy[0]

    # Filter by class and confidence
    filtered = detections[
        (detections["name"].isin(target_classes)) &
        (detections["confidence"] >= CONFIDENCE_THRESHOLD)
    ]

    # Draw results
    for _, row in filtered.iterrows():
        xmin, ymin, xmax, ymax = int(row["xmin"]), int(row["ymin"]), int(row["xmax"]), int(row["ymax"])
        label = f"{row['name']} {row['confidence']:.2f}"

        cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)
        cv2.putText(frame, label, (xmin, ymin - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # Show the frame
    cv2.imshow("YOLOv5 Real-Time Detection", frame)

    # Press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
