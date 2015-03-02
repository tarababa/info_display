info_display
============

The primary purpose of this project was for me to gain some experience with Python. Over time the project has grown and bits have been added on

This project uses two Yoctopuce modules, a maxi display and the meteo module:

  * [Yocto-maxidisplay](http://www.yoctopuce.com/EN/products/usb-displays/yocto-maxidisplay)
  * [Yocto-meteo](http://www.yoctopuce.com/EN/products/usb-environmental-sensors/yocto-meteo)
  
The Elecfreak GSM/GPRS module is used to send SMS-es

  * [EFComPro GSM/GPRS](http://www.elecfreaks.com/store/gprsgsm-moduleefcom-pro-EFComPro-p-450.html)

##Functions
Quite a few, typically configurable, functions have now been included. The following chapters describe these functions
in a bit more detail.

###Navigation
For navigation the buttons on the maxi-display module are used. From left to right, the buttons are used as follows:

1. The first button moves to the next *left* menu
2. The second button moves to the next *right* menu
3. The third button moves *up* in the menu hierarchy
4. The fourth button moves *down* in the menu hierarchy
5. The fifth button is a *select* button, when supported by the chosen menu the up and down buttons can be used to view additional
data for the chosen options such as weather forecasts and loadshedding schedules for the next days on the chosen location. 
Pressing the select button a second time returns the up and down buttons tho their normal functions
6. The sixth button is now used to terminate the info-display program, except when in the "radio" menu, then it is used
to turn the radio on and off.

The image below shows the start-up screen, the buttons highlighted.
![Start-up screen](https://github.com/tarababa/info_display/blob/master/img/doc/startup_screen.png)


###Meteo
Using the output from the meteo module temprature, humidity and barometric pressure information is aggragated and shown in
in the form of graphs on the display module. Not much to configure here
![Temperature](https://github.com/tarababa/info_display/blob/master/img/doc/temperature.png)
The system is setup in such a way that one full graph shows just over 24 hours of measurements, if memory serves a sample
is taken about once every thirteen minutes.

###Wheather forecast
Using the rss feed from yr.no weather forecasts are displayed. 
![Weather forecast](https://github.com/tarababa/info_display/blob/master/img/doc/weather_forecast.png)

The locations for which weather forecasts are available can be configured in the `config.ini` configuration file under 
the section `[weather_yr]` as shown in the snippet below:
```
[weather_yr]
location.0=Langebaan,http://www.yr.no/place/South_Africa/Western_Cape/Langebaan_Lagoon/varsel.rss
location.1=Jeffrey's Bay,http://www.yr.no/place/South_Africa/Eastern_Cape/Jeffreys Bay/varsel.rss
location.2=Buchs,http://www.yr.no/place/Switzerland/Aargau/Buchs/varsel.rss
location.3=Prague,http://www.yr.no/place/Czech_Republic/Prague/Prague/varsel.rss
location.4=Best,http://www.yr.no/place/Netherlands/North_Brabant/Best/varsel.rss
location.5=Slagnäs,http://www.yr.no/place/Sweden/Norrbotten/Slagnäs/varsel.rss
location.6=Karlstad,http://www.yr.no/place/Sweden/Värmland/Karlstad/varsel.rss
location.7=Warsaw,http://www.yr.no/place/Poland/Masovia/Warsaw/varsel.rss
location.8=Newbridge,http://www.yr.no/place/Ireland/Leinster/Droichead_Nua/varsel.rss
```
Using the up and down buttons will move the menu to the next / previous location. After pressing the select button the
up and down buttons move us through the advance forecast for the selected location. Pressing the select button again 
returns the up and down buttons to their normal function.

###Exchange rate
[Yahoo's finance api](http://query.yahooapis.com) is used to visualise exchange rates over time, the graph shown captures
about 2 hours of data, queurying Yahoo about once a minute. Using the up and down buttons one can move through the available
conversions. The conversions shown are configured in the `config.ini` file under the heading `exchange_rates_yahoo` as shown
below

```
[exchange_rates_yahoo]
rate.0=CHF,ZAR
rate.1=USD,ZAR
rate.2=EUR,CHF
rate.3=CHF,USD
rate.4=CHF,SEK
rate.5=CHF,CZK
```

![Exchange rates](https://github.com/tarababa/info_display/blob/master/img/doc/exchange_rate.png)

###Load-shedding
Load-shedding is a concept not everyone, in particular in first world, may be familiar with. But in South Africa due to
years of under investment in the state owned electricty company ESKOM the country finds it self in a position where ESKOM
is not always able to meet the demand for electricity. In order to avoid a nation-wide black-out ESKOM uses rolling black-outs
turning off suburbs based on a rota system for about two and a half hours at a time. Depending on the lack of capacity it may
shed 1000MW, 2000MW or 4000MW wich corresponds with stage 1, 2 or 3 load-shedding.
The current load-shedding stage and the load-shedding schedules are published on [loadshedding.eskom.co.za](http://loadshedding.eskom.co.za),
The actual load on the system can be viewed on [MyEskom](http://myeskom.co.za), whether to expect load-shedding
on any given day and when is published on [Twitter](https://twitter.com/Eskom_SA)

Data from all three sources is pulled together to provide as accurate loadshedding information, for a suburb, as possible.
Using the up and down buttons one can view the current schedule and status for the configured suburbs. Pressing the select
button changes the function of the up and down buttons so one can move through the load-shedding schedules of the chosen
suburb for the following days and current load-shedding stage. Pressing the select button again returns the function of the
up and down buttons to normal.

The suburbs for which data is collected is configured in `config.ini` under the heading `[eskom_loadshedding]`, take note
I've not tested this with multiple suburbs configured, it should work but no guarantees...

```
[eskom_loadshedding]
schedule.0=Western Cape,Saldanha Bay,Langebaan
```

![Load-shedding](https://github.com/tarababa/info_display/blob/master/img/doc/loadshedding.png)

###Radio
A simple MPD (Music Player Daemon) client has been integrated, specifically to tune in to internet radio stations.
Using the up and down buttons one can step through the available stations. The select button changes the function
of the left and right buttons to volume control, pressing the select button again reverts the function of the left and right
buttons to normal. When the radio menu is chosen the radio is on by default and remains on even when navigated away from
the radio menu. To turn the radio of use the on/off button in the radio menu (i.e. the sixth button)

The available radio stations are configured in `config.ini` under the heading `[radio_playlist]` as shown in the example below.

```
[radio_playlist]
playlist.0=http://bbcmedia.ic.llnwd.net/stream/bbcmedia_intl_lc_radio1_q,BBC1 - UK
playlist.1=http://bbcmedia.ic.llnwd.net/stream/bbcmedia_intl_lc_radio2_p,BBC2 - UK
playlist.2=http://bbcmedia.ic.llnwd.net/stream/bbcmedia_intl_lc_radio3_p,BBC3 - UK
playlist.3=http://bbcmedia.ic.llnwd.net/stream/bbcmedia_intl_lc_radio4_p,BBC4 - UK
playlist.4=http://bbcmedia.ic.llnwd.net/stream/bbcmedia_intl_lc_radio4extra_p,BBC4 Extra - UK
playlist.5=http://bbcmedia.ic.llnwd.net/stream/bbcmedia_intl_lc_5live_p,BBC5 Live - UK
playlist.6=http://bbcmedia.ic.llnwd.net/stream/bbcmedia_intl_lc_5sportxtra_p,BB5 Sports Extra - UK
playlist.7=http://bbcmedia.ic.llnwd.net/stream/bbcmedia_intl_lc_6music_p,BBC6 Music - UK
playlist.8=mms://a219.l9068742218.c90687.g.lm.akamaistream.net/D/219/90687/v0001/reflector:42218,Rix FM - Swedish
playlist.9=http://icelive0.03872-icelive0.cdn.qbrick.com/5982/03872_mix_mp3,Mix Megapol - Swedish
playlist.10=http://http-live.sr.se/p1-mp3-192,Sveriges Radio P1 - Swedish
playlist.11=http://http-live.sr.se/p2-mp3-192,Sveriges Radio P2 - Swedish
playlist.12=http://http-live.sr.se/p3-mp3-192,Sveriges Radio P3 - Swedish
playlist.13=http://http-live.sr.se/p4sport-mp3-192,Sveriges Radio P4 sport - Swedish
playlist.14=http://icecast.omroep.nl:80/radio1-bb-mp3,Radio 1 - Dutch
playlist.15=http://icecast.omroep.nl:80/radio2-bb-mp3,Radio 2 - Dutch
Playlist.16=http://icecast.omroep.nl:80/3fm-bb-mp3, 3FM - Dutch
playlist.17=http://icecast4.play.cz:80/frekvence1-128.mp3,Frekvence 1 - Czech
playlist.18=http://pool.cdn.lagardere.cz:80/web-f1-legendy,Frekvence 1 Legendy - Czech
playlist.19=http://pool.cdn.lagardere.cz:80/web-80,Frekvence 1 Osmdesatky - Czech
playlist.20=http://icecast8.play.cz/cro1-128.mp3,ČRo Radiozurnal - Czech
playlist.21=http://icecast2.play.cz/cro2-128aac,ČRo 2 - Czech
playlist.22=http://icecast2.play.cz/cro3-128aac,ČRo 3 - Czech
playlist.23=mms://dms-cl-022.skypro-media.net/argovia-128,Radio Argovia - Swiss
playlist.24=http://stream.srg-ssr.ch/m/drs1/mp3_128,Radio SRF1 - Swiss
playlist.25=http://stream.srg-ssr.ch/m/drs2/mp3_128,Radio SRF2 - Swiss
playlist.26=http://stream.srg-ssr.ch/m/drs3/mp3_128,Radio SRF3 - Swiss
```

![Radio](https://github.com/tarababa/info_display/blob/master/img/doc/radio.png)

###Clock
A clock which shows the time in words, implemented in a configurable fashion allowing additional languages to be added.
At present an English and a Ducth clock have been configured. The clocks are configured in `clocks.ini` under a heading
indicative of the language such as `[english]` and `[dutch]`. A dot at the bottom of the screens shows the passing of seconds.

![Clock](https://github.com/tarababa/info_display/blob/master/img/doc/clock.png)

###SMS Service
A SMS service is provided through the EFComPro GSM/GPRS module. Each time the loadshedding status changes or the
forecasted loadshedding status changes all subscribers are notified by means of a SMS. Sofar only a load-shedding
SMS service has been implemented. For now the subscribers to the SMS service are configured in `sms_service.ini` under
the heading `[eskom_loadshedding]` as shown in the snippet below. I plan to rework the configuration in such a fashion
the subscribers are configured in `[config.ini]` and the `sms_service.ini` will be created as required. The data in
`sms_service.ini` and `eskom_db.ini` are used to detected whether a load-shedding SMS need to be sent.

```
[eskom_loadshedding]
subscriber.0 = +27xxxxxxxxx,langebaan
subscriber.1 = +27xxxxxxxxx,langebaan
```

![Load-shedding](https://github.com/tarababa/info_display/blob/master/img/doc/loadshedding_1.png) ![Load-shedding](https://github.com/tarababa/info_display/blob/master/img/doc/loadshedding_2.png) 
![Load-shedding](https://github.com/tarababa/info_display/blob/master/img/doc/loadshedding_3.png) ![Load-shedding](https://github.com/tarababa/info_display/blob/master/img/doc/loadshedding_4.png)


##Installation
This installation manual may not be entirely correct or complete so be warned. I will in time test this description and complete/correct as required.

###Raspbian
I'm using the [2014-09-09 wheezy Raspbian release](http://downloads.raspberrypi.org/raspbian/images/raspbian-2014-09-12/2014-09-09-wheezy-raspbian.zip), anything of a later date should work too and can be downloaded from 
the [Raspberry Pi website](http://www.raspberrypi.org/downloads/).

####USB Full speed
With the 2014-09-09 release of Raspbian I've found that the following change is not required, but on some earlier releases
the Yoctopuce hardware would not work correctly withouth the USB running in "full-speed" mode. Add `dwc_otg.speed=1` to the
/boot/cmdline.txt file as shown below.

```dwc_otg.lpm_enable=0 console=ttyAMA0,115200 kgdboc=ttyAMA0,115200 dwc_otg.speed=1 console=tty1 root=/dev/mmcblk0p2 rootfstype=ext4 elevator=deadline rootwait```

####Turn off serial console on UART
To be able to use the UART as a serial interface to the EFComPro GSM/GPRS module we need to turn of the serial console, to do so
remove any references to `ttyAMA0`` from the /boot/cmdline.txt file, in the example below `console=ttyAMA0,115200` and `kgdboc=ttyAMA0,115200`
must be removed.

```dwc_otg.lpm_enable=0 console=ttyAMA0,115200 kgdboc=ttyAMA0,115200 dwc_otg.speed=1 console=tty1 root=/dev/mmcblk0p2 rootfstype=ext4 elevator=deadline rootwait```

####cmdline.txt
Having made the changes according to the previous to chapters the my cmdline.txt looks as follows:
```dwc_otg.lpm_enable=0 dwc_otg.speed=1 console=tty1 root=/dev/mmcblk0p2 rootfstype=ext4 elevator=deadline rootwait```
For the changes to take effect the the Raspberry Pi must be restarted `sudo shutdown -r now`

###Music Deamon Player (MPD)
For the radio function to work MPD must be installed on the Raspberry Pi, the instructions below also install the Music Player Client
which is optional, the radio function does not depend on this. It may help however to test correct installation of the MPD.
```
 sudo apt-get install mpd
 sudo apt-get install mpc
```
Ensure that the `/etc/mpd.conf` configuration file reflects the folling values:
```
bind_to_address         "any"
port                    "6600"
```   
#####python-mpd2 library
The info display application uses the mpd2 library to communicate with MPD, to install:
```sudo o pip-3.2 install python-mpd2```
If Python Install tools are not isntalled, install them as follows:
```
sudo apt-get update
sudo apt-get install python3-pip
```

###lxml
To parse some of the load-shedding data we use the lxml library to install on Raspberry Pi:
```sudo apt-get install python3-lxml```
If you would like to install lxml on a Windows environment then download the [lxml package](http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml)
and install it using pip on the command window, the example below assumes the command is executed in the directory where the lxml package
was downloaded to. **Note: the latter is not required to make the application run on the Raspberry Pi**
```pip install lxml-3.4.1-cp34-none-win32.whl```
   
###Twython
A Python Twitter API, also used to collect load-shedding information (forecast), to install on Raspberry Pi:
```sudo pip-3.2 install twython```
If you would like to install Twython on a Windows environment then use pip in a command window, again this is **not required** to run
the info display application on a Raspberry Pi.
```pip install twython```

###pyserial
Python serial library used to communicate with the EFComPro GSM/GPRS module, to install on Raspberry Pi:
```sudo pip-3.2 install pyserial```
If you would like to install Twython on a Windows environment then use pip in a command window, again this is **not required** to run
the info display application on a Raspberry Pi.
```pip install pyserial```

###EFComPro GSM/GPRS
Connect TXD pin 8 of the Raspberry Pi to the Rx pin of the EFComPro module, Raspberry Pi Pin 10, RXD is connected to the TX pin
of the EFComPro module.
If using a seperate powersupply for the EFComPro module then connect GND of the EfcompPro module's powersupply to GND of the 
Raspberry Pi i.e. pin 6. The numbering of the pins on the GPIO header of the Raspberry Pi can for instance be found on this [cheatsheet](https://www.dropbox.com/s/m5l185qxq9w5mzk/raspberry-pi-gpio-cheat-sheet.jpg)

***WARNING: the Raspberry Pi is a 3.3V device, connecting 5V to the GPIO pins may cause irreversible damage to the Raspberry Pi***

###Info Display
This is the actual info display application, clone it from git:
```git clone https://github.com/tarababa/info_display.git```

####Starting info display
To start the info display application on the Raspberry Pi so it will run in the background:
```sudo nohup /usr/bin/python3 /home/pi/information_display/info_display/information_display.py &```

####Auto start info display
You can also make the info display application start automatically when the Raspberry Pi starts.
1. Make information_display.py executable: `chmod a+x information_display.py`
2.  Copy init.d configuration: `sudo cp /home/pi/info_display/etc/info_display /etc/init.d`
3.  Make info_display executable: `sudo chmod a+x /etc/init.d/info_display`
4.  `sudo update-rc.d info_display defaults`

The next time you restart the Raspberry Pi the info display application will start automatically. You can also start, stop and restart
the info display application using the following commands:
```
sudo service info_display start
sudo service info_display stop
sudo service info_display restart
```






