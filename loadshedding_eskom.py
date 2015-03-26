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
collects loadshedding information from loadshedding.eskom.co.za
the y_maxi_display.py module for visualisation

"""

import os,sys
import logging, traceback
import queue
import urllib, urllib.parse, urllib.request
import collections
import configuration
import configparser
from lxml import etree
from lxml.html import fromstring
import json
import time, datetime
import re
from twython import Twython
from configparser import NoOptionError
import socket


LOGGER = 'ESKOM'  #name of logger for this module
power_status         = collections.namedtuple("powerstatus","level trend")
loadSheddingForecast = collections.namedtuple("forecast","stage time_from time_to") #from twitter
loadSheddingSchedule = collections.namedtuple("schedule","forecast power_status lsstatus suburb day period1 period2 period3")

#LS Status to stage
STATUS2STAGE = {'-1':('1','UNKNOWN'),
                 '1':('1','NOT LOADSHEDDING'),
                 '2':('1','STAGE 1'),
                 '3':('2','STAGE 2'),
                 '4':('3','STAGE 3')}
#Hardcoded map of province to code.
PROVINCES = {'EASTERN CAPE'  : 1,
             'FREE STATE'    : 2,
             'GAUTENG'       : 3,
             'KWAZULU-NATAL' : 4,
             'LIMPOPO'       : 5,
             'MPUMALANGA'    : 6,
             'NORTH WEST'    : 7,
             'NORTHERN CAPE' : 8,
             'WESTERN CAPE'  : 9}
          
#http://loadshedding.eskom.co.za/LoadShedding/GetSurburbData/?pageSize=200&pageNum=1&id=208  208 is saldanha bay

#http://loadshedding.eskom.co.za/LoadShedding/GetScheduleM/38312/2/9/330  38312 is langebaan, 2 = stage 2, 9 = western cape, 330 is Tot field from suburb data.

#http://loadshedding.eskom.co.za/LoadShedding/GetMunicipalities/?Id=9  9 is western cape

#http://loadshedding.eskom.co.za/LoadShedding/GetStatus?_= 1,2,3,4


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
  configuration.twitter_configuration();
#------------------------------------------------------------------------------#
# eskom_loadshedding_status: get loadshedding status from                      #
#                            loadshedding.eskom.co.za                          #
#                                                                              #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 24.03.2014 Initial version                                       #
#------------------------------------------------------------------------------#
def eskom_loadshedding_status():
  logger = logging.getLogger(LOGGER)
  logger.debug('start')
  lsstatus='-1'
  #set the url
  url = 'http://loadshedding.eskom.co.za/LoadShedding/GetStatus'
  logger.debug('url['+url+']')
  #spoof the user agent.
  user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'  
  #set headers, in particular the user agent
  headers = { 'User-Agent' : user_agent }
  #create request
  req = urllib.request.Request(url, None, headers)
  #read html page, find the element lsstatus which contains the load shedding status
  try:
    lsstatus =urllib.request.urlopen(req).read().decode('utf-8') 
    logger.debug('lsstatus[' + lsstatus + ']')
  except:
    #sometimes we get urllib.error.HTTPError: HTTP Error 400: Bad Request
    #to try and figure out what went wrong we trace the request
    logger.error('req['+str(req)+']')
    logger.error('unexpected error ['+  str(traceback.format_exc()) +']') 
    lsstatus = '-1'
  
  return lsstatus  

#------------------------------------------------------------------------------#
# eskom_get_municipality: gets numeric value for a municipality from           #
#                         loadshedding.eskom.co.za                             #
# Parameters province:     province for wich to get municipalities             #
#            municipality: municipality of interest                            #
#                                                                              #
# Return values: numeric identifier of the desired municipality                #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 24.03.2014 Initial version                                       #
#------------------------------------------------------------------------------#
def eskom_get_municipality(province,municipality):
  logger = logging.getLogger(LOGGER)
  logger.debug('start')
  #set the url
  url = 'http://loadshedding.eskom.co.za/LoadShedding/GetMunicipalities/?Id=' + str(PROVINCES.get(province.upper()))
  logger.debug('url['+url+']')
  #spoof the user agent.
  user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'  
  #set headers, in particular the user agent
  headers = { 'User-Agent' : user_agent }
  #create request
  req = urllib.request.Request(url, None, headers)
  #get a json list of all municipalities in our chosen province
  try:
    municipalities = json.loads(urllib.request.urlopen(req).read().decode('utf-8')) 
  except:
    #sometimes we get urllib.error.HTTPError: HTTP Error 400: Bad Request
    #to try and figure out what went wrong we trace the request
    logger.error('req['+str(req)+']')
    logger.error('unexpected error ['+  str(traceback.format_exc()) +']') 
  
  #find our municipality
  municipalityDict = next((m for m in municipalities if m['Text'] == municipality), None)
  if municipalityDict is not None:
    logger.debug('found MunicipalityDict[' + str(municipalityDict) +']')
  else: 
    logger.error('No record found for municipality[' + str(municipality) +']')
    
  return municipalityDict['Value']
  
#------------------------------------------------------------------------------#
# eskom_get_suburb: gets numeric value for a suburb from                       #
#                   loadshedding.eskom.co.za                                   #
# Parameters municipality: numeric identifier of desired municipality          #
#            suburb:       suburb of interest                                  #
#                                                                              #
# Return values: numeric identifier of the desired suburb                #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 24.03.2014 Initial version                                       #
#------------------------------------------------------------------------------#
def eskom_get_suburb(municipality,suburb):
  logger = logging.getLogger(LOGGER)
  logger.debug('start')
  #set the url
  url = 'http://loadshedding.eskom.co.za/LoadShedding/GetSurburbData/?pageSize=999&pageNum=1&id=' +str(municipality)
  logger.debug('url['+url+']')
  #spoof the user agent.
  user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'  
  #set headers, in particular the user agent
  headers = { 'User-Agent' : user_agent }
  #create request
  req = urllib.request.Request(url, None, headers)
  #get a json list of all municipalities in our chosen province
  try:
    suburbs = json.loads(urllib.request.urlopen(req).read().decode('utf-8')) 
  except:
    #sometimes we get urllib.error.HTTPError: HTTP Error 400: Bad Request
    #to try and figure out what went wrong we trace the request
    logger.error('req['+str(req)+']')
    logger.error('unexpected error ['+  str(traceback.format_exc()) +']') 
  
  #find our municipality
  suburbsDict = next((s for s in suburbs['Results'] if s['text'] == suburb), None)
  if suburbsDict is not None:
    logger.debug('found suburbsDict[' + str(suburbsDict) +']')
  else: 
    logger.error('No record found for suburb[' + str(suburb) +']')
    
  return suburbsDict['id'],suburbsDict['Tot']  
  
#------------------------------------------------------------------------------#
# eskom_get_loadshedding_schedule: gets loadshedding schedule for a particular #
#                                  suburb and loadshedding stage               #
# Parameters province: province identifier, required for URL                   #
#            suburb  : in plaintext, required for return value                 #
#            suburbId:  numeric identifier of desired suburb                   #
#            suburbTot: numeric identifier...???                               #
#            lsstatus: loadshedding status, required to determine loadshedding #
#                      stage which goes in the URL                             #
#            powerStatus: for inclusion in the return value                    #
#            forecast: loadshedding "forecast" from twitter                    #
#                                                                              #
# Return values: schedule                                                      #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 24.03.2014 Initial version                                       #
#------------------------------------------------------------------------------#
def eskom_get_loadshedding_schedule(province,suburb,suburbId,suburbTot, lsstatus, powerStatus, forecast):
  logger = logging.getLogger(LOGGER)
  logger.debug('start')
  #set the url
  if lsstatus == '1' and  forecast.stage in ('1','2','3','4','5'):
    url = 'http://loadshedding.eskom.co.za/LoadShedding/GetScheduleM/' + str(suburbId) + '/' + forecast.stage + '/' + str(PROVINCES.get(province.upper())) + '/' + str(suburbTot)
  else:
    url = 'http://loadshedding.eskom.co.za/LoadShedding/GetScheduleM/' + str(suburbId) + '/' + STATUS2STAGE[lsstatus][0] + '/' + str(PROVINCES.get(province.upper())) + '/' + str(suburbTot)    
  logger.debug('url['+url+']')
  #spoof the user agent.
  user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'  
  #set headers, in particular the user agent
  headers = { 'User-Agent' : user_agent }
  #create request
  req = urllib.request.Request(url, None, headers)
  #get a html document containing the loadshedding schedule for the chosen
  #suburb and the actual loadshedding stage
  try:
    scheduleContent = (urllib.request.urlopen(req).read().decode('utf-8'))
    scheduleDoc     =  fromstring(scheduleContent)
    dayMonth = scheduleDoc.find_class('dayMonth')
    scheduleDay = scheduleDoc.find_class('scheduleDay')
    myLoadSheddingSchedule=[]
    for day in scheduleDay:
      scheduleText=[]
      for schedule in day:
        scheduleText.append(str(schedule.text_content().strip()))
      while len(scheduleText) < 4:
        scheduleText.append(None)
      loadSheddingScheduleDay=loadSheddingSchedule(forecast,powerStatus,lsstatus,suburb,scheduleText[0],scheduleText[1],scheduleText[2],scheduleText[3])  
      myLoadSheddingSchedule.append(loadSheddingScheduleDay)  
    return myLoadSheddingSchedule
  except:
    #sometimes we get urllib.error.HTTPError: HTTP Error 400: Bad Request
    #to try and figure out what went wrong we trace the request
    logger.error('req['+str(req)+']')
    logger.error('unexpected error ['+  str(traceback.format_exc()) +']') 
#------------------------------------------------------------------------------#
# eskom_power_status: gets the national power status from myeskom.co.za        #
#                                  suburb and loadshedding stage               #
# Parameters None                                                              #
#                                                                              #
# Return values: powerstatus and trend                                         #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 24.03.2014 Initial version                                       #
#------------------------------------------------------------------------------#
def eskom_power_status():
  logger = logging.getLogger(LOGGER)
  logger.debug('start')

  #set the url, not sure whether timestamp will break this in other timezones..
  url = 'https://www.myeskom.co.za/pages/Dashboard/24?v=' + str(int(time.time() * 1000))
  logger.debug('url['+url+']')
  #spoof the user agent.
  user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'  
  #set headers, in particular the user agent
  headers = { 'User-Agent' : user_agent }
  #binary encoded post data
  auth = {'authKey' : 'NOTAUTHENTICATED', 
          'city'    : ''}  
  #data = urllib.parse.urlencode(auth)
  binary_data = urllib.parse.urlencode(auth).encode('utf-8')
  #create request
  req = urllib.request.Request(url, binary_data, headers )
  #get a json document containing amongst other things
  #the national power status
  try:
    data = json.loads(urllib.request.urlopen(req).read().decode('utf-8')) 
    powerStatus = data['data']['page']
    logger.debug('level[' + powerStatus['level'] + '] powerStatus[' + powerStatus['levelstatus'] + '] status [' + powerStatus['status'] +']')
    return power_status(powerStatus['level'],powerStatus['levelstatus'])
  except:
    #sometimes we get urllib.error.HTTPError: HTTP Error 400: Bad Request
    #to try and figure out what went wrong we trace the request
    logger.error('req['+str(req)+']')
    logger.error('unexpected error ['+  str(traceback.format_exc()) +']') 
#------------------------------------------------------------------------------#
# eskom_twitter: get loadshedding forecast from twitter                        #
#                                                                              #
# parameters: lsstatus: ESKOM loadshedding status                              #           
#                                                                              #
# returnvalues: loadshedding_forecast                                          #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 24.03.2014 Initial version                                       #
#------------------------------------------------------------------------------#
def eskom_twitter(lsstatus):
  logger = logging.getLogger(LOGGER)
  #If access_token not obtained yet then 
  #go get it now and save it in config.
  APP_KEY=configuration.TWITTER.get('twitter','APP_KEY',raw=True)
  APP_SECRET=configuration.TWITTER.get('twitter','APP_SECRET',raw=True)
  try:
    ACCESS_TOKEN=configuration.TWITTER.get('twitter','ACCESS_TOKEN',raw=True)
  except NoOptionError as err:
    twitter = Twython(APP_KEY, APP_SECRET, oauth_version=2)
    ACCESS_TOKEN = twitter.obtain_access_token()
    configuration.TWITTER.set('twitter', 'ACCESS_TOKEN', ACCESS_TOKEN)
    with open('./etc/twitter.ini', 'w') as twitterfile:
      configuration.TWITTER.write(twitterfile)
        
  twitter = Twython(APP_KEY,access_token=ACCESS_TOKEN)
  
  #get search results from twitter
  r=twitter.search(q='from:Eskom_SA -stopped -cancelled -restoration -restored -resumed -resume)')
  
  for tweet in r['statuses']:
    #when was the tweet created
    created_at = datetime.datetime.strptime(tweet['created_at'], '%a %b %d %H:%M:%S +0000 %Y')
    today = datetime.datetime.today()
    text = tweet['text']
    logger.debug('created_at['+ tweet['created_at'] + '] text['+text+']');
    #Look for something like Stage 1
    stage = re.findall("(?i)STAGE\s*\d{1}",text) 
    if stage: #got forecasted stage, go and find from-to times
      #look for something like 08h00
      times = re.findall("(\d{2}\D{1,3}\d{2})",text)
      if times: #loadshedding has been forcasted...
        if len(times)==2:
          endTime = re.findall('\d+',times[1]) #get forecasted end time, hour and minutes seperate
          if endTime and len(endTime)==2:
            if today.day == created_at.day and today.hour < int(endTime[0]):
              #forecast is for today and endtime has not passed yet...
              #obviously this fails if endtime is only tomorrow... 
              logger.debug('got loadshedding from[' + str(times[0]) + '] to[' + str(times[1]) +']')
              #return loadSheddingForecast(stage[0].split(' ')[1],times[0],times[1])
              return loadSheddingForecast(stage[0][-1],times[0],times[1])
            else:
              break
          else:
            break
        else:
          #no endtime, lets see if we can turn of this particular forcast message
          if lsstatus in ('-1','1'): # not loadshedding (or unknown)
            #current time has gone 30 minutes past the forecasted starttime, and we are not loadshedding 
            #then we dont need the forecast message anymore
            if today+datetime.timedelta(minutes=30) > datetime.datetime.combine(created_at.date(), datetime.datetime.min.time())+datetime.timedelta(hours=int(times[0][0:2]),minutes=int(times[0][3:5])):
              None
            else:
              logger.debug('got loadshedding from[' + str(times[0]) + ']')
              return loadSheddingForecast(stage[0].split(' ')[1],times[0],None)
          else:
            #we're loadshedding include forecast
            logger.debug('got loadshedding from[' + str(times[0]) + ']')
            return loadSheddingForecast(stage[0].split(' ')[1],times[0],None)
  return loadSheddingForecast(None,None,None)  
#------------------------------------------------------------------------------#
# trace_loadshedding_schedule: Trace loadshedding schedule to a log file,      #
#                              get a logger if none is provided                #
#                                                                              #
# Parameters: schedule loadshedding schedule                                   #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 24.03.2014 Initial version                                       #
#------------------------------------------------------------------------------#  
def trace_loadshedding_schedule(schedule):
   logger = logging.getLogger(LOGGER) #will use ESKOM logger
   trace_loadshedding_schedule(lsschedule,logger)   
#------------------------------------------------------------------------------#
# trace_loadshedding_schedule: Trace loadshedding schedule to a log file       #
#                                                                              #
# Parameters: schedule  loadshedding schedule                                  #
#             logger    which logger to use for tracing of the schedule        #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 24.03.2014 Initial version                                       #
#------------------------------------------------------------------------------#  
def trace_loadshedding_schedule(schedule,logger):
  for day in schedule:
    logger.info('[' + str(day) + ']');
#------------------------------------------------------------------------------#
# get_loadshedding_config: get the list of locations for which we want to check#
#                      the loadshedding schedule                               #
# Parameters:                                                                  #
#                                                                              #
# ReturnValues:  list of suburbs for which to get the schedule                 #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 24.03.2014 Initial version                                       #
#------------------------------------------------------------------------------#  
def get_loadshedding_config():
  logger = logging.getLogger(LOGGER)
  loadshedding_config=[]
  for config in configuration.CONFIG['eskom_loadshedding'] :
    province, municipality, suburb =configuration.CONFIG['eskom_loadshedding'][config].split(',')
    #append location to list  
    loadshedding_config.append((province, municipality, suburb))      
  return loadshedding_config
#------------------------------------------------------------------------------#
# doGetSchedule: return schedule                                               #
#                                                                              #
# Parameters: cfg: eskom loadshedding configuration, for one particular suburb #
#             powerStatus: grid load                                           #
#             lsstatus: loadshedding status  (this not the same as the stage!) #
#             forecast: loadshedding forecast from twitter                     #
#                                                                              #
# Returnvalues: Schedule for one particular suburb and current loadshedding    #
#               stage
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 24.03.2014 Initial version                                       #
#------------------------------------------------------------------------------# 
def doGetSchedule(cfg,powerStatus,lsstatus,forecast):
  #Get municipality information:
  municipality=eskom_get_municipality(cfg[0],cfg[1])
  #Get suburb parameters
  suburbId,suburbTot=eskom_get_suburb(municipality,cfg[2])
  #now return the schedule to the caller
  return eskom_get_loadshedding_schedule(cfg[0],cfg[2],suburbId,suburbTot,lsstatus,powerStatus,forecast)  
#------------------------------------------------------------------------------#
# doUpdateDb: Update database with current loadshedding values, provided they  #
#             have changed                                                     #
# Parameters: schedules: current loadshedding status for all configurations    #
#                                                                              #
# Returnvalues: None                                                           #
#                                                                              #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 24.03.2014 Initial version                                       #
#------------------------------------------------------------------------------# 
def doUpdateDb(schedules):
  ESKOM_DB_FILE='./etc/eskom_db.ini'
  #load the database from file
  def loadDb():
    db = configparser.ConfigParser(allow_no_value=True)
    try:
      with open(ESKOM_DB_FILE) as f:
        None
      db.read(ESKOM_DB_FILE,encoding='utf-8')
    except IOError:
      #file doesnt exist, that's ok, go and init the database
      return initDb(db)
    return db
  #Initialize the database
  def initDb(db):
    db['stage'] = {'ls_status'         : '-1',
                   'ls_status_dt'      : '',
                   'forecast_stage'    : '',
                   'forecast_dt'       : '',
                   'forecast_time_from':'',
                   'forecast_time_to'  : '',
                   'power_status_level': '',
                   'power_status_trend':'',
                   'power_status_dt'   :''}
    db['schedules'] = {'schedule.0'    : ''}       
    return db
  #Write data to file
  def writeDb(db):
    with open(ESKOM_DB_FILE, 'w') as f:
      db.write(f)    
    return db
  
  #load (and initialize if necessary) the database
  db=loadDb()
  i=0 #index for schedule
  for schedule in schedules:
    now=schedule[0] #only todays schedule
    if i==0:
      ## this we only need to once
      if now.lsstatus is not None and now.lsstatus != db['stage']['ls_status']:
        db.set('stage', 'ls_status', now.lsstatus)
        db.set('stage', 'ls_status_dt', datetime.datetime.strftime(datetime.datetime.today(),'%a %b %d %H:%M:%S %Y'))
      if str(now.forecast.stage) != db['stage']['forecast_stage']:
        db.set('stage', 'forecast_stage', str(now.forecast.stage))
        db.set('stage', 'forecast_time_from', str(now.forecast.time_from))
        db.set('stage', 'forecast_time_to', str(now.forecast.time_to))
        db.set('stage', 'forecast_dt', datetime.datetime.strftime(datetime.datetime.today(),'%a %b %d %H:%M:%S %Y'))
      if now.power_status.level is not None and now.power_status.level !=db['stage']['power_status_level']:
        db.set('stage', 'power_status_level', now.power_status.level)
        db.set('stage', 'power_status_dt', datetime.datetime.strftime(datetime.datetime.today(),'%a %b %d %H:%M:%S %Y'))
      if now.power_status.trend is not None and now.power_status.trend !=db['stage']['power_status_trend']:    
        db.set('stage', 'power_status_trend', now.power_status.trend)
        db.set('stage', 'power_status_dt', datetime.datetime.strftime(datetime.datetime.today(),'%a %b %d %H:%M:%S %Y'))
      
    db.set('schedules', now.suburb, now.day+','+str(now.period1)+','+str(now.period2)+','+str(now.period3))
    i+=1
  
  #write current values to DB file  
  writeDb(db)
    
#------------------------------------------------------------------------------#
# eskom_deamon: responsible for collecting loadshedding status, schedules and  #
#               grid load, and sending data to display thread                  #
#                                                                              #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 24.03.2014 Initial version                                       #
#------------------------------------------------------------------------------# 
def eskom_deamon(main_q,message_q,display_q):
  shutdown = False
  message  = None  
  loadshedding_schedules = []
  #setup logging
  init()
  logger = logging.getLogger(LOGGER)
  #get configuration
  loadshedding_config=get_loadshedding_config()
  #sometimes getting eskom's power status hangs indefinetely
  #to avoid this we set a socket timeout
  socket.setdefaulttimeout(10)

  while not shutdown:
    try:
      message=message_q.get(timeout=120)
      if isinstance(message, configuration.MESSAGE):
        logger.debug('message.sender['   + str(message.sender)  + ']')
        logger.debug('message.receiver[' + str(message.receiver)+ ']')
        logger.debug('message.type['     + str(message.type)    + ']')
        logger.debug('message.subtype['  + str(message.subtype) + ']')
        ##############################################
        #REQUEST LOADSHEDDING SCHEDULE INFORMATION   #
        ##############################################
        if message.type == 'GET_LOADSHEDDING_SCHEDULE' and message.subtype=='ALL':
          powerStatus=eskom_power_status()
          lsstatus=eskom_loadshedding_status()
          forecast=eskom_twitter(lsstatus)
          schedules = []
          #Loop through all configured locations
          for config in loadshedding_config:
            schedules.append(doGetSchedule(config,powerStatus,lsstatus,forecast))
          display_q.put( configuration.MESSAGE('ESKOM','DISPLAY','SCHEDULES','DATA', schedules))
          #update eskom_db
          doUpdateDb(schedules)
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


#configuration.general_configuration();
#configuration.logging_configuration();
#configuration.twitter_configuration();
#loadshedding_schedules = []
#init()
#logger = logging.getLogger(LOGGER)
#loadshedding_config=get_loadshedding_config()
#powerStatus=eskom_power_status()
#lsstatus=eskom_loadshedding_status()
#forecast=eskom_twitter(lsstatus)
#schedules = []
#schedules.append(doGetSchedule(loadshedding_config[0],eskom_power_status(),lsstatus, forecast))  
#doUpdateDb(schedules)        

#for testing
#configuration.general_configuration();
#configuration.logging_configuration();
#configuration.twitter_configuration();
#
#configuration.init_log(LOGGER);
#logger = logging.getLogger(LOGGER)
#ls=eskom_loadshedding_status()
#
#lf=eskom_twitter(LS)
#
#print (lf)
#
#loadshedding_schedules = []
#loadshedding_config=get_loadshedding_config()
#loadshedding_schedules.append(doGetSchedule(loadshedding_config[0],eskom_power_status(),eskom_twitter()))
#trace_loadshedding_schedule(loadshedding_schedules[0], logger)

