import numpy as np
import time

from hrl.inputs.keyboard import Keyboard

btns = ['Left','Right','Up','Down','Space']
kbd = Keyboard(btns)

for btn in btns:
    print("Please press " + btn + ":")
    (foo,t) = kbd.readButton(btns=[btn])
    print("Time taken: " + str(t))


