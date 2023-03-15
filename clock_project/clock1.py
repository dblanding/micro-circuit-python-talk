"""
Grandfather clock speed regulator

An IR sensor is mounted to detect movement of the pendulum past BDC.
The value of the sensor is digital high when nothing is detected.
It goes low briefly as the rod extending below the bob passes BDC.

The pendulum tick-tock rate is 66 ticks per minute, (3960 per hour).

With each 'tick', the value of count is incremented.
After every 3960 ticks, the RTC time (h:m:s) is printed.
This gives a value of clock speed error (sec/hr).
"""

import board
import busio
import adafruit_pcf8523
import time
from digitalio import DigitalInOut, Direction, Pull

# RTC setup
myI2C = busio.I2C(board.SCL, board.SDA)
rtc = adafruit_pcf8523.PCF8523(myI2C)

# Pendulum sensor setup
sensor = DigitalInOut(board.D2)
sensor.direction = Direction.INPUT
sensor.pull = Pull.UP
count = 0
snsr_high = False  # shows status previous time through loop

# LED setup.
led = DigitalInOut(board.LED)
led.direction = Direction.OUTPUT

# Initial time
t = rtc.datetime
print(t.tm_hour, ":", t.tm_min, ":", t.tm_sec, "\t Ticks = ", count)

while True:
    # The led turns on when sensor.value goes low
    led.value = not sensor.value

    if led.value and not snsr_high:
        # leading edge
        snsr_high = True
        count += 1
    elif snsr_high and not led.value:
        # falling edge
        snsr_high = False
        
    if count == (60 * 66):
        t = rtc.datetime
        print(t.tm_hour, ":", t.tm_min, ":", t.tm_sec, "\t Ticks = ", count)
        count = 0

    time.sleep(0.001)  # debounce delay
