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
holds, sets and returns relevant values relevant across an application
such as tracelevel and other command line options that might be required 
accross modules. These values should be set only by the init function
in the main program, after wich they may only be read.

"""


import os,sys
import collections
import logging, logging.handlers
import configparser

CONFIG = None       #configuration from config.ini
LOGGING= None       #logging configuration from ini file
TWITTER= None       #twitter configuration from inin file
SMSSERVICE= None    #datbase of SMS service subscribers

MESSAGE   = collections.namedtuple('message', 'sender receiver type subtype content')
#------------------------------------------------------------------------------#
# set_SMSSERVICE: set globally available configuration (from sms_service.ini)  #
#                                                                              #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 09.11.2013 Initial version                                       #
#------------------------------------------------------------------------------#
def set_SMSSERVICE(config):
  global SMSSERVICE 
  SMSSERVICE = config
#------------------------------------------------------------------------------#
# get_SMSSERVICE: returns globally available configuration (sms_service.ini)   #
#                                                                              #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 09.11.2013 Initial version                                       #
#------------------------------------------------------------------------------#
def get_SMSSERVICE():
  global SMSSERVICE
  return SMSSERVICE  
#------------------------------------------------------------------------------#
# set_TWITTER: set globally available configuration (from twitter.ini)         #
#                                                                              #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 09.11.2013 Initial version                                       #
#------------------------------------------------------------------------------#
def set_TWITTER(config):
  global TWITTER 
  TWITTER = config
#------------------------------------------------------------------------------#
# get_TWITTER: returns globally available configuration (from twitter.ini)     #
#                                                                              #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 09.11.2013 Initial version                                       #
#------------------------------------------------------------------------------#
def get_TWITTER():
  global TWITTER
  return TWITTER
#------------------------------------------------------------------------------#
# set_CONFIG: set globally available configuration (from config.ini)           #
#                                                                              #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 09.11.2013 Initial version                                       #
#------------------------------------------------------------------------------#
def set_CONFIG(config):
  global CONFIG 
  CONFIG = config
#------------------------------------------------------------------------------#
# get_CONFIG: returns globally available configuration (from config.ini)       #
#                                                                              #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 09.11.2013 Initial version                                       #
#------------------------------------------------------------------------------#
def get_CONFIG():
  global CONFIG
  return CONFIG
#------------------------------------------------------------------------------#
# set_LOGGING: set globally available logging configuration (from logging.ini) #
#                                                                              #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 23.01.2014 Initial version                                       #
#------------------------------------------------------------------------------#
def set_LOGGING(config):
  global LOGGING 
  LOGGING= config
#------------------------------------------------------------------------------#
# get_LOGGING: returns globally available logging configuration                #
#              (from config.ini)                                               # 
#                                                                              #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 09.11.2013 Initial version                                       #
#------------------------------------------------------------------------------#
def get_LOGGING():
  global LOGGING
  return LOGGING
#------------------------------------------------------------------------------#
# init: Read sms_service.ini file                                              #
#                                                                              #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 17.11.2013 Initial version                                       #
#------------------------------------------------------------------------------#
def sms_service_configuration():
  ###################################
  # get configuration from ini file #
  ###################################
  config = configparser.ConfigParser(allow_no_value=True)
  config.read('./etc/sms_service.ini',encoding='utf-8')
  set_SMSSERVICE(config)    
#------------------------------------------------------------------------------#
# init: Write sms_service.ini file                                             #
#                                                                              #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 17.11.2013 Initial version                                       #
#------------------------------------------------------------------------------#
def write_sms_service_configuration():
  if SMSSERVICE is not None:
    with open('./etc/sms_service.ini', 'w') as f:
      SMSSERVICE.write(f)    
#------------------------------------------------------------------------------#
# init: Read twitter.ini file                                                  #
#                                                                              #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 17.11.2013 Initial version                                       #
#------------------------------------------------------------------------------#
def twitter_configuration():
  ###################################
  # get configuration from ini file #
  ###################################
  config = configparser.RawConfigParser(allow_no_value=True)
  config.read('./etc/twitter.ini',encoding='utf-8')
  set_TWITTER(config)  
#------------------------------------------------------------------------------#
# init: Read config.ini file                                                   #
#                                                                              #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 17.11.2013 Initial version                                       #
#------------------------------------------------------------------------------#
def general_configuration():
  ###################################
  # get configuration from ini file #
  ###################################
  config = configparser.ConfigParser(allow_no_value=True)
  config.read('./etc/config.ini',encoding='utf-8')
  set_CONFIG(config)
#------------------------------------------------------------------------------#
# init: Read log.ini file. This file whether the various modules should        #
#       write logfiles and if so at what level                                 #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 17.11.2013 Initial version                                       #
#------------------------------------------------------------------------------#
def logging_configuration():
  ##################################
  # Get configuration for loggging #
  ##################################  
  config = configparser.ConfigParser(allow_no_value=True)
  config.read('./etc/log.ini')
  set_LOGGING(config)
#------------------------------------------------------------------------------#
# init: initialize logger                                                      #
#                                                                              #
# Parameters: LOGGER Name of the logger, statically defined in the calling     #
#                    module such as MAIN or WEATHER etc.                       #
#                                                                              #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 17.11.2013 Initial version                                       #
#------------------------------------------------------------------------------#  
def init_log(LOGGER):
  bLogToFile   =False
  bLogToConsole=False
  
  #get logging configuration from log.ini file
  LOGGING=get_LOGGING()
  if LOGGING.getboolean(LOGGER,'log_to_file'): 
    bLogToFile = True
  if LOGGING.getboolean(LOGGER,'log_to_console'): 
    bLogToConsole = True
    
  #################
  # setup logging #
  #################

  # create logger
  logger = logging.getLogger(LOGGER)
  logger.setLevel(logging.DEBUG)

  # create formatter
  formatter = logging.Formatter('%(asctime)s - %(name)s - %(module)s.%(funcName)s - %(levelname)s - %(message)s')
  
  # create console handler and set level as per configuration
  if bLogToConsole == True:
    ch = logging.StreamHandler()
    ch.setLevel(getattr(logging, LOGGING[LOGGER]['level'], None)) 
    # add formatter to ch (console handler)
    ch.setFormatter(formatter)
    # add ch and rfh (rotating filehandler to logger
    logger.addHandler(ch)
  
  # create rotating filehandler and set leval as per configuration
  # 10 files, each 10 megabytes.
  if bLogToFile == True:
    rfh = logging.handlers.RotatingFileHandler('./log/'+LOGGER+'.log', 'a', (1024*1024*10), 10)  
    rfh.setLevel(getattr(logging,  LOGGING[LOGGER]['level'], None))
    #add formatter to rotating filehandler
    rfh.setFormatter(formatter)
    #rfh (rotating filehandler to logger
    logger.addHandler(rfh)
  
