import argparse
from datetime import timedelta
from random import shuffle
from timeit import default_timer as timer

import numpy as np

from hrl import HRL

parser = argparse.ArgumentParser(
    prog="hrl-util lut measure",
    description="""
    This script measures the relationship between the desired intensity (a
    normalized value between 0 and 1) given to the monitor, and the luminance
    produced by the monitor, and saves it to the file 'measure.csv'. This is
    the first step in generating a lookup table for normalizing a monitor's
    luminance.
    """,
)

parser.add_argument(
    "-sz",
    "--patch_size",
    default=0.5,
    type=float,
    help="Size of calibration patch, as fraction of total screen size, by default 0.5",
)

parser.add_argument(
    "-b",
    "--bit_depth",
    default=16,
    type=int,
    help="Sampling resolution (in bits), by default 16 -> 2**16 = 65536 levels",
)

parser.add_argument(
    "-mn",
    "--int_min",
    default=0.0,
    type=float,
    help="Minimum sampled intensity, by default 0.0",
)

parser.add_argument(
    "-mx",
    "--int_max",
    default=1.0,
    type=float,
    help="Maximum sampled intensity, by default 1.0",
)

parser.add_argument(
    "-n",
    "--n_samples",
    default=5,
    type=int,
    help="Number samples to be taken at each intensity, by default 5",
)

parser.add_argument(
    "-sl",
    "--sleep_time",
    default=200,
    type=int,
    help="time (ms) to wait between each measurement, by default 200",
)

parser.add_argument(
    "-rn",
    "--randomize",
    action="store_true",
    help="Randomize order of intensity values, by default False",
)

parser.add_argument(
    "-rv",
    "--reverse",
    action="store_true",
    help="Reverse order of intensity values (high to low rather than low to high), by default False",
)

parser.add_argument(
    "-p",
    "--photometer",
    type=str,
    default="optical",
    help="Photometer to use, by default 'optical'",
)

parser.add_argument(
    "-o",
    "--out_file",
    type=str,
    default="measure.csv",
    help="Output filename, by default 'measure.csv'",
)

parser.add_argument(
    "-bg",
    "--background",
    type=float,
    default=0.0,
    help="Background intensity ([0, 1]) outside of the central patch, by default 0",
)

parser.add_argument(
    "-wd",
    "--width",
    type=int,
    default=1024,
    help="Screen resolution width in pixels, by default 1024. Should coincide with the settings in xorg.conf",
)

parser.add_argument(
    "-hg",
    "--height",
    type=int,
    default=768,
    help="Screen resolution height in pixels, by default 768. Should coincide with the settings in xorg.conf",
)

parser.add_argument(
    "-gr",
    "--graphics",
    choices=["gpu", "datapixx", "viewpixx"],
    default="datapixx",
    help="Graphics device to use, by default 'datapixx'",
)

parser.add_argument(
    "-sc",
    "--screen",
    type=int,
    default=1,
    help="Screen number, by default: 1",
)

parser.add_argument(
    "-wo",
    "--width_offset",
    type=int,
    default=0,
    help="Horizontal offset for window in pixels, by default 0. Useful for configurations with a single Xscreen and multiple monitors.",
)


def measure(args):
    parsed_args = parser.parse_args(args)

    # Starting timer
    start = timer()

    # Initializing HRL
    headers = ["Intensity"] + ["Luminance" + str(i) for i in range(parsed_args.n_samples)]

    screen_width = parsed_args.width
    screen_height = parsed_args.height

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
        flnm=parsed_args.out_file,
        hdrs=headers,
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
    main()
