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
Handles serial communication with the ELEC Freaks SIM900 module, reads and sends
sms message and can request airtime balance
..http://pyserial.sourceforge.net/#
"""



import sys,os
import collections
import logging,traceback
import serial
import time
import configuration

IN_WAITING_TIMEOUT = 0.5
READ_TIMEOUT       = 1


sms_message = collections.namedtuple('sms', 'index status sender name date time message')
# name of logger
LOGGER = 'SIM900'

class Sim900():
 
  def __init__(self, logger):
    self.logger=logger
    #assigne serialport  
    serialPort=str(configuration.CONFIG['sim900']['SERIAL_PORT'])
    baudRate  =int(configuration.CONFIG['sim900']['BAUD_RATE'])
    self.logger.debug('using serial port['+serialPort+'] baudRate['+str(baudRate)+'] readTimeout[' + str(READ_TIMEOUT)+']')    
    self.ser = serial.Serial(serialPort, baudRate, timeout=READ_TIMEOUT )
    self.inWaitingTimeout=IN_WAITING_TIMEOUT
    # wait for connection to intialize
    time.sleep(1)
    # not interested in whatever is in the input buffer
    self.ser.flushInput()    
  #------------------------------------------------------------------------------#
  # getAirtimeBalance: request airtime balance from the network                  #
  #                                                                              #
  # Parameters: none                                                        #
  #                                                                              #
  # returnvalues: reply from the network                                         #
  #------------------------------------------------------------------------------#
  # version who when       description                                           #
  # 1.00    hta 12.05.2014 Initial version                                       #
  #------------------------------------------------------------------------------#      
  def getAirtimeBalance(self):
    # get configured ussd code, this is network dependent
    ussd = serialPort=str(configuration.CONFIG['sim900']['ussd_balance'])
    return self.unstructSuppServiceData(ussd)

  #------------------------------------------------------------------------------#
  # getModelIdentification: retrieve model identification from device            #
  #                                                                              #
  # Parameters: none                                                             #
  #                                                                              #
  # returnvalues: returnChar String represnting value of firmware version        #
  #------------------------------------------------------------------------------#
  # version who when       description                                           #
  # 1.00    hta 12.05.2014 Initial version                                       #
  #------------------------------------------------------------------------------#      
  def getModelIdentification(self):
    # prepare the command
    cmd=bytes('AT+CGMM\r\n','utf-8')
    self.send(cmd)
    response=self.recv()
    if len(response)>=2:
      return response[2]
    else:
      return 'UNKNOWN'
  #------------------------------------------------------------------------------#
  # unstructSuppServiceData: send ussd code to the network                       #
  #                                                                              #
  # Parameters: ussd code                                                        #
  #                                                                              #
  # returnvalues: reply from the network                                         #
  #------------------------------------------------------------------------------#
  # version who when       description                                           #
  # 1.00    hta 12.05.2014 Initial version                                       #
  #------------------------------------------------------------------------------#      
  def unstructSuppServiceData(self,ussd):
    # prepare the command
    cmd=bytes('AT+CUSD=1,"'+ussd+'"\r\n','utf-8')
    self.send(cmd)
    response=self.recv()
    if response[len(response)-1]=='OK':
      #device processed command, now we need to wait for
      #the reply from the network, this can take a bit longer
      self.ser.timeout=20 
      response=self.recv()
      self.ser.timeout=READ_TIMEOUT #restore readtimeout
    return response
  #------------------------------------------------------------------------------#
  # selectSMSMessageFormat: select sms message format                            #
  #                                                                              #
  # Parameters: format : 0=pdu                                                   #
  #                      1=text                                                  #
  #                                                                              #
  # returnvalues: OK or ERROR                                                    #
  #------------------------------------------------------------------------------#
  # version who when       description                                           #
  # 1.00    hta 12.05.2014 Initial version                                       #
  #------------------------------------------------------------------------------#      
  def selectSMSMessageFormat(self,format):
    # prepare the command
    cmd=bytes('AT+CMGF='+str(format)+'\r\n','utf-8')
    self.send(cmd)
    response=self.recv()
    return response[len(response)-1]
  #------------------------------------------------------------------------------#
  # listSMSMessages: get list of SMS messages                                    #
  #                                                                              #
  # Parameters: status : REC_UNREAD (received unread)                            #
  #                      REC_READ   (received read)                              #
  #                      STO UNSENT (stored not sent)                            #
  #                      STO SENT   (stored and sent)                            #
  #                      ALL        (all messages)                               #
  #             mode   : 0 normal                                                #
  #                      1 dont changes status i.e. from UNREAD to READ          #
  #                                                                              #
  # returnvalues: list of sms messages                                           #
  #------------------------------------------------------------------------------#
  # version who when       description                                           #
  # 1.00    hta 12.05.2014 Initial version                                       #
  #------------------------------------------------------------------------------#      
  def listSMSMessages(self,status,mode=0):
    # prepare the command
    cmd=bytes('AT+CMGL="'+status+'",'+str(mode)+'\r\n','utf-8')
    self.send(cmd)
    #increase inWaiting timeout for reception of serial data
    self.inWaitingTimeout=1
    response=self.recv()
    self.inWaitingTimeout=IN_WAITING_TIMEOUT
    #create a list of sms messages
    messages=[]
    for i in range (len(response)):
      #notice that there is no errorhandling... if for some reason we 
      #dont manage to get all the data from the device this will all
      #go horribly wrong!
      if response[i].startswith('+CMGL:'): #start of an sms record
        line=response[i].split(',') #first line of sms record
        index=line[0].split(' ')[1].strip()
        status=line[1].strip('"')
        sender=line[2].strip('"')
        name  =line[3].strip('"')
        date  =line[4].strip('"')
        time  =line[5].strip('"')
        message=response[i+1]
        messages.append(sms_message(index,status,sender,name,date,time,message))
    return messages    
  #------------------------------------------------------------------------------#
  # deleteSMS: delete sms messages(s)                                            #
  #                                                                              #
  # Parameters: index : index of message to delete 1-25                          #
  #             delflag: 0 delete message specified by index                     #
  #                      1 delete all read messages                              #
  #                      2 delete all read and sent message                      #
  #                      3 delete all read sent and not sent messages            #
  #                      4 delete all messages                                   #
  #                                                                              #
  # returnvalues: OK or ERROR                                                    #
  #------------------------------------------------------------------------------#
  # version who when       description                                           #
  # 1.00    hta 12.05.2014 Initial version                                       #
  #------------------------------------------------------------------------------#      
  def deleteSMS(self,index,delflag=0):
    # prepare the command
    cmd=bytes('AT+CMGD='+str(index)+','+str(delflag)+'\r\n','utf-8')
    self.send(cmd)
    response=self.recv()
    return response[len(response)-1]
  #------------------------------------------------------------------------------#
  # sendSMS: send an sms message                                                 #
  #                                                                              #
  # Parameters: da : destination address i.e. telephonenumber                    #
  #             message: message, max 160 characters                             #
  #                                                                              #
  # returnvalues: OK or ERROR                                                    #
  #------------------------------------------------------------------------------#
  # version who when       description                                           #
  # 1.00    hta 12.05.2014 Initial version                                       #
  #------------------------------------------------------------------------------#      
  def sendSMS(self,da,message):
    # prepare the command
    cmd=bytes('AT+CMGS="'+da+'"\r','utf-8')
    self.send(cmd)
    time.sleep(1) #this is necessary, if we are too fast the message does not go out properly. 
    cmd=bytes(message+'\x1A','utf-8') #\x1A is CRTL-Z which terminates the message
    self.send(cmd)
    time.sleep(2) #this is also necessary, if we are too fast the message does not go out properly
    #network sends back a message reference value
    #this can take a bit longer
    #increase inWaiting timeout for reception of serial data
    self.inWaitingTimeout=2
    self.ser.timeout=20 
    response=self.recv()
    self.ser.timeout=READ_TIMEOUT #restore readtimeout      
    self.inWaitingTimeout=IN_WAITING_TIMEOUT      
    logger.debug(response)  
    return response[len(response)-1]    
  #------------------------------------------------------------------------------#
  # send: send a command to the device                                           #
  #                                                                              #
  # Parameters: cmd command to be sent to device, sequence of bytes              #
  #                                                                              #
  # returnvalues: none                                                           #
  #------------------------------------------------------------------------------#
  # version who when       description                                           #
  # 1.00    hta 12.05.2014 Initial version                                       #
  #------------------------------------------------------------------------------#      
  def send(self,cmd):   
    self.ser.write(cmd)     
  #------------------------------------------------------------------------------#
  # recv: receive data from device. A read timout can (must) be configured       #
  #                                                                              #
  # Parameters: none                                                             #
  #                                                                              #
  # returnvalues: a list of strings, the data received from the device is split  #
  #               at \r\n                                                        #
  #------------------------------------------------------------------------------#
  # version who when       description                                           #
  # 1.00    hta 12.05.2014 Initial version                                       #
  #------------------------------------------------------------------------------#      
  def recv(self):   
    # Wait for response
    response = bytes()
    doneInWaiting=False
    iInWaiting=0
    while True:
      r =self.ser.read(1) #we have set a timeout of 1 sec
      if not doneInWaiting:  # try and use inWaiting, this will help with long timeouts
        doneInWaiting=True
        time.sleep(self.inWaitingTimeout)
        iInWaiting=self.ser.inWaiting()
        logger.debug('iInWaiting[' + str(iInWaiting) + ']')
      if r==bytes('','utf-8'): # i.e. timeout nothing was read
        break
      response+=r
      
      if iInWaiting > 0:
        response+=self.ser.read(iInWaiting)
        break
    try:
      lines = response.decode('utf-8','ignore').strip().split('\r\n')
      return lines
    except Exception:
      self.logger.error('unexpected error ['+  str(traceback.format_exc()) +']')    
      
configuration.general_configuration();
configuration.logging_configuration();
configuration.init_log(LOGGER);
logger = logging.getLogger(LOGGER)

sim900=Sim900(logger)
#logger.debug(sim900.getModelIdentification())

#logger.debug(sim900.getAirtimeBalance())

logger.debug(sim900.selectSMSMessageFormat(1))

#logger.debug(sim900.listSMSMessages('ALL'))

#logger.debug(sim900.deleteSMS(4,0))

#logger.debug(sim900.listSMSMessages('ALL'))

logger.debug(sim900.sendSMS('+27782475857','Yippee it is working now\r\ntwo lines'))

