"""
Measure room temperature using Dallas 18B20
Make daily data available via webserver
Log daily highs and lows
Power failure tolerant
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
import rp2
from secrets import secrets
import uasyncio as asyncio
import socket

rp2.country('US')

# Global values
gc_text = ''
DATAFILENAME = 'data.txt'
LOGFILENAME = 'log.txt'
ERRORLOGFILENAME = 'errorlog.txt'
ssid = secrets['ssid']
psk = secrets['wifi_password']
TZ_OFFSET = secrets['tz_offset']
tz_offset = TZ_OFFSET
fahr = 0

# Set up logging
logger = logging.getLogger('mylogger')
logger.setLevel(logging.INFO)
fh = logging.FileHandler(ERRORLOGFILENAME)
logger.addHandler(fh)

# Set up onboard led
onboard = Pin("LED", Pin.OUT, value=0)

# Set up DST pin
# Jumper to ground when DST is in effect
DST_pin = Pin(17, Pin.IN, Pin.PULL_UP)

# Set up pin for temperature sensor
SensorPin = Pin(26, Pin.IN, Pin.PULL_UP)
sensor = ds18x20.DS18X20(onewire.OneWire(SensorPin))
roms = sensor.scan()

html = """<!DOCTYPE html>
<html>
    <head> <title>Room Temperature</title> </head>
    <body> <h1>Room Temperature</h1>
        <h3>%s</h3>
        <pre>%s</pre>
    </body>
</html>
"""

def sync_rtc_to_ntp():
    """Sync RTC to (utc) time from ntp server."""
    try:
        settime()
    except OSError as e:
        logger.error("Error while trying to set time: " + str(e))
    print('setting rtc to UTC...')

def local_hour_to_utc_hour(loc_h):
    utc_h = loc_h - tz_offset
    if utc_h > 23:
        utc_h -= 24
    return utc_h

def utc_hour_to_local_hour(utc_h):
    loc_h = utc_h + tz_offset
    if loc_h < 0:
        loc_h += 24
    return loc_h

def record(line):
    """Combined print and append to data file."""
    print(line)
    line += '\n'
    with open(DATAFILENAME, 'a') as file:
        file.write(line)

wlan = network.WLAN(network.STA_IF)

def connect():
    wlan.active(True)
    wlan.config(pm = 0xa11140) # Disable power-save mode
    wlan.connect(ssid, psk)

    max_wait = 30
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            print("wlan.status =", wlan.status())
            break
        max_wait -= 1
        print('waiting for Wi-Fi connection...')
        time.sleep(1)

    if not wlan.isconnected():
        return False
    else:
        print('connected')
        status = wlan.ifconfig()
        print('ip = ' + status[0])
        return True

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
        elif '/err' in request_line.split()[1]:
            with open(ERRORLOGFILENAME) as file:
                data = file.read()
            heading = "ERRORS"
        else:
            with open(DATAFILENAME) as file:
                data = file.read()
            heading = "Append '/log' to URL to see log file"

        # Add current temp
        data += f'Current temp = {fahr:.1f} F \n'
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
    global gc_text, tz_offset, fahr
    print('Connecting to Network...')
    connect()

    # Pico Real Time Clock
    rtc = RTC()
    local_time = rtc.datetime()
    print("Initial (rtc) ", local_time)

    # Sync RTC to ntp time server (utc)
    sync_rtc_to_ntp()
    time.sleep(1)

    gm_time = rtc.datetime()
    # yr, mo, day, dow(0-6 -> mon-sun), hr, min, sec, subsec
    print('Reset to (UTC)', gm_time)
    record("power-up @ (%d, %d, %d, %d, %d, %d, %d, %d) (UTC)" % gm_time)

    print('Setting up webserver...')
    asyncio.create_task(asyncio.start_server(serve_client, "0.0.0.0", 80))
    while True:

        # check for daylight savings time
        if DST_pin.value():
            tz_offset = TZ_OFFSET
        else:
            tz_offset = TZ_OFFSET + 1

        try:
            current_time = rtc.datetime()
            y = current_time[0]  # curr year
            mo = current_time[1] # current month
            d = current_time[2]  # current day
            h = current_time[4]  # curr hour (UTC)
            lh = utc_hour_to_local_hour(h) # (local)
            m = current_time[5]  # curr minute
            s = current_time[6]  # curr second
            
            timestamp = f"{lh:02}:{m:02}"

            # After a power outage, the Pico will restart
            # immediately with default date = 1/1/2021.
            # The router takes longer to come back online.

            # Test WiFi connection
            if  y == 2021 or not wlan.isconnected():
                wlan.disconnect()
                record(f"Attempting to re-connect Wi-Fi at {timestamp}")
                success = connect()
                record(f"Re-connected = {success}")
                if success:
                    sync_rtc_to_ntp()
                time.sleep(10)  # Patience w/ the router

            # Measure temperature periodically
            if s % 10 == 0:
                try:
                    sensor.convert_temp()
                    await asyncio.sleep(2)
                    for rom in roms:
                        temp = round(sensor.read_temp(rom),1)
                    fahr = temp * 9/5 + 32
                except Exception as e:
                    logger.error("sensor read error: " + str(e))
            
            # Print time and temperature every 30 min
            if s == 5 and not m % 30:
                record(f"{fahr:.1f} F @ {timestamp}")
                    
                gc_text = 'free: ' + str(gc.mem_free()) + '\n'
                gc.collect()

            # Once daily (after midnight)
            if lh == 0 and m == 10 and s == 1:
                
                # Find high and low values from previous day
                with open(DATAFILENAME) as f:
                    lines = f.readlines()

                # first line is yesterday's date
                yesterdate = lines[0].split()[-1].strip()

                # collect lines starting with temperature value
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
