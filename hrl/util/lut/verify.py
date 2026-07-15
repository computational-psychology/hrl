import argparse
from datetime import timedelta
from functools import partial
from timeit import default_timer as timer

import numpy as np

from hrl import HRL
from hrl.calibration.measurement import draw_uniform_square, measure_lut
from hrl.util.lut import intensities_argparser
from hrl.util.lut.measure import measurement_argparser

parser = argparse.ArgumentParser(
    prog="verify",
    description="""
    This script verifies a lookup table by measuring luminance values with
    the LUT applied, ensuring the linearization is working correctly.
    """,
    add_help=False,
    parents=[intensities_argparser, measurement_argparser],
)

parser.add_argument(
    "-o",
    "--out_file",
    type=str,
    default="lut_verification.csv",
    help="Output filename, by default 'lut_verification.csv'",
)

parser.add_argument(
    "-l",
    "--lut",
    type=str,
    default="lut.csv",
    help="Path to LookUp Table to verify, by default 'lut.csv'",
)


def command(parsed_args):

    # Starting timer
    start = timer()

    # Initializing HRL
    headers = ["Intensity"] + ["Luminance" + str(i) for i in range(parsed_args.n_samples)]

    ihrl = HRL(
        graphics=parsed_args.graphics,
        lut=parsed_args.lut,  # Apply the LUT that needs to be verified
        inputs="keyboard",
        photometer=parsed_args.photometer,
        wdth=parsed_args.width,
        hght=parsed_args.height,
        bg=parsed_args.background,
        fs=True,
        wdth_offset=parsed_args.width_offset,
        db=True,
        scrn=parsed_args.screen,
        rfl=parsed_args.out_file,
        rhds=headers,
    )

    # Set up intensity values to be measured
    lut = np.genfromtxt(parsed_args.lut, skip_header=1, delimiter=",")
    intensities = lut[:, 0]  # Use the input intensity values from the LUT
    print(f"Measuring {len(intensities)} intensity values from LUT ({parsed_args.lut})...")
    if parsed_args.randomize:
        np.random.shuffle(intensities)
    elif parsed_args.reverse:
        intensities = intensities[::-1]

    # Measure luminance for intensity values
    measure_lut(
        ihrl,
        intensities=intensities,
        stim_draw_func=partial(draw_uniform_square, patch_size=parsed_args.patch_size),
        n_samples=parsed_args.n_samples,
        sleep_time=parsed_args.sleep_time,
    )

    # Measurement is over!
    ihrl.close()
    end = timer()
    print(f"Time elapsed: {timedelta(seconds=end - start)}")


if __name__ == "__main__":
    command(argparse.ArgumentParser(parents=[parser]).parse_args())
