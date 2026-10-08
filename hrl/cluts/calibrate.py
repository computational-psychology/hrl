"""Calibrating a display: measuring it, and turning the measurements into a CLUT."""

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
