import socket
import json
import time
import threading
import RPi.GPIO as GPIO
from pynput import keyboard
 
# =========================
# CONFIG
# =========================
ROBOT_ID = "robot_1"   # change per robot (robot_2, robot_3, etc.)
 
MASTER_IP = "192.168.4.183"  # CHANGE to your master Pi IP
PORT = 5000
 
SPEED = 100
STATE_CONFIRM_TIME = 0.25
 
# =========================
# NETWORK
# =========================
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((MASTER_IP, PORT))
 
def send_state():
    data = {
        "robot_id": ROBOT_ID,
        "base_state": current_state,
        "motor1_speed": motor1_speed,
        "motor2_speed": motor2_speed,
        "motor1_dir": motor1_dir,
        "motor2_dir": motor2_dir
    }
 
    try:
        sock.send((json.dumps(data) + "\n").encode())
    except:
        pass
 
# =========================
# GPIO SETUP
# =========================
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
 
DIR1 = 22
PWM1 = 23
DIR2 = 24
PWM2 = 25
 
GPIO.setup(DIR1, GPIO.OUT)
GPIO.setup(DIR2, GPIO.OUT)
GPIO.setup(PWM1, GPIO.OUT)
GPIO.setup(PWM2, GPIO.OUT)
 
pwm1 = GPIO.PWM(PWM1, 1000)
pwm2 = GPIO.PWM(PWM2, 1000)
 
pwm1.start(0)
pwm2.start(0)
 
# =========================
# INPUT
# =========================
keys = {"w": False, "a": False, "s": False, "d": False}
running = True
 
# =========================
# STATE
# =========================
motor1_dir = 0
motor2_dir = 0
motor1_speed = 0
motor2_speed = 0
 
current_state = "IDLE"
pending_state = "IDLE"
state_start_time = time.time()
 
last_sent_state = None
 
# =========================
# MOTOR CONTROL
# =========================
def forward():
    global motor1_dir, motor2_dir, motor1_speed, motor2_speed
 
    motor1_dir = 1
    motor2_dir = 1
    motor1_speed = SPEED
    motor2_speed = SPEED
 
    GPIO.output(DIR1, GPIO.HIGH)
    GPIO.output(DIR2, GPIO.HIGH)
 
    pwm1.ChangeDutyCycle(SPEED)
    pwm2.ChangeDutyCycle(SPEED)
 
def reverse():
    global motor1_dir, motor2_dir, motor1_speed, motor2_speed
 
    motor1_dir = 0
    motor2_dir = 0
    motor1_speed = SPEED
    motor2_speed = SPEED
 
    GPIO.output(DIR1, GPIO.LOW)
    GPIO.output(DIR2, GPIO.LOW)
 
    pwm1.ChangeDutyCycle(SPEED)
    pwm2.ChangeDutyCycle(SPEED)
 
def left():
    global motor1_dir, motor2_dir, motor1_speed, motor2_speed
 
    motor1_dir = 1
    motor2_dir = 0
    motor1_speed = SPEED
    motor2_speed = SPEED
 
    GPIO.output(DIR1, GPIO.HIGH)
    GPIO.output(DIR2, GPIO.LOW)
 
    pwm1.ChangeDutyCycle(SPEED)
    pwm2.ChangeDutyCycle(SPEED)
 
def right():
    global motor1_dir, motor2_dir, motor1_speed, motor2_speed
 
    motor1_dir = 0
    motor2_dir = 1
    motor1_speed = SPEED
    motor2_speed = SPEED
 
    GPIO.output(DIR1, GPIO.LOW)
    GPIO.output(DIR2, GPIO.HIGH)
 
    pwm1.ChangeDutyCycle(SPEED)
    pwm2.ChangeDutyCycle(SPEED)
 
def stop():
    global motor1_dir, motor2_dir, motor1_speed, motor2_speed
 
    motor1_dir = 0
    motor2_dir = 0
    motor1_speed = 0
    motor2_speed = 0
 
    pwm1.ChangeDutyCycle(0)
    pwm2.ChangeDutyCycle(0)
 
# =========================
# INPUT HANDLING
# =========================
def on_press(key):
    global running
 
    try:
        if key.char in keys:
            keys[key.char] = True
    except:
        pass
 
    if key == keyboard.Key.esc:
        running = False
        return False
 
def on_release(key):
    try:
        if key.char in keys:
            keys[key.char] = False
    except:
        pass
 
# =========================
# CONTROL LOOP (same logic as master)
# =========================
def control_loop():
    global current_state, pending_state, state_start_time, last_sent_state
 
    while running:
 
        # ------------------------
        # DESIRED STATE
        # ------------------------
        if keys["w"]:
            forward()
            desired_state = "FORWARD"
 
        elif keys["s"]:
            reverse()
            desired_state = "REVERSE"
 
        elif keys["a"]:
            left()
            desired_state = "LEFT"
 
        elif keys["d"]:
            right()
            desired_state = "RIGHT"
 
        else:
            stop()
            desired_state = "IDLE"
 
        now = time.time()
 
        # ------------------------
        # STATE FILTER (same as master)
        # ------------------------
        if desired_state != pending_state:
            pending_state = desired_state
            state_start_time = now
 
        if (now - state_start_time) >= STATE_CONFIRM_TIME:
            current_state = pending_state
 
        # ------------------------
        # SEND ONLY ON CHANGE
        # ------------------------
        if current_state != last_sent_state:
            send_state()
            last_sent_state = current_state
 
        time.sleep(0.03)
 
# =========================
# START
# =========================
listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()
 
try:
    print(f"[{ROBOT_ID} STARTED]")
    control_thread = threading.Thread(target=control_loop)
    control_thread.start()
    control_thread.join()
 
finally:
    stop()
    pwm1.stop()
    pwm2.stop()
    GPIO.cleanup()
    sock.close()
 
    print("[CLIENT SHUTDOWN]")