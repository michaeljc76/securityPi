import cv2
import mediapipe as mp
import face_recognition
import numpy as np

# Initialize MediaPipe face detection
mp_face_detection = mp.solutions.face_detection
mp_drawing = mp.solutions.drawing_utils
face_detection = mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.6)

# Load known face
known_image = face_recognition.load_image_file("your_face.jpg")
known_encoding = face_recognition.face_encodings(known_image)[0]
known_name = "You"

# Start camera
cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_detection.process(rgb_frame)

    if results.detections:
        for detection in results.detections:
            # Get bounding box
            bboxC = detection.location_data.relative_bounding_box
            ih, iw, _ = frame.shape
            x1 = int(bboxC.xmin * iw)
            y1 = int(bboxC.ymin * ih)
            w = int(bboxC.width * iw)
            h = int(bboxC.height * ih)
            x2 = x1 + w
            y2 = y1 + h

            # Crop the face region
            face_crop = rgb_frame[y1:y2, x1:x2]

            # Encode face using face_recognition
            try:
                encodings = face_recognition.face_encodings(face_crop)
                if encodings:
                    match = face_recognition.compare_faces([known_encoding], encodings[0])[0]
                    name = known_name if match else "Unknown"
                else:
                    name = "No Encoding"
            except Exception as e:
                name = f"Error: {e}"

            # Draw rectangle and name
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, name, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

    cv2.imshow("Face Recognition with MediaPipe", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
