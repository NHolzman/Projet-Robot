
import RPi.GPIO as GPIO
import sys
import tty
import termios
import time

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
    GPIO.output(pin, GPIO.LOW)

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

# --- Function to read a single key ---
def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

# --- Main loop ---
try:
    print("Hold-key style motor control. Press 'q' to exit.")
    while True:
        key = getch()
        stop_motors()

        if key == "w":
            both_forward()
        elif key == "a":
            motor1_forward()
        elif key == "d":
            motor2_forward()
        elif key == "s":
            both_reverse()
        elif key == "q":
            break

        # Short sleep to allow visual motor movement
        time.sleep(0.1)

finally:
    stop_motors()
    GPIO.cleanup()
    print("GPIO cleaned up, program exited safely")