# lights_test.py

import adafruit_requests
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
SUNSET_URL = "http://api.sunrise-sunset.org/json?lat=%f&lng=%f&formatted=0"\
    % (lat, long)
# LIGHTS_ON_URL = "http://192.168.1.51/control?cmd=event,setON"
# LIGHTS_OFF_URL = "http://192.168.1.51/control?cmd=event,setOff"
# URL above doesn't work from CircuitPython. URL below doesn't work either
# both give 'Unknown or restricted command!'
LIGHTS_ON_URL = "http://192.168.1.54/control?cmd=GPIO,12,1"
LIGHTS_OFF_URL = "http://192.168.1.54/control?cmd=GPIO,12,0"

# Default sunset time: Hour Minute Second
H = 18
M = 20
S = 0

wifi.radio.connect(secrets["ssid"], secrets["password"])

pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())
ntp = adafruit_ntp.NTP(pool, tz_offset=secrets["tz_offset"])

# Sync rtc with ntp time
# rtc.RTC().datetime = ntp.datetime

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
    print("Lights on:", response.text)

def turn_lights_off():
    """Turn off carriage lights"""
    response = requests.get(LIGHTS_OFF_URL)
    print("Lights off", response.text)

while True:
    # print(rtc.RTC().datetime)
    turn_lights_on()

    time.sleep(10)

    # print(rtc.RTC().datetime)
    turn_lights_off()

    time.sleep(10)
