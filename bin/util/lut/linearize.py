### Imports ###

import numpy as np
import argparse as ap
import scipy as sp

### Argument parser ###

prsr = ap.ArgumentParser(prog="hrl-util lut linearize",
    description="""
    This script takes the result of hrl-util lut smooth, i.e. smooth.csv,
    and linearly subsamples the luminance axis at a given resolution.
    
    The script saves the results in 'lut.csv'. The column 'IntensityIn' defines a
    new intensity function which linearly increases luminance. This is the
    final step in generating a look up table.
    """)

prsr.add_argument('-r',dest='res',default=12,type=int,
        help='The subsampling resoultion in bits. Default: 12')

### Core ###

def linearize(args):

    args = prsr.parse_args(args)

    # Sample a linear subset of the gamma table
    tbl = np.genfromtxt('smooth.csv',skip_header=1)
    idx = 0
    idxs = []
    itss = tbl[:,0]
    lmns = tbl[:,1]
    for smp in np.linspace(np.min(lmns),np.max(lmns),2**args.res):
        #while smp > lmns[idx]: idx += 1
        idx = np.nonzero(lmns >= smp)[0][0]
        idxs.append(idx)
    ofl = open('lut.csv','w')
    ofl.write('IntensityIn IntensityOut Luminance\r\n')
    rslt = np.array([np.linspace(0,1,2**args.res),itss[idxs],lmns[idxs]]).transpose()

    print 'Saving to File...'

    np.savetxt(ofl,rslt)
    ofl.close()
    #return lambda x: np.interp(x,np.linspace(0,1,2**args.res),itss[idxs])
