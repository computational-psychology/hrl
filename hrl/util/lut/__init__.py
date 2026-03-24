"""LUT (Lookup Table) utilities for gamma correction."""

import argparse

intensities_argparser = argparse.ArgumentParser(add_help=False)
intensities_arggroup = intensities_argparser.add_argument_group("LUT intensities")
intensities_arggroup.add_argument(
    "-b",
    "--bit_depth",
    type=int,
    default=16,
    help="(Sub)sampling resolution (in bits), by default 16 -> 2**16 = 65536 levels",
)
intensities_arggroup.add_argument(
    "-mn",
    "--int_min",
    type=float,
    default=0.0,
    help="Minimum intensity, by default 0.0",
)
intensities_arggroup.add_argument(
    "-mx",
    "--int_max",
    type=float,
    default=1.0,
    help="Maximum intensity, by default 1.0",
)
intensities_arggroup.add_argument(
    "-rn",
    "--randomize",
    action="store_true",
    help="Randomize intensity order?",
)
intensities_arggroup.add_argument(
    "-rv",
    "--reverse",
    action="store_true",
    help="Reverse intensity order?",
)


from . import linearize, measure, plot, smooth, verify


def register_lut_commands(parent_subparsers):

    parser_lut = parent_subparsers.add_parser(
        "lut",
        help="Scripts for generating gamma correction lookup tables",
        description="""
        When considering monitors, one may distinguish between the actual
        luminance produced by the monitor, and the scale free 'intensity'
        that the software and computer request of the monitor. These scripts
        generate lookup tables (LUTs) to linearize the relationship between
        intensity and luminance.
        """,
    )
    lut_subparsers = parser_lut.add_subparsers(
        title="lut commands",
        dest="lut_command",
        required=True,
        help="Available LUT operations",
    )

    for module in [measure, smooth, linearize, plot, verify]:
        p = lut_subparsers.add_parser(
            module.parser.prog,
            description=module.parser.description,
            parents=[module.parser],
        )
        p.set_defaults(func=module.command)

    return parser_lut
