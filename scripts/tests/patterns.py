import numpy as np
import pygame as pg


def flatGradient(wdth,hght):
    return np.repeat([np.linspace(0,1,wdth,endpoint=False)],hght,0)
