"""Calibrating a display: measuring it, and turning the measurements into a CLUT.

The usual path:

1. `measure` the color (CIE XYZ) of each channel on its own, swept across its input
   range (`channel_sweeps`), several times per input.
2. `remove_outliers` and `average` the repeated readings.
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
