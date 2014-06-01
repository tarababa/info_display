#*********************************************************************
#*
#* $Id: yocto_altitude.py 16185 2014-05-12 16:00:20Z seb $
#*
#* Implements yFindAltitude(), the high-level API for Altitude functions
#*
#* - - - - - - - - - License information: - - - - - - - - - 
#*
#*  Copyright (C) 2011 and beyond by Yoctopuce Sarl, Switzerland.
#*
#*  Yoctopuce Sarl (hereafter Licensor) grants to you a perpetual
#*  non-exclusive license to use, modify, copy and integrate this
#*  file into your software for the sole purpose of interfacing
#*  with Yoctopuce products.
#*
#*  You may reproduce and distribute copies of this file in
#*  source or object form, as long as the sole purpose of this
#*  code is to interface with Yoctopuce products. You must retain
#*  this notice in the distributed source file.
#*
#*  You should refer to Yoctopuce General Terms and Conditions
#*  for additional information regarding your rights and
#*  obligations.
#*
#*  THE SOFTWARE AND DOCUMENTATION ARE PROVIDED 'AS IS' WITHOUT
#*  WARRANTY OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING 
#*  WITHOUT LIMITATION, ANY WARRANTY OF MERCHANTABILITY, FITNESS
#*  FOR A PARTICULAR PURPOSE, TITLE AND NON-INFRINGEMENT. IN NO
#*  EVENT SHALL LICENSOR BE LIABLE FOR ANY INCIDENTAL, SPECIAL,
#*  INDIRECT OR CONSEQUENTIAL DAMAGES, LOST PROFITS OR LOST DATA,
#*  COST OF PROCUREMENT OF SUBSTITUTE GOODS, TECHNOLOGY OR 
#*  SERVICES, ANY CLAIMS BY THIRD PARTIES (INCLUDING BUT NOT 
#*  LIMITED TO ANY DEFENSE THEREOF), ANY CLAIMS FOR INDEMNITY OR
#*  CONTRIBUTION, OR OTHER SIMILAR COSTS, WHETHER ASSERTED ON THE
#*  BASIS OF CONTRACT, TORT (INCLUDING NEGLIGENCE), BREACH OF
#*  WARRANTY, OR OTHERWISE.
#*
#*********************************************************************/


__docformat__ = 'restructuredtext en'
from yocto_api import *


#--- (YAltitude class start)
#noinspection PyProtectedMember
class YAltitude(YSensor):
    """
    The Yoctopuce application programming interface allows you to read an instant
    measure of the sensor, as well as the minimal and maximal values observed.
    
    """
#--- (end of YAltitude class start)
    #--- (YAltitude return codes)
    #--- (end of YAltitude return codes)
    #--- (YAltitude definitions)
    QNH_INVALID = YAPI.INVALID_DOUBLE
    #--- (end of YAltitude definitions)

    def __init__(self, func):
        super(YAltitude, self).__init__(func)
        self._className = 'Altitude'
        #--- (YAltitude attributes)
        self._callback = None
        self._qnh = YAltitude.QNH_INVALID
        #--- (end of YAltitude attributes)

    #--- (YAltitude implementation)
    def _parseAttr(self, member):
        if member.name == "qnh":
            self._qnh = member.ivalue / 65536.0
            return 1
        super(YAltitude, self)._parseAttr(member)

    def set_currentValue(self, newval):
        """
        Changes the current estimated altitude. This allows to compensate for
        ambient pressure variations and to work in relative mode.
        
        @param newval : a floating point number corresponding to the current estimated altitude
        
        @return YAPI.SUCCESS if the call succeeds.
        
        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(int(round(newval * 65536.0, 1)))
        return self._setAttr("currentValue", rest_val)

    def set_qnh(self, newval):
        """
        Changes the barometric pressure adjusted to sea level used to compute
        the altitude (QNH). This enables you to compensate for atmospheric pressure
        changes due to weather conditions.
        
        @param newval : a floating point number corresponding to the barometric pressure adjusted to sea
        level used to compute
                the altitude (QNH)
        
        @return YAPI.SUCCESS if the call succeeds.
        
        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(int(round(newval * 65536.0, 1)))
        return self._setAttr("qnh", rest_val)

    def get_qnh(self):
        """
        Returns the barometric pressure adjusted to sea level used to compute
        the altitude (QNH).
        
        @return a floating point number corresponding to the barometric pressure adjusted to sea level used to compute
                the altitude (QNH)
        
        On failure, throws an exception or returns YAltitude.QNH_INVALID.
        """
        if self._cacheExpiration <= YAPI.GetTickCount():
            if self.load(YAPI.DefaultCacheValidity) != YAPI.SUCCESS:
                return YAltitude.QNH_INVALID
        return self._qnh

    @staticmethod
    def FindAltitude(func):
        """
        Retrieves an altimeter for a given identifier.
        The identifier can be specified using several formats:
        <ul>
        <li>FunctionLogicalName</li>
        <li>ModuleSerialNumber.FunctionIdentifier</li>
        <li>ModuleSerialNumber.FunctionLogicalName</li>
        <li>ModuleLogicalName.FunctionIdentifier</li>
        <li>ModuleLogicalName.FunctionLogicalName</li>
        </ul>
        
        This function does not require that the altimeter is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YAltitude.isOnline() to test if the altimeter is
        indeed online at a given time. In case of ambiguity when looking for
        an altimeter by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.
        
        @param func : a string that uniquely characterizes the altimeter
        
        @return a YAltitude object allowing you to drive the altimeter.
        """
        # obj
        obj = YFunction._FindFromCache("Altitude", func)
        if obj is None:
            obj = YAltitude(func)
            YFunction._AddToCache("Altitude", func, obj)
        return obj

    def nextAltitude(self):
        """
        Continues the enumeration of altimeters started using yFirstAltitude().
        
        @return a pointer to a YAltitude object, corresponding to
                an altimeter currently online, or a None pointer
                if there are no more altimeters to enumerate.
        """
        hwidRef = YRefParam()
        if YAPI.YISERR(self._nextFunction(hwidRef)):
            return None
        if hwidRef.value == "":
            return None
        return YAltitude.FindAltitude(hwidRef.value)

#--- (end of YAltitude implementation)

#--- (Altitude functions)

    @staticmethod
    def FirstAltitude():
        """
        Starts the enumeration of altimeters currently accessible.
        Use the method YAltitude.nextAltitude() to iterate on
        next altimeters.
        
        @return a pointer to a YAltitude object, corresponding to
                the first altimeter currently online, or a None pointer
                if there are none.
        """
        devRef = YRefParam()
        neededsizeRef = YRefParam()
        serialRef = YRefParam()
        funcIdRef = YRefParam()
        funcNameRef = YRefParam()
        funcValRef = YRefParam()
        errmsgRef = YRefParam()
        size = YAPI.C_INTSIZE
        #noinspection PyTypeChecker,PyCallingNonCallable
        p = (ctypes.c_int * 1)()
        err = YAPI.apiGetFunctionsByClass("Altitude", 0, p, size, neededsizeRef, errmsgRef)

        if YAPI.YISERR(err) or not neededsizeRef.value:
            return None

        if YAPI.YISERR(
                YAPI.yapiGetFunctionInfo(p[0], devRef, serialRef, funcIdRef, funcNameRef, funcValRef, errmsgRef)):
            return None

        return YAltitude.FindAltitude(serialRef.value + "." + funcIdRef.value)

#--- (end of Altitude functions)
