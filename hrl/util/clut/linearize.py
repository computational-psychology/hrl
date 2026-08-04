import argparse
from pathlib import Path

import numpy as np

import hrl.cluts
from hrl.util.clut import triplets_argparser

parser = argparse.ArgumentParser(
    prog="linearize",
    description="""
    This script takes processed CLUT measurements (e.g. smooth.csv)
    and creates a linearized CLUT at the requested resolution.

    The script saves the result in 'clut.csv'.
    """,
    add_help=False,
    parents=[triplets_argparser],
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
    measurements = np.genfromtxt(in_file, delimiter=",", skip_header=1)

    linearized_clut = hrl.cluts.linearize(measurements, bit_depth=parsed_args.bit_depth)

    out_file = parsed_args.out_file.expanduser().resolve()
    print(f"Saving to {out_file} ...")
    headers = "intensity_in,R_out,G_out,B_out,X_R,X_G,X_B,Y_R,Y_G,Y_B,Z_R,Z_G,Z_B"
    np.savetxt(out_file, linearized_clut, delimiter=",", header=headers, comments="")


if __name__ == "__main__":
    command(parser.parse_args())
