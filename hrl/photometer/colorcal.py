from .photometer import Photometer
from .crscolorcal import ColorCAL as CC
import pygame
import numpy as np


class ColorCal(Photometer):
    def __init__(self, dev):
        super(ColorCal, self).__init__()
        self.phtm = CC(dev)

    def readLuminance(self, n=3, slp=1):
        for i in range(n):
            try:
                pygame.time.delay(slp)
                lm = self.phtm.getLum()
                return lm
            except:
                print("ColorCAL error:")
        return np.nan
