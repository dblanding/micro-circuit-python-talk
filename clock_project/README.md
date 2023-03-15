# Project: Use a microprocessor to regulate grandfather clock (pendulum)
* Programmed an ESP32 to get time from an npt server and initiate the onboard RTC
    * Easy-Peasy, but I think it would be more fun for me to do the rest of the programming in python...
* Tried using CircuitPython on the  Metro M0 Express
    * Metro doesn't support WiFi connectivity - but I don't really need this.
    * Metro doesn't have an RTC, so I ordered an Adafruit PCF8523 Real Time Clock
    * [Adafruit PCF8523 Real Time Clock](https://learn.adafruit.com/adafruit-pcf8523-real-time-clock)
    * [Connection to the Metro M0 with Arduino](https://learn.adafruit.com/adafruit-pcf8523-real-time-clock/rtc-with-arduino)
    * [Connection to the Metro M0 with CircuitPython](https://learn.adafruit.com/adafruit-pcf8523-real-time-clock/rtc-with-circuitpython)

``` CircuitPython
import busio
import adafruit_pcf8523
import time
import board

myI2C = busio.I2C(board.SCL, board.SDA)
rtc = adafruit_pcf8523.PCF8523(myI2C)

days = ("Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday")

target_sec = 30  # target value of RTC seconds for loop

if False:   # change to True if you want to set the time!
    #                     year, mon, date, hour, min, sec, wday, yday, isdst
    t = time.struct_time((2017,  10,   29,   15,  14,  15,    0,   -1,    -1))
    # you must set year, mon, date, hour, min, sec and weekday
    # yearday is not supported, isdst can be set but we don't do anything with it at this time

    print("Setting time to:", t)     # uncomment for debugging
    rtc.datetime = t
    print()

while True:
    t = rtc.datetime
    sec = t.tm_sec
    print(sec)
    delta = sec - target_sec

    if not delta:
        time.sleep(60)  # Just keep on ticking every 60 sec
    elif abs(delta) == 1:
        time.sleep(60 - delta * 0.1)  # trim by 1/10 sec
    else:
        time.sleep(60 - delta)  # jump to target

```

## [Rotary Encoder in CircuitPython](https://learn.adafruit.com/rotary-encoder/circuitpython)

* Just for fun, I hooked up a rotary encoder to check it out. Works great!

``` CircuitPython
import rotaryio
import board

encoder = rotaryio.IncrementalEncoder(board.D10, board.D9)
last_position = None
while True:
    position = encoder.position
    if last_position is None or position != last_position:
        print(position)
    last_position = position
```
## [Metro M0 Express board layout](https://cdn-learn.adafruit.com/assets/assets/000/110/930/original/circuitpython_Adafruit_Metro_M0_Express_Pinout.png?1650392350)
## Use [Digital IO in CircuitPython](https://learn.adafruit.com/circuitpython-essentials/circuitpython-digital-in-out) to listen to IR sensor (catch clock ticks)
## Checked out [Adafruit IO](https://learn.adafruit.com/welcome-to-adafruit-io/what-is-adafruit-io) Cloud Service
* Metro M0 Express doesn't work with AdafruitIO. Only boards with WiFi
* However, the M4 **does** have WiFi and it works with Adafruit IO.
    * For $35, it might be good to get one of those.
        * I could then put the clock project on this and have online access to the clock data
    * I also noticed that there is an E-paper weather station project for the M4.
        * Unfortunately, the E-paper is curently out of stock
        * I asked to be notified when it is in stock.

## Final clock.py code on Metro M0 Express

``` Python
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

```

