"""
Run a webserver in a separate thread (on core 2)
publishing the contents of data.txt
"""

import gc
import micropython
from  machine import Pin, RTC
import network
import socket
from secrets import secrets
import _thread
from time import sleep
import uasyncio as asyncio

# 2 threads will each access the same resource
#   The main loop
#   The webserver
lock = _thread.allocate_lock()

# Onboard led used to indicate mainloop activity
led = Pin("LED", Pin.OUT, value=0)

html = """<!DOCTYPE html>
<html>
    <head> <title>Pico W</title> </head>
    <body> <h1>Pico W #2</h1>
        <pre>%s</pre>
    </body>
</html>
"""

def record(line):
    """Combined print and append to data file."""
    print(line)
    line += '\n'
    lock.acquire()
    with open(datafilename, 'a') as file:
        file.write(line)
    lock.release()

def connect_to_network():
    wlan.active(True)
    # wlan.config(pm = 0xa11140) # Disable power-save mode
    wlan.connect(secrets['ssid'], secrets['wifi_password'])

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


def start_webserver():
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(1)
    while True:
        cl, addr = s.accept()
        cl_file = cl.makefile('rwb', 0)

        lock.acquire()
        with open('data.txt') as file:
            data = file.read()
        lock.release()

        while True:
            line = cl_file.readline()
            if not line or line == b'\r\n':
                break
        response = html % data

        cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
        cl.send(response)
        cl.close()

async def do_stuff():
        print()
        print('free:', str(gc.mem_free()))
        print('info:', str(gc.mem_alloc()))
        print('info:', str(micropython.mem_info()))
        # Force garbage collection
        gc.collect()
        # Flash LED
        for _ in range(3):
            led.on()
            await asyncio.sleep(0.1)
            led.off()
            await asyncio.sleep(0.1)
        await asyncio.sleep(30)


if __name__ == "__main__":
    # Connect to network
    wlan = network.WLAN(network.STA_IF)
    print('Connecting to Network...')
    connect_to_network()
    
    # Start webserver in separate thread
    _thread.start_new_thread(start_webserver, ())
    
    # Do some stuff in the main thread
    while True:
        asyncio.run(do_stuff())
