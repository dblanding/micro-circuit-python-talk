import board
import busio
import adafruit_pcf8523
import time
from digitalio import DigitalInOut, Direction, Pull

myI2C = busio.I2C(board.SCL, board.SDA)
rtc = adafruit_pcf8523.PCF8523(myI2C)

days = ("Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday")

# LED setup.
led = DigitalInOut(board.LED)
led.direction = Direction.OUTPUT

switch = DigitalInOut(board.D2)
switch.direction = Direction.INPUT
switch.pull = Pull.UP
count = 0
tripped = False

# Initial time
t = rtc.datetime
hour = t.tm_hour
minutes = t.tm_min
seconds = t.tm_sec
print(hour, ":", minutes, ":", seconds, "\t Ticks = ", count)

while True:
    led.value = not switch.value
    if led.value and not tripped:
        # switch leading edge
        tripped = True
        count += 1
        # print(count)
    elif tripped and not led.value:
        # switch falling edge
        tripped = False
        
    if count == (60 * 66):
        t = rtc.datetime
        hour = t.tm_hour
        minutes = t.tm_min
        seconds = t.tm_sec
        print(hour, ":", minutes, ":", seconds, "\t Ticks = ", count)
        count = 0
    time.sleep(0.001)  # debounce delay
