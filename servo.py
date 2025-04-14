import cv2
import mediapipe as mp
import face_recognition
import numpy as np
import time
from gpiozero import Servo
from signal import pause

# Initialize servo on GPIO17
servo = Servo(17)  # Change pin number if needed
servo_opened = False
last_activation_time = 0

# Initialize MediaPipe face detection
mp_face_detection = mp.solutions.face_detection
mp_drawing = mp.solutions.drawing_utils
face_detection = mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.6)

# Load known faces
known_faces = []
known_names = []

# Mike
image_mike = face_recognition.load_image_file("mike.png")
encodings_mike = face_recognition.face_encodings(image_mike)
if encodings_mike:
    known_faces.append(encodings_mike[0])
    known_names.append("Mike")

# Steven
image_steven = face_recognition.load_image_file("steven.png")
encodings_steven = face_recognition.face_encodings(image_steven)
if encodings_steven:
    known_faces.append(encodings_steven[0])
    known_names.append("Steven")

# Jay
image_jay = face_recognition.load_image_file("jay.png")
encodings_jay = face_recognition.face_encodings(image_jay)
if encodings_jay:
    known_faces.append(encodings_jay[0])
    known_names.append("Jay")

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
            bboxC = detection.location_data.relative_bounding_box
            ih, iw, _ = frame.shape
            x1 = int(bboxC.xmin * iw)
            y1 = int(bboxC.ymin * ih)
            w = int(bboxC.width * iw)
            h = int(bboxC.height * ih)
            x2 = x1 + w
            y2 = y1 + h

            pad = 20
            x1 = max(0, x1 - pad)
            y1 = max(0, y1 - pad)
            x2 = min(iw, x2 + pad)
            y2 = min(ih, y2 + pad)

            face_crop = rgb_frame[y1:y2, x1:x2]

            try:
                face_location = [(y1, x2, y2, x1)]
                encodings = face_recognition.face_encodings(rgb_frame, face_location)
                name = "Unknown"

                if encodings:
                    matches = face_recognition.compare_faces(known_faces, encodings[0])
                    if True in matches:
                        match_index = matches.index(True)
                        name = known_names[match_index]

                        # 🧠 SECURITY TRIGGER: Activate servo if Mike or Steven is detected
                        if name in ["Mike", "Steven"]:
                            current_time = time.time()
                            if not servo_opened or current_time - last_activation_time > 5:
                                print(f"{name} recognized - Opening door (servo)")
                                servo.value = 1  # rotate 90 degrees (may vary with servo)
                                time.sleep(1.5)
                                servo.value = -1  # rotate back
                                servo_opened = True
                                last_activation_time = current_time

                else:
                    name = "No Encoding"

            except Exception as e:
                name = f"Error: {e}"
                print(e)

            # Draw name and rectangle
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, name, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    cv2.imshow("Face Recognition with MediaPipe", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
