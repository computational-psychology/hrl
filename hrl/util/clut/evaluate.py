import argparse
from pathlib import Path

import numpy as np

from hrl.cluts import differences
from hrl.cluts.calibrate import average, predict

parser = argparse.ArgumentParser(
    prog="evaluate",
    description="""
    Score a CLUT against measurements taken with it applied (e.g. by 'measure --lut'):
    how far the measured colors are from what the CLUT predicts, in luminance
    and in chromaticity, for each channel on its own.
    """,
    add_help=False,
)
parser.add_argument(
    "-l",
    "--lut",
    type=Path,
    default="clut.csv",
    help="path to the CLUT the measurements were taken with, by default 'clut.csv'",
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


def report(measurements, clut, min_level=0.1):
    """A text report of how well `clut` predicts `measurements`.

    Parameters
    ----------
    measurements : array-like
        table with columns ``R, G, B, X, Y, Z``, measured with `clut` applied
    clut : Array[float]
        the CLUT, shape (L, 13)
    min_level : float, optional
        inputs whose brightest channel is below this are left out, by default 0.1

    Returns
    -------
    str
    """
    # Repeated readings averaged
    comparison = average(measurements)

    # Which readings to compare: those with a channel at `min_level` or above
    rgb = comparison[:, :3]
    kept = rgb.max(axis=1) >= min_level

    # How far each reading is from what the CLUT predicts for it
    off = differences(comparison[:, 3:], predict(comparison, clut))

    # The table: a row per channel, then all together
    chromaticity_header = "chromaticity (xy)"
    lines = [
        f"Measured against the CLUT's prediction, inputs with a channel at {min_level} or "
        f"above ({kept.sum()} of {len(comparison)}):",
        "",
        f"  {'':20s} {'n':>5s}   {'luminance':>16s}   {chromaticity_header:>20s}   {'XYZ':>6s}",
        f"  {'':20s} {'':5s}   {'mean':>7s}  {'|mean|':>6s}   {'median':>6s}  {'95th':>6s}"
        f"   {'median':>6s}",
    ]
    for channel, name in enumerate(["red alone", "green alone", "blue alone"]):
        lines.append(_summary(name, off[kept & (rgb[:, channel] > 0.0)]))
    lines.append(_summary("all", off[kept]))

    return "\n".join(lines)


def command(parsed_args):
    clut_file = parsed_args.lut.expanduser().resolve()
    in_file = parsed_args.in_file.expanduser().resolve()
    print(f"Loading CLUT from {clut_file} and measurements from {in_file} ...\n")

    clut = np.genfromtxt(clut_file, delimiter=",", skip_header=1)
    measurements = np.genfromtxt(in_file, delimiter=",", skip_header=1)

    print(report(measurements, clut, min_level=parsed_args.min_level))


if __name__ == "__main__":
    command(parser.parse_args())
