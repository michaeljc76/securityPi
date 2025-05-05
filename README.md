# securityPi
Steven Le, Jay Patel, Michael Crowley

securityPi is a Smart Door Lock System for Raspberry Pi that uses face detection/recognition to control a servo which can be used to lock/unlock doors or compartments. It features a Tkinter-based GUI, live camera feed, PIR motion sensing, and alerts. When a known person is recognized, the door unlocks, and if an unknown face is detected, the system sounds a buzzer, lights an LED, and sends an email alert along with an image of the unidentifed face. This project combines MediaPipe and face_recognition libraries for face detection and recognition.

## Features
- Face Detection & Recognition: Detect faces in real time via google's mediapipe and identify known users using the face_recognition library.
- Live Camera Feed: Display the camera view in a Tkinter GUI, with overlays marking detected faces.
- Motion-Activated: A PIR motion sensor triggers the camera when someone approaches, saving power and avoiding constant video processing.
- Door Control: Uses a 20kg servo motor to unlock/open the door when a recognized face is seen.
- Alerts: Built-in buzzer and LED to signal events (LED turns green or red and buzzer turns off or on if person is recognized/unrecognized).
- Email Notifications: Sends an alert via Gmail SMTP when an unknown person is detected (requires a Gmail app password)

## Requirements
- Raspberry Pi 4 running Raspberry Pi OS.
- Raspberry Pi camera Module v2 (or compatible), connected to the Pi’s CSI port.
- PIR motion sensor (e.g. HC-SR501) to detect motion.
- Servo motor to actuate the door lock.
- LED and buzzer (with resistors).
- Misc: Jumper wires, breadboard, and a Gmail account for notifications.

## Installing Dependencies
Python requirements: can be installed by running `pip install -r requirements.txt`

(You may also need to install dlib or cmake if prompted since face_recognition requires dlib).

## Adding Faces
To recognize people, create a folder (e.g. faces/) and put one image of each person. Name the files clearly, and modify the program to use these faces. When you run the program, it will load these images, compute face encodings, and label recognized faces accordingly. Ensure good lighting and frontal faces for accurate encoding.

## Configuring Email Alerts
Edit emails.txt to change the sending and recieving emails, along with the sender's password

## Running the Project
Once everything is set up, run the main program:
```
python3 detect_gui.py
```
You may need sudo if accessing GPIO without permissions. The GUI window will open, showing the camera feed. The program waits for PIR motion, then analyzes faces. On recognized faces, it will rotate the servo 90 degrees to unlock, otherwise it will beep and flash the LED, and send an email to your configured address.

## Troubleshooting
- Camera not working: Ensure the camera is enabled in raspi-config (Interface Options → Camera) and that the ribbon is seated correctly. Test with libcamera-hello.
- GPIO Errors: If you see permission errors, run with sudo or add your user to the gpio group. Ensure no other process is using the same GPIO pins.
- Face Recognition Too Slow: Raspberry Pi may struggle with heavy models. Try reducing frame size or switching to a faster model. Mediapipe and face_detection proved fast and effective in our tests.
- PIR False Triggers: Adjust the PIR sensor’s dials and verify wiring.
- Servo Jittering: Check the power supply. If the servo draws too much current, use a separate 5V supply.
- Email Not Sent: Verify SMTP credentials and network connectivity. Google may block sign-ins, so use an app password.