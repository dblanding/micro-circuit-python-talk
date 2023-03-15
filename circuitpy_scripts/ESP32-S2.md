# I got the Metro ESP32-S2 Express ($19.95 from Amazon)
* Loading CircuitPython on it was a little bit trickier than it was on the M0 and M4.
* Found some useful advice on the forum at [Metro ESP32-S2 circuitpython bin not loading](https://forums.adafruit.com/viewtopic.php?p=894208&hilit=load+circuitpython+on+metro+esp32+s2#p894208)
* Summary of the <a href="ESP32-S2_setup.md" target="_blank">Setup process</a>
* Below are listed the 'builtin' modules on the **Metro ESP32-S2 Express** board:
```
Adafruit CircuitPython 8.0.2 on 2023-02-14; Adafruit Metro ESP32S2 with ESP32S2
>>> help("modules")
__future__        digitalio         msgpack           sys
__main__          displayio         neopixel_write    terminalio
_asyncio          dualbank          nvm               time
_pixelmap         errno             onewireio         touchio
adafruit_bus_device                 espcamera         os                traceback
adafruit_bus_device.i2c_device      espidf            paralleldisplay   ulab
adafruit_bus_device.spi_device      espulp            ps2io             ulab
adafruit_pixelbuf fontio            pulseio           ulab.numpy
aesio             framebufferio     pwmio             ulab.numpy.fft
alarm             frequencyio       qrio              ulab.numpy.linalg
analogio          gc                rainbowio         ulab.scipy
array             getpass           random            ulab.scipy.linalg
atexit            gifio             re                ulab.scipy.optimize
audiobusio        hashlib           rgbmatrix         ulab.scipy.signal
audiocore         i2cperipheral     rotaryio          ulab.scipy.special
audiomixer        i2ctarget         rtc               ulab.utils
binascii          io                sdcardio          usb_cdc
bitbangio         ipaddress         select            usb_hid
bitmaptools       json              sharpdisplay      usb_midi
board             keypad            socketpool        uselect
builtins          math              ssl               vectorio
busio             mdns              storage           watchdog
canio             memorymap         struct            wifi
collections       microcontroller   supervisor        zlib
countio           micropython       synthio
Plus any modules on the filesystem
```
The only library I needed (that wasn't built in) was `adafruit_ntp.mpy` which I dragged from `adafruit-circuitpython-bundle-8.x-mpy-20230215/` and dropped into the `~/CIRCUITPY/lib/` folder.

I got a bit more info on how to sync the RTC w/ NTP from [ RTC, TIME, NTP on ESP32-S2 #3321](https://github.com/adafruit/circuitpython/issues/3321). To set the onboard RTC, simply run the following code:
```
import rtc
rtc.RTC().datetime = ntp.datetime
```
Without first syncing to ntp, the rtc would initialize to Midnight on Jan1, 2000 on power-up.

## AT last! The **Metro ESP32-S2 Express** fills the bill!

* The Metro M0 Express doesn't have WiFi, nor does it have an rtc.
    * The cheap rtc I added for my grandfather clock project drifts ~ a minute / month
* The Metro M4 AirLift Express has WiFi, but its performance is HORRIBLE!
* It looks like the **Metro ESP32-S2 Express** will work great for both of my projects:
    * Grandfather Clock Regulation
    * Carriage Lights Control

carriage_lights.py
```
import adafruit_requests
import ipaddress
import ssl
import adafruit_ntp
import rtc
import socketpool
import time
import wifi
from secrets import secrets

lat = secrets['lat']
long = secrets['long']

# URLs to fetch from
SUNSET_URL = "http://api.sunrise-sunset.org/json?lat=%f&lng=%f&formatted=0" % (lat, long)
LIGHTS_ON_URL = "http://192.168.1.54/control?cmd=event,setON"
LIGHTS_OFF_URL = "http://192.168.1.54/control?cmd=event,setOff"

# Default sunset time: Hour Minute Second
H = 18
M = 20
S = 0

wifi.radio.connect(secrets["ssid"], secrets["password"])

pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())
ntp = adafruit_ntp.NTP(pool, tz_offset=secrets["tz_offset"])

# Sync rtc with ntp time
rtc.RTC().datetime = ntp.datetime


def get_sunset_time():
    """Get time of today's sunset. return (H, M, S)"""
    response = requests.get(SUNSET_URL)
    data = response.json()
    utc_sunset_str = data['results']['sunset']
    date_str, time_str = utc_sunset_str.split('T')
    utc_hr_str, m_str, s_str, *rest = time_str.split(':')
    H = int(utc_hr_str) - 5
    M = int(m_str)
    S = int(s_str.split('+')[0])
    return (H, M, S)

def turn_lights_on():
    """Turn on carriage lights"""
    response = requests.get(LIGHTS_ON_URL)
    print("Lights on", response.text)

def turn_lights_off():
    """Turn off carriage lights"""
    response = requests.get(LIGHTS_OFF_URL)
    print("Lights off", response.text)

while True:
    print(rtc.RTC().datetime)
    hour = rtc.RTC().datetime.tm_hour
    minute = rtc.RTC().datetime.tm_min

    # At 5PM, update time of today's sunset
    if hour == 17 and minute == 0:
        H, M, S = get_sunset_time()
        print(H, M, S)

    # At sunset, turn on lights
    if hour == H and minute == M:
        turn_lights_on()

    # At 9:00 PM, turn lights off
    if hour == 21 and minute == 0:
        turn_lights_off()

    time.sleep(60)
```

* Problem with turning lights off using [URL](http://192.168.1.54/control?cmd=event,setOff) `http://192.168.1.54/control?cmd=event,setOff`
    * Instead of `OK`, response.text was `Unknown or restricted command!`
    * I tried using the REPL to investigate the problem, but I wasn't able to turn the lights ON or OFF from the REPL
    * Tried using [URL](http://192.168.1.54/control?cmd=GPIO,12,0) = `http://192.168.1.54/control?cmd=GPIO,12,0` but got same response.

* To investigate, I wrote a main.py program that turns the lights on then waits 10 seconde and turns them off. To my surprise, occasionally the turn Off command works OK and the turn On command fails!
```
Lights off Unknown or restricted command!
Lights on: OK
Lights off OK
Lights on: Unknown or restricted command!
Lights off OK
Lights on: OK
Lights off Unknown or restricted command!
Lights on: OK
Lights off Unknown or restricted command!
Lights on: OK
Lights off Unknown or restricted command!
Lights on: OK
Lights off Unknown or restricted command!
Lights on: OK
Lights off Unknown or restricted command!
```

# As a remedy, I decided to investigate installing a newer version of ESPEasy on a Sonoff1 & Sonoff2
* Started out using the [Random Nerd Tutorial](https://randomnerdtutorials.com/sonoff-basic-switch-esp-easy-firmware-node-red/) but this was from 2018, **and** it didn't work!
* Also came across [this](https://github.com/letscontrolit/ESPEasy/issues/2931) which gave some useful info:
```
I installed ESP_Easy_mega-20200222_normal_ESP8285_1M.bin on a couple Sonoff Basic R2's without issue. So if this bin does not work for you then more information would be helpful.

Flash again and connect using AP mode. After you enter the credentials, and before the reboot, go to the Tools=>Advanced=>Serial Log Level and set the serial log to debug. Submit (save).

The serial log will provide messages that may explain the problem. So launch your favorite serial terminal, reboot, and review all the messages from ESPEasy.

BTW, whenever problems occur from a firmware update it is wise to flash with the blank_1MB.bin file to clear out the Flash memory (removes old settings). Then flash the Mega Release.
```
* I was finally able to install ESPEasy Mega on Sonoff1 and Sonoff2 and get the WiFi credentials loaded, but the speed of response of the Web interface was ***beyond** slow. 

* I wrote up a main.py file in CircuitPython that simply turned the carriage lights on / off with 10 sec delays using these URL's instead of the rules based ones and the lights actually did as they were instructed for a couple of cycles:
    * http://192.168.1.54/control?cmd=GPIO,12,1  # ON
    * http://192.168.1.54/control?cmd=GPIO,12,0  # OFF

* **Seriously!??** This didn't work before. What is going on? Why is it working now?
    * (Perhaps the reason that it didn't work earlier is that I was doing it from the REPL)
    * I have only learned more recently that some stuff (such as print()) doesn't work from the REPL
* So I put these URL's into code.py and now it seems to work fine!
* **I need to restore ESPEasy_R120 on Sonoff1 & Sonoff2**

# [Sending email with CircuitPython](https://mjoldfield.com/atelier/2021/11/python-smtp.html)
* Tried this using smtp.gmail.com as the mail server.
    * It failed, giving the error `530 5.7.0 Must issue a STARTTLS command first.`
* Python has an smtp module that enables this, but this isn't available in CircuitPython.
```
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login(fromaddr, <password>)
text = msg.as_string()
server.sendmail(fromaddr, toaddr, text)
server.quit()
```
* I started down the road of [How to Set Up an SMTP Server on Ubuntu](https://linuxhint.com/set-up-an-smtp-server-ubuntu/)
    * But didn't follow through.
    * I decided I didn't need to do this right now. Got as far as Step 3...

## 2/27/2023 I decided to just **Cap off** the [Carriage Lights project](carriage_lights_circuitpy) and put it on a P/S and let it do its job.
