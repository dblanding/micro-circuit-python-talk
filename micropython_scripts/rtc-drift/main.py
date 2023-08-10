"""
Measure drift of onboard RTC by checking
NTP time periodically.
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

# Set up logging
logger = logging.getLogger('mylogger')
logger.setLevel(logging.INFO)
fh = logging.FileHandler('errorlog.txt')
logger.addHandler(fh)

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
    <head> <title>RTC Drift</title> </head>
    <body> <h1>RTC Drift</h1>
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

        with open(DATAFILENAME) as file:
            data = file.read()

        data += gc_text

        response = html % (data)
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
            dow = current_time[3]  # current day 0f week (Sunday=6)
            h = current_time[4]  # curr hour (UTC)
            m = current_time[5]  # curr minute
            s = current_time[6]  # curr second
            
            
            # Print time every hour
            if not s and not m % 60:
                try:
                    lh = h + tz_offset  # local hour
                    if lh < 0:
                        lh += 24
                    record(f"{lh:02}:{m:02}")
                    
                    gc_text = 'free: ' + str(gc.mem_free()) + '\n'
                    gc.collect()
                except Exception as e:
                    record(repr(e))
            
            # At 4:59 AM (UTC)
            if h == 4 and m == 59:
                
                # Start a new data file for today
                with open(DATAFILENAME, 'w') as file:
                    file.write('Date: %d/%d/%d\n' % (mo, d, y))
                
                if dow == 0:  # Monday
                    settime()
                    drift = s - rtc.datetime()[6]
                    record('Drift = %s seconds per week' % drift)

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
