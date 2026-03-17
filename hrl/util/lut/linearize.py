import argparse

import numpy as np

parser = argparse.ArgumentParser(
    prog="hrl-util lut linearize",
    description="""
    This script takes the result of hrl-util lut smooth, i.e. smooth.csv,
    and linearly subsamples the luminance axis at a given resolution.

    The script saves the results in 'lut.csv'. The column 'intensity_in' defines a
    new intensity function which linearly increases luminance. This is the
    final step in generating a look up table.
    """,
)

parser.add_argument(
    "-b",
    "--bit_depth",
    default=16,
    type=int,
    help="Subsampling resolution (in bits), by default 16 -> 2**16 = 65536 levels",
)


def command(args):
    """Sample a linear subset of the gamma table"""
    parsed_args = parser.parse_args(args)

    n_steps = 2**parsed_args.bit_depth

    # Load (smoothed) LUT
    lut = np.genfromtxt("smooth.csv", skip_header=1, delimiter=",")
    intensities = lut[:, 0]
    luminances = lut[:, 1]

    idx = 0
    idxs = []
    smpl_idx = np.zeros(n_steps, dtype=bool)
    for i, smp in enumerate(np.linspace(np.min(luminances), np.max(luminances), n_steps)):
        idx = np.nonzero(luminances >= smp)[0][0]
        if not len(idxs) or (idx != idxs[-1]):
            smpl_idx[i] = True
            idxs.append(idx)
    linearized_lut = np.array(
        [np.linspace(0, 1, n_steps)[smpl_idx], intensities[idxs], luminances[idxs]]
    ).transpose()

    # Save linearized LUT to file
    print("Saving to File...")
    out_file = open("lut.csv", "w")
    headers = "intensity_in,intensity_out,luminance\n"
    out_file.write(headers)
    np.savetxt(out_file, linearized_lut, delimiter=",")
    out_file.close()

    # return lambda x: np.interp(x,np.linspace(0,1,2**parsed_args.res),intensities[idxs])
