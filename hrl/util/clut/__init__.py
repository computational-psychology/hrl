"""CLUT (Color Lookup Table) utilities for color calibration."""

from . import evaluate, linearize, measure


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

    for module in [measure, linearize, evaluate]:
        p = clut_subparsers.add_parser(
            module.parser.prog,
            description=module.parser.description,
            parents=[module.parser],
        )
        p.set_defaults(func=module.command)

    return parser_clut
