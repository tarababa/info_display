#!/usr/bin/python
# -*- coding: utf-8 -*-
import os,sys
import time
import math
import urllib.parse
import urllib.request
import collections
import decimal
# add ../../Sources to the PYTHONPATH
sys.path.append(os.path.join("..","..","Sources"))

from yocto_api import *
from yocto_display import *

exchangeRate = collections.namedtuple("rate"," baseCurrency currency timestamp rate")

def usage():
  scriptname = os.path.basename(sys.argv[0])
  print("Usage:")
  print(scriptname+' <serial_number>')
  print(scriptname+' <logical_name>')
  print(scriptname+' any  ')
  sys.exit()

def die(msg):
  sys.exit(msg+' (check USB cable)')

def init():
  errmsg=YRefParam()

  if len(sys.argv)<2 :  usage()

  target=sys.argv[1]

  # Setup the API to use local USB devices
  if YAPI.RegisterHub("usb", errmsg)!= YAPI.SUCCESS:
    sys.exit("init error"+errmsg.value)



  if target=='any':
    # retreive any RGB led
    disp = YDisplay.FirstDisplay()
    if disp is None :
      die('No module connected')
  else:
    disp= YDisplay.FindDisplay(target + ".display")

  if not disp.isOnline():
    die("Module not connected ")

  # display clean up
  disp.resetAll()
  disp.set_brightness(10)

  return disp

def showExchangeRate(sBaseCurrency, sCurrency, sRate, sTimestamp, disp):
  # retreive the display size
  w=128 #disp.get_displayWidth()
  h=64 #disp.get_displayHeight()

  layer1=disp.get_displayLayer(1)
  layer1.clear()
  layer1.hide()
  layer1.selectFont('Small.yfm')
  layer1.drawText(0,0, YDisplayLayer.ALIGN.TOP_LEFT, sBaseCurrency )
  layer1.drawText(50,0, YDisplayLayer.ALIGN.TOP_LEFT, sTimestamp )
  layer1.selectFont('Medium.yfm')
  layer1.drawText(0,10, YDisplayLayer.ALIGN.TOP_LEFT, sRate+" "+sCurrency )
  disp.swapLayerContent(1,0)
  

def showClock(disp, time):
	
  #get height and width
  width=128 #disp.get_displayWidth()
  height=64 #disp.get_displayHeight()
  
  yOffset = 11
  xOffset = 10
  
  radius=6
  
  layer4=disp.get_displayLayer(4)
  layer4.hide()
  layer4.clear()
  layer4.drawCircle(width-xOffset-radius,radius+yOffset,radius)
  #go to centre of circle
  layer4.moveTo(width-xOffset-radius,radius+yOffset)
  #draw hand, seems it must be a a bit shorter
  #than the radius to stay within the circle 
  #hence radius-1
  y=(radius-1)*math.cos(2*math.pi*time)
  x=(radius-1)*math.sin(2*math.pi*time)
  layer4.lineTo((width-xOffset-radius)+int(x),radius+yOffset-int(y))

  layer2=disp.get_displayLayer(2)
  disp.swapLayerContent(4,2)
  
def getExchangeRate():
  #provider of exchange rate
  url = 'http://www.xe.com/currencyconverter/convert.cgi'
  #spoof the user agent.
  user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'

  data={}
  data['template']='crm1'
  data['Amount']='1'
  data['From']='CHF'
  data['To']='ZAR'
  url_values = urllib.parse.urlencode(data)
  headers = { 'User-Agent' : user_agent }

  #SLOG proxy
  proxy_support = urllib.request.ProxyHandler({'http' : '172.20.5.199:8080'})
  opener = urllib.request.build_opener(proxy_support)
  urllib.request.install_opener(opener)

  req = urllib.request.Request(url+'?'+url_values, None, headers)
  response = urllib.request.urlopen(req)
  the_page = response.read()
  myString = str( the_page, encoding='utf8' )
  mySubString=myString[myString.find("1 CHF ="):   myString.find("1 CHF =") + myString[myString.find("1 CHF ="):].find(" ZAR</span>")+4]
  
  sTimestamp=myString[myString.find("Live rates at ")+14:myString.find("Live rates at ")+14+23]
  #Live rates at 2013.09.01 07:25:00 UTC &#160; </div>
  
  sBaseCurrency = "CHF"
  sCurrency     = "ZAR"
  sRate         = mySubString[mySubString.find("1 CHF = ")+8: mySubString.find(" ZAR")]
  return sBaseCurrency, sCurrency, sRate, sTimestamp
	
def addRate(sBaseCurrency, sCurrency, sTimestamp, sRate, rates):
  
  rates.append(exchangeRate(sBaseCurrency, sCurrency, sTimestamp,sRate))

def simulatedRates(rates):
  addRate('CHF','ZAR','20130831153112','11.0516',rates)	
  addRate('CHF','ZAR','20130831153212','11.0416',rates)	
  addRate('CHF','ZAR','20130831153312','11.0832',rates)	
  addRate('CHF','ZAR','20130831153412','11.1116',rates)	
  addRate('CHF','ZAR','20130831153512','11.2916',rates)	
  addRate('CHF','ZAR','20130831153612','11.1826',rates)	
  addRate('CHF','ZAR','20130831153712','11.1716',rates)	
  addRate('CHF','ZAR','20130831153812','11.1733',rates)	
  addRate('CHF','ZAR','20130831153912','11.1912',rates)	
  addRate('CHF','ZAR','20130831154012','11.1989',rates)	
  addRate('CHF','ZAR','20130831154112','11.2000',rates)	
  addRate('CHF','ZAR','20130831154212','11.2100',rates)	
  addRate('CHF','ZAR','20130831154312','11.2150',rates)	
  addRate('CHF','ZAR','20130831154412','11.2345',rates)	
  addRate('CHF','ZAR','20130831154512','11.2391',rates)	
  addRate('CHF','ZAR','20130831154612','11.2401',rates)	
  addRate('CHF','ZAR','20130831154712','11.2430',rates)	
  addRate('CHF','ZAR','20130831154812','11.2501',rates)	
  addRate('CHF','ZAR','20130831154912','11.2501',rates)	
  addRate('CHF','ZAR','20130831155012','11.2623',rates)	
  addRate('CHF','ZAR','20130831155112','11.2603',rates)	
  
def showRates(rates):
  for rate in rates:
    print("{0} {1} {2} {3}".format(rate.baseCurrency, rate.currency, rate.rate, rate.timestamp ))
		

def getMinMaxRateAndSampleSize(rates):
  dMaxRate=0
  dMinRate=decimal.Decimal(rates[0].rate)
  iSampleSize=0
  for rate in rates:
    if decimal.Decimal(rate.rate)>dMaxRate:
      dMaxRate=decimal.Decimal(rate.rate)
    if decimal.Decimal(rate.rate)<dMinRate:
      dMinRate=decimal.Decimal(rate.rate)    
    iSampleSize+=1
  return dMinRate,dMaxRate,iSampleSize
  
def showGraph(rates,disp):  
  graph=[]
  coords = collections.namedtuple("coord","x y")
  iResizeFactor=500
  iGraphWidth=105
  
  
  dMinRate,dMaxRate,iSampleSize = getMinMaxRateAndSampleSize(rates)

  #we have a vertical resolution of 32 pixels for the exchange rate.
  #Thus if the difference between min and max is more then 32 the
  #graph may not show all the values. Thus lets calculate the 
  #resisze factor dynamically
  if iResizeFactor*(dMaxRate-dMinRate)>37:
    iResizeFactor=32/(dMaxRate-dMinRate)
    print("adjusted iResizeFactor to {0}".format(iResizeFactor))

  #print("max rate {0} sample size {1}".format(dMaxRate,iSampleSize))
  if iSampleSize >= iGraphWidth:
    i = -iGraphWidth
    j = 0
  else:
    i = 0
    j = iSampleSize
 
  x=0
  while i < j:
    # Y-coordinate is calculated so that the maximum value is displayed at the top
    # of the graph, if the iResizeFactor is static it this strategy may cause the
    # mimimum rate to fall below the bottom of the display i.e. the mimimum rate
    # may not always be shown, the maximum rate will always fit on the display
    y = iResizeFactor*decimal.Decimal(rates[i].rate) - (iResizeFactor*dMaxRate - 32)
    graph.append(coords(x,y))
    x+=1
    i+=1

  layer1=disp.get_displayLayer(1)
  layer1.hide()
  layer1.clear()
  for coord in graph:
    #print("{0} {1}".format(coord.x, coord.y ))    
    #As the bottom of the display correspends with y=63 we must substract
    #the calculated y value from the 63. 
    if coord.x==0: 
      layer1.moveTo(coord.x,63-coord.y)
      layer1.drawPixel(coord.x,63-coord.y)
    else:
      layer1.lineTo(coord.x,63-coord.y)
  
  #Min and max rates next to grap
  layer1.selectFont('Small.yfm')
  layer1.drawText(iGraphWidth+2,31, YDisplayLayer.ALIGN.TOP_LEFT, 'Min')
  layer1.drawText(iGraphWidth+2,40, YDisplayLayer.ALIGN.TOP_LEFT, str(dMinRate))
  layer1.drawText(iGraphWidth+2,49, YDisplayLayer.ALIGN.TOP_LEFT, 'Max')
  layer1.drawText(iGraphWidth+2,57, YDisplayLayer.ALIGN.TOP_LEFT, str(dMaxRate))
  
  layer3=disp.get_displayLayer(3)
  disp.swapLayerContent(1,3)

def main():
  disp=init()	
  rates=[]
  #simulatedRates(rates)

  while (1):
    try:  
      sBaseCurrency, sCurrency, sRate, sTimestamp=getExchangeRate()
      showExchangeRate(sBaseCurrency,sCurrency,sRate,sTimestamp,disp)
      addRate(sBaseCurrency,sCurrency,sTimestamp,sRate,rates)
      showGraph(rates,disp)
    except Exception:
      print ("not good")
    #run clock
    for i in range (0,25):
      showClock(disp, i/24)
      time.sleep(2.4)
      
    #keep sample limited to 128 samples
    try:
      rates=rates[-128:]
    except Exception:
      print("oops")
if __name__ == '__main__':
  main()
  
    
