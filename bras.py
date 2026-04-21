import RPi.GPIO as GPIO
import time

# Utilisation de la numérotation BCM (mode GPIO number plutôt que PIN number)
GPIO.setmode(GPIO.BCM)

# Choisir les GPIO pour les signaux
SERVO_PIN1 = 2
SERVO_PIN2 = 3
SERVO_PIN3 = 4
GPIO.setup(SERVO_PIN1, GPIO.OUT)
GPIO.setup(SERVO_PIN2, GPIO.OUT)
GPIO.setup(SERVO_PIN3, GPIO.OUT)

# Création des PWM à 50 Hz (standard servo)
pwm1 = GPIO.PWM(SERVO_PIN1, 62)
pwm1.start(0)
pwm2 = GPIO.PWM(SERVO_PIN2, 62)
pwm2.start(0)
pwm3 = GPIO.PWM(SERVO_PIN3, 62)
pwm3.start(0)

def set_angle(angle, pwm):
    # Conversion angle → DutyCycle
    duty = 2 + (angle / 18)  # approx pour SG90 (0°=2%, 90°=7%, 180°=12%)
    pwm.ChangeDutyCycle(duty)
    time.sleep(0.7)  # temps pour que le servo bouge
    pwm.ChangeDutyCycle(0)  # éviter vibrations

def set_armServo(angle1, angle2, angle3, delay):
    set_angle(angle1, pwm1)
    set_angle(angle2, pwm2)
    set_angle(angle3, pwm3)
    time.sleep(delay)

try:
    while True:
        set_armServo(0, 15, 0, 0.3)
        set_armServo(0, 90, 0, 0.3)
        set_armServo(0, 165, 0, 0.3)

except KeyboardInterrupt:
    pass
pwm1.stop()
pwm2.stop()
pwm3.stop()
GPIO.cleanup() # Défaire le setup des GPIO
