from picamera2 import Picamera2
import cv2
import RPi.GPIO as GPIO
import time

# GPIO setup
PIR_PIN = 4  # Adjust this to your PIR sensor's GPIO pin
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIR_PIN, GPIO.IN)

# Camera setup
picam = Picamera2()
config = picam.create_preview_configuration(main={"format": "RGB888", "size": (640, 480)})
picam.configure(config)

camera_active = False

try:
    while True:
        motion_detected = GPIO.input(PIR_PIN)

        if motion_detected and not camera_active:
            print("Motion detected! Activating camera...")
            picam.start()
            camera_active = True

        elif not motion_detected and camera_active:
            print("No motion. Stopping camera...")
            camera_active = False
            picam.stop()
            cv2.destroyWindow("Live Feed")

        if camera_active:
            frame = picam.capture_array()
            cv2.imshow("Live Feed", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    picam.stop()
    GPIO.cleanup()
    cv2.destroyAllWindows()
