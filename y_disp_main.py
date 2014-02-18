#!/usr/bin/python
# -*- coding: utf-8 -*-
################################################################################
# Application         : Yoctopuce display control
# File                : $HeadURL:  $
# Version             : $Revision: $
# Created by          : hta
# Created             : 01.10.2013
# Changed by          : $Author: b7tarah $
# File changed        : $Date: 2013-08-21 15:19:43 +0200 (Mi, 21 Aug 2013) $
# Environment         : Python 3.2.3 
# ##############################################################################
# Description : Main program controlling the information shown on the 
#               Yoctopuce maxi display.
#              
#              
#              
#
#
################################################################################


import os,sys
import logging
import queue, threading
import urllib, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
import collections
import y_disp_global
import y_disp_weather_yr
import y_meteo, y_button
import y_disp_maxi_display
import timers
sys.path.append(os.path.join("..","YoctoLib.python.12553","Sources"))
from yocto_api import *
from yocto_display import *

LOGGER = 'MAIN'  #name of logger for the main module


        
#------------------------------------------------------------------------------#
# init: Read config.ini, log.ini, starup arguments and setup logging           #
#       Content of config.ini and the startup arguments are made available     #
#       globally to all modules through y_disp_global                          #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 09.11.2013 Initial version                                       #
#------------------------------------------------------------------------------#
def init():
  y_disp_global.general_configuration();
  y_disp_global.logging_configuration();
  y_disp_global.init_args();
  y_disp_global.init_log(LOGGER);
#------------------------------------------------------------------------------#
# do_timers: processes timers, put message in relevant work_queues             #
#                                                                              #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 11.11.2013 Initial version                                       #
#------------------------------------------------------------------------------#
def do_timers(timer, work_queue):
  logger = logging.getLogger(LOGGER)  
  logger.info('got timer[' + timer + ']')
  if timer=='WEATHER':
    work_queue.put( y_disp_global.MESSAGE('MAIN','WEATHER','GET_WEATHER_FORECAST','LANGEBAANLAGOON', None))
  elif timer=='METEO':
    work_queue.put( y_disp_global.MESSAGE('MAIN','METEO','METEO','GET_SENSOR_DATA',None))
  else:
    logger.info ('no action defined for timer[' + timer + ']')
  
#------------------------------------------------------------------------------#
# main: Main thread, reponsible for setting global values and starting         #
#       required threads.                                                      #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 09.11.2013 Initial version                                       #
#------------------------------------------------------------------------------#
def test_():
  #initialize
  init();
  logger = logging.getLogger(LOGGER)  
  logger.debug('start')
  logger.debug(y_disp_global.CONFIG['y_meteo']['weather_station_logical_name'])
def main():
  #get commandline arguments, config.ini and setup logging
  init();
  logger = logging.getLogger(LOGGER)  
  logger.debug('start')

  #setup queues for the various threads to communicated
  main_q    = queue.Queue()
  display_q = queue.Queue()
  weather_q = queue.Queue()    
  meteo_q   = queue.Queue()
  button_q  = queue.Queue()


  ###############################
  # start display module thread # 
  ###############################
  #create and start meteo module thread
  display_thread = threading.Thread(target=y_disp_maxi_display.display_deamon, args=(main_q, meteo_q, display_q))
  display_thread.name = 'DISPLAY'
  display_thread.deamon=False
  display_thread.start()
  
  #################################
  # start weather forecast thread # 
  #################################
  weather_q.put( y_disp_global.MESSAGE('MAIN','WEATHER','GET_WEATHER_FORECAST','ALL', None))
  #create and start weather forecaset thread
  weather_thread = threading.Thread(target=y_disp_weather_yr.weather_deamon, args=(main_q, display_q, weather_q))
  weather_thread.name = 'WHEATHER'  
  weather_thread.deamon=False
  weather_thread.start()
  #start repeating weather timer
  weather_timer_thread = timers.RepeatingTimer(3600, function=do_timers, args=('WEATHER',weather_q))
  weather_timer_thread.name = 'WEATHER_TIMER'
  weather_timer_thread.start()   

  #############################
  # start meteo module thread # 
  #############################
  meteo_q.put( y_disp_global.MESSAGE('MAIN','METEO','METEO','GET_SENSOR_DATA',None))
  #create and start meteo module thread
  meteo_thread = threading.Thread(target=y_meteo.meteo_deamon, args=(main_q, meteo_q, display_q))
  meteo_thread.name = 'METEO'
  meteo_thread.deamon=False
  meteo_thread.start()
  #start repeating meteo timer
  meteo_timer_thread = timers.RepeatingTimer(940, function=do_timers, args=('METEO',meteo_q))
  meteo_timer_thread.name = 'METEO_TIMER'
  meteo_timer_thread.start()   

  ##############################
  # start button module thread # 
  ##############################
  #create and start meteo module thread
  button_thread = threading.Thread(target=y_button.button_deamon, args=(main_q, button_q, display_q))
  button_thread.name = 'BUTTON'
  button_thread.deamon=False
  button_thread.start()

  result=None
  shutdown=False
  #main thread
  while not shutdown:
    try:
      message = main_q.get(30)
      if isinstance(message, y_disp_global.MESSAGE):
        logger.debug('message.sender['   + str(message.sender)  + ']')
        logger.debug('message.receiver[' + str(message.receiver)+ ']')
        logger.debug('message.type['     + str(message.type)    + ']')
        logger.debug('message.subtype['  + str(message.subtype) + ']')
        ##################
        #WEATHER FORECAST#
        ##################
        if message.type == 'WEATHER_FORECAST': 
          y_disp_weather_yr.trace_forecast(message.content,logger)
        ##################
        #SHUTDOWN REQUEST#
        ##################
        elif message.type == 'SHUTDOWN':
          logger.warning('got SHUTDOWN request, shutting down')
          shutdown=True
          #cancel timer threads
          meteo_timer_thread.cancel()
          weather_timer_thread.cancel()
          #send shutdown message to all modules
          button_q.put(  y_disp_global.MESSAGE('MAIN','BUTTON', 'SHUTDOWN',None,None))
          meteo_q.put(   y_disp_global.MESSAGE('MAIN','METEO',  'SHUTDOWN',None,None))
          weather_q.put( y_disp_global.MESSAGE('MAIN','WEATHER','SHUTDOWN',None,None))
          display_q.put( y_disp_global.MESSAGE('MAIN','DISPLAY','SHUTDOWN',None,None))          
        else:
          logger.warning('got unknown message')
      else:
        logger.error('got undefined message[' + str(message) + ']')
    except queue.Empty as err:
      logger.info('queue empty')
    except:
      logger.error('unexpected error ['+ str(sys.exc_info()[0]) +']')        
      
      
  logger.debug('done')    
   
  
if __name__ == '__main__':
  
  main()
