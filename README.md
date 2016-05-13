# WiFi-tracker

* This is a 3rd year students (BN311) project of [Institute of Technology, Blanchardstown] (http://www.itb.ie)

* Application was written for Kali Linux.
* It is collecting wifi management probes and beacons from mobile device in a passive mode.
* After probes are collected application converts SSIDs to geolocations using Wigle.net (you need an account) and plots markers on googlemap.
* Application can also Wifijam last seen beacons.
* There is a def with telegram bot alerts, which can send "mac addr, station name" for the security perimeter feature of the application.

* Please note, that application is still under development. 

### Stuff used in this project:

Many thanks authors of the projects below for inspiration!

* [Hydrogen] (https://github.com/hydrogen18/probecap)
* [Wifijammer] (https://github.com/DanMcInerney/wifijammer) 
* [Viraptor] (https://github.com/viraptor/wigle)
* [gmplot] (https://pypi.python.org/pypi/gmplot/1.0.5) 
* [manuf.py] (https://github.com/coolbho3k/manuf.py)

###TO-DOs
* Create a fork of the application acting as a Wi-Fi perimeter monitoring tool
* Add Telegram bot functionality
* Enhance security and usability
