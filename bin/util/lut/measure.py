### Imports ###

# Package Imports
from hrl import HRL

# Qualified Imports
import numpy as np
import sys
import argparse as ap
import os

# Unqualified Imports
from random import shuffle


# Argument parser
prsr = ap.ArgumentParser(prog="hrl-util lut measure",
    description="""
    This script measures the relationship between the desired intensity (a
    normalized value between 0 and 1) given to the monitor, and the luminance
    produced by the monitor, and saves it to the file 'measure.csv'. This is
    the first step in generating a lookup table for normalizing a monitor's
    luminance.
    """)

prsr.add_argument('-sz',dest='sz',default=0.5,type=float,help='The size of the central patch, as a fraction of the total screen size. Default: 0.5')

prsr.add_argument('-s',dest='stps',default=65536,type=int,help='The number of unique intensity values to be sampled. Default: 65536')

prsr.add_argument('-mn',dest='mn',default=0.0,type=float,help='The minimum sampled intensity. Default: 0.0')

prsr.add_argument('-mx',dest='mx',default=1.0,type=float,help='The maximum sampled intensity. Default: 1.0')

prsr.add_argument('-n',dest='nsmps',default=5,type=int,help='The number of samples to be taken at each intensity. Default: 5')

prsr.add_argument('-sl',dest='slptm',default=200,type=int,help='The number of milliseconds to wait between each measurement. Default:200')

prsr.add_argument('-r',dest='rndm',action='store_true',help='Shall we randomize the order of intensity values? Default: False')

prsr.add_argument('-v',dest='rvs',action='store_true',help='Shall we reverse the order of intensity values (high to low rather than low to high)? Default: False')

# Settings (these can all be changed with system arguments)

def measure(args):
    
    args = prsr.parse_args(args)

    wdth = 1024
    hght = 768

    # Initializing HRL

    flnm = 'measure.csv'
    flds = ['Intensity'] + [ 'Luminance' + str(i) for i in range(args.nsmps) ]

    graphics = 'datapixx'
    inputs = 'keyboard'
    photometer = 'optical'

    fs = True

    hrl = HRL(graphics=graphics,inputs=inputs,photometer=photometer
            ,wdth=wdth,hght=hght,bg=0,rfl=flnm,rhds=flds,fs=fs,scrn=1)

    itss = np.linspace(args.mn,args.mx,args.stps)
    if args.rndm: shuffle(itss)
    if args.rvs: itss = itss[::-1]

    (pwdth,phght) = (wdth*args.sz,hght*args.sz)
    ppos = ((wdth - pwdth)/2,(hght - phght)/2)
    print pwdth
    print ppos
    print phght

    done = False

    for its in itss:

        hrl.results['Intensity'] = its

        ptch = hrl.graphics.newTexture(np.array([[its]]))
        ptch.draw(ppos,(pwdth,phght))
        hrl.graphics.flip()

        print 'Current Intensity:', its
        smps = []
        for i in range(args.nsmps):
            smps.append(hrl.photometer.readLuminance(5,args.slptm))

        for i in range(len(smps)):
            hrl.results['Luminance' + str(i)] = smps[i]

        hrl.writeResultLine()

        if hrl.inputs.checkEscape(): break

    # Experiment is over!
    hrl.close()


if __name__ == '__main__':
    main()
