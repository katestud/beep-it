from machine import I2C,Pin
import time
from imu import MPU6050
import math

TOUCH_PIN = 15
MPU_SDA_PIN = 2
MPU_SCL_PIN = 3

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
i2c=I2C(1, sda=Pin(MPU_SDA_PIN), scl=Pin(MPU_SCL_PIN), freq=400000)

print("Scanning for I2C devices...")
devices = i2c.scan()

if devices:
    print(f"Found devices at: {[hex(device) for device in devices]}")
else:
    print("No I2C devices found. Check wiring!")

mpu = MPU6050(i2c)

# Assuming mpu is already initialized
def is_shaking(threshold=2.0):
    xAccel = mpu.accel.x
    yAccel = mpu.accel.y
    zAccel = mpu.accel.z

    # Calculate the overall acceleration magnitude
    accel_magnitude = math.sqrt(xAccel**2 + yAccel**2 + zAccel**2)

    # Compare to a threshold (2g is a good starting point)
    if accel_magnitude > threshold:
        return True
    return False
######### SHAKE DETECTOR #########


######### PRINT DETECTED VALUES #########

while True:
    if is_shaking():
        print("Device is shaking!")
    if is_touched():
        print("Touch detected!")
    time.sleep(0.1)
######### PRINT DETECTED VALUES #########
