import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

parser = argparse.ArgumentParser(
    prog="plot",
    description="""
    This function takes the lookup table data and plots it to to depict the
    results of the correction.
    """,
    add_help=False,
)
parser.add_argument(
    "-i",
    "--in_file",
    default="lut.csv",
    type=Path,
    help="path to LUT csv plot, by default 'lut.csv'",
)


def command(parsed_args):
    lut_file = parsed_args.in_file.expanduser().resolve()
    lut = np.genfromtxt(lut_file, delimiter=",", skip_header=1)

    plt.figure()

    plt.subplot(211)
    plt.plot(lut[:, 0], lut[:, 0], label="Original")
    plt.plot(lut[:, 0], lut[:, 1], label="Corrected")
    plt.xlabel("Input Intensity")
    plt.ylabel("Output Intensity")
    plt.title("Corrected Intensity")
    plt.legend(loc="upper left")

    plt.subplot(212)
    plt.plot(lut[:, 1], lut[:, 2], label="Original")
    plt.plot(lut[:, 0], lut[:, 2], label="Corrected")
    plt.xlabel("Input Intensity")
    plt.ylabel("Luminance")
    plt.title("Corrected Luminance")
    plt.legend(loc="upper left")

    plt.show()


if __name__ == "__main__":
    command(parser.parse_args())
