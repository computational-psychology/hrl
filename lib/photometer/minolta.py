from photometer import Photometer
import pyminolta as pym
import pygame as pg
import numpy as np

class Minolta(Photometer):

    def __init__(self,dev,timeout=5):
        super(Minolta,self).__init__()
        self.phtm = pym.Minolta(dev,timeout=timeout)

    def readLuminance(self,n=3,slp=1):
        for i in range(n):
            try: 
                pg.time.delay(slp)
                lm = self.phtm.getLuminance()
                return lm
            except:
                return np.nan
