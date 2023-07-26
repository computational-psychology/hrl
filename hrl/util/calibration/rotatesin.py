#!/usr/bin/env python

### Imports ###

import argparse as ap
import sys
from random import shuffle

import numpy as np

# Qualified Imports
import pygame as pg
from OpenGL.GL import *

# Unqualified Imports
from pygame.locals import *

# Package Imports
from hrl import *

# Argument parser
prsr = ap.ArgumentParser(
    description=(
        "Implementation of Felix test 3. This script holds a square in the middle of the screen"
        " with a fixed background luminance. The square depicts a square wave, which is rotated 90"
        " degrees at a given frequency. Escape can be pressed while the program is running in"
        " order to cancel execution and save the results accumulated so far."
    )
)

prsr.add_argument(
    "flnm",
    default="rotatesin.csv",
    nargs="?",
    help=(
        "The filename of the file where the results will be stored in the results directory."
        " Default: rotatesin.csv"
    ),
)

prsr.add_argument(
    "-sz",
    dest="sz",
    default=0.3,
    type=float,
    help="The size of the central patch, as a fraction of the total screen size. Default: 0.3",
)

prsr.add_argument(
    "-sc",
    dest="scyc",
    default=1,
    type=int,
    help="The number of spatial cycles of the square wave. Default: 1",
)

prsr.add_argument(
    "-tf",
    dest="tfrq",
    default=10.0,
    type=float,
    help="The temporal frequency in Hz of the rotation operation. Default: 10.0",
)

prsr.add_argument(
    "-cs",
    dest="ctst",
    default=1.0,
    type=float,
    help="The contrast of the square wave. Between 0 and 1. Default: 1.0",
)

prsr.add_argument(
    "-lm", dest="lm", default=0.5, type=float, help="The background luminance. Default: 0.5"
)

# prsr.add_argument('-sl',dest='sln',default=10,type=int,help='How often do we sample the luminance, in terms of \'frame wavelength\' i.e. how many frames do we skip between measurements. 0 indicates a measurement after every rotation. Default: 10')

prsr.add_argument(
    "-pw",
    dest="pwt",
    default=2,
    type=int,
    help=(
        "The number of milliseconds the computer waits when making an OptiCAL measurement. Small"
        " values cause less of a delay, but may lead to exceptions. Default: 2"
    ),
)

prsr.add_argument(
    "-n",
    dest="ncyc",
    default=200,
    type=int,
    help="The number of cycles to run the experiment. Default: 200",
)

# Settings (these can all be changed with system arguments)


def main():
    wdth = 1024
    hght = 768
    flds = ["Luminance"]
    args = prsr.parse_args()
    flnm = "results/" + args.flnm

    # Initializations
    hrl = HRL(
        wdth,
        hght,
        args.lm,
        coords=(0, 1, 0, 1),
        flipcoords=False,
        dpx=True,
        ocal=True,
        rfl=flnm,
        rhds=flds,
        fs=True,
    )

    sqrwv = lambda x: args.ctst * round((np.sin(2 * np.pi * x) + 1) / 2) + (0.5 - args.ctst / 2)

    pwdth, phght = int(wdth * args.sz), int(hght * args.sz)
    ppos = ((wdth - pwdth) / 2, (hght - phght) / 2)

    sqrwv1 = np.array([[sqrwv(x)] for x in np.linspace(0, args.scyc, phght, endpoint=False)])
    sqrwv2 = np.array([[sqrwv(x) for x in np.linspace(0, args.scyc, pwdth, endpoint=False)]])

    ptch1 = hrl.newTexture(sqrwv1)
    ptch2 = hrl.newTexture(sqrwv2)

    slptm = int(1000.0 / args.tfrq)
    print(slptm)

    for i in range(args.ncyc):
        ptch1.draw(ppos, (pwdth, phght))
        hrl.flip()
        hrl.rmtx["Luminance"] = hrl.readLuminance(1, 0)
        hrl.writeResultLine()

        pg.time.wait(slptm)

        ptch2.draw(ppos, (pwdth, phght))
        hrl.flip()
        hrl.rmtx["Luminance"] = hrl.readLuminance(1, 0)
        hrl.writeResultLine()

        pg.time.wait(slptm)

        if hrl.checkEscape():
            break

    # Experiment is over!
    hrl.close()


if __name__ == "__main__":
    main()
