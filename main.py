from machine import I2C, Pin, ADC
import time
from imu import MPU6050
import math
import random

# Pin Definitions
TOUCH_PIN = 15
MPU_SDA_PIN = 2
MPU_SCL_PIN = 3
SLIDING_POTENTIOMETER_PIN = 28
JOYSTICK_X_PIN = 27
JOYSTICK_Y_PIN = 26

# Debounce settings (in seconds)
DEBOUNCE_TIME = 0.5
SHAKE_DEBOUNCE = 0.8  # Longer debounce for shake to ensure complete movement
SLIDER_DEBOUNCE = 0.3
JOYSTICK_DEBOUNCE = 0.4

# Debug mode
DEBUG = True

# Slider settings
SLIDER_THRESHOLD = 1000  # Minimum change to detect movement
SLIDER_PARTIAL_THRESHOLD = 500  # Minimum change for partial slide
SLIDER_MIN_MOVEMENT = 100  # Minimum movement in one direction to count

class GameAction:
    TOUCH = "Touch it!"
    FLICK = "Flick it!"
    SHAKE = "Shake it!"
    SLIDE = "Slide it!"

    @classmethod
    def get_random_action(cls):
        actions = [cls.TOUCH, cls.FLICK, cls.SHAKE, cls.SLIDE]
        return random.choice(actions)

class GameState:
    def __init__(self):
        self.is_game_on = False
        self.score = 0
        self.last_action_time = 0
        self.current_action = None
        self.action_timeout = 3.0  # seconds to complete the action
        self.last_prompt_time = 0
        self.prompt_interval = 2.0  # seconds between prompts
        self.input_manager = None  # Will be set when game starts

    def start_game(self):
        self.is_game_on = True
        self.score = 0
        self.last_action_time = time.time()
        self.current_action = None
        print("\nWelcome to Bop It!")
        print("Follow the prompts!")
        self.generate_new_action()

    def stop_game(self):
        self.is_game_on = False
        print(f"\nGame ended! Final score: {self.score}")

    def generate_new_action(self):
        self.current_action = GameAction.get_random_action()
        self.last_action_time = time.time()
        print(f"\n{self.current_action}")
        self.last_prompt_time = time.time()
        # Reset debounce timers when generating a new action
        if self.input_manager:
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
        self.generate_new_action()

    def handle_wrong_action(self, action):
        print(f"Wrong action: {action}! Try again!")

class InputManager:
    def __init__(self):
        # Touch Sensor Setup
        self.touch_sensor = Pin(TOUCH_PIN, Pin.IN)
        self.last_touch_time = 0
        self.last_touch_state = False

        # IMU Setup
        self.i2c_sensor = I2C(1, sda=Pin(MPU_SDA_PIN), scl=Pin(MPU_SCL_PIN), freq=400000)
        self.mpu_sensor = MPU6050(self.i2c_sensor)
        self.last_shake_time = 0
        self.shake_detected = False

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

    def is_touched(self, current_action=None):
        current_time = time.time()
        current_state = self.touch_sensor.value()

        # Only check current_action if we're in a game
        if current_action is not None and current_action != GameAction.TOUCH:
            self.last_touch_state = current_state
            return False

        # Only trigger on rising edge (touch start) and after debounce
        if current_state and not self.last_touch_state and (current_time - self.last_touch_time) > DEBOUNCE_TIME:
            self.last_touch_time = current_time
            self.last_touch_state = current_state
            return True
        elif not current_state:
            self.last_touch_state = False

        return False

    def is_shaking(self, threshold=2.0, current_action=None):
        current_time = time.time()
        if current_time - self.last_shake_time < SHAKE_DEBOUNCE:
            return False

        # If the action has changed, reset the detection to prevent false triggers
        if current_action != GameAction.SHAKE:
            self.shake_detected = False
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

    def is_joystick_moved(self, threshold=1000, current_action=None):
        current_time = time.time()
        if current_time - self.last_joystick_time < JOYSTICK_DEBOUNCE:
            return False, self.joystick_x_position, self.joystick_y_position

        # If the action has changed, update positions to prevent false triggers
        if current_action != GameAction.FLICK:
            self.joystick_x_position = self.vrx.read_u16()
            self.joystick_y_position = self.vry.read_u16()
            self.joystick_detected = False
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

    def is_slider_moved(self, threshold=SLIDER_THRESHOLD, current_action=None):
        current_time = time.time()
        if current_time - self.last_slider_time < SLIDER_DEBOUNCE:
            return False, self.slider_value

        current_value = self.slider_sensor.read_u16()
        diff = current_value - self.slider_value

        # If the action has changed, update the last value to prevent false triggers
        if current_action != GameAction.SLIDE:
            self.slider_value = current_value
            return False, current_value

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
        if DEBUG and current_action == GameAction.SLIDE:
            print(f"Slider current: {current_value}, last: {self.slider_value}, diff: {diff}, cumulative: {self.slider_cumulative}")

        # Check for full slide
        if abs(diff) > threshold and not self.slider_detected:
            if DEBUG and current_action == GameAction.SLIDE:
                print(f"Full slider movement detected! Threshold: {threshold}")
            self.slider_value = current_value
            self.last_slider_time = current_time
            self.slider_detected = True
            self.slider_cumulative = 0
            return True, current_value
        # Check for partial slide
        elif self.slider_cumulative > SLIDER_PARTIAL_THRESHOLD and not self.slider_detected:
            if DEBUG and current_action == GameAction.SLIDE:
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
    game_state.input_manager = input_manager  # Set the input manager reference

    # Debug I2C devices
    print("Scanning for I2C devices...")
    devices = input_manager.i2c_sensor.scan()
    if devices:
        print(f"Found devices at: {[hex(device) for device in devices]}")
    else:
        print("No I2C devices found. Check wiring!")

    while True:
        # Simple state machine for game on/off
        if not game_state.is_game_on:
            # Check for game start condition (placeholder)
            if input_manager.is_touched(current_action=None):  # Pass None since we're not in a game action yet
                print("Starting game!")
                game_state.start_game()
            time.sleep(0.1)
            continue

        # Game is running
        current_time = time.time()

        # Check for timeouts and generate new action if needed
        if current_time - game_state.last_prompt_time > game_state.prompt_interval:
            game_state.generate_new_action()

        # Check inputs and validate against current action
        if input_manager.is_touched(current_action=game_state.current_action):
            if game_state.check_action(GameAction.TOUCH):
                game_state.handle_correct_action()
            else:
                game_state.handle_wrong_action("touch")

        if input_manager.is_shaking(current_action=game_state.current_action):
            if game_state.check_action(GameAction.SHAKE):
                game_state.handle_correct_action()
            else:
                game_state.handle_wrong_action("shake")

        joystick_moved, x_axis, y_axis = input_manager.is_joystick_moved(current_action=game_state.current_action)
        if joystick_moved:
            if game_state.check_action(GameAction.FLICK):
                game_state.handle_correct_action()
            else:
                game_state.handle_wrong_action("flick")

        slider_moved, current_value = input_manager.is_slider_moved(current_action=game_state.current_action)
        if slider_moved:
            if game_state.check_action(GameAction.SLIDE):
                game_state.handle_correct_action()
            else:
                game_state.handle_wrong_action("slide")

        # Check for game end condition (placeholder)
        if game_state.score >= 10:  # Example end condition
            game_state.stop_game()

        time.sleep(0.1)

if __name__ == "__main__":
    main()
