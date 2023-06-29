#!/usr/bin/env python

### Imports ###

import argparse as ap
import os
import sys

# Unqualified Imports
from random import shuffle

# Qualified Imports
import numpy as np

# Package Imports
from hrl import *

# Argument parser
prsr = ap.ArgumentParser(
    description=(
        "Implementation of Felix test 1.  This script runs across the entire luminance range,"
        " either normally, randomly, or reversedly. This is useful for calculating the Gamma"
        " function, and Hysterisis can be measured by running several tests and comparing them."
        " Escape can be pressed to cancel the program while it's running, and the results"
        " accumulated so far will be saved."
    )
)

prsr.add_argument(
    "flnm",
    default="gamma.csv",
    nargs="?",
    help=(
        "The filename of the file where the results will be stored in the results folder. Default:"
        " gamma.csv"
    ),
)

prsr.add_argument(
    "-sz",
    dest="sz",
    default=0.5,
    type=float,
    help="The size of the central patch, as a fraction of the total screen size. Default: 0.5",
)

prsr.add_argument(
    "-s",
    dest="stps",
    default=65536,
    type=int,
    help="The number of unique intensity values to be sampled. Default: 65536",
)

prsr.add_argument(
    "-mn", dest="mn", default=0.0, type=float, help="The minimum sampled intensity. Default: 0.0"
)

prsr.add_argument(
    "-mx", dest="mx", default=1.0, type=float, help="The maximum sampled intensity. Default: 1.0"
)

prsr.add_argument(
    "-t",
    dest="tst",
    default=None,
    type=str,
    help="Give a file name to test a given gamma table. Default: None",
)

prsr.add_argument(
    "-n",
    dest="nsmps",
    default=5,
    type=int,
    help="The number of samples to be taken at each intensity. Default: 5",
)

prsr.add_argument(
    "-sl",
    dest="slptm",
    default=200,
    type=int,
    help="The number of milliseconds to wait between each measurement. Default:200",
)

prsr.add_argument(
    "-a",
    dest="avg",
    action="store_true",
    help="Shall we average the samples at a particular intensity? Default: False",
)

prsr.add_argument(
    "-r",
    dest="rndm",
    action="store_true",
    help="Shall we randomize the order of intensity values? Default: False",
)

prsr.add_argument(
    "-v",
    dest="rvs",
    action="store_true",
    help=(
        "Shall we reverse the order of intensity values (high to low rather than low to high)?"
        " Default: False"
    ),
)

# Settings (these can all be changed with system arguments)


def main():
    wdth = 1024
    hght = 768
    args = prsr.parse_args()
    # Initializations

    flnm = "results/" + args.flnm
    if args.avg:
        flds = ["Intensity", "Luminance"]
    else:
        flds = ["Intensity"] + ["Luminance" + str(i) for i in range(args.nsmps)]

    hrl = HRL(
        wdth,
        hght,
        0,
        coords=(0, 1, 0, 1),
        flipcoords=False,
        dpx=True,
        ocal=True,
        rfl=flnm,
        rhds=flds,
        lut=args.tst,
        fs=True,
    )

    itss = np.linspace(args.mn, args.mx, args.stps)
    if args.rndm:
        shuffle(itss)
    if args.rvs:
        itss = itss[::-1]

    (pwdth, phght) = (wdth * args.sz, hght * args.sz)
    ppos = ((wdth - pwdth) / 2, (hght - phght) / 2)
    print(pwdth)
    print(ppos)
    print(phght)

    done = False

    for its in itss:
        hrl.rmtx["Intensity"] = its

        ptch = hrl.newTexture(np.array([[its]]))
        ptch.draw(ppos, (pwdth, phght))
        hrl.flip()

        print(f"Current Intensity: {its}")
        smps = []
        for i in range(args.nsmps):
            smps.append(hrl.readLuminance(5, args.slptm))

        if args.avg:
            smps = filter(lambda x: x != np.nan, smps)
            smp = np.mean(smps)
            hrl.rmtx["Luminance"] = smp

        else:
            for i in range(len(smps)):
                hrl.rmtx["Luminance" + str(i)] = smps[i]

        hrl.writeResultLine()

        if hrl.checkEscape():
            break

    # Experiment is over!
    hrl.close()


if __name__ == "__main__":
    main()
