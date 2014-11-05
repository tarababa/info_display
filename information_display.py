#!/usr/bin/env python3

#    Copyright 2014 Helios Taraba 
#
#    This file is part of information_display.
#
#    information_display is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    information_display is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with information_display.  If not, see <http://www.gnu.org/licenses/>.


"""
Main program responsible for starting all required threads, controlling the
information shown and functions provided
             
"""

import os,sys
import logging,traceback
import queue, threading
import collections
import configuration
import weather_yr
import y_meteo, y_button
import y_maxi_display
import radio
import exchange_rates_yahoo
import timers

LOGGER = 'MAIN'  #name of logger for the main module

#------------------------------------------------------------------------------#
# init: Read config.ini and setup logging                                      #
#       Content of config.ini as made available globally to all modules through#
#       through the configuration module                                       #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 09.11.2013 Initial version                                       #
# 1.10    hta 25.05.2015 Removed call to arguments, corrected description      #
#------------------------------------------------------------------------------#
def init():
  configuration.general_configuration();
  configuration.logging_configuration();
  configuration.init_log(LOGGER);
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
    work_queue.put( configuration.MESSAGE('MAIN','WEATHER','GET_WEATHER_FORECAST','ALL', None))
  elif timer=='METEO':
    work_queue.put( configuration.MESSAGE('MAIN','METEO','METEO','GET_SENSOR_DATA',None))
  elif timer=='EXCHANGE':
    work_queue.put( configuration.MESSAGE('MAIN','EXCHANGE','GET_EXCHANGE_RATE','ALL', None))
  elif timer=='RADIO':
    work_queue.put( configuration.MESSAGE('MAIN','RADIO','REFRESH','RADIO_INFO', None))
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
  logger.debug(configuration.CONFIG['y_meteo']['weather_station_logical_name'])
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
  exchange_q= queue.Queue()
  radio_q   = queue.Queue()


  ###############################
  # start display module thread # 
  ###############################
  #create and start meteo module thread
  display_thread = threading.Thread(target=y_maxi_display.display_deamon, args=(main_q, meteo_q, radio_q, display_q))
  display_thread.name = 'DISPLAY'
  display_thread.deamon=False
  display_thread.start()
  
  #################################
  # start weather forecast thread # 
  #################################
  weather_q.put( configuration.MESSAGE('MAIN','WEATHER','GET_WEATHER_FORECAST','ALL', None))
  #create and start weather forecaset thread
  weather_thread = threading.Thread(target=weather_yr.weather_deamon, args=(main_q, display_q, weather_q))
  weather_thread.name = 'WHEATHER'  
  weather_thread.deamon=False
  weather_thread.start()
  #start repeating weather timer (times out every six hours)
  weather_timer_thread = timers.RepeatingTimer(21600, function=do_timers, args=('WEATHER',weather_q))
  weather_timer_thread.name = 'WEATHER_TIMER'
  weather_timer_thread.start()   
  
  ##############################
  # start exchange rate thread # 
  ##############################
  exchange_q.put( configuration.MESSAGE('MAIN','EXCHANGE','GET_EXCHANGE_RATE','ALL', None))
  #create and start weather forecaset thread
  exchange_thread = threading.Thread(target=exchange_rates_yahoo.exchange_rate_deamon, args=(main_q, display_q, exchange_q))
  exchange_thread.name = 'EXCHANGE'  
  exchange_thread.deamon=False
  exchange_thread.start()
  #start repeating exchange rate timer (times out every minute)
  exchange_timer_thread = timers.RepeatingTimer(60, function=do_timers, args=('EXCHANGE',exchange_q))
  exchange_timer_thread.name = 'WEATHER_TIMER'
  exchange_timer_thread.start()     
  
  ######################
  # start radio thread # 
  ######################
  radio_q.put( configuration.MESSAGE('MAIN','RADIO','INIT','RADIO_INFO',None))
  #create and start meteo module thread
  radio_thread = threading.Thread(target=radio.radio_deamon, args=(main_q, radio_q, display_q))
  radio_thread.name = 'RADIO'
  radio_thread.deamon=False
  radio_thread.start()
  #start repeating radio timer
  radio_timer_thread = timers.RepeatingTimer(60, function=do_timers, args=('RADIO',radio_q))
  radio_timer_thread.name = 'RADIO_TIMER'
  radio_timer_thread.start()    

  #############################
  # start meteo module thread # 
  #############################
  meteo_q.put( configuration.MESSAGE('MAIN','METEO','METEO','GET_SENSOR_DATA',None))
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
  button_thread = threading.Thread(target=y_button.button_deamon, args=(main_q, button_q, display_q, radio_q))
  button_thread.name = 'BUTTON'
  button_thread.deamon=False
  button_thread.start()

  result=None
  shutdown=False
  #main thread
  while not shutdown:
    try:
      message = main_q.get(30)
      if isinstance(message, configuration.MESSAGE):
        logger.debug('message.sender['   + str(message.sender)  + ']')
        logger.debug('message.receiver[' + str(message.receiver)+ ']')
        logger.debug('message.type['     + str(message.type)    + ']')
        logger.debug('message.subtype['  + str(message.subtype) + ']')
        ##################
        #WEATHER FORECAST#
        ##################
        if message.type == 'WEATHER_FORECAST': 
          weather_yr.trace_forecast(message.content,logger)
        ##################
        #SHUTDOWN REQUEST#
        ##################
        elif message.type == 'SHUTDOWN':
          logger.warning('got SHUTDOWN request, shutting down')
          shutdown=True
          #cancel timer threads
          meteo_timer_thread.cancel()
          weather_timer_thread.cancel()
          exchange_timer_thread.cancel()
          radio_timer_thread.cancel()
          #send shutdown message to all modules
          button_q.put(  configuration.MESSAGE('MAIN','BUTTON',  'SHUTDOWN',None,None))
          meteo_q.put(   configuration.MESSAGE('MAIN','METEO',   'SHUTDOWN',None,None))
          weather_q.put( configuration.MESSAGE('MAIN','WEATHER', 'SHUTDOWN',None,None))
          display_q.put( configuration.MESSAGE('MAIN','DISPLAY', 'SHUTDOWN',None,None))          
          exchange_q.put(configuration.MESSAGE('MAIN','EXCHANGE','SHUTDOWN',None,None))          
          radio_q.put(   configuration.MESSAGE('MAIN','RADIO','SHUTDOWN',None,None))          
        else:
          logger.warning('got unknown message')
      else:
        logger.error('got undefined message[' + str(message) + ']')
    except queue.Empty as err:
      logger.info('queue empty')
    except:
      logger.error('unexpected error ['+ str(traceback.format_exc()) + ']')        

      
  logger.debug('done')    
   
  
if __name__ == '__main__':
  main()
