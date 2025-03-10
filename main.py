from machine import I2C, Pin, ADC
import time
from imu import MPU6050
import math

# Pin Definitions
TOUCH_PIN = 15
MPU_SDA_PIN = 2
MPU_SCL_PIN = 3
SLIDING_POTENTIOMETER_PIN = 28
JOYSTICK_X_PIN = 27
JOYSTICK_Y_PIN = 26

class GameState:
    def __init__(self):
        self.is_game_on = False
        self.score = 0
        self.last_action_time = 0
        self.current_action = None

    def start_game(self):
        self.is_game_on = True
        self.score = 0
        self.last_action_time = time.time()

    def stop_game(self):
        self.is_game_on = False
        print(f"Game ended! Final score: {self.score}")

class InputManager:
    def __init__(self):
        # Touch Sensor Setup
        self.touch_sensor = Pin(TOUCH_PIN, Pin.IN)

        # IMU Setup
        self.i2c_sensor = I2C(1, sda=Pin(MPU_SDA_PIN), scl=Pin(MPU_SCL_PIN), freq=400000)
        self.mpu_sensor = MPU6050(self.i2c_sensor)

        # Joystick Setup
        self.vrx = ADC(Pin(JOYSTICK_X_PIN))
        self.vry = ADC(Pin(JOYSTICK_Y_PIN))
        self.joystick_x_position = self.vrx.read_u16()
        self.joystick_y_position = self.vry.read_u16()

        # Slider Setup
        self.slider_sensor = ADC(Pin(SLIDING_POTENTIOMETER_PIN))
        self.slider_value = self.slider_sensor.read_u16()

    def is_touched(self):
        return self.touch_sensor.value()

    def is_shaking(self, threshold=2.0):
        xAccel = self.mpu_sensor.accel.x
        yAccel = self.mpu_sensor.accel.y
        zAccel = self.mpu_sensor.accel.z
        accel_magnitude = math.sqrt(xAccel**2 + yAccel**2 + zAccel**2)
        return accel_magnitude > threshold

    def is_joystick_moved(self, threshold=1000):
        x_axis = self.vrx.read_u16()
        y_axis = self.vry.read_u16()

        x_moved = abs(x_axis - self.joystick_x_position) > threshold
        y_moved = abs(y_axis - self.joystick_y_position) > threshold

        if x_moved or y_moved:
            self.joystick_x_position = x_axis
            self.joystick_y_position = y_axis
            return True, x_axis, y_axis
        return False, x_axis, y_axis

    def is_slider_moved(self, threshold=500):
        current_value = self.slider_sensor.read_u16()
        if abs(current_value - self.slider_value) > threshold:
            self.slider_value = current_value
            return True, current_value
        return False, current_value

def main():
    game_state = GameState()
    input_manager = InputManager()

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
            if input_manager.is_touched():
                print("Starting game!")
                game_state.start_game()
            time.sleep(0.1)
            continue

        # Game is running
        if input_manager.is_shaking():
            print("Device is shaking!")
            game_state.score += 1

        if input_manager.is_touched():
            print("Touch detected!")
            game_state.score += 1

        joystick_moved, x_axis, y_axis = input_manager.is_joystick_moved()
        if joystick_moved:
            print(f"Joystick moved! X: {x_axis}, Y: {y_axis}")
            game_state.score += 1

        slider_moved, current_value = input_manager.is_slider_moved()
        if slider_moved:
            print(f"Slider moved! Current value: {current_value}")
            game_state.score += 1

        # Check for game end condition (placeholder)
        if game_state.score >= 10:  # Example end condition
            game_state.stop_game()

        time.sleep(0.1)

if __name__ == "__main__":
    main()
