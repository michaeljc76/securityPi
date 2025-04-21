import tkinter as tk
from tkinter import messagebox
import cv2
import numpy as np
import threading
import time
import RPi.GPIO as GPIO
from datetime import datetime, timedelta
from PIL import Image, ImageTk

# ===== GPIO Setup =====
SERVO_PIN = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(SERVO_PIN, GPIO.OUT)
servo = GPIO.PWM(SERVO_PIN, 50)
servo.start(0)

def open_door():
    print("[INFO] Door opening...")
    servo.ChangeDutyCycle(7.5)
    time.sleep(1.5)
    servo.ChangeDutyCycle(2.5)
    time.sleep(0.5)
    servo.ChangeDutyCycle(0)

# ===== Global States =====
allow_unknowns = False
unknown_detected = False
buffered = False
last_detection_time = datetime.min
buffer_duration = 5  # seconds

# ===== Face Detection =====
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
video = cv2.VideoCapture(0)

# ===== GUI Setup =====
root = tk.Tk()
root.title("Pi Security Cam")
root.geometry("360x560")
root.configure(bg="#1e1e1e")
root.resizable(False, False)

frame_label = tk.Label(root, bg="#1e1e1e")
frame_label.pack(pady=10)

status_label = tk.Label(root, text="System ready.", font=("Helvetica", 10), bg="#1e1e1e", fg="lightgray")
status_label.pack(pady=10)

def update_status(text):
    status_label.config(text=f"🔔 {text}")

def toggle_unknowns():
    global allow_unknowns
    allow_unknowns = not allow_unknowns
    toggle_btn.config(text=f"Allow Unknowns: {'ON' if allow_unknowns else 'OFF'}")
    update_status("Toggled unknowns permission.")

def manual_open():
    global unknown_detected, buffered
    if unknown_detected and buffered:
        open_door()
        update_status("Door opened manually.")
        unknown_detected = False
        buffered = False
    else:
        messagebox.showinfo("Info", "No unknowns in buffer.")

def process_frame():
    global unknown_detected, buffered, last_detection_time

    ret, frame = video.read()
    if not ret:
        return

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.2, 5)

    if len(faces) > 0:
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

        now = datetime.now()
        if (now - last_detection_time).total_seconds() > buffer_duration:
            unknown_detected = True
            buffered = True
            last_detection_time = now
            update_status("Unknown detected. Waiting for response...")

            def buffer_check():
                global unknown_detected, buffered
                time.sleep(buffer_duration)
                if allow_unknowns and unknown_detected:
                    open_door()
                    update_status("Door auto-opened for unknown.")
                buffered = False
                unknown_detected = False

            threading.Thread(target=buffer_check, daemon=True).start()

    # Show frame in GUI
    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(img)
    img = img.resize((320, 240))
    imgtk = ImageTk.PhotoImage(image=img)
    frame_label.imgtk = imgtk
    frame_label.configure(image=imgtk)

    root.after(10, process_frame)

# ===== Buttons =====
tk.Button(root, text="🔓 Open Door", command=manual_open,
          font=("Helvetica", 14), bg="#4CAF50", fg="white", width=20, height=2).pack(pady=10)

toggle_btn = tk.Button(root, text="Allow Unknowns: OFF", command=toggle_unknowns,
                       font=("Helvetica", 12), bg="#FFC107", fg="black", width=20, height=2)
toggle_btn.pack(pady=10)

# ===== Start Camera Loop =====
root.after(0, process_frame)

# ===== Safe Exit Cleanup =====
def cleanup():
    servo.stop()
    GPIO.cleanup()
    video.release()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", cleanup)
root.mainloop()
