import RPi.GPIO as GPIO
import time
import keyboard  # pip install keyboard

# --- GPIO setup ---
GPIO.setmode(GPIO.BCM)

# Motor 1
DIR1 = 22
VIT1 = 23

# Motor 2
DIR2 = 24
VIT2 = 25

pins = [DIR1, VIT1, DIR2, VIT2]
for pin in pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)  # Ensure motors start OFF

# --- Helper functions ---
def stop_motors():
    for pin in pins:
        GPIO.output(pin, GPIO.LOW)

def motor1_forward():
    GPIO.output(DIR1, GPIO.HIGH)
    GPIO.output(VIT1, GPIO.HIGH)

def motor1_reverse():
    GPIO.output(DIR1, GPIO.LOW)
    GPIO.output(VIT1, GPIO.HIGH)

def motor2_forward():
    GPIO.output(DIR2, GPIO.HIGH)
    GPIO.output(VIT2, GPIO.HIGH)

def motor2_reverse():
    GPIO.output(DIR2, GPIO.LOW)
    GPIO.output(VIT2, GPIO.HIGH)

def both_forward():
    motor1_forward()
    motor2_forward()

def both_reverse():
    motor1_reverse()
    motor2_reverse()

# --- Main loop ---
try:
    print("Keyboard motor control started. Press ESC to exit.")
    while True:
        key = keyboard.read_event()  # Waits for key press
        if key.event_type == keyboard.KEY_DOWN:
            stop_motors()  # Stop previous action
            if key.name == "w":
                both_forward()
                print("Both motors forward")
            elif key.name == "a":
                motor1_forward()
                print("Motor 1 forward")
            elif key.name == "d":
                motor2_forward()
                print("Motor 2 forward")
            elif key.name == "s":
                both_reverse()
                print("Both motors reverse")
            elif key.name == "esc":
                break

finally:
    stop_motors()
    GPIO.cleanup()
    print("GPIO cleaned up, program exited safely")