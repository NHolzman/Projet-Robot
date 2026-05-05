import pigpio
import time
from pynput import keyboard

# ================== CONFIGURATION ==================
SERVO_PIN1 = 2
SERVO_PIN2 = 3
SERVO_PIN3 = 4

# Global limits
MIN_PW = 500   # 0 degrees
MAX_PW = 2500  # 180 degrees

# Specific limits for Servo 0
SERVO0_MIN = 1600
SERVO0_MAX = 2400

STEP_SIZE = 100 

class ServoArm:
    def __init__(self):
        self.pi = pigpio.pi()
        if not self.pi.connected:
            print("Could not connect to pigpiod. Did you run 'sudo pigpiod'?")
            exit()
            
        self.pins = [SERVO_PIN1, SERVO_PIN2, SERVO_PIN3]
        # Initialize Servo 0 within its specific range (e.g., 2000us)
        self.current_pws = [2000, 1500, 1500] 
        
        for i, pin in enumerate(self.pins):
            self.pi.set_servo_pulsewidth(pin, self.current_pws[i])

    def update_servo(self, index, delta):
        new_pw = self.current_pws[index] + delta
        
        # --- Range Logic ---
        if index == 0:
            # Apply specific constraints for Servo 0
            new_pw = max(SERVO0_MIN, min(SERVO0_MAX, new_pw))
        else:
            # Apply global constraints for all other servos
            new_pw = max(MIN_PW, min(MAX_PW, new_pw))
        
        self.current_pws[index] = new_pw
        self.pi.set_servo_pulsewidth(self.pins[index], new_pw)
        print(f"Servo {index} Pulse Width: {new_pw}")

    def cleanup(self):
        for pin in self.pins:
            self.pi.set_servo_pulsewidth(pin, 0) 
        self.pi.stop()

# ================== LOGIC ==================
arm = ServoArm()

def on_press(key):
    try:
        if key == keyboard.Key.left:    arm.update_servo(0, -STEP_SIZE)
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
    print(f"Control Ready. Servo 0 limited to {SERVO0_MIN}-{SERVO0_MAX}. ESC to Quit.")
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()
        arm.cleanup()
