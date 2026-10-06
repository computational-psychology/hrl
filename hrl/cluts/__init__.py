"""Color LookUp Tables (CLUTs): calibrating a color display, and using the result.

HRL uses CLUTs to perform gamma correction on color images,
mapping input intensities to linearized output intensities.
This module provides functions to create and apply these CLUTs.

The Color LUTs map input R, G, B intensities to linearized RGB values
and provide a color transformation matrix for each intensity level.
These CLUTs are structured as 2D NumPy arrays with 13 columns, one row per input level:
0: `intensity_in`: Input intensities (ranging between [0.0, 1.0])
1-3: `R_out`, `G_out`, `B_out`: Gamma-corrected output RGB values
4-12: 3x3 color transformation (RGB -> XYZ) matrix values, flattened row-wise:
    [X_R, X_G, X_B, Y_R, Y_G, Y_B, Z_R, Z_G, Z_B]

Columns 4-12 are what a calibration measures: each channel swept on its own. Every
channel's XYZ includes the light the screen gives off at black, so in the first row,
input 0, all three channels hold the same XYZ: that of the black screen. It is the
color counterpart of a grayscale LUT's luminance column, which also includes the dark
luminance, in its first row.

Generally, these CLUTs are created by measuring a display
and linearization of the resulting measurements.
Here, we do provide a function to create parametric CLUTs (`create_clut`)
based on standard gamma correction formulas
-- this is useful for testing and simulation, but should not be used
for real display characterization!

The rest of the package is in
submodules, one per job:

`hrl.cluts.colorimetry`
    converting between input RGB and CIE XYZ with the primaries matrix a CLUT holds.

Functions
---------
gamma_correct_RGB(img, CLUT)
    Apply gamma correction to an RGB array using a provided color LUT.
create_clut(n=256, gamma=[1.0, 1.0, 1.0], color_matrix=None, dark_chromaticity=None)
    Create a parametric CLUT with gamma correction and color conversion.

"""

import numpy as np

from .colorimetry import RGB_to_XYZ, XYZ_from_CLUT, XYZ_to_RGB, invert_primaries_matrix


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


def create_clut(
    n=256,
    gamma=[1.0, 1.0, 1.0],
    primaries_matrix=None,
    black_point=None,
):
    """Create a parametric CLUT, for a display with a gamma and fixed primaries.

    Describes a display whose channels each respond to their drive value with a power
    law (``drive ** gamma``).
    Optionally, the CLUT can also describe how the display's channels mix to produce color,
    and what the display's black point is.

    The color counterpart of `hrl.luts.create_lut`.

    Parameters
    ----------
    n : int, optional
        number of entries in the CLUT, by default 256.
    gamma : [float, float, float] or float, optional
        gamma exponents for R, G, B, by default [1.0, 1.0, 1.0].
    primaries_matrix : Array, optional
        3x3 color transformation matrix, by default identity (XYZ=RGB).
    black_point : Array, optional
        XYZ of the black screen, 3 values; by default zeros (no light at black).

    Returns
    -------
    Array
        with 13 columns, see the module docstring:
            R_out, G_out, B_out = intensity_in^(1/gamma[i]) for each channel
            First row's 3x3 matrix represents black_point as the black point
            Last row's 3x3 matrix is primaries_matrix
            Intermediate rows linearly interpolate between dark and full color
    """
    if black_point is None:
        black_point = np.zeros(3)
    if primaries_matrix is None:
        primaries_matrix = np.eye(3)
    if isinstance(gamma, (int, float)):
        gamma = [gamma, gamma, gamma]

    x = np.linspace(0.0, 1.0, n)
    corrected = [x ** (1 / g) for g in gamma]
    rgb = np.column_stack(corrected)

    # RGB->XYZ matrices per entry: linearly interpolate from dark to full color
    # At x=0: dark chromaticity as diagonal (simplified representation)
    # At x=1: full primaries_matrix
    dark_matrix = np.diag(black_point)
    matrices = x[:, None, None] * (primaries_matrix - dark_matrix) + dark_matrix
    matrices_flat = matrices.reshape(n, -1)

    # Combine all columns
    return np.column_stack([x, rgb, matrices_flat])


__all__ = [
    "RGB_to_XYZ",
    "XYZ_from_CLUT",
    "XYZ_to_RGB",
    "create_clut",
    "gamma_correct_RGB",
    "invert_primaries_matrix",
]
