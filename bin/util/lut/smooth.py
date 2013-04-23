### Imports ###

import numpy as np
import argparse as ap
import scipy as sp

### Argument parser ###

prsr = ap.ArgumentParser(prog="hrl-util lut smooth",
    description="""
    This script applies a kernel smoothing algorithm to the data contained in
    the file 'measure.csv' and generates 'smooth.csv' as a result.

    The first part of this script gathers the given data into an array, clear
    out useless rows, and average points at the same intensity. The second part
    uses a simple smoothing kernel to fit the gamma function.

    A critical part of applying this function is to make sure that the data set
    has been evenly sampled across the intensity range, as internally the
    algorithm has no idea how far apart in intensity each sample is, and
    implicitly assumes each step size to be the same.

    Right now the kernel can be directly changed but it looks like this:
    [0.2,0.2,0.2,0.2,0.2]. Use the other parameters to experiment with
    different smoothing parameters.
    """)

prsr.add_argument('-o',dest='ordr',default=5,type=int,
        help="The number of times (order) to smooth the data. Default: 5")

prsr.add_argument('-c',dest='corr',default=20,type=int,
        help='The number of points at the end of the dataset used to estimate the correcting scaling factor. Default: 20')

### Core ###

def smooth(args):

    args = prsr.parse_args(args)

    # Create the average table
    hshmp = {}
    fls = ['measure.csv']
    tbls = [ np.genfromtxt(fl,skip_header=1) for fl in fls ]
    # First we build up a big intensity to luminance map
    for tbl in tbls:
        for rw in tbl:
            if hshmp.has_key(rw[0]):
                hshmp[rw[0]] = np.concatenate([hshmp[rw[0]],rw[1:]])
            else:
                hshmp[rw[0]] = rw[1:]
    # Now we average the values, clearing all nans from the picture.
    for ky in hshmp.keys():
        hshmp[ky] = np.mean(hshmp[ky][np.isnan(hshmp[ky]) == False])
        if np.isnan(hshmp[ky]): hshmp.pop(ky)
    tbl = np.array([hshmp.keys(),hshmp.values()]).transpose()
    tbl = tbl[tbl[:,0].argsort()]

    # And smooth it
    krn=[0.2,0.2,0.2,0.2,0.2]
    wfl='smooth.csv'

    xsmps = tbl[:,0]
    ysmps = tbl[:,1]
    smthd = ysmps

    for i in range(args.ordr): smthd = sp.convolve(smthd,krn)
    smthd = smthd[:len(ysmps)]
    mn = min(ysmps)
    def fun(x):
        if x < mn:
            return mn
        else:
            return x
    smthd = map(fun,smthd)
    smthd *= 1 + (np.mean(ysmps[-args.corr:]) -
            np.mean(smthd[-args.corr:]))/np.mean(smthd[-args.corr:])

    print 'Saving to File...'
    rslt = np.array([xsmps,smthd]).transpose()
    ofl = open(wfl,'w')
    ofl.write('Input Luminance\r\n')
    np.savetxt(ofl,rslt)
    ofl.close()
