import tkinter as tk
from tkinter import messagebox
import cv2
import numpy as np
import os
from PIL import Image
from datetime import datetime
import threading
import time
import requests
import RPi.GPIO as GPIO

# ==== Servo Setup ====
SERVO_PIN = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(SERVO_PIN, GPIO.OUT)
servo = GPIO.PWM(SERVO_PIN, 50)  # 50Hz
servo.start(0)

def open_door():
    print("[INFO] Opening door...")
    servo.ChangeDutyCycle(7.5)  # adjust if needed for your servo's open position
    time.sleep(1.5)
    servo.ChangeDutyCycle(2.5)  # adjust for closed position
    time.sleep(0.5)
    servo.ChangeDutyCycle(0)    # stop signal

# ==== Face Recognition Setup ====
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read('trainer.yml')
cascadePath = "haarcascade_frontalface_default.xml"
faceCascade = cv2.CascadeClassifier(cascadePath)

names = {}
labels_path = "labels.txt"
if os.path.exists(labels_path):
    with open(labels_path, "r") as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            name = line.strip()
            names[i] = name

# ==== State Tracking ====
allow_unknowns = False
unknown_detected = False
last_alert_time = datetime.min
alert_interval = timedelta(seconds=10)

# ==== Alert Function ====
def send_alert(image_path, timestamp):
    print(f"[INFO] Alert triggered at {timestamp}")
    # Upload or log image here if needed
    # Example: requests.post("http://your-server/api", files={"image": open(image_path, "rb")})

def send_and_maybe_open_door(image_path, timestamp):
    global unknown_detected
    send_alert(image_path, timestamp)
    unknown_detected = True
    update_status("Unknown detected. Waiting for response...")
    time.sleep(5)  # 5-second buffer
    if allow_unknowns:
        open_door()
        update_status("Door opened automatically for unknown.")

# ==== Face Recognition Loop ====
def run_recognition():
    global last_alert_time

    cam = cv2.VideoCapture(0)
    cam.set(3, 640)  # width
    cam.set(4, 480)  # height

    while True:
        ret, frame = cam.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = faceCascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)

        for (x, y, w, h) in faces:
            id_, confidence = recognizer.predict(gray[y:y+h, x:x+w])

            if confidence < 60:
                name = names.get(id_, "Unknown")
                color = (0, 255, 0)
                label = f"{name} ({round(100 - confidence)}%)"
            else:
                name = "Unknown"
                color = (0, 0, 255)
                label = f"Unknown ({round(100 - confidence)}%)"

                now = datetime.now()
                if now - last_alert_time > alert_interval:
                    timestamp_str = now.strftime('%Y%m%d_%H%M%S')
                    image_path = f"intruder_{timestamp_str}.jpg"
                    cv2.imwrite(image_path, frame)
                    threading.Thread(target=send_and_maybe_open_door, args=(image_path, now)).start()
                    last_alert_time = now

            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            cv2.putText(frame, label, (x+5, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

        cv2.imshow('Camera', frame)
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

    cam.release()
    cv2.destroyAllWindows()

def start_recognition_thread():
    threading.Thread(target=run_recognition, daemon=True).start()

# ==== GUI Setup ====
def update_status(text):
    status_label.config(text=f"🔔 {text}")

def toggle_unknowns():
    global allow_unknowns
    allow_unknowns = not allow_unknowns
    toggle_btn.config(text=f"Allow Unknowns: {'ON' if allow_unknowns else 'OFF'}")
    update_status("Unknown access permission changed.")

def manual_open():
    global unknown_detected
    if unknown_detected:
        open_door()
        update_status("Door manually opened.")
        unknown_detected = False
    else:
        messagebox.showinfo("Info", "No unknown detected.")

def create_gui():
    global toggle_btn, status_label

    root = tk.Tk()
    root.title("Pi Security Cam")
    root.geometry("360x450")
    root.configure(bg="#1e1e1e")
    root.resizable(False, False)

    tk.Label(root, text="Pi Security", font=("Helvetica", 24, "bold"),
             bg="#1e1e1e", fg="white").pack(pady=20)

    tk.Button(root, text="📷 Start Camera", command=start_recognition_thread,
              font=("Helvetica", 14), bg="#2196F3", fg="white", width=20, height=2).pack(pady=10)

    toggle_btn = tk.Button(root, text="Allow Unknowns: OFF", command=toggle_unknowns,
                           font=("Helvetica", 12), bg="#FFC107", fg="black", width=20, height=2)
    toggle_btn.pack(pady=10)

    tk.Button(root, text="🔓 Open Door", command=manual_open,
              font=("Helvetica", 14), bg="#4CAF50", fg="white", width=20, height=2).pack(pady=10)

    status_label = tk.Label(root, text="System ready.", font=("Helvetica", 10),
                            bg="#1e1e1e", fg="lightgray")
    status_label.pack(side="bottom", pady=20)

    root.mainloop()

# ==== Safe GPIO Cleanup ====
import atexit
atexit.register(lambda: (servo.stop(), GPIO.cleanup(), print("GPIO cleaned up.")))

# ==== Start GUI ====
create_gui()
