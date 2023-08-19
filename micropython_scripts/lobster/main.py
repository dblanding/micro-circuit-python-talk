"""
Monitor input pin and drive output pin high/low to follow
"""

from machine import Pin
import time

onboard = Pin("LED", Pin.OUT, value=0)

input = Pin(14, Pin.IN, Pin.PULL_DOWN)
output = Pin(15, Pin.OUT)

count = 0

while True:
    if input.value():
        print("Input high")
        onboard.on()
        output.on()
    else:
        print("Input low")
        onboard.off()
        output.off()
    count += 1
    if count % 10 == 0:
        count = 0
        onboard.on()
    else:
        onboard.off()
    time.sleep(0.1)