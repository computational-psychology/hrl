#!/usr/bin/env python -O

import argparse


def main():
    """Main entry point for hrl-util CLI."""
    from hrl.util.lut import register_lut_commands

    toplevel_parser = argparse.ArgumentParser(
        prog="hrl-util",
        description="""
        Welcome to the HRL utility program. From here, various scripts can be
        accessed for calibrating and testing configurations of experiment hardware.
        """,
    )
    toplevel_subparsers = toplevel_parser.add_subparsers(
        dest="command",
        required=True,
        metavar="<command>",
    )

    register_lut_commands(toplevel_subparsers)

    args = toplevel_parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
