from hrl import HRL
from hrl.graphics import graphics
from socket import gethostname
import os
import sys

import numpy as np
from stimuli.papers.RHS2007 import WE_thick

# size of Siements monitor
WIDTH = 1024
HEIGHT = 768


# center of screen
whlf = WIDTH / 2.0
hhlf = HEIGHT / 2.0


def show_stim(hrl):
    stim = WE_thick()

    # texture creation in buffer : stimulus
    stimulus = hrl.graphics.newTexture(stim["img"])

    # Show stimlus
    stimulus.draw((whlf - stimulus.wdth / 2, hhlf - stimulus.hght / 2))

    # flip everything
    hrl.graphics.flip(clr=True)  # clr= True to clear buffer

    # delete texture from buffer
    graphics.deleteTextureDL(stimulus._dlid)


def respond(hrl):
    btn = None

    # Process button presses
    (btn, t1) = hrl.inputs.readButton()
    if btn == "Up":
        print("Pressed up")
        # additional code here
        # ....

    elif btn == "Down":
        print("Pressed down")
        # additional code here
        # ....

    elif btn == "Right":
        print("Pressed right")
        # additional code here
        # ....

    elif btn == "Left":
        print("Pressed left")
        # additional code here
        # ....

    elif btn == "Space":
        print("Pressed space")

    elif btn == "Escape":
        print("Escape pressed, exiting experiment!!")
        hrl.close()
        sys.exit(0)

    return btn


def run_block(hrl):
    for trial in range(0, 3):
        print("Running trial %d" % trial)
        show_stim(hrl)
        btn = respond(hrl)
        while btn != "Space":
            btn = respond(hrl)
    print("Done with block")


def run_experiment():
    lut = os.path.dirname(os.path.abspath(__file__)) + "/lut.csv"

    # Figure out if we're running in the vision lab
    inlab = True if "vlab" in gethostname() else False

    if inlab:
        # create HRL object
        hrl = HRL(
            graphics="datapixx",
            inputs="responsepixx",
            photometer=None,
            wdth=WIDTH,
            hght=HEIGHT,
            bg=0.2,
            scrn=1,
            lut=lut,
            db=True,
            fs=True,
        )

    else:
        hrl = HRL(
            graphics="gpu",
            inputs="keyboard",
            photometer=None,
            wdth=WIDTH,
            hght=HEIGHT,
            bg=0.2,
            scrn=1,
            lut=lut,
            db=True,
            fs=False,
        )

    run_block(hrl)


if __name__ == "__main__":
    run_experiment()
