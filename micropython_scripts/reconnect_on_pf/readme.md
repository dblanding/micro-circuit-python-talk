# Explore robust code to make the Pico W devices more tolerant of power failure
* When the power goes out, however briefly, the pico W devices lose their WiFi connection and must be manually restarted in order to recover.
* This file explores a way to periodically test the WiFi connection and reconnect it if needed.

## The code here is based on the garage temperature sensor, which has a 1 second loop delay.
* Both the garage door sensor and temperature sensor have 1 second loop delays, making them easier to test (by interrupting power to the router). In contrast, the clock and lights have loop delays on the order of 1 minute.
* In tests where, the router power is cycled, this code seems to work well. Now I will leave it running and wait for the occurrence of some actual power outages.
