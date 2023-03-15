# data_logger.py

import machine
import utime

sensor_temp = machine.ADC(machine.ADC.CORE_TEMP)
conversion_factor = 3.3 / (65535)

with open("temps.txt", "w") as file:

    while True:
        reading = sensor_temp.read_u16() * conversion_factor
        celsius = 27 - (reading - 0.706)/0.001721
        fahrenheit = celsius * 9/5 + 32
        file.write(str(fahrenheit) + '\n')
        utime.sleep(2)
