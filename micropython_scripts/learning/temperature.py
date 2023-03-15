# temperature.py

import machine
import utime

sensor_temp = machine.ADC(4)
conversion_factor = 3.3 / (65535)

while True:
    reading = sensor_temp.read_u16() * conversion_factor
    celsius = 27 - (reading - 0.706)/0.001721
    fahrenheit = celsius * 9/5 + 32
    print(fahrenheit)
    utime.sleep(2)
