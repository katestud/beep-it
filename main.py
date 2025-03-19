from machine import I2C, Pin, ADC, PWM
from i2c_lcd import I2cLcd
import time
from imu import MPU6050
import math
import random
import sounds

# Pin Definitions
TOUCH_PIN = 15
MPU_SDA_PIN = 2
MPU_SCL_PIN = 3
LCD_SDA_PIN = 4
LCD_SCL_PIN = 5
SLIDING_POTENTIOMETER_PIN = 28
JOYSTICK_X_PIN = 27
JOYSTICK_Y_PIN = 26
BUZZER_PIN = 13

# LCD I2C Settings
LCD_I2C_ADDR = 0x27
LCD_I2C_NUM_ROWS = 2
LCD_I2C_NUM_COLS = 16

# Debounce settings (in seconds)
DEBOUNCE_TIME = 0.5
SHAKE_DEBOUNCE = 0.8  # Longer debounce for shake to ensure complete movement
SLIDER_DEBOUNCE = 0.3
JOYSTICK_DEBOUNCE = 0.4

# Debug mode
DEBUG = False

# Prototype mode (when shake doesn't really work)
PROTOTYPE_MODE = False

# Slider settings
SLIDER_THRESHOLD = 1000  # Minimum change to detect movement
SLIDER_PARTIAL_THRESHOLD = 500  # Minimum change for partial slide
SLIDER_MIN_MOVEMENT = 100  # Minimum movement in one direction to count

class GameAction:
    TOUCH = "BEEP IT!"
    FLICK = "FLICK IT!"
    SHAKE = "SHAKE IT!"
    SLIDE = "SLIDE IT!"

    @classmethod
    def get_random_action(cls):
        actions = [cls.TOUCH, cls.FLICK, cls.SHAKE, cls.SLIDE]
        if PROTOTYPE_MODE:
            actions.remove(cls.SHAKE)
        return random.choice(actions)

class GameState:
    def __init__(self):
        self.is_game_on = False
        self.score = 0
        self.mistakes = 0
        self.last_action_time = 0
        self.current_action = None
        self.action_timeout = 3.0  # seconds to complete the action
        self.last_prompt_time = 0
        self.prompt_interval = 5.0  # seconds between prompts
        self.input_manager = None  # Will be set when game starts

    def start_game(self):
        self.is_game_on = True
        self.score = 0
        self.mistakes = 0
        self.last_action_time = time.time()
        self.current_action = None
        print("\nWelcome to Beep It!")
        print("Follow the prompts!")
        self.generate_new_action()

    def stop_game(self):
        self.is_game_on = False
        if self.input_manager:
          self.input_manager.lcd_display.clear()
          self.input_manager.lcd_display.putstr(f"Final score: {self.score}")
          self.input_manager.lcd_display.move_to(0, 1)
          self.input_manager.lcd_display.putstr("Beep to start")
        print(f"\nGame ended! Final score: {self.score}")

    def generate_new_action(self):
        self.current_action = GameAction.get_random_action()
        self.last_action_time = time.time()
        print(f"\n{self.current_action}")
        self.last_prompt_time = time.time()
        # Reset debounce timers when generating a new action
        if self.input_manager:
            sounds.playsong(self.input_manager.buzzer, self.current_action)
            self.input_manager.lcd_display.clear()
            self.input_manager.lcd_display.putstr(self.current_action)
            self.input_manager.reset_debounce_timers()


    def check_action(self, action_type):
        if not self.current_action:
            return False

        current_time = time.time()
        if current_time - self.last_action_time > self.action_timeout:
            print("Too slow! Try again!")
            self.generate_new_action()
            return False

        return action_type == self.current_action

    def handle_correct_action(self):
        self.score += 1
        print(f"Correct! Score: {self.score}")
        if self.input_manager:
            self.input_manager.lcd_display.clear()
            self.input_manager.lcd_display.putstr(f"Correct! Score: {self.score}")
            time.sleep(0.5)

        self.generate_new_action()

    def handle_wrong_action(self, action):
        self.mistakes += 1
        print(f"Wrong action: {action}! Try again!")
        if self.input_manager:
            self.input_manager.lcd_display.clear()
            self.input_manager.lcd_display.putstr(f"Wrong action: {action}! Try again!")
            time.sleep(0.5)
            self.input_manager.lcd_display.clear()
            self.input_manager.lcd_display.putstr(self.current_action)
            sounds.playsong(self.input_manager.buzzer, "FAILURE")
class InputManager:
    def __init__(self):
        # Touch Sensor Setup
        self.touch_sensor = Pin(TOUCH_PIN, Pin.IN)
        self.last_touch_time = 0
        self.last_touch_state = False

        # IMU Setup
        self.i2c1_sensor = I2C(1, sda=Pin(MPU_SDA_PIN), scl=Pin(MPU_SCL_PIN), freq=400000)
        self.mpu_sensor = MPU6050(self.i2c1_sensor)
        self.last_shake_time = 0
        self.shake_detected = False

        # LCD Setup
        self.i2c0_sensor = I2C(0, sda=Pin(LCD_SDA_PIN), scl=Pin(LCD_SCL_PIN), freq=400000)
        self.lcd_display = I2cLcd(self.i2c0_sensor, LCD_I2C_ADDR, LCD_I2C_NUM_ROWS, LCD_I2C_NUM_COLS)

        # Buzzer Setup
        self.buzzer = PWM(Pin(BUZZER_PIN))

        # Joystick Setup
        self.vrx = ADC(Pin(JOYSTICK_X_PIN))
        self.vry = ADC(Pin(JOYSTICK_Y_PIN))
        self.joystick_x_position = self.vrx.read_u16()
        self.joystick_y_position = self.vry.read_u16()
        self.last_joystick_time = 0
        self.joystick_detected = False

        # Slider Setup
        self.slider_sensor = ADC(Pin(SLIDING_POTENTIOMETER_PIN))
        self.slider_value = self.slider_sensor.read_u16()
        self.last_slider_time = 0
        self.slider_detected = False
        self.slider_direction = 0  # 1 for right, -1 for left
        self.slider_cumulative = 0  # Track cumulative movement
        if DEBUG:
            print(f"Initial slider value: {self.slider_value}")

    def reset_debounce_timers(self):
        """Reset all debounce timers to allow immediate input detection"""
        current_time = time.time()
        self.last_touch_time = current_time
        self.last_shake_time = current_time
        self.last_joystick_time = current_time
        self.last_slider_time = current_time
        self.shake_detected = False
        self.joystick_detected = False
        self.slider_detected = False
        self.slider_direction = 0
        self.slider_cumulative = 0
        # Update all sensor values to prevent false triggers
        self.slider_value = self.slider_sensor.read_u16()
        self.joystick_x_position = self.vrx.read_u16()
        self.joystick_y_position = self.vry.read_u16()
        self.last_touch_state = False

    def is_touched(self):
        current_time = time.time()
        current_state = self.touch_sensor.value()

        # Only trigger on rising edge (touch start) and after debounce
        if current_state and not self.last_touch_state and (current_time - self.last_touch_time) > DEBOUNCE_TIME:
            self.last_touch_time = current_time
            self.last_touch_state = current_state
            return True
        elif not current_state:
            self.last_touch_state = False

        return False

    def is_shaking(self, threshold=2.0):
        current_time = time.time()
        if current_time - self.last_shake_time < SHAKE_DEBOUNCE:
            return False

        xAccel = self.mpu_sensor.accel.x
        yAccel = self.mpu_sensor.accel.y
        zAccel = self.mpu_sensor.accel.z
        accel_magnitude = math.sqrt(xAccel**2 + yAccel**2 + zAccel**2)

        if accel_magnitude > threshold and not self.shake_detected:
            self.last_shake_time = current_time
            self.shake_detected = True
            return True
        elif accel_magnitude <= threshold:
            self.shake_detected = False

        return False

    def is_joystick_moved(self, threshold=1000):
        current_time = time.time()
        if current_time - self.last_joystick_time < JOYSTICK_DEBOUNCE:
            return False, self.joystick_x_position, self.joystick_y_position

        x_axis = self.vrx.read_u16()
        y_axis = self.vry.read_u16()

        x_moved = abs(x_axis - self.joystick_x_position) > threshold
        y_moved = abs(y_axis - self.joystick_y_position) > threshold

        if (x_moved or y_moved) and not self.joystick_detected:
            self.joystick_x_position = x_axis
            self.joystick_y_position = y_axis
            self.last_joystick_time = current_time
            self.joystick_detected = True
            return True, x_axis, y_axis
        elif not x_moved and not y_moved:
            self.joystick_detected = False

        return False, x_axis, y_axis

    def is_slider_moved(self, threshold=SLIDER_THRESHOLD):
        current_time = time.time()
        if current_time - self.last_slider_time < SLIDER_DEBOUNCE:
            return False, self.slider_value

        current_value = self.slider_sensor.read_u16()
        diff = current_value - self.slider_value

        # Determine direction of movement
        if diff > SLIDER_MIN_MOVEMENT:
            direction = 1  # Moving right
        elif diff < -SLIDER_MIN_MOVEMENT:
            direction = -1  # Moving left
        else:
            direction = 0  # No significant movement

        # Update cumulative movement if moving in the same direction
        if direction != 0:
            if direction == self.slider_direction:
                self.slider_cumulative += abs(diff)
            else:
                self.slider_cumulative = abs(diff)
            self.slider_direction = direction
        else:
            self.slider_direction = 0

        # Only print debug info if we're expecting a slide action
        if DEBUG:
            print(f"Slider current: {current_value}, last: {self.slider_value}, diff: {diff}, cumulative: {self.slider_cumulative}")

        # Check for full slide
        if abs(diff) > threshold and not self.slider_detected:
            if DEBUG:
                print(f"Full slider movement detected! Threshold: {threshold}")
            self.slider_value = current_value
            self.last_slider_time = current_time
            self.slider_detected = True
            self.slider_cumulative = 0
            return True, current_value
        # Check for partial slide
        elif self.slider_cumulative > SLIDER_PARTIAL_THRESHOLD and not self.slider_detected:
            if DEBUG:
                print(f"Partial slider movement detected! Cumulative: {self.slider_cumulative}")
            self.slider_value = current_value
            self.last_slider_time = current_time
            self.slider_detected = True
            self.slider_cumulative = 0
            return True, current_value
        # Reset if movement stops or changes direction
        elif abs(diff) <= SLIDER_MIN_MOVEMENT:
            self.slider_detected = False
            self.slider_cumulative = 0
            self.slider_direction = 0

        return False, current_value


def main():
    game_state = GameState()
    input_manager = InputManager()
    game_state.input_manager = input_manager  # type: ignore

    time.sleep(2)

    # Debug I2C devices
    print("Scanning for I2C devices...")
    devices = input_manager.i2c1_sensor.scan()
    if devices:
        print(f"Found I2C1 devices at: {[hex(device) for device in devices]}")
    else:
        print("No I2C1 devices found. Check wiring!")

    devices = input_manager.i2c0_sensor.scan()
    if devices:
        print(f"Found I2C0 devices at: {[hex(device) for device in devices]}")
    else:
        print("No I2C0 devices found")

    input_manager.lcd_display.backlight_on()
    input_manager.lcd_display.putstr("Beep It! Beep to start")

    while True:
        # Simple state machine for game on/off
        if not game_state.is_game_on:
            # Check for game start condition (placeholder)
            if input_manager.is_touched():
                print("Starting game!")
                input_manager.lcd_display.clear()
                input_manager.lcd_display.putstr("Starting game!")
                sounds.playsong(input_manager.buzzer, "GAME_START")
                game_state.start_game()
            time.sleep(1)
            continue

        # Game is running
        current_time = time.time()

        # Check for timeouts and generate new action if needed
        if current_time - game_state.last_prompt_time > game_state.prompt_interval:
            game_state.generate_new_action()

        # Check inputs and validate against current action
        if input_manager.is_touched():
            print("Touch detected!")
            if game_state.check_action(GameAction.TOUCH):
                game_state.handle_correct_action()
            else:
                game_state.handle_wrong_action("touch")

        if input_manager.is_shaking():
            print("Shake detected!")
            if game_state.check_action(GameAction.SHAKE):
                game_state.handle_correct_action()
            else:
                game_state.handle_wrong_action("shake")

        joystick_moved, x_axis, y_axis = input_manager.is_joystick_moved()
        if joystick_moved:
            print("Joystick detected!")
            if game_state.check_action(GameAction.FLICK):
                game_state.handle_correct_action()
            else:
                game_state.handle_wrong_action("flick")

        slider_moved, current_value = input_manager.is_slider_moved()
        if slider_moved:
            print("Slider detected!")
            if game_state.check_action(GameAction.SLIDE):
                game_state.handle_correct_action()
            else:
                game_state.handle_wrong_action("slide")

        if game_state.mistakes >= 3:
            game_state.stop_game()

        time.sleep(0.1)

if __name__ == "__main__":
    main()
