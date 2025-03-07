from machine import Pin
import time

# Make sure this is attached to 3.3V instead of 5V to avoid damaging the board
TOUCH_SENSOR = Pin(15, Pin.IN)

while True:
    if TOUCH_SENSOR.value():
        print("Touch detected!")
    else:
        print("No touch detected!")
    time.sleep(0.1)
