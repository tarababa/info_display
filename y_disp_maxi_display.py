#!/usr/bin/python
# -*- coding: utf-8 -*-
################################################################################
# Application         : Yoctopuce display control
# File                : $HeadURL:  $
# Version             : $Revision: $
# Created by          : hta
# Created             : 01.10.2013
# Changed by          : $Author: b7tarah $
# File changed        : $Date: 2013-08-21 15:19:43 +0200 (Mi, 21 Aug 2013) $
# Environment         : Python 3.2.3 
# ##############################################################################
# Description : Main program controlling the information shown on the 
#               Yoctopuce maxi display.
#              
#              
#              
#
#
################################################################################


import os,sys,math,decimal
import logging,traceback
import queue, threading
import collections
import time
from time import localtime, strftime
import y_disp_global,y_meteo,y_disp_weather_yr,menu
# add ../YoctoLib.python.12553/Sources to the PYTHONPATH
sys.path.append(os.path.join("..","YoctoLib.python.12553","Sources"))
from yocto_api import *
from yocto_display import *


LOGGER         = 'MAXIDISPLAY'  #name of logger for the main module
data           = collections.namedtuple('data','sample')
display_module = collections.namedtuple('display_module', 'module module_name display current uptime')
#menu           = dict(menu=('METEO_T_GRAPH',menu_meteo_t_graph))



#------------------------------------------------------------------------------#
# init: Read config.ini, read startup arguments and setup logging              #
#       Content of config.ini and the startup arguments are made available     #
#       globally to all modules through y_disp_global                          #
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
# get_module: Get an instance of the yoctopuce disppaly module                 #
#                                                                              #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 09.11.2013 Initial version                                       #
#------------------------------------------------------------------------------#  
def get_module(name):
  logger = logging.getLogger(LOGGER)  
  errmsg=YRefParam()  
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
    #then just get the first display and determine
    #its module
    display = YDisplay.FirstDisplay()    
    if display is None :
      logger.error('No module connected')
    else:    
      module = display.get_module()
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
# display: Create instance of display module if necessary, instantiate the     #
#          sensors if necessary and return sensor readings                     #
#          For the display module we only return current and uptime!           #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 09.11.2013 Initial version                                       #
#------------------------------------------------------------------------------#   
def do_display(module):
  logger = logging.getLogger(LOGGER)
  #if we previously created a valid instance of the 
  #meteo module then we use that one.
  if  isinstance(module, display_module) and module.module != None:
    module_name        = module.module_name       
    ymodule            = module.module    
    display            = module.display
    current            = module.current          
    uptime             = module.uptime
  else: 
    module_name        = None
    ymodule            = None
    display            = None
    current            = None
    uptime             = None
  
  
  try:
    #display module ready to go?  
    #If yes then initialize individual sensors if necessary and obtain readings 
    if ymodule != None and ymodule.isOnline:
      #if display not created then create it
      if display == None:
        display  = YDisplay.FindDisplay(module_name+'.display')      
      current = ymodule.get_usbCurrent()
      uptime  = ymodule.get_upTime()/1000
      logger.debug('current['     + '%2.2f' % current     +' mA]' +
                   'uptime['      + str(uptime)           +' s]'  )
    else:
      #Yocto module has not been intialized or is not online
      #then go and try to intialize the module
      if y_disp_global.CONFIG.has_option('y_maxi_display','logical_name'):
        #if configured get a specific module
        ymodule = get_module(y_disp_global.CONFIG['y_maxi_display']['logical_name'])
      else:
        #not configured get any module
        ymodule = get_module(None)          
      if ymodule != None:
        # Yocto module has been initialized, then lets 
        # populate our data model for the display module
        module_name = ymodule.get_serialNumber()
        # we have an instance of the display module
        module = display_module(ymodule,module_name, display, current, uptime)
        # recursively collect "data" from the module i.e. current and uptime
        return do_display(module)
  except YAPI.YAPI_Exception as err:
    logger.error(str(err))
    ymodule = None
    module_name = None
  
  return display_module(ymodule,module_name, display, current, uptime)

#------------------------------------------------------------------------------#
# init_module: Returns an instance of the display_module                       #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 09.11.2013 Initial version                                       #
#------------------------------------------------------------------------------#
def init_module():
 return display_module(None,None,None,None,None) 

#------------------------------------------------------------------------------#
# getMinMaxAndSampleSize: Determines the number of samples and the value of    #
#                         the smallest and largest samples in the collection   #
# Parameter:  samples list of samples                                          #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 09.11.2013 Initial version                                       #
#------------------------------------------------------------------------------#
def getMinMaxAndSampleSize(samples):
  maxSample=0
  minSample=decimal.Decimal(samples[0].sample)
  sampleSize=0
  for sample in samples:
    if decimal.Decimal(sample.sample)>maxSample:
      maxSample=decimal.Decimal(sample.sample)
    if decimal.Decimal(sample.sample)<minSample:
      minSample=decimal.Decimal(sample.sample)    
    sampleSize+=1
  return minSample,maxSample,sampleSize 
#------------------------------------------------------------------------------#
# show_graph: show a graph                                                     #
#             This function shows a graph on the display at desired x and y -  #         
#             coordinates. The graph shows a configurable number of samples.   #
#             On the right hand side of the graph min and max values can be    #
#             shown.                                                           #
#             An automatic enlargement factor is calculated to use the full    #
#             available height of the graph which is also configurable         #
# Parameters: graph_x  x-coordinate to postion graph. 0 is the the left side   #
#                      of display. (usb connector is top-left corner)          #
#             graph_y y-coordinate of the graph, 0 is the bottom of the display#
#                     (usb-connector is top left corner)                       #
#             width   The width of the graph in pixels, this defines how many  #
#                     samples can be displayed                                 #
#             height  The height of the graph in pixels.                       #
#          max_resize In order to prevent the graph to look to spikey a maximum#
#                     resize factor can be provided
#             data    collection of data samples to be plotted. The data       #
#                     provided represents the y-coordinate, for each point     #
#                     on the graph the x-coordinate is increased by 1          #
#             display Yocto display to be used                                 #
#                                                                              #
#                                                                              #
                                                                               #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 09.11.2013 Initial version                                       #
#------------------------------------------------------------------------------#
def showGraph(graph_x,graph_y,width,height,maxResize,samples,display):  
  logger = logging.getLogger(LOGGER)
  graph         = []
  coordinates   = collections.namedtuple("coordinate","x y")
  x             = graph_x
  resizeFactor  = 1
  
  #validate width against desired x-coordinate of graph
  #if not compatible adjust width to maximum possible
  if width+graph_x>128:
    width = 128-x
  #validate height against desired y-coordinate of graph
  #if not compatible adjust to maximum possible
  if height+graph_y>64:
    height = 64-graph_y
  
  #going and determine minimum and maximum sample  
  #and the number of samples present
  minData,maxData,sampleSize = getMinMaxAndSampleSize(samples)
  logger.debug('minData['    + str(minData)    + ']' +
               'maxData['    + str(maxData)    + ']' + 
               'sampleSize[' + str(sampleSize) + ']' )

  #now determine a resize factor to ensure the graph can 
  #be displayed within the constraints of its maximum height
  if maxData-minData == 0:
    resizeFactor = math.floor(height/minData)
  elif resizeFactor*(maxData-minData) > height:
    resizeFactor = math.floor(height/(maxData-minData))
    logger.debug('shrinking, resizeFactor[' + str(resizeFactor) +']')
  #If the maximum y coordinate would be smaller than
  #half the maximum height of the graph we enlarge the 
  #graph
  elif resizeFactor*(maxData-minData) < height/2:
    resizeFactor = math.floor(height/(maxData-minData))
    logger.debug('enlarging, resizeFactor[' + str(resizeFactor) +']')

  # resizing factor larger than allowed
  # than limit to its maximum value
  if resizeFactor > maxResize:
    resizeFactor = maxResize

  #Our collection of samples may be larger than the amount of samples
  #we can display, which is defined by width. If this is the case
  #we plot the most recent samples and thus begin our iteration offset 
  #from zero
  if sampleSize >= width:
    i = -width
    j = 0
  else:
    i = 0
    j = sampleSize
 
  #prepare collection of x,y coordinates suitable for display
  while i < j:
    # Y-coordinate is calculated so that the maximum value is displayed at the top
    # of the graph defined by its maximum height. Furthermore the y-coordinate
    # calculated here takes into acount the desired position of the graph itself
    # as held in the graph_y coordinate parameter, note that graph_y=0 represents
    # the bottom of the display, however from a display perspective the bottom
    # of the display corresponds with y=63 (usb connector is in top left corner)
    y = 63 - graph_y - math.floor((resizeFactor*decimal.Decimal(samples[i].sample) - (resizeFactor*maxData - height))) 
    #it is still possible out of bounds y coordinate has been
    #calculated, in particular -1 since any value however small
    #below zero is converted to -1
    if y < 0:
      y=0
    graph.append(coordinates(x,y))
    x+=1
    i+=1

  #build graph but dont display it yet
  layer4=display.get_displayLayer(4)
  layer4.hide()
  layer4.clear()
  firstSample=True
  for coord in graph:
    #For first sample we draw a pixel, for all
    #consecutive samples we draw a line to the
    #x,y coordinates of that sample
    if firstSample: 
      layer4.moveTo(coord.x,coord.y)
      layer4.drawPixel(coord.x,coord.y)
      firstSample=False
    else:
      layer4.lineTo(coord.x,coord.y)
  
  #get layer 0, and use it do display the
  #graph we have prepared in layer 4
  layer0=display.get_displayLayer(0)
  display.swapLayerContent(4,0)

#------------------------------------------------------------------------------#
# showMinMax: show Minimum and maximum values on display                       #
#             A block of min/max is placed at the desired x/y coordinates      #         
#             showing the minimum and maximum values as passed to this function#
#             Typically used in conjunction with a grahp shown next to the min #
#             and max values                                                   #
# Parameters: text_x   x-coordinate to postion text. 0 is the the left side    #
#                      of display. (usb connector is top-left corner)          #
#             text_y  y-coordinate of the text, 0 is the bottom of the display #
#                     (usb-connector is top left corner)                       #
#             uom     unit of measure associated with min/max values           #
#             minData The minimum value to be shown                            #
#             maxData The maximum value to be shown                            #
#             display Yocto display to be used                                 #
#                                                                              #
#                                                                              #
                                                                               #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 28.01.2014 Initial version                                       #
#------------------------------------------------------------------------------#
def showMinMax(text_x,text_y,uom,minData,maxData,display):  
  logger = logging.getLogger(LOGGER)

  #build graph but dont display it yet
  layer4=display.get_displayLayer(4)
  layer4.hide()
  layer4.clear()
  
  #Min and max rates next to grap
  layer4.selectFont('Small.yfm')
  layer4.drawText(text_x,63-(text_y+36), YDisplayLayer.ALIGN.TOP_LEFT, 'Min')
  layer4.drawText(text_x,63-(text_y+27), YDisplayLayer.ALIGN.TOP_LEFT, minData + ' ' + uom)
  layer4.drawText(text_x,63-(text_y+18), YDisplayLayer.ALIGN.TOP_LEFT, 'Max')
  layer4.drawText(text_x,63-(text_y+9), YDisplayLayer.ALIGN.TOP_LEFT,  maxData + ' ' + uom)      
  
  #get layer 1, and use it do display the
  #graph we have prepared in layer 4
  layer1=display.get_displayLayer(1)
  display.swapLayerContent(4,1)
  
#------------------------------------------------------------------------------#
# showCurrent: show current value at desired x/y coordinates                   #
#              If provided two lines are shown the first line typically descri-#
#              what is displayed
# Parameters: text_x   x-coordinate to postion text. 0 is the the left side    #
#                      of display. (usb connector is top-left corner)          #
#             text_y  y-coordinate of the text, 0 is the bottom of the display #
#                     (usb-connector is top left corner)                       #
#             uom     unit of measure associated with currrent value           #
#             currVal current value                                            #
#             header  A header line, text, may be set to None                  #
#             display Yocto display to be used                                 #
#                                                                              #
#                                                                              #
                                                                               #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 28.01.2014 Initial version                                       #
#------------------------------------------------------------------------------#
def showCurrent(text_x,text_y,uom, currVal, header, display):  
  logger = logging.getLogger(LOGGER)

  #build graph but dont display it yet
  layer4=display.get_displayLayer(4)
  layer4.hide()
  layer4.clear()
  
  if header != None:
    layer4.selectFont('Small.yfm')
    layer4.drawText(text_x,63-(text_y+24), YDisplayLayer.ALIGN.TOP_LEFT, header)
    layer4.selectFont('Medium.yfm')
    layer4.drawText(text_x,63-(text_y+17), YDisplayLayer.ALIGN.TOP_LEFT, currVal + ' ' + uom)
  
  #get layer 2, and use it do display the
  #graph we have prepared in layer 4
  layer2=display.get_displayLayer(2)
  display.swapLayerContent(4,2)  

#------------------------------------------------------------------------------#
# showCurrent: show date and time                                              #
# Parameters: activeMenu menu.active_menu, in particular following attributes  #
#                        are relevant:                                         #                 
#               date_x   x-coordinate to postion date. 0 is the the left side  #
#                        of display. (usb connector is top-left corner)        #
#               date_y   y-coordinate of the date, 0 is the bottom of the      #
#                        display (usb-connector is top left corner)            #
#               time_x   x-coordinate to postion date. 0 is the the left side  #
#                        of display. (usb connector is top-left corner)        #
#               time_y   y-coordinate of the date, 0 is the bottom of the      #
#                        display (usb-connector is top left corner)            #
#             display Yocto display to be used                                 #
#                                                                              #
#                                                                              #
                                                                               #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 28.01.2014 Initial version                                       #
#------------------------------------------------------------------------------#
def showDateTime(activeMenu,display):  
  logger = logging.getLogger(LOGGER)

  #build graph but dont display it yet
  layer4=display.get_displayLayer(4)
  layer4.hide()
  layer4.clear()
  
  if activeMenu.date and activeMenu.date_x != None and activeMenu.date_y != None:
    layer4.selectFont('Small.yfm')
    #layer4.drawText(date_x,63-(date_y+16), YDisplayLayer.ALIGN.TOP_LEFT, strftime('%a, %d %b %Y', localtime())) #date
    layer4.drawText(activeMenu.date_x,63-activeMenu.date_y, YDisplayLayer.ALIGN.TOP_LEFT, strftime('%a, %d %b %Y', localtime())) #date
  if activeMenu.time and activeMenu.time_x != None and activeMenu.time_y != None:
    layer4.selectFont('Small.yfm')
    #layer4.drawText(time_x+17,63-(time_y+3), YDisplayLayer.ALIGN.TOP_LEFT, strftime('%X', localtime()))         #time
    layer4.drawText(activeMenu.time_x,63-activeMenu.time_y, YDisplayLayer.ALIGN.TOP_LEFT, strftime('%X', localtime()))         #time
  
  #get layer 3, and use it do display the
  #text we have prepared in layer 4
  layer3=display.get_displayLayer(3)
  display.swapLayerContent(4,3)  

#------------------------------------------------------------------------------#
# clearScreen: clears layers 1, 2 and 3                                        #
#                                                                              #
# Parameters: display   an instance of the yocto maxi display                  #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 10.02.2014 Initial version                                       #
#------------------------------------------------------------------------------# 
def clearScreen(display):
  for i in range (1,4):
     layer=display.get_displayLayer(i)
     layer.clear()    
#------------------------------------------------------------------------------#
# menu_meteo_t_graph: menu point, show meteo data temperature graph            #
#                                                                              #
# Parameters: meteoData is either a list of y_meteo.meteo_module or a single   #
#                       y_meteo.meteo_module record. In the latter case only   #
#                       the current value is update in the former case the com-#
#                       plete screen is redrawn                                #
#             action    REFRESH to only update current value                   #
#                       GRAPH   to replot graph                                #
#             display   an instance of the yocto maxi display                  #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 28.01.2014 Initial version                                       #
#------------------------------------------------------------------------------# 
def menu_meteo_t_graph(meteoData,action,cls,display):
  samples=[]
  if action=='REFRESH': # only refresh current value
    showCurrent(0,39,'°C','%2.2f'%meteoData.temperature,'Temperature' ,display)
  else:
    #clear layers 1,2 and 3
    if cls:
      clearScreen(display)
      cls==False    
    for sample in meteoData:
      samples.append(data(sample.temperature))
    showGraph(0,0,92, 40, 40, samples, display)
    minData, maxData, sampleSize = getMinMaxAndSampleSize(samples)
    showMinMax(93,0,'°C','%2.2f'%minData,'%2.2f'%maxData ,display)
    showCurrent(0,39,'°C','%2.2f'%samples[-1].sample,'Temperature' ,display)
  
#------------------------------------------------------------------------------#
# menu_meteo_h_graph: menu point, show meteo data humidity graph               #
#                                                                              #
# Parameters: meteoData is either a list of y_meteo.meteo_module or a single   #
#                       y_meteo.current_values record. In the latter case only #
#                       the current value is update in the former case the com-#
#                       plete screen is redrawn                                #
#             action    REFRESH to only update current value                   #
#                       GRAPH   to replot graph                                #
#             display   an instance of the yocto maxi display                  #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 28.01.2014 Initial version                                       #
#------------------------------------------------------------------------------# 
def menu_meteo_h_graph(meteoData,action,cls,display):
  samples=[]
  if action=='REFRESH': # only refresh current value
    showCurrent(0,39,'%','%2.0f'%meteoData.humidity,'Humidity' ,display)
  else:
    #clear layers 1,2 and 3
    if cls:
      clearScreen(display)
      cls==False    
    for sample in meteoData:
      samples.append(data(sample.humidity))
    showGraph(0,0,92, 40, 5, samples, display)
    minData, maxData, sampleSize = getMinMaxAndSampleSize(samples)
    showMinMax(93,0,'%','%2.0f'%minData,'%2.2f'%maxData ,display)
    showCurrent(0,39,'%','%2.0f'%samples[-1].sample,'Humidity' ,display)
#------------------------------------------------------------------------------#
# menu_meteo_p_graph: menu point, show meteo data barometric pressure graph    #
#                                                                              #
# Parameters: meteoData is either a list of y_meteo.meteo_module or a single   #
#                       y_meteo.current_values record. In the latter case only #
#                       the current value is update in the former case the com-#
#                       plete screen is redrawn                                #
#             action    REFRESH to only update current value                   #
#                       GRAPH   to replot graph                                #
#             display   an instance of the yocto maxi display                  #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 28.01.2014 Initial version                                       #
#------------------------------------------------------------------------------# 
def menu_meteo_p_graph(meteoData,action,cls,display):
  samples=[]
  if action=='REFRESH': # only refresh current value
    showCurrent(0,39,'mB','%4.0f'%meteoData.pressure,'Pressure' ,display)
  else:
    #clear layers 1,2 and 3
    if cls:
      clearScreen(display)
      cls==False    
    for sample in meteoData:
      samples.append(data(sample.pressure))
    showGraph(0,0,92, 40, 3, samples, display)
    minData, maxData, sampleSize = getMinMaxAndSampleSize(samples)
    showMinMax(93,0,'mB','%4.0f'%minData,'%4.0f'%maxData ,display)
    showCurrent(0,39,'mB','%4.0f'%samples[-1].sample,'Pressure' ,display)
#------------------------------------------------------------------------------#
# menu_meteo_summary: menu point, show meteo data summary, shows all available #
#                     (meteo) sensor data. When this screen is started the data#
#                     shown is from the array which is used to plot meteo      #
#                     graphs, which means data shown initial may be nearly 16  #
#                     minutes old. However as we also request a refresh of of  #
#                     meteo sensor information the shown data will be updated  #
#                     very quickly.                                            #
#                                                                              #
# Parameters: meteoData is a single y_meteo.meteo_module record                #
#             action    GRAPH or REFRESH
#             display   an instance of the yocto maxi display                  #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 28.01.2014 Initial version                                       #
#------------------------------------------------------------------------------# 
def menu_meteo_summary(meteoData,action,cls,display):
  if action=='GRAPH':
    displayData=meteoData[-1]
  else:
    displayData=meteoData
  x=0
  y=5
  #build summary but dont display it yet
  layer4=display.get_displayLayer(4)
  layer4.hide()
  layer4.clear()
  
  layer4.selectFont('Small.yfm')
  
  layer4.drawText(x,y+8, YDisplayLayer.ALIGN.TOP_LEFT, 'Temp.')
  layer4.drawText(x+32,y+8, YDisplayLayer.ALIGN.TOP_LEFT, '%2.2f'%displayData.temperature + ' °C' )
  layer4.drawText(x,y+17, YDisplayLayer.ALIGN.TOP_LEFT, 'Humidity' )
  layer4.drawText(x+32,y+17, YDisplayLayer.ALIGN.TOP_LEFT, '%2.0f'%displayData.humidity + ' %')
  layer4.drawText(x,y+26, YDisplayLayer.ALIGN.TOP_LEFT, 'Pressure')
  layer4.drawText(x+32,y+26, YDisplayLayer.ALIGN.TOP_LEFT, '%4.0f'%displayData.pressure+ ' mBar' )
  
  #clear layers 1,2 and 3
  if cls:
    clearScreen(display)
    cls==False
    
  #get layer 0, and use it do display the
  #summary prepared on layer4
  
  layer0=display.get_displayLayer(0)
  display.swapLayerContent(4,0)    

#------------------------------------------------------------------------------#
# menu_show_characters_small: for test purposes, shows alphabet in small font  #
#                                                                              #
# Parameters: display   an instance of the yocto maxi display                  #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 28.01.2014 Initial version                                       #
#------------------------------------------------------------------------------# 
def menu_show_characters_small(navigate,menuIndex,pageIndex,cls,display):
  x=0
  y=0
  j=0
  #build summary but dont display it yet
  layer4=display.get_displayLayer(4)
  layer4.hide()
  layer4.clear()
  layer4.selectFont('Small.yfm')
  
  #printable characters
  pc=list(range(32,127))
  pc.extend(range(160,265))

  for i in pc:
    if x+char_pixel_width(chr(i),'small') >= 128:
      #next line
      x=0
      y=y+8
    layer4.drawText(x,y, YDisplayLayer.ALIGN.TOP_LEFT, chr(i))
    x=x+char_pixel_width(chr(i),'small')
  
      
  #clear layers 1,2 and 3
  if cls:
    clearScreen(display)
    cls==False
    
  #get layer 0, and use it do display the
  #summary prepared on layer4
  
  layer0=display.get_displayLayer(0)
  display.swapLayerContent(4,0)    
  
  return menuIndex,pageIndex
 
#------------------------------------------------------------------------------#
# multipageNavigator: Navigate through screens spanning multiple pages and     #
#                                                                              #
# Parameters: pages     list of all pages associated with current menu item    #
#             navigate   Navigation UP, DOWN, MENU_UP, MENU_DOWN               #
#             pageIndex current page index                                     #
#                                                                              #
# returnvalue pageIndex new pageindex as per navigate                          #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 28.01.2014 Initial version                                       #
#------------------------------------------------------------------------------# 
def multipageNavigator(pages,navigate,menuIndex,pageIndex):
  logger = logging.getLogger(LOGGER)

  if navigate == None and menuIndex == None and pageIndex == None:
    #intial call, show first page
    menuIndex=0
    pageIndex=0
  elif navigate == 'UP':
    # at top page then wrap around to bottom page
    if pageIndex == 0:
      pageIndex = len(pages)-1
    else:
      pageIndex = pageIndex - 1
  elif navigate == 'DOWN':
    # at bottom page then wrap around to top page
    if pageIndex == len(pages)-1:
      pageIndex = 0
    else:
      pageIndex = pageIndex + 1
  elif navigate in ('MENU_UP','MENU_DOWN'):
    None
  else:
    logger.error('unexpected value for page[' + str(navigate) + ']') 
  return menuIndex,pageIndex
#------------------------------------------------------------------------------#
# multimenuNavigator: Navigate through dynamically created menu items          #
# Parameters: menuItems list containing all menuitems containing a list with   #
#                       all page.                                              #
#             navigate   MENU_UP, MENU_DOWN                                    #
#             menuIndex current menu index                                     #
#                                                                              #
# returnvalue menuIndex new menuindex as per navigate                          #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 28.01.2014 Initial version                                       #
#------------------------------------------------------------------------------# 
def multimenuNavigator(menus,navigate,menuIndex,pageIndex):
  logger = logging.getLogger(LOGGER)

  if navigate == None and menuIndex == None and pageIndex == None:
    #intial call, show first page
    menuIndex=0
    pageIndex=0
  elif navigate == 'MENU_DOWN':
    # at bottom page then wrap around to top page
    if menuIndex == len(menus)-1:
      menuIndex = 0
    else:
      menuIndex = menuIndex + 1
  elif navigate == 'MENU_UP':
    # at top page then wrap around to bottom page
    if menuIndex == 0:
      menuIndex = len(menus)-1
    else:
      menuIndex = menuIndex - 1
  elif navigate in ('UP','DOWN'):
    None
  else:
    logger.error('unexpected value for page[' + str(navigate) + ']') 
  return menuIndex,pageIndex
#------------------------------------------------------------------------------#
# menu_show_characters_small: for test purposes, shows alphabet in small font  #
#                                                                              #
# Parameters: display   an instance of the yocto maxi display                  #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 28.01.2014 Initial version                                       #
#------------------------------------------------------------------------------# 
def menu_show_characters_medium(navigate,menuIndex,pageIndex,cls,display):
  logger = logging.getLogger(LOGGER)
  x=0
  y=0
  j=0
  #build summary but dont display it yet
  layer4=display.get_displayLayer(4)
  layer4.hide()
  layer4.clear()
  layer4.selectFont('Medium.yfm')
  
  #printable characters
  pc=list(range(32,127))
  pc.extend(range(160,265))
  
  pages=[]
  page =[]
  
  #build the pages in memory
  for i in pc:
    if x+char_pixel_width(chr(i),'medium') >= 128:
      #next line
      x=0
      y=y+16
      if y>48: 
        #next page
        pages.append(page)
        page=[]
        y=0
    page.append((x,y,chr(i)))
    x=x+char_pixel_width(chr(i),'medium')
  if len(page) != 0:
    #last page
    pages.append(page)
    page=[]
    y=0    
  
  #decide which page to show  
  menuIndex,pageIndex = multipageNavigator(pages,navigate,menuIndex,pageIndex)  
     
  for page in pages[pageIndex]: 
    layer4.drawText(page[0],page[1], YDisplayLayer.ALIGN.TOP_LEFT, page[2])
      
  #clear layers 1,2 and 3
  if cls:
    clearScreen(display)
    cls==False
    
  #get layer 0, and use it do display the
  #summary prepared on layer4
  
  layer0=display.get_displayLayer(0)
  display.swapLayerContent(4,0)
  
  return menuIndex,pageIndex
#------------------------------------------------------------------------------#
# menu_show_characters_small: for test purposes, shows alphabet in small font  #
#                                                                              #
# Parameters: display   an instance of the yocto maxi display                  #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 28.01.2014 Initial version                                       #
#------------------------------------------------------------------------------# 
def menu_show_characters_8x8(navigate,menuIndex,pageIndex,cls,display):
  logger = logging.getLogger(LOGGER)
  x=0
  y=0
  j=0

  #printable characters
  pc=list(range(32,127))
  pc.extend(range(160,265))
  
  pages=[]
  page =[]
  
  #build the pages in memory
  for i in pc:
    if x+char_pixel_width(chr(i),'8x8') >= 128:
      #next line
      x=0
      y=y+8
      if y>56: 
        #next page
        pages.append(page)
        page=[]
        y=0
    page.append((x,y,chr(i)))
    x=x+char_pixel_width(chr(i),'8x8')
  if len(page) != 0:
    #last page
    pages.append(page)
    page=[]
    y=0    
  
  #decide which page to show, note menuIndex is not used here! menuIndex is
  #used for dynamically created menus such as weather forcast per location
  #and exchange rates per currency.
  menuIndex,pageIndex = multipageNavigator(pages,navigate,menuIndex,pageIndex)  
     
  #prepare information but dont display it yet
  layer4=display.get_displayLayer(4)
  layer4.hide()
  layer4.clear()
  layer4.selectFont('8x8.yfm')
  
  for page in pages[pageIndex]: 
    layer4.drawText(page[0],page[1], YDisplayLayer.ALIGN.TOP_LEFT, page[2])
      
  #clear layers 1,2 and 3
  if cls:
    clearScreen(display)
    cls==False
    
  #get layer 0, and use it do display the
  #summary prepared on layer4
  
  layer0=display.get_displayLayer(0)
  display.swapLayerContent(4,0)
  
  return menuIndex,pageIndex
  
#------------------------------------------------------------------------------#
# char_pixel_width: returns the width of a string in pixels                    #
#                                                                              #
# Parameters: font: Small, Medium, Large                                       #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 28.01.2014 Initial version                                       #
#------------------------------------------------------------------------------# 
def char_pixel_width(string, font='Small'):
  logger = logging.getLogger(LOGGER)
  
  width=0
  if font.lower() == 'small':
    one_pixel  =list(' !\'.1Ii:l|¡¦')
    two_pixel  =list('(),;[]`jr²³´¹')
    three_pixel=list('"$%*+-/023456789<=>?ABCDEFGHJKLOPQRSTUVXUZ\^abcdefghknopqstuvxyz{}¢¥§¨°±µº¿×÷')
    four_pixel =list('&@N£¤¶ø')
    five_pixel =list('MWmw~«»')
    six_pixel  =list('©¼½¾')
    seven_pixel=[]
    eight_pixel=[]
    nine_pixel =[]
    ten_pixel  =[]
    eleven_pixel=[]
    twelve_pixel=[]
    thirteen_pixel=[]
    fourteen_pixel=[]
    fifteen_pixel=[]
    undef_width=4
  elif font.lower() == 'medium':
    one_pixel   =list(' ¡¦i')
    two_pixel   =list('!\'|Ijl:')
    three_pixel =list('-,.;]/`´°¹')
    four_pixel  =list('[()\º³trf')
    five_pixel  =list('"*{}²')
    six_pixel   =list('chnxy')
    seven_pixel =list('+01256789<=>?^Lbdgkopqsuvz§¨µ¿×÷~N£¤¶ø')
    eight_pixel =list('$34Y«»¢¥ae±')
    nine_pixel  =list('&#ABEFHJKPRSTXZ')
    ten_pixel   =list('&CDGOQUw')
    eleven_pixel=list('¼½¾VMm')
    twelve_pixel=list('©%')
    thirteen_pixel=[]
    fourteen_pixel=list('W®')
    fifteen_pixel=list('@')
    undef_width=8
  elif font.lower() == '8x8':
    one_pixel   =list(' ¡¦')
    two_pixel   =list(':!\'')
    three_pixel =list('{ciks|')
    four_pixel  =list('(+;[]`1lHIjKOrht²³´¹')
    five_pixel  =list(',.)"$@-023456789<=>?ABCDEFGJNPQRSTUXYZ\befnopquxyz}¢¥§¨°±µº¿×÷')
    six_pixel  =list('%&MWLVadvg£¤¶ø/^')
    seven_pixel   =list('*mw~«»')
    eight_pixel =list('©¼½¾')
    nine_pixel  =[]
    ten_pixel   =[]
    eleven_pixel=[]
    twelve_pixel=[]
    thirteen_pixel=[]
    fourteen_pixel=[]
    fifteen_pixel =[]
    undef_width=7
    
  for c in string:
    if c in one_pixel:
      width=width+2;
    elif c in two_pixel:
      width=width+3;
    elif c in three_pixel:
      width=width+4;
    elif c in four_pixel:
      width=width+5;
    elif c in five_pixel:
      width=width+6;
    elif c in six_pixel:
      width=width+7;
    elif c in seven_pixel:
      width=width+8;
    elif c in eight_pixel:
      width=width+9;
    elif c in nine_pixel:
      width=width+10;
    elif c in ten_pixel:
      width=width+11;      
    elif c in eleven_pixel:
      width=width+12;  
    elif c in twelve_pixel:
      width=width+13;  
    elif c in thirteen_pixel:
      width=width+14;  
    elif c in fourteen_pixel:
      width=width+15;  
    elif c in fifteen_pixel:
      width=width+16;  
    else:
      width=width+undef_width
      logger.warning('pixel width not defined for character['+str(c)+']')
  return width
#------------------------------------------------------------------------------#
# menu_weather_forecast: menu point, show weatherforcast                       #
#                                                                              #
# Parameters: forecasts  weather forecasts                                     #
#             navigate   Navigation UP, DOWN, MENU_UP, MENU_DOWN               #
#             pageIndex current page index                                     #
#             menuIndex current menu index                                     #
#             cls       When true screen is cleared before showing information #
#             display   an instance of the yocto maxi display                  #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 28.01.2014 Initial version                                       #
#------------------------------------------------------------------------------# 
def menu_weather_forecast(forecasts,navigate,menuIndex,pageIndex,cls,display):
  logger = logging.getLogger(LOGGER)
  
  #get the correct menuIndex and pageIndex page from the forecasts
  menuIndex,pageIndex = multimenuNavigator(forecasts,navigate,menuIndex,pageIndex)
  menuIndex,pageIndex = multipageNavigator(forecasts[menuIndex].forecast_items,navigate,menuIndex,pageIndex)
    
  #  forecast.forecast_items
  logger.debug('pageIndex['+str(pageIndex)+']')
  logger.debug('menuIndex['+str(menuIndex)+']')
  item = forecasts[menuIndex].forecast_items[pageIndex]
  
  #prepare weather forecast to display 
  #but do not show it
  layer4=display.get_displayLayer(4)
  layer4.hide()
  layer4.clear()
  
  #first line
  x=0
  y=0
  layer4.selectFont('Medium.yfm')  
  for c in forecasts[menuIndex].location:
    layer4.drawText(x,y, YDisplayLayer.ALIGN.TOP_LEFT, c)
    x=x+char_pixel_width(c,'Medium')
  layer4.selectFont('Small.yfm')  
  x=x+(128-x)/2
  layer4.drawText(x,y, YDisplayLayer.ALIGN.TOP_CENTER, item.datetime.dayname)
  y=y+8
  layer4.drawText(x,y, YDisplayLayer.ALIGN.TOP_CENTER, item.datetime.day+' '+item.datetime.monthname)
  
  #next line
  x=10
  y=y+10

  layer4.selectFont('8x8.yfm')  
  for c in 'From ':
    layer4.drawText(x,y, YDisplayLayer.ALIGN.TOP_LEFT, c)
    x=x+char_pixel_width(c,'8x8')
  for c in item.precipitation.time_from+':  00':
    layer4.drawText(x,y, YDisplayLayer.ALIGN.TOP_LEFT, c)
    x=x+char_pixel_width(c,'8x8')
  for c in ' to ':
    layer4.drawText(x,y, YDisplayLayer.ALIGN.TOP_LEFT, c)
    x=x+char_pixel_width(c,'8x8')
  for c in  item.precipitation.time_to+':  00':
    layer4.drawText(x,y, YDisplayLayer.ALIGN.TOP_LEFT, c)
    x=x+char_pixel_width(c,'8x8')

  #next line
  x=0
  y=y+8
  layer4.selectFont('Medium.yfm')  
  for c in item.temperature.temperature:
    layer4.drawText(x,y, YDisplayLayer.ALIGN.TOP_LEFT, c)
    x=x+char_pixel_width(c,'Medium')
  for c in item.temperature.unit:
    layer4.drawText(x,y, YDisplayLayer.ALIGN.TOP_LEFT, c)
    x=x+char_pixel_width(c,'Medium')
  layer4.selectFont('Small.yfm')
  if 128-x < char_pixel_width(item.wind.strength+item.wind.unit+' '+item.wind.direction):
    x=x+(128-x)/2  
    layer4.drawText(x,y, YDisplayLayer.ALIGN.TOP_CENTER, item.wind.description + ',' + item.wind.strength+item.wind.unit)
    y=y+8
    layer4.drawText(x,y, YDisplayLayer.ALIGN.TOP_CENTER,  item.wind.direction)
  else:
    x=x+(128-x)/2  
    layer4.drawText(x,y, YDisplayLayer.ALIGN.TOP_CENTER, item.wind.description)
    y=y+8
    layer4.drawText(x,y, YDisplayLayer.ALIGN.TOP_CENTER,  item.wind.strength+item.wind.unit + ' ' + item.wind.direction)    

  #next line
  x=64
  y=y+9
  layer4.selectFont('8x8.yfm')  
  layer4.drawText(x,y, YDisplayLayer.ALIGN.TOP_CENTER, item.cloudcover.clouds)

  #next line
  x=0
  y=y+9
  x=char_pixel_width('Precipitation: ')+char_pixel_width(item.precipitation.precipitation,'8x8')+char_pixel_width(' '+item.precipitation.unit,'8x8')
  x=(128-x)/2
  layer4.selectFont('Small.yfm')  
  layer4.drawText(x,y, YDisplayLayer.ALIGN.TOP_LEFT, 'Precipitation: ')
  x=x+char_pixel_width('Precipitation: ')
  layer4.selectFont('8x8.yfm')  
  if item.precipitation.precipitation.find('-')!=-1:
    #percipitation range then display hyphen using Small font 
    #this is purely cosmetic.
    precipitation=item.precipitation.precipitation.split('-')
    for c in precipitation[0]: 
      layer4.drawText(x,y, YDisplayLayer.ALIGN.TOP_LEFT, c)
      x=x+char_pixel_width(c,'8x8')
    layer4.selectFont('Small.yfm')  
    layer4.drawText(x+1,y, YDisplayLayer.ALIGN.TOP_LEFT, '-')
    x=x+char_pixel_width('-','Small')
    layer4.selectFont('8x8.yfm')  
    for c in precipitation[1]:
      layer4.drawText(x,y, YDisplayLayer.ALIGN.TOP_LEFT, c)
      x=x+char_pixel_width(c,'8x8')
  else:      
    for c in item.precipitation.precipitation:
      layer4.drawText(x,y, YDisplayLayer.ALIGN.TOP_LEFT, c)
      x=x+char_pixel_width(c,'8x8')
  for c in ' '+item.precipitation.unit:
    layer4.drawText(x,y, YDisplayLayer.ALIGN.TOP_LEFT, c)
    x=x+char_pixel_width(c,'8x8')
  
  #clear layers 1,2 and 3
  if cls:
    clearScreen(display)
    cls==False
    
  #get layer 0, and use it do display the
  #summary prepared on layer4
  
  layer0=display.get_displayLayer(0)
  display.swapLayerContent(4,0)    
  
  #return the current page index
  return menuIndex,pageIndex
  
#------------------------------------------------------------------------------#
# display_deamon: Instanciates a display module which is responsible for show- #
#                 desired information.                                         #
#                 Some logic is implemented here to aggrate (meteo) information#
#                 in order to plot graphs...                                   #
#                                                                              #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 09.11.2013 Initial version                                       #
#------------------------------------------------------------------------------# 
def display_deamon(main_q, meteo_q, message_q):
  shutdown = False
  message  = None
  module   = init_module()
  #setup logging
  y_disp_global.init_log(LOGGER)
  logger = logging.getLogger(LOGGER)
  #init local variables
  cleanScreen = False
  activeMenu = menu.active_menu(None,None,None,None,None,None,None,None,None,None)   
  pageIndex  = None
  menuIndex  = None
  displayData= None
  meteoData  = []
  forecasts  = None
  
  #initialize module
  while module.module == None:
    module = do_display(init_module())
    if module.module == None:
      time.sleep(1)
      
  #listen for message to execute.
  while not shutdown:
    try:
      #read message queue
      message=message_q.get(timeout=1)
      if module.module == None:
        module=do_display(init_module())
      else:
        #Received a message, type and subtype define 
        #what is to be done with the messasge
        if isinstance(message, y_disp_global.MESSAGE):
          logger.debug('message.sender['   + str(message.sender)  + ']')
          logger.debug('message.receiver[' + str(message.receiver)+ ']')
          logger.debug('message.type['     + str(message.type)    + ']')
          logger.debug('message.subtype['  + str(message.subtype) + ']')
          ########################################
          #MESSAGES FROM (YOCTOPUCE) METEO MODULE#
          ########################################
          if message.type == 'METEO_DATA': 
            if message.subtype == 'GRAPH':
              #Append meteo data to list so that we have
              #historical data to show a graph
              meteoData.append(message.content)
              displayData = meteoData
            else: #REFRESH
              displayData = message.content
            ##############################################  
            #Update active  meteo data information screen# 
            ##############################################
            if activeMenu.id in ('menu_meteo_t_graph','menu_meteo_p_graph','menu_meteo_h_graph','menu_meteo_summary'):
              getattr(sys.modules[__name__],activeMenu.id)(displayData,message.subtype,False,module.display)

          #######################################
          #MESSAGES FROM WEATHER FORECAST MODULE#
          #######################################
          elif message.type == 'WEATHER_FORECAST':
            forecasts=message.content
            if activeMenu.id=='menu_weather_forecast':
              menu_weather_forecast(forecasts,None,menuIndex,pageIndex,False,module.display)

          #########################################
          #MESSAGES FROM (YOCTOPUCE) BUTTON MODULE#
          #########################################
          elif message.type == 'MENU' and message.subtype == None:
            
            if activeMenu.id != message.content.id:
              #new menu then screen must be cleared..
              clearScreen=True
              #for multimenu menus, ensure upon initial
              #call menu with index zero is shown
              menuIndex=None              
              #for multipage menus, ensure upon initial
              #call page with index zero is shown.
              pageIndex=None
            activeMenu=message.content 
            ###########################
            #METEO INFORMATION SCREENS#
            ###########################
            if activeMenu.id in ('menu_meteo_t_graph','menu_meteo_p_graph','menu_meteo_h_graph','menu_meteo_summary'):
              getattr(sys.modules[__name__],activeMenu.id)(meteoData,'GRAPH',clearScreen,module.display)
              if activeMenu.id == 'menu_meteo_summary':
                #request refresh of sensor readings
                meteo_q.put(y_disp_global.MESSAGE('DISPLAY','METEO','REFRESH',None,None))
            ##########################
            #WEATHER FORECAST SCREENS#
            ##########################            
            elif activeMenu.id == 'menu_weather_forecast':
              menuIndex,pageIndex=menu_weather_forecast(forecasts,activeMenu.navigate,menuIndex,pageIndex,clearScreen,module.display)
            ###################
            #TEST SCREEN FONTS#
            ###################
            elif activeMenu.id in('menu_show_characters_small','menu_show_characters_medium','menu_show_characters_8x8'):    
              #menu_show_characters_small(clearScreen,module.display)
              menuIndex,pageIndex=getattr(sys.modules[__name__],activeMenu.id)(activeMenu.navigate,menuIndex,pageIndex,clearScreen,module.display)              
            else:
              logger.warning('not implemented action['+str(message.content.id )+']')
          #########################################
          #MESSAGES FROM (YOCTOPUCE) BUTTON MODULE#
          #########################################
          elif message.type == 'MENU' and message.subtype == 'RESET_PAGEINDEX':
            if pageIndex != None:
              pageIndex = 0
              
          ##################    
          #SHUTDOWN MESSAGE#
          ##################
          elif message.type == 'SHUTDOWN':
            shutdown=True
            logger.warning('got shutdown request, SHUTTING DOWN NOW')
          else:
            ######################    
            #UNKNOWN MESSAGE TYPE#
            ######################    
            logger.error('got unknown message from sender[' + str(message.sender)   + '] ' +
                         'receiver['                        + str(message.receiver) + '] ' +
                         'type['                            + str(message.type)     + '] ' +
                         'subtype['                         + str(message.subtype)  + ']');
              
        #make sure we dont have more than 128 samples of meteo data
        try:
          meteoData=meteoData[-128:]
        except Exception as err:
          logger.error(str(err))
          
        #show time and/or date?
        if activeMenu.date or activeMenu.time and module.module !=None:
          showDateTime(activeMenu,module.display)
        
    except queue.Empty as err:
      if module.module != None:
        if activeMenu != None:
          showDateTime(activeMenu,module.display)
    except YAPI.YAPI_Exception as err:
      logger.error(str(err))
      module.module = None
      module.module_name = None           
    except:
      logger.error('unexpected error ['+ str(traceback.format_exc()) +']')        
        
  logger.debug('done')    
      
      
     
#------------------------------------------------------------------------------#
# testData: Returns a list of test data consisting of 128 samples              #
#                                                                              #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 27.01.2014 Initial version                                       #
#------------------------------------------------------------------------------#     
def testData():
  testData=[]
  for i in range (0,128):
    testData.append(data(math.sin(i/5)))
  return testData
#------------------------------------------------------------------------------#
# main:                                                                        #
#                                                                              #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 09.11.2013 Initial version                                       #
#------------------------------------------------------------------------------#
def main():
  #get commandline arguments, config.ini and setup logging
  init();
  logger = logging.getLogger(LOGGER)  
  logger.debug('start')
  
  #go try connect to module  
  module=do_display(init_module())
  showGraph(0,0,80, 32, 9999, testData(), module.display)
  minData, maxData, sampleSize = getMinMaxAndSampleSize(testData())
  showMinMax(80,0,'°C','%2.0f'%minData,'%2.0f'%maxData ,module.display)  
  showCurrent(0,39,'°C','%2.2f'%testData()[-15].sample,'Temperature' ,module.display)
  showDateTime(70,47,module.display)
  
if __name__ == '__main__':
  
  main()
