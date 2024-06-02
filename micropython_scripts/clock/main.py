"""
MicroPython (on Pico) speed regulator for grandfather clock
Nominal pendulum tick rate is 66 ticks/min.

* includes a webserver to publish performance data and error log
* automatic re-connect to WiFi after power failure
* OTA updates on power-up

An IR sensor is mounted to detect pendulum movement past BDC.
The value of the sensor is normally high when nothing is detected.
It goes low when it detects the rod extending below the bob.

The pendulum 'bob' is adjusted (mechanically) to run slightly slow.
An electro-magnet at BDC is used to speed up the pendulum as needed.

Without the influence of the electro-magnet,
the clock runs approximately 2 sec/hour slow.
When the electro-magnet (positioned with a 1/4 inch gap) is turned ON,
the clock runs approximately 8 sec/hour fast.

At power-up, connect to WiFi and check for OTA updates, then set time
to UTC. Get time (h:m:s). When the value of s reaches 30, start main loop.
Within the loop, count the ticks of the pendulum. 
Once 66 ticks are counted, check the time again. If s > 30,
the electro-magnet is turned on, otherwise it remains off.

In normal operation, the clock ticks merrily along, with the
value of s mostly staying at 30, changing to 31 every 3 or 4 cycles.
"""

import gc
from  machine import Pin
import network
from ntptime import settime
import time
import urequests
from secrets import secrets
import uasyncio as asyncio
from ota import OTAUpdater

# Global values
gc_text = ''
data = []
MAXLEN = 50  # max len(data)
ERRORLOGFILENAME = 'errorlog.txt'
ssid = secrets['ssid']
password = secrets['wifi_password']

html = """<!DOCTYPE html>
<html>
    <head> <title>Clock Regulator</title> </head>
    <body> <h1>Clock Regulator</h1>
        <h3>%s</h3>
        <pre>%s</pre>
    </body>
</html>
"""

# setup pins for LED, Electro_magnet, Pendulum_sensor
led = Pin("LED", Pin.OUT, value=0)  # LED
em = Pin(3, Pin.OUT, value=0)  # Electro_magnet
sensor = Pin(4, Pin.IN, Pin.PULL_UP)  # Pendulum_sensor

wlan = network.WLAN(network.STA_IF)

def timestamp():
    Dyear, Dmonth, Dday, Dhour, Dmin, Dsec, *rest = time.localtime()
    DdateandTime = "{:02d}/{:02d}/{} {:02d}:{:02d}:{:02d}"
    return DdateandTime.format(Dmonth, Dday, Dyear, Dhour, Dmin, Dsec)

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

def sync_to_ntp():
    """Sync Pico clock to UTC time."""
    try:
        settime()
    except OSError as e:
        with open(ERRORLOGFILENAME, 'a') as file:
            file.write(f"{timestamp()} OSError while trying to set time: {str(e)}\n")
    print('setting time to UTC...')

def get_curr_time():
    current_time = time.localtime()
    h = current_time[3]  # curr hour (UTC)
    m = current_time[4]  # curr minute
    s = current_time[5]  # curr second
    return h, m, s

async def serve_client(reader, writer):
    try:
        print("Client connected")
        request_line = await reader.readline()
        print("Request:", request_line)
        # We are not interested in HTTP request headers, skip them
        while await reader.readline() != b"\r\n":
            pass

        if '/err' in request_line.split()[1]:
            with open(ERRORLOGFILENAME) as file:
                text = file.read()
            heading = "ERRORS"
        else:
            text = ''
            for line in data:
                text += line
            text += gc_text
            heading = "Append '/err' to URL to see error log"

        response = html % (heading, text)
        writer.write('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
        writer.write(response)

        await writer.drain()
        await writer.wait_closed()
        print("Client disconnected")
    except Exception as e:
        with open(ERRORLOGFILENAME, 'a') as file:
            file.write(f"{timestamp()} serve_client error: {str(e)}\n")

async def main():
    global data, gc_text
    print('Connecting to Network...')
    connect()

    # Check for OTA updates
    repo_name = "micro-circuit-python-talk"
    path = "micropython_scripts/clock"
    branch = "main"
    firmware_url = f"https://github.com/dblanding/{repo_name}/{branch}/{path}/"
    ota_updater = OTAUpdater(firmware_url, "main.py", "ota.py")
    ota_updater.download_and_install_update_if_available()

    # Sync time to UTC
    sync_to_ntp()
    time.sleep(1)

    _, _, s = get_curr_time()

    print('Setting up webserver...')
    asyncio.create_task(asyncio.start_server(serve_client, "0.0.0.0", 80))

    # Wait until s == 30
    while s != 30:
        _, _, s = get_curr_time()
        time.sleep(1)

    count = 0  # Accumulated number of elapsed 'ticks'
    snsr_high = False  # status previous time through loop

    while True:
        # Turn led 'on' when sensor.value goes low, 'off' when high
        if not sensor.value() and snsr_high:  # leading edge
            snsr_high = False
            led.on()
            count += 1
        elif sensor.value() and not snsr_high:  # trailing edge
            snsr_high = True
            led.off()

        try:
            # Once every 66 ticks
            if count == 66:
                h, m, s = get_curr_time()
                str_curr_time = '%s:%s:%s (UTC)' % (h, m, s)
                
                # reset counter
                count = 0
                
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

        except Exception as e:
            with open(ERRORLOGFILENAME, 'a') as file:
                file.write(f"{timestamp()} main loop error: {str(e)}\n")

        await asyncio.sleep(0.005)  # debounce delay

try:
    asyncio.run(main())
finally:
    asyncio.new_event_loop()
