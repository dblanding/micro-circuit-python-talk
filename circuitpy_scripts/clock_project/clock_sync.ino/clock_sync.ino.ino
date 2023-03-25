
/*
  Using:
  https://RandomNerdTutorials.com/esp32-date-time-ntp-client-server-arduino/
  to get time from time server
    
  How to use internal RTC of ESP32
  https://www.theelectronics.co.in/2022/04/how-to-use-internal-rtc-of-esp32.html
  to generate time pulses from internal RTC of ESP32
*/

#include <WiFi.h>
#include "time.h"
#include <ESP32Time.h>

const char* ssid     = "NETGEAR90";
const char* password = "exoticgadfly005";

const char* ntpServer = "pool.ntp.org";
const long  gmtOffset_sec = -3600*5;
const int   daylightOffset_sec = 3600;

//ESP32Time rtc;
ESP32Time rtc(0);

void setup() {
  Serial.begin(115200);
  
  // Connect to Wi-Fi
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi connected.");
  
  // Init and get the time
  configTime(gmtOffset_sec, daylightOffset_sec, ntpServer);

  /*---------set RTC with NTP---------------*/
  struct tm timeinfo;
  if (getLocalTime(&timeinfo)){
    rtc.setTimeStruct(timeinfo);
    Serial.println(rtc.getTime("%A, %B %d %Y %H:%M:%S"));
    // formating options  http://www.cplusplus.com/reference/ctime/strftime/
  }
}

void loop() {
//  Serial.println(rtc.getTime());          //  (String) 15:24:38
//  Serial.println(rtc.getDate());          //  (String) Sun, Jan 17 2021
//  Serial.println(rtc.getDate(true));      //  (String) Sunday, January 17 2021
//  Serial.println(rtc.getDateTime());      //  (String) Sun, Jan 17 2021 15:24:38
//  Serial.println(rtc.getDateTime(true));  //  (String) Sunday, January 17 2021 15:24:38
//  Serial.println(rtc.getTimeDate());      //  (String) 15:24:38 Sun, Jan 17 2021
//  Serial.println(rtc.getTimeDate(true));  //  (String) 15:24:38 Sunday, January 17 2021
//
//  Serial.println(rtc.getMicros());        //  (long)    723546
//  Serial.println(rtc.getMillis());        //  (long)    723
//  Serial.println(rtc.getEpoch());         //  (long)    1609459200
//  Serial.println(rtc.getSecond());        //  (int)     38    (0-59)
  Serial.println(rtc.getMinute());        //  (int)     24    (0-59)
//  Serial.println(rtc.getHour());          //  (int)     3     (0-12)
//  Serial.println(rtc.getHour(true));      //  (int)     15    (0-23)
//  Serial.println(rtc.getAmPm());          //  (String)  pm
//  Serial.println(rtc.getAmPm(true));      //  (String)  PM
//  Serial.println(rtc.getDay());           //  (int)     17    (1-31)
//  Serial.println(rtc.getDayofWeek());     //  (int)     0     (0-6)
//  Serial.println(rtc.getDayofYear());     //  (int)     16    (0-365)
//  Serial.println(rtc.getMonth());         //  (int)     0     (0-11)
//  Serial.println(rtc.getYear());          //  (int)     2021

//  Serial.println(rtc.getLocalEpoch());         //  (long)    1609459200 epoch without offset
  Serial.println("Tick");
  delay(1000);
}
