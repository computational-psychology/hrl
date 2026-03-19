import argparse
from datetime import timedelta
from random import shuffle
from timeit import default_timer as timer

import numpy as np

from hrl import HRL
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
    lut = parsed_args.lut

    # Starting timer
    start = timer()

    # Initializing HRL
    filename = parsed_args.out_file
    headers = ["Intensity"] + ["Luminance" + str(i) for i in range(parsed_args.n_samples)]

    graphics = parsed_args.graphics
    photometer = parsed_args.photometer
    screen = parsed_args.screen
    screen_width = parsed_args.width
    screen_height = parsed_args.height
    width_offset = parsed_args.width_offset
    background_intensity = parsed_args.background

    ihrl = HRL(
        graphics=graphics,
        inputs="keyboard",
        photometer=photometer,
        wdth=screen_width,
        hght=screen_height,
        bg=background_intensity,
        fs=True,
        lut=lut,
        wdth_offset=width_offset,
        db=True,
        scrn=screen,
        rfl=filename,
        rhds=headers,
    )

    steps = 2**parsed_args.bit_depth
    intensities = np.linspace(parsed_args.int_min, parsed_args.int_max, steps)
    if parsed_args.randomize:
        shuffle(intensities)
    if parsed_args.reverse:
        intensities = intensities[::-1]

    (patch_width, patch_height) = (
        screen_width * parsed_args.patch_size,
        screen_height * parsed_args.patch_size,
    )
    patch_position = ((screen_width - patch_width) / 2, (screen_height - patch_height) / 2)
    print(patch_width)
    print(patch_position)
    print(patch_height)

    for c, intensity in enumerate(intensities):
        ihrl.results["Intensity"] = intensity

        patch = ihrl.graphics.newTexture(np.array([[intensity]]))
        patch.draw(patch_position, (patch_width, patch_height))
        ihrl.graphics.flip()

        print(
            f"Current Intensity: {intensity:.2f} [progress: {c / len(intensities) * 100}% -- {c:d} of {len(intensities)}]"
        )
        samples = []
        for i in range(parsed_args.n_samples):
            samples.append(ihrl.photometer.readLuminance(5, parsed_args.sleep_time))

        for i in range(len(samples)):
            ihrl.results["Luminance" + str(i)] = samples[i]

        ihrl.writeResultLine()

        if ihrl.inputs.checkEscape():
            break

    # Experiment is over!
    ihrl.close()

    # Time elapsed
    end = timer()
    print(f"Time elapsed: {timedelta(seconds=end - start)}")


if __name__ == "__main__":
    command(argparse.ArgumentParser(parents=[parser]).parse_args())
