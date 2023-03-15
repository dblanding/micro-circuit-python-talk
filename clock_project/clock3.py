"""
Grandfather clock speed regulator
Nominal pendulum tick-tock rate is 66 ticks/min.

An IR sensor is mounted to detect pendulum movement past BDC.
The value of the sensor is digital high when nothing is detected.
It goes low when it detects the rod extending below the bob.

The pendulum 'bob' is adjusted (mechanically) to run slightly slow.
An electro-magnet at BDC is used to speed up the pendulum as needed.

Without the influence of the electro-magnet,
the clock runs approximately 2 sec/hour slow.
When the electro-magnet (positioned with a 1/4 inch gap) is turned ON,
the clock runs approximately 8 sec/hour fast.

After every 'batch' of 66 ticks, the RTC time (h:m:s) is fetched.
If the value of s is above a target value = 30, the electro-magnet
is turned on for the next cycle (batch).
If s is at or below the target value, the electro-magnet is turned off.

In mormal operation, the clock will tick merrily along, with the
electro-magnet turned on for approximately one minute of every four,
clock time synced to the RTC within less than 1 second.
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
count = 0  # Accumulated number of elapsed 'ticks'
snsr_high = False  # status previous time through loop

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
    # Turn led 'on' when sensor.value goes low, 'off' when high
    led.value = not sensor.value

    if led.value and not snsr_high:  # leading edge of 'tick'
        snsr_high = True
        count += 1
    elif snsr_high and not led.value:  # falling edge
        snsr_high = False

    if count == 66:
        t = rtc.datetime
        s = t.tm_sec
        print(t.tm_hour, ":", t.tm_min, ":", s, "\t Ticks = ", count)
        count = 0
        if s > 30:
            em.value = True
            print("Electro-magnet ON")
        else:
            em.value = False
            print("Electro-magnet OFF")

    time.sleep(0.001)  # debounce delay
