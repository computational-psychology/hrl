#!/usr/bin/env python
"""Convert desired luminances into the input intensities to put in a stimulus.

A calibrated monitor is described by a LookUp Table (``lut.csv``), produced by
``hrl-util lut linearize``. It has three columns:

    intensity_in, intensity_out, luminance

``HRL`` uses the first two columns at run time, to gamma-correct whatever you
display. This script is for the other direction: you know which luminance (in
candela per square metre) you want a region of your stimulus to have, and you
need to know which number to put in the numpy array.

That mapping is between the first and the third column.

Usage
-----
Print the intensities for some luminances::

    python luminance_to_intensity.py lut.csv 50 100 200

Or use the functions from your own stimulus generation code::

    from luminance_to_intensity import load_lut, intensity_for_luminance

    lut = load_lut("lut.csv")
    intensity = intensity_for_luminance(lut, 100.0)

@author: HRL examples
"""

import argparse

import numpy as np


def load_lut(filepath):
    """Load a LookUp Table from a csv file.

    Reads comma-delimited files, and falls back to whitespace-delimited,
    which is how older LUT files in this lab were written.

    Parameters
    ----------
    filepath : str or pathlib.Path
        path to the LUT file, as written by ``hrl-util lut linearize``

    Returns
    -------
    numpy.ndarray
        LUT of shape (N, 3), with columns
        intensity_in, intensity_out, luminance

    Raises
    ------
    ValueError
        if the file could not be read as a table of at least 3 columns
    """
    lut = np.genfromtxt(filepath, skip_header=1, delimiter=",")

    if lut.ndim != 2 or lut.shape[1] < 3 or np.all(np.isnan(lut)):
        # Not comma-delimited: retry with whitespace
        lut = np.genfromtxt(filepath, skip_header=1)

    if lut.ndim != 2 or lut.shape[1] < 3:
        raise ValueError(f"{filepath} does not look like a LUT: expected at least 3 columns")

    return lut


def luminance_range(lut):
    """Report the luminance range covered by a LUT.

    Parameters
    ----------
    lut : numpy.ndarray
        LUT of shape (N, 3), see `load_lut`

    Returns
    -------
    tuple of float
        minimum and maximum measured luminance, in cd/m2
    """
    luminances = lut[:, 2]
    return float(np.min(luminances)), float(np.max(luminances))


def intensity_for_luminance(lut, luminance):
    """Find the input intensity that produces a desired luminance.

    Interpolates the measured luminance column of the LUT against the
    input intensity column.

    Luminances outside the measured range are clipped to the nearest end
    of the range, which is what `numpy.interp` does. Use `luminance_range`
    to check whether a request was in range before relying on the result.

    Parameters
    ----------
    lut : numpy.ndarray
        LUT of shape (N, 3), see `load_lut`
    luminance : float or ArrayLike
        desired luminance(s), in cd/m2

    Returns
    -------
    float or numpy.ndarray
        input intensity value(s) in [0.0, 1.0], to put in the stimulus array
    """
    return np.interp(luminance, lut[:, 2], lut[:, 0])


def luminance_for_intensity(lut, intensity):
    """Find the luminance produced by an input intensity.

    The inverse of `intensity_for_luminance`.

    Parameters
    ----------
    lut : numpy.ndarray
        LUT of shape (N, 3), see `load_lut`
    intensity : float or ArrayLike
        input intensity value(s) in [0.0, 1.0]

    Returns
    -------
    float or numpy.ndarray
        luminance(s) in cd/m2
    """
    return np.interp(intensity, lut[:, 0], lut[:, 2])


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Convert desired luminances (cd/m2) into the input intensities to put in a "
            "stimulus array, using a measured LUT."
        )
    )
    parser.add_argument("lut", help="path to the LUT csv file, e.g. lut.csv")
    parser.add_argument(
        "luminances",
        type=float,
        nargs="+",
        help="desired luminance value(s), in cd/m2",
    )
    args = parser.parse_args()

    lut = load_lut(args.lut)
    lum_min, lum_max = luminance_range(lut)
    print(f"LUT {args.lut}: {len(lut)} levels, {lum_min:.4f} to {lum_max:.4f} cd/m2")

    for luminance in args.luminances:
        intensity = intensity_for_luminance(lut, luminance)
        if luminance < lum_min or luminance > lum_max:
            note = "  (OUT OF RANGE, clipped)"
        else:
            note = ""
        print(f"{luminance:10.4f} cd/m2  -->  intensity {intensity:.6f}{note}")


if __name__ == "__main__":
    main()
