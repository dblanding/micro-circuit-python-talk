"""
MicroPython script based on CircuitPython code clock3.py but with
the addition of a webserver to publish performance data.

Grandfather clock speed regulator
Nominal pendulum tick-tock rate is 66 ticks/min.

An IR sensor is mounted to detect pendulum movement past BDC.
The value of the sensor is normally high when nothing is detected.
It goes low when it detects the rod extending below the bob.

The pendulum 'bob' is adjusted (mechanically) to run slightly slow.
An electro-magnet at BDC is used to speed up the pendulum as needed.

Without the influence of the electro-magnet,
the clock runs approximately 2 sec/hour slow.
When the electro-magnet (positioned with a 1/4 inch gap) is turned ON,
the clock runs approximately 8 sec/hour fast.

After every 'batch' of 66 ticks, the RTC time (h:m:s) is fetched.
If the value of s is above a target value = 30, the electro-magnet
is turned on for the next cycle (batch).
If s is at or below the target value, the electro-magnet is turned off.

In mormal operation, the clock will tick merrily along, with the
electro-magnet turned on for approximately one minute of every four,
clock time synced to the RTC within less than 1 second.
"""

import gc
from  machine import Pin, RTC
import network
from ntptime import settime
import time
import urequests
import _thread
from secrets import secrets
import uasyncio as asyncio
import socket

# Global values
gc_text = ''
data = []
MAXLEN = 50  # max len(data)
ssid = secrets['ssid']
password = secrets['wifi_password']

html = """<!DOCTYPE html>
<html>
    <head> <title>Clock Regulator</title> </head>
    <body> <h1>Clock Regulator</h1>
        <pre>%s</pre>
    </body>
</html>
"""

# setup pins for LED, Electro_magnet, Pendulum_sensor
led = Pin("LED", Pin.OUT, value=0)  # LED
em = Pin(3, Pin.OUT, value=0)  # Electro_magnet
sensor = Pin(4, Pin.IN, Pin.PULL_UP)  # Pendulum_sensor

count = 0  # Accumulated number of elapsed 'ticks'
snsr_high = False  # status previous time through loop

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

    text = ''
    for line in data:
        text += line
    text += gc_text

    response = html % text
    writer.write('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
    writer.write(response)

    await writer.drain()
    await writer.wait_closed()
    print("Client disconnected")

async def main():
    global snsr_high, count, data, gc_text
    print('Connecting to Network...')
    connect_to_network()

    # Pico Real Time Clock
    rtc = RTC()
    local_time = rtc.datetime()
    print("Initial (rtc)  ", local_time)

    # Set RTC to (utc) time from ntp server
    print('setting rtc to UTC...')
    try:
        settime()
    except OSError as e:
        print('OSError', e, 'while trying to set rtc')

    gm_time = rtc.datetime()
    print("rtc reset (UTC)", gm_time)

    print('Setting up webserver...')
    asyncio.create_task(asyncio.start_server(serve_client, "0.0.0.0", 80))

    while True:
        # Turn led 'on' when sensor.value goes low, 'off' when high
        if not sensor.value() and snsr_high:  # leading edge
            snsr_high = False
            led.on()
            count += 1
        elif sensor.value() and not snsr_high:  # trailing edge
            snsr_high = True
            led.off()

        # Once every 66 ticks
        if count == 66:
            current_time = rtc.datetime()
            print(str(current_time))
            h = current_time[4]  # curr hour (UTC)
            m = current_time[5]  # curr minute
            s = current_time[6]  # curr second
            str_curr_time = '%s:%s:%s (UTC)' % (h, m, s)
            
            # reset counter
            count = 0
            
            # set time to NTP server once daily
            if h == 1 and m == 0:
                try:
                    settime()
                except OSError as e:
                    print('OSError', e, 'while trying to set rtc')
            
            # Decide if the electro-magnet should be energized
            if s > 30:
                em.on()
                print("Electro-magnet ON")
                data.append(str_curr_time + ' EM_ON\n')
            else:
                em.off()
                print("Electro-magnet OFF")
                data.append(str_curr_time + ' EM_OFF\n')
            if len(data) > MAXLEN:
                data.pop(0)
            
            # collect garbage hourly
            if m == 0:
                gc_text = 'free: ' + str(gc.mem_free()) + '\n'
                gc.collect()

        await asyncio.sleep(0.005)  # debounce delay

try:
    asyncio.run(main())
finally:
    asyncio.new_event_loop()
