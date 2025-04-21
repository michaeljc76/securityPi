from picamera2 import Picamera2
import cv2
import mediapipe as mp
import face_recognition
import numpy as np
import RPi.GPIO as GPIO
import time

SERVO_PIN = 17
BUZZER_PIN = 23

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

# SERVO SETUP
GPIO.setmode(GPIO.BCM)  # Use Broadcom pin numbering
GPIO.setup(SERVO_PIN, GPIO.OUT)

# Set up PWM for the servo
servo_pwm = GPIO.PWM(SERVO_PIN, 50)  # 50Hz PWM frequency
servo_pwm.start(0)  # Start with 0% duty cycle

# Function to set servo angle
last_angle = None  # Track the last angle

def set_servo_angle(angle):
    global last_angle
    if last_angle == angle:
        return  # Skip if already at desired angle
    last_angle = angle
    duty_cycle = (angle / 18) + 2
    servo_pwm.ChangeDutyCycle(duty_cycle)
    time.sleep(0.5)  # Reduced sleep for snappiness
    servo_pwm.ChangeDutyCycle(0)  # Stop sending signal

# BUZZER SETUP
GPIO.setup(BUZZER_PIN, GPIO.OUT)
buzzer_pwm = GPIO.PWM(BUZZER_PIN, 1000)

def buzz():
    buzzer_pwm.start(50)
    print("Buzzing at 1kHz...")
    time.sleep(1)
    buzzer_pwm.stop()
    print("Stopped buzzing.")

# CAMERA SETUP
picam = Picamera2()

preview_config = picam.create_preview_configuration(main={"format": "RGB888", "size": (1440, 1080)})
picam.configure(preview_config)
picam.start()

detected_name = None  # Variable to store the name of the detected person

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
                if encodings:
                    matches = face_recognition.compare_faces(known_faces, encodings[0])
                    name = "Unknown"

                    if True in matches:
                        match_index = matches.index(True)
                        name = known_names[match_index]
                        detected_name = name  # Store the detected name
                    else:
                        detected_name = None  # No match found
                else:
                    name = "No Encoding"
            except Exception as e:
                name = f"Error: {e}"
                print(e)

            # Draw rectangle and name
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, name, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2)

        # Move servo based on face detection
    if detected_name in ["Steven", "Mike"]:
        set_servo_angle(90)  # Move to 90 degrees if Steven or Mike is detected
    elif detected_name == "Unknown":
        buzz()
        set_servo_angle(0)  # Move back to 0 degrees if neither is detected
    else: # Nothing in frame
        set_servo_angle(0)

    cv2.imshow("Face Recognition with MediaPipe", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
GPIO.cleanup()
cv2.destroyAllWindows()
