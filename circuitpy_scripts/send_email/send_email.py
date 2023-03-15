"""
Adapted from https://mjoldfield.com/atelier/2021/11/python-smtp.html
I tried to get it to work by using gmail as the smtp server but it does
not work. The gmail server complains that I need to send the command to
STARTTLS and then communicate in TLS mode.
Python has an smtp library that does this, but CircuitPYthon doesn't.
"""

import board
import time
import alarm
import digitalio
import wifi
import socketpool

from secrets import secrets

sleep_time = 10 # seconds

def wifi_connect():
    print("My MAC addr:", [hex(i) for i in wifi.radio.mac_address])

    print("Available WiFi networks:")
    for network in wifi.radio.start_scanning_networks():
    	print("\t%s\t\tRSSI: %d\tChannel: %d" % (str(network.ssid, "utf-8"),
    			network.rssi, network.channel))
    wifi.radio.stop_scanning_networks()

    print("Connecting to AP...")
    wifi.radio.connect(secrets["ssid"], secrets["password"])

    network = wifi.radio.ap_info
    print("Connected to {} via {}, RSSI = {}".format(
    	   network.ssid, network.authmode, network.rssi))
    print("My IP address is", str(wifi.radio.ipv4_address))

def mail_open_socket():
    server = secrets["smtp_server"]
    print("Connecting to mail server ", server)
    pool = socketpool.SocketPool(wifi.radio)
    sock = pool.socket()
    addr = (server, 587)
    sock.connect(addr)
    return sock

def mail_rxtx(s, msg):
    if msg is not None:
    	print('> ' + msg)
    	s.send(msg.encode('ascii') + b'\n')

    buff_size = 1024
    buff = bytearray(buff_size)
    s.recv_into(buff)
    x = buff.decode('ascii')
    print('< ' + x.rstrip())
    return x

def mail_send(m_subj, m_msg):
    m_from = secrets["mail_from"]
    m_to   = secrets["mail_to"]

    s = mail_open_socket()
    mail_rxtx(s, None)
    mail_rxtx(s, "HELO pico")
    mail_rxtx(s, "MAIL FROM:{}".format(m_from))
    mail_rxtx(s, "RCPT TO:{}".format(m_to))
    mail_rxtx(s, "DATA")
    mail_rxtx(s, "From: {}\nTo: {}\nSubject: {}\n\n{}\n.".format(m_from, m_to, m_subj, m_msg))

if __name__ == "__main__":
    print("connecting to wifi")
    wifi_connect()
    time.sleep(sleep_time)

    print("Send email")
    m_subj = "Hello World!"
    m_msg  = "Your text goes here"
    mail_send(m_subj, m_msg)
