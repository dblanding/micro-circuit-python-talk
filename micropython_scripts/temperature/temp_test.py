"""
Measure room temp using Dallas 18B20
"""

import onewire, ds18x20, time
from machine import Pin
SensorPin = Pin(26, Pin.IN, Pin.PULL_UP)
sensor = ds18x20.DS18X20(onewire.OneWire(SensorPin))
roms = sensor.scan()
print(roms)
while True:
   sensor.convert_temp()
   time.sleep(2)
   for rom in roms:
       temperature = round(sensor.read_temp(rom),1)
       fahr = temperature * 9/5 + 32
       print(fahr,"F")
time.sleep(5)
