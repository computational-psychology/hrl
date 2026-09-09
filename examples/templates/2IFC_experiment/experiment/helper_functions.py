"""
Some helper functions used in the experiment
@authors: GA and LS
"""

import numpy as np

def make_sound(f, sampleRate=44100):
    x = np.arange(0, sampleRate)
    arr = (4096 * np.sin(2.0 * np.pi * f * x / sampleRate)).astype(np.int16)
    return arr
