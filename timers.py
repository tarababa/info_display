################################################################################
# Application         : Generic timer related classes
# File                : $HeadURL:  $
# Version             : $Revision: $
# Created by          : hta
# Created             : 26.01.2014
# Changed by          : $Author: b7tarah $
# File changed        : $Date: 2013-08-21 15:19:43 +0200 (Mi, 21 Aug 2013) $
# Environment         : Python 3.2.3 
# ##############################################################################
# Description : Generic timer related classed
################################################################################
import os,sys
import threading

#------------------------------------------------------------------------------#
# Timer: Timer class based on the standard threading.Timer class. This class   #
#        differs from the standard in that it splits the waits up into slices  #
#        of a maximum of 1800 seconds. The reason for this is that it seems    #
#        that somewhere between 1800 and 3600 seconds the standard implemen-   #
#        taition will hang indefinetly on the wait.                            #
#        I suspect 2147 is the maximum wait time that will work, I have        #
#        not really found anything describing my problem some hints I found:   #
#         - http://trac.pjsip.org/repos/ticket/975                             # 
#         - http://developer.nokia.com/community/discussion/showthread.php/187312-snippet-Ao_timer-without-2147-second-limit
#------------------------------------------------------------------------------#
# version who when       description                                           #
# 1.00    hta 09.11.2013 Initial version                                       #
#------------------------------------------------------------------------------#
class Timer(threading.Thread):
  def __init__(self, interval, function, args=None, kwargs=None):
    threading.Thread.__init__(self)
    self.interval = interval
    self.function = function
    self.args = args if args is not None else []
    self.kwargs = kwargs if kwargs is not None else {}
    self.finished = threading.Event()
  
  def cancel(self):
    """Stop the timer if it hasn't finished yet."""
    self.finished.set()
  
  def run(self):
    MAX=1800
    while self.interval > MAX:
        self.finished.wait(MAX)
        self.interval = self.interval-MAX
    self.finished.wait(self.interval)
    if not self.finished.is_set():
        self.function(*self.args, **self.kwargs)
    self.finished.set()
    

class RepeatingTimer(threading.Thread):
  def __init__(self, interval, function, args=None, kwargs=None):
    threading.Thread.__init__(self)
    self.interval = interval
    self.function = function
    self.args = args if args is not None else []
    self.kwargs = kwargs if kwargs is not None else {}
    self.finished = threading.Event()
  
  def cancel(self):
    """Stop the timer if it hasn't finished yet."""
    self.finished.set()
  
  def run(self):
    MAX=1800
    while not self.finished.is_set():
      waitRemainder = self.interval
      while waitRemainder > MAX:
          self.finished.wait(MAX)
          waitRemainder = waitRemainder-MAX
      self.finished.wait(waitRemainder)
      if not self.finished.is_set():
          self.function(*self.args, **self.kwargs)
    
class RRepeatingTimer(object):
  def __init__(self, interval, function, args=None, kwargs=None):
    super(RepeatingTimer, self).__init__()    
    self.interval = interval
    self.function = function
    self.args = args if args is not None else []
    self.kwargs = kwargs if kwargs is not None else {}
  
  def cancel(self):
    """Stop the timer if it hasn't finished yet."""
    self.finished.set()
  
  def start(self):
    self.callback()
    
  def stop(self):
    self.interval = False

  def callback(self):
    if self.interval:
      self.function(*self.args, **self.kwargs)
      Timer(self.interval, self.callback).start()   
