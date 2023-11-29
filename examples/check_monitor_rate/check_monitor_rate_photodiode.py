"""
Checks frame rate of the monitor.

When ran in a "normal" user screen, windowed, you will not get an
accurate measurement.

When ran in the experimental monitor, frame rate should be exactly
the same as the one reported by the manufacturer. It should also be
ZERO dropped frames. That ensures that your graphics pipeline is working
fine.


"""

### Imports ###

# Package Imports
from hrl import HRL

# Qualified Imports
import numpy as np
import sys
import os
import time
from math import pi

# Unqualified Imports
from random import uniform
from socket import gethostname

inlab_siemens = True if "vlab" in gethostname() else False
inlab_viewpixx = True if "viewpixx" in gethostname() else False

import clock

defaultClock = clock.monotonicClock

### Main ###
def main():
    ### HRL Parameters ###
    # Here we define all the paremeters required to instantiate an HRL object.

    # Which devices we wish to use in this experiment. See the
    # pydoc documentation for a list of # options.
    if inlab_siemens:
        graphics = "datapixx"
        inputs = "responsepixx"
        scrn = 1
        fs = True  # fullscreen
        wdth = 1024  # Screen size
        hght = 768

    elif inlab_viewpixx:
        graphics = "viewpixx"
        inputs = "responsepixx"
        scrn = 1
        fs = True  # fullscreen
        wdth = 1920  # Screen size
        hght = 1080

    else:
        graphics = "gpu"  # 'datapixx' is another option
        inputs = "keyboard"  # 'responsepixx' is another option
        scrn = 0
        fs = False  # not fullscreen: windowed
        wdth = 1024  # Screen size
        hght = 768

    photometer = None

    # background value
    bg = 0.0

    # Pass this to HRL if we want to use gamma correction.
    lut = "lut.csv"

    # Create the hrl object with the above fields. All the default argument names are
    # given just for illustration.
    hrl = HRL(
        graphics=graphics,
        inputs=inputs,
        photometer=photometer,
        wdth=wdth,
        hght=hght,
        bg=bg,
        fs=fs,
        scrn=scrn,
    )

    ### measuring frame rate
    nIdentical = 10
    nMaxFrames = 100
    nWarmUpFrames = 10
    threshold = 1
    refreshThreshold = 1.0
    nDroppedFrames = 0
    # run warm-ups
    for frameN in range(nWarmUpFrames):
        hrl.graphics.flip()

    # run test frames
    firsttimeon = True
    frameIntervals = []
    rate = 0
    for frameN in range(nMaxFrames):
        hrl.graphics.flip()

        frameTime = now = defaultClock.getTime()

        if firsttimeon:
            firsttimeon = False
            lastFrameT = now
            pass

        deltaT = now - lastFrameT
        lastFrameT = now
        frameIntervals.append(deltaT)

        if len(frameIntervals) >= nIdentical and (
            np.std(frameIntervals[-nIdentical:]) < (threshold / 1000.0)
        ):
            rate = 1.0 / np.mean(frameIntervals[-nIdentical:])

    print("Measured refresh rate")
    print(
        "%f +- %f (mean +- 1 SD)"
        % (
            1.0 / (np.mean(frameIntervals[-nIdentical:])),
            np.std(1.0 / np.array(frameIntervals[-nIdentical:])),
        )
    )

    # setting threshold for dropped frames detection
    refreshThreshold = 1.0 / rate * 1.2

    ### Experiment setup ###
    # We are arranging circles and shapes around the screen, so it's helpful to
    # section the screen into eights and halves.
    whlf = wdth / 2.0
    hhlf = hght / 2.0
    wqtr = wdth / 4.0
    hqtr = hght / 4.0

    # We create a sinusoidal grating texture
    texsize = (256, 256)

    # timing and drawing 1000 frames
    nDroppedFrames = 0
    firsttimeon = True
    frameIntervals = []

    white = np.ones(texsize)
    black = np.zeros(texsize)
    
    tex_white = hrl.graphics.newTexture(white)
    tex_black = hrl.graphics.newTexture(black)
    
    Nframes = int(30 * rate)

    for i in range(Nframes):
        
        
        if i % 2 == 0 :
            # draw white
            tex_white.draw(pos=(0, hght - texsize[1]), sz=texsize)
        else:
            tex_black.draw(pos=(0, hght - texsize[1]), sz=texsize)

        
        # flip
        hrl.graphics.flip(clr=True)

        # timing
        frameTime = defaultClock.getTime()

        if firsttimeon:
            firsttimeon = False
            lastFrameT = frameTime

        else:
            deltaT = frameTime - lastFrameT
            lastFrameT = frameTime
            frameIntervals.append(deltaT)

            # throw warning if dropped frame
            if deltaT > refreshThreshold:
                nDroppedFrames += 1
                txt = "t of last frame was %.2f ms (=1/%i)"
                msg = txt % (deltaT * 1000, 1.0 / deltaT)
                print(msg)

    print("")
    print("total number of dropped frames %d" % nDroppedFrames)
    print("")
    print("Interpretation:")
    print(
        """
    To have 1 and only 1 dropped frame is NORMAL.

    To have more than 1 dropped frame is NOT NORMAL.
    It might mean that there is something wrong the graphic card settings or
    graphic card's driver. You should check that synchronizing
    to VSYNC is enabled."""
    )

    timestr = time.strftime("%Y%m%d-%H%M%S")

    with open("%s.txt" % timestr, "w") as f:
        for t in frameIntervals:
            f.write("%f\n" % t)


### Run Main ###
if __name__ == "__main__":
    main()
