#!/usr/bin/env python
#coding: utf-8

import pydatapixx
import time

a = datapixx.open()

# wait for key press
for i in range(5):
	print a.waitButton(0.5)

# check if there was a key press since last call
a.readButton() # first run for initialisation
for i in range(5):
	print a.readButton()
	time.sleep(1)

# blink with each button and then with all at once
a.blink(datapixx.BWHITE, 2)
a.blink(datapixx.BBLUE, 1)
a.blink(datapixx.BGREEN, 2)
a.blink(datapixx.BYELLOW, 3)
a.blink(datapixx.BRED, 4)
a.blink(datapixx.BWHITE | datapixx.BBLUE | datapixx.BGREEN | datapixx.BYELLOW | datapixx.BRED)


# using configLights() function set single lights, double lights and switch all off
a.configLights(datapixx.BRED)
time.sleep(1)
a.configLights(datapixx.BRED|datapixx.BYELLOW)
time.sleep(1)
a.configLights(datapixx.BGREEN)
time.sleep(1)
a.configLights()
