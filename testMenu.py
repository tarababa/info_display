#!/usr/bin/python
# -*- coding: utf-8 -*-
################################################################################
# Application         : Yoctopuce information display
# File                : $HeadURL:  $
# Version             : $Revision: $
# Created by          : hta
# Created             : 01.10.2013
# Changed by          : $Author: b7tarah $
# File changed        : $Date: 2013-08-21 15:19:43 +0200 (Mi, 21 Aug 2013) $
# Environment         : Python 3.3.3 
# ##############################################################################
# Description: Tests Menu class
#              
#
################################################################################


import os,sys
import logging, logging.handlers
import y_disp_global
import menu


LOGGER = 'MENU'     #name of logger

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
  y_disp_global.general_configuration();
  y_disp_global.logging_configuration();
  y_disp_global.init_args();
  y_disp_global.init_log(LOGGER); 
  
def main():
  #Initialize
  init()
  logger = logging.getLogger(LOGGER)  
  myMenu = menu.Menu()
  c=None
  while True:
    c = input('Enter a char: ')
    if len(c)==1:
      if c=='1':
        myMenu.up()
        logger.debug('menu.activeMenu['+str(myMenu.active())+']')   
      elif c=='2':
        myMenu.down()
        logger.debug('menu.activeMenu['+str(myMenu.active())+']')   
      elif c=='3':
        myMenu.left()
        logger.debug('menu.activeMenu['+str(myMenu.active())+']')   
      elif c=='4':
        myMenu.right()
        logger.debug('menu.activeMenu['+str(myMenu.active())+']')   
        logger.debug('menu.activeMenu['+str(myMenu.active().id)+']')   
      elif c=='9':
        exit('0')
if __name__ == '__main__':
  main()  
