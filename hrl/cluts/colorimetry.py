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

There are two approaches to reading a display's color from its CLUT; both are used in this module.
The first uses a _primaries matrix_:
a single 3x3 matrix that describes what each channel adds, above black, per unit of input.
This is the simple model that is easily inverted,
and it's what `RGB_to_XYZ` and `XYZ_to_RGB` use by default (the matrix itself:
`primaries_from_CLUT`).
It assumes that each channel's color is constant, independent of its input (no drift);
it'll be a good approximation for displays whose primaries are stable.

However, for displays whose primaries drift more with input, no single matrix can describe them.
In that case, the second approach is a true LookUp Table: look up the actually measured XYZ
per channel, per level (``per_level=True``).
For levels between the tabulated ones, it interpolates along a straight line between them.
Running it backwards has no formula: `XYZ_to_RGB` searches for the input.

Either approach assumes that the display's channels add up:
the color is the black point plus what each channel adds.
Whether a display's channels really do add up is an empirical question,
and can be checked with `hrl.cluts.calibrate.predict_from_channels`
on what ``python -m hrl.util clut measure --sets mixtures`` measures.
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


def _channel_curves(CLUT, gamma_correct=True):
    """Read a CLUT as three curves: how much light each channel adds at each input.

    Read once, evaluated as often as needed: `XYZ_to_RGB` (per level) evaluates the same
    curves at every round of its search.

    Parameters
    ----------
    CLUT : Array[float]
        Color Lookup Table with shape (L, 13), see `hrl.cluts`.
    gamma_correct : bool, optional
        If True (default), the curves are tabulated at the values passed to graphics,
        which applies this CLUT. If False, at the drive values sent to the screen
        directly, as if no CLUT were loaded.

    Returns
    -------
    dict
        ``black_point``: XYZ with every channel off, shape (3,).
        ``levels``: shape (3, L). ``levels[c]`` are the inputs at which channel c's curve
        is tabulated, increasing.
        ``light``: shape (3, L, 3). ``light[c]`` is the XYZ channel c adds, above the
        black point, at each of those inputs.
    """
    CLUT = np.asarray(CLUT, dtype=float)

    # Columns 4-12 hold, per channel, the XYZ with only that channel on: [row, channel, axis]
    alone = CLUT[:, 4:13].reshape(-1, 3, 3)

    # At input 0 every channel is off, so all three hold the black point
    black_point = alone[0, 0]

    # The inputs each channel's curve is tabulated at: what graphics is passed, or, without
    # the CLUT, the drive values it turns them into
    levels = np.tile(CLUT[:, 0], (3, 1)) if gamma_correct else CLUT[:, 1:4].T

    # What each channel adds, above the black point: [channel, row, axis]
    light = np.stack([alone[:, channel] - black_point for channel in range(3)])

    return {"black_point": black_point, "levels": levels, "light": light}


def _evaluate(rgb, curves):
    """The color each input produces, and how fast that color changes with each input.

    The color is worked out just as the model says: start from the black point, and
    add each channel's light at its input. Between two tabulated inputs, a channel's
    curve is a straight line, so its light there is read off that line. Inputs beyond
    the table count as its ends.

    That straight line is also why the second result is easy to get. How fast the color
    changes as one channel's input goes up is simply the slope of the line that input
    sits on. `XYZ_to_RGB` (per level) uses these slopes to work out which way to move a
    guess.

    Parameters
    ----------
    rgb : Array[float]
        inputs, shape (N, 3)
    curves : dict
        as returned by `_channel_curves`, or laid out the same way; each channel's
        ``levels`` and ``light`` may have a length of its own

    Returns
    -------
    xyz : Array[float]
        the color each input produces, shape (N, 3)
    slopes : Array[float]
        shape (N, 3, 3). ``slopes[n, :, c]`` is how much X, Y and Z go up per unit
        increase of channel c's input, at input n. (This matrix is often called the
        Jacobian.)
    """
    xyz = np.tile(curves["black_point"], (len(rgb), 1))
    slopes = np.empty((len(rgb), 3, 3))

    for channel in range(3):
        levels = curves["levels"][channel]
        light = curves["light"][channel]
        value = np.clip(rgb[:, channel], levels[0], levels[-1])

        # Find the straight piece each input falls on: between levels[i] and levels[i + 1]
        i = np.clip(np.searchsorted(levels, value) - 1, 0, len(levels) - 2)

        # Slope of that piece: how much this channel's light changes per unit of input
        slope = (light[i + 1] - light[i]) / (levels[i + 1] - levels[i])[:, None]

        # Light at the input: start of the piece, plus slope times the distance along it
        xyz += light[i] + slope * (value - levels[i])[:, None]
        slopes[:, :, channel] = slope

    return xyz, slopes


def RGB_to_XYZ(rgb, CLUT, per_level=False, gamma_correct=True):
    """The color (CIE XYZ) a display shows for given input RGB.

    By default, uses the display's primaries matrix (see `primaries_from_CLUT`): the black
    point, plus each channel's column of the matrix, times its input.

    With ``per_level=True``, uses what the CLUT records instead: the black point, plus the
    light each channel adds at its input, as measured at each of the CLUT's input levels.
    This is a true LookUp Table, which follows primaries whose color drifts with their
    input. For levels between the tabulated ones, it interpolates along a straight line
    between them.

    Parameters
    ----------
    rgb : array-like
        input RGB, values in [0.0, 1.0], shape (..., 3): one triplet, a list of them, or an
        image
    CLUT : Array[float]
        Color Lookup Table with shape (L, 13), see `hrl.cluts`.
    per_level : bool, optional
        read each channel's color per level of input, rather than from the primaries
        matrix; by default False, which is faster
    gamma_correct : bool, optional
        If True (default), `rgb` are the values passed to graphics, which applies this
        CLUT. If False, `rgb` are drive values sent to the screen directly, as if no
        CLUT were loaded.

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

    CLUT = np.asarray(CLUT, dtype=float)

    if not per_level:
        if not gamma_correct:
            # The matrix works on inputs: look up which input each drive value belongs to
            rgb = np.stack(
                [np.interp(rgb[..., c], CLUT[:, 1 + c], CLUT[:, 0]) for c in range(3)], axis=-1
            )
        primaries_matrix, black_point = primaries_from_CLUT(CLUT)
        return rgb @ primaries_matrix.T + black_point

    shape = rgb.shape
    return _evaluate(rgb.reshape(-1, 3), _channel_curves(CLUT, gamma_correct))[0].reshape(shape)


def XYZ_to_RGB(xyz, CLUT, per_level=False, rounds=25, halvings=10):
    """The input RGB that shows a wanted color (CIE XYZ) on a display, and how close it gets.

    By default, runs the primaries matrix backwards (see `primaries_from_CLUT`): takes off the
    black point, and multiplies by the matrix's inverse.

    With ``per_level=True``, there is no formula to run backwards: each channel's curve is
    a measured table, and all three channels add light to every one of X, Y and Z. So
    this finds the input by improving a guess, over and over:

    1. Start from the primaries matrix's answer.
    2. Work out the color that guess produces, and how far it is from the wanted one.
    3. Use the slopes at the guess to estimate how much each channel's input has to
       change to close that gap. That is three equations (one each for X, Y and Z) in
       three unknowns (the change to R, G and B), solved together.
    4. Make that change, keeping every input within [0, 1]. If that would land further
       from the wanted color than before, try half the change instead, then a quarter,
       and so on, so a guess never gets worse. Then go back to step 2.

    Each channel's curve is straight between tabulated inputs. So once the guess sits on
    the right straight pieces, the estimate in step 3 is exact, and the next round lands
    on the answer. Where two pieces meet at a sharp bend, though, the full change can
    overshoot onto the next piece and back again; halving it is what stops that. A
    handful of rounds is enough. (This is Newton's method, with backtracking.)

    All targets are solved together, as arrays, rather than one at a time.

    Parameters
    ----------
    xyz : array-like
        wanted color(s), CIE XYZ, shape (..., 3): one, a list of them, or an image
    CLUT : Array[float]
        Color Lookup Table with shape (L, 13), see `hrl.cluts`.
    per_level : bool, optional
        work per level of input, rather than with the primaries matrix (see
        `RGB_to_XYZ`); by default False, which is much faster
    rounds : int, optional
        with ``per_level=True``: how many times to improve the guess, by default 25
    halvings : int, optional
        with ``per_level=True``: how many times a change that would make a guess worse is
        halved before giving up on that round, by default 10

    Returns
    -------
    rgb : Array[float]
        input RGB, the same shape as `xyz`, every value within [0, 1]
    error : Array[float]
        shape ``xyz.shape[:-1]``: the distance, in XYZ, between the color `rgb` produces
        and the color that was asked for

    Notes
    -----
    **Check the error.** It is zero, to rounding, for any color the display can show.
    For one it cannot show -- too bright, or too saturated -- some inputs end up pinned at
    0 or 1, and the error says how far from the wanted color the result landed. Not every
    target is reachable, so compare the error to a tolerance to find out whether this one
    was.
    """
    # Check or reshape the input to be (..., 3)
    xyz = np.asarray(xyz, dtype=float)
    if xyz.shape[-1] != 3:
        if xyz.size == 3:
            xyz = xyz.reshape((1, 3))
        else:
            raise ValueError("expected 3 values along the last axis, shape (..., 3)")
    shape = xyz.shape
    xyz = xyz.reshape(-1, 3)

    # Get the primaries matrix and black point from the CLUT
    primaries_matrix, black_point = primaries_from_CLUT(CLUT)

    # The primaries matrix's answer, within [0, 1]: the answer by default, and the first
    # guess per level
    rgb = xyz - black_point  # Subtract black point
    rgb = (
        rgb @ np.linalg.inv(primaries_matrix).T
    )  # multiply by the inverse of the primaries matrix
    rgb = np.clip(rgb, 0.0, 1.0)

    if not per_level:
        error = np.linalg.norm(rgb @ primaries_matrix.T + black_point - xyz, axis=1)
        return rgb.reshape(shape), error.reshape(shape[:-1])

    curves = _channel_curves(CLUT)

    def distance(rgb, wanted):
        """How far, in XYZ, the color each input produces is from the wanted one."""
        return np.linalg.norm(_evaluate(rgb, curves)[0] - wanted, axis=1)

    error = distance(rgb, xyz)

    for _ in range(rounds):
        # Step 2: what color does the current guess produce, and how far off is it?
        predicted, slopes = _evaluate(rgb, curves)
        gap = (xyz - predicted)[..., None]

        # Step 3: the change to R, G, B that the slopes say would close the gap. If some
        # channel's light does not change at its current input (a slope of zero), there
        # is no exact answer; `pinv` then gives the change that closes as much as it can.
        try:
            change = np.linalg.solve(slopes, gap)[..., 0]
        except np.linalg.LinAlgError:
            change = (np.linalg.pinv(slopes) @ gap)[..., 0]

        # Step 4: apply it, without leaving the range the display accepts...
        candidate = np.clip(rgb + change, 0.0, 1.0)
        candidate_error = distance(candidate, xyz)

        # ...and where that made a guess worse, try half the change, and half again
        for _ in range(halvings):
            worse = candidate_error > error
            if not worse.any():
                break
            change[worse] /= 2
            candidate[worse] = np.clip(rgb[worse] + change[worse], 0.0, 1.0)
            candidate_error[worse] = distance(candidate[worse], xyz[worse])

        # Keep a new guess only where it is at least as close as the old one
        better = candidate_error <= error
        rgb[better] = candidate[better]
        error[better] = candidate_error[better]

    return rgb.reshape(shape), error.reshape(shape[:-1])


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
