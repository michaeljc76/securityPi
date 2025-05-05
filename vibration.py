from gpiozero import Button

vibration_sensor = Button(17)

def vibration_detected():
    print("⚠ ALERT: Security system is MOVING! Possible tampering detected.")

vibration_sensor.when_pressed = vibration_detected

input("Press Enter to exit...\n")
