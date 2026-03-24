import argparse

import numpy as np

import hrl.calibration.measurement
from hrl.util.lut import intensities_argparser

parser = argparse.ArgumentParser(
    prog="linearize",
    description="""
    This script takes the result of hrl-util lut smooth, i.e. smooth.csv,
    and linearly subsamples the luminance axis at a given resolution.

    The script saves the results in 'lut.csv'. The column 'intensity_in' defines a
    new intensity function which linearly increases luminance. This is the
    final step in generating a look up table.
    """,
    add_help=False,
    parents=[intensities_argparser],
)


def command(parsed_args):
    """Sample a linear subset of the gamma table"""
    n_steps = 2**parsed_args.bit_depth

    # Load (smoothed) LUT
    lut = np.genfromtxt("smooth.csv", skip_header=1, delimiter=",")

    # Linearize LUT
    linearized_lut = hrl.calibration.measurement.linearize(lut, bit_depth=parsed_args.bit_depth)

    # Save linearized LUT to file
    print("Saving to File...")
    out_file = open("lut.csv", "w")
    headers = "intensity_in,intensity_out,luminance\n"
    out_file.write(headers)
    np.savetxt(out_file, linearized_lut, delimiter=",")
    out_file.close()


if __name__ == "__main__":
    command(parser.parse_args())
