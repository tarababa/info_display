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
send sms updates to subscribers
             
"""

import os,sys
import time, datetime
import logging, traceback
import queue
import configuration
import configparser
import sim900

LOGGER = 'SMS'     #name of logger 
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
  configuration.init_log(LOGGER)  
#------------------------------------------------------------------------------#
# eskom_loadshedding_sms: create loadshedding SMSs for subscribers             #
#                                                                              #
#                                                                              #
# Parameters:   subscribers, list of all SMS service subscribers (any service) #
#               gsm, instance of sim900 GSM module                             #
#                                                                              #
# ReturnValues:  list of subscribers and their subscriptions                   #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 23.02.2015 Initial version                                       #
#------------------------------------------------------------------------------#  
def eskom_loadshedding_sms(subscribers,gsm):
  global logger
  ESKOM_DB_FILE='./etc/eskom_db.ini'
  #load the database from file
  def loadDb():
    db = configparser.ConfigParser(allow_no_value=True)
    try:
      with open(ESKOM_DB_FILE) as f:
        None
      f.close()
      db.read(ESKOM_DB_FILE,encoding='utf-8')
      return db
    except IOError:
      #file doesnt exist, that's ok, it has not been created yet
      #so we dont send any SMS either.
      return None
      
  db=loadDb()
  if db == None:
    logger.warning('ESKOM DB not FOUND')
    return None # where done here for now.
  
  update_dt=None  
  if datetime.datetime.strptime(db['stage']['forecast_dt'],'%a %b %d %H:%M:%S %Y') > datetime.datetime.strptime(db['stage']['ls_status_dt'], '%a %b %d %H:%M:%S %Y'):
    update_dt=db['stage']['forecast_dt']
  else:
    update_dt=db['stage']['ls_status_dt']

  for subscriber in subscribers:
    if subscriber[0]== 'eskom_loadshedding':
      smsSent=False
      if subscriber[4] != update_dt:
        #subscriber is not up to date yet we must send a message
        if db['stage']['ls_status'] not in ('2','3','4') and db['stage']['forecast_time_from'] != 'None' and db['stage']['forecast_stage'] != 'None':
          #NOT LOAD SHEDDING YET
          sLine1='NOT Loadshedding YET!'
          sLine2='Forecast stage '+ db['stage']['forecast_stage']
          if db['stage']['forecast_time_from'] != 'None' and db['stage']['forecast_time_to'] != 'None':
            sLine2 = sLine2 + ' from '+db['stage']['forecast_time_from'] + ' to ' +db['stage']['forecast_time_to']      
          elif db['stage']['forecast_time_from'] != 'None':
            sLine2 = sLine2 + ' from '+db['stage']['forecast_time_from']          
          day, date, p1, p2, p3 = db['schedules'][subscriber[3]].split(',') 
          sLine3= subscriber[3].capitalize() + ' ' + day + date
          sLine4= 'Schedule: ' + p1 
          if p2 != 'None':
            sLine4= sLine4 + ', ' + p2
          if p3 != 'None':
            sLine4= sLine4 + ', ' + p3
          sLine5 = 'Load: '+db['stage']['power_status_level'] + ', Trend: ' + db['stage']['power_status_trend']
          sSms=sLine1+chr(10)+sLine2+chr(10)+sLine3+chr(10)+sLine4+chr(10)+sLine5
          logger.debug(sSms)
          result=gsm.sendSMS(subscriber[2],sSms)          
          smsSent=True
        elif  db['stage']['ls_status'] in ('2','3','4'):
          #LOAD SHEDDING
          sLine1='LOADSHEDDING, stage '+ str(int(db['stage']['ls_status'])-1)
          day, date, p1, p2, p3 = db['schedules'][subscriber[3]].split(',') 
          sLine2= subscriber[3].capitalize() + ' ' + day + date
          sLine3= 'Schedule: ' + p1 
          if p2 != 'None':
            sLine3= sLine3 + ', ' + p2
          if p3 != 'None':
            sLine3= sLine3 + ', ' + p3
          if db['stage']['forecast_time_from'] != 'None' and db['stage']['forecast_time_to'] != 'None':
            sLine4 = 'Forecast from '+db['stage']['forecast_time_from'] + ' to ' +db['stage']['forecast_time_to']
          elif db['stage']['forecast_time_from'] != 'None':
            sLine4 = 'Forecast from '+db['stage']['forecast_time_from']                 
          sLine5 = 'Load: '+db['stage']['power_status_level'] + ', Trend: ' + db['stage']['power_status_trend']
          sSms=sLine1+chr(10)+sLine2+chr(10)+sLine3+chr(10)+sLine4+chr(10)+sLine5
          logger.debug(sSms)
          result=gsm.sendSMS(subscriber[2],sSms)          
          smsSent=True
        elif  db['stage']['ls_status']=='1':
          #NOT LOADSHEDDING
          sLine1='NOT LOADSHEDDING'
          sLine2 = 'Load: '+db['stage']['power_status_level'] + ', Trend: ' + db['stage']['power_status_trend']
          sSms=sLine1+chr(10)+sLine2
          logger.debug(sSms)
          result=gsm.sendSMS(subscriber[2],sSms)
          smsSent=True
        #update timestamp on subscriber.
        if smsSent:
          configuration.SMSSERVICE.set(subscriber[0],subscriber[1],subscriber[2]+','+subscriber[3]+','+update_dt)  
          configuration.write_sms_service_configuration()
          smsSent=False
#------------------------------------------------------------------------------#
# get_service_subscribers: return a list of subscribers and the service they   #
#                          are subscribed to                                   #
#                                                                              #
# Parameters:          None                                                    #
#                                                                              #
# ReturnValues:  list of subscribers and their subscriptions                   #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 23.02.2015 Initial version                                       #
#------------------------------------------------------------------------------#  
def get_service_subscribers():
  global logger
  service_config=[]
  cellNo, municipality, update_dt = None, None, None
  for service in configuration.SMSSERVICE:
    if service != 'DEFAULT':
      for subscriber in configuration.SMSSERVICE[service]:
        bMutated=False
        try:
          cellNo,municipality,update_dt=configuration.SMSSERVICE[service][subscriber].rstrip(',').split(',')
        except ValueError:
          cellNo,municipality=configuration.SMSSERVICE[service][subscriber].rstrip(',').split(',') #At least subscribers' tel. no. and municipality must be configured
          update_dt = datetime.datetime.strftime(datetime.datetime.today(),'%a %b %d %H:%M:%S %Y')
          bMutated=True
        if update_dt is None:
          update_dt = datetime.datetime.strftime(datetime.datetime.today(),'%a %b %d %H:%M:%S %Y')
          bMutated=True
        if bMutated:
          configuration.SMSSERVICE.set(service,subscriber,cellNo+','+municipality+','+update_dt) #Just setting, not writing out to file yet
        service_config.append((service, subscriber, cellNo, municipality, update_dt))      
      return service_config
#------------------------------------------------------------------------------#
# sms_deamon: send sms's to subscribers as per their subscriptions             #
#                                                                              #
#                                                                              #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 23.05.2014 Initial version                                       #
#------------------------------------------------------------------------------# 
def sms_deamon(result_q, message_q, display_q):
  global logger
  shutdown = False
  message  = None
  #setup logging
  configuration.init_log(LOGGER)
  logger = logging.getLogger(LOGGER)
  #initialize subscriber database
  configuration.sms_service_configuration()  
  #Initialize sim900 device to send sms
  gsm=sim900.Sim900(logger)
  gsm.selectSMSMessageFormat(1)  


  #listen for message to execute.
  while not shutdown:
    logger.info('going to listen on message queue')
    try:
      message=message_q.get(timeout=60)
      if isinstance(message, configuration.MESSAGE):
        logger.debug('message.sender['   + str(message.sender)  + ']')
        logger.debug('message.receiver[' + str(message.receiver)+ ']')
        logger.debug('message.type['     + str(message.type)    + ']')
        logger.debug('message.subtype['  + str(message.subtype) + ']')
        ##################################
        #PROCESS SUBSCRIBERS AND SERVICES#
        ##################################
        if message.type == 'DOSMS':
          #get list of subscribers and their subscriptions
          #we need to read them each time because we change
          #the timestamp after each sms we send for a subscriber/service
          subscribers=get_service_subscribers()            
          eskom_loadshedding_sms(subscribers, gsm)          
        ##################
        #SHUTDOWN REQUEST#
        ##################
        elif message.type == 'SHUTDOWN':
          shutdown=True
          logger.warning('got SHUTDOWN request, shutting down')
    except queue.Empty as err:
      logger.debug ('queue empty ' + str(err))
    except:
      logger.error('unexpected error ['+ str(traceback.format_exc()) +']')   
            
      
  logger.debug('done')    
  
#configuration.logging_configuration()  
#configuration.general_configuration()  
#configuration.sms_service_configuration()
#configuration.init_log(LOGGER)
#logger = logging.getLogger(LOGGER)
#
#sim900=sim900.Sim900(logger)
#logger.debug(sim900.selectSMSMessageFormat(1))
#
#
#subscribers=get_service_subscribers()  
#eskom_loadshedding_sms(subscribers, sim900)

