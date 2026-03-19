"""HRL utility package for calibration and testing."""

import argparse

graphics_argparser = argparse.ArgumentParser(add_help=False)
graphics_arggroup = graphics_argparser.add_argument_group("Graphics settings")
graphics_arggroup.add_argument(
    "-gr",
    "--graphics",
    choices=["gpu", "datapixx", "viewpixx"],
    default="datapixx",
    help="Graphics device (default: datapixx)",
)
graphics_arggroup.add_argument(
    "-wd",
    "--width",
    type=int,
    default=1024,
    help="Screen width in pixels (default: 1024)",
)
graphics_arggroup.add_argument(
    "-hg",
    "--height",
    type=int,
    default=768,
    help="Screen height in pixels (default: 768)",
)
graphics_arggroup.add_argument(
    "-bg",
    "--background",
    type=float,
    default=0.0,
    help="Background intensity (default: 0.0)",
)
graphics_arggroup.add_argument(
    "-sc",
    "--screen",
    type=int,
    default=1,
    help="Screen number (default: 1)",
)
graphics_arggroup.add_argument(
    "-wo",
    "--width_offset",
    type=int,
    default=0,
    help="Horizontal offset for window (default: 0)",
)
