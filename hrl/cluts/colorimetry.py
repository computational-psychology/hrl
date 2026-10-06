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


def XYZ_from_CLUT(CLUT):
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
        shape (3, 3); the black point's XYZ, on the diagonal.
    """
    black = CLUT[0, 4:7]
    primaries_matrix = np.column_stack(
        [
            (CLUT[-1, 4 + 3 * channel : 7 + 3 * channel] - black) / CLUT[-1, 1 + channel]
            for channel in range(3)
        ]
    )
    black_point = np.diag(black)

    return primaries_matrix, black_point


def RGB_to_XYZ(img, primaries_matrix, black_point=np.zeros((3, 3))):
    """Convert RGB image to CIE 1931 XYZ color space using provided color matching functions.

    Parameters
    ----------
    img : Array[float]
        RGB image with values between [0.0, 1.0].
        Shape: (H, W, 3).
    primaries_matrix : Array[float]
        primaries matrix (XYZ CIE 1931 from RGB) with shape (3, 3).
    black_point : Array[float], optional
        black point (XYZ CIE 1931 for the "black" state) with shape (3, 3), by default: None

    Returns
    -------
    Array[float]
        XYZ CIE 1931 image with shape (H, W, 3).
    """
    # Reshape image to (H*W, 3) for matrix multiplication
    H, W, _ = img.shape
    img_reshaped = img.reshape(-1, 3)

    # Convert RGB to XYZ
    XYZ_reshaped = img_reshaped @ primaries_matrix.T

    # Add black point
    XYZ_reshaped += black_point.sum(axis=0)

    # Reshape back to (H, W, 3)
    XYZ = XYZ_reshaped.reshape(H, W, 3)

    return XYZ


def invert_primaries_matrix(XYZ_from_RGB_matrix):
    """Compute the inverse of a primaries matrix.

    Parameters
    ----------
    XYZ_from_RGB_matrix : Array[float]
        primaries matrix (XYZ CIE 1931 from RGB) with shape (3, 3).

    Returns
    -------
    Array[float]
        inverted primaries matrix (RGB from XYZ CIE 1931) with shape (3, 3).
    """
    return np.linalg.inv(XYZ_from_RGB_matrix)


def XYZ_to_RGB(XYZ, inv_primaries_matrix, black_point=np.zeros((3, 3))):
    """Convert CIE 1931 XYZ image to RGB color space using provided inverse primaries matrix.

    Parameters
    ----------
    XYZ : Array[float]
        XYZ CIE 1931 image with shape (H, W, 3).
    inv_primaries_matrix : Array[float]
        inverse primaries matrix (RGB from XYZ CIE 1931) with shape (3, 3).
    black_point : Array[float], optional
        black point (XYZ CIE 1931 for the "black" state) with shape (3, 3), by default: None

    Returns
    -------
    Array[float]
        RGB image with values between [0.0, 1.0] and shape (H, W, 3).
    """
    # Reshape image to (H*W, 3) for matrix multiplication
    H, W, _ = XYZ.shape
    XYZ_reshaped = XYZ.reshape(-1, 3)

    # Subtract black point
    XYZ_reshaped -= black_point.sum(axis=0)

    # Convert XYZ to RGB
    RGB_reshaped = XYZ_reshaped @ inv_primaries_matrix.T

    # Reshape back to (H, W, 3)
    RGB = RGB_reshaped.reshape(H, W, 3)

    return RGB
