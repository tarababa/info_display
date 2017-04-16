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
manages buttons pressed on yocto maxi displays and controls
menu navigation accordingly2
             
"""

import os,sys
import time
import logging, traceback
import queue
import collections
import configuration
import menu
sys.path.append(os.path.join('yoctolib_python','Sources'))
from yocto_api import *
from yocto_anbutton import *

LOGGER         = 'BUTTON'     #name of logger for the yoctopuce button module
logger         = None
button_q       = None
button_module  = collections.namedtuple('button_module', 'module module_name ' +
                                                         'button1 button2 ' +
                                                         'button3 button4 ' +
                                                         'button5 button6 ' +
                                                         'current uptime')
B1LastTimeReleased = 0
B2LastTimeReleased = 0
B3LastTimeReleased = 0
B4LastTimeReleased = 0
B5LastTimeReleased = 0
B6LastTimeReleased = 0
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
  global logger
  configuration.init_log(LOGGER); 
  logger = logging.getLogger(LOGGER)  
  
#------------------------------------------------------------------------------#
# get_module: Get an instance of the yoctopuce meteo module                    #
#                                                                              #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 09.11.2013 Initial version                                       #
#------------------------------------------------------------------------------#  
def get_module(name):
  global logger
  errmsg=YRefParam()  
  # Setup the API to use local USB devices
  # Setup the API to use local USB devices
  # Note this may fail with a return code -6, device busy and
  # an error message, YAPI  already registerd. This seems to happen
  # when multiple threads are trying to do this simultaneously. When
  # RegisterHub fails get_module returns None, it is up to the caller
  # to attempt RegisterHub again
  try:
    retVal=YAPI.RegisterHub("usb", errmsg)
    if retVal != YAPI.SUCCESS:
      logger.warning('YAPI.RegisterHub['+str(retVal)+'] errmsg['+errmsg.value+']')
      return None
  except Exception as err:
    # catch things like: "OSError: exception: access violation writing 0x0000000000000000"
    logger.error(str(err))
    return None
  if name == None or name == '':
    #No particular logical name or serial number specified
    #then just get the first humidity sensor and determine
    #its module
    button = YAnButton.FirstAnButton()    
    if button is None:
      logger.error('failed to find a button')
      return None
    else:
      module = button.get_module()
      name = module.get_serialNumber()
      logger.info('got module.get_serialNumber['+ module.get_serialNumber() +']'+
                      ' module.get_logicalName['+ module.get_logicalName()  +']')
  else:
    logger.debug('looking for specific module with logical name[' + name + ']')
    module = YModule.FindModule(name)
    if str(module).endswith('unresolved'):
      logger.error('failed to find module for name['+name+']')
      return None
    else:
      logger.info('got module.get_serialNumber['+ module.get_serialNumber() +']'+
                      ' module.get_logicalName['+ module.get_logicalName()  +']')      
        
  return module  

#------------------------------------------------------------------------------#
# doValueChangeCallback: Callback function, called each time button value      #
#                        changes, which in turn triggers a message to the      #
#                        button deamon                                         #
# Parameter: data: user data associated with callback, as set when creating the#
#                  callback                                                    #
#            value: current (new) advertised value, aprox. 0 when button       #
#                   and aprox 999 when button not pressed                      #
#                                                                              #
# ReturnValues:  None                                                          #
#                                                                              #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 30.05.2014 Initial version                                       #
#------------------------------------------------------------------------------#   
def doValueChangeCallback(data,value):
  global logger, button_q, B1LastTimeReleased, B2LastTimeReleased, B3LastTimeReleased
  global B4LastTimeReleased, B5LastTimeReleased, B6LastTimeReleased
  delay = 250 #Minimum delay between button presses
  delayTooShort = False
  userData = data.get_userData()  
  logger.info('got button['+userData['button'] +'] value['+value+']')
  try:
    lastTimeReleased = data.get_lastTimeReleased()
    if userData['button'] == 'B1':
      logger.info('got button['+userData['button'] +'] lastTimeReleased['+str(lastTimeReleased)+'] B1LastTimeReleased['+str(B1LastTimeReleased)+']')          
      if lastTimeReleased - B1LastTimeReleased < delay:
        delayTooShort = True
      else: B1LastTimeReleased = lastTimeReleased
    elif userData['button'] == 'B2':
      logger.info('got button['+userData['button'] +'] lastTimeReleased['+str(lastTimeReleased)+'] B2LastTimeReleased['+str(B2LastTimeReleased)+']')          
      if lastTimeReleased - B2LastTimeReleased < delay:
        delayTooShort = True
      else: B2LastTimeReleased = lastTimeReleased
    elif userData['button'] == 'B3':
      logger.info('got button['+userData['button'] +'] lastTimeReleased['+str(lastTimeReleased)+'] B3LastTimeReleased['+str(B3LastTimeReleased)+']')          
      if lastTimeReleased - B3LastTimeReleased < delay:
        delayTooShort = True
      else: B3LastTimeReleased = lastTimeReleased     
    elif userData['button'] == 'B4':
      logger.info('got button['+userData['button'] +'] lastTimeReleased['+str(lastTimeReleased)+'] B4LastTimeReleased['+str(B4LastTimeReleased)+']')          
      if lastTimeReleased - B4LastTimeReleased < delay:
        delayTooShort = True
      else: B4LastTimeReleased = lastTimeReleased  
    elif userData['button'] == 'B5':
      logger.info('got button['+userData['button'] +'] lastTimeReleased['+str(lastTimeReleased)+'] B5LastTimeReleased['+str(B5LastTimeReleased)+']')          
      if lastTimeReleased - B5LastTimeReleased < delay:
        delayTooShort = True
      else: B5LastTimeReleased = lastTimeReleased       
    elif userData['button'] == 'B6':
      logger.info('got button['+userData['button'] +'] lastTimeReleased['+str(lastTimeReleased)+'] B6LastTimeReleased['+str(B6LastTimeReleased)+']')          
      if lastTimeReleased - B6LastTimeReleased < delay:
        delayTooShort = True
      else: B6LastTimeReleased = lastTimeReleased           
  except Exception as err:
    logger.error('unexpected error ['+ str(traceback.format_exc()) + ']')   
  try:
    if int(value) > 700 and not delayTooShort:
      #button pressed
      message = configuration.MESSAGE('BUTTON','BUTTON','BUTTON','PRESSED',userData['button'])
      button_q.put(message)     
  except Exception as err:
    logger.error('unexpected error ['+ str(traceback.format_exc()) + ']') 
#------------------------------------------------------------------------------#
# do_buttons: Create instance of button module if necessary, instantiate the   #
#             buttons if necessary and return sensor readings                  #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 09.11.2013 Initial version                                       #
#------------------------------------------------------------------------------#   
def do_buttons(module):
  global logger
  #Initialize variables
  module_name        = None  
  ymodule            = None  
  button1            = None
  button2            = None
  button3            = None
  button4            = None
  button5            = None
  button6            = None
  current            = None 
  uptime             = None
    
  
  #if we previously created a valid instance of the 
  #button module then we use that one.
  if  isinstance(module, button_module) and module.module != None:
    module_name        = module.module_name    
    ymodule            = module.module            
    button1            = module.button1   
    button2            = module.button2   
    button3            = module.button3   
    button4            = module.button4
    button5            = module.button5
    button6            = module.button6   
    current            = module.current          
    uptime             = module.uptime


    
  try:
    #button module ready to go?  
    #If yes then initialize individual buttons 
    #if necessary and obtain readings
    if ymodule != None and ymodule.isOnline:
      #if buttons not created then create
      #once created obtain pulse counter and is pressed status
      if button1 == None:
        button1 = YAnButton.FindAnButton(module_name + '.anButton1')
        button1.registerValueCallback(None)        
        button1.set_sensitivity(1000)
        button1.set_calibrationMax(10)
        button1.set_calibrationMin(0)      
        button1.set_userData({'button':'B1','unit':''})
        button1.registerValueCallback(doValueChangeCallback)        
      if button2 == None:
        button2 = YAnButton.FindAnButton(module_name + '.anButton2')
        button2.registerValueCallback(None)        
        button2.set_sensitivity(1000)
        button2.set_calibrationMax(10)
        button2.set_calibrationMin(0)          
        button2.set_userData({'button':'B2','unit':''})
        button2.registerValueCallback(doValueChangeCallback)          
      if button3 == None:
        button3 = YAnButton.FindAnButton(module_name + '.anButton3')
        button3.registerValueCallback(None)                
        button3.set_sensitivity(1000)
        button3.set_calibrationMax(10)
        button3.set_calibrationMin(0)          
        button3.set_userData({'button':'B3','unit':''})
        button3.registerValueCallback(doValueChangeCallback)          
      if button4 == None:
        button4 = YAnButton.FindAnButton(module_name + '.anButton4')
        button4.registerValueCallback(None)                        
        button4.set_sensitivity(1000)
        button4.set_calibrationMax(10)
        button4.set_calibrationMin(0)         
        button4.set_userData({'button':'B4','unit':''})
        button4.registerValueCallback(doValueChangeCallback)             
      if button5 == None:
        button5 = YAnButton.FindAnButton(module_name + '.anButton5')
        button5.registerValueCallback(None)                        
        button5.set_sensitivity(1000)
        button5.set_calibrationMax(10)
        button5.set_calibrationMin(0)              
        button5.set_userData({'button':'B5','unit':''})
        button5.registerValueCallback(doValueChangeCallback)         
      if button6 == None:
        button6 = YAnButton.FindAnButton(module_name + '.anButton6')
        button6.registerValueCallback(None)                
        button6.set_sensitivity(1000)
        button6.set_calibrationMax(10)
        button6.set_calibrationMin(0)              
        button6.set_userData({'button':'B6','unit':''})
        button6.registerValueCallback(doValueChangeCallback)            
        
      current = ymodule.get_usbCurrent()
      uptime  = ymodule.get_upTime()/1000
      logger.debug('done getting current and uptime')
    else:
      #Module has not been intialized or is not online
      #then go and try to intialize the module
      if configuration.CONFIG.has_option('y_button','button_logical_name'):
        #if configured get a specific module
        ymodule = get_module(configuration.CONFIG['y_button']['button_logical_name'])
      else:
        #not configured get any module
       ymodule = get_module(None)          
      if ymodule != None:
        module_name = ymodule.get_serialNumber()
        # Yocto module has been initialized, then lets 
        # populate our data model for the display module
        # we have an instance of the display module
        module = button_module(ymodule,module_name, button1,  
                                                    button2, 
                                                    button3, 
                                                    button4, 
                                                    button5, 
                                                    button6, 
                                                    current, uptime)
        # recursively collect "data" from the module i.e. current and uptime
        return do_buttons(module)        
  except YAPI.YAPI_Exception as err:
    logger.error(str(err))
    ymodule = None
    module_name = None
  
  return button_module(ymodule,module_name, button1, 
                                            button2,
                                            button3,
                                            button4,
                                            button5,
                                            button6,
                                            current, uptime)

#------------------------------------------------------------------------------#
# init_module: Returns an instance of the button_module                        #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 09.11.2013 Initial version                                       #
#------------------------------------------------------------------------------#
def init_module():
 return button_module(None,None,None,None,None,
                      None,None,None,None,None) 
#------------------------------------------------------------------------------#
# trace_result: Trace result to a log file, get a logger if none is provided   #
#                                                                              #
# Parameters: result  result record                                            #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 23.01.2014 Initial version                                       #
#------------------------------------------------------------------------------#  
def trace_result(result):
  global logger
  trace_result(result,logger) 
#------------------------------------------------------------------------------#
# trace_result: write button data to logger                                    #
#                                                                              #
# Parameters: result  result record                                            #
#             logger  which logger to use to trace result record to            #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 09.11.2013 Initial version                                       #
#------------------------------------------------------------------------------#
def trace_result(result,logger):
  if result.module != None and result.pulsecounter1!=None:
    logger.info('current['     + '%2.2f' % current     +' mA]' +
                'uptime['      + str(uptime)           +' s]'  )
  else:
    logger.warn('no yoctopuce module instanciated, module['       + str(result.module) +']' +
                'or init not complete, no button reading uptime[' + str(result.uptime) +']' )  
#------------------------------------------------------------------------------#
# meteo_deamon: Instanciate button module and poll it for button data.         #
#               whenever change in a monitored button is detected determine    #
#               new menu point, if possilbe                                    #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 09.11.2013 Initial version                                       #
#------------------------------------------------------------------------------# 
def button_deamon(main_q, message_q, display_q, radio_q):
  global logger, button_q
  button_q=message_q
  init()

  shutdown = False
  message  = None   
  module   = init_module()
  myMenu=menu.Menu()
  
  #initialize module
  while module.module == None:
    module = do_buttons(init_module())
    if module.module == None:
      time.sleep(1)
      
  #initialized, send active menu to display module
  display_q.put(configuration.MESSAGE('BUTTON','DISPLAY','MENU', None, myMenu.active()))
  
  #listen for message to execute.
  while not shutdown:
    logger.debug('going to listen on message queue')
    try:
      message=message_q.get(timeout=1)
      if isinstance(message, configuration.MESSAGE):
        logger.debug('message.sender['   + str(message.sender)  + ']')
        logger.debug('message.receiver[' + str(message.receiver)+ ']')
        logger.debug('message.type['     + str(message.type)    + ']')
        logger.debug('message.subtype['  + str(message.subtype) + ']')      
        ##################
        #SHUTDOWN REQUEST#
        ##################
        if message.type == 'SHUTDOWN':
          shutdown=True
          logger.warning('got SHUTDOWN request, shutting down')
        ########################
        #BUTTON PRESSED MESSAGE#
        ########################          
        elif message.type == 'BUTTON':
          if message.subtype == 'PRESSED':
            if message.content == 'B1': 
              #button 1 pressed? this is the navigate LEFT button
              myMenu.left()
              #inform display module
              display_q.put(configuration.MESSAGE('BUTTON','DISPLAY','MENU', None, myMenu.active()))
              logger.info('left, activeMenu['+str(myMenu.active().id)+']')          
            elif message.content == 'B2':
            #button 2 pressed? this is the navigate RIGHT button
              myMenu.right()
              #inform display module        
              display_q.put(configuration.MESSAGE('BUTTON','DISPLAY','MENU', None, myMenu.active()))
              logger.info('right, activeMenu['+str(myMenu.active().id)+']')
            elif message.content == 'B2':
            #button 2 pressed? this is the navigate RIGHT button
              myMenu.right()
              #inform display module        
              display_q.put(configuration.MESSAGE('BUTTON','DISPLAY','MENU', None, myMenu.active()))
              logger.info('right, activeMenu['+str(myMenu.active().id)+']')
            #button 3 pressed? this is the navigate UP button
            elif message.content == 'B3':
              myMenu.up()
              # for multimenu i.e. dynamic menu, when there is only one menu
              # make sure pageindex is set to 0 when up or down button is pressed
              # and the OK button is no longer active
              if not myMenu.getOk():
                display_q.put(configuration.MESSAGE('BUTTON','DISPLAY','MENU','RESET_PAGEINDEX', myMenu.active()))                
              #inform display module
              display_q.put(configuration.MESSAGE('BUTTON','DISPLAY','MENU', None, myMenu.active()))
              logger.info('up, activeMenu['+str(myMenu.active().id)+']')
            #button 4 pressed? this is the navigate DOWN button
            elif message.content == 'B4':
              myMenu.down()
              # for multimenu i.e. dynamic menu, when there is only one menu
              # make sure pageindex is set to 0 when up or down button is pressed
              # and the OK button is no longer active
              if not myMenu.getOk():
                display_q.put(configuration.MESSAGE('BUTTON','DISPLAY','MENU','RESET_PAGEINDEX', myMenu.active()))          
              #inform display module        
              display_q.put(configuration.MESSAGE('BUTTON','DISPLAY','MENU', None, myMenu.active()))
              logger.info('down, activeMenu['+str(myMenu.active().id)+']')
            #button 5 pressed? this is the OK button, this button is used to "lock" 
            #multipage screens whereupon the up/down buttons can be used to page 
            #through the pages. Pressing OK again, unlocks the multipage screen and
            #allows the user to use the up and down buttons to navigate to the next
            #menu/screen
            elif message.content == 'B5':
              myMenu.ok()
              logger.info('OK, activeMenu['+str(myMenu.active().id)+']')     
            #button 6 pressed? this is our exit button which
            #sends shutdown to all threads
            elif message.content == 'B6':
              #if the radio menu is active we use button 6 to toggle the radio on/off 
              #rather then for shutting down the info_display program.
              if myMenu.active().id == 'menu_radio':
                message = configuration.MESSAGE('BUTTON','RADIO','PLAY','TOGGLE',None)
                radio_q.put(message)                
              else:
                message = configuration.MESSAGE('BUTTON','MAIN','SHUTDOWN',None,None)
                main_q.put(message)                       
        else:
          logger.warning('got unknown message')
    except queue.Empty as err:  
      module=do_buttons(module)
      if module.module != None:
        YAPI.HandleEvents()
    except:
      logger.error('unexpected error ['+ str(traceback.format_exc()) +']')       

