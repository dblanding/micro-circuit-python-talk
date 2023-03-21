# lights.py
# RasPi Pico auto-control outdoor lights
# Turn on at sunset / off at fixed time
# Work with UTC time

import gc
import micropython
from  machine import Pin, RTC
import network
from ntptime import settime
from time import sleep
import urequests
import _thread
from secrets import secrets
import uasyncio as asyncio


# 2 threads will each access the same datafile
#   The main once-per-minute loop (3 quick led blinks once per min)
#   The webserver showing daily data (1 blink every 5 sec)
onboard = Pin("LED", Pin.OUT, value=0)
lock = _thread.allocate_lock()

# Global values
DST = True  # daylight time in effect
datafilename = 'data.txt'
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

def local_hour_to_utc_hour(loc_h):
    utc_h = loc_h - tz_offset
    if utc_h > 23:
        utc_h -= 24
    return utc_h

def record(line):
    """Combined print and append to data file."""
    print(line)
    line += '\n'
    lock.acquire()
    with open(datafilename, 'a') as file:
        file.write(line)
    lock.release()

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

def connect_to_network():
    wlan.active(True)
    # wlan.config(pm = 0xa11140) # Disable power-save mode
    wlan.connect(ssid, password)

    max_wait = 10
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print('waiting for connection...')
        sleep(1)

    if wlan.status() != 3:
        raise RuntimeError('network connection failed')
    else:
        print('connected')
        status = wlan.ifconfig()
        print('ip = ' + status[0])

# Connect to network
wlan = network.WLAN(network.STA_IF)
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


html = """<!DOCTYPE html>
<html>
    <head> <title>Pico W</title> </head>
    <body> <h1>Pico W</h1>
        <pre>%s</pre>
    </body>
</html>
"""

async def serve_client(reader, writer):
    print("Client connected")
    request_line = await reader.readline()
    print("Request:", request_line)
    # We are not interested in HTTP request headers, skip them
    while await reader.readline() != b"\r\n":
        pass

    data = ''
    lock.acquire()
    with open(datafilename) as file:
        data += file.read()
    lock.release()

    response = html % data
    writer.write('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
    writer.write(response)

    await writer.drain()
    await writer.wait_closed()
    print("Client disconnected")

async def main():
    # print('Connecting to Network...')
    # connect_to_network()

    print('Setting up webserver...')
    asyncio.create_task(asyncio.start_server(serve_client, "0.0.0.0", 80))
    while True:
        onboard.on()
        # print("heartbeat")
        await asyncio.sleep(0.25)
        onboard.off()
        await asyncio.sleep(5)

def start_web_server():
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()

# _thread.start_new_thread(start_web_server, ())

while True:
    current_time = rtc.datetime()
    h = current_time[4]  # curr hour (UTC)
    m = current_time[5]  # curr minute
    s = current_time[6]  # curr second
    
    # Print UTC time on the half hour
    if not m % 30:
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
        lock.acquire()
        with open(datafilename, 'w') as file:
            file.write('')
        lock.release()
    
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
            time.sleep(5)

    # At 9:01 PM local time, turn lights off
    utc_hour = local_hour_to_utc_hour(9 + 12)
    if h == utc_hour and m == 1:
        record("Turning lights off")
        for attempt in range(3):
            if lights_off():
                break
            time.sleep(5)

    # Flash LED
    for _ in range(3):
        onboard.on()
        sleep(0.1)
        onboard.off()
        sleep(0.1)

    # Stay on sync with seconds == 0
    sleep(60 - s)
