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
Returns date and time in plain text
             
"""

import os,sys
import datetime
import logging, traceback
import configuration
import configparser

class Clock():
  def __init__(self):
    self.clocks=self.doInitClocks()
    self.numOfClocks=len(self.clocks)
    self.seconds=0
    self.lastTime=''
    
  #------------------------------------------------------------------------------#
  # doInitClocks: load language files for clocks                                 #
  #                                                                              #
  #                                                                              #
  #------------------------------------------------------------------------------#
  # version who when       description                                           #
  # 1.00    hta 09.08.2014 Initial version                                       #
  #------------------------------------------------------------------------------#  
  def doInitClocks(self):
    hours={}
    minutes={}
    clocks=[]
    next_hour_from = 60
    clockConfiguration = configparser.ConfigParser(allow_no_value=True)
    clockConfiguration.read('./etc/clocks.ini')
    
    for language in clockConfiguration :
      for config in clockConfiguration[language]:  #proces language at a time
        identifier, sequence = config.split('.')
        for pair in clockConfiguration[language][config].split(','):    
          if identifier == 'hour':
            #create dictionary for all hours
            key=(pair.split('=')[0]).strip()
            val=(pair.split('=')[1]).strip()
            hours.update(((key,val),))
          elif identifier == 'minute':
            #create dictionary for all minutes
            key=(pair.split('=')[0]).strip()
            val=(pair.split('=')[1]).strip()
            minutes.update(((key,val),))  
          elif identifier == 'next_hour_from':
            next_hour_from = eval(pair)
            
      if language != 'DEFAULT':
        clocks.append({'language':language, 'next_hour_from': next_hour_from, 'translation':(hours,minutes)})   
        hours={}
        minutes={}
    return clocks

  #------------------------------------------------------------------------------#
  # time:  returns time in plain text in a chosen language                       #
  #                                                                              #
  # Parameter:  index: pointer to specific language clock                        #
  #                                                                              #
  # ReturnValues: time: a string value for current time in chosen language       #
  #------------------------------------------------------------------------------#
  # version who when       description                                           #
  # 1.00    hta 09.08.2014 Initial version                                       #
  #------------------------------------------------------------------------------# 
  def time(self,index):
    time=''
    if index > self.numOfClocks-1:
      index = 0
    #determine language associated with index  
    language=self.clocks[index].get('language')
    #get current time
    key_hour=str(datetime.datetime.now().hour).zfill(2)
    key_minute=str(datetime.datetime.now().minute).zfill(2)
    self.seconds=datetime.datetime.now().second
    
    #Use next hour, language specific
    if int(key_minute) > self.clocks[index].get('next_hour_from'):
        key_hour = str(int(key_hour)+1).zfill(2)
    
    #differentiate between whole hours    
    if key_minute=='00':
      key_hour=key_hour+key_minute
      time=self.clocks[index].get('translation')[0].get(key_hour)
    else:
      time=self.clocks[index].get('translation')[1].get(key_minute) + ' ' + self.clocks[index].get('translation')[0].get(key_hour)
    
    return time
    
  #------------------------------------------------------------------------------#
  # setLastTime:  update value of lastTime to the value passed by the caller     #
  #               Is used by caller to avoid updating display when time has not  #
  #               changed between calls, at least not from an hour/minute per-   #
  #               perspective                                                    #
  #                                                                              #
  # Parameter:    time: desired value of lasttime                                #
  #                                                                              #
  # ReturnValues: time: a string value for current time in chosen language       #
  #------------------------------------------------------------------------------#
  # version who when       description                                           #
  # 1.00    hta 10.08.2014 Initial version                                       #
  #------------------------------------------------------------------------------#    
  def setLastTime(self,time):
    self.lastTime=time
    

