import argparse
from datetime import timedelta
from functools import partial
from pathlib import Path
from timeit import default_timer as timer

from hrl import HRL
from hrl.cluts import _draw_uniform_rgb_square, _setup_rgb_triplets, measure
from hrl.util.clut import triplets_argparser

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
    Measure the relationship between RGB triplets (channel-isolated sweeps)
    and CIE XYZ tristimulus values, and save to 'measure.csv'.
    This is the first step in generating a CLUT.
    """,
    add_help=False,
    parents=[triplets_argparser, measurement_argparser],
)
parser.add_argument(
    "-o",
    "--out_file",
    type=Path,
    default="measure.csv",
    help="path to output measurements csv, by default 'measure.csv'",
)


def command(parsed_args):
    """Measure the relationship between RGB triplets and XYZ tristimulus values."""

    start = timer()

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
    )

    triplets = _setup_rgb_triplets(
        i_min=parsed_args.int_min,
        i_max=parsed_args.int_max,
        n_steps=2**parsed_args.bit_depth,
        n_samples=parsed_args.n_samples,
        shuffle=parsed_args.randomize,
        reverse=parsed_args.reverse,
    )
    print(
        f"Measuring {len(triplets)} RGB triplets "
        f"([{parsed_args.int_min}, {parsed_args.int_max}] per channel sweep)..."
    )

    measure(
        ihrl,
        triplets=triplets,
        stim_draw_func=partial(_draw_uniform_rgb_square, patch_size=parsed_args.patch_size),
        out_file=parsed_args.out_file,
        sleep_time=parsed_args.sleep_time,
    )

    ihrl.close()

    end = timer()
    print(f"Time elapsed: {timedelta(seconds=end - start)}")


if __name__ == "__main__":
    command(parser.parse_args())
