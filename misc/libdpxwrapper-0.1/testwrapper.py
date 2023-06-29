#!/usr/bin/env python
# coding: utf-8

import sys
import time
from ctypes import *

from libdpxwrapper import *

# open communication with the device
DPxOpen()

# check for errors
if DPxGetError() != DPX_SUCCESS:
    print("Could not open DATAPixx")
    sys.exit(1)

print("DPxIsReady():", DPxIsReady())


# change video mode
DPxSetVidMode(DPXREG_VID_CTRL_MODE_C24)  # passthrough
DPxUpdateRegCache()
if DPxGetError() != DPX_SUCCESS:
    print("could not change video mode")


if DPxIsVidDviActive():
    print("Getting data over DVI")
    if DPxIsVidOverClocked():
        print("Input is overclocked!")
    else:
        print("Frequency is OK")
else:
    print("No data over DVI")

# prepare response box
DPxSetDinDataDir(0x00FF0000)
DPxEnableDinStabilize()
DPxEnableDinDebounce()

DPxEnableDinLogTimetags()
DPxEnableDinLogEvents()
dinBuffAddr = 0x800000
dinBuffSize = 0x400000
DPxSetDinBuff(dinBuffAddr, dinBuffSize)
DPxUpdateRegCache()

# get current video frequency
print("freq:", DPxGetVidVFreq())

a = c_int()
b = c_int()
DPxGetNanoTime(byref(a), byref(b))
print("NanoTime:", a, b)

# set CLUT
CLUT = c_uint16 * 768  # create data type for uint16 array
clut_data = CLUT()  # create array
for i in range(768):
    clut_data[i] = 0
clut_data[-2] = 65535
DPxSetVidClut(clut_data)
DPxUpdateRegCache()
raw_input("set clut->")
DPxSetVidMode(DPXREG_VID_CTRL_MODE_L48)  # use red as lut index
DPxUpdateRegCache()
raw_input("set back->")
DPxSetVidMode(DPXREG_VID_CTRL_MODE_C24)  # passthrough
DPxUpdateRegCache()


# clean up
DPxStopAllScheds()
DPxUpdateRegCache()
DPxClose()
