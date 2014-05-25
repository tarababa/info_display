#!/usr/bin/python
# -*- coding: utf-8 -*-
################################################################################
# Application         : Get Weatherforcast from YR.NO
# File                : $HeadURL:  $
# Version             : $Revision: $
# Created by          : hta
# Created             : 01.10.2013
# Changed by          : $Author: b7tarah $
# File changed        : $Date: 2013-08-21 15:19:43 +0200 (Mi, 21 Aug 2013) $
# Environment         : Python 3.2.3 
# ##############################################################################
# Description: collects wheather data. For more information on the services used
#              see also: http://api.yr.no/weatherapi/documentation.
#
################################################################################


import os,sys
import time
import argparse
import logging, logging.handlers
import queue, threading
import collections
import configuration

# add ../YoctoLib.python.12553/Sources to the PYTHONPATH
sys.path.append(os.path.join("..","YoctoLib.python.12553","Sources"))
from yocto_api import *
from yocto_humidity import *
from yocto_temperature import *
from yocto_pressure import *

LOGGER = 'METEO'     #name of logger for the yoctopuce weather module

meteo_module   = collections.namedtuple('meteo_module', 'module module_name humidity_sensor pressure_sensor temperature_sensor humidity pressure temperature current uptime')
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
# get_module: Get an instance of the yoctopuce meteo module                    #
#                                                                              #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 09.11.2013 Initial version                                       #
#------------------------------------------------------------------------------#  
def get_module(name):
  logger = logging.getLogger(LOGGER)  
  errmsg=YRefParam()  
  # Setup the API to use local USB devices
  # Setup the API to use local USB devices
  # Note this may fail with a return code -6, device busy and
  # an error message, YAPI  already registerd. This seems to happen
  # when multiple threads are trying to do this simultaneously. When
  # RegisterHub fails get_module returns None, it is up to the caller
  # to attempt RegisterHub again
  try:
    retVal=YAPI.RegisterHub("usb", errmsg)
    if retVal != YAPI.SUCCESS:
      logger.warning('YAPI.RegisterHub['+str(retVal)+'] errmsg['+errmsg.value+']')
      return None
  except Exception as err:
    # catch things like: "OSError: exception: access violation writing 0x0000000000000000"
    logger.error(str(err))
    return None
  if name == None:
    #No particular logical name or serial number specified
    #then just get the first humidity sensor and determine
    #its module
    sensor = YHumidity.FirstHumidity()
    if sensor is None:
      logger.error('failed to find humidity sensor')
      return None
    else:
      module = sensor.get_module()
      name = module.get_serialNumber()
      logger.info('got module.get_serialNumber['+ module.get_serialNumber() +']'+
                      ' module.get_logicalName['+ module.get_logicalName()  +']')
  else:
    logger.debug('looking for specific module with logical name[' + name + ']')
    module = YModule.FindModule(name)
    if module == None:
      logger.error('failed to module for name['+name+']')
      return None
    else:
      logger.info('got module.get_serialNumber['+ module.get_serialNumber() +']'+
                      ' module.get_logicalName['+ module.get_logicalName()  +']')      
        
  return module  
  
#------------------------------------------------------------------------------#
# meteo_data: Create instance of meteo module if necessary, instantiate the    #
#             sensors if necessary and return sensor readings                  #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 09.11.2013 Initial version                                       #
#------------------------------------------------------------------------------#   
def meteo_data(module):
  #init variables
  module_name        = None
  ymodule            = None
  humidity_sensor    = None
  pressure_sensor    = None
  temperature_sensor = None
  humidity           = None
  pressure           = None
  temperature        = None
  current            = None
  uptime             = None
  logger = logging.getLogger(LOGGER)
  
  #if we previously created a valid instance of the 
  #meteo module then we use that one.
  if  isinstance(module, meteo_module) and module.module != None:
    module_name        = module.module_name       
    ymodule            = module.module            
    humidity_sensor    = module.humidity_sensor   
    pressure_sensor    = module.pressure_sensor   
    temperature_sensor = module.temperature_sensor
    humidity           = module.humidity          
    pressure           = module.pressure          
    temperature        = module.temperature       
    current            = module.current          
    uptime             = module.uptime
    
  try:
    #meteo module ready to go?  
    #If yes then initialize individual sensors 
    #if necessary and obtain readings
    if ymodule != None and ymodule.isOnline:
      #if humidity sensor not created then create it
      if humidity_sensor == None:
        humidity_sensor    = YHumidity.FindHumidity(module_name+'.humidity')
      #get humidity reading  
      humidity = humidity_sensor.get_currentValue()
      #if pressure sensor not created then create it
      if pressure_sensor == None:
        pressure_sensor    = YPressure.FindPressure(module_name+'.pressure')
      #get pressure reading
      pressure = pressure_sensor.get_currentValue()
      #if temperature sensor not created then create it
      if temperature_sensor == None:
        temperature_sensor = YTemperature.FindTemperature(module_name+'.temperature')
      #get temperature reading
      temperature = temperature_sensor.get_currentValue()
      current = ymodule.get_usbCurrent()
      uptime  = ymodule.get_upTime()/1000
      logger.debug('humidity['    + '%2.0f' % humidity    +  '%] '+
                   'pressure['    + '%4.0f' % pressure    +' mb] '+
                   'temperature[' + '%2.2f' % temperature +' °C]' +
                   'current['     + '%2.2f' % current     +' mA]' +
                   'uptime['      + str(uptime)           +' s]'  )
    else:
      #Module has not been intialized or is not online
      #then go and try to intialize the module
      if configuration.CONFIG.has_option('y_meteo','weather_station_logical_name'):
        #if configured get a specific module
        ymodule = get_module(configuration.CONFIG['y_meteo']['weather_station_logical_name'])
      else:
        #not configured get any module
       ymodule = get_module(None)          
      if ymodule != None:
        module_name = ymodule.get_serialNumber()
        # Yocto module has been initialized, then lets 
        # populate our data model for the meteo module
        # we have an instance of the meteo module
        module = meteo_module(ymodule,module_name, humidity_sensor, pressure_sensor, temperature_sensor, 
                                                   humidity, pressure, temperature, current, uptime)
        # recursively collect "data" from the module i.e. current and uptime
        return meteo_data(module)           
  except YAPI.YAPI_Exception as err:
    logger.error(str(err))
    ymodule = None
    module_name = None
  
  return meteo_module(ymodule,module_name, humidity_sensor, pressure_sensor, temperature_sensor, 
                                           humidity, pressure, temperature, current, uptime)

#------------------------------------------------------------------------------#
# init_module: Returns an instance of the meteo_module                         #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 09.11.2013 Initial version                                       #
#------------------------------------------------------------------------------#
def init_module():
 return meteo_module(None,None,None,None,None,None,None,None,None,None) 
#------------------------------------------------------------------------------#
# trace_result: Trace result to a log file, get a logger if none is provided   #
#                                                                              #
# Parameters: result  result record                                            #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 23.01.2014 Initial version                                       #
#------------------------------------------------------------------------------#  
def trace_result(result):
   logger = logging.getLogger(LOGGER) #will use METEO logger
   trace_result(result,logger) 
#------------------------------------------------------------------------------#
# trace_result: write sensor data to logger                                    #
#                                                                              #
# Parameters: result  result record                                            #
#             logger  which logger to use to trace result record to            #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 09.11.2013 Initial version                                       #
#------------------------------------------------------------------------------#
def trace_result(result,logger):
  if result.module != None and result.humidity!=None:
    logger.info('humidity['    + '%2.0f' % result.humidity    +  '%] '+
                'pressure['    + '%4.0f' % result.pressure    +' mb] '+
                'temperature[' + '%2.2f' % result.temperature +' °C]' +
                'current['     + '%2.2f' % result.current     +' mA]' +
                'uptime['      + str(result.uptime)           +' s]'  )
  else:
    logger.warn('no yoctopuce module instanciated, module['        + str(result.module)   +']' +
                'or init not complete, no sensor reading humidty[' + str(result.humidity) +']' )  
#------------------------------------------------------------------------------#
# meteo_deamon: Instanciate meteo module and poll it for sensor data.          #
#               If reqeusted by the main trhead then supply it with            #
#               with sensor data                                               #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 09.11.2013 Initial version                                       #
#------------------------------------------------------------------------------# 
def meteo_deamon(result_q, message_q, display_q):
  shutdown = False
  message  = None    
  module   = init_module()
  #setup logging
  configuration.init_log(LOGGER)
  logger = logging.getLogger(LOGGER)
  
  #intialize module  
  while module.module == None:
    module = meteo_data(init_module())
    if module.module == None:
      time.sleep(1)
  
  #listen for message to execute.
  while not shutdown:
    logger.info('going to listen on message queue')
    try:
      message=message_q.get(timeout=5)
      if isinstance(message, configuration.MESSAGE):
        logger.debug('message.sender['   + str(message.sender)  + ']')
        logger.debug('message.receiver[' + str(message.receiver)+ ']')
        logger.debug('message.type['     + str(message.type)    + ']')
        logger.debug('message.subtype['  + str(message.subtype) + ']')
        ###############################################
        #REQUEST TO READ SENSOR DATA FROM METEO MODULE#
        ###############################################      
        if message.type == 'METEO': 
          if message.subtype=='GET_SENSOR_DATA':
            logger.info('going to fetch meteo data')
            module = meteo_data(module)
            #Send result to display thread
            #but only if we actually got data
            if module.module != None and module.humidity!=None:
              display_q.put(configuration.MESSAGE('METEO','DISPLAY','METEO_DATA','GRAPH',module))
          elif message.subtype == 'REFRESH':
            #Display module requested and upated of meteo data
            display_q.put( configuration.MESSAGE('METEO','DISPLAY','METEO_DATA','REFRESH',meteo_data(module)))
        ##################
        #SHUTDOWN REQUEST#
        ##################
        elif message.type == 'SHUTDOWN':
          shutdown=True
          logger.warning('got SHUTDOWN request, shutting down')
    except queue.Empty as err:
      logger.debug ('queue empty ' + str(err))
      #no request from main module to get data
      #but we'll read data anyway and extract 
      #current sensor readings and send them to
      #the display module
      module=meteo_data(module)
      message = configuration.MESSAGE('METEO','DISPLAY','METEO_DATA','REFRESH',module)
      display_q.put(message)
    except:
      logger.error('unexpected error ['+ str(sys.exc_info()[0]) +']')        
            
      
  logger.debug('done')    

def main():
  #Initialize
  init()
  logger = logging.getLogger(LOGGER)  
  module=meteo_module(None,None,None,None,None,None,None,None,None,None)  
  while True:
    module=meteo_data(module)
    time.sleep (1.5)
      
  
if __name__ == '__main__':
  main()
