import argparse
from pathlib import Path

import numpy as np

from hrl.cluts.calibrate import average, remove_outliers, smooth

parser = argparse.ArgumentParser(
    prog="smooth",
    description="""
    Process CLUT measurements: remove outliers, average repeated readings of each
    RGB triplet, and average each channel's readings over neighbouring input
    levels. Saves the result to 'smooth.csv', ready for 'linearize'.
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
parser.add_argument(
    "-w",
    "--width",
    default=5,
    type=int,
    help="how many neighbouring input levels to average over, by default 5; 1 disables",
)


def command(parsed_args):
    measurements = []
    for file in parsed_args.in_file:
        filename = file.expanduser().resolve()
        print(f"Loading from {filename} ...")
        measurements.append(np.genfromtxt(filename, delimiter=",", skip_header=1))
    measurements = np.vstack(measurements)

    measurements = remove_outliers(measurements)
    measurements = average(measurements)
    measurements = smooth(measurements, width=parsed_args.width)

    out_file = parsed_args.out_file.expanduser().resolve()
    print(f"Saving to {out_file} ...")
    np.savetxt(out_file, measurements, delimiter=",", header="R,G,B,X,Y,Z", comments="")


if __name__ == "__main__":
    command(parser.parse_args())
