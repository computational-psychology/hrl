import argparse
from datetime import timedelta
from functools import partial
from timeit import default_timer as timer

from hrl import HRL
from hrl.calibration.measurement import draw_uniform_square, measure_lut, setup_intensities
from hrl.util import graphics_argparser
from hrl.util.lut import intensities_argparser

measurement_argparser = argparse.ArgumentParser(add_help=False, parents=[graphics_argparser])

measurement_arggroup = measurement_argparser.add_argument_group("Measuring")
measurement_arggroup.add_argument(
    "-p",
    "--photometer",
    type=str,
    default="minolta",
    help="Photometer to use, by default 'minolta'",
)
measurement_arggroup.add_argument(
    "-n",
    "--n_samples",
    type=int,
    default=5,
    help="Samples per intensity, by default 5",
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
    This script measures the relationship between the desired intensity (a
    normalized value between 0 and 1) given to the monitor, and the luminance
    produced by the monitor, and saves it to the file 'measure.csv'. This is
    the first step in generating a lookup table for normalizing a monitor's
    luminance.
    """,
    add_help=False,
    parents=[intensities_argparser, measurement_argparser],
)
parser.add_argument(
    "-o",
    "--out_file",
    type=str,
    default="measure.csv",
    help="Output filename, by default 'measure.csv'",
)


def command(parsed_args):
    """Measure the relationship between intensity and luminance."""

    # Starting timer
    start = timer()

    # Initializing HRL
    headers = ["Intensity"] + ["Luminance" + str(i) for i in range(parsed_args.n_samples)]

    ihrl = HRL(
        graphics=parsed_args.graphics,
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
    intensities = setup_intensities(
        parsed_args.int_min,
        parsed_args.int_max,
        2**parsed_args.bit_depth,
        parsed_args.randomize,
        parsed_args.reverse,
    )
    print(
        f"Measuring {len(intensities)} intensity values ([{parsed_args.int_min}, {parsed_args.int_max}])..."
    )

    # Measure luminance for intensity values
    measure_lut(
        ihrl,
        intensities=intensities,
        stim_draw_func=partial(draw_uniform_square, patch_size=parsed_args.patch_size),
        n_samples=parsed_args.n_samples,
        sleep_time=parsed_args.sleep_time,
    )

    # Experiment is over!
    ihrl.close()

    # Time elapsed
    end = timer()
    print(f"Time elapsed: {timedelta(seconds=end - start)}")


if __name__ == "__main__":
    command(parser.parse_args())
