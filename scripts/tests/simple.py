from hrl.graphics.gpu import GPU
from hrl.inputs.keyboard import Keyboard

import numpy as np
import pygame as pg
import time

btns = ['Left','Right','Up','Down','Space']
kbd = Keyboard(btns)

grphcs = GPU(600,600,0.5,False,True)
grphcs.flip()
txt = grphcs.newTexture(np.array([[1]]))
txt.draw((200,200),(200,200))
grphcs.flip()

for btn in btns:

    print('Please press ' + btn)
    (foo,t) = kbd.readButton(btns=[btn])
    print('Time taken: ' + str(t))


