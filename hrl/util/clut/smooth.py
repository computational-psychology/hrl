import argparse
from pathlib import Path

import numpy as np

import hrl.cluts

parser = argparse.ArgumentParser(
    prog="smooth",
    description="""
    Process CLUT measurements by removing outliers and averaging repeated
    RGB triplet samples, and save the result to 'smooth.csv'.

    NOTE: Unlike grayscale LUT processing, no kernel smoothing is currently
    applied for CLUTs; this command performs robust averaging only.
    """,
    add_help=False,
)
parser.add_argument(
    "-i",
    "--in_file",
    default="measure.csv",
    type=Path,
    nargs="+",
    help="path(s) for input measurement csv(s), by default 'measure.csv'",
)
parser.add_argument(
    "-o",
    "--out_file",
    default="smooth.csv",
    type=Path,
    help="path for output processed measurements csv, by default 'smooth.csv'",
)


def command(parsed_args):
    measurements = []
    in_files = parsed_args.in_file
    if isinstance(in_files, (str, Path)):
        in_files = [in_files]
    for file in in_files:
        filename = file.expanduser().resolve()
        print(f"Loading from {filename} ...")
        measurements.append(np.genfromtxt(filename, delimiter=",", skip_header=1))
    measurements = np.vstack(measurements)

    measurements = hrl.cluts.remove_outliers(measurements)
    measurements = hrl.cluts.average(measurements)

    out_file = parsed_args.out_file.expanduser().resolve()
    print(f"Saving to {out_file}...")
    header = "R,G,B,X,Y,Z"
    np.savetxt(out_file, measurements, delimiter=",", header=header, comments="")


if __name__ == "__main__":
    command(parser.parse_args())
