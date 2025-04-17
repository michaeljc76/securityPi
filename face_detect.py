import cv2
import os
import numpy as np
import pickle
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta
import mediapipe as mp

# Email setup
ALERT_EMAIL = "steven500le@gmail.com"
ALERT_PASSWORD = "cyji yoqw crcr qfhx"
TO_EMAIL = "steven900le@gmail.com"

def send_alert(image_path):
    msg = EmailMessage()
    msg['Subject'] = 'ALERT: Unknown Person Detected'
    msg['From'] = ALERT_EMAIL
    msg['To'] = TO_EMAIL
    msg.set_content('An unknown person was detected by the camera.')

    with open(image_path, 'rb') as img:
        img_data = img.read()
        msg.add_attachment(img_data, maintype='image', subtype='jpeg', filename='intruder.jpg')

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(ALERT_EMAIL, ALERT_PASSWORD)
            smtp.send_message(msg)
        print("Email alert sent.")
    except Exception as e:
        print("Failed to send email:", e)

# Face detection model
mp_face_detection = mp.solutions.face_detection
face_detection = mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.5)

def run_recognition():
    try:
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.read("face_model.yml")
        with open("labels.pickle", "rb") as f:
            label_ids = pickle.load(f)
            labels = {v: k for k, v in label_ids.items()}
    except:
        print("Model files not found. Please train first.")
        return

    last_alert_time = datetime.min
    alert_interval = timedelta(seconds=30)  # wait 30 seconds between email alerts

    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_detection.process(rgb_frame)

        if results.detections:
            for detection in results.detections:
                bbox = detection.location_data.relative_bounding_box
                ih, iw, _ = frame.shape
                x, y, w, h = int(bbox.xmin * iw), int(bbox.ymin * ih), \
                             int(bbox.width * iw), int(bbox.height * ih)
                x = max(0, x)
                y = max(0, y)
                x_end = min(iw, x + w)
                y_end = min(ih, y + h)
                face_roi = frame[y:y_end, x:x_end]

                if face_roi is not None and face_roi.size != 0:
                    gray_face = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
                    resized_face = cv2.resize(gray_face, (100, 100))
                    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                    processed_face = clahe.apply(resized_face)

                    id_, confidence = recognizer.predict(processed_face)

                    if confidence < 100:
                        name = labels[id_]
                        color = (0, 255, 0)
                    else:
                        name = "Unknown"
                        color = (0, 0, 255)

                        now = datetime.now()
                        if now - last_alert_time > alert_interval:
                            image_path = "intruder.jpg"
                            cv2.imwrite(image_path, face_roi)
                            send_alert(image_path)
                            last_alert_time = now

                    cv2.rectangle(frame, (x, y), (x_end, y_end), color, 2)
                    cv2.putText(frame, f"{name} {confidence:.1f}", 
                                (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        cv2.imshow("Face Recognition", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# Run the system
run_recognition()
