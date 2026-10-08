import argparse
from pathlib import Path

import numpy as np

from hrl.cluts import differences
from hrl.cluts.calibrate import average, predict, predict_from_channels, read_measurements

parser = argparse.ArgumentParser(
    prog="evaluate",
    description="""
    Score a CLUT against measurements taken with it applied (e.g. by 'measure
    --lut'): how far the measured colors are from what the CLUT predicts, in
    luminance and in chromaticity, for each kind of reading measured: each
    channel on its own, greys, and other mixtures.

    Readings 'measure' labels for a particular check are also checked for it:
    mixtures labelled 'additivity' against the sum of their parts, measured
    alone in the same session. That check needs no CLUT (--lut).
    """,
    add_help=False,
)
parser.add_argument(
    "-l",
    "--lut",
    type=Path,
    default=None,
    help="path to the CLUT the measurements were taken with; without one, only the "
    "checks that need none",
)
parser.add_argument(
    "-i",
    "--in_file",
    type=Path,
    default="measure.csv",
    help="path to measurements csv, by default 'measure.csv'",
)
parser.add_argument(
    "-ml",
    "--min_level",
    type=float,
    default=0.1,
    help="leave out inputs whose brightest channel is below this, where readings are "
    "mostly noise, by default 0.1",
)


def _summary(name, off):
    """One line: how many, and how far off in luminance, in chromaticity, and in XYZ."""
    if len(off) == 0:
        return f"  {name:20s}      none measured"
    xyz, luminance, chromaticity = off[:, 0], 100 * off[:, 1], off[:, 2]
    return (
        f"  {name:20s} {len(off):5d}   "
        f"{np.mean(luminance):+6.2f}%  {np.mean(np.abs(luminance)):5.2f}%   "
        f"{np.median(chromaticity):.4f}  {np.percentile(chromaticity, 95):.4f}   "
        f"{np.median(xyz):6.3f}"
    )


def report(measurements, clut=None, labels=None, min_level=0.1):
    """A text report of how well `clut` predicts `measurements`, and of the checks they
    were labelled for.

    Every reading is compared with what the CLUT predicts for it, if one is given.
    Readings labelled for a particular check, as `measure` labels them, are also checked
    for that, with a CLUT or without:

    - ``additivity``: mixtures against what their parts, measured alone in the same set,
      predict (`hrl.cluts.calibrate.predict_from_channels`).

    Only what the measurements include is reported.

    Parameters
    ----------
    measurements : array-like
        table with columns ``R, G, B, X, Y, Z``, measured with `clut` applied
    clut : Array[float], optional
        the CLUT, shape (L, 13); without it, only the checks that need none
    labels : sequence of str, optional
        what each reading was measured for, one per row; by default none
    min_level : float, optional
        inputs whose brightest channel is below this are left out of the comparison with
        the CLUT, by default 0.1

    Returns
    -------
    str
    """
    measurements = np.asarray(measurements, dtype=float)
    labels = np.asarray([""] * len(measurements) if labels is None else labels, dtype=str)

    # Repeated readings averaged, within each label
    groups = [(label, average(measurements[labels == label])) for label in dict.fromkeys(labels)]
    comparison = np.vstack([table for _, table in groups])
    labels = np.concatenate([[label] * len(table) for label, table in groups])

    lines = []
    if clut is not None:
        # What each reading is: how many channels it has on, and whether it is a grey
        rgb = comparison[:, :3]
        lit = (rgb > 0.0).sum(axis=1)
        grey = (lit == 3) & np.all(rgb == rgb[:, :1], axis=1)

        # The kinds of reading, each as the rows that are of that kind
        names = ["red alone", "green alone", "blue alone"]
        kinds = [(name, (lit == 1) & (rgb[:, c] > 0.0)) for c, name in enumerate(names)]
        kinds += [("greys (R = G = B)", grey), ("other mixtures", (lit >= 2) & ~grey)]

        # Which readings to compare: those with a channel at `min_level` or above
        kept = rgb.max(axis=1) >= min_level

        # How far each reading is from what the CLUT predicts for it
        off = differences(comparison[:, 3:], predict(comparison, clut))

        # The table: a row per kind of reading measured, then all together
        chromaticity_header = "chromaticity (xy)"
        lines += [
            f"Measured against the CLUT's prediction, inputs with a channel at {min_level} or "
            f"above ({kept.sum()} of {len(comparison)}):",
            "",
            f"  {'':20s} {'n':>5s}   {'luminance':>16s}   {chromaticity_header:>20s}   {'XYZ':>6s}",
            f"  {'':20s} {'':5s}   {'mean':>7s}  {'|mean|':>6s}   {'median':>6s}  {'95th':>6s}"
            f"   {'median':>6s}",
        ]
        lines += [_summary(name, off[kept & rows]) for name, rows in kinds if rows.any()]
        lines.append(_summary("all", off[kept]))

    # Mixtures against the sum of their parts, all from the set measured for it
    additivity = comparison[labels == "additivity"]
    if len(additivity) > 0:
        try:
            expected = predict_from_channels(additivity)
        except ValueError as error:
            lines += ["", f"Cannot check additivity: {error}."]
        else:
            # Only mixtures, and only those their parts were measured for
            mixture = (additivity[:, :3] > 0.0).sum(axis=1) >= 2
            predictable = ~np.isnan(expected).any(axis=1)
            mixtures = mixture & predictable

            lines += [
                "",
                "Mixtures against the sum of their parts, measured alone in this session:",
                "",
                _summary("mixtures", differences(additivity[mixtures, 3:], expected[mixtures])),
            ]

    if not lines:
        lines = [
            "Nothing to report: no CLUT to compare with, and no readings labelled for a check."
        ]
    return "\n".join(lines).lstrip("\n")


def command(parsed_args):
    in_file = parsed_args.in_file.expanduser().resolve()
    measurements, labels = read_measurements(in_file)

    # The CLUT the measurements were taken with, if given
    clut = None
    if parsed_args.lut is not None:
        clut_file = parsed_args.lut.expanduser().resolve()
        print(f"Loading CLUT from {clut_file} and measurements from {in_file} ...\n")
        clut = np.genfromtxt(clut_file, delimiter=",", skip_header=1)
    else:
        print(f"Loading measurements from {in_file}, without a CLUT ...\n")

    print(report(measurements, clut, labels=labels, min_level=parsed_args.min_level))


if __name__ == "__main__":
    command(parser.parse_args())
