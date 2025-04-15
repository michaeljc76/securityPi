from picamera2 import Picamera2
import cv2
import numpy as np
import time

# Motion detection config
motion_threshold = 500000  # Adjust this for sensitivity
motion_timeout = 5         # Time (in seconds) to keep showing video after last motion
prev_gray = None
last_motion_time = 0
camera_active = False

# Camera setup
picam = Picamera2()
config = picam.create_preview_configuration(main={"format": "RGB888", "size": (640, 480)})
picam.configure(config)
picam.start()

try:
    while True:
        frame = picam.capture_array()
        current_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if prev_gray is None:
            prev_gray = current_gray
            continue

        # Compute absolute difference between current frame and previous
        diff = cv2.absdiff(current_gray, prev_gray)
        _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
        motion_score = np.sum(thresh)

        current_time = time.time()
        if motion_score > motion_threshold:
            last_motion_time = current_time
            if not camera_active:
                print("Motion detected! Showing camera feed.")
                camera_active = True
        elif camera_active and (current_time - last_motion_time > motion_timeout):
            print("No motion. Hiding camera feed.")
            camera_active = False
            cv2.destroyWindow("Live Feed")

        if camera_active:
            cv2.imshow("Live Feed", frame)

        prev_gray = current_gray

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    cv2.destroyAllWindows()
