import RPi.GPIO as GPIO
import time

# Set up GPIO
BUZZER_PIN = 23
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUZZER_PIN, GPIO.OUT)

# Set up PWM on the buzzer pin at 1kHz frequency
pwm = GPIO.PWM(BUZZER_PIN, 1000)

try:
    pwm.start(50)  # 50% duty cycle
    print("Buzzing...")
    time.sleep(1)  # Buzz for 1 second
    pwm.stop()
    print("Stopped buzzing.")
finally:
    GPIO.cleanup()
