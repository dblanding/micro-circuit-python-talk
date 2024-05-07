"""
control carriage lights: On at sunset / Off at 'bedtime'
Make daily log data available via webserver
Power failure tolerant
"""

import gc
import micropython
from  machine import Pin, RTC
import network
from ntptime import settime
import time
import urequests
from secrets import secrets
import uasyncio as asyncio

# Global values
DATAFILENAME = 'data.txt'
ssid = secrets['ssid']
password = secrets['wifi_password']
lat = secrets['lat']
long = secrets['long']
TZ_OFFSET = secrets['tz_offset']

# Set up DST pin
# Jumper to ground when DST is in effect
DST_pin = Pin(17, Pin.IN, Pin.PULL_UP)

# Account for Daylight Savings Time
if DST_pin.value():
    tz_offset = TZ_OFFSET
else:
    tz_offset = TZ_OFFSET + 1

# URLs to fetch from
SUNSET_URL = "http://api.sunrise-sunset.org/json?lat=%f&lng=%f&formatted=0"\
    % (lat, long)
LIGHTS_ON_URL = "http://192.168.1.54/control?cmd=GPIO,12,1"
LIGHTS_OFF_URL = "http://192.168.1.54/control?cmd=GPIO,12,0"

# Set up onboard led
onboard = Pin("LED", Pin.OUT, value=0)

html = """<!DOCTYPE html>
<html>
    <head> <title>Lights Controller</title> </head>
    <body> <h1>Carriage Lights Controller</h1>
        <pre>%s</pre>
    </body>
</html>
"""

def record(line):
    """Combined print and append to data file."""
    print(line)
    line += '\n'
    with open(DATAFILENAME, 'a') as file:
        file.write(line)

def sync_rtc_to_ntp():
    """Sync RTC to (utc) time from ntp server."""
    try:
        settime()
    except OSError as e:
        err_string = 'OSError' + e + 'while trying to set rtc'
        record(err_string)
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

def get_sunset_time():
    """Get (UTC) time of today's sunset. return (H, M, S)"""
    try:
        response = urequests.get(SUNSET_URL)
        data = response.json()
        utc_sunset_str = data['results']['sunset']
        date_str, time_str = utc_sunset_str.split('T')
        utc_hr_str, m_str, s_str, *rest = time_str.split(':')
        H = int(utc_hr_str)
        M = int(m_str)
        S = int(s_str.split('+')[0])
        return (H, M, S)
    except Exception as e:
        record(repr(e))

def lights_on():
    ok = False
    r = urequests.get(LIGHTS_ON_URL)
    record(r.text)
    ok = True
    return ok

def lights_off():
    ok = False
    r = urequests.get(LIGHTS_OFF_URL)
    record(r.text)
    ok = True
    return ok

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
    print("Client connected")
    request_line = await reader.readline()
    print("Request:", request_line)
    # We are not interested in HTTP request headers, skip them
    while await reader.readline() != b"\r\n":
        pass

    with open(DATAFILENAME) as file:
        data = file.read()

    response = html % data
    writer.write('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
    writer.write(response)

    await writer.drain()
    await writer.wait_closed()
    print("Client disconnected")

async def main():
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
    print('Reset to (UTC)', gm_time)
    record("power-up @ (%d, %d, %d, %d, %d, %d, %d, %d) (UTC)" % gm_time)

    print('Setting up webserver...')
    asyncio.create_task(asyncio.start_server(serve_client, "0.0.0.0", 80))

    # Get sunset time
    H, M, S = get_sunset_time()

    while True:

        # Check for daylight savings time (set w/ jumper)
        if DST_pin.value():
            tz_offset = TZ_OFFSET
        else:
            tz_offset = TZ_OFFSET + 1
        
        current_time = rtc.datetime()
        y = current_time[0]  # curr year
        mo = current_time[1] # current month
        d = current_time[2]  # current day
        h = current_time[4]  # curr hour (UTC)
        lh = utc_hour_to_local_hour(h) # (local)
        m = current_time[5]  # curr minute
        s = current_time[6]  # curr second

        timestamp = f"{lh:02}:{m:02}:{s:02}"

        # Test WiFi connection twice per minute
        if s in (15, 45):
            if not wlan.isconnected():
                record(f"{timestamp} WiFi not connected")
                wlan.disconnect()
                record("Attempting to re-connect")
                success = connect()
                record(f"Re-connected: {success}")
                # After successful reconnection, sync rtc to ntp
                if success:
                    sync_rtc_to_ntp()
                    time.sleep(1)
            
        # Print UTC time on the hour
        if not s and not m % 60:
            record("%d:%02d:%02d (UTC); %d:%02d:%02d (Local)" % (h, m, s, lh, m, s))

            print('free:', str(gc.mem_free()))
            print('info (gc):', str(gc.mem_alloc()))
            print('info:', str(micropython.mem_info()))
            gc.collect()

        # At 11:59 AM (UTC) purge data file
        if h == 11 and m == 59 and s == 0:
            with open(DATAFILENAME, 'w') as file:
                file.write('Date: %d/%d/%d\n' % (mo, d, y))
                file.write('Sunset yesterday @ %d:%02d:%02d (UTC)\n' % (H, M, S))

        # At 22:0:0 (UTC), get time of today's sunset
        if h == 22 and m == 0 and s == 0:
            record("Getting time of today's sunset")
            try:
                H, M, S = get_sunset_time()
                LH = utc_hour_to_local_hour(H)
                record("Sunset today at %d:%02d:%02d local time" % (LH, M, S))
            except Exception as e:
                record('Error: %s at %d:%02d:%02d' % (e, h, m, s))
        
        # At sunset, turn lights on
        if h == H and m == M  and s == 0:
            record("Turning lights on")
            try:
                lights_on()
            except Exception as e:
                record(repr(e))

        # At 9:01 PM local time, turn lights off
        utc_hour = local_hour_to_utc_hour(9 + 12)
        if h == utc_hour and m == 1 and s == 0:
            record("Turning lights off")
            try:
                lights_off()
            except Exception as e:
                record(repr(e))

        onboard.on()
        # print("heartbeat")
        await asyncio.sleep(0.1)
        onboard.off()
        await asyncio.sleep(0.9)

try:
    asyncio.run(main())
finally:
    asyncio.new_event_loop()
