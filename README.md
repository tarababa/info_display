info_display
============

The primary purpose of this project was to for me to gain some experience with Python. Over time the project has grown and bits have been added on

This project uses two Yoctopuce modules, a maxi display and the meteo module:

  * [Yocto-maxidisplay](http://www.yoctopuce.com/EN/products/usb-displays/yocto-maxidisplay)
  * [Yocto-meteo](http://www.yoctopuce.com/EN/products/usb-environmental-sensors/yocto-meteo)
  
The Elecfreak GSM/GPRS module is used to send SMS-es

  * [EFComPro GSM/GPRS](http://www.elecfreaks.com/store/gprsgsm-moduleefcom-pro-efcompro-p-450.html)

##Functions
Quite a few, typically configurable, functions have now been included. The following chapters describe these functions
in a bit more detail.
For navigation the buttons on the maxi-display module are used. From left to right, the buttons are used as follows:

1. The first button moves to the next *left* menu
2. The second button moves to the next *right* menu
3. The third button moves *up* in the menu hierarchy
4. The fourth button moves *down* in the menu hierarchy
5. The fifth button is a *select* button, when supported by the chosen menu the up and down buttons can be used to view additional
data for the chosen options such as weather forecasts and loadshedding schedules for the next days on the chosen location. 
Pressing the select button a second time returns the up and down buttons tho their normal functions
6. The sixth button is now used to terminate the info-display program, expect when in the "radio" menu, then it is used
to turn the radio on and off.

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
button changes the function of the up and down buttons so that one can move through the load-shedding schedules of the chosen
suburb for the following days and current load-shedding stage. Pressing the select button again returns the function of the
up and down buttons to normal.

The suburbs for which data is collected is configured in `config.ini` under the heading `[eskom_loadshedding]`, take note
I've not tested this with multiple suburbs configured, it should work but no guarantees...

```
[eskom_loadshedding]
schedule.0=Western Cape,Saldanha Bay,Langebaan
```

![Load-shedding](https://github.com/tarababa/info_display/blob/master/img/doc/loadshedding.png)



-Get MPD/MPC
 sudo apt-get install mpd
 sudo apt-get install mpc (optional)
 in /etc/mpd.conf ensure following configuration:
   bind_to_address         "any"
   port                    "6600"
   

-Install Info display from git
 git clone https://github.com/tarababa/info_display.git

-Install python setuptools
 sudo apt-get update
 sudo apt-get install python3-pip

-Install python-mpd2 library
 sudo pip-3.2 install python-mpd2

-To start
 sudo nohup /usr/bin/python3 /home/pi/information_display/info_display/information_display.py &
 
-Autostart
 make information_display.py executable: chmod a+x information_display.py
 sudo cp /home/pi/info_display/etc/info_display /etc/init.d
 then make info_display executable: sudo chmod a+x info_display
 sudo update-rc.d info_display defaults


-Install lxml (for ESKOM loadshedding information)
 On windows:
   Download package from http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml
   Install using pip
   D:\03-git\info_display>pip install D:\Data\b7tarah\Downloads\lxml-3.4.1-cp34-none-win32.whl
 On raspberry PI:
   sudo apt-get install python3-lxml

-Install twython
 On windows:
   pip install twython
 On Raspberry PI:
   sudo pip-3.2 install twython

