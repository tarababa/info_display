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
import logging, traceback
import queue
import urllib, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
import collections
import configuration


LOGGER = 'WEATHER'  #name of logger for the weather module
#ARGS   = {}         #startup arguments, globally available

#define collections to hold forecast
forecast                    = collections.namedtuple("forecast","location publicationdatetime forecast_items")
forecast_pulicationdt       = collections.namedtuple("publicationdatetime","dayname day monthname year time timezone")
forecast_item               = collections.namedtuple("item","datetime cloudcover temperature wind precipitation symbol")
forecast_item_dt            = collections.namedtuple("datetime","dayname day monthname year time")
forecast_item_cloud_cover   = collections.namedtuple("cloudcover","clouds")
forecast_item_temperature   = collections.namedtuple("temperature","temperature unit time")
forecast_item_wind          = collections.namedtuple("wind","description strength unit direction")
forecast_item_precipitation = collections.namedtuple("precipitation","precipitation unit time_from time_to")
forecast_item_symbol        = collections.namedtuple("symbol","image")

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

################################################################################
# process a title tag of a forcast item
#
def do_title(title):
  logger = logging.getLogger(LOGGER)
  logger.debug('title['+title+']')
  #<title>Wednesday 06 November 2013 at 17:00</title>
  titlelist=title.split(' ')
  return forecast_item_dt(titlelist[0],titlelist[1],titlelist[2],titlelist[3],titlelist[5])
################################################################################
# return cloud forecast
# 
#
def do_cloud_cover(cloud):
  logger = logging.getLogger(LOGGER)
  logger.debug('cloud['+cloud+']')
  return forecast_item_cloud_cover(cloud.rstrip('.'))
################################################################################
# return temperature forecast
# 
#
def do_temperature(temperature):
  logger = logging.getLogger(LOGGER)
  logger.debug('temperature['+temperature+']')
  temperaturelist=temperature.split(' ')
  return forecast_item_temperature(temperaturelist[0].strip('°C'), temperaturelist[0][-2:], temperaturelist[2].strip('.'))
################################################################################
# return wind forecast
# 
#
def do_wind(wind):
  logger = logging.getLogger(LOGGER)
  logger.debug('wind['+wind+']')
  windlist_1=wind.split(', ')         #split description from rest of wind data      
  windlist_2=windlist_1[1].split(' ') #split wind data
  return forecast_item_wind(windlist_1[0], windlist_2[0], windlist_2[1], windlist_2[3])  
################################################################################
# return precipitation forecast
# 
#
def do_precipitation(precipitation):
  def isNumeric(string):
      try:
          float(string)
          return True
      except ValueError:
          return False  
  logger = logging.getLogger(LOGGER)
  logger.debug('precipitation['+precipitation+']')
  precipitationlist=precipitation.split(' ')  
  if isNumeric(precipitationlist[0]) and isNumeric(precipitationlist[2]):
    # precipitation range
    return forecast_item_precipitation(precipitationlist[0]+'-'+precipitationlist[2], precipitationlist[3], precipitationlist[7], precipitationlist[9].rstrip('.'))
  elif isNumeric(precipitationlist[0]):
    # specific amount of precipitation
    return forecast_item_precipitation(precipitationlist[0], precipitationlist[1], precipitationlist[5], precipitationlist[7].rstrip('.'))
  else:
    # no precipitation
    return forecast_item_precipitation('0.0', 'mm', precipitationlist[4], precipitationlist[6].rstrip('.'))
################################################################################
# process a description tag of a forcast item
# and return cloud_cover, temperature, wind and precipitation forecasts
#
def do_description(description):
  logger = logging.getLogger(LOGGER)
  logger.debug('description['+description+']')
  #<description>Partly cloudy. 17°C at 17:00. Fresh breeze, 8 m/s from west. No precipitation expected between 17 and 23.</description>
  #<description>Partly cloudy. 23°C at 17:00. Moderate breeze, 7 m/s from south. 0.1 mm mm precipitation between 17 and 23.</description>
  descriptionlist=description.split('. ')
  cloud_cover = do_cloud_cover(descriptionlist[0])  
  temperature = do_temperature(descriptionlist[1])
  wind = do_wind(descriptionlist[2])
  precipitation = do_precipitation(descriptionlist[3])
  return cloud_cover, temperature, wind, precipitation  
################################################################################
# process a enclosure tag of a forcast item
# and return forecast symbol image name
#
def do_enclosure(enclosure):
  logger = logging.getLogger(LOGGER)
  logger.debug('enclosure['+str(enclosure)+']')
  #<enclosure url="http://symbol.yr.no/grafikk/sym/b38/03d.png" length="1000" type="image/png" />
  enclosurelist=enclosure['url'].split('/')
  filename=enclosurelist.pop() # get last item from list, this should be the filename
  extension=filename[filename.rfind('.'):]
  filename=filename[0:3].replace('.','d') #expect 2 digits plus d for day and n for night, if not present assume d (day)
  return forecast_item_symbol(filename+extension)
################################################################################
# process a pubDate of a forcast
# 
#
def do_pubdate(pubdate):
  logger = logging.getLogger(LOGGER)
  logger.debug('pubdate['+str(pubdate)+']')
  #<pubDate>Wed, 06 Nov 2013 10:00:00 GMT</pubDate>
  pubdatelist=pubdate.split(' ')
  return forecast_pulicationdt(pubdatelist[0].rstrip(','), pubdatelist[1], pubdatelist[2], pubdatelist[3], pubdatelist[4], pubdatelist[5])   
################################################################################
# get rss weatherforecast 
#
#
def yr_rss(config):
  logger = logging.getLogger(LOGGER)
  logger.debug('start')
  forcastitems = [] #list of forcast items
  #set the url to desired location
  url =config[1]
  logger.debug('url['+url+']')
  #spoof the user agent.
  user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'  
  #set headers, in particular the user agent
  headers = { 'User-Agent' : user_agent }
  #create request
  req = urllib.request.Request(url, None, headers)
  #read rss as xml tree
  rss = ET.parse(urllib.request.urlopen(req)).getroot()
  
  #get publication data of forcast
  publicationdt=do_pubdate(rss.find('./channel/pubDate').text)  
  
  #get forcast items
  for item in rss.iter('item'):
    for child in item:
      if child.tag == 'title': 
        item_dt=do_title(child.text)
      elif child.tag == 'description':
        item_cloud_cover, item_temperature, item_wind, item_precipitation = do_description(child.text)
      elif child.tag == 'enclosure':
        item_symbol=do_enclosure(child.attrib)
      logger.debug('child.tag['+str(child.tag)+']child.attrib['+str(child.attrib)+'][child.text['+str(child.text)+']')
    #add the forcast item to the list of forecast items
    forcastitems.append(forecast_item(item_dt, item_cloud_cover, item_temperature, item_wind, item_precipitation, item_symbol) )  
    
  return forecast(config[0],publicationdt,forcastitems)
################################################################################
#Get and save all weather icons from yr.no
#
#
def yr_save_weathericons():
  logger = logging.getLogger(LOGGER)
  img_no_act =  1
  img_no_max =  23
  day   = 0
  night = 1
  time_of_day = day 
  #set the url to desired location
  url ='http://api.yr.no/weatherapi/weathericon/1.0/'
  #spoof the user agent.
  user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'  
  #set headers, in particular the user agent
  headers = { 'User-Agent' : user_agent }
  #there are day and nigh-time icons.
  while time_of_day <= night:
    while img_no_act <= img_no_max:
      #set url values (i.e. parameters
      img_file_name = str(img_no_act).zfill(2)+  str(time_of_day).replace('0','d').replace('1','n')+'.png'
      logger.debug('img_file_name['+img_file_name+']')
      #create a set of required parameters
      param={}
      param['symbol']=img_no_act
      param['is_night']=time_of_day
      param['content_type']='image/png'
      url_values = urllib.parse.urlencode(param)  
      #create request
      logger.debug('url['+url+'?'+url_values+']')
      req = urllib.request.Request(url+'?'+url_values, None, headers)
      #connect
      try:
        img = urllib.request.urlopen(req)
        #get image and write it to file
        with open(img_file_name,'wb') as f:
          f.write(img.read())
          f.close() #close file
        img.close() #close connection
      except urllib.error.HTTPError as err:
        #gracefully handle those images which dont exist as
        #they have no relevants at night (such as sun for instance)
        #but only when server replies with Bad Request error 400
        if img_no_act in (16,17,18,19) and time_of_day==night and err.code==400:
          logger.info('skipping img_file_name['+img_file_name+'] (not relevant at night)')
        else:
          raise
      img_no_act+=1
    #get the night time images
    time_of_day+=1
    img_no_act=1
#------------------------------------------------------------------------------#
# trace_forecast: Trace forcast to a log file, get a logger if none is provided#
#                                                                              #
# Parameters: forecast  forecast record as defined in weather_yr               #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 23.01.2014 Initial version                                       #
#------------------------------------------------------------------------------#  
def trace_forecast(forecast):
   logger = logging.getLogger(LOGGER) #will use WEATHER logger
   trace_forecast(forecast,logger)
#------------------------------------------------------------------------------#
# trace_forecast: writes forecast record to logger                             #
#                                                                              #
# Parameters: forecast  forecast record as defined in weather_yr               #
#             logger    which logger to use for tracing of the forecast        #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 17.11.2013 Initial version                                       #
#------------------------------------------------------------------------------#  
def trace_forecast(forecast,logger):
 
   
  logger.info('forecast.publicationdatetime['+forecast.publicationdatetime.dayname  +']['
                                             +forecast.publicationdatetime.day      +']['
                                             +forecast.publicationdatetime.monthname+']['
                                             +forecast.publicationdatetime.year     +']['
                                             +forecast.publicationdatetime.time     +']['
                                             +forecast.publicationdatetime.timezone +']')  
  for item in forecast.forecast_items:
    logger.info('item.datetime['+item.datetime.dayname   +']['
                                +item.datetime.day       +']['
                                +item.datetime.monthname +']['
                                +item.datetime.year      +']['
                                +item.datetime.time      +']')    
    logger.info('item.cloudcover['+item.cloudcover.clouds +']')
    logger.info('item.temperature['+item.temperature.temperature +']['
                                   +item.temperature.unit        +']['
                                   +item.temperature.time        +']')
    logger.info('item.wind['+item.wind.description +']['
                            +item.wind.strength    +']['
                            +item.wind.unit        +']['
                            +item.wind.direction   +']')     
    logger.info('item.precipitation['+item.precipitation.precipitation +']['
                                     +item.precipitation.unit          +']['
                                     +item.precipitation.time_from     +']['
                                     +item.precipitation.time_to       +']')
    logger.info('item.symbol['+item.symbol.image +']')    
#------------------------------------------------------------------------------#
# get_forecast_config: return a list of all locations for which the forecast   #
#                      information should be displayed                         #
#                                                                              #
# Parameters:          None                                                    #
#                                                                              #
# ReturnValues:  list of location names and associated URLs                    #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 17.11.2013 Initial version                                       #
#------------------------------------------------------------------------------#  
def get_forecast_config():
  logger = logging.getLogger(LOGGER)
  forecast_config=[]
  for config in configuration.CONFIG['weather_yr'] :
    location,url=configuration.CONFIG['weather_yr'][config].split(',')
    #fix non-ascii characters in URL
    url    = urllib.parse.urlsplit(url)
    url    = list(url)    
    url[2] = urllib.parse.quote(url[2])
    #append location and url to list  
    forecast_config.append((location, urllib.parse.urlunsplit(url)))      
  return forecast_config
  
def weather_deamon(main_q,display_q,message_q):
  shutdown = False
  message  = None  
  forcasts = []
  #setup logging
  init()
  logger = logging.getLogger(LOGGER)
  forecastConfig=get_forecast_config()
  
  while not shutdown:
    try:
      message=message_q.get(timeout=120)
      if isinstance(message, configuration.MESSAGE):
        logger.debug('message.sender['   + str(message.sender)  + ']')
        logger.debug('message.receiver[' + str(message.receiver)+ ']')
        logger.debug('message.type['     + str(message.type)    + ']')
        logger.debug('message.subtype['  + str(message.subtype) + ']')
        ##############################################
        #REQUEST WEATHER FORECAST FOR SPECIFIC REGION#
        ##############################################
        if message.type == 'GET_WEATHER_FORECAST' and message.subtype=='ALL':
          forecasts = []
          #Loop through all configured location urls
          for config in forecastConfig:
            forecasts.append(yr_rss(config))
          display_q.put( configuration.MESSAGE('WEATHER','MAIN','WEATHER_FORECAST','ALL', forecasts))
        ##################    
        #SHUTDOWN MESSAGE#
        ##################
        elif message.type == 'SHUTDOWN':
          logger.warning('got shutdown request, SHUTTING DOWN NOW')
          shutdown=True
        else:
          ######################    
          #UNKNOWN MESSAGE TYPE#
          ######################    
          logger.error('got unknown message from sender[' + str(message.sender)   + '] ' +
                       'receiver['                        + str(message.receiver) + '] ' +
                       'type['                            + str(message.type)     + '] ' +
                       'subtype['                         + str(message.subtype)  + ']');
    #timeout listening on queue
    except queue.Empty as err:
      logger.debug('queue empty ' + str(err))  
    except:
      logger.error('unexpected error ['+  str(traceback.format_exc()) +']')        
      
  logger.debug('done')    

