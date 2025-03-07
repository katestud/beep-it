from machine import Pin
import time

touch_sensor = Pin(15, Pin.IN)  # GP15 as input

while True:
    if touch_sensor.value():
        print("Touch detected!")
    else:
        print("No touch detected!")
    time.sleep(0.1)
