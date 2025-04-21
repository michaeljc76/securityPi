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

# PIR sensor variables
camera_active = False
last_motion_time = 0
pir_cooldown = 5  # seconds - adjust based on your needs
pir_stabilization_time = 2  # seconds - give PIR time to stabilize

print("PIR sensor warming up...")
time.sleep(pir_stabilization_time)  # Allow PIR sensor to stabilize
print("PIR sensor ready")

try:
    window_created = False
    
    while True:
        motion_detected = GPIO.input(PIR_PIN)
        current_time = time.time()
        
        # Motion detected logic with debouncing
        if motion_detected:
            last_motion_time = current_time
            if not camera_active:
                print("Motion detected! Activating camera...")
                picam.start()
                camera_active = True
                
        # Only turn off camera if no motion for pir_cooldown seconds
        elif camera_active and (current_time - last_motion_time) > pir_cooldown:
            print("No motion for", pir_cooldown, "seconds. Stopping camera...")
            picam.stop()
            camera_active = False
            if window_created:
                cv2.destroyAllWindows()
                window_created = False
        
        # Display frame if camera is active
        if camera_active:
            frame = picam.capture_array()
            cv2.imshow("Live Feed", frame)
            window_created = True
            
        # Check for quit key
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
            
        # Short delay to prevent CPU hogging
        time.sleep(0.1)
        
except KeyboardInterrupt:
    print("Program stopped by user")
finally:
    if camera_active:
        picam.stop()
    GPIO.cleanup()
    cv2.destroyAllWindows()
    print("Cleanup complete")
