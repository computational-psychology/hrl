"""CLUT (Color Lookup Table) utilities for color calibration."""

import argparse

triplets_argparser = argparse.ArgumentParser(add_help=False)
triplets_arggroup = triplets_argparser.add_argument_group("CLUT triplets")
triplets_arggroup.add_argument(
    "-b",
    "--bit_depth",
    type=int,
    default=8,
    help="(Sub)sampling resolution (in bits), by default 8 -> 2**8 = 256 levels per channel sweep",
)
triplets_arggroup.add_argument(
    "-mn",
    "--int_min",
    type=float,
    default=0.0,
    help="Minimum channel intensity, by default 0.0",
)
triplets_arggroup.add_argument(
    "-mx",
    "--int_max",
    type=float,
    default=1.0,
    help="Maximum channel intensity, by default 1.0",
)
triplets_arggroup.add_argument(
    "-n",
    "--n_samples",
    type=int,
    default=5,
    help="Samples per RGB triplet, by default 5",
)
triplets_arggroup.add_argument(
    "-rn",
    "--randomize",
    action="store_true",
    help="Randomize triplet order?",
)
triplets_arggroup.add_argument(
    "-rv",
    "--reverse",
    action="store_true",
    help="Reverse triplet order?",
)


from . import linearize, measure, smooth, verify


def register_clut_commands(parent_subparsers):

    parser_clut = parent_subparsers.add_parser(
        "clut",
        help="Scripts for generating color correction lookup tables",
        description="""
        These scripts generate color lookup tables (CLUTs) to linearize
        RGB output and estimate RGB->XYZ conversion relationships from
        colorimetric measurements.
        """,
    )
    clut_subparsers = parser_clut.add_subparsers(
        title="clut commands",
        dest="clut_command",
        required=True,
        help="Available CLUT operations",
    )

    for module in [measure, smooth, linearize, verify]:
        p = clut_subparsers.add_parser(
            module.parser.prog,
            description=module.parser.description,
            parents=[module.parser],
        )
        p.set_defaults(func=module.command)

    return parser_clut
