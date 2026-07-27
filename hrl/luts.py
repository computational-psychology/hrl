"""Lookup table (LUT) utilities for gamma correction and luminance mapping.

HRL uses LUTs to perform gamma correction on greyscale images,
mapping input intensities to linearized output intensities.
This module provides functions to create and apply these LUTs.

The greyscale LUTs are structured as 2D NumPy arrays with three columns:
0: `intensity_in`: Input intensities (ranging between [0.0, 1.0])
1: `intensity_out`: Gamma-corrected output intensities
2: `luminance`: Corresponding luminance values

Generally, these LUTs are created through measurement of a display
and linearization of the resulting measurements.
This can be done using the `hrl-util`, documented elsewhere.
Here, we do provide a function to create parametric LUTs
based on standard gamma correction formulas
-- this is useful for testing and simulation, but should not be used
for real display characterization!

For color displays, color LUTs (CLUTs) are used, see hrl.cluts for more information.


Functions
---------
gamma_correct_grey(img, LUT)
    Apply gamma correction to a greyscale array using a provided LUT.
create_lut(n=256, gamma=1.0, k=1.0, dark=0.0)
    Create a parametric LUT with gamma correction and luminance scaling.

"""

import numpy as np


def gamma_correct_grey(img, LUT):
    """Apply gamma correction to a greyscale array using a provided LUT.

    Parameters
    ----------
    img : Array[float]
        input greyscale array with values between [0.0, 1.0].
        Can be a scalar, 1D array, or 2D array.
    LUT : Array[float]
        LookUp Table with at least shape (N, 2), where the first column is
        input intensities and the second column is the corrected values.
        Can have more columns, which will be ignored.

    Returns
    -------
    Array[float]
        gamma-corrected greyscale array with the same shape as input.
    """
    return np.interp(img, LUT[:, 0], LUT[:, 1])


def create_lut(
    n=256,
    gamma=1.0,
    k=1.0,
    dark=0.0,
):
    """Create a parametric LUT with gamma correction and luminance scaling.

    Parameters
    ----------
    n : int, optional
        Number of entries in the LUT, by default 256.
    gamma : float, optional
        Gamma exponent for correction, by default 1.0 (identity).
    k : float, optional
        Scaling factor for luminance calculation, by default 1.0.
    dark : float, optional
        Dark luminance offset, by default 0.0.

    Returns
    -------
    Array
        With 3 columns [intensity_in, intensity_out, luminance]:
            intensity_out = intensity_in^(1/gamma)
            luminance = k * intensity_in^gamma + dark
    """
    # Linearly spaced input intensities from 0 to 1
    x = np.linspace(0.0, 1.0, n)

    # Linearly spaced luminance value.
    # Use linspace, because that's also what we use in the calibration (linearize())
    # This way, luminance values are bit-identical, important for testing and reproducibility.
    lum = np.linspace(dark, k + dark, n)

    # Output intensities: apply inverse gamma correction
    out = x ** (1 / gamma)

    return np.column_stack([x, out, lum])
