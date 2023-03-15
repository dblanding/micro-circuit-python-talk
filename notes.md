# Notes on MicroPython / CircuitPython in preparation for HOT presentation

## Advice from Yang:
```
I'm fine with you being the judge of group interest.  A presentation on Circuit Python would be good regardless of the example.

Just off the top:
Aduino IDE vs CircuitPython
    - maybe blinky program in both?
    - which has better libraries & where to find them?
    - sources for open source SW?
Adafruit
    - should I be concerned with Adafruit sucking me into  their system/environment?
    - alternatives to Adafruit hardware?  software?
CircuitPython vs MicroPython
    - Difference?
    - Which to start in?
Learning resources
    - Tips for beginner - where/how to start?
```

## Relevant links:
* Video (55 min) presented at FOSDEM '23 [An Introduction to MicroPython](https://ftp.osuosl.org/pub/fosdem/2023/UD2.218A/python_micropython_intro.mp4)
* Random Nerd Tutorials [Getting Started with Thonny MicroPython (Python) IDE for ESP32 and ESP8266](https://randomnerdtutorials.com/?s=flash+firmware+onto+8266)
* [Sonoff DIY Smart Switch Project](https://drive.google.com/file/d/1whJVSwAy5lDRt20VTkXW4LZ6KZNcHsqH/view)
* [What is the difference between Python and MicroPython?](https://www.educative.io/answers/what-is-the-difference-between-python-and-micropython)

* [MicroPython vs Python](https://linuxhint.com/micropython-vs-python-comparison/)

* Video: [CircuitPython vs Micropython](https://core-electronics.com.au/videos/circuitpython-vs-micropython-key-differences)

* Video: [Basic Comparison Between MicroPython and Arduino](https://www.youtube.com/watch?v=4eL5tQLDE2o)

* [Official MicroPython Website](https://micropython.org/)
* Official [pyboard](https://store.micropython.org/pyb-features)

* Video [Most Popular Programming Languages](https://statisticsanddata.org/data/the-most-popular-programming-languages-1965-2022-new-update/)
* Asked on CircuitPython Forum if there is a [library to send emails](https://forums.adafruit.com/viewtopic.php?p=963132#p963132) like uMail in MicroPython

## 3/6/23 Looked into trying out MicroPython

* From the [Official MicroPython Website](https://micropython.org/), it looks like MicroPython comes pre-loaded onto specific boards, such as the [MicroPython pyboard - v1.1](https://www.adafruit.com/product/2390) currently out of stock but priced at $44.95.
* In fact all the boards listed in the [MicroPython Store](https://store.micropython.org/) are out of stock.
* So maybe it isn't possible to try out MicorPython right now?
* Watched the latter part of [Wouter van Ooijen's talk](https://ftp.osuosl.org/pub/fosdem/2023/UD2.218A/python_micropython_intro.mp4) and see what I can learn about how MicorPython works.
    * He recommends trying out MicroPython on the Raspberry Pi PICO-W RP2040
        * Ordered one from Amazon $12.95 + tax
        * Also ordered a book  [Get Started with MicroPython on Raspberry Pi Pico](https://www.mclibre.org/descargar/docs/revistas/hackspace-books/hackspace-get-started-with-micropython-on-pico-01-202101.pdf) by Gareth Halfacree
        * Looks like I should be able to get started right away!

## Install MicroPython on Raspberry Pi Pico-W RP2040
* Install Thonny 
    * Temporarily remove 'conda lines' from ~/.bashrc, exposing python3.8
        * $ `pip install thonny`
* Now Thonny can be started from normal terminal
    * (base) $ `thonny`
* Drag & Drop installation of MicroPython onto Pico

![Drag&Drop Micor-Python Animated GIF](imgs/MicroPython-640x360-v2.gif)

* STEP 1 above shows downloading the UF2 file.
    * This actually happens after step 3
* STEP 2 actually happens first
    * Press and hold the 'BOOTSEL' button
    * Plug in the USB cable
    * Release the 'BOOTSEL' button
    * 'RPI-RP2' now shows up mounted in the host computer's filesystem
* In STEP 3 above:
    * A file browser shows 2 files under 'RPI-RP2':
        * INFO_UF2.TXT (Contents of file shown below)
        * INDEX.HTM
            * clicking on INDEX.HTM redirects to [The official documentation for Raspberry Pi computers and microcontrollers](https://www.raspberrypi.com/documentation/microcontrollers/?version=E0C9125B0D9B)
                * clicked on **MicroPython** Getting started with MicroPython
                    * Clicked on download MicroPython UF2 file for Raspberry Pi Pico W
* STEP 4 --> Drag & Drop the downloaded .UF2 file into the 'RPI-RP2' folder
* STEP 5 --> Done. Micropython is now loaded on the Pico. Start Thonny.

_________________________
Contents of INFO_UF2.TXT:
```
UF2 Bootloader v3.0
Model: Raspberry Pi RP2
Board-ID: RPI-RP2
```
_________________________

## Documentation for MicroPython on Raspberry Pi Pico W

* [The official documentation for Raspberry Pi computers and microcontrollers](https://www.raspberrypi.com/documentation/microcontrollers/?version=E0C9125B0D9B)
    * [Connecting to the Internet with Raspberry Pi Pico W](https://datasheets.raspberrypi.com/picow/connecting-to-the-internet-with-pico-w.pdf)
* [Official MicroPython documentation (for the RP2)](https://docs.micropython.org/en/latest/rp2/general.html)
* Kevin McAleer video [Micropython Threads - Use Both Cores, on Raspberry Pi Pico and ESP32](https://www.youtube.com/watch?v=QeDnjcdGrpY)
* Andreas Spiess video #240 [Time to Say Good-Bye (to Arduino)](https://www.youtube.com/watch?v=m1miwCJtxeM&list=RDCMUCu7_D0o48KbfhpEohoP7YSQ&index=11)
* Andreas Spiess video #370 [Pi Pico vs Competition](https://www.youtube.com/watch?v=cVHCllbN3bQ)
* Andreas Spiess video #372 [How to use the two Cores of the Pi Pico? And how fast are Interrupts?](https://www.youtube.com/watch?v=9vvobRfFOwk) 
* Drone Bot Workshop [CircuitPython with Raspberry Pi Pico](https://www.youtube.com/watch?v=07vG-_CcDG0)


## Time: RTC, NTP

* [Pico / Pico W - Real Time Clock RTC - Sync Time with NTP](https://forums.raspberrypi.com/viewtopic.php?t=337259)

```
After connecting a PICO to Thonny the RTC registers are set to your computer's time. As long as power is maintained to the PICO you will have UTC time within some number of milliseconds of your computer's time plus drift.
```
The Pico RTC `rtc.datetime()` reports a tuple of 8 values:
```
(year, month, day_of_mo, day_of_wk, hour, minute, second, is_dst)
```
Running the following code:
```
rtc = machine.RTC()
print(rtc.datetime())

# Get time from ntp server (use UTC)
ntptime.settime()
print(rtc.datetime())
```
produces the following output:
```
(2023, 3, 9, 3, 7, 10, 30, 0)
(2023, 3, 9, 3, 12, 10, 32, 0)
```
* The RTC was initially set by Thonny and had the correct local time.
* Then 2 seconds later set by the NTP server.
    * Note the 5 hour time difference (NTP server sets the RTC to UTC)
* According to advice on the internet:
```
Time zones are an enormous PITA, and almost certainly too much trouble for a microcontroller.
You're much better off just keeping time as UTC on the Pico, exactly as you get it from NTP, and leave it at that. If conversions to local time zones are necessary, hand the data off to your host system and let the host do it.
Friends don't let friends mess around with local time zones on a microcontroller.
```
* Sometimes I get `oserror errno 110 etimedout` when I call settime()
    * Fixed it (we'll see) with a try / except block
* [How To Make A Raspberry Pi Pico W Web Server](https://www.tomshardware.com/how-to/raspberry-pi-pico-w-web-server)
    * Add this to allow me to check status of lights control when operating headless.
* A Potentially interesting project: [The Golden Age of Wireless: Adopting Raspberry Pi’s Pico W](https://blog.smittytone.net/2022/07/29/the-golden-age-of-wireless-adopting-raspberry-pis-pico-w/)

## OSError: [Errno 12] ENOMEM / Garbage Collection

* Getting OSError: [Errno 12] ENOMEM (Error NO MEMory)
    * My main while loop was chewing through all its memeory
    * Program wouldn't run a full day
    * Added the following lines into loop
    * The free memory would print every 10 minutes and just kept going down until there was none left
    
```
print('free:', str(gc.mem_free()))
print('info:', str(gc.mem_alloc()))
print('info:', str(micropython.mem_info()))
```

* Automatic garbage collection wasn't working
* Adding `gc.collect()` line to force garbage collection solved the problem
* Using gc.ccollect(): [MicroPython on microcontrollers](https://docs.micropython.01studio.org/zh_CN/latest/reference/constrained.html)
    *  See 'Strings vs Bytes' 1/2 way down the page
