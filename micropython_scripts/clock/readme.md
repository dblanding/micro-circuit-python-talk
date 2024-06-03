# Using an electro-magnet to regulate the speed of a grandfather clock

## How a standard grandfather clock works:
* A grandfather clock relies on a swinging pendulum to maintain the speed of the clock.
* The natural period of oscillation of the swinging pendulum is exactly determined by the length of the pendulum and the downward force of gravity.
* The mass of the pendulum **bob** is not a factor in the equation.

![pendulum-escapement](imgs/pendulum-escapement.gif)
![pendulum Equation](imgs/pendulum_equation.jpg)

* A typical grandfater clock "ticks" at a rate of exactly **66 ticks per minute**
* The period of oscillation **T** is equal to the time for the pendulum to make **2 Ticks**

## How the speed of a grandfather clock can be influnced:

* By placing an [electro-magnet](https://www.amazon.com/gp/product/B07H3V8N2Q/ref=ppx_yo_dt_b_asin_title_o03_s00?ie=UTF8&psc=1) below the pendulum at the bottom dead center (BDC) position, we can use the electro-magnet to slightly **augment** the force of gravity.
* By energizing the elecro-magnet, the period of oscillation will be slightly reduced, thus **speeding up the clock** slightly.

## How the speed of the grandfather clock is detected

* An [infrared sensor module](https://www.amazon.com/dp/B07FJLMLVZ?psc=1&ref=ppx_yo2ov_dt_b_product_details) is positioned to detect the pendulum as it swings through BDC.
* This sensor generates a brief pulse every time the pendulum crosses BDC.
* The pulses are counted.
* With every 66 pulses, the time given by the microprocessor's RTC should show another elapsed minute.

## Mechanical configuration:

![mech config](imgs/IMG-3250.jpg)

## The way the program works:

* The Pendulum length is adjusted to make the clock run slightly **SLOW**
* After every 66 pulses, the value of **s** (seconds given by the RTC) is obtained.
    * If the value exceeds the target value, the electro-magnet is energized
    * Otherwise, the electro-magnet is turned off.
* In operation, the electro-magnet is off most of the time, turning on for one minute every so often.
* Since the microprocessor is onboard the clock, running in **headless** mode, the program also runs a webserver to show its recent performance.
* As seen in the image below, the clock is running slightly slow, so after 7 (+/-) batches of 66 pulses, the value of `s` changes from the target value of `30` to `31`, causing the electro-magnet to be energized.

![Web screen](imgs/web-screen.png)

* But every once in a while, for some reason, something happens to cause the `sec` value to  be way far away from 30:
such as `15:56:10 (UTC) EM_OFF`  or `15:56:50 (UTC) EM_ON`.
* I have no idea how this happens, but when it does, it takes hours for the electromagnet to bring it back to 30.
* In order to investigate, I changed the value of MAXLEN from 50 to 500, thinking I could check the history of the last 500 minutes worth of data a few times a day and maybe find a clue about the possible cause of this.
* Unfortunately, This didn't work. After about 200 lines of data had accumulated, my http request for data produced the following error:
    * `05/31/2024 15:02:22 serve_client error: memory allocation failed, allocating 3523 bytes`
    * 200 lines of data (@ roughly 22 bytes per line) = 4400 bytes, which is more than the max allowable (3523 bytes).
* So I restored the value of MAXLEN to 50 and will use a [monitor](monitor) to submit a web request every 50 minutes and write the accumulated data to a file.
    * I thought the failure might be occuring at the same time as the web request was being handled.
    * But the data shows no such correlation. 
    * Failure occured after several hours of operation, cause unknown, but not at the same time as the handling of any web request.
    * It shows that after hours of stable operation at 66 ticks/minute, a series of 'batches' of 66 ticks occured after:
        * first 38 seconds (22 sec early)
        * then 52 seconds (8 sec early)
        * then after 20 min + 33 sec (1833 sec)
        * then after 38 sec (22 sec early)
        * then after 57 sec (3 sec early)
        * then resumed normal operation (once / minute, but now displaced from the s=30 target)

````
23:20:31 (UTC) EM_ON
23:21:30 (UTC) EM_OFF
23:22:30 (UTC) EM_OFF
23:23:30 (UTC) EM_OFF
23:24:8 (UTC) EM_OFF
23:25:0 (UTC) EM_OFF
23:49:33 (UTC) EM_ON
23:50:11 (UTC) EM_OFF
23:51:8 (UTC) EM_OFF
23:52:8 (UTC) EM_OFF
23:53:8 (UTC) EM_OFF
23:54:8 (UTC) EM_OFF
````
* Whatever the cause, I don't think it's mechanical or software. A real puzzle...

## Revise Code to make it easier to monitor performance
* Start using OTA updates on startup for code modifications
* Use time.localtime() instead of RTC()
* Change TARGET_SECONDS to 1 (was 30)
* When value of s **jumps** by a value >1, record event as an error
* Change web I/F to just show current time and electro-magnet status

