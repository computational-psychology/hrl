"""Calibrating a display: measuring it, and turning the measurements into a CLUT.

The usual path:

1. `measure` the color (CIE XYZ) of each channel on its own, swept across its input
   range (`channel_sweeps`), several times per input.
2. `remove_outliers` and `average` the repeated readings.
3. `smooth` each channel's readings over neighbouring inputs.
4. `make_monotonic`: fit each channel's readings with curves that never go down.
5. `linearize` them into a CLUT.

To check a CLUT, measure again with it applied (``python -m hrl.util clut measure --lut CLUT``):
`predict` gives the color the CLUT expects for each reading, and
`hrl.cluts.colorimetry.differences` says how far apart they are.
"""

from functools import partial
from pathlib import Path

import numpy as np


def channel_sweeps(levels=256):
    """Each channel (R, G, B) on its own, at each `levels`.

    Parameters
    ----------
    levels : int or array-like, optional
        the input levels each channel is swept through: a number of levels evenly spaced
        from 0 to 1, or the levels themselves; by default 256

    Returns
    -------
    numpy.ndarray
        shape ``(3 * len(levels), 3)``, columns ``R, G, B``: the red sweep, the green
        sweep, then the blue sweep. A level of 0 gives black, once per channel.
    """
    # If levels is a single number, create that many evenly spaced levels from 0 to 1
    if np.ndim(levels) == 0:
        levels = np.linspace(0.0, 1.0, int(levels))

    levels = np.asarray(levels, dtype=float).reshape(-1)

    # Construct triplets
    triplets = np.zeros((3, len(levels), 3))
    for channel in range(3):
        triplets[channel, :, channel] = levels

    return triplets.reshape(-1, 3)


def _draw_uniform_rgb_square(ihrl, triplet, patch_size=0.5):
    """Draw a centered RGB square patch for CLUT measurements.

    Parameters
    ----------
    ihrl : HRL
        HRL instance used for drawing and flipping
    triplet : array-like
        RGB triplet in [0.0, 1.0]
    patch_size : float, optional
        size of patch as fraction of the screen, by default 0.5
    """
    screen_width, screen_height = ihrl.graphics.width, ihrl.graphics.height
    patch_width = screen_width * patch_size
    patch_height = screen_height * patch_size
    patch_position = (
        (screen_width - patch_width) / 2,
        (screen_height - patch_height) / 2,
    )
    patch = ihrl.graphics.newTexture(np.array([[triplet]], dtype=float))
    patch.draw(patch_position, (patch_width, patch_height))
    ihrl.graphics.flip()


def measure(
    ihrl,
    triplets,
    stim_draw_func=partial(_draw_uniform_rgb_square, patch_size=0.5),
    out_file=None,
    sleep_time=200,
    n_samples=1,
    shuffle=False,
    reverse=False,
):
    """Measure CIE XYZ tristimulus values for a sequence of RGB triplets.

    Parameters
    ----------
    ihrl : HRL
        HRL instance with a configured colorimeter.
    triplets : array-like
        RGB triplets to measure, shape ``(N, 3)``, each once.
    stim_draw_func : callable, optional
        function with signature ``(ihrl, triplet)`` that draws the stimulus,
        by default a centered uniform square patch.
    out_file : str or Path, optional
        output CSV path, by default None (no file output).
    sleep_time : float, optional
        delay in ms passed to the colorimeter, by default 200.
    n_samples : int, optional
        how many times each triplet is measured, by default 1
    shuffle : bool, optional
        measure the triplets, repeats included, in random order; by default False
    reverse : bool, optional
        measure them in reverse order; by default False

    Returns
    -------
    numpy.ndarray
        table with columns ``R, G, B, X, Y, Z``, in the order measured.
    """
    triplets = np.asarray(triplets, dtype=float)

    # Apply repeats and ordering
    triplets = np.repeat(triplets, n_samples, axis=0)
    if shuffle:
        triplets = triplets[np.random.permutation(len(triplets))]
    if reverse:
        triplets = triplets[::-1]

    # Write to file?
    if out_file is not None:
        out_file = Path(out_file).expanduser().resolve()

    measurements = np.full((len(triplets), 6), np.nan, dtype=float)

    for idx_triplet, triplet in enumerate(triplets):
        print(
            "Current Triplet: "
            f"({triplet[0]:.3f}, {triplet[1]:.3f}, {triplet[2]:.3f}) "
            f"[{idx_triplet:d} of {len(triplets)} "
            f"({idx_triplet / len(triplets):.2%}%)]"
        )

        measurements[idx_triplet, :3] = triplet

        # Draw (update) stimulus
        stim_draw_func(ihrl, triplet)

        # Measure tristimulus
        xyz = ihrl.photometer.readTristimulus(5, int(sleep_time))
        measurements[idx_triplet, 3:] = xyz

        # Write measured samples to file
        if out_file is not None:
            np.savetxt(
                out_file,
                measurements,
                delimiter=",",
                header="R,G,B,X,Y,Z",
                comments="",
            )

        if ihrl.inputs is not None and ihrl.inputs.checkEscape():
            break

    return measurements


def remove_outliers(measurements, abs_tol=0.075, rel_tol=0.0075):
    """Remove outlier tristimulus measurements within repeated RGB triplets.

    Outliers are identified within each repeated RGB triplet group based on
    nearest-neighbor distance in XYZ space.

    Parameters
    ----------
    measurements : array-like
        table with columns ``R, G, B, X, Y, Z``
    abs_tol : float, optional
        absolute tolerance in XYZ Euclidean distance, by default 0.075
    rel_tol : float, optional
        relative tolerance vs. XYZ norm, by default 0.0075

    Returns
    -------
    numpy.ndarray
        measurements with outlier XYZ rows set to NaN
    """
    measurements = np.asarray(measurements, dtype=float)

    # Sort by triplet and then by XYZ norm so nearest neighbors are adjacent per triplet.
    xyz_norm = np.linalg.norm(measurements[:, 3:], axis=1)
    sort_idx = np.lexsort(
        (
            xyz_norm,
            measurements[:, 2],
            measurements[:, 1],
            measurements[:, 0],
        )
    )
    measurements = measurements[sort_idx].copy()
    rgb = measurements[:, :3]
    xyz = measurements[:, 3:]
    xyz_norm = xyz_norm[sort_idx]

    # Where each triplet's group of repeats starts and ends
    _, starts = np.unique(rgb, axis=0, return_index=True)
    ends = np.concatenate([starts[1:] - 1, [len(measurements) - 1]])

    # Distance from each reading to the one before it and the one after it, within its
    # group only
    diff_prev = np.linalg.norm(np.diff(xyz, axis=0, prepend=np.full((1, 3), np.inf)), axis=1)
    diff_next = np.linalg.norm(np.diff(xyz, axis=0, append=np.full((1, 3), np.inf)), axis=1)
    diff_prev[starts] = np.inf
    diff_next[ends] = np.inf

    # Distance from each reading to its nearest neighbor
    min_diff = np.minimum(diff_prev, diff_next)

    # Singletons have no neighbors in their triplet group and cannot be outliers.
    min_diff[np.isinf(diff_prev) & np.isinf(diff_next)] = 0.0

    # Outliers are far from their nearest neighbor, both in XYZ and relative to their own
    # norm
    rel_denom = np.where(xyz_norm > 0.0, xyz_norm, np.inf)
    outliers = (min_diff > abs_tol) & ((min_diff / rel_denom) > rel_tol)

    # Mark their XYZ as missing, keeping the triplet
    measurements[outliers, 3:] = np.nan

    return measurements


def average(measurements):
    """Average repeated tristimulus measurements per RGB triplet.

    Parameters
    ----------
    measurements : array-like
        table with columns ``R, G, B, X, Y, Z``

    Returns
    -------
    numpy.ndarray
        averaged table with one row per unique triplet and columns
        ``R, G, B, X, Y, Z``
    """
    measurements = np.asarray(measurements, dtype=float)

    # Drop rows where at least one tristimulus value is NaN.
    valid = ~np.isnan(measurements[:, 3:]).any(axis=1)
    measurements = measurements[valid]

    rgb = measurements[:, :3]
    xyz = measurements[:, 3:]

    unique_rgb, inverse = np.unique(rgb, axis=0, return_inverse=True)
    counts = np.bincount(inverse)

    xyz_avg = np.column_stack(
        [
            np.bincount(inverse, weights=xyz[:, 0]) / counts,
            np.bincount(inverse, weights=xyz[:, 1]) / counts,
            np.bincount(inverse, weights=xyz[:, 2]) / counts,
        ]
    )

    return np.column_stack([unique_rgb, xyz_avg])


def smooth(measurements, width=5):
    """Average each channel's measurements over neighbouring input levels.

    The counterpart of `hrl.luts.smooth` for color measurements. A colorimeter reading
    carries several percent of noise, and averaging repeats at one level only takes that
    down by the square root of the repeat count. Neighbouring levels are measuring
    almost the same thing, so averaging across them removes more of it, at the cost of
    input resolution.

    Each channel's ramp starts at the black reading (every channel at 0), which takes
    part in the average as the ramp's first level, but is itself left as measured: it
    belongs to all three ramps at once.

    Parameters
    ----------
    measurements : array-like
        table with columns ``R, G, B, X, Y, Z``, channel-isolated, one row per triplet,
        as `average` returns
    width : int, optional
        how many neighbouring levels to average over, by default 5, matching the
        five-tap kernel `hrl.luts.smooth` uses. 1 leaves the measurements alone.

    Returns
    -------
    numpy.ndarray
        the same table with X, Y and Z smoothed along each channel's own ramp

    Notes
    -----
    Rows that are not channel-isolated are left untouched.
    """
    measurements = np.asarray(measurements, dtype=float)
    if width <= 1:
        return measurements.copy()

    smoothed = measurements.copy()

    # A moving average over `width` levels, centered on each level
    kernel = np.ones(width) / width
    lead, trail = width // 2, width - 1 - width // 2

    # The black reading, which starts every channel's ramp but is left as measured
    black = np.all(np.isclose(measurements[:, :3], 0.0, atol=1e-10), axis=1)

    for channel in range(3):
        # This channel's ramp: its rows with the other two channels off
        others = [index for index in range(3) if index != channel]
        rows = np.flatnonzero(
            np.isclose(measurements[:, others[0]], 0.0, atol=1e-10)
            & np.isclose(measurements[:, others[1]], 0.0, atol=1e-10)
        )
        # Too few levels to average over: leave the ramp as it is
        if len(rows) < width:
            continue

        # In order of input level, from black up
        rows = rows[np.argsort(measurements[rows, channel])]
        lit = ~black[rows]

        # Average X, Y and Z, each along the ramp
        for axis in range(3):
            # Pad each end with its own value, so the ends are averaged over fewer levels
            padded = np.pad(measurements[rows, 3 + axis], (lead, trail), mode="edge")
            averaged = np.convolve(padded, kernel, "valid")
            smoothed[rows[lit], 3 + axis] = averaged[lit]

    return smoothed


def _monotonic(values):
    """The closest curve to `values` that never goes down.

    Walks through the values, keeping them in blocks, each a run of values averaged
    together. Each new value starts its own block; while the block before it has a
    higher average, the two merge into one block holding their combined average. At
    the end, each block's average fills the positions it covers. So readings that dip
    -- which photometer noise makes happen -- are replaced by their average:
    1, 2, 6, 4, 5, 7 becomes 1, 2, 5, 5, 5, 7.

    "Closest" means the smallest sum of squared differences. (In statistics this is
    called isotonic regression, by the pool-adjacent-violators algorithm.)

    Parameters
    ----------
    values : array-like
        measured values, in the order they should be non-decreasing in

    Returns
    -------
    numpy.ndarray
        non-decreasing, same shape as `values`
    """
    blocks = []  # [average, count], one per run of values averaged together
    for value in np.asarray(values, dtype=float):
        blocks.append([value, 1])
        # Merge with the previous block while it is higher, so the curve never goes down
        while len(blocks) > 1 and blocks[-2][0] > blocks[-1][0]:
            average, count = blocks.pop()
            previous, previous_count = blocks[-1]
            total = previous_count + count
            blocks[-1] = [(previous * previous_count + average * count) / total, total]

    averages, counts = zip(*blocks)
    return np.repeat(averages, counts)


def make_monotonic(measurements):
    """Make each channel's X, Y and Z never go down as its input goes up.

    Driving a channel harder emits more light at every wavelength, so its X, Y and Z can
    only rise with its input; where measured readings go down, that is noise. Each
    channel's X, Y and Z are replaced by the closest curves that never go down
    (`_monotonic`), starting from the black reading. Readings below black are raised to
    it first: a channel on its own cannot be darker than the black screen.

    This is what `linearize` needs: turning a channel's curve around -- which input gives
    a wanted luminance -- has an answer only if the curve never goes down. Smoothing
    first (`smooth`) keeps the fit from having to average long stretches together.

    Parameters
    ----------
    measurements : array-like
        table with columns ``R, G, B, X, Y, Z``, channel-isolated, one row per triplet,
        as `average` and `smooth` return, including a black reading (every channel at 0)

    Returns
    -------
    numpy.ndarray
        the same table with each channel's X, Y and Z never going down along its ramp;
        the black reading, and rows that are not channel-isolated, are left as they are

    Raises
    ------
    ValueError
        if there is no black reading
    """
    measurements = np.asarray(measurements, dtype=float)
    result = measurements.copy()

    # The black reading, which starts every channel's ramp but is left as measured
    black = np.all(np.isclose(measurements[:, :3], 0.0, atol=1e-10), axis=1)
    if not black.any():
        raise ValueError(
            "no reading at RGB (0, 0, 0); each channel's curve starts from the black screen"
        )

    # The black screen's color: what no channel on its own can be darker than
    dark = measurements[black, 3:].mean(axis=0)

    for channel in range(3):
        # This channel's ramp: its rows with the other two channels off
        others = [index for index in range(3) if index != channel]
        rows = np.flatnonzero(
            np.isclose(measurements[:, others[0]], 0.0, atol=1e-10)
            & np.isclose(measurements[:, others[1]], 0.0, atol=1e-10)
        )

        # In order of input level, from black up
        rows = rows[np.argsort(measurements[rows, channel])]
        lit = ~black[rows]

        # X, Y and Z, each raised to at least black, then made to never go down
        for axis in range(3):
            values = np.maximum(measurements[rows, 3 + axis], dark[axis])
            result[rows[lit], 3 + axis] = _monotonic(values)[lit]

    return result


def _channel_subset(measurements, channel, atol=1e-10):
    """Extract channel-isolated rows for a given RGB channel index."""
    other = [idx for idx in range(3) if idx != channel]
    mask = np.isclose(measurements[:, other[0]], 0.0, atol=atol) & np.isclose(
        measurements[:, other[1]], 0.0, atol=atol
    )
    subset = measurements[mask]
    subset = subset[np.argsort(subset[:, channel])]
    return subset


def linearize(measurements, bit_depth=8):
    """Turn channel-isolated XYZ measurements into a CLUT.

    For each channel, finds the drive values at which its luminance goes up in equal
    steps, from its darkest to its brightest. Those drive values are the CLUT's
    ``R_out``, ``G_out``, ``B_out``; with them applied, each channel's luminance is a
    straight line in the input. The XYZ the channel shows at each of them is recorded
    alongside.

    Each channel's luminance has to never go down as its input goes up, which
    `make_monotonic` makes so; measurements where it does go down are refused.

    Parameters
    ----------
    measurements : array-like
        averaged measurements with columns ``R, G, B, X, Y, Z``
    bit_depth : int, optional
        target CLUT input resolution, by default 8

    Returns
    -------
    numpy.ndarray
        CLUT with 13 columns, see `hrl.cluts.clut`:
        ``intensity_in, R_out, G_out, B_out, R_X, R_Y, R_Z, G_X, G_Y, G_Z, B_X, B_Y, B_Z``

    Raises
    ------
    ValueError
        if a channel's luminance goes down anywhere as its input goes up
    """
    measurements = np.asarray(measurements, dtype=float)
    if measurements.ndim != 2 or measurements.shape[1] != 6:
        raise ValueError("measurements must be a 2D array with 6 columns: R,G,B,X,Y,Z")

    n_samples = 2**bit_depth
    intensity_in = np.linspace(0.0, 1.0, n_samples)

    # Determine dark tristimulus from explicit black triplet if available.
    black_mask = np.isclose(measurements[:, :3], 0.0, atol=1e-10).all(axis=1)
    if np.any(black_mask):
        dark_xyz = np.mean(measurements[black_mask, 3:], axis=0)
    else:
        dark_idx = np.argmin(np.sum(measurements[:, :3], axis=1))
        dark_xyz = measurements[dark_idx, 3:]

    channel_out = []
    channel_xyz = []

    for channel in range(3):
        subset = _channel_subset(measurements, channel)
        if len(subset) < 2:
            raise RuntimeError(
                "linearize requires at least two measurements per isolated channel "
                f"for channel index {channel}"
            )

        ch_input = subset[:, channel]
        ch_xyz = subset[:, 3:]

        # Collapse repeated measurements at identical channel input before interpolation.
        unique_input, inverse = np.unique(ch_input, return_inverse=True)
        counts = np.bincount(inverse)
        ch_xyz = np.column_stack(
            [
                np.bincount(inverse, weights=ch_xyz[:, 0]) / counts,
                np.bincount(inverse, weights=ch_xyz[:, 1]) / counts,
                np.bincount(inverse, weights=ch_xyz[:, 2]) / counts,
            ]
        )
        ch_input = unique_input

        # Linearize using Y (luminance) progression per channel. Turning the curve around
        # -- which input gives a wanted luminance -- needs it to never go down.
        y_vals = ch_xyz[:, 1]
        if np.any(np.diff(y_vals) < 0.0):
            raise ValueError(
                f"the {'RGB'[channel]} channel's luminance goes down as its input goes up; "
                "make the measurements monotonic first (`make_monotonic`, which "
                "``hrl-util clut smooth`` runs)"
            )

        # Where the curve is flat, several inputs give the same luminance, and there is
        # no single input to look up. Make each flat stretch one point, at the average of
        # its inputs (and of their X and Z). `np.unique` labels each point with its flat
        # stretch; summing per label and dividing by the number of points in it gives
        # the averages.
        y_unique, run = np.unique(y_vals, return_inverse=True)
        run_size = np.bincount(run)
        ch_input_pooled = np.bincount(run, weights=ch_input) / run_size
        ch_x_pooled = np.bincount(run, weights=ch_xyz[:, 0]) / run_size
        ch_z_pooled = np.bincount(run, weights=ch_xyz[:, 2]) / run_size

        # Except at the bottom: a stretch that starts at drive 0 is black, which is what
        # the CLUT's first row says input 0 shows, so input 0 must drive the channel at 0
        if ch_input[0] == 0.0:
            ch_input_pooled[0] = 0.0

        desired_y = np.linspace(y_unique[0], y_unique[-1], n_samples)

        channel_out.append(np.interp(desired_y, y_unique, ch_input_pooled))
        # Y is the wanted luminance itself, a straight line: that is what linearizing
        # means. X and Z are read off the measurements at it.
        channel_xyz.append(
            np.column_stack(
                [
                    np.interp(desired_y, y_unique, ch_x_pooled),
                    desired_y,
                    np.interp(desired_y, y_unique, ch_z_pooled),
                ]
            )
        )

    rgb_out = np.column_stack(channel_out)

    # At input 0 every channel is off, so the first row holds the black screen for all three
    for xyz in channel_xyz:
        xyz[0] = dark_xyz

    return np.column_stack([intensity_in, rgb_out, *channel_xyz])


def predict(measurements, CLUT):
    """The color a CLUT expects for each measured input.

    For black, or a channel on its own, that is what the CLUT records: black is its first
    row, and a channel on its own is that channel's columns, read at its input -- between
    tabulated inputs, along a straight line.

    Parameters
    ----------
    measurements : array-like
        table with columns ``R, G, B, X, Y, Z`` (or just ``R, G, B``), where R, G, B are
        the inputs passed to graphics with this CLUT applied, each with at most one
        channel on
    CLUT : Array[float]
        Color Lookup Table with shape (L, 13), see `hrl.cluts`.

    Returns
    -------
    numpy.ndarray
        shape (N, 3): the XYZ expected for each row, row for row

    See Also
    --------
    hrl.cluts.colorimetry.differences : how far the measured colors are from these.
    """
    rgb = np.asarray(measurements, dtype=float)[:, :3]
    CLUT = np.asarray(CLUT, dtype=float)

    # With every channel off, the screen is black: the CLUT's first row
    predicted = np.tile(CLUT[0, 4:7], (len(rgb), 1))
    for channel in range(3):
        on = rgb[:, channel] > 0.0
        alone = CLUT[:, 4 + 3 * channel : 7 + 3 * channel]
        predicted[on] = np.column_stack(
            [np.interp(rgb[on, channel], CLUT[:, 0], alone[:, axis]) for axis in range(3)]
        )
    return predicted
