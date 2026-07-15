import argparse

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


def command(parsed_args):
    # Load measurement data
    files = ["measure.csv"]
    measurements = [np.genfromtxt(fl, skip_header=1, delimiter=",") for fl in files]

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
    print("Saving to File...")
    out_filename = "smooth.csv"
    out_file = open(out_filename, "w")
    out_file.write("intensity_in,luminance\n")
    np.savetxt(out_file, table, delimiter=",")
    out_file.close()


if __name__ == "__main__":
    command(parser.parse_args())
