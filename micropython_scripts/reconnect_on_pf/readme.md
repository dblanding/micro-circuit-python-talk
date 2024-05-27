# Explore robust code to make the Pico W devices more tolerant of power failure

* This code explores a way to periodically test the WiFi connection and reconnect if needed.

## The code here doesn't **actually do** anything. It is the code for the garage temperature sensor, which has a 1 second loop delay.

* This code also implements OTA updates, as shown by Kevin McAleer in his [MicroPython Over-the-Air updater](https://github.com/kevinmcaleer/ota)
    * I modified his code slightly
        * Whereas Kevin injects the branch name `main` in the OTAUpdater class, I chose to have the caller add it.
        * My WiFi connection is made outside of OTAUpdater, so I removed it from the OTAUpdater code.
        
## Multi-file updater
* I think it would be useful to be able to update mutiple files at once
* `OTA_multi_Updater` aims to do that.

