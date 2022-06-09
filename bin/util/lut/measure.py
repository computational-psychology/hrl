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

# Timing
from timeit import default_timer as timer
from datetime import timedelta


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

prsr.add_argument('-p', dest='photometer', type=str, default='optical', help='The photometer to use. Default: optical')

prsr.add_argument('-o', dest='flnm', type=str, default='measure.csv', help='The output filename. Default: measure.csv')

prsr.add_argument('-bg', dest='bg', type=float, default=0.0, help='The background intensity outside of the central patch. Default: 0')

prsr.add_argument('-wd', dest='wd', type=int, default=1024, help='The screen resolution width, in pixels. It should coincide with the settings in xorg.conf. Default: 1024')

prsr.add_argument('-hg', dest='hg', type=int, default=768, help='The screen resolution height, in pixels. It should coincide with the settings in xorg.conf. Default: 768')

prsr.add_argument('-gr', dest='graphics', type=str, default='datapixx', help='Whether using the GPU (gpu) or the DataPixx interface (datapixx). Default: datapixx')

prsr.add_argument('-sc', dest='scrn', type=str, default='1', help='Screen number. Default: 1')

prsr.add_argument('-wo', dest='wdth_offset', type=int, default=0, help='Horizontal offset for window. Useful for setups with a single Xscreen but multiple monitors (Xinerame). Default: 0')


# Settings (these can all be changed with system arguments)

def measure(args):

    args = prsr.parse_args(args)

    wdth = args.wd
    hght = args.hg
    
    # Starting timer
    start = timer()
    
    # Initializing HRL
    flnm = args.flnm
    flds = ['Intensity'] + [ 'Luminance' + str(i) for i in range(args.nsmps) ]

    graphics = args.graphics
    inputs = 'keyboard'
    photometer = args.photometer
    scrn = args.scrn
    bg = args.bg
    wdth_offset = args.wdth_offset


    hrl = HRL(graphics=graphics,inputs=inputs,photometer=photometer,
              wdth=wdth, hght=hght, bg=bg, fs=True,
              wdth_offset=wdth_offset, db=True, scrn=scrn,
              rfl=flnm, rhds=flds)

    itss = np.linspace(args.mn,args.mx,args.stps)
    if args.rndm: shuffle(itss)
    if args.rvs: itss = itss[::-1]

    (pwdth,phght) = (wdth*args.sz,hght*args.sz)
    ppos = ((wdth - pwdth)/2,(hght - phght)/2)
    print(pwdth)
    print(ppos)
    print(phght)

    done = False
    
    c=0

    for its in itss:
        c+=1
        hrl.results['Intensity'] = its

        ptch = hrl.graphics.newTexture(np.array([[its]]))
        ptch.draw(ppos,(pwdth,phght))
        hrl.graphics.flip()

        print('Current Intensity: %f / progress: %d of %d' % (its, c, args.stps))
        smps = []
        for i in range(args.nsmps):
            smps.append(hrl.photometer.readLuminance(5,args.slptm))

        for i in range(len(smps)):
            hrl.results['Luminance' + str(i)] = smps[i]

        hrl.writeResultLine()

        if hrl.inputs.checkEscape(): break

    # Experiment is over!
    hrl.close()
    
    # stop timer
    end = timer()
    
    # Time elapsed
    print('Time elapsed:')
    print(timedelta(seconds=end-start))



if __name__ == '__main__':
    main()
