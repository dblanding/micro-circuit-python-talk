# CircuitPython Project

* Started with email from Gerald Swan [Perpetual Battery-Free Weather Station](https://makezine.com/projects/perpetual-battery-free-weather-station/)
    * Explain (briefly) why this piqued my interet and why I abandoned it.
    * I was partly invested in it, haaving ordered the Adafruit Metro M0 Express
* Gerald also shared his Grandfather clock project with me, so I decided to use the M0 for this

## Adafruit website has a `Learn` tab

* They do a good job catering to newbies
    * Getting started with CircuitPython is front and center under the Learn Tab

## Compare python (interpreted) vs compiled (C, C++) vs MicroPython

* Pull together some good visuals, showing the differences in structural topology

* Point out that CircuitPython is a derivative (fork?) of MicroPython

## Demo the Mu Editor in action, showing the way the board plugs into the computer

## Show the way the GF Clock Speed regulator works using the M0 + RTC
    
* Details of physical configuration
* Details of the way the code works
* Performance: After a month of operation, the RTC drifted about 1 minute.

## Got the M4 AirLift to be able to connect to an NTP server

* Disappointing performance in connecting to WiFi

## Got the Metro ESP32-S2 Express

* Some minor differences from the M0 & M4
    * Uses C-type USB rather than micro-USB
    * Setup to load CircuitPython
    * Lots of builtins
    * Has its own RTC
    * Worked great running NTP Connection

# Traffic Camera

## Review online resources

* Speed cams
* Vehicle counters

## Review my project
