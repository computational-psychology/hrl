import argparse
from pathlib import Path

import numpy as np

import hrl.cluts.calibrate

parser = argparse.ArgumentParser(
    prog="linearize",
    description="""
    This script takes processed CLUT measurements (e.g. smooth.csv)
    and creates a linearized CLUT at the requested resolution.

    The script saves the result in 'clut.csv'.
    """,
    add_help=False,
)
parser.add_argument(
    "-b",
    "--bit_depth",
    type=int,
    default=8,
    help="resolution of the CLUT, in bits, by default 8 -> 2**8 = 256 input levels",
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
    default="clut.csv",
    type=Path,
    help="path for output csv, by default 'clut.csv'",
)


def command(parsed_args):
    in_file = parsed_args.in_file.expanduser().resolve()
    print(f"Loading measurements from {in_file} ...")
    measurements, _ = hrl.cluts.calibrate.read_measurements(in_file)

    linearized_clut = hrl.cluts.calibrate.linearize(measurements, bit_depth=parsed_args.bit_depth)

    out_file = parsed_args.out_file.expanduser().resolve()
    print(f"Saving to {out_file} ...")
    headers = "intensity_in,R_out,G_out,B_out,R_X,R_Y,R_Z,G_X,G_Y,G_Z,B_X,B_Y,B_Z"
    np.savetxt(out_file, linearized_clut, delimiter=",", header=headers, comments="")


if __name__ == "__main__":
    command(parser.parse_args())
