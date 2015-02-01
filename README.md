info_display
============

Primary purpose of this project is to get some experience with Python.

This project uses two Yoctopuce modules, a the maxi display and the meteo module:
  http://www.yoctopuce.com/EN/products/usb-displays/yocto-maxidisplay
  http://www.yoctopuce.com/EN/products/usb-environmental-sensors/yocto-meteo

Using the output from the meteo module temprature, humidity and barometric pressure information is aggragated and shown in
in the form of graphs on the display module.

Furthermore weatherforecast data is pulled from the yr.no rss and can be viewed on the display. 

Navigation through the various menus is done through the six buttons which are integrated in the Yocto display module.
  
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
 
