"""Converting between RGB and XYZ, with a CLUT."""

import numpy as np


def XYZ_from_CLUT(CLUT):
    """Extract CIE 1931 XYZ color matching functions from a provided Color LUT.

    Parameters
    ----------
    CLUT : Array[float]
        Color Lookup Table with shape (N, 13), see `hrl.cluts`.

    Returns
    -------
    Array[float]
        color matrix (XYZ CIE 1931 from RGB) with shape (3, 3).
    """
    color_matrix = CLUT[-1, 4:13].reshape(3, 3)
    dark_chromaticity = CLUT[0, 4:13].reshape((3, 3))

    return color_matrix, dark_chromaticity


def RGB_to_XYZ(img, color_matrix, dark_chromaticity=np.zeros((3, 3))):
    """Convert RGB image to CIE 1931 XYZ color space using provided color matching functions.

    Parameters
    ----------
    img : Array[float]
        RGB image with values between [0.0, 1.0].
        Shape: (H, W, 3).
    color_matrix : Array[float]
        color matrix (XYZ CIE 1931 from RGB) with shape (3, 3).
    dark_chromaticity : Array[float], optional
        dark chromaticity values for each channel with shape (3, 3), by default: None

    Returns
    -------
    Array[float]
        XYZ CIE 1931 image with shape (H, W, 3).
    """
    # Reshape image to (H*W, 3) for matrix multiplication
    H, W, _ = img.shape
    img_reshaped = img.reshape(-1, 3)

    # Convert RGB to XYZ
    XYZ_reshaped = img_reshaped @ color_matrix.T

    # Add dark chromaticity
    XYZ_reshaped += dark_chromaticity.sum(axis=0)

    # Reshape back to (H, W, 3)
    XYZ = XYZ_reshaped.reshape(H, W, 3)

    return XYZ


def invert_color_matrix(XYZ_from_RGB_matrix):
    """Compute the inverse of a color matching matrix.

    Parameters
    ----------
    XYZ_from_RGB_matrix : Array[float]
        color matrix (XYZ CIE 1931 from RGB) with shape (3, 3).

    Returns
    -------
    Array[float]
        inverted color matrix (RGB from XYZ CIE 1931) with shape (3, 3).
    """
    return np.linalg.inv(XYZ_from_RGB_matrix)


def XYZ_to_RGB(XYZ, inv_color_matrix, dark_chromaticity=np.zeros((3, 3))):
    """Convert CIE 1931 XYZ image to RGB color space using provided inverse color matching functions.

    Parameters
    ----------
    XYZ : Array[float]
        XYZ CIE 1931 image with shape (H, W, 3).
    inv_color_matrix : Array[float]
        inverse color matrix (RGB from XYZ CIE 1931) with shape (3, 3).
    dark_chromaticity : Array[float], optional
        dark chromaticity values for each channel with shape (3, 3), by default: None

    Returns
    -------
    Array[float]
        RGB image with values between [0.0, 1.0] and shape (H, W, 3).
    """
    # Reshape image to (H*W, 3) for matrix multiplication
    H, W, _ = XYZ.shape
    XYZ_reshaped = XYZ.reshape(-1, 3)

    # Subtract dark chromaticity
    XYZ_reshaped -= dark_chromaticity.sum(axis=0)

    # Convert XYZ to RGB
    RGB_reshaped = XYZ_reshaped @ inv_color_matrix.T

    # Reshape back to (H, W, 3)
    RGB = RGB_reshaped.reshape(H, W, 3)

    return RGB
