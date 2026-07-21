import argparse
from pathlib import Path

import numpy as np

import hrl.calibration.measurement

parser = argparse.ArgumentParser(
    prog="smooth",
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
    """,
    add_help=False,
)
parser.add_argument(
    "-n",
    "--order",
    default=0,
    type=int,
    help="number of times (order) to smooth the data, by default 0 (no smoothing, just averaging)",
)
parser.add_argument(
    "-k",
    "--kernel",
    default=[0.2, 0.2, 0.2, 0.2, 0.2],
    type=float,
    nargs="+",
    help="kernel for smoothing, by default [0.2, 0.2, 0.2, 0.2, 0.2]",
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
    help="path for output smoothed measurements csv, by default 'smooth.csv'",
)


def command(parsed_args):
    # Load measurement data
    measurements = []
    in_files = parsed_args.in_file
    if isinstance(in_files, (str, Path)):
        in_files = [in_files]
    for file in in_files:
        filename = file.expanduser().resolve()
        print(f"Loading from {filename} ...")
        measurements.append(np.genfromtxt(filename, delimiter=",", skip_header=1))

    # Combine
    luminance_map = hrl.calibration.measurement.combine(measurements)

    # Remove outliers
    luminance_map = hrl.calibration.measurement.remove_outliers(luminance_map)

    # Average
    table = hrl.calibration.measurement.average(luminance_map)

    # Smooth
    table[:, 1] = hrl.calibration.measurement.smooth(
        table[:, 1], order=parsed_args.order, kernel=parsed_args.kernel
    )

    # Save smoothed LUT to file
    out_file = parsed_args.out_file.expanduser().resolve()
    print(f"Saving to {out_file}...")
    header = "intensity_in,luminance"
    np.savetxt(out_file, table, delimiter=",", header=header, comments="")


if __name__ == "__main__":
    command(parser.parse_args())
