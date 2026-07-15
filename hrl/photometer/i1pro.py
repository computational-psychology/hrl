""" Class to read luminance values with X-Rite i1Pro.

It relies on the pypixxlib library from VPixx 

"""

from .photometer import Photometer
from pypixxlib.i1 import I1Pro
import pygame
import numpy as np

def wait_any_button(timeout=0):
    t0 = pygame.time.get_ticks()
    btn = None
    while (timeout == 0) or (pygame.time.get_ticks() - t0 < timeout):
        event = pygame.event.wait(1)  # waits for only 1 ms
        if event.type == pygame.KEYDOWN:
            break
        
        
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
        print('****************************************************')
        print("Calibrating device, put the device on its nest and push the side button")
        self.phtm.calibrate("Emission")
        
        print(f"Current color space is {self.phtm.getColorSpace()}")
        print(f"Current measurement mode is {self.phtm.getMeasurementMode()}")
        print(f"Current illumination mode is {self.phtm.getIlluminationMode()}")
        print("... Calibration done.")
        print('****************************************************')
        print('')
        print('Put the device on the screen to be measured and press any key to start / continue the measurements')
        wait_any_button(timeout=0)


    def readTristimulus(self, n=3, slp=1, verbose=False):
        
        # check if calibration is needed
        if self.phtm.isCalibrationExpired():
            self.calibrate()
            
        # do measurements
        for i in range(n):
            try:
                pygame.time.delay(slp)
                
                # measure the XYZ tristimulus values
                self.phtm.runMeasurement()
                X, Y, Z = self.phtm.getLatestTriStimulusMeasurements()
                if verbose:
                    print('Tristimulus values:')
                    print(f"X: {X}, Y: {Y}, Z:{Z}")
                              
                                         
                return X, Y, Z
            except:
                print("Error in reading from instrument")
        # if no try was successful
        return np.nan
        
        
    def readLuminance(self, n=3, slp=1, verbose=False):
        
        # reads tristimulus values X, Y, Z.
        _, lum, _ = self.readTristimulus(n=n, slp=slp, verbose=verbose)
        
        # returns Y, which is luminance by definition.    
        return lum       

        

