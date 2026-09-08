import argparse
from pathlib import Path

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
parser.add_argument(
    "-i",
    "--in_file",
    default="smooth.csv",
    type=Path,
    help="path to input measurements csv, by default 'smooth.csv'",
)
parser.add_argument(
    "-o",
    "--out_file",
    default="lut.csv",
    type=Path,
    help="path for output csv, by default 'lut.csv'",
)


def command(parsed_args):
    """Sample a linear subset of the gamma table"""

    # Load (smoothed) LUT
    in_file = parsed_args.in_file.expanduser().resolve()
    print(f"Loading measurements from {in_file} ...")
    measurements = np.genfromtxt(in_file, delimiter=",", skip_header=1)

    # Linearize LUT
    linearized_lut = hrl.calibration.measurement.linearize(
        measurements, bit_depth=parsed_args.bit_depth
    )

    # Write to file
    out_file = parsed_args.out_file.expanduser().resolve()
    print(f"Saving to {out_file} ...")
    headers = "intensity_in,intensity_out,luminance"
    np.savetxt(out_file, linearized_lut, delimiter=",", header=headers, comments="")


if __name__ == "__main__":
    command(parser.parse_args())
