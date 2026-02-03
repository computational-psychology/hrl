#!/usr/bin/env python
# coding: utf-8

"""
Setting various LUTs for monochrome display (all 3 components equal)
"""

import pydatapixx
import numpy as np

a = pydatapixx.open()

a.setVidMode(pydatapixx.DPREG_VID_CTRL_MODE_L48)  # red as index into CLUT

clut = (np.linspace(0, 0.4, 256) * 65535).tolist()
a.setVidClut(clut)
raw_input("->")

clut = (np.linspace(0.4, 0.8, 256) * 65535).tolist()
a.setVidClut(clut)
raw_input("->")

clut = (np.linspace(0.8, 1, 256) * 65535).tolist()
a.setVidClut(clut)
