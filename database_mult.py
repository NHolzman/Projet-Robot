import socket
import sqlite3
import json
import threading
import time
from pynput import keyboard
import RPi.GPIO as GPIO

# =========================
# CONFIG
# =========================
ROBOT_ID = "robot_master"

HOST = "0.0.0.0"
PORT = 5000

SPEED = 100

# State filtering (IMPORTANT)
STATE_CONFIRM_TIME = 0.25  # tweak 0.15–0.5s depending on responsiveness

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
# DATABASE
# =========================
conn = sqlite3.connect("robot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS robot_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    robot_id TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,

    base_state TEXT,

    motor1_speed INTEGER,
    motor2_speed INTEGER,

    motor1_dir INTEGER,
    motor2_dir INTEGER
)
""")
conn.commit()

db_lock = threading.Lock()

def log_state():
    with db_lock:
        cursor.execute("""
            INSERT INTO robot_state (
                robot_id,
                base_state,
                motor1_speed,
                motor2_speed,
                motor1_dir,
                motor2_dir
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            ROBOT_ID,
            current_state,
            motor1_speed,
            motor2_speed,
            motor1_dir,
            motor2_dir
        ))
        conn.commit()

# =========================
# NETWORK SERVER
# =========================
def handle_client(client):
    buffer = ""

    while True:
        try:
            data = client.recv(1024).decode()
            if not data:
                break

            buffer += data

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                parsed = json.loads(line)

                with db_lock:
                    cursor.execute("""
                        INSERT INTO robot_state (
                            robot_id,
                            base_state,
                            motor1_speed,
                            motor2_speed,
                            motor1_dir,
                            motor2_dir
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        parsed["robot_id"],
                        parsed["base_state"],
                        parsed["motor1_speed"],
                        parsed["motor2_speed"],
                        parsed["motor1_dir"],
                        parsed["motor2_dir"]
                    ))
                    conn.commit()

                print("Remote:", parsed)

        except:
            break

    client.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()

    print(f"[SERVER] Listening on {HOST}:{PORT}")

    while True:
        client, addr = server.accept()
        print(f"[CONNECTED] {addr}")

        thread = threading.Thread(target=handle_client, args=(client,))
        thread.daemon = True
        thread.start()

# =========================
# INPUT
# =========================
keys = {"w": False, "a": False, "s": False, "d": False}
running = True

# =========================
# ROBOT STATE
# =========================
motor1_dir = 0
motor2_dir = 0
motor1_speed = 0
motor2_speed = 0

current_state = "IDLE"
pending_state = "IDLE"
state_start_time = time.time()

last_logged_state = None

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
    global motor1_speed, motor2_speed, motor1_dir, motor2_dir

    motor1_speed = 0
    motor2_speed = 0

    motor1_dir = 0
    motor2_dir = 0

    pwm1.ChangeDutyCycle(0)
    pwm2.ChangeDutyCycle(0)

# =========================
# KEY EVENTS
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
# CONTROL LOOP (FILTERED STATE MACHINE)
# =========================
def control_loop():
    global current_state, pending_state, state_start_time, last_logged_state

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
        # STATE FILTERING (ALL STATES)
        # ------------------------
        if desired_state != pending_state:
            pending_state = desired_state
            state_start_time = now

        if (now - state_start_time) >= STATE_CONFIRM_TIME:
            current_state = pending_state

        # ------------------------
        # LOG ONLY STABLE CHANGES
        # ------------------------
        if current_state != last_logged_state:
            log_state()
            last_logged_state = current_state

        time.sleep(0.03)

# =========================
# START SYSTEM
# =========================
server_thread = threading.Thread(target=start_server)
server_thread.daemon = True
server_thread.start()

listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()

try:
    print("[MASTER ROBOT RUNNING]")
    print("WASD control | ESC to quit")

    control_thread = threading.Thread(target=control_loop)
    control_thread.start()
    control_thread.join()

finally:
    stop()
    pwm1.stop()
    pwm2.stop()
    GPIO.cleanup()
    conn.close()

    print("[SHUTDOWN COMPLETE]")