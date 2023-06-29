from hrl.photometer.optical import OptiCAL

import numpy as np
import pygame as pg
import time


phtm = OptiCAL("/dev/ttyUSB0")
print("\nLuminance: " + str(phtm.readLuminance(5, 5)) + "\n")
