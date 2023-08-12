"""
Measure room temperature using Dallas 18B20
Make daily data available via webserver
Log daily highs and lows
"""

import onewire
import ds18x20
import gc
import logging
import micropython
from  machine import Pin, RTC
import network
from ntptime import settime
import time
import _thread
from secrets import secrets
import uasyncio as asyncio
import socket

onboard = Pin("LED", Pin.OUT, value=0)

# Set up logging
logger = logging.getLogger('mylogger')
logger.setLevel(logging.INFO)
fh = logging.FileHandler('errorlog.txt')
logger.addHandler(fh)

# Set up pin for temperature sensor
SensorPin = Pin(26, Pin.IN, Pin.PULL_UP)
sensor = ds18x20.DS18X20(onewire.OneWire(SensorPin))
roms = sensor.scan()

# Global values
gc_text = ''
DST = True  # daylight time in effect
DATAFILENAME = 'data.txt'
LOGFILENAME = 'log.txt'
ssid = secrets['ssid']
password = secrets['wifi_password']
tz_offset = secrets['tz_offset']
if DST:
    tz_offset += 1

html = """<!DOCTYPE html>
<html>
    <head> <title>Garage Temperature</title> </head>
    <body> <h1>Garage Temperature</h1>
        <h3>%s</h3>
        <pre>%s</pre>
    </body>
</html>
"""

def local_hour_to_utc_hour(loc_h):
    utc_h = loc_h - tz_offset
    if utc_h > 23:
        utc_h -= 24
    return utc_h

def record(line):
    """Combined print and append to data file."""
    print(line)
    line += '\n'
    with open(DATAFILENAME, 'a') as file:
        file.write(line)

wlan = network.WLAN(network.STA_IF)

def connect_to_network():
    wlan.active(True)
    wlan.config(pm = 0xa11140) # Disable power-save mode
    wlan.connect(ssid, password)

    max_wait = 10
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print('waiting for connection...')
        time.sleep(1)

    if wlan.status() != 3:
        raise RuntimeError('network connection failed')
    else:
        print('connected')
        status = wlan.ifconfig()
        print('ip = ' + status[0])

async def serve_client(reader, writer):
    try:
        print("Client connected")
        request_line = await reader.readline()
        print("Request:", request_line)
        # We are not interested in HTTP request headers, skip them
        while await reader.readline() != b"\r\n":
            pass

        if '/log' in request_line.split()[1]:
            with open(LOGFILENAME) as file:
                data = file.read()
            heading = "Date, Low, High"
        else:
            with open(DATAFILENAME) as file:
                data = file.read()
            heading = "Append '/log' to URL to see log file"

        data += gc_text

        response = html % (heading, data)
        writer.write('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
        writer.write(response)

        await writer.drain()
        await writer.wait_closed()
        print("Client disconnected")
    except Exception as e:
        logger.error("serve_client error: " + str(e))

async def main():
    global gc_text
    print('Connecting to Network...')
    connect_to_network()

    # Pico Real Time Clock
    rtc = RTC()
    local_time = rtc.datetime()
    print("Initial (rtc) ", local_time)

    # Set RTC to (utc) time from ntp server
    # while rtc.datetime()[0] == 2021:
    try:
        settime()
    except OSError as e:
        print('OSError', e, 'while trying to set rtc')
    print('setting rtc to UTC...')
    time.sleep(1)

    gm_time = rtc.datetime()
    print('Reset to (UTC)', gm_time)
    record("power-up @ (%d, %d, %d, %d, %d, %d, %d, %d) (UTC)" % gm_time)

    print('Setting up webserver...')
    asyncio.create_task(asyncio.start_server(serve_client, "0.0.0.0", 80))
    while True:
        try:
            current_time = rtc.datetime()
            y = current_time[0]  # curr year
            mo = current_time[1] # current month
            d = current_time[2]  # current day
            h = current_time[4]  # curr hour (UTC)
            m = current_time[5]  # curr minute
            s = current_time[6]  # curr second
            
            
            # Print time and temperature every 30 min
            if s in (1, 2) and not m % 30:
                try:
                    sensor.convert_temp()
                    await asyncio.sleep(2)
                    for rom in roms:
                        temp = round(sensor.read_temp(rom),1)
                    fahr = temp * 9/5 + 32
                    lh = h + tz_offset  # local hour
                    if lh < 0:
                        lh += 24
                    record(f"{fahr:.1f} F @ {lh:02}:{m:02}")
                    
                    gc_text = 'free: ' + str(gc.mem_free()) + '\n'
                    gc.collect()
                except Exception as e:
                    record(repr(e))
            
            # At 4:59 AM (UTC)
            if h == 4 and m == 59:
                
                # Find high and low values from previous day
                with open(DATAFILENAME) as f:
                    lines = f.readlines()

                # first line is yesterday's date
                yesterdate = lines[0].split()[-1].strip()

                # collect all lines starting with temperature value
                lines = [line for line in lines if line[0].isdigit()]

                # define a key to sort by float() of first word in string
                def float_first(element):
                    """return float(temp) for element: 'temp @ time'."""
                    temp, *rest = element.split()
                    return float(temp)

                # sort by temperature
                # must convert string value of temperature to float
                # so temperatures over 100 will sort higher than 99
                lines.sort(key=float_first)
                low = lines[0].strip()
                high = lines[-1].strip()
                
                # Log high and low values from previous day
                logline = f'{yesterdate}, {low}, {high}\n'
                with open(LOGFILENAME, 'a') as f:
                    f.write(logline)
                
                # Start a new data file for today
                with open(DATAFILENAME, 'w') as file:
                    file.write('Date: %d/%d/%d\n' % (mo, d, y))
                    file.write('Temp F @ Time\n')

        except Exception as e:
            logger.error("main loop error: " + str(e))

        # Flash LED
        onboard.on()
        await asyncio.sleep(0.1)
        onboard.off()
        await asyncio.sleep(0.9)

try:
    asyncio.run(main())
finally:
    asyncio.new_event_loop()
