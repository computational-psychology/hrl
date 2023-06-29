from .photometer import Photometer
from .pyminolta import Minolta as Min
from .pyminolta import MinoltaException
import pygame as pg
import numpy as np


class Minolta(Photometer):
    def __init__(self, dev, timeout=5):
        super(Minolta, self).__init__()
        self.phtm = Min(dev, timeout=timeout)

    def readLuminance(self, n=3, slp=1):
        for i in range(n):
            try:
                pg.time.delay(slp)
                lm = self.phtm.getLuminance()
                return lm
            except MinoltaException as instance:
                print("Minolta error:", instance.parameter)
        # if no trial was successful
        return np.nan
