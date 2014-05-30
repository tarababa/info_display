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
# Description: control MPD (Music Player Deamon) to play radio streams
#              see also: http://pythonhosted.org//python-mpd2/index.html
#                        https://github.com/Mic92/python-mpd2
################################################################################


import os,sys
import time
import logging, traceback
import queue
import urllib, urllib.parse, urllib.request
from mpd import MPDClient, CommandError
import configuration

LOGGER = 'RADIO'     #name of logger 
logger = None


#------------------------------------------------------------------------------#
# init: Content of config.ini as made available globally to all modules through#
#       through the configuration module and has been setup by the main        #
#       information_display module. So here we only need to setup a logger     #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 09.11.2013 Initial version                                       #
# 1.10    hta 25.05.2015 Removed call to arguments, corrected description      #
#------------------------------------------------------------------------------#
def init():
  configuration.init_log(LOGGER);  
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
  try:
    mpdc = MPDClient()               # create client object
    mpdc.timeout = None              # network timeout in seconds (floats allowed), default: None
    mpdc.connect(str(configuration.CONFIG['radio']['mpd_server']),
                 int(configuration.CONFIG['radio']['mpd_port']))  # connect to localhost:6600
    logger.info('initialized mpdc, version['+mpdc.mpd_version+']')
    return mpdc
  except:
    logger.error('unexpected error ['+ str(traceback.format_exc()) +']')   
    return None
#------------------------------------------------------------------------------#
# volUp: turn volume up, to maximum of 100                                     #
#                                                                              #
# Parameter: inc: amount by which to increase volume                           #
#            radio_info: dictionary containing mpd status information          #
#            mpdc: The music player daemon client                              #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 24.05.2014 Initial version                                       #
#------------------------------------------------------------------------------# 
def volUp(inc, radio_info, mpdc):            
  global logger
  logger.debug('inc['+str(inc)+']')
  if int(radio_info.get('volume',50))+inc > 100:
    logger.info ('cannot exceed max volume of 100')
  else:
    mpdc.setvol(int(radio_info.get('volume',50))+inc)
#------------------------------------------------------------------------------#
# volDown: turn volume down, to minimum of 0                                   #
#                                                                              #
# Parameter: dec: amount by which to decrease volume                           #
#            radio_info: dictionary containing mpd status information          #
#            mpdc: The music player daemon client                              #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 24.05.2014 Initial version                                       #
#------------------------------------------------------------------------------# 
def volDown(dec, radio_info, mpdc):            
  global logger
  logger.debug('dec['+str(dec)+']')
  if int(radio_info.get('volume',50))-dec < 0:
    logger.info ('cannot go below min volume of 0')
  else:
    mpdc.setvol(int(radio_info.get('volume',50))-dec)  
#------------------------------------------------------------------------------#
# turnOn: turn radio on                                                        #
#                                                                              #
# Parameter: radio_info: dictionary containing mpd status information          #
#            mpdc: The music player daemon client                              #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 24.05.2014 Initial version                                       #
#------------------------------------------------------------------------------# 
def turnOn(radio_info, mpdc):            
  global logger
  logger.debug('state['+radio_info.get('state','?')+']')
  if radio_info.get('state','?') != 'play':
    logger.debug('turning on')
    mpdc.play()
  else:
    logger.info('radio already on')
#------------------------------------------------------------------------------#
# turnOff: turn radio off                                                      #
#                                                                              #
# Parameter: radio_info: dictionary containing mpd status information          #
#            mpdc: The music player daemon client                              #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 24.05.2014 Initial version                                       #
#------------------------------------------------------------------------------# 
def turnOff(radio_info, mpdc):            
  global logger
  logger.debug('state['+radio_info.get('state','?')+']')
  if radio_info.get('state','?') == 'play':
    logger.debug('turning off')
    mpdc.stop()
  else:
    logger.info('radio already off')    
#------------------------------------------------------------------------------#
# toggleOnOff: turn radio off, if it is on and vice versa                      #
#                                                                              #
# Parameter: radio_info: dictionary containing mpd status information          #
#            mpdc: The music player daemon client                              #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 24.05.2014 Initial version                                       #
#------------------------------------------------------------------------------# 
def toggleOnOff(radio_info, mpdc):            
  global logger
  logger.debug('state['+radio_info.get('state','?')+']')
  if radio_info.get('state','?') == 'play':
    turnOff(radio_info,mpdc)
  else:
    turnOn(radio_info,mpdc)
#------------------------------------------------------------------------------#
# nextStation: activate next station in playlist, if already at last station   #
#              then circle back to first station in playlist                   #
# Parameter: radio_info: dictionary containing mpd status information          #
#            mpdc: The music player daemon client                              #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 24.05.2014 Initial version                                       #
#------------------------------------------------------------------------------# 
def nextStation(radio_info, mpdc):            
  global logger
  if int(radio_info.get('playlistlength',1))-1 == int(radio_info.get('song')):
    #at end of playlist? then start at beginning
    logger.debug('song['+ radio_info.get('song')+']')
    logger.debug('playlistlength['+ radio_info.get('playlistlength')+']')
    mpdc.play(0)
  else:
    mpdc.play(int(radio_info.get('song'))+1)
#------------------------------------------------------------------------------#
# previoustation: activate previous station in playlist, if at first station   #
#                 then activate last station in playlist                       #
# Parameter: radio_info: dictionary containing mpd status information          #
#            mpdc: The music player daemon client                              #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 24.05.2014 Initial version                                       #
#------------------------------------------------------------------------------# 
def previousStation(radio_info, mpdc):            
  global logger
  if int(radio_info.get('song')) != 0:
    logger.debug('song['+radio_info.get('song')+']')
    mpdc.previous()
  else:
    logger.debug('playlistlength['+ radio_info.get('playlistlength')+']')
    mpdc.play(int(radio_info.get('playlistlength'))-1)   
    
#------------------------------------------------------------------------------#
# refreshRadioInfo: get latest radio status information from the mpd           #
#                                                                              #
# Parameter: mpdc: The music player daemon client                              #
#                                                                              #
# ReturnValues:  radio_info: dictionary containing mpd status information      #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 24.05.2014 Initial version                                       #
#------------------------------------------------------------------------------# 
def refreshRadioInfo(playlist,mpdc):            
  global logger
  
  #get dictionary containing playlist length, volume, state
  radio_info=mpdc.status()
  #update dictionary in particular name of station playing.
  radio_info.update(mpdc.currentsong())
  #no name for current channel set, then use the one from the configured playlist
  if radio_info.get('name','?') == '?':
    radio_info.update({'name':playlist[int(radio_info.get('song',0))][0]})
  return radio_info

#------------------------------------------------------------------------------#
# get_playlist_config: return a list of all radiostations which should be made #
#                      available                                               #
#                                                                              #
# Parameters:          None                                                    #
#                                                                              #
# ReturnValues:  list of location names and associated URLs                    #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 17.11.2013 Initial version                                       #
#------------------------------------------------------------------------------#  
def get_playlist_config():
  global logger
  playlist_config=[]
  for config in configuration.CONFIG['radio_playlist'] :
    url,station=configuration.CONFIG['radio_playlist'][config].split(',')
    #fix non-ascii characters in URL
    url    = urllib.parse.urlsplit(url)
    url    = list(url)    
    url[2] = urllib.parse.quote(url[2])
    #append location and url to list  
    playlist_config.append((station, urllib.parse.urlunsplit(url)))      
  return playlist_config
#------------------------------------------------------------------------------#
# doInitPlaylist: create our own playlist                                      #
#                                                                              #
# Parameter: mpdc: The music player daemon client                              #
#                                                                              #
# ReturnValues:  radio_info: dictionary containing mpd status information      #
#                playlist_config: playlist from configuration i.e. url and a   #
#                                 name for the station                         #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 24.05.2014 Initial version                                       #
#------------------------------------------------------------------------------# 
def doInitPlaylist(mpdc):            
  global logger
  #first remove the playlist we want to create
  playlistName=configuration.CONFIG['radio']['playlist_name']
  #try to remove the playlist if it exists
  try:
    mpdc.rm(playlistName)
  except CommandError as e:
    if str(e)=='[50@0] {rm} No such playlist':
      logger.info('playlist['+playlistName+'] does not exist')
    else: 
      raise CommandError(e)
  #clear any playlist currently in memory
  mpdc.clear()
  #get playlist from config.ini
  playlist_config=get_playlist_config()
  for station in playlist_config:
    #add urll to the mpd playlist
    mpdc.add(station[1])
  #now save the playlist
  mpdc.save(playlistName)
  #no need to load the playlist, it is already loaded  
  
  return playlist_config
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
  mpdc     = None
  #setup logging
  configuration.init_log(LOGGER)
  logger = logging.getLogger(LOGGER)
  #initialize music player deamon client
  #create in instance 
  mpdc=init_radio()
  #create our own playlist, 
  playlist=doInitPlaylist(mpdc)
  #get dictionary containing playlist length, volume, state
  radio_info=refreshRadioInfo(playlist,mpdc)

  #listen for message to execute.
  while not shutdown:
    logger.info('going to listen on message queue')
    try:
      message=message_q.get(timeout=60)
      #if mpdc failed to initialize earlier or if connection was 
      #reset we try to establish connection again
      while mpdc is None:
         mpdc=init_radio()
         #still no connection, let's 
         #wait and try again
         if mpdc is None:
           time.sleep(2)
      radio_info=refreshRadioInfo(playlist,mpdc)
      if isinstance(message, configuration.MESSAGE):
        logger.debug('message.sender['   + str(message.sender)  + ']')
        logger.debug('message.receiver[' + str(message.receiver)+ ']')
        logger.debug('message.type['     + str(message.type)    + ']')
        logger.debug('message.subtype['  + str(message.subtype) + ']')
        ################
        #TURN RADIO ON?#
        ################
        if message.type == 'PLAY':
          if message.subtype=='ON':
            turnOn(radio_info,mpdc)
          elif message.subtype=='TOGGLE':
            toggleOnOff(radio_info,mpdc)            
        ##########################
        #REQUEST TO CHANGE VOLUME#
        ##########################
        elif message.type == 'VOLUME': 
          if message.subtype=='UP':
            volUp(2,radio_info,mpdc)
          elif message.subtype == 'DOWN':
            logger.info('volume down')
            volDown(2,radio_info,mpdc)
        ###########################
        #REQUEST TO CHANGE CHANNEL#
        ###########################
        elif message.type == 'CHANNEL':
          if message.subtype == 'PREV':
            previousStation(radio_info,mpdc)
          elif message.subtype == 'NEXT':
            nextStation(radio_info,mpdc)
   
        ##################
        #SHUTDOWN REQUEST#
        ##################
        elif message.type == 'SHUTDOWN':
          shutdown=True
          logger.warning('got SHUTDOWN request, shutting down')
          if mpdc is not None:
            mpdc.stop()
            mpdc.close()
            mpdc.disconnect()
      if not shutdown:
        radio_info=refreshRadioInfo(playlist,mpdc)
        logger.debug(str(radio_info))
        message = configuration.MESSAGE('RADIO','DISPLAY','RADIO','REFRESH',radio_info)
        display_q.put(message)       
        logger.info('done, closing connection to MPD')
        mpdc.close()
        mpdc.disconnect()
        mpdc=None
    except queue.Empty as err:
      logger.debug ('queue empty ' + str(err))
      try:
        mpdc=init_radio()
        radio_info=refreshRadioInfo(playlist,mpdc)
        message = configuration.MESSAGE('RADIO','DISPLAY','RADIO','REFRESH',radio_info)
        display_q.put(message)
        logger.info('done, closing connection to MPD')
        mpdc.close()
        mpdc.disconnect()
        mpdc=None        
      except:
        logger.error('unexpected error ['+ str(traceback.format_exc()) +']')   
        mpdc=None        
    except:
      logger.error('unexpected error ['+ str(traceback.format_exc()) +']')   
      mpdc=None
            
      
  logger.debug('done')    

