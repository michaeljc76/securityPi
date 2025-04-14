from picamera2 import Picamera2
import cv2
import mediapipe as mp
import face_recognition
import numpy as np

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
if encodings_mike:  # Check if face encoding is found
    encoding_mike = encodings_mike[0]
    known_faces.append(encoding_mike)
    known_names.append("Mike")
else:
    print("No face found in Mike's image")

# Steven
image_steven = face_recognition.load_image_file("steven.png")
encodings_steven = face_recognition.face_encodings(image_steven)
if encodings_steven:  # Check if face encoding is found
    encoding_steven = encodings_steven[0]
    known_faces.append(encoding_steven)
    known_names.append("Steven")
else:
    print("No face found in Steven's image")

# Jay
# Steven
image_jay = face_recognition.load_image_file("jay.png")
encodings_jay = face_recognition.face_encodings(image_jay)
if encodings_jay:  # Check if face encoding is found
    encoding_jay = encodings_jay[0]
    known_faces.append(encoding_jay)
    known_names.append("Jay")
else:
    print("No face found in Jay's image")

# Start camera
picam = Picamera2()
picam.configure(picam.preview_configuration(main={"format": "RGB888", "size": (640, 480)}))
picam.start()

while True:
    frame = picam.capture_array()

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

            # Add padding to mediapipe bounding box
            pad = 20
            x1 = max(0, x1 - pad)
            y1 = max(0, y1 - pad)
            x2 = min(iw, x2 + pad)
            y2 = min(ih, y2 + pad)

            # Crop the face region
            # face_crop = rgb_frame[y1:y2, x1:x2]
            face_crop = rgb_frame[y1:y2, x1:x2]

            # Encode face using face_recognition
            try:
                face_location = [(y1, x2, y2, x1)]  # top, right, bottom, left
                encodings = face_recognition.face_encodings(rgb_frame, face_location)
                #encodings = face_recognition.face_encodings(face_crop)
                if encodings:
                    matches = face_recognition.compare_faces(known_faces, encodings[0])
                    name = "Unknown"

                    if True in matches:
                        match_index = matches.index(True)
                        name = known_names[match_index]
                else:
                    name = "No Encoding"
            except Exception as e:
                name = f"Error: {e}"
                print(e)

            # Draw rectangle and name
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, name, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    cv2.imshow("Face Recognition with MediaPipe", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
