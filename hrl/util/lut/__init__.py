"""LUT (Lookup Table) utilities for gamma correction."""

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
