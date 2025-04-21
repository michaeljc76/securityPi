from picamera2 import Picamera2
import cv2
import face_recognition
import numpy as np
import RPi.GPIO as GPIO
import time
import tkinter as tk
from tkinter import messagebox

# SERVO & BUZZER PIN SETUP
SERVO_PIN = 17
BUZZER_PIN = 23

# Initialize GPIO
GPIO.setmode(GPIO.BCM)  # Use Broadcom pin numbering
GPIO.setup(SERVO_PIN, GPIO.OUT)
GPIO.setup(BUZZER_PIN, GPIO.OUT)

# Set up PWM for the servo
servo_pwm = GPIO.PWM(SERVO_PIN, 50)  # 50Hz PWM frequency
servo_pwm.start(0)  # Start with 0% duty cycle

# Set up PWM for the buzzer
buzzer_pwm = GPIO.PWM(BUZZER_PIN, 1000)

# Initialize known faces
known_faces = []
known_names = []

# Load known faces (using face_recognition library)
def load_known_faces():
    global known_faces, known_names

    # Mike
    image_mike = face_recognition.load_image_file("mike.png")
    encodings_mike = face_recognition.face_encodings(image_mike)
    if encodings_mike:
        encoding_mike = encodings_mike[0]
        known_faces.append(encoding_mike)
        known_names.append("Mike")

    # Steven
    image_steven = face_recognition.load_image_file("steven.png")
    encodings_steven = face_recognition.face_encodings(image_steven)
    if encodings_steven:
        encoding_steven = encodings_steven[0]
        known_faces.append(encoding_steven)
        known_names.append("Steven")

    # Jay
    image_jay = face_recognition.load_image_file("jay.png")
    encodings_jay = face_recognition.face_encodings(image_jay)
    if encodings_jay:
        encoding_jay = encodings_jay[0]
        known_faces.append(encoding_jay)
        known_names.append("Jay")

# Initialize the GUI
root = tk.Tk()
root.title("Face Recognition")

# Create a label to show the detected name
label = tk.Label(root, text="No face detected", font=("Arial", 16))
label.pack(pady=20)

# Create a button to exit the program
exit_button = tk.Button(root, text="Exit", command=root.quit, font=("Arial", 14))
exit_button.pack(pady=10)

# Function to set the servo angle
last_angle = None

def set_servo_angle(angle):
    global last_angle
    if last_angle == angle:
        return
    last_angle = angle
    duty_cycle = (angle / 18) + 2
    servo_pwm.ChangeDutyCycle(duty_cycle)
    time.sleep(0.5)  # Reduced sleep for snappiness
    servo_pwm.ChangeDutyCycle(0)  # Stop sending signal

# Function to buzz the buzzer
def buzz():
    buzzer_pwm.start(50)
    print("Buzzing...")
    time.sleep(1)
    buzzer_pwm.stop()
    print("Buzz stopped.")

# Set up camera and start capturing
picam = Picamera2()

# Lower resolution for faster processing
preview_config = picam.create_preview_configuration(main={"format": "RGB888", "size": (320, 240)})
picam.configure(preview_config)
picam.start()

detected_name = None

# Load known faces
load_known_faces()

# Function to handle face recognition and update the GUI
def update_gui():
    global detected_name
    frame = picam.capture_array()

    # Convert frame to RGB (face_recognition uses RGB, not BGR)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Find faces in the image
    face_locations = face_recognition.face_locations(rgb_frame)

    if face_locations:
        for face_location in face_locations:
            # Get the encoding for the face
            encoding = face_recognition.face_encodings(rgb_frame, [face_location])

            if encoding:
                matches = face_recognition.compare_faces(known_faces, encoding[0])
                name = "Unknown"

                if True in matches:
                    match_index = matches.index(True)
                    name = known_names[match_index]
                    detected_name = name  # Store the detected name
                else:
                    detected_name = None  # No match found
            else:
                name = "No Encoding"

            # Draw rectangle and name on frame
            top, right, bottom, left = face_location
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    # Update the label with the detected name
    label.config(text=f"Detected: {detected_name if detected_name else 'No face detected'}")

    # Control servo and buzzer based on detection
    if detected_name in ["Steven", "Mike"]:
        set_servo_angle(90)  # Move to 90 degrees if Steven or Mike is detected
    elif detected_name == "Unknown":
        buzz()
        set_servo_angle(0)  # Move back to 0 degrees if neither is detected
    else:  # Nothing in frame
        set_servo_angle(0)

    # Show the frame with annotations
    cv2.imshow("Face Recognition", frame)

    # Continue to update GUI every 100ms
    root.after(100, update_gui)

# Start updating the GUI
update_gui()

# Start the main event loop for the GUI
root.mainloop()

# Cleanup on exit
picam.stop()
GPIO.cleanup()
cv2.destroyAllWindows()
