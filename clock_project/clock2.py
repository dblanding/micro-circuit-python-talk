"""
Grandfather clock speed regulator
Nominal pendulum tick-tock rate is 66 ticks/min (3960/hr).

An IR sensor is mounted to detect pendulum movement past BDC.
The value of the sensor is digital high when nothing is detected.
It goes low briefly as the rod extending below the bob passes BDC.

The pendulum 'bob' is adjusted (mechanically) to run slightly slow.
An electro-magnet at BDC is used to speed up the pendulum as needed.

Without the influence of the electro-magnet,
the clock runs approximately 2 sec/hour slow.
With the electro-magnet (positioned with a 1/4 inch gap)
the clock runs approximately 8 sec/hour fast.

With each 'tick', the value of count is incremented.
After every 'batch' of 3960 ticks, the RTC time (h:m:s) is fetched.
If the value of s is above a target value (30), the electro-magnet
is energized for the next cycle (batch).
If s is below the target value, the electro-magnet is switched off.
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
snsr_high = False  # show status previous time through loop

# LED setup. The LED turns on when the bob is detected
led = DigitalInOut(board.LED)
led.direction = Direction.OUTPUT

# Electro-magnet setup
em = DigitalInOut(board.D3)
em.direction = Direction.OUTPUT
em.value = False

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
        s = t.tm_sec
        print(t.tm_hour, ":", t.tm_min, ":", s, "\t Ticks = ", count)
        count = 0
        if s > 30:
            em.value = True
        else:
            em.value = False
        print("Electro-magnet is on: ", em.value)

    time.sleep(0.001)  # debounce delay
