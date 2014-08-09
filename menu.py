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
import configuration

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
    #load structure of the menu from configuration.       ]
    self.menu=self.loadMenu()
    #upon start the startup menu is active
    self.active_menu_index=(0,0)                 
    self.setActiveMenu()
    self.ok_activated=False #ok button not activated
    
  def loadMenu(self):
    menu_item={}
    my_menu=[]
    menu_items=[]
    prev_col=0
    for config in configuration.CONFIG['menu'] :
      prefix, col, row = config.split('.')
      for pair in configuration.CONFIG['menu'][config].split(','):
        #create dictionary for one menu item
        #containing all its keywords
        key=(pair.split('=')[0]).strip()
        val=eval(pair.split('=')[1])
        menu_item.update(((key,val),))
      if int(col)==prev_col:
        #if menu item belongs to same menu point as previous item
        #then add the menu item to a list of those menu items
        menu_items.append(menu_item)
        menu_item={} #previous dictionary still exists in the menu_items list, but menu_item 
                     #is no longer associated with this menu_item dictionary
      else:
        #we have a new menu point, so lets at the list of menu items so far created
        #i.e. the "previous" menu point to the menu list
        my_menu.append(menu_items)
        menu_items= [] #previous menu_items still exist in the my_menu list, but are no longer associated with this  menu_items list
        menu_items.append(menu_item)
        menu_item={}
        prev_col=int(col)  
    #apped the last menu-point to the my_menu list
    my_menu.append(menu_items)
    return my_menu
    
  
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
