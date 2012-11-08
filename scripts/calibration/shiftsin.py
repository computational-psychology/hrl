### Imports ###

# Package Imports
from hrl import HRL

# Qualified Imports
import pygame as pg
import numpy as np
import sys
import argparse as ap

# Unqualified Imports
from pygame.locals import *
from OpenGL.GL import *
from random import shuffle


# Argument parser
prsr = ap.ArgumentParser(description= "Implementation of Felix test 4. This script holds a square in the middle of the screen with a fixed background luminance. The square depicts a sin wave, which is shifted back and forth with a phase of 180 degrees - superimposed the two waves have a luminance equal to that of the background. Performed at a high refresh rate, the result to the naked eye should be a uniform background. This is an excellent test of frame dropping. Escape can be pressed while the program is running in order to cancel execution and save the results accumulated so far.")

prsr.add_argument('-sz',dest='sz',default=1.0,type=float,help='The size of the central patch, as a fraction of the total screen size. Default: 1.0')

prsr.add_argument('-sc',dest='scyc',default=5,type=int,help='The number of spatial cycles of the wave. Default: 5')

prsr.add_argument('-tf',dest='tfrq',default=260.0,type=float,help='The temporal frequency in Hz of the applied phase shift. Default: 264.0')

prsr.add_argument('-n',dest='ncyc',default=2000,type=int,help='The number of cycles to run the experiment. Default: 2000')

# Settings (these can all be changed with system arguments)

def main():
    wdth = 1024
    hght = 768
    args = prsr.parse_args()

    # Initializations

    hrl = HRL(wdth,hght,0,dpx=True,ocal=True,fs=True)
    hrl = HRL(wdth,hght,0,coords=(0,1,0,1),flipcoords=False,dpx=True,ocal=True,fs=True)

    pwdth,phght = int(wdth*args.sz),int(hght*args.sz)
    ppos = ((wdth - pwdth)/2,(hght - phght)/2)

    wv1 = np.array([ [round((np.sin(x*np.pi*2) + 1)/2)] for x in
                       np.linspace(0,args.scyc,phght) ])

    wv2 = np.array([ [round((np.sin(x*np.pi*2 + np.pi) + 1)/2)] for x in
                       np.linspace(0,args.scyc,phght) ])

    ptch1 = hrl.newTexture(wv1)
    ptch2 = hrl.newTexture(wv2)

    slptm = int(1000.0 / args.tfrq)

    for i in range(args.ncyc):

        ptch1.draw(ppos,(pwdth,phght))
        hrl.flip()

        pg.time.wait(slptm)

        ptch2.draw(ppos,(pwdth,phght))
        hrl.flip()

        pg.time.wait(slptm)

        if hrl.checkEscape(): break

# Experiment is over!
    hrl.close()


if __name__ == '__main__':
    main()
