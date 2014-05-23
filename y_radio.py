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
import logging, logging.handlers
import queue, threading
import y_disp_global
from mpd import MPDClient

LOGGER = 'RADIO'     #name of logger 
logger = None


#------------------------------------------------------------------------------#
# init: Read config.ini, read startup arguments and setup logging              #
#       Content of config.ini and the startup arguments are made available     #
#       globally to all modules through y_disp_global                          #
#       Only used when module is ran on its own, for test purposes             #
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
# init_radio: intialize a MPD client                                           #
#                                                                              #
#                                                                              #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 23.05.2014 Initial version                                       #
#------------------------------------------------------------------------------# 
def init_radio():            
  global logger
  mpdc = MPDClient()               # create client object
  mpdc.timeout = 10                # network timeout in seconds (floats allowed), default: None
  mpdc.idletimeout = 5
  mpdc.connect(str(y_disp_global.CONFIG['radio']['mpd_server']),
               int(y_disp_global.CONFIG['radio']['mpd_port']))  # connect to localhost:6600
  logger.info('initialized mpdc, version['+mpdc.mpd_version+']')
  return mpdc
#------------------------------------------------------------------------------#
# radio_deamon: handle radio control requests i.e. change channel and volume   #
#                                                                              #
#                                                                              #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 23.05.2014 Initial version                                       #
#------------------------------------------------------------------------------# 
def radio_deamon(result_q, message_q, display_q):
  global logger
  shutdown = False
  message  = None    
  #setup logging
  y_disp_global.init_log(LOGGER)
  logger = logging.getLogger(LOGGER)
  #initialize music player deamon client
  #create in instance 
  mpdc=init_radio()
  #clear current playlist
  mpdc.clear()
  #load radio station playlist
  mpdc.load('myPlayList.m3u')  
  #get dictionary containing playlist length, volume, state
  radio_info=mpdc.status()
  #add to dictionary in particular name of station playing.
  radio_info.update(mpdc.currentsong())
  logger.debug('currentsong['+str(mpdc.currentsong())+']')
  #listen for message to execute.
  while not shutdown:
    logger.info('going to listen on message queue')
    try:
      message=message_q.get(timeout=15)
      if isinstance(message, y_disp_global.MESSAGE):
        logger.debug('message.sender['   + str(message.sender)  + ']')
        logger.debug('message.receiver[' + str(message.receiver)+ ']')
        logger.debug('message.type['     + str(message.type)    + ']')
        logger.debug('message.subtype['  + str(message.subtype) + ']')
        ################
        #TURN RADIO ON?#
        ################
        if message.type == 'PLAY':
          if message.subtype=='ON':
            logger.info('turn on')
            mpdc.play()  
            #after changing channel we need to wait a bit 
            #for the "currentsong" i.e. channel name to be
            #updated.
            time.sleep(1.5)            
        #####################################
        #REQUEST TO CHANGE CHANNEL OR VOLUME#
        #####################################
        elif message.type == 'VOLUME': 
          if message.subtype=='UP':
            logger.info('volume up')
            mpdc.setvol(int(radio_info.get('volume',50))+2)
          elif message.subtype == 'DOWN':
            logger.info('volume down')
            mpdc.setvol(int(radio_info.get('volume',50))-2)
        elif message.type == 'CHANNEL':
          if message.subtype == 'PREV':
            logger.info('previous channel')
            if int(radio_info.get('song')) != 0:
              logger.debug('song['+ radio_info.get('song')+']')
              mpdc.previous()
            else:
              logger.debug('playlistlength['+ radio_info.get('playlistlength')+']')
              mpdc.play(int(radio_info.get('playlistlength'))-1)
          elif message.subtype == 'NEXT':
            logger.info('next channel')
            try:
              if int(radio_info.get('playlistlength',1))-1 == int(radio_info.get('song')):
                logger.debug('song['+ radio_info.get('song')+']')
                logger.debug('playlistlength['+ radio_info.get('playlistlength')+']')
                mpdc.play(0)
              else:
                mpdc.next()
            except:
              mpdc.next()   
          #after changing channel we need to wait a bit 
          #for the "currentsong" i.e. channel name to be
          #updated.
          time.sleep(1.5)    
        ##################
        #SHUTDOWN REQUEST#
        ##################
        elif message.type == 'SHUTDOWN':
          shutdown=True
          logger.warning('got SHUTDOWN request, shutting down')
          mpdc.stop()
          mpdc.close()
          mpdc.disconnect()
      if not shutdown:
        #update dictionary containing playlist length, volume, state
        radio_info=mpdc.status()
        #update dictionary in particular name of station playing.
        radio_info.update(mpdc.currentsong())            
        message = y_disp_global.MESSAGE('RADIO','DISPLAY','RADIO','REFRESH',radio_info)
        display_q.put(message)        
    except queue.Empty as err:
      logger.debug ('queue empty ' + str(err))
      #update dictionary containing playlist length, volume, state
      radio_info=mpdc.status()
      #update dictionary in particular name of station playing.
      radio_info.update(mpdc.currentsong())            
      message = y_disp_global.MESSAGE('RADIO','DISPLAY','RADIO','REFRESH',radio_info)
      display_q.put(message) 
    except:
      logger.error('unexpected error ['+ str(sys.exc_info()[0]) +']')        
            
      
  logger.debug('done')    

def main():
  global logger
  #Initialize
  init()
  logger = logging.getLogger(LOGGER)  
  mpdc=init_radio()
  mpdc.clear()
  mpdc.load('myPlayList.m3u')
  mpdc.play(10)
  mpdc.setvol(80)
  logger.debug('status['+str(mpdc.status())+']')
  logger.debug('status['+str(mpdc.stats())+']')
  logger.debug('currentsong['+str(mpdc.currentsong())+']')
  
if __name__ == '__main__':
  main()
