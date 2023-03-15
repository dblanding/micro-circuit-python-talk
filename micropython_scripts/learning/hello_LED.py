# hello_LED.py

from machine import Pin
from time import sleep
import time
led = Pin("LED", Pin.OUT)
while True:
    led.toggle()
    time.sleep(1)
