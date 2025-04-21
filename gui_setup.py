from picamera2 import Picamera2
import cv2
import mediapipe as mp
import face_recognition
import numpy as np
import RPi.GPIO as GPIO
import time
import smtplib
from email.message import EmailMessage
from datetime import datetime

# --- GPIO Setup ---
SERVO_PIN = 17
BUZZER_PIN = 23
GPIO.setmode(GPIO.BCM)
GPIO.setup(SERVO_PIN, GPIO.OUT)
GPIO.setup(BUZZER_PIN, GPIO.OUT)

# --- Servo Setup ---
servo_pwm = GPIO.PWM(SERVO_PIN, 50)
servo_pwm.start(0)
last_angle = None

def set_servo_angle(angle):
    global last_angle
    if last_angle == angle:
        return
    last_angle = angle
    duty_cycle = (angle / 18) + 2
    servo_pwm.ChangeDutyCycle(duty_cycle)
    time.sleep(0.5)
    servo_pwm.ChangeDutyCycle(0)

# --- Buzzer Setup ---
buzzer_pwm = GPIO.PWM(BUZZER_PIN, 1000)

def buzz():
    buzzer_pwm.start(50)
    print("Buzzing at 1kHz...")
    time.sleep(1)
    buzzer_pwm.stop()
    print("Stopped buzzing.")

# --- Email Setup ---
TO_EMAIL = "steven900le@gmail.com"
ALERT_EMAIL = "steven500le@gmail.com"
ALERT_PASSWORD = "oxwu icfw uogq eesj"

def send_alert(image_path, timestamp):
    msg = EmailMessage()
    msg['Subject'] = f'⚠️ ALERT: Unknown Person Detected at {timestamp.strftime("%Y-%m-%d %H:%M:%S")}'
    msg['From'] = ALERT_EMAIL
    msg['To'] = TO_EMAIL

    body = f"""
ALERT: An unknown person was detected by your security system.

📅 Time of Detection: {timestamp.strftime('%A, %B %d, %Y at %I:%M:%S %p')}
📍 Camera Device: Pi Security Cam

Please review the attached image for verification.
    """.strip()

    msg.set_content(body)

    with open(image_path, 'rb') as img:
        img_data = img.read()
        msg.add_attachment(img_data, maintype='image', subtype='jpeg',
                           filename=f"intruder_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg")

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(ALERT_EMAIL, ALERT_PASSWORD)
            smtp.send_message(msg)
        print("✅ Email alert sent.")
    except Exception as e:
        print("❌ Failed to send email:", e)

# --- Load Known Faces ---
known_faces = []
known_names = []

def load_face(image_path, name):
    image = face_recognition.load_image_file(image_path)
    encodings = face_recognition.face_encodings(image)
    if encodings:
        known_faces.append(encodings[0])
        known_names.append(name)
    else:
        print(f"No face found in {name}'s image")

load_face("mike.png", "Mike")
load_face("steven.png", "Steven")
load_face("jay.png", "Jay")

# --- MediaPipe Face Detection ---
mp_face_detection = mp.solutions.face_detection
mp_drawing = mp.solutions.drawing_utils
face_detection = mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.6)

# --- Camera Setup ---
picam = Picamera2()
preview_config = picam.create_preview_configuration(main={"format": "RGB888", "size": (1440, 1080)})
picam.configure(preview_config)
picam.start()

# --- Main Loop ---
detected_name = None

try:
    while True:
        frame = picam.capture_array()
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_detection.process(rgb_frame)

        detected_name = None  # Reset every loop

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
                face_location = [(y1, x2, y2, x1)]

                try:
                    encodings = face_recognition.face_encodings(rgb_frame, face_location)
                    name = "Unknown"
                    if encodings:
                        matches = face_recognition.compare_faces(known_faces, encodings[0])
                        if True in matches:
                            match_index = matches.index(True)
                            name = known_names[match_index]
                            detected_name = name
                        else:
                            detected_name = "Unknown"
                    else:
                        name = "No Encoding"
                except Exception as e:
                    name = f"Error: {e}"
                    print(e)

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, name, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        if detected_name in ["Steven", "Mike"]:
            set_servo_angle(90)
        elif detected_name == "Unknown":
            timestamp = datetime.now()
            image_path = f"unknown_{int(time.time())}.jpg"
            cv2.imwrite(image_path, frame)
            buzz()
            send_alert(image_path, timestamp)
            set_servo_angle(0)
        else:
            set_servo_angle(0)

        cv2.imshow("Face Recognition with MediaPipe", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    servo_pwm.stop()
    buzzer_pwm.stop()
    GPIO.cleanup()
    cv2.destroyAllWindows()
