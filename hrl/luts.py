"""Lookup table (LUT) utilities for gamma correction and luminance mapping.

HRL uses LUTs to perform gamma correction on greyscale images,
mapping input intensities to linearized output intensities.
This module provides functions to create and apply these LUTs.

The greyscale LUTs are structured as 2D NumPy arrays with three columns:
0: `intensity_in`: Input intensities (ranging between [0.0, 1.0])
1: `intensity_out`: Gamma-corrected output intensities
2: `luminance`: Corresponding luminance values

For color displays, color LUTs (CLUTs) are used,
which map input R, G, B intensities to linearized RGB values
and provide a color transformation matrix for each intensity level.
These CLUTs are structured as 2D NumPy arrays with thirteen columns:
0: `intensity_in`: Input intensities (ranging between [0.0, 1.0])
1-3: `R_out`, `G_out`, `B_out`: Gamma-corrected output RGB values
4-12: 3x3 color transformation (RGB -> XYZ) matrix values, flattened row-wise:
    [X_R, X_G, X_B, Y_R, Y_G, Y_B, Z_R, Z_G, Z_B]

Generally, these (C)LUTs are created through measurement of a display
and linearization of the resulting measurements.
This can be done using the `hrl-util`, documented elsewhere.
Here, we do provide a function to create parametric (C)LUTs
based on standard gamma correction formulas
-- this is useful for testing and simulation, but should not be used
for real display characterization!


Functions
---------
gamma_correct_grey(img, LUT)
    Apply gamma correction to a greyscale array using a provided LUT.
gamma_correct_RGB(img, CLUT)
    Apply gamma correction to an RGB array using a provided color LUT.
create_lut(n=256, gamma=1.0, k=1.0, dark=0.0)
    Create a parametric LUT with gamma correction and luminance scaling.
create_clut(n=256, gamma=[1.0, 1.0, 1.0], color_matrix=None, dark_chromaticity=None)
    Create a parametric CLUT with gamma correction and color conversion.

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


def gamma_correct_RGB(img, CLUT):
    """Apply gamma correction to an RGB array using a provided color LUT.

    Parameters
    ----------
    img : Array[float]
        input RGB array with values between [0.0, 1.0].
        Can be a single RGB triplet (shape: (1, 1, 3)) or an RGB image (shape: (H, W, 3)).
    CLUT : Array[float]
        Color LookUp Table with at least shape (N, 4), where the first column is
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


### (C)LUT Factories ###
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
    x = np.linspace(0.0, 1.0, n)

    out = x ** (1 / gamma)

    lum = k * x**gamma + dark
    lum[0] = dark  # enforce zero row

    return np.column_stack([x, out, lum])


def create_clut(
    n=256,
    gamma=[1.0, 1.0, 1.0],
    color_matrix=None,
    dark_chromaticity=None,
):
    """Create a parametric CLUT with gamma correction and color conversion.

    Parameters
    ----------
    n : int, optional
        number of entries in the CLUT, by default 256.
    gamma : [float, float, float] or float, optional
        gamma exponents for R, G, B correction, by default [1.0, 1.0, 1.0].
    color_matrix : Array, optional
        3x3 color transformation matrix, by default identity (XYZ=RGB).
    dark_chromaticity : Array, optional
        3-element vector for dark state chromaticity (XYZ at black), by default zeros (no dark light).

    Returns
    -------
    Array
        with 13 columns [intensity_in, R_out, G_out, B_out, 9 matrix values]:
            R_out, G_out, B_out = intensity_in^(1/gamma[i]) for each channel
            First row's 3x3 matrix represents dark_chromaticity as the black point
            Last row's 3x3 matrix is color_matrix
            Intermediate rows linearly interpolate between dark and full color
    """
    if dark_chromaticity is None:
        dark_chromaticity = np.zeros(3)
    if color_matrix is None:
        color_matrix = np.eye(3)
    if isinstance(gamma, (int, float)):
        gamma = [gamma, gamma, gamma]

    x = np.linspace(0.0, 1.0, n)
    corrected = [x ** (1 / g) for g in gamma]
    rgb = np.column_stack(corrected)

    # RGB->XYZ matrices per entry: linearly interpolate from dark to full color
    # At x=0: dark chromaticity as diagonal (simplified representation)
    # At x=1: full color_matrix
    dark_matrix = np.diag(dark_chromaticity)
    matrices = x[:, None, None] * (color_matrix - dark_matrix) + dark_matrix
    matrices_flat = matrices.reshape(n, -1)

    # Combine all columns
    return np.column_stack([x, rgb, matrices_flat])
