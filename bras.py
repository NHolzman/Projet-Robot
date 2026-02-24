import RPi.GPIO as GPIO
import time

# Utilisation de la numérotation BCM (mode GPIO number plutôt que PIN number)
GPIO.setmode(GPIO.BCM)

# Choisir les GPIO pour les signaux
SERVO_PIN1 = 14
SERVO_PIN2 = 15
SERVO_PIN3 = 18
GPIO.setup(SERVO_PIN1, GPIO.OUT)
GPIO.setup(SERVO_PIN2, GPIO.OUT)
GPIO.setup(SERVO_PIN3, GPIO.OUT)

# Création des PWM à 50 Hz (standard servo)
pwm1 = GPIO.PWM(SERVO_PIN1, 50)
pwm1.start(0)
pwm2 = GPIO.PWM(SERVO_PIN2, 50)
pwm2.start(0)
pwm3 = GPIO.PWM(SERVO_PIN3, 50)
pwm3.start(0)

def set_angle(angle, pwm):
    # Conversion angle → DutyCycle
    duty = 2 + (angle / 18)  # approx pour SG90 (0°=2%, 90°=7%, 180°=12%)
    pwm.ChangeDutyCycle(duty)
    time.sleep(0.7)  # temps pour que le servo bouge
    pwm.ChangeDutyCycle(0)  # éviter vibrations

try:
    while True:
        set_angle(60, pwm1)
        set_angle(30, pwm2)
        set_angle(90, pwm3)
        time.sleep(0.1) # 100ms juste pour dire qu'on ne recommence pas tout de suite
        set_angle(90, pwm1)
        set_angle(60, pwm2)
        set_angle(110, pwm3)
        time.sleep(0.1)
        set_angle(150, pwm1)
        set_angle(120, pwm2)
        set_angle(130, pwm3)
        time.sleep(0.1)

except KeyboardInterrupt:
    pass

pwm1.stop()
pwm2.stop()
pwm3.stop()
GPIO.cleanup() # Défaire le setup des GPIO
