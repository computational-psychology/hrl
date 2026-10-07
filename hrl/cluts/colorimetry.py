"""Converting between RGB and XYZ, with a CLUT.

The CLUT contains the relationship between input RGB values
and the corresponding measured CIE 1931 XYZ values for each channel.
Taken together, these values form the _primaries matrix_
that can be used to convert between RGB and XYZ color spaces.

Additionally, the 0-intensity values for each channel capture the _black point_:
the residual dark light when all channels are off.
This is the XYZ tristimulus values for what "black" means on the display.
"""

import numpy as np


def primaries_from_CLUT(CLUT):
    """Extract XYZ primaries matrix and black point from a provided Color LUT.

    Parameters
    ----------
    CLUT : Array[float]
        Color Lookup Table with shape (N, 13), see `hrl.cluts`.

    Returns
    -------
    primaries_matrix : Array[float]
        shape (3, 3); column c is what channel c adds per unit of input.
    black_point : Array[float]
        shape (3,); XYZ values for what "black" means on the display.
    """
    black_point = CLUT[0, 4:7]
    primaries_matrix = np.column_stack(
        [
            (CLUT[-1, 4 + 3 * channel : 7 + 3 * channel] - black_point) / CLUT[-1, 1 + channel]
            for channel in range(3)
        ]
    )
    return primaries_matrix, black_point


def RGB_to_XYZ(rgb, CLUT):
    """The color (CIE XYZ) a display shows for given input RGB.

    Uses the display's primaries matrix (see `primaries_from_CLUT`): the black point, plus each
    channel's column of the matrix, times its input.

    Parameters
    ----------
    rgb : array-like
        input RGB, values in [0.0, 1.0], shape (..., 3): one triplet, a list of them, or an
        image
    CLUT : Array[float]
        Color Lookup Table with shape (L, 13), see `hrl.cluts`.

    Returns
    -------
    Array[float]
        XYZ, the same shape as `rgb`
    """
    # Check or reshape the input to be (..., 3)
    rgb = np.asarray(rgb, dtype=float)
    if rgb.shape[-1] != 3:
        if rgb.size == 3:
            rgb = rgb.reshape((1, 3))
        else:
            raise ValueError("expected 3 values along the last axis, shape (..., 3)")

    # Get the primaries matrix and black point from the CLUT
    primaries_matrix, black_point = primaries_from_CLUT(CLUT)

    # Convert RGB to XYZ: multiply by primaries matrix
    XYZ = rgb @ primaries_matrix.T

    # Add black point
    XYZ += black_point

    return XYZ


def XYZ_to_RGB(xyz, CLUT):
    """The input RGB that shows a wanted color (CIE XYZ) on a display.

    Runs the primaries matrix backwards (see `primaries_from_CLUT`): takes off the black point,
    and multiplies by the matrix's inverse. A color the display cannot show comes out with
    inputs outside [0, 1].

    Parameters
    ----------
    xyz : array-like
        wanted color(s), CIE XYZ, shape (..., 3): one, a list of them, or an image
    CLUT : Array[float]
        Color Lookup Table with shape (L, 13), see `hrl.cluts`.

    Returns
    -------
    Array[float]
        input RGB, the same shape as `xyz`
    """
    # Check or reshape the input to be (..., 3)
    xyz = np.asarray(xyz, dtype=float)
    if xyz.shape[-1] != 3:
        if xyz.size == 3:
            xyz = xyz.reshape((1, 3))
        else:
            raise ValueError("expected 3 values along the last axis, shape (..., 3)")

    # Get the primaries matrix and black point from the CLUT
    primaries_matrix, black_point = primaries_from_CLUT(CLUT)

    # Subtract black point
    rgb = xyz - black_point

    # Convert XYZ to RGB: multiply by the inverse of the primaries matrix
    rgb = rgb @ np.linalg.inv(primaries_matrix).T

    return rgb
