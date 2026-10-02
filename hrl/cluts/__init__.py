"""Color LookUp Tables (CLUTs): calibrating a color display, and using the result.

HRL uses CLUTs to perform gamma correction on color images,
mapping input intensities to linearized output intensities.
This module provides functions to create and apply these CLUTs.

The Color LUTs map input R, G, B intensities to linearized RGB values
and provide a color transformation matrix for each intensity level.
These CLUTs are structured as 2D NumPy arrays with 13 columns, one row per input level:

0: ``intensity_in``
    input intensity, from 0.0 to 1.0. This is the value you ask graphics for.
1-3: ``R_out``, ``G_out``, ``B_out``
    the value each channel is driven at to show that input. Graphics reads only
    these first four columns, to gamma-correct images (`gamma_correct_RGB`).
4-6: ``R_X``, ``R_Y``, ``R_Z``
    the color (CIE XYZ) the screen shows with only the red channel at this input,
    and green and blue at 0.
7-9: ``G_X``, ``G_Y``, ``G_Z``
    the same, with only green on.
10-12: ``B_X``, ``B_Y``, ``B_Z``
    the same, with only blue on.

Columns 4-12 are what a calibration measures: each channel swept on its own. Every
channel's XYZ includes the light the screen gives off at black, so in the first row,
input 0, all three channels hold the same XYZ: that of the black screen. It is the
color counterpart of a grayscale LUT's luminance column, which also includes the dark
luminance, in its first row.

Generally, these CLUTs are created by measuring a display
and linearization of the resulting measurements.
This can be directly from the command-line through ``python -m hrl.util clut``,
which uses the functionality in `hrl.cluts.calibrate`.
Here, we do provide a function to create parametric CLUTs (`create_clut`)
based on standard gamma correction formulas
-- this is useful for testing and simulation, but should not be used
for real display characterization!

The rest of the package is in
submodules, one per job:

`hrl.cluts.calibrate`
    making a CLUT from measurements: `measure` (and `read_measurements`),
    `remove_outliers`, `average`, `linearize`;
    and checking one: `predict` (what a CLUT expects for measured inputs) and
    `predict_from_channels` (what the inputs should give if the channels add up).
    Can use this from the using ``python -m hrl.util clut ...``.
`hrl.cluts.colorimetry`
    converting between input RGB and CIE XYZ with the primaries matrix a CLUT holds
    (`RGB_to_XYZ`, `XYZ_to_RGB`, which says how close it got; the matrix itself:
    `primaries_from_CLUT`). Or, with ``per_level=True``, per level of input, following
    primaries whose color drifts more.
    Also can give grey of a given luminance (`achromatic_RGB`),
    and how far a color direction can go (`max_excursion`);
    and how far measured colors are from expected ones (`differences`).
`hrl.cluts.triplets`
    sets of RGB triplets to show and measure: each channel swept on its own
    (`channel_sweeps`), mixtures of the channels with their parts
    (`channel_mixtures`), and colors around a background at its luminance
    (`isoluminant_colors`).

The usual path: measure the display and build its CLUT with ``python -m hrl.util clut``; show
stimuli through it with ``Graphics_RGB(lut=...)``; and use `XYZ_to_RGB` to find the input
for the colors an experiment calls for.

Functions
---------
gamma_correct_RGB(img, CLUT)
    Apply gamma correction to an RGB array using a provided color LUT.
create_clut(n=256, gamma=[1.0, 1.0, 1.0], color_matrix=None, dark_chromaticity=None)
    Create a parametric CLUT with gamma correction and color conversion.

"""

import numpy as np

from .colorimetry import (
    RGB_to_XYZ,
    XYZ_to_RGB,
    achromatic_RGB,
    differences,
    max_excursion,
    primaries_from_CLUT,
)


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
        3x3 matrix whose column c is the XYZ that channel c adds, above black, at full
        input; by default identity (XYZ = RGB).
    black_point : Array, optional
        XYZ of the black screen, 3 values; by default zeros (no light at black).

    Returns
    -------
    Array
        with 13 columns, see the module docstring:
            R_out, G_out, B_out = intensity_in ** (1 / gamma[c])
            channel c's XYZ = dark + intensity_in * color_matrix[:, c]
    """
    if black_point is None:
        black_point = np.zeros(3)
    if primaries_matrix is None:
        primaries_matrix = np.eye(3)
    if isinstance(gamma, (int, float)):
        gamma = [gamma, gamma, gamma]
    black = np.asarray(black_point, dtype=float)
    primaries_matrix = np.asarray(primaries_matrix, dtype=float)

    x = np.linspace(0.0, 1.0, n)
    drive = np.column_stack([x ** (1 / g) for g in gamma])

    # Each channel's XYZ with only it on: black, plus its light, linear in the input
    alone = [black + x[:, None] * primaries_matrix[:, channel] for channel in range(3)]

    return np.column_stack([x, drive, *alone])


__all__ = [
    "RGB_to_XYZ",
    "XYZ_to_RGB",
    "achromatic_RGB",
    "create_clut",
    "differences",
    "gamma_correct_RGB",
    "max_excursion",
    "primaries_from_CLUT",
]
