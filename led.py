from picamera2 import Picamera2
import cv2
import mediapipe as mp
import face_recognition
import numpy as np
import RPi.GPIO as GPIO
import time

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
else:
    print("No face found in Mike's image")

# Steven
image_steven = face_recognition.load_image_file("steven.png")
encodings_steven = face_recognition.face_encodings(image_steven)
if encodings_steven:
    known_faces.append(encodings_steven[0])
    known_names.append("Steven")
else:
    print("No face found in Steven's image")

# Jay
image_jay = face_recognition.load_image_file("jay.png")
encodings_jay = face_recognition.face_encodings(image_jay)
if encodings_jay:
    known_faces.append(encodings_jay[0])
    known_names.append("Jay")
else:
    print("No face found in Jay's image")

# GPIO SETUP
GPIO.setmode(GPIO.BCM)

# SERVO SETUP
servo_pin = 18  # Adjust pin if needed
GPIO.setup(servo_pin, GPIO.OUT)
servo_pwm = GPIO.PWM(servo_pin, 50)
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

# RGB LED SETUP
red_pin = 17
green_pin = 27
GPIO.setup(red_pin, GPIO.OUT)
GPIO.setup(green_pin, GPIO.OUT)

def show_color(color):
    if color == "green":
        GPIO.output(green_pin, GPIO.HIGH)
        GPIO.output(red_pin, GPIO.LOW)
    elif color == "red":
        GPIO.output(green_pin, GPIO.LOW)
        GPIO.output(red_pin, GPIO.HIGH)
    else:
        GPIO.output(green_pin, GPIO.LOW)
        GPIO.output(red_pin, GPIO.LOW)

# CAMERA SETUP
picam = Picamera2()
preview_config = picam.create_preview_configuration(main={"format": "RGB888", "size": (1440, 1080)})
picam.configure(preview_config)
picam.start()

detected_name = None

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
                            detected_name = None
                    else:
                        name = "No Encoding"

                except Exception as e:
                    print(f"Encoding error: {e}")
                    name = "Error"

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, name, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2)

        # Check if authorized person is detected
        if detected_name in ["Steven", "Mike"]:
            set_servo_angle(90)
            show_color("green")
        else:
            set_servo_angle(0)
            show_color("red")

        cv2.imshow("Face Recognition with MediaPipe", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    servo_pwm.stop()
    show_color("off")
    GPIO.cleanup()
    cv2.destroyAllWindows()
