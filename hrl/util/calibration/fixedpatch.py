#!/usr/bin/env python

### Imports ###

import argparse as ap
import sys
from multiprocessing import Process
from random import shuffle

import numpy as np

# Qualified Imports
import pygame as pg
from OpenGL.GL import *

# Unqualified Imports
from pygame.locals import *

# Package Imports
from hrl import HRL

# Argument parser
prsr = ap.ArgumentParser(
    description=(
        "Implementation of Felix test 2. This script holds a square in the middle of the screen at"
        " a fixed luminance, while oscillating the background luminance. Luminance should be"
        " measured at the central square. Ideally, the recorded luminance would not change, but it"
        " is unlikely that this will actually be case. Escape can be pressed while the program is"
        " running in order to cancel execution and save the results accumulated so far."
    )
)

prsr.add_argument(
    "flnm",
    default="fixedpatch.csv",
    nargs="?",
    help=(
        "The filename of the file where the results will be stored in the results directory."
        " Default: fixedpatch.csv"
    ),
)

prsr.add_argument(
    "-lm",
    dest="lm",
    default=0.5,
    type=float,
    help="The luminance of the central patch. Default: 0.5",
)

prsr.add_argument(
    "-sz",
    dest="sz",
    default=0.3,
    type=float,
    help="The size of the central patch, as a fraction of the total screen size. Default: 0.3",
)

prsr.add_argument(
    "-bf",
    dest="bfrq",
    default=0.1,
    type=float,
    help=(
        "The frequency of background oscilliation (in Hz), and the base frequency of sampling with"
        " the luminance device. Default: 0.1"
    ),
)

prsr.add_argument(
    "-ba",
    dest="bamp",
    default=1.0,
    type=float,
    help="The amplitude of background oscilliation (from 0 to 1). Default: 1.0",
)

prsr.add_argument(
    "-sf",
    dest="sfrq",
    default=10,
    type=int,
    help="The number of measurements to attempt within each cycle of the oscillation. Default: 10",
)

prsr.add_argument(
    "-tr",
    dest="tmprs",
    default=130,
    type=int,
    help=(
        "The temporal resolution of the background oscillation, in units of number of redraws per"
        " second. Note that if the base frequency does not evenly divide into the temporal"
        " resolution, the length of the cycle will be rounded. Default: 130"
    ),
)

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

prsr.add_argument(
    "-r",
    dest="rnd",
    action="store_true",
    help="Shall we round the sin wave into a square wave? Default: False",
)

prsr.add_argument(
    "-p",
    dest="photometer",
    type=str,
    default="optical",
    help="The photometer to use. Default: optical",
)

# Settings (these can all be changed with system arguments)

def main():
    wdth = 1024
    hght = 768
    flds = ["Intensity", "Luminance"]
    args = prsr.parse_args()
    flnm = "results/" + args.flnm

    hrl = HRL(
        graphics = "gpu",  # 'datapixx' is another option
        inputs = "keyboard",  # 'responsepixx' is another option
        scrn = 0,
        wdth = wdth,
        hght = hght,
        #coords=(0, 1, 0, 1),
        #flipcoords=False,
        #dpx=True,
        #photometer=None,
        photometer=args.photometer,
        rfl=flnm,
        rhds=flds,
        fs=True,
    )
    # Initializations

    ptch = hrl.graphics.newTexture(np.array([[args.lm]]))
    pwdth, phght = wdth * args.sz, hght * args.sz
    ppos = ((wdth - pwdth) / 2, (hght - phght) / 2)

    if args.rnd:
        rnd = round
    else:
        rnd = lambda x: x

    nitss = int(args.tmprs / args.bfrq)
    itss = [
        args.bamp * rnd((1 + np.sin(2 * np.pi * x)) / 2) + ((1 - args.bamp) / 2)
        for x in np.linspace(0, 1, nitss)
    ]
    tsts = [n % (nitss / args.sfrq) == 0 for n in range(nitss)]
    cycl = list(zip(itss, tsts))
    slptm = int(1000.0 / args.tmprs)

    def opticalRead(its):
        print(f"Current Intensity: {its}")
        #lm = hrl.photometer.readLuminance(1, 0)
        lm = 0.0
        hrl.results["Intensity"] = its
        hrl.results["Luminance"] = lm
        hrl.writeResultLine()

    for its, tst in cycl * args.ncyc:
        hrl.graphics.changeBackground(its)
        ptch.draw(ppos, (pwdth, phght))
        hrl.graphics.flip()

        pg.time.wait(slptm)

        if tst:
            prcs = Process(target=opticalRead, args=(its,))
            prcs.start()

        if hrl.inputs.checkEscape():
            break

    # Experiment is over!
    hrl.close()


if __name__ == "__main__":
    main()
