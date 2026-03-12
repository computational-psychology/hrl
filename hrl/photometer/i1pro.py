""" Class to read luminance values with x-rite i1Pro.

It relies on the pypixxlib library, from VPixx 

"""
from .photometer import Photometer
from pypixxlib.i1 import I1Pro
import pygame
import numpy as np


class i1Pro(Photometer):
    def __init__(self, timeout=5):
        super(i1Pro, self).__init__()
        self.phtm = I1Pro()
        
        print("i1Pro device connected")
        print(f"revision: {self.phtm.revision} - serial number: {self.phtm.serial_number}")
        self.phtm.setColorSpace("CIEXYZ")
     
        # check if calibration is necessary
        self.calibrate()
        
    def calibrate(self):
        print("Calibrating device, put the device on its nest and push the side button")
        self.phtm.calibrate("Emission")
        
        print(f"Current color space is {self.phtm.getColorSpace()}")
        print(f"Current measurement mode is {self.phtm.getMeasurementMode()}")
        print(f"Current illumination mode is {self.phtm.getIlluminationMode()}")
        print("... ready to measure.")

    def readLuminance(self, n=3, slp=1):
        # check is calibration is necessary
        
        # do measurements
        for i in range(n):
            try:
                pygame.time.delay(slp)
                
                # measure the XYZ tristimulus values
                self.phtm.runMeasurement()
                X, Y, Z = self.phtm.getLatestTriStimulusMeasurements()
                print(f"X: {X}, Y: {Y}, Z:{Z}")                                         
                return Y
            except:
                print("Error in reading from instrument")
        # if no try was successful
        return np.nan
