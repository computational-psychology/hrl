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

inlab = True if "vlab" in gethostname() else False


import clock
defaultClock = clock.monotonicClock


def makeGaussian(size, fwhm = 3, center=None):
    """ Make a square gaussian kernel.

    size is the length of a side of the square
    fwhm is full-width-half-maximum, which
    can be thought of as an effective radius.
    """

    x = np.arange(0, size, 1, float)
    y = x[:,np.newaxis]

    if center is None:
        x0 = y0 = size // 2
    else:
        x0 = center[0]
        y0 = center[1]

    return np.exp(-4*np.log(2) * ((x-x0)**2 + (y-y0)**2) / fwhm**2)


def normalize(v, endrange=(0,1)):
    mx = v.max()
    mm = v.min()
    
    n = (v - mm)/(mx-mm)
    r = endrange[1]-endrange[0]
        
    return (n*r+endrange[0])
    
### Main ###
def main():


    ### HRL Parameters ###
    # Here we define all the paremeters required to instantiate an HRL object.

    # Which devices we wish to use in this experiment. See the
    # pydoc documentation for a list of # options.
    if inlab:
        graphics='datapixx' 
        inputs='responsepixx'
        scrn=1
        fs = True  # fullscreen 
    else:
        graphics='gpu' # 'datapixx' is another option
        inputs='keyboard' # 'responsepixx' is another option
        scrn=1
        fs = False # not fullscreen: windowed
        
    photometer=None

    # Screen size
    wdth = 1024
    hght = 768
    
    # background value
    bg = 0.3
    

    # Pass this to HRL if we want to use gamma correction.
    lut = 'lut.csv'

    # Create the hrl object with the above fields. All the default argument names are
    # given just for illustration.
    hrl = HRL(graphics=graphics,inputs=inputs,photometer=photometer
            ,wdth=wdth,hght=hght,bg=bg,fs=fs,scrn=scrn)

    ### measuring frame rate
    nIdentical=10
    nMaxFrames=100
    nWarmUpFrames=10
    threshold=1
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
                            
        if (len(frameIntervals) >= nIdentical and
                (np.std(frameIntervals[-nIdentical:]) <(threshold / 1000.0))):
            rate = 1.0 / np.mean(frameIntervals[-nIdentical:])
            
    print("Measured refresh rate")
    print("%f +- %f (mean +- 1 SD)" % (1.0/(np.mean(frameIntervals[-nIdentical:])), np.std(1.0/np.array(frameIntervals[-nIdentical:]))))

    # setting threshold for dropped frames detection
    refreshThreshold = 1.0 / rate * 1.2

    ### Experiment setup ###
    # We are arranging circles and shapes around the screen, so it's helpful to
    # section the screen into eights and halves.
    whlf = wdth/2.0
    hhlf = hght/2.0
    wqtr = wdth/4.0
    hqtr = hght/4.0

    # We create a sinusoidal grating texture
    texsize = (256, 256)
    
    contrast = 0.4
    
    gauss =  normalize(makeGaussian(texsize[0], fwhm = 80, center=(128, 128)))
    
    
    # timing and drawing 100 frames
    nDroppedFrames = 0
    firsttimeon = True
    frameIntervals = []

    for i in range(1000):    
        s = normalize(np.sin(np.linspace(0, 10*pi, texsize[0])+i))
        grating1 = np.tile(s, (texsize[1], 1))
        
        s = normalize(np.sin(np.linspace(0, 20*pi, texsize[0])+i))
        grating2 = np.tile(s, (texsize[1], 1))
        
        gabor1 = normalize(grating1 * gauss, (bg, bg+contrast))
        gabor2 = normalize(grating2 * gauss, (bg, bg+contrast))
       
        # draw to texture
        tex1 = hrl.graphics.newTexture(gabor1)
        tex1.draw(pos=(wqtr-texsize[0]/2.0, hhlf-texsize[1]/2.0), sz=texsize)

        tex2 = hrl.graphics.newTexture(gabor2)
        tex2.draw(pos=(3*wqtr-texsize[0]/2.0, hhlf-texsize[1]/2.0), sz=texsize, rot=90)
        
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
                txt = 't of last frame was %.2f ms (=1/%i)'
                msg = txt % (deltaT * 1000, 1.0/ deltaT)
                print(msg)
        

    print("total number of dropped frames %d" % nDroppedFrames)
    
    timestr = time.strftime("%Y%m%d-%H%M%S")
    
    with open('%s.txt' % timestr, 'w') as f:
        for t in frameIntervals:
            f.write("%f\n" % t)
    

### Run Main ###
if __name__ == '__main__':
    main()
