import argparse

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


def command(parsed_args):
    lut = np.genfromtxt("lut.csv", skip_header=1, delimiter=",")

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
