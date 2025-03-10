from machine import I2C,Pin, ADC
import time
from imu import MPU6050
import math

TOUCH_PIN = 15
MPU_SDA_PIN = 2
MPU_SCL_PIN = 3

# This is important, as we want to connect to one of the analog to digital
# converter pins. See https://microcontrollerslab.com/joystick-module-raspberry-pi-pico/
# Joystick can also measure button click on the SW pin, but we don't need that
# for the Bop It Game.
JOYSTICK_X_PIN = 27
JOYSTICK_Y_PIN = 26

######### TOUCH SENSOR #########
# # Make sure this is attached to 3.3V instead of 5V to avoid damaging the board
TOUCH_SENSOR = Pin(TOUCH_PIN, Pin.IN)

def is_touched():
    if TOUCH_SENSOR.value():
        return True
    return False
######### TOUCH SENSOR #########

######### SHAKE DETECTOR #########
# Make sure to wire the SDA and SCL pins according to whether we're using I2C0 or I2C1
I2C_SENSOR=I2C(1, sda=Pin(MPU_SDA_PIN), scl=Pin(MPU_SCL_PIN), freq=400000)

# Debugging to make sure the wiring is set up correctly
print("Scanning for I2C devices...")
devices = I2C_SENSOR.scan()

if devices:
    print(f"Found devices at: {[hex(device) for device in devices]}")
else:
    print("No I2C devices found. Check wiring!")

MPU_SENSOR = MPU6050(I2C_SENSOR)

# Assuming mpu is already initialized
def is_shaking(threshold=2.0):
    xAccel = MPU_SENSOR.accel.x
    yAccel = MPU_SENSOR.accel.y
    zAccel = MPU_SENSOR.accel.z

    # Calculate the overall acceleration magnitude
    accel_magnitude = math.sqrt(xAccel**2 + yAccel**2 + zAccel**2)

    # Compare to a threshold (2g is a good starting point)
    if accel_magnitude > threshold:
        return True
    return False
######### SHAKE DETECTOR #########

######### JOYSTICK DETECTOR #########
VRX = ADC(Pin(JOYSTICK_X_PIN))
VRY = ADC(Pin(JOYSTICK_Y_PIN))

def is_joystick_moved(x_last, y_last, threshold=1000):
    """Detect if the joystick position has changed beyond a threshold."""
    x_axis = VRX.read_u16()
    y_axis = VRY.read_u16()

    # Check if the movement exceeds the threshold
    x_moved = abs(x_axis - x_last) > threshold
    y_moved = abs(y_axis - y_last) > threshold

    return x_moved or y_moved, x_axis, y_axis

x_last = VRX.read_u16()
y_last = VRY.read_u16()

######### JOYSTICK DETECTOR #########


######### PRINT DETECTED VALUES #########

while True:
    if is_shaking():
        print("Device is shaking!")
    if is_touched():
        print("Touch detected!")

    # Check if the joystick has moved
    moved, xAxis, yAxis = is_joystick_moved(x_last, y_last)
    if moved:
        print(f"Joystick moved! X: {xAxis}, Y: {yAxis}")
        # Update last known position
        x_last = xAxis
        y_last = yAxis
    time.sleep(0.1)
######### PRINT DETECTED VALUES #########
