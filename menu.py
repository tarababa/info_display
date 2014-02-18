################################################################################
# Application         : Information display
# File                : $HeadURL:  $
# Version             : $Revision: $
# Created by          : hta
# Created             : 26.01.2014
# Changed by          : $Author: b7tarah $
# File changed        : $Date: 2013-08-21 15:19:43 +0200 (Mi, 21 Aug 2013) $
# Environment         : Python 3.3.3 
# ##############################################################################
# Description : A menu class for navigating through the various screens 
#               which are implemented in the information display project
################################################################################
import os,sys,collections
import logging

active_menu   = collections.namedtuple('menu', 'id multimenu multipage navigate date date_x date_y time time_x time_y')
#------------------------------------------------------------------------------#
# Memnu: Menu class                                                            #
#                                                                              #
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 29.01.2014 Initial version                                       #
#------------------------------------------------------------------------------#
class Menu():
 
      
  def __init__(self):
    #define the structure of the menu. This structure defines which menu is 
    #shown next when the up, down, left or right button is pressed.
    self.menu = [ [dict(id='menu_startup', multimenu=False, multipage=False, navigate=None, date=False, date_x=None, date_y=None, time=False, time_x=None, time_y=None)],
                  [dict(id='menu_meteo_t_graph', multimenu=False, multipage=False, navigate=None, date=True, date_x=70, date_y=63, time=True, time_x=87, time_y=50),
                   dict(id='menu_meteo_h_graph', multimenu=False, multipage=False, navigate=None, date=True, date_x=70, date_y=63, time=True, time_x=87, time_y=50),
                   dict(id='menu_meteo_p_graph', multimenu=False, multipage=False, navigate=None, date=True, date_x=70, date_y=63, time=True, time_x=87, time_y=50),
                   dict(id='menu_meteo_summary', multimenu=False, multipage=False, navigate=None, date=True, date_x=0, date_y=63, time=True, time_x=95, time_y=63)],
                  [dict(id='menu_weather_forecast', multimenu=True, multipage=True, navigate=None, date=False, date_x=None, date_y=None, time=False, time_x=None, time_y=None)], 
                  [dict(id='menu_show_characters_small',  multimenu=False, multipage=False, navigate=None, date=False, date_x=None, date_y=None, time=False, time_x=None, time_y=None), 
                   dict(id='menu_show_characters_8x8',    multimenu=False, multipage=True, navigate=None, date=False, date_x=None, date_y=None, time=False, time_x=None, time_y=None),
                   dict(id='menu_show_characters_medium', multimenu=False, multipage=True, navigate=None, date=False, date_x=None, date_y=None, time=False, time_x=None, time_y=None)] 
               ]
    #upon start the startup menu is active
    self.active_menu_index=(0,0)                 
    self.setActiveMenu()
    self.ok_activated=False #ok button not activated
  
  def setActiveMenu(self):
      self.active_menu = active_menu(self.menu[self.active_menu_index[0]][self.active_menu_index[1]].get('id'),
                                     self.menu[self.active_menu_index[0]][self.active_menu_index[1]].get('multimenu'),
                                     self.menu[self.active_menu_index[0]][self.active_menu_index[1]].get('multipage'),
                                     self.menu[self.active_menu_index[0]][self.active_menu_index[1]].get('navigate'),
                                     self.menu[self.active_menu_index[0]][self.active_menu_index[1]].get('date'),
                                     self.menu[self.active_menu_index[0]][self.active_menu_index[1]].get('date_x'),
                                     self.menu[self.active_menu_index[0]][self.active_menu_index[1]].get('date_y'),
                                     self.menu[self.active_menu_index[0]][self.active_menu_index[1]].get('time'),
                                     self.menu[self.active_menu_index[0]][self.active_menu_index[1]].get('time_x'),
                                     self.menu[self.active_menu_index[0]][self.active_menu_index[1]].get('time_y'))   

  def setNavigate(self,navigate):
      self.active_menu = active_menu(self.menu[self.active_menu_index[0]][self.active_menu_index[1]].get('id'),
                                     self.menu[self.active_menu_index[0]][self.active_menu_index[1]].get('multimenu'),
                                     self.menu[self.active_menu_index[0]][self.active_menu_index[1]].get('multipage'),
                                     navigate,
                                     self.menu[self.active_menu_index[0]][self.active_menu_index[1]].get('date'),
                                     self.menu[self.active_menu_index[0]][self.active_menu_index[1]].get('date_x'),
                                     self.menu[self.active_menu_index[0]][self.active_menu_index[1]].get('date_y'),
                                     self.menu[self.active_menu_index[0]][self.active_menu_index[1]].get('time'),
                                     self.menu[self.active_menu_index[0]][self.active_menu_index[1]].get('time_x'),
                                     self.menu[self.active_menu_index[0]][self.active_menu_index[1]].get('time_y'))    
  def up(self):
    
    if self.active_menu.multipage and self.ok_activated:
      self.setNavigate('UP')
    elif self.active_menu.multimenu:
      self.setNavigate('MENU_UP')      
    else:    
      self.ok_activated=False #deactivate ok button
      #determine index of last menu item in active menu branch
      maxIndex = len(self.menu[self.active_menu_index[0]])-1
      #if active menu is the first menu in the branch then the up button
      #takes us to the last menu in our branch
      if self.active_menu_index[1]==0:
        self.active_menu_index=(self.active_menu_index[0],maxIndex)
      else: #move up one menu in current menu branch
        self.active_menu_index=(self.active_menu_index[0],self.active_menu_index[1]-1)            
      self.setActiveMenu()

  def down(self):
    #multipage screen and ok button active
    if self.active_menu.multipage and self.ok_activated:
      self.setNavigate('DOWN')
    elif self.active_menu.multimenu:
      self.setNavigate('MENU_DOWN')
    else:
      self.ok_activated=False #deactivate ok button
      #determine index of last menu item in active menu branch
      maxIndex = len(self.menu[self.active_menu_index[0]])-1
      #if active menu is the last menu in the branch then the down button
      #takes us to the first menu of the current menu branch
      if self.active_menu_index[1]==maxIndex:
        self.active_menu_index=(self.active_menu_index[0],0)
      else: #move up one menu in current menu branch
        self.active_menu_index=(self.active_menu_index[0],self.active_menu_index[1]+1)            
      self.setActiveMenu()

  def left(self):
    self.ok_activated=False #deactivate ok button
    #determine index of last menu branch
    maxIndex = len(self.menu)-1
    #if first menu branch is active then left button activates
    #last menu branch. When going left or right, the menu activated
    #is always the top menu of the new branch
    if self.active_menu_index[0]==0:
      self.active_menu_index=(maxIndex,0)
    else: #move one menu branch to the left
      self.active_menu_index=(self.active_menu_index[0]-1,0)            
    self.setActiveMenu()
      
  def right(self):
    self.ok_activated=False #deactivate ok button
    #determine index of last menu branch
    maxIndex = len(self.menu)-1
    #if last menu branch is active then right button activates
    #first menu branch. When going left or right, the menu activated
    #is always the top menu of the new branch
    if self.active_menu_index[0]==maxIndex:
      self.active_menu_index=(0,0)
    else: #move one menu branch to the left
      self.active_menu_index=(self.active_menu_index[0]+1,0)            
    self.setActiveMenu()

  def ok(self):
    if not self.ok_activated:
      self.ok_activated = True;
    else:
      self.ok_activated = False;
  
  def getOk(self):
    return self.ok_activated
      
  def active(self):
    return self.active_menu    
