import os
import sys
import time

import numpy as np
from hrl import HRL
from hrl.graphics import graphics

WIDTH = 1024
HEIGHT = 768

# size of the rectangular patch
sz = 0.5

# size and position of rectangular patch
pwdth, phght = WIDTH * sz, HEIGHT * sz
ppos = (WIDTH - pwdth) / 2, (HEIGHT - phght) / 2
    
# number of intensities to be measured
N = 10        
            
    
def show_stim(hrl, intensity):
    
    # texture creation in buffer : stimulus
    ptch = hrl.graphics.newTexture(np.array([[intensity]]))

    # Show stimlus
    ptch.draw(ppos, (pwdth, phght))

    # flip everything
    hrl.graphics.flip(clr=True)  # clr= True to clear buffer


def run_block(hrl):
    
    # intensity vector
    intensities = np.linspace(0, 1, N)
    # randomize in place
    np.random.shuffle(intensities)
        
    for intensity in intensities:
        
        # show rectangle
        show_stim(hrl, intensity)
        
        # read photometer
        lum = hrl.photometer.readLuminance()
        #time.sleep(1)
        #lum = 0.0
        
        print(f"Intensity {intensity:.2f} - Luminance {lum:.2f}")       
      

    print("Done")


def run_experiment():

    hrl = HRL(
        graphics="gpu",
        inputs="keyboard",
        photometer='i1pro',
        wdth=WIDTH,
        hght=HEIGHT,
        bg=0.5,
        scrn=0,
        lut=None,
        db=True,
        fs=False,
    )

    run_block(hrl)


if __name__ == "__main__":
    run_experiment()
