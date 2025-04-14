from gpiozero import Servo
from time import sleep

# Initialize the servo on GPIO17 (adjust pin if needed)
servo = Servo(17)

print("Moving servo to 90 degrees (fully right)...")
servo.value = 1  # Move to rightmost (approx. 90 degrees depending on servo)
sleep(1.5)

print("Moving servo back to -90 degrees (fully left)...")
servo.value = -1  # Move to leftmost position
sleep(1.5)

print("Test complete. Servo returned to original position.")
