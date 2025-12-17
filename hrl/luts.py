"""Lookup table (LUT) utilities for gamma correction and luminance mapping.

HRL uses LUTs to perform gamma correction on greyscale images
and map intensities to luminance values.
This module provides functions to create and apply these LUTs.

The LUTs are structured as 2D NumPy arrays with three columns:
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
        lookup table with at least shape (N, 2), where the first column is
        input intensities and the second column is the corrected values.
        Can have more columns, which will be ignored.

    Returns
    -------
    Array[float]
        gamma-corrected greyscale array with the same shape as input.
    """
    return np.interp(img, LUT[:, 0], LUT[:, 1])


def gamma_correct_RGB(img, CLUT):
    """Apply gamma correction to an RGB array using a provided color LUT.

    Parameters
    ----------
    img : Array[float]
        input RGB array with values between [0.0, 1.0].
        Can be a single RGB triplet (shape: (1, 1, 3)) or an RGB image (shape: (H, W, 3)).
    CLUT : Array[float]
        color lookup table with at least shape (N, 4), where the first column is
        input intensities and the next three columns are the corrected R, G, B values.
        Can have more columns, which will be ignored.

    Returns
    -------
    Array[float]
        gamma-corrected RGB array with the same shape as input.
    """
    # Apply interpolation per channel
    linearized_RGB = np.array(
        [
            np.interp(img[..., channel], CLUT[:, 0], CLUT[:, channel + 1])
            for channel in range(img.shape[-1])
        ]
    )

    # Move channel axis from first to last position
    # For (1, 1, 3) input: (3, 1, 1) -> (1, 1, 3)
    # For (H, W, 3) input: (3, H, W) -> (H, W, 3)
    linearized_RGB = np.moveaxis(linearized_RGB, 0, -1)

    return linearized_RGB


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
        with 3 columns [intensity_in, intensity_in, luminance]:
            intensity_in = intensity_in^(1/gamma)
            luminance = k * intensity_in + dark
    """
    x = np.linspace(0.0, 1.0, n)

    out = x ** (1 / gamma)

    lum = k * x**gamma + dark
    lum[0] = dark  # enforce zero row

    return np.column_stack([x, out, lum])
