"""Converting between RGB and XYZ, with a CLUT.

The CLUT contains the relationship between input RGB values
and the corresponding measured CIE 1931 XYZ values for each channel.
Taken together, these values form the _primaries matrix_
that can be used to convert between RGB and XYZ color spaces.

Additionally, the 0-intensity values for each channel capture the _black point_:
the residual dark light when all channels are off.
This is the XYZ tristimulus values for what "black" means on the display.

The RGB here is always the *input*: the values as they are passed to Graphics
(where the CLUT is applied).
"""

import numpy as np


def primaries_from_CLUT(CLUT):
    """Extract XYZ primaries matrix and black point from a provided Color LUT.

    The black point is the XYZ tristimulus values for what "black" means on the display
    -- the (average) measurement of the display when all channels are off; first row of the CLUT.
    The primaries matrix is the XYZ that each channel adds above that, per unit of input.

    This primaries matrix is fitted by least squares to the CLUT's measured XYZ values;
    since real primaries may drift somewhat with input, not single measured row fits every level.
    For a discussion of this, see Brainard, Pelli & Robson, 2002, Display characterization.
    (Psychtoolbox's default calibration also fits each primary over all measured levels)

    Luminance is fitted exactly, since the CLUT linearizes on luminance (Y).
    It cannot linearize on all three tristimulus values at once.

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
    CLUT = np.asarray(CLUT, dtype=float)
    inputs = CLUT[:, 0]
    black_point = CLUT[0, 4:7]

    # For each channel: the line through the origin, XYZ_added = input * column, that
    # misses its measured XYZ (above black) least, summed over all levels
    primaries_matrix = np.column_stack(
        [
            inputs @ (CLUT[:, 4 + 3 * channel : 7 + 3 * channel] - black_point) / (inputs @ inputs)
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


def differences(measured, expected):
    """How far measured colors are from expected ones: overall, in luminance, and in chromaticity.

    Parameters
    ----------
    measured, expected : array-like
        colors as CIE XYZ, shape (..., 3), compared row for row

    Returns
    -------
    numpy.ndarray
        shape (..., 3), columns:

        - XYZ: the distance between the two, in XYZ, in the units they were measured in.
        - Y: measured luminance relative to the expected, minus 1. 0.02 means 2% brighter
          than expected.
        - xy: the distance between their chromaticities, CIE 1931 x, y -- the xy of xyY,
          which leaves luminance out.

    Examples
    --------
    >>> differences([102.0, 100.0, 98.0], [100.0, 100.0, 100.0]).round(4)
    array([2.8284, 0.    , 0.0067])
    """
    measured = np.asarray(measured, dtype=float)
    expected = np.asarray(expected, dtype=float)

    def xy(xyz):
        """CIE 1931 x, y chromaticity."""
        return xyz[..., :2] / xyz.sum(axis=-1, keepdims=True)

    return np.stack(
        [
            np.linalg.norm(measured - expected, axis=-1),
            measured[..., 1] / expected[..., 1] - 1.0,
            np.linalg.norm(xy(measured) - xy(expected), axis=-1),
        ],
        axis=-1,
    )
