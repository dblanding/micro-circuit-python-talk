"""
Reconnect to wifi on power failure
Based on garage temperature code
"""

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

# Global values
gc_text = ''
DATAFILENAME = 'data.txt'
LOGFILENAME = 'log.txt'
ERRORLOGFILENAME = 'errorlog.txt'
ssid = secrets['ssid']
password = secrets['wifi_password']
TZ_OFFSET = secrets['tz_offset']
tz_offset = TZ_OFFSET

# Set up logging
logger = logging.getLogger('mylogger')
logger.setLevel(logging.INFO)
fh = logging.FileHandler(ERRORLOGFILENAME)
logger.addHandler(fh)

# Set up DST pin
# Jumper to ground when DST is in effect
DST_pin = Pin(17, Pin.IN, Pin.PULL_UP)

html = """<!DOCTYPE html>
<html>
    <head> <title>Re-Connect on Power Failure</title> </head>
    <body> <h1>Re-Connect</h1>
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

def connect():
    """Return True on successful connection, otherwise False"""
    wlan.active(True)
    wlan.config(pm = 0xa11140) # Disable power-save mode
    wlan.connect(ssid, password)

    max_wait = 10
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            print("wlan.status =", wlan.status())
            break
        max_wait -= 1
        print('waiting for connection...')
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
            heading = "Date"
        elif '/err' in request_line.split()[1]:
            with open(ERRORLOGFILENAME) as file:
                data = file.read()
            heading = "ERRORS"
        else:
            with open(DATAFILENAME) as file:
                data = file.read()
            heading = "Append '/log' or '/err' to URL to see log file or error log"

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
    global gc_text, tz_offset
    print('Connecting to Network...')
    connect()

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

        # check DST jumper (daylight savings time)
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
            m = current_time[5]  # curr minute
            s = current_time[6]  # curr second
            
            # Test WiFi connection twice per minute
            if s in (1, 31):
                if not wlan.isconnected():
                    record("WiFi not connected")
                    wlan.disconnect()
                    record("Attempting to re-connect")
                    success = connect()
                    record(f"Successful reconnection: {success}")
            
            # Print time every 30 min
            if s in (2,) and not m % 30:
                try:
                    lh = h + tz_offset  # local hour
                    if lh < 0:
                        lh += 24
                    record(f"datapoint @ {lh:02}:{m:02}")
                    
                    gc_text = 'free: ' + str(gc.mem_free()) + '\n'
                    gc.collect()
                except Exception as e:
                    record(repr(e))

            # At 5:01 AM (UTC)
            if h == 4 and m == 10:
                
                # Read lines from previous day
                with open(DATAFILENAME) as f:
                    lines = f.readlines()

                # first line is yesterday's date
                yesterdate = lines[0].split()[-1].strip()

                # cull all lines containing '@'
                lines = [line
                         for line in lines
                         if '@' not in line]
                
                # Log lines from previous day
                with open(LOGFILENAME, 'a') as f:
                    for line in lines:
                        f.write(line)
                
                # Start a new data file for today
                with open(DATAFILENAME, 'w') as file:
                    file.write('Date: %d/%d/%d\n' % (mo, d, y))

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
