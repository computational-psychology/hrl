import argparse
import csv
from datetime import timedelta
from functools import partial
from pathlib import Path
from timeit import default_timer as timer

import numpy as np

from hrl import HRL
from hrl.cluts.calibrate import _draw_uniform_rgb_square, measure
from hrl.cluts.triplets import channel_mixtures, channel_sweeps

rgb_graphics_argparser = argparse.ArgumentParser(add_help=False)
rgb_graphics_arggroup = rgb_graphics_argparser.add_argument_group("Graphics settings")
rgb_graphics_arggroup.add_argument(
    "-gr",
    "--graphics",
    choices=["RGB", "gpu_RGB", "viewpixx_RGB"],
    default="RGB",
    help="RGB graphics device alias, by default 'RGB'",
)
rgb_graphics_arggroup.add_argument(
    "-wd",
    "--width",
    type=int,
    default=1024,
    help="Screen width in pixels (default: 1024)",
)
rgb_graphics_arggroup.add_argument(
    "-hg",
    "--height",
    type=int,
    default=768,
    help="Screen height in pixels (default: 768)",
)
rgb_graphics_arggroup.add_argument(
    "-bg",
    "--background",
    type=float,
    default=0.0,
    help="Background gray value for RGB display (default: 0.0)",
)
rgb_graphics_arggroup.add_argument(
    "-sc",
    "--screen",
    type=int,
    default=1,
    help="Screen number (default: 1)",
)
rgb_graphics_arggroup.add_argument(
    "-wo",
    "--width_offset",
    type=int,
    default=0,
    help="Horizontal offset for window (default: 0)",
)

measurement_argparser = argparse.ArgumentParser(add_help=False, parents=[rgb_graphics_argparser])

measurement_arggroup = measurement_argparser.add_argument_group("Measuring")
measurement_arggroup.add_argument(
    "-p",
    "--photometer",
    type=str,
    default="i1pro",
    help="Colorimeter to use, by default 'i1pro'",
)
measurement_arggroup.add_argument(
    "-sl",
    "--sleep_time",
    type=int,
    default=200,
    help="Sleep time (ms) between measurements, by default 200",
)

patch_arggroup = measurement_argparser.add_argument_group("Calibration patch")
patch_arggroup.add_argument(
    "-sz",
    "--patch_size",
    type=float,
    default=0.5,
    help="Patch size as fraction of screen, by default 0.5",
)


parser = argparse.ArgumentParser(
    prog="measure",
    description="""
    Measure CIE XYZ tristimulus values for sets of RGB triplets, and save them,
    each labelled with the set it is from, to 'measure.csv'.

    The sets (--sets): 'sweeps', each channel on its own at every level, which
    is the first step in generating a CLUT; and 'mixtures' of the three
    channels, and greys, with each channel alone at the levels they use, which
    check whether the channels add up. Any other triplets can be given in a CSV
    file (--triplets).

    With a CLUT applied (--lut), the same measurements check that CLUT:
    'evaluate' compares them with what it predicts.
    """,
    add_help=False,
    parents=[measurement_argparser],
)

sweeps_arggroup = parser.add_argument_group("Sweep levels")
sweeps_arggroup.add_argument(
    "-b",
    "--bit_depth",
    type=int,
    default=8,
    help="(Sub)sampling resolution (in bits), by default 8 -> 2**8 = 256 levels per channel sweep",
)
sweeps_arggroup.add_argument(
    "-mn",
    "--int_min",
    type=float,
    default=0.0,
    help="Minimum channel intensity, by default 0.0",
)
sweeps_arggroup.add_argument(
    "-mx",
    "--int_max",
    type=float,
    default=1.0,
    help="Maximum channel intensity, by default 1.0",
)

order_arggroup = parser.add_argument_group("Repeats and order")
order_arggroup.add_argument(
    "-n",
    "--n_samples",
    type=int,
    default=5,
    help="Samples per RGB triplet, by default 5",
)
order_arggroup.add_argument(
    "-rn",
    "--randomize",
    action="store_true",
    help="Randomize triplet order?",
)
order_arggroup.add_argument(
    "-rv",
    "--reverse",
    action="store_true",
    help="Reverse triplet order?",
)

parser.add_argument(
    "-o",
    "--out_file",
    type=Path,
    default="measure.csv",
    help="path to output measurements csv, by default 'measure.csv'",
)
parser.add_argument(
    "-l",
    "--lut",
    type=Path,
    default=None,
    help="CLUT to apply while measuring, to check it; by default none",
)
parser.add_argument(
    "-s",
    "--sets",
    nargs="+",
    choices=["sweeps", "mixtures"],
    default=None,
    help="sets of triplets to measure, by default 'sweeps', or none if --triplets is given",
)
parser.add_argument(
    "-t",
    "--triplets",
    type=Path,
    default=None,
    help="CSV file of triplets to measure as well, with columns R, G and B, and "
    "optionally a label for each; by default none",
)

mixtures_arggroup = parser.add_argument_group("Mixtures (--sets mixtures)")
mixtures_arggroup.add_argument(
    "-gs",
    "--grey_steps",
    type=int,
    default=17,
    help="number of greys (R = G = B), evenly spaced over the sweep levels, by default 17",
)
mixtures_arggroup.add_argument(
    "-al",
    "--additivity_levels",
    type=float,
    nargs="+",
    default=[0.25, 0.5, 0.75, 1.0],
    help="per-channel intensities to cross into mixtures, by default 0.25 0.5 0.75 1.0, "
    "which is 64 mixtures plus the readings they are compared against",
)


def command(parsed_args):
    """Measure the relationship between RGB triplets and XYZ tristimulus values."""

    start = timer()

    ihrl = HRL(
        graphics=parsed_args.graphics,
        lut=parsed_args.lut,
        inputs="keyboard",
        photometer=parsed_args.photometer,
        wdth=parsed_args.width,
        hght=parsed_args.height,
        bg=parsed_args.background,
        fs=True,
        wdth_offset=parsed_args.width_offset,
        db=True,
        scrn=parsed_args.screen,
    )

    # The levels each channel is swept over; greys are measured at some of them too
    levels = np.linspace(parsed_args.int_min, parsed_args.int_max, 2**parsed_args.bit_depth)

    # The sets to measure: sweeps, unless asked for others or given triplets
    sets = parsed_args.sets
    if sets is None:
        sets = [] if parsed_args.triplets is not None else ["sweeps"]

    # The triplets to measure, each labelled with the set it is from
    triplets, labels = np.empty((0, 3)), []
    if "sweeps" in sets:
        sweeps = channel_sweeps(levels)
        triplets = np.vstack([triplets, sweeps])
        labels += ["channels"] * len(sweeps)
    if "mixtures" in sets:
        # Greys at sweep levels, so that each channel is also measured alone at levels a
        # CLUT made from the sweeps tabulates
        steps = np.linspace(0, len(levels) - 1, parsed_args.grey_steps).round().astype(int)
        mixtures = channel_mixtures(levels=parsed_args.additivity_levels, grey_levels=levels[steps])
        triplets = np.vstack([triplets, mixtures])
        labels += ["additivity"] * len(mixtures)
    if parsed_args.triplets is not None:
        # Triplets from a file: its R, G and B columns, and its labels, if it has any
        with open(parsed_args.triplets, newline="") as f:
            rows = list(csv.DictReader(f, skipinitialspace=True))
        given = np.array([[float(row[c]) for c in "RGB"] for row in rows]).reshape(-1, 3)
        triplets = np.vstack([triplets, given])
        labels += [row.get("label") or "" for row in rows]
        sets = sets + [str(parsed_args.triplets)]

    print(
        f"Measuring {len(triplets)} RGB triplets ({', '.join(sets)}), "
        f"{parsed_args.n_samples} times each"
        + (f", with CLUT {parsed_args.lut} applied" if parsed_args.lut else "")
        + "..."
    )

    measure(
        ihrl,
        triplets=triplets,
        labels=labels,
        stim_draw_func=partial(_draw_uniform_rgb_square, patch_size=parsed_args.patch_size),
        out_file=parsed_args.out_file,
        sleep_time=parsed_args.sleep_time,
        n_samples=parsed_args.n_samples,
        shuffle=parsed_args.randomize,
        reverse=parsed_args.reverse,
    )

    ihrl.close()

    end = timer()
    print(f"Time elapsed: {timedelta(seconds=end - start)}")


if __name__ == "__main__":
    command(parser.parse_args())
