from picamera2 import Picamera2
import cv2
import RPi.GPIO as GPIO
import time
import datetime

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
motion_active = False
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
        
        # Update motion status with visible indication
        if motion_detected:
            if not motion_active:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{timestamp}] MOTION DETECTED!")
                motion_active = True
            last_motion_time = current_time
            
            # Start camera if not already active
            if not camera_active:
                print("Activating camera...")
                picam.start()
                camera_active = True
        else:
            if motion_active:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{timestamp}] Motion stopped")
                motion_active = False
        
        # Only turn off camera if no motion for pir_cooldown seconds
        if not motion_detected and camera_active and (current_time - last_motion_time) > pir_cooldown:
            print("No motion for", pir_cooldown, "seconds. Stopping camera...")
            picam.stop()
            camera_active = False
            if window_created:
                cv2.destroyAllWindows()
                window_created = False
        
        # Display frame if camera is active
        if camera_active:
            frame = picam.capture_array()
            
            # Add motion indicator to the frame
            if motion_active:
                # Draw a red circle in the top-right corner to indicate motion
                cv2.circle(frame, (frame.shape[1] - 30, 30), 15, (0, 0, 255), -1)
                # Add "MOTION DETECTED" text
                cv2.putText(frame, "MOTION DETECTED", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                # Add timestamp
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cv2.putText(frame, timestamp, (10, frame.shape[0] - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
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
