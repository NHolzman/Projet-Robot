import pigpio
import time
from pynput import keyboard

# ================== CONFIGURATION ==================
SERVO_PIN1 = 2
SERVO_PIN2 = 3
SERVO_PIN3 = 4

# pigpio uses pulse width in microseconds (usually 500 to 2500)
MIN_PW = 500   # 0 degrees
MAX_PW = 2500  # 180 degrees
STEP_SIZE = 100 # Change in pulse width per press

class ServoArm:
    def __init__(self):
        self.pi = pigpio.pi()
        if not self.pi.connected:
            print("Could not connect to pigpiod. Did you run 'sudo pigpiod'?")
            exit()
            
        self.pins = [SERVO_PIN1, SERVO_PIN2, SERVO_PIN3]
        self.current_pws = [1500, 1500, 1500] # Start at 90 degrees (1500us)
        
        for i, pin in enumerate(self.pins):
            self.pi.set_servo_pulsewidth(pin, self.current_pws[i])

    def update_servo(self, index, delta):
        new_pw = self.current_pws[index] + delta
        new_pw = max(MIN_PW, min(MAX_PW, new_pw)) # Clamp
        self.current_pws[index] = new_pw
        self.pi.set_servo_pulsewidth(self.pins[index], new_pw)
        print(f"Servo {index} Pulse Width: {new_pw}")

    def cleanup(self):
        for pin in self.pins:
            self.pi.set_servo_pulsewidth(pin, 0) # Stop pulses
        self.pi.stop()

# ================== LOGIC ==================
arm = ServoArm()

def on_press(key):
    try:
        if key == keyboard.Key.left:  arm.update_servo(0, -STEP_SIZE)
        elif key == keyboard.Key.right: arm.update_servo(0, STEP_SIZE)
        elif key == keyboard.Key.up:    arm.update_servo(1, STEP_SIZE)
        elif key == keyboard.Key.down:  arm.update_servo(1, -STEP_SIZE)
        elif hasattr(key, 'char'):
            if key.char == 'w': arm.update_servo(2, STEP_SIZE)
            elif key.char == 's': arm.update_servo(2, -STEP_SIZE)
    except Exception as e:
        print(f"Error: {e}")

def on_release(key):
    if key == keyboard.Key.esc: return False

if __name__ == "__main__":
    print("Control Ready. ESC to Quit.")
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()
        arm.cleanup()
