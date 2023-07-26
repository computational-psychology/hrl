import os

os.environ["DISPLAY"] = ":0.1"

from hrl.graphics.datapixx import DATAPixx
from hrl.inputs.responsepixx import RESPONSEPixx
from hrl.extra import initializeDATAPixx

import numpy as np
import pygame as pg
import time

# Test

dpx = initializeDATAPixx()

btns = ["Left", "Right", "Up", "Down", "Space"]
kbd = RESPONSEPixx(btns, dpx)

grphcs = DATAPixx(600, 600, 0.5, False, True)

grphcs.flip()
txt = grphcs.newTexture(np.array([[1]]))
txt.draw((200, 200), (200, 200))
grphcs.flip()

for btn in btns:
    print("Please press " + btn)
    (foo, t) = kbd.readButton(btns=[btn])
    print("Time taken: " + str(t))
