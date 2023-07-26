### Imports ###

import numpy as np
import argparse as ap
import pylab as plt

### Argument parser ###

prsr = ap.ArgumentParser(
    prog="hrl-util lut plot",
    description="""
    This function takes the lookup table data and plots it to to depict the
    results of the correction.
    """,
)

### Core ###


def plot(args):
    lut = np.genfromtxt("lut.csv", skip_header=1)

    plt.figure(1)

    plt.subplot(211)
    plt.plot(lut[:, 0], lut[:, 0])
    plt.plot(lut[:, 0], lut[:, 1])
    plt.xlabel("Input Intensity")
    plt.ylabel("Output Intensity")
    plt.title("Corrected Intensity")
    plt.legend(["Original", "Corrected"], loc="upper left")

    plt.subplot(212)
    plt.plot(lut[:, 1], lut[:, 2])
    plt.plot(lut[:, 0], lut[:, 2])
    plt.xlabel("Input Intensity")
    plt.ylabel("Luminance")
    plt.title("Corrected Luminance")
    plt.legend(["Original", "Corrected"], loc="upper left")

    plt.show()
