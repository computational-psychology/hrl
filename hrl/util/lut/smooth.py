### Imports ###

import numpy as np
import argparse as ap
import scipy as sp

### Argument parser ###

prsr = ap.ArgumentParser(
    prog="hrl-util lut smooth",
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
    """,
)

prsr.add_argument(
    "-o",
    dest="ordr",
    default=0,
    type=int,
    help="The number of times (order) to smooth the data. Default: 0 (no smoothing, just averaging",
)


### Core ###


def smooth(args):
    args = prsr.parse_args(args)

    # Create the average table
    hshmp = {}
    fls = ["measure.csv"]
    tbls = [np.genfromtxt(fl, skip_header=1) for fl in fls]
    # First we build up a big intensity to luminance map
    for tbl in tbls:
        for rw in tbl:
            if rw[0] in hshmp:
                hshmp[rw[0]] = np.concatenate([hshmp[rw[0]], rw[1:]])
            else:
                hshmp[rw[0]] = rw[1:]

    # Now we average the values, clearing all nans from the picture.
    for ky in hshmp.keys():
        values = hshmp[ky][~np.isnan(hshmp[ky])]
        # set outliers to NaN. Outliers are values that are more than 0.05 cd
        # or more than 0.5% of their value from the closest measurement at the
        # same intensity.
        min_diff = np.empty_like(values)
        for i in range(len(values)):
            idx = np.ones(len(values), dtype=bool)
            idx[i] = False
            min_diff[i] = np.min(np.abs(values[idx] - values[i]))
        values[(min_diff > 0.075) & (min_diff / values > 0.0075)] = np.NaN
        hshmp[ky] = np.mean(values[np.isnan(values) == False])
        if np.isnan(hshmp[ky]):
            raise RuntimeError("no valid measurement for %f" % ky)
    tbl = np.array([list(hshmp.keys()), list(hshmp.values())]).transpose()
    tbl = tbl[tbl[:, 0].argsort()]
    print(tbl.shape)

    # And smooth it
    krn = [0.2, 0.2, 0.2, 0.2, 0.2]
    wfl = "smooth.csv"

    smthd = tbl[:, 1]

    for i in range(args.ordr):
        smthd = np.hstack((np.ones(2) * smthd[0], smthd, np.ones(2) * smthd[-1]))
        smthd = sp.convolve(smthd, krn, "valid")

    print("Saving to File...")
    tbl[:, 1] = smthd
    ofl = open(wfl, "w")
    ofl.write("Input Luminance\r\n")
    np.savetxt(ofl, tbl)
    ofl.close()
