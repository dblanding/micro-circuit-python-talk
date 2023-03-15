# Set up procedure for Adafruit Metro ESP32-S2 Express board

## In a nutshell:
1. First flash the tinyuf2_combined.bin to the board.
2. Then a drive called METROS2BOOT appears on your PC.
3. Onto this drive you have to copy (in the file explorer) the CircuitPython .UF2 file. Then the CIRCUITPY device shows up.

## In Detail:
1. Plug new board into laptop -> Doesn't show up as a mounted drive
2. Open a terminal and type in `ls /dev/tty*` and look for any **new** entries when board is plugged in. -> Nope
3. Go to [ROM Bootloader](https://learn.adafruit.com/adafruit-metro-esp32-s2/rom-bootloader) page
    * Follow sequence of steps (button pushes)
        * With board plugged in do this:
            * Press and hold the DFU / Boot0 button down.
            * Press and release the Reset button.
            * Now you can release the DFU / Boot0 button
    * Try step 2 again
        * Now `/dev/ttyACM0` shows up in list
    * Install Espressif's esptool program
        * `pip3 install --upgrade esptool`
    * The command ` esptool.py --port /dev/ttyACM0 chip_id` produces the output below:

```
esptool.py v4.5
Serial port /dev/ttyACM0
Connecting...
Detecting chip type... Unsupported detection protocol, switching and trying again...
Detecting chip type... ESP32-S2
Chip is ESP32-S2 (revision v0.0)
Features: WiFi, No Embedded Flash, No Embedded PSRAM, ADC and temperature sensor calibration in BLK2 of efuse V1
Crystal is 40MHz
MAC: 7c:df:a1:45:33:42
Uploading stub...
Running stub...
Stub running...
Warning: ESP32-S2 has no Chip ID. Reading MAC instead.
MAC: 7c:df:a1:45:33:42
WARNING: ESP32-S2 (revision v0.0) chip was placed into download mode using GPIO0.
esptool.py can not exit the download mode over USB. To run the app, reset the chip manually.
To suppress this note, set --after option to 'no_reset'.
```

4. Go to [Install UF2 Bootloader](https://learn.adafruit.com/adafruit-metro-esp32-s2/install-uf2-bootloader) page
    * Download latest release of TinyUF2 for ESP32-S2 board (zip file)
    * Unzip the file and find `combined.bin` file
    * Use esptool to upload file to board 
        * `esptool.py --port /dev/ttyACM0 --after=no_reset write_flash 0x0 /home/doug/metro_express/ESP32-S2_files/tinyuf2-adafruit_metro_esp32s2-0.12.3/combined.bin`
        * This produces the output shown below:
    * Click **RESET** button on board
        * `METROS2BOOT` device (boot folder) now shows up on my Desktop

```
esptool.py v4.5
Serial port /dev/ttyACM0
Connecting...
Detecting chip type... Unsupported detection protocol, switching and trying again...
Detecting chip type... ESP32-S2
Chip is ESP32-S2 (revision v0.0)
Features: WiFi, No Embedded Flash, No Embedded PSRAM, ADC and temperature sensor calibration in BLK2 of efuse V1
Crystal is 40MHz
MAC: 7c:df:a1:45:33:42
Uploading stub...
Running stub...
Stub running...
Configuring flash size...
Flash will be erased from 0x00000000 to 0x002f5fff...
Compressed 3100704 bytes to 119721...
Wrote 3100704 bytes (119721 compressed) at 0x00000000 in 17.6 seconds (effective 1408.1 kbit/s)...
Hash of data verified.

Leaving...
Staying in bootloader.
```

5. Download UF2 file from https://circuitpython.org/board/adafruit_metro_esp32s2/
    * Drag and drop this file into the boot folder
        * file version 8.0.2 for my board #1
        * file version 8.0.3 for my board #2
    * This causes boot folder to no longer be visible. `CIRCUITPY` device now shows up in its place (under `/media/doug/`)

Setup complete!

Note: In order to update CircuitPython to the latest version, you need to drag and drop the latest version into the boot folder.
* In order to get back to the boot folder, double press reset. The timing can be tricky. After the initial press, watch the neopixel. When it turns purple, press again. Then you should get the METROS2BOOT folder. And the neopixel should be green.
    * Did this to upgrade board #1 from 8.0.2 to 8.0.3

