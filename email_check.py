# from picamera2 import Picamera2
import cv2
import mediapipe as mp
import face_recognition
import numpy as np
import RPi.GPIO as GPIO
import time
import smtplib
from email.message import EmailMessage

# ========== Email Setup ==========
def send_email_alert(subject, body):
    sender_email = " kimChaewonLeSera@gmail.com"
    sender_password = "havQPi5y8rFutrG"  # Use App Password if 2FA is enabled
    receiver_email = "steven500le@gmail.com"

    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)
        print("Email sent successfully.")
    except Exception as e:
        print(f"Error sending email: {e}")

# ========== LED Setup ==========
GPIO.setmode(GPIO.BCM)
RED_PIN = 22
GREEN_PIN = 23
BLUE_PIN = 24

GPIO.setup(RED_PIN, GPIO.OUT)
GPIO.setup(GREEN_PIN, GPIO.OUT)
GPIO.setup(BLUE_PIN, GPIO.OUT)

def show_color(color):
    if color == "red":
        GPIO.output(RED_PIN, GPIO.HIGH)
        GPIO.output(GREEN_PIN, GPIO.LOW)
        GPIO.output(BLUE_PIN, GPIO.LOW)
    elif color == "green":
        GPIO.output(RED_PIN, GPIO.LOW)
        GPIO.output(GREEN_PIN, GPIO.HIGH)
        GPIO.output(BLUE_PIN, GPIO.LOW)
    else:
        GPIO.output(RED_PIN, GPIO.LOW)
        GPIO.output(GREEN_PIN, GPIO.LOW)
        GPIO.output(BLUE_PIN, GPIO.LOW)

# ========== Servo Setup ==========
servo_pin = 17
GPIO.setup(servo_pin, GPIO.OUT)
servo_pwm = GPIO.PWM(servo_pin, 50)  # 50Hz
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

# ========== Face Recognition Setup ==========
mp_face_detection = mp.solutions.face_detection
face_detection = mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.6)

known_faces = []
known_names = []

def load_face(name, filename):
    image = face_recognition.load_image_file(filename)
    encodings = face_recognition.face_encodings(image)
    if encodings:
        known_faces.append(encodings[0])
        known_names.append(name)
    else:
        print(f"No face found in {name}'s image")

load_face("Mike", "mike.png")
load_face("Steven", "steven.png")
load_face("Jay", "jay.png")

# ========== Camera Setup ==========
picam = Picamera2()
preview_config = picam.create_preview_configuration(main={"format": "RGB888", "size": (1440, 1080)})
picam.configure(preview_config)
picam.start()

detected_name = None
last_alert_time = 0
alert_cooldown = 30  # seconds

# ========== Main Loop ==========
try:
    while True:
        frame = picam.capture_array()
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_detection.process(rgb_frame)

        detected_name = None

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

                face_location = [(y1, x2, y2, x1)]
                encodings = face_recognition.face_encodings(rgb_frame, face_location)

                if encodings:
                    matches = face_recognition.compare_faces(known_faces, encodings[0])
                    name = "Unknown"
                    if True in matches:
                        match_index = matches.index(True)
                        name = known_names[match_index]
                        detected_name = name
                    else:
                        detected_name = "Unknown"
                else:
                    detected_name = None

                # Draw rectangle
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, detected_name or "No Match", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2)

        # LED and Servo Logic
        if detected_name in ["Steven", "Mike"]:
            set_servo_angle(90)
            show_color("green")
        elif detected_name == "Unknown":
            set_servo_angle(0)
            show_color("red")

            # Throttle alert emails
            current_time = time.time()
            if current_time - last_alert_time > alert_cooldown:
                send_email_alert(
                    subject="⚠️ Unknown Person Detected!",
                    body="An unknown individual was detected by your Raspberry Pi face recognition system."
                )
                last_alert_time = current_time
        else:
            show_color("off")

        cv2.imshow("Face Recognition with MediaPipe", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    picam.stop()
    servo_pwm.stop()
    GPIO.cleanup()
    cv2.destroyAllWindows()
