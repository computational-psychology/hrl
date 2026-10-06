"""Sets of RGB triplets to show and measure.

Each function gives a set of input RGB triplets, each triplet once, for a purpose:

`channel_sweeps`
    each channel on its own, across its range: what a CLUT is built from.
`channel_mixtures`
    mixtures of the channels, and greys, with the parts they are made of: what checks
    whether the channels add up.

How often each triplet is measured, and in what order, is up to whoever measures them
(see `hrl.cluts.calibrate.measure`).
"""

import numpy as np


def channel_sweeps(levels=256):
    """Each channel on its own, at each of `levels`: red, then green, then blue.

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

    Examples
    --------
    >>> channel_sweeps(3)
    array([[0. , 0. , 0. ],
           [0.5, 0. , 0. ],
           [1. , 0. , 0. ],
           [0. , 0. , 0. ],
           [0. , 0.5, 0. ],
           [0. , 1. , 0. ],
           [0. , 0. , 0. ],
           [0. , 0. , 0.5],
           [0. , 0. , 1. ]])
    """
    if np.ndim(levels) == 0:
        levels = np.linspace(0.0, 1.0, int(levels))
    levels = np.asarray(levels, dtype=float).reshape(-1)

    triplets = np.zeros((3, len(levels), 3))
    for channel in range(3):
        triplets[channel, :, channel] = levels
    return triplets.reshape(-1, 3)


def channel_mixtures(levels=(0.25, 0.5, 0.75, 1.0), grey_levels=None):
    """Mixtures of the three channels, and the parts they are made of.

    Every combination of `levels` across the three channels, and greys (R = G = B) at
    `grey_levels`; with each channel on its own at every level used, and black. The parts
    are what a mixture is compared against when checking whether the channels add up
    (`hrl.cluts.calibrate.predict_from_channels`): that only works if they are measured
    too, in the same session, at the same levels.

    Parameters
    ----------
    levels : array-like, optional
        per-channel levels to cross into mixtures, by default 0.25, 0.5, 0.75 and 1.0,
        which is 64 mixtures; nine levels would be 729
    grey_levels : int or array-like, optional
        levels for greys as well: a number of levels evenly spaced from 0 to 1, or the
        levels themselves; by default none beyond those among the mixtures

    Returns
    -------
    numpy.ndarray
        columns ``R, G, B``: black; each channel alone at each level, red then green then
        blue; the mixtures; then the greys not already among them.

    Examples
    --------
    >>> len(channel_mixtures())  # black, 3 x 4 alone, 4**3 mixtures
    77
    >>> len(channel_mixtures(grey_levels=5))  # 3 more levels alone, 3 more greys
    89
    """
    # The levels to mix, and the grey levels, each as a list of levels
    levels = np.asarray(levels, dtype=float).reshape(-1)
    if grey_levels is None:
        grey_levels = np.empty(0)
    elif np.ndim(grey_levels) == 0:
        grey_levels = np.linspace(0.0, 1.0, int(grey_levels))
    grey_levels = np.asarray(grey_levels, dtype=float).reshape(-1)

    # Every combination of the levels across the three channels
    mixtures = np.stack(np.meshgrid(levels, levels, levels, indexing="ij"), axis=-1)
    mixtures = mixtures.reshape(-1, 3)

    # Greys beyond black and the mixtures' own, and the levels their parts add
    greys = [g for g in np.unique(grey_levels) if g > 0.0 and g not in levels]
    alone_levels = np.concatenate([levels, greys])
    grey_triplets = np.repeat(np.reshape(greys, (-1, 1)), 3, 1)

    # Each channel on its own, at every level the mixtures and greys use
    alone = np.zeros((3, len(alone_levels), 3))
    for channel in range(3):
        alone[channel, :, channel] = alone_levels
    alone = alone.reshape(-1, 3)

    # Black first, then the parts, then what is made of them
    return np.vstack([np.zeros((1, 3)), alone, mixtures, grey_triplets])
