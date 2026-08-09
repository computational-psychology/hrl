import argparse
from datetime import timedelta
from functools import partial
from pathlib import Path
from timeit import default_timer as timer

import numpy as np

from hrl import HRL
from hrl.cluts import _draw_uniform_rgb_square, measure
from hrl.util.clut import triplets_argparser
from hrl.util.clut.measure import measurement_argparser

parser = argparse.ArgumentParser(
    prog="verify",
    description="""
    Verify a CLUT by measuring XYZ values with the CLUT applied,
    ensuring the correction is active and stable.
    """,
    add_help=False,
    parents=[triplets_argparser, measurement_argparser],
)

parser.add_argument(
    "-o",
    "--out_file",
    type=Path,
    default="clut_verification.csv",
    help="Output filename, by default 'clut_verification.csv'",
)

parser.add_argument(
    "-l",
    "--lut",
    type=Path,
    default="clut.csv",
    help="Path to CLUT to verify, by default 'clut.csv'",
)


def command(parsed_args):
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

    clut = np.genfromtxt(parsed_args.lut, skip_header=1, delimiter=",")
    intensities = clut[:, 0]

    # Verify per channel-isolated sweeps at CLUT input levels.
    r_triplets = np.column_stack(
        [intensities, np.zeros_like(intensities), np.zeros_like(intensities)]
    )
    g_triplets = np.column_stack(
        [np.zeros_like(intensities), intensities, np.zeros_like(intensities)]
    )
    b_triplets = np.column_stack(
        [np.zeros_like(intensities), np.zeros_like(intensities), intensities]
    )
    triplets = np.vstack([r_triplets, g_triplets, b_triplets])

    if parsed_args.randomize:
        np.random.shuffle(triplets)
    elif parsed_args.reverse:
        triplets = triplets[::-1]

    print(f"Measuring {len(triplets)} RGB triplets from CLUT ({parsed_args.lut})...")

    measure(
        ihrl,
        triplets=triplets,
        stim_draw_func=partial(_draw_uniform_rgb_square, patch_size=parsed_args.patch_size),
        sleep_time=parsed_args.sleep_time,
        out_file=parsed_args.out_file,
    )

    ihrl.close()
    end = timer()
    print(f"Time elapsed: {timedelta(seconds=end - start)}")


if __name__ == "__main__":
    command(argparse.ArgumentParser(parents=[parser]).parse_args())
