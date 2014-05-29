################################################################################
# Application         : manage buttons
# File                : $HeadURL:  $
# Version             : $Revision: $
# Created by          : hta
# Created             : 01.10.2013
# Changed by          : $Author: b7tarah $
# File changed        : $Date: 2013-08-21 15:19:43 +0200 (Mi, 21 Aug 2013) $
# Environment         : Python 3.2.3 
# ##############################################################################
# Description: manages buttons pressed on yocto maxi displays and controls
#              menu navigation accordingly
#
################################################################################


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

LOGGER = 'BUTTON'     #name of logger for the yoctopuce button module

button_module  = collections.namedtuple('button_module', 'module module_name ' +
                                                         'button1 pulsecounter1 prevcounter1 buttonpressed1 prevpressed1 button2 pulsecounter2 prevcounter2 buttonpressed2 prevpressed2 ' +
                                                         'button3 pulsecounter3 prevcounter3 buttonpressed3 prevpressed3 button4 pulsecounter4 prevcounter4 buttonpressed4 prevpressed4 ' +
                                                         'button5 pulsecounter5 prevcounter5 buttonpressed5 prevpressed5 button6 pulsecounter6 prevcounter6 buttonpressed6 prevpressed6 ' +
                                                         'current uptime')
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
# get_module: Get an instance of the yoctopuce meteo module                    #
#                                                                              #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 09.11.2013 Initial version                                       #
#------------------------------------------------------------------------------#  
def get_module(name):
  logger = logging.getLogger(LOGGER)  
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
  if name == None:
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
    if module == None:
      logger.error('failed to module for name['+name+']')
      return None
    else:
      logger.info('got module.get_serialNumber['+ module.get_serialNumber() +']'+
                      ' module.get_logicalName['+ module.get_logicalName()  +']')      
        
  return module  
  
#------------------------------------------------------------------------------#
# meteo_data: Create instance of button module if necessary, instantiate the   #
#             buttons if necessary and return sensor readings                  #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 09.11.2013 Initial version                                       #
#------------------------------------------------------------------------------#   
def do_buttons(module):
  #Initialize variables
  module_name        = None  
  ymodule            = None  
  button1            = None
  pulsecounter1      = None
  prevcounter1       = None
  buttonpressed1     = None
  prevpressed1       = None 
  button2            = None
  pulsecounter2      = None
  prevcounter2       = None 
  buttonpressed2     = None
  prevpressed2       = None 
  button3            = None
  pulsecounter3      = None
  prevcounter3       = None
  buttonpressed3     = None
  prevpressed3       = None 
  button4            = None
  pulsecounter4      = None
  prevcounter4       = None
  buttonpressed4     = None
  prevpressed4       = None 
  button5            = None
  pulsecounter5      = None
  prevcounter5       = None
  buttonpressed5     = None
  prevpressed5       = None
  button6            = None
  pulsecounter6      = None
  prevcounter6       = None
  buttonpressed6     = None
  prevpressed6       = None
  current            = None 
  uptime             = None
    
  logger = logging.getLogger(LOGGER)
  #if we previously created a valid instance of the 
  #button module then we use that one.
  if  isinstance(module, button_module) and module.module != None:
    module_name        = module.module_name       
    ymodule            = module.module            
    button1            = module.button1   
    pulsecounter1      = module.pulsecounter1
    buttonpressed1     = module.buttonpressed1
    button2            = module.button2   
    pulsecounter2      = module.pulsecounter2
    buttonpressed2     = module.buttonpressed2
    button3            = module.button3   
    pulsecounter3      = module.pulsecounter3
    buttonpressed3     = module.buttonpressed3
    button4            = module.button4
    pulsecounter4      = module.pulsecounter4
    buttonpressed4     = module.buttonpressed4
    button5            = module.button5
    pulsecounter5      = module.pulsecounter5
    buttonpressed5     = module.buttonpressed5
    button6            = module.button6   
    pulsecounter6      = module.pulsecounter6
    buttonpressed6     = module.buttonpressed6
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
        button1       = YAnButton.FindAnButton(module_name + '.anButton1')
      prevcounter1  = pulsecounter1
      prevpressed1  = buttonpressed1              
      pulsecounter1 = button1.get_pulseCounter()
      buttonpressed1= button1.get_isPressed()
      #called first time then init previous values to current values
      if prevcounter1 == None:
        prevcounter1 = pulsecounter1
        prevpressed1 = buttonpressed1
      if button2 == None:
        button2       = YAnButton.FindAnButton(module_name + '.anButton2')
      prevcounter2  = pulsecounter2
      prevpressed2  = buttonpressed2              
      pulsecounter2 = button2.get_pulseCounter()
      buttonpressed2= button2.get_isPressed()  
      #called first time then init previous values to current values
      if prevcounter2 == None:
        prevcounter2 = pulsecounter2
        prevpressed2 = buttonpressed2
      if button3 == None:
        button3       = YAnButton.FindAnButton(module_name + '.anButton3')
      prevcounter3  = pulsecounter3
      prevpressed3  = buttonpressed3              
      pulsecounter3 = button3.get_pulseCounter()
      buttonpressed3= button3.get_isPressed()
      #called first time then init previous values to current values
      if prevcounter3 == None:
        prevcounter3 = pulsecounter3
        prevpressed3 = buttonpressed3      
      if button4 == None:
        button4       = YAnButton.FindAnButton(module_name + '.anButton4')
      prevcounter4  = pulsecounter4
      prevpressed4  = buttonpressed4              
      pulsecounter4 = button4.get_pulseCounter()
      buttonpressed4= button4.get_isPressed()
      #called first time then init previous values to current values
      if prevcounter4 == None:
        prevcounter4 = pulsecounter4
        prevpressed4 = buttonpressed4      
      if button5 == None:
        button5       = YAnButton.FindAnButton(module_name + '.anButton5')
      prevcounter5  = pulsecounter5
      prevpressed5  = buttonpressed5        
      pulsecounter5 = button5.get_pulseCounter()
      buttonpressed5= button5.get_isPressed()
      #called first time then init previous values to current values
      if prevcounter5 == None:
        prevcounter5 = pulsecounter5
        prevpressed5 = buttonpressed5      
      if button6 == None:
        button6       = YAnButton.FindAnButton(module_name + '.anButton6')
      prevcounter6  = pulsecounter6        
      prevpressed6  = buttonpressed6        
      pulsecounter6 = button6.get_pulseCounter()
      buttonpressed6= button6.get_isPressed()
      #called first time then init previous values to current values
      if prevcounter6 == None:
        prevcounter6 = pulsecounter6
        prevpressed6 = buttonpressed6      
      current = ymodule.get_usbCurrent()
      uptime  = ymodule.get_upTime()/1000
      #logger.debug('pulsecounter1['   + str(pulsecounter1)  +'] '+
      #            'prevcounter1['    + str(prevcounter1)   +'] '+
      #            'buttonpressed1['  + str(buttonpressed1) +'] '+
      #            'prevpressed1['    + str(prevpressed1)   +'] '+
      #            'pulsecounter2['   + str(pulsecounter2)  +'] '+
      #            'prevcounter2['    + str(prevcounter2)   +'] '+
      #            'buttonpressed2['  + str(buttonpressed2) +'] '+
      #            'prevpressed2['    + str(prevpressed2)   +'] '+
      #            'pulsecounter3['   + str(pulsecounter3)  +'] '+
      #            'prevcounter3['    + str(prevcounter3)   +'] '+
      #            'buttonpressed3['  + str(buttonpressed3) +'] '+
      #            'prevpressed3['    + str(prevpressed3)   +'] '+
      #            'pulsecounter4['   + str(pulsecounter4)  +'] '+
      #            'prevcounter4['    + str(prevcounter4)   +'] '+
      #            'buttonpressed4['  + str(buttonpressed4) +'] '+
      #            'prevpressed4['    + str(prevpressed4)   +'] '+
      #            'pulsecounter5['   + str(pulsecounter5)  +'] '+
      #            'prevcounter5['    + str(prevcounter5)   +'] '+
      #            'buttonpressed5['  + str(buttonpressed5) +'] '+
      #            'prevpressed5['    + str(prevpressed5)   +'] '+
      #            'pulsecounter6['   + str(pulsecounter6)  +'] '+
      #            'prevcounter6['    + str(prevcounter6)   +'] '+
      #            'buttonpressed6['  + str(buttonpressed6) +'] '+
      #            'prevpressed6['    + str(prevpressed6)   +'] '+
      #            'current['     + '%2.2f' % current     +' mA]' +
      #            'uptime['      + str(uptime)           +' s]'  )
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
        module = button_module(ymodule,module_name, button1, pulsecounter1, prevcounter1, buttonpressed1, prevpressed1, 
                                                    button2, pulsecounter2, prevcounter2, buttonpressed2, prevpressed2,
                                                    button3, pulsecounter3, prevcounter3, buttonpressed3, prevpressed3,
                                                    button4, pulsecounter4, prevcounter4, buttonpressed4, prevpressed4,
                                                    button5, pulsecounter5, prevcounter5, buttonpressed5, prevpressed5,
                                                    button6, pulsecounter6, prevcounter6, buttonpressed6, prevpressed6,
                                                    current, uptime)
        # recursively collect "data" from the module i.e. current and uptime
        return do_buttons(module)        
  except YAPI.YAPI_Exception as err:
    logger.error(str(err))
    ymodule = None
    module_name = None
  
  return button_module(ymodule,module_name, button1, pulsecounter1, prevcounter1, buttonpressed1, prevpressed1, 
                                            button2, pulsecounter2, prevcounter2, buttonpressed2, prevpressed2,
                                            button3, pulsecounter3, prevcounter3, buttonpressed3, prevpressed3,
                                            button4, pulsecounter4, prevcounter4, buttonpressed4, prevpressed4,
                                            button5, pulsecounter5, prevcounter5, buttonpressed5, prevpressed5,
                                            button6, pulsecounter6, prevcounter6, buttonpressed6, prevpressed6,
                                            current, uptime)

#------------------------------------------------------------------------------#
# init_module: Returns an instance of the button_module                        #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 09.11.2013 Initial version                                       #
#------------------------------------------------------------------------------#
def init_module():
 return button_module(None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,
                      None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None) 
#------------------------------------------------------------------------------#
# trace_result: Trace result to a log file, get a logger if none is provided   #
#                                                                              #
# Parameters: result  result record                                            #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 23.01.2014 Initial version                                       #
#------------------------------------------------------------------------------#  
def trace_result(result):
   logger = logging.getLogger(LOGGER) #will use BUTTON logger
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
    logger.info('pulsecounter1['   + str(pulsecounter1)  +'] '+
                'prevcounter1['    + str(prevcounter1)   +'] '+
                'buttonpressed1['  + str(buttonpressed1) +'] '+
                'prevpressed1['    + str(prevpressed1)   +'] '+
                'pulsecounter2['   + str(pulsecounter2)  +'] '+
                'prevcounter2['    + str(prevcounter2)   +'] '+
                'buttonpressed2['  + str(buttonpressed2) +'] '+
                'prevpressed2['    + str(prevpressed2)   +'] '+
                'pulsecounter3['   + str(pulsecounter3)  +'] '+
                'prevcounter3['    + str(prevcounter3)   +'] '+
                'buttonpressed3['  + str(buttonpressed3) +'] '+
                'prevpressed3['    + str(prevpressed3)   +'] '+
                'pulsecounter4['   + str(pulsecounter4)  +'] '+
                'prevcounter4['    + str(prevcounter4)   +'] '+
                'buttonpressed4['  + str(buttonpressed4) +'] '+
                'prevpressed4['    + str(prevpressed4)   +'] '+
                'pulsecounter5['   + str(pulsecounter5)  +'] '+
                'prevcounter5['    + str(prevcounter5)   +'] '+
                'buttonpressed5['  + str(buttonpressed5) +'] '+
                'prevpressed5['    + str(prevpressed5)   +'] '+
                'pulsecounter6['   + str(pulsecounter6)  +'] '+
                'prevcounter6['    + str(prevcounter6)   +'] '+
                'buttonpressed6['  + str(buttonpressed6) +'] '+
                'prevpressed6['    + str(prevpressed6)   +'] '+
                'current['     + '%2.2f' % current     +' mA]' +
                'uptime['      + str(uptime)           +' s]'  )
  else:
    logger.warn('no yoctopuce module instanciated, module['              + str(result.module)        +']' +
                'or init not complete, no button reading pulsecounter1[' + str(result.pulsecounter1) +']' )  
#------------------------------------------------------------------------------#
# meteo_deamon: Instanciate button module and poll it for button data.         #
#               whenever change in a monitored button is detected determine    #
#               new menu point, if possilbe                                    #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 09.11.2013 Initial version                                       #
#------------------------------------------------------------------------------# 
def button_deamon(main_q, message_q, display_q, radio_q):
  shutdown = False
  message  = None   
  module   = init_module()
  #setup logging
  configuration.init_log(LOGGER)
  logger = logging.getLogger(LOGGER)
  #instanciate menu
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
        else:
          logger.warning('got unknown message')
    except queue.Empty as err:
      ###################
      #GET BUTTON STATUS#
      ###################
      module=do_buttons(module)
      if module.module != None:
        #button 6 pressed? this is our exit button which
        #sends shutdown to all threads
        if (module.pulsecounter6 >= (module.prevcounter6+2)) or (module.pulsecounter6 >= (module.prevcounter6+1) and module.buttonpressed6):
          #if the radio menu is active we use button 6 to toggle the radio on/off 
          #rather then for shutting down the info_display program.
          if myMenu.active().id == 'menu_radio':
            message = configuration.MESSAGE('BUTTON','RADIO','PLAY','TOGGLE',None)
            radio_q.put(message)                
          else:
            message = configuration.MESSAGE('BUTTON','MAIN','SHUTDOWN',None,None)
            main_q.put(message)            
        #button 1 pressed? this is the navigate LEFT button
        if (module.pulsecounter1 >= (module.prevcounter1+2)) or (module.pulsecounter1 >= (module.prevcounter1+1) and module.buttonpressed1):
          myMenu.left()
          #inform display module
          display_q.put(configuration.MESSAGE('BUTTON','DISPLAY','MENU', None, myMenu.active()))
          logger.info('left, activeMenu['+str(myMenu.active().id)+']')
        #button 2 pressed? this is the navigate RIGHT button
        elif (module.pulsecounter2 >= (module.prevcounter2+2)) or (module.pulsecounter2 >= (module.prevcounter2+1) and module.buttonpressed2):
          myMenu.right()
          #inform display module        
          display_q.put(configuration.MESSAGE('BUTTON','DISPLAY','MENU', None, myMenu.active()))
          logger.info('right, activeMenu['+str(myMenu.active().id)+']')
        #button 3 pressed? this is the navigate UP button
        elif (module.pulsecounter3 >= (module.prevcounter3+2)) or (module.pulsecounter3 >= (module.prevcounter3+1) and module.buttonpressed3):
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
        elif (module.pulsecounter4 >= (module.prevcounter4+2)) or (module.pulsecounter4 >= (module.prevcounter4+1) and module.buttonpressed4):
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
        elif (module.pulsecounter5>= (module.prevcounter5+2)) or (module.pulsecounter4 >= (module.prevcounter5+1) and module.buttonpressed5):
          myMenu.ok()
          logger.info('OK, activeMenu['+str(myMenu.active().id)+']') 
    except:
      logger.error('unexpected error ['+ str(traceback.format_exc()) +']')       

