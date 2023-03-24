"""
control carriage lights: On at sunset / Off at 'bedtime'
Make daily log data available via webserver
"""

import gc
import micropython
from  machine import Pin, RTC
import network
from ntptime import settime
import time
import urequests
import _thread
from secrets import secrets
import uasyncio as asyncio
import socket

onboard = Pin("LED", Pin.OUT, value=0)

# Global values
DST = True  # daylight time in effect
DATAFILENAME = 'data.txt'
ssid = secrets['ssid']
password = secrets['wifi_password']
lat = secrets['lat']
long = secrets['long']
tz_offset = secrets['tz_offset']
if DST:
    tz_offset += 1

# URLs to fetch from
SUNSET_URL = "http://api.sunrise-sunset.org/json?lat=%f&lng=%f&formatted=0"\
    % (lat, long)
LIGHTS_ON_URL = "http://192.168.1.54/control?cmd=GPIO,12,1"
LIGHTS_OFF_URL = "http://192.168.1.54/control?cmd=GPIO,12,0"

# Default values for sunset time
H = 23
M = 0
S = 0

html = """<!DOCTYPE html>
<html>
    <head> <title>Pico W</title> </head>
    <body> <h1>Pico W</h1>
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

def get_sunset_time():
    """Get (UTC) time of today's sunset. return (H, M, S)"""
    response = urequests.get(SUNSET_URL)
    data = response.json()
    utc_sunset_str = data['results']['sunset']
    date_str, time_str = utc_sunset_str.split('T')
    utc_hr_str, m_str, s_str, *rest = time_str.split(':')
    H = int(utc_hr_str)
    M = int(m_str)
    S = int(s_str.split('+')[0])
    return (H, M, S)

def lights_on():
    ok = False
    try:
        r = urequests.get(LIGHTS_ON_URL)
        record(r.text)
        ok = True
    except Exception as e:
        record(str(e))
    return ok

def lights_off():
    ok = False
    try:
        r = urequests.get(LIGHTS_OFF_URL)
        record(r.text)
        ok = True
    except Exception as e:
        record(str(e))
    return ok

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
    print("Client connected")
    request_line = await reader.readline()
    print("Request:", request_line)
    # We are not interested in HTTP request headers, skip them
    while await reader.readline() != b"\r\n":
        pass

    file = open(DATAFILENAME)
    data = file.read()
    file.close

    response = html % data
    writer.write('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
    writer.write(response)

    await writer.drain()
    await writer.wait_closed()
    print("Client disconnected")

async def main():
    global H, M, S
    print('Connecting to Network...')
    connect_to_network()

    # Pico Real Time Clock
    rtc = RTC()
    local_time = rtc.datetime()
    print("Initial (rtc)  ", local_time)

    # Set RTC to (utc) time from ntp server
    try:
        settime()
    except OSError as e:
        print('OSError', e, 'while trying to set rtc')

    gm_time = rtc.datetime()
    print("rtc reset (UTC)", gm_time)

    print('Setting up webserver...')
    asyncio.create_task(asyncio.start_server(serve_client, "0.0.0.0", 80))
    while True:
        current_time = rtc.datetime()
        y = current_time[0]  # curr year
        mo = current_time[1] # current month
        d = current_time[2]  # current day
        h = current_time[4]  # curr hour (UTC)
        m = current_time[5]  # curr minute
        s = current_time[6]  # curr second
        
        
        # Print UTC time on the hour
        if not m % 60:
            lh = h + tz_offset  # local hour
            if lh < 0:
                lh += 24
            record("%s:%s:%s (UTC); %s:%s:%s (Local)" % (h, m, s, lh, m, s))
            
            print('free:', str(gc.mem_free()))
            print('info (gc):', str(gc.mem_alloc()))
            print('info:', str(micropython.mem_info()))
            gc.collect()
        
        # At 4:59 AM (UTC) purge data file
        if h == 4 and m == 59:
            with open(DATAFILENAME, 'w') as file:
                file.write('Date: %d/%d/%d\n' % (mo, d, y))
        
        # At 22:0:0 (UTC), get time of today's sunset
        if h == 22 and m == 0:
            H, M, S = get_sunset_time()
            LH = H + tz_offset
            record("Sunset today at %s:%s:%s local time" % (LH, M, S))
        
        # At sunset, turn on lights
        if h == H and m == M:
            record("Turning lights on")
            for attempt in range(3):
                if lights_on():
                    break
                await asyncio.sleep(5)

        # At 9:01 PM local time, turn lights off
        utc_hour = local_hour_to_utc_hour(9 + 12)
        if h == utc_hour and m == 1:
            record("Turning lights off")
            for attempt in range(3):
                if lights_off():
                    break
                await asyncio.sleep(5)

        # Flash LED
        for _ in range(3):
            onboard.on()
            await asyncio.sleep(0.1)
            onboard.off()
            await asyncio.sleep(0.1)

        onboard.on()
        # print("heartbeat")
        await asyncio.sleep(0.25)
        onboard.off()
        # Stay on sync with seconds == 0
        await asyncio.sleep(60 - s)

try:
    asyncio.run(main())
finally:
    asyncio.new_event_loop()

