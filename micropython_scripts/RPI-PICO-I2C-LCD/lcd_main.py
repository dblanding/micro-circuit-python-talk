"""
How to connect an LCD display to a Raspberry Pi Pico
https://www.freva.com/how-to-connect-an-lcd-display-to-a-raspberry-pi-pico/
"""

from machine import Pin, I2C
from lcd_api import LcdApi
from pico_i2c_lcd import I2cLcd

I2C_ADDR = 0x3f
I2C_NUM_ROWS = 2
I2C_NUM_COLS = 16

i2c = I2C(0, sda=machine.Pin(0), scl=machine.Pin(1), freq=400000)
lcd = I2cLcd(i2c, I2C_ADDR, I2C_NUM_ROWS, I2C_NUM_COLS)

lcd.backlight_on()
lcd.putstr("Prog MicroPython")
lcd.move_to(0,1)
lcd.putstr("on Ras-pi Pico W")
# 16 chars("________________")
