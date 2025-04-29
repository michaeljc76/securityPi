import tkinter as tk
from tkinter import ttk
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
ALERT_PASSWORD = "srid lnij uqbf tnao"

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
preview_config = picam.create_preview_configuration(main={"format": "RGB888", "size": (320, 240)})
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

        style = ttk.Style()
        style.configure("Rounded.TButton",
                        font=("Helvetica", 14),
                        padding=10,
                        relief="flat",
                        background="#00cc66",
                        foreground="white")
        style.map("Rounded.TButton", background=[("active", "#00aa55")])

        control_frame = tk.Frame(window, bg="#1e1e2f")
        control_frame.pack(pady=5)

        self.open_button = ttk.Button(control_frame, text="Open Door", command=self.open_door, style="Rounded.TButton")
        self.open_button.pack(side=tk.LEFT, padx=10)

        self.toggle_text = tk.StringVar()
        self.toggle_text.set("Camera: ON")
        self.toggle_button = ttk.Button(control_frame, textvariable=self.toggle_text, command=self.toggle_camera, style="Rounded.TButton")
        self.toggle_button.pack(side=tk.LEFT, padx=10)

        self.log_box = Text(window, height=8, width=80, bg="#f0f0f0", fg="black")
        self.log_box.pack(pady=(10, 0))
        scrollbar = Scrollbar(window, command=self.log_box.yview)
        self.log_box.config(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.quit_button = ttk.Button(window, text="Quit", command=self.on_close, style="Rounded.TButton")
        self.quit_button.pack(pady=10)

        self.running = True
        self.detected_name = None
        self.unknown_detected = False
        self.last_alert_time = 0
        self.camera_active = True
        self.frame_counter = 0

        self.placeholder = np.ones((240, 320, 3), dtype=np.uint8) * 100
        cv2.putText(self.placeholder, "Camera Off", (70, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

        self.update_frame()

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
            self.log("📷 Camera activated")
        else:
            self.toggle_text.set("Camera: OFF")
            self.update_status("Camera Off")
            self.log("📷 Camera deactivated")
            img = Image.fromarray(cv2.cvtColor(self.placeholder, cv2.COLOR_BGR2RGB))
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

    def update_frame(self):
        if not self.running:
            return

        if self.camera_active:
            frame = picam.capture_array()

            # Resize for faster display
            small_frame = cv2.resize(frame, (320, 240))

            rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            if self.frame_counter % 5 == 0:  # Only run detection every 5 frames
                results = face_detection.process(rgb_small)
                self.detected_name = None

                if results.detections:
                    for det in results.detections:
                        bboxC = det.location_data.relative_bounding_box
                        ih, iw, _ = small_frame.shape
                        x1 = int(bboxC.xmin * iw)
                        y1 = int(bboxC.ymin * ih)
                        w = int(bboxC.width * iw)
                        h = int(bboxC.height * ih)
                        x2, y2 = x1 + w, y1 + h
                        pad = 20
                        x1, y1 = max(0, x1 - pad), max(0, y1 - pad)
                        x2, y2 = min(iw, x2 + pad), min(ih, y2 + pad)
                        face_crop = rgb_small[y1:y2, x1:x2]
                        face_location = [(y1, x2, y2, x1)]
                        try:
                            encodings = face_recognition.face_encodings(rgb_small, face_location)
                            name = "Unknown"
                            if encodings:
                                matches = face_recognition.compare_faces(known_faces, encodings[0])
                                if True in matches:
                                    idx = matches.index(True)
                                    name = known_names[idx]
                            self.detected_name = name
                        except:
                            continue

                current_time = time.time()
                if self.detected_name in ["Steven", "Mike"]:
                    set_servo_angle(90)
                    self.unknown_detected = False
                elif self.detected_name == "Unknown":
                    if not self.unknown_detected or (current_time - self.last_alert_time > 30):
                        buzz()
                        send_alert(frame, datetime.now())
                        self.log("🚨 Unknown detected!")
                        self.last_alert_time = current_time
                        self.unknown_detected = True

                if self.detected_name:
                    self.update_status(self.detected_name)

            img = Image.fromarray(rgb_small)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

            self.frame_counter += 1

        self.window.after(66, self.update_frame)  # Roughly 15 FPS

    def on_close(self):
        self.running = False
        servo_pwm.stop()
        buzzer_pwm.stop()
        GPIO.cleanup()
        picam.close()
        self.window.destroy()

# --- Main Program ---
root = tk.Tk()
app = FaceApp(root)
root.mainloop()
