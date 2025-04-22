import tkinter as tk
from tkinter import Label, Button, Text, Scrollbar, END
from PIL import Image, ImageTk
import threading
import cv2
from picamera2 import Picamera2
import mediapipe as mp
import face_recognition
import numpy as np
import RPi.GPIO as GPIO
import time
import smtplib
from email.message import EmailMessage
from datetime import datetime
import os

# --- GPIO Setup ---
SERVO_PIN = 17
BUZZER_PIN = 23
GPIO.setmode(GPIO.BCM)
GPIO.setup(SERVO_PIN, GPIO.OUT)
GPIO.setup(BUZZER_PIN, GPIO.OUT)
servo_pwm = GPIO.PWM(SERVO_PIN, 50)
servo_pwm.start(0)
buzzer_pwm = GPIO.PWM(BUZZER_PIN, 1000)
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

def buzz():
    buzzer_pwm.start(50)
    time.sleep(1)
    buzzer_pwm.stop()

# --- Email Setup ---
TO_EMAIL = "steven900le@gmail.com"
ALERT_EMAIL = "steven500le@gmail.com"
ALERT_PASSWORD = "oxwu icfw uogq eesj"

def send_alert(image_np, timestamp):
    filename = "intruder.jpg"
    cv2.imwrite(filename, image_np)
    msg = EmailMessage()
    msg['Subject'] = f'⚠️ ALERT: Unknown Person at {timestamp.strftime("%Y-%m-%d %H:%M:%S")}'
    msg['From'] = ALERT_EMAIL
    msg['To'] = TO_EMAIL
    msg.set_content(f"Unknown person detected at {timestamp.strftime('%c')}. Image attached.")
    with open(filename, 'rb') as img:
        msg.add_attachment(img.read(), maintype='image', subtype='jpeg', filename='intruder.jpg')
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(ALERT_EMAIL, ALERT_PASSWORD)
            smtp.send_message(msg)
    except Exception as e:
        print("Email error:", e)
    finally:
        if os.path.exists(filename):
            os.remove(filename)

# --- Load Known Faces ---
known_faces = []
known_names = []

def load_face(image_path, name):
    image = face_recognition.load_image_file(image_path)
    encodings = face_recognition.face_encodings(image)
    if encodings:
        known_faces.append(encodings[0])
        known_names.append(name)

load_face("mike.png", "Mike")
load_face("steven.png", "Steven")
load_face("jay.png", "Jay")

# --- MediaPipe Setup ---
mp_face_detection = mp.solutions.face_detection
face_detection = mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.6)

# --- Camera Setup ---
picam = Picamera2()
preview_config = picam.create_preview_configuration(main={"format": "RGB888", "size": (280, 190)})
picam.configure(preview_config)
picam.start()

# --- GUI Setup ---
class FaceApp:
    def __init__(self, window):
        self.window = window
        self.window.title("Smart Door System")
        self.window.geometry("720x680")
        self.window.configure(bg="#1e1e2f")

        self.video_label = Label(window, bg="#1e1e2f")
        self.video_label.pack(pady=5)

        self.status = Label(window, text="Initializing...", font=("Helvetica", 16, "bold"), fg="#00ffcc", bg="#1e1e2f")
        self.status.pack(pady=10)

        # Control buttons frame
        control_frame = tk.Frame(window, bg="#1e1e2f")
        control_frame.pack(pady=5)

        self.open_button = Button(control_frame, text="Open Door", command=self.open_door, font=("Helvetica", 14),
                                bg="#00cc66", fg="white", activebackground="#00aa55", relief="raised")
        self.open_button.pack(side=tk.LEFT, padx=10)

        # Camera toggle button
        self.camera_active = True
        self.toggle_text = tk.StringVar()
        self.toggle_text.set("Camera: ON")
        self.toggle_button = Button(control_frame, textvariable=self.toggle_text, command=self.toggle_camera,
                                  font=("Helvetica", 14), bg="#3498db", fg="white", activebackground="#2980b9", 
                                  relief="raised", width=12)
        self.toggle_button.pack(side=tk.LEFT, padx=10)

        self.log_box = Text(window, height=8, width=80, bg="#f0f0f0", fg="black")
        self.log_box.pack(pady=(10, 0))
        scrollbar = Scrollbar(window, command=self.log_box.yview)
        self.log_box.config(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.quit_button = Button(window, text="Quit", command=self.on_close, bg='red', fg='white')
        self.quit_button.pack(pady=10)

        self.running = True
        self.detected_name = None
        self.unknown_detected = False
        self.last_alert_time = 0
        
        # Create a placeholder image for when camera is off
        self.placeholder = np.ones((190, 280, 3), dtype=np.uint8) * 100  # Gray placeholder
        cv2.putText(self.placeholder, "Camera Off", (70, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        
        self.thread = threading.Thread(target=self.camera_loop)
        self.thread.start()

        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

    def log(self, message):
        self.log_box.insert(END, f"{datetime.now().strftime('%H:%M:%S')} - {message}\n")
        self.log_box.see(END)

    def update_status(self, name):
        self.status.config(text=f"Detected: {name}")

    def open_door(self):
        set_servo_angle(90)
        self.log("✅ Door manually opened.")
    
    def toggle_camera(self):
        self.camera_active = not self.camera_active
        if self.camera_active:
            self.toggle_text.set("Camera: ON")
            self.toggle_button.config(bg="#3498db")
            self.log("📷 Camera activated")
        else:
            self.toggle_text.set("Camera: OFF")
            self.toggle_button.config(bg="#95a5a6")  # Gray color when off
            self.update_status("Camera Off")
            self.log("📷 Camera deactivated")
            # Display placeholder image
            img = Image.fromarray(cv2.cvtColor(self.placeholder, cv2.COLOR_BGR2RGB))
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

    def camera_loop(self):
        while self.running:
            if not self.camera_active:
                time.sleep(0.1)  # Reduce CPU usage when camera is off
                continue
                
            frame = picam.capture_array()
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_detection.process(rgb)

            self.detected_name = None
            if results.detections:
                for det in results.detections:
                    bboxC = det.location_data.relative_bounding_box
                    ih, iw, _ = frame.shape
                    x1 = int(bboxC.xmin * iw)
                    y1 = int(bboxC.ymin * ih)
                    w = int(bboxC.width * iw)
                    h = int(bboxC.height * ih)
                    x2, y2 = x1 + w, y1 + h
                    pad = 20
                    x1, y1 = max(0, x1 - pad), max(0, y1 - pad)
                    x2, y2 = min(iw, x2 + pad), min(ih, y2 + pad)
                    face_crop = rgb[y1:y2, x1:x2]
                    face_location = [(y1, x2, y2, x1)]
                    try:
                        encodings = face_recognition.face_encodings(rgb, face_location)
                        name = "Unknown"
                        if encodings:
                            matches = face_recognition.compare_faces(known_faces, encodings[0])
                            if True in matches:
                                idx = matches.index(True)
                                name = known_names[idx]
                        self.detected_name = name
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, name, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                    except:
                        continue

            current_time = time.time()
            if self.detected_name in ["Steven", "Mike"]:
                set_servo_angle(90)
                self.unknown_detected = False
            elif self.detected_name == "Unknown":
                if not self.unknown_detected or (current_time - self.last_alert_time > 15):
                    buzz()
                    send_alert(frame, datetime.now())
                    self.log("⚠️ Unknown person detected! Awaiting manual action...")
                    self.last_alert_time = current_time
                    self.unknown_detected = True
                set_servo_angle(0)
            else:
                set_servo_angle(0)

            self.update_status(self.detected_name if self.detected_name else "None")

            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

    def on_close(self):
        self.running = False
        self.thread.join()
        servo_pwm.stop()
        buzzer_pwm.stop()
        GPIO.cleanup()
        self.window.destroy()

# --- Launch GUI ---
if __name__ == "__main__":
    root = tk.Tk()
    app = FaceApp(root)
    root.mainloop()