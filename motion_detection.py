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
last_state_change = time.time()
pir_cooldown = 5  # seconds
motion_timeout = 30  # Force reset motion status if stuck for this many seconds

print("PIR sensor calibrating - please wait 10 seconds...")
time.sleep(10)  # Reduced calibration time from 60 to 10 seconds
print("PIR sensor ready")

try:
    window_created = False
    
    while True:
        # Read current state
        current_state = GPIO.input(PIR_PIN)
        current_time = time.time()
        
        # Print the raw sensor value every 5 seconds for debugging
        if int(current_time) % 5 == 0 and current_time % 1 < 0.1:
            print(f"Current PIR value: {current_state}")
        
        # Force reset if motion has been active too long
        if motion_active and (current_time - last_state_change) > motion_timeout:
            print(f"Motion detection stuck ON for {motion_timeout} seconds - forcing reset")
            motion_active = False
            last_state_change = current_time
        
        # Process motion detection
        if current_state == 1:  # Motion detected (HIGH)
            if not motion_active:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{timestamp}] MOTION DETECTED!")
                motion_active = True
                last_state_change = current_time
                last_motion_time = current_time  # Only update when motion starts
                
            # Start camera if not already active
            if not camera_active:
                print("Activating camera...")
                picam.start()
                camera_active = True
        else:  # No motion (LOW)
            if motion_active:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{timestamp}] Motion stopped")
                motion_active = False
                last_state_change = current_time
        
        # Camera control logic - Add debug info
        if camera_active and not current_state:
            print(f"Time since last motion: {current_time - last_motion_time:.1f}s (need {pir_cooldown}s)")

        # Only stop camera if no motion AND cooldown period passed
        if camera_active and not current_state and (current_time - last_motion_time) > pir_cooldown:
            print("No motion for", pir_cooldown, "seconds. Stopping camera...")
            picam.stop()
            camera_active = False
            if window_created:
                cv2.destroyAllWindows()
                window_created = False
        
        # Display frame if camera is active
        if camera_active:
            frame = picam.capture_array()
            
            # Add visual indicators
            if motion_active:
                cv2.circle(frame, (frame.shape[1] - 30, 30), 15, (0, 0, 255), -1)
                cv2.putText(frame, "MOTION DETECTED", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            else:
                cv2.circle(frame, (frame.shape[1] - 30, 30), 15, (0, 255, 0), -1)
                cv2.putText(frame, "NO MOTION", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
            # Add PIR state and timestamp
            pir_state_text = f"PIR: {current_state}"
            cv2.putText(frame, pir_state_text, (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(frame, timestamp, (10, frame.shape[0] - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            cv2.imshow("Live Feed", frame)
            window_created = True
            
        # Exit on 'q' key press
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
            
        time.sleep(0.1)
        
except KeyboardInterrupt:
    print("Program stopped by user")
finally:
    if camera_active:
        picam.stop()
    GPIO.cleanup()
    cv2.destroyAllWindows()
    print("Cleanup complete")
