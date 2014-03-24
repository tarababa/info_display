#!/usr/bin/python
# -*- coding: utf-8 -*-
################################################################################
# Application         : Get exchange rates from yahoo
# File                : $HeadURL:  $
# Version             : $Revision: $
# Created by          : hta
# Created             : 01.10.2013
# Changed by          : $Author: b7tarah $
# File changed        : $Date: 2013-08-21 15:19:43 +0200 (Mi, 21 Aug 2013) $
# Environment         : Python 3.2.3 
# ##############################################################################
# Description: collects exchange rate information from yahoo
#
################################################################################


import os,sys
import argparse
import logging, logging.handlers,traceback
import queue, threading
import urllib, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
import collections
import y_disp_global


LOGGER = 'EXCHANGE'  #name of logger for this module

#define collections to hold exchange rates
exchange_rate               = collections.namedtuple("exchange_rate","from_currency to_currency rate date time ask bid")



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
  y_disp_global.general_configuration()
  y_disp_global.logging_configuration()
  y_disp_global.init_args()
  y_disp_global.init_log(LOGGER) 

#------------------------------------------------------------------------------#
# yahoo_exchange_rate_xml: get exchange rate in XML format from yahoo          #
#                                                                              #
# http://query.yahooapis.com/v1/public/yql?q=select * from yahoo.finance.xchange where pair in ("CHFZAR")&diagnostics=false&env=store://datatables.org/alltableswithkeys
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 24.03.2014 Initial version                                       #
#------------------------------------------------------------------------------#
def yahoo_exchange_rate_xml(config):
  logger = logging.getLogger(LOGGER)
  logger.debug('start')
  #set the url to desired location
  url =config[2]
  logger.debug('url['+url+']')
  #spoof the user agent.
  user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'  
  #set headers, in particular the user agent
  headers = { 'User-Agent' : user_agent }
  #create request
  req = urllib.request.Request(url, None, headers)
  #read xml tree
  xml_rate = ET.parse(urllib.request.urlopen(req)).getroot()
  
  #get exchange rate
  for rate in xml_rate.iter('rate'):
    for child in rate:
      if child.tag == 'Name': 
        name=child.text
      elif child.tag == 'Rate':
        this_exchange_rate = child.text
      elif child.tag == 'Date':
        date = child.text
      elif child.tag == 'Time':
        time = child.text
      elif child.tag == 'Ask':
        ask = child.text
      elif child.tag == 'Bid':
        bid = child.text
      logger.debug('child.tag['+str(child.tag)+']child.attrib['+str(child.attrib)+'][child.text['+str(child.text)+']')
 
  return exchange_rate(config[0], config[1] , this_exchange_rate, date, time, ask, bid)

#------------------------------------------------------------------------------#
# trace_exchange_rate: Trace exchange rate to a log file, get a logger if none #
#                      is provided                                             #
#                                                                              #
# Parameters: rate     exchange_rate record                                    #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 24.03.2014 Initial version                                       #
#------------------------------------------------------------------------------#  
def trace_exchange_rate(rate):
   logger = logging.getLogger(LOGGER) #will use EXCHANGE logger
   trace_exchange_rate(rate,logger)
#------------------------------------------------------------------------------#
# trace_exchange_rate: writes exchange_rate record to logger                   #
#                                                                              #
# Parameters: rate      exchange_rate record                                   #
#             logger    which logger to use for tracing of the exchange_rate   #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 24.03.2014 Initial version                                       #
#------------------------------------------------------------------------------#  
def trace_exchange_rate(rate,logger):
  logger.info('rate.from_currency['+ rate.from_currency  + ']')
  logger.info('rate.to_currency['  + rate.to_currency    + ']')
  logger.info('rate.rate['         + rate.rate           + ']')
  logger.info('rate.date['         + rate.date           + ']')
  logger.info('rate.time['         + rate.time           + ']')
  logger.info('rate.ask['          + rate.ask            + ']')
  logger.info('rate.bid['          + rate.bid            + ']')
#------------------------------------------------------------------------------#
# get_exchange_config: return a list of all rates which should be displayed    #
#                                                                              #
# Parameters:          None                                                    #
#                                                                              #
# ReturnValues:  list of location names and associated URLs                    #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 24.03.2014 Initial version                                       #
#------------------------------------------------------------------------------#  
def get_exchange_rate_config():
  logger = logging.getLogger(LOGGER)
  exchange_config=[]
  url_yahooapi='http://query.yahooapis.com/v1/public/yql?q=select * from yahoo.finance.xchange where pair in ("#PAIR")&diagnostics=false&env=store://datatables.org/alltableswithkeys'
  for config in y_disp_global.CONFIG['exchange_rates_yahoo'] :
    from_currency,to_currency=y_disp_global.CONFIG['exchange_rates_yahoo'][config].split(',')
    #replace #PAIR tag in url_yahooapi with exchange rate pair
    url =url_yahooapi.replace('#PAIR', from_currency+to_currency)
    #fix encoding "non-ascii" characters in URL
    url    = urllib.parse.urlsplit(url)
    url    = list(url)    
    url[2] = urllib.parse.quote(url[2])
    url[3] = urllib.parse.quote(url[3], safe='=*()&')
    url[4] = urllib.parse.quote_plus(url[4])
    #append location and url to list  
    exchange_config.append((from_currency, to_currency, urllib.parse.urlunsplit(url)))      
  return exchange_config

#------------------------------------------------------------------------------#
# exchange_rate_deamon: responsible for collecting exchange rates for specified#
#                       currencies and send data to display thread             #
#                                                                              #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 24.03.2014 Initial version                                       #
#------------------------------------------------------------------------------# 
def exchange_rate_deamon(main_q,display_q,message_q):
  shutdown = False
  message  = None  
  exchange_rates = []
  #setup logging
  init()
  logger = logging.getLogger(LOGGER)
  exchange_rate_config=get_exchange_rate_config()
  
  while not shutdown:
    try:
      message=message_q.get(timeout=120)
      if isinstance(message, y_disp_global.MESSAGE):
        logger.debug('message.sender['   + str(message.sender)  + ']')
        logger.debug('message.receiver[' + str(message.receiver)+ ']')
        logger.debug('message.type['     + str(message.type)    + ']')
        logger.debug('message.subtype['  + str(message.subtype) + ']')
        ##############################################
        #REQUEST WEATHER FORECAST FOR SPECIFIC REGION#
        ##############################################
        if message.type == 'GET_EXCHANGE_RATE' and message.subtype=='ALL':
          rates = []
          #Loop through all configured location urls
          for config in exchange_rate_config:
            rates.append(yahoo_exchange_rate_xml(config))
          display_q.put( y_disp_global.MESSAGE('EXCHANGE','DISPLAY','EXCHANGE_RATES','GRAPH', rates))
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
      
#------------------------------------------------------------------------------#
# main: for standalone testing purposes                                        #
#                                                                              #
# Parameters:          None                                                    #
#                                                                              #
# ReturnValues:  list of location names and associated URLs                    #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 24.03.2014 Initial version                                       #
#------------------------------------------------------------------------------#        
def main():
  #get commandline arguments and setup logging
  init()
  logger = logging.getLogger(LOGGER)
  #get configuration
  exchange_rate_config=get_exchange_rate_config()
  
  rates = []
  
  #Loop through all configured exchange rates
  for config in exchange_rate_config:
    rates.append(yahoo_exchange_rate_xml(config))  
  #trace result
  for rate in rates:
    trace_exchange_rate(rate,logger)
    
if __name__ == '__main__':
  main()
