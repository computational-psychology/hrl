from .photometer import Photometer
import pyoptical as pop
import pygame as pg
import numpy as np


class OptiCAL(Photometer):
    def __init__(self, dev, timeout=5):
        super(OptiCAL, self).__init__()
        self.phtm = pop.OptiCAL(dev, timeout=timeout)

    def readLuminance(self, n, slp):
        for i in range(n):
            try:
                pg.time.delay(slp)
                lm = self.phtm.read_luminance()
                return lm
            except:
                return np.nan
