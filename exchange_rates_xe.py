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
collects exchange rate information from xe.com and passes the information on to
the y_maxi_display.py module for visualisation
             
"""

import os,sys
import logging, traceback
import queue
import urllib, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
import collections
import configuration


LOGGER = 'XE.EXCHANGE'  #name of logger for this module

#define collections to hold exchange rates
exchange_rate = collections.namedtuple("exchange_rate","from_currency to_currency rate date time ask bid")

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
  
def getExchangeRate():
  logger = logging.getLogger(LOGGER)
  logger.debug('start')
  
  #provider of exchange rate
  url = 'http://www.xe.com/currencyconverter/convert.cgi'
  #spoof the user agent.
  user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'

  headers = { 'User-Agent' : user_agent }

  #SLOG proxy
  #proxy_support = urllib.request.ProxyHandler({'http' : '172.20.5.199:8080'})
  #opener = urllib.request.build_opener(proxy_support)
  #urllib.request.install_opener(opener)
  logger.debug('url['+url+'?'+url_values+']')  
  req = urllib.request.Request(url+'?'+url_values, None, headers)
  response = urllib.request.urlopen(req)
  the_page = response.read()

  myString = str( the_page, encoding='utf8' )
  #print (myString)
  mySubString=myString[myString.find("1 CHF ="):   myString.find("1 CHF =") + myString[myString.find("1 CHF ="):].find(" ZAR</span>")+4]
  logger.debug('mySubString[' + mySubString + ']') 
  
 
  sTimestamp=myString[myString.find("Live rates at ")+14:myString.find("Live rates at ")+14+23]
  logger.debug('sTimestamp[' + sTimestamp + ']') 
  #Live rates at 2013.09.01 07:25:00 UTC &#160; </div>
  
  sBaseCurrency = "CHF"
  sCurrency     = "ZAR"
  sRate         = mySubString[mySubString.find("1 CHF = ")+8: mySubString.find(" ZAR")]
  logger.debug('sRate[' + sRate + ']')   
  return sBaseCurrency, sCurrency, sRate, sTimestamp
#------------------------------------------------------------------------------#
# xe_exchange_rate_xml: get exchange rate from XE                              #
#                                                                              #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 24.03.2014 Initial version                                       #
#------------------------------------------------------------------------------#
def xe_exchange_rate(config):
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

  try:
    response = str( urllib.request.urlopen(req,timeout=120).read(), encoding='utf8' )
  except:
    #sometimes we get urllib.error.HTTPError: HTTP Error 400: Bad Request
    #to try and figure out what went wrong we trace the request
    logger.error('req['+str(req)+']')
    logger.error('unexpected error ['+  str(traceback.format_exc()) +']')   
  
  fromCurrency = '1 ' + config[0] + ' = '
  toCurrency   = ' '  + config[1] + '</span>'
  #find exchange rate  
  this_exchange_rate = response[response.find(fromCurrency)+len(fromCurrency) : response.find(toCurrency)]
  logger.debug('this_exchange_rate['+this_exchange_rate+']')
  ask = this_exchange_rate 
  bid = this_exchange_rate 
  
  #find time and date
  dateTimeMarker = 'Live rates at '
  date=response[response.find(dateTimeMarker)+len(dateTimeMarker):response.find(dateTimeMarker)+len(dateTimeMarker)+10]
  time=response[response.find(dateTimeMarker)+len(dateTimeMarker)+10+1:response.find(dateTimeMarker)+len(dateTimeMarker)+10+1+8]
  logger.debug('date[' + date + ']') 
  logger.debug('time[' + time + ']') 
 
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
  data={}
  data['template']='crm1'
  data['Amount']='1'  
  url_xe='http://www.xe.com/currencyconverter/convert.cgi?'
  for config in configuration.CONFIG['exchange_rates'] :
    if config.find('rate.') >= 0:    
      from_currency,to_currency=configuration.CONFIG['exchange_rates'][config].split(',')
      data['From']=from_currency
      data['To']=to_currency
      url_values = urllib.parse.urlencode(data)    
      url = url_xe + url_values  
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
      if isinstance(message, configuration.MESSAGE):
        logger.debug('message.sender['   + str(message.sender)  + ']')
        logger.debug('message.receiver[' + str(message.receiver)+ ']')
        logger.debug('message.type['     + str(message.type)    + ']')
        logger.debug('message.subtype['  + str(message.subtype) + ']')
        ########################
        #REQUEST EXCHANGE RATES#
        ########################
        if message.type == 'GET_EXCHANGE_RATE' and message.subtype=='ALL':
          rates = []
          #Loop through all configured location urls
          for config in exchange_rate_config:
            rates.append(xe_exchange_rate(config))
          display_q.put( configuration.MESSAGE('EXCHANGE','DISPLAY','EXCHANGE_RATES','GRAPH', rates))
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
      


configuration.logging_configuration()  
configuration.general_configuration()  
#configuration.init_log(LOGGER)
exchange_rates = []
rates = []
init()
exchange_rate_config=get_exchange_rate_config()
print(xe_exchange_rate(exchange_rate_config[0]))


for config in exchange_rate_config:
  rates.append(xe_exchange_rate(config))
  
print (rates)
