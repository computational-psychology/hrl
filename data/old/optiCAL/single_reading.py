#!/usr/bin/python
#coding: utf-8

import pyoptical
op = pyoptical.OptiCAL('/dev/ttyUSB0')
try: 
	print op.read_luminance()
except pyoptical.NACKException:
	print 'nack'


