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
    dest="sz",
    default=0.5,
    type=float,
    help="The size of the central patch, as a fraction of the total screen size. Default: 0.5",
)

parser.add_argument(
    "-s",
    dest="stps",
    default=65536,
    type=int,
    help="The number of unique intensity values to be sampled. Default: 65536",
)

parser.add_argument(
    "-mn",
    dest="mn",
    default=0.0,
    type=float,
    help="The minimum sampled intensity. Default: 0.0",
)

parser.add_argument(
    "-mx",
    dest="mx",
    default=1.0,
    type=float,
    help="The maximum sampled intensity. Default: 1.0",
)

parser.add_argument(
    "-n",
    dest="nsmps",
    default=5,
    type=int,
    help="The number of samples to be taken at each intensity. Default: 5",
)

parser.add_argument(
    "-sl",
    dest="slptm",
    default=200,
    type=int,
    help="The number of milliseconds to wait between each measurement. Default:200",
)

parser.add_argument(
    "-r",
    dest="rndm",
    action="store_true",
    help="Shall we randomize the order of intensity values? Default: False",
)

parser.add_argument(
    "-v",
    dest="rvs",
    action="store_true",
    help="Shall we reverse the order of intensity values"
    + " (high to low rather than low to high)? Default: False",
)

parser.add_argument(
    "-p",
    dest="photometer",
    type=str,
    default="optical",
    help="The photometer to use. Default: optical",
)

parser.add_argument(
    "-o",
    dest="flnm",
    type=str,
    default="lut_test.csv",
    help="The output filename. Default: lut_test.csv",
)

parser.add_argument(
    "-l",
    dest="lut",
    type=str,
    default="lut.csv",
    help="The lookup table filename. Default: lut.csv",
)

parser.add_argument(
    "-bg",
    dest="bg",
    type=float,
    default=0.0,
    help="The background intensity outside of the central patch. Default: 0",
)

parser.add_argument(
    "-wd",
    dest="wd",
    type=int,
    default=1024,
    help="The screen resolution width, in pixels."
    + " It should coincide with the settings in xorg.conf. Default: 1024",
)

parser.add_argument(
    "-hg",
    dest="hg",
    type=int,
    default=768,
    help="The screen resolution height, in pixels."
    + " It should coincide with the settings in xorg.conf. Default: 768",
)

parser.add_argument(
    "-gr",
    dest="graphics",
    type=str,
    default="datapixx",
    help="Whether using the GPU (gpu) or the DataPixx interface (datapixx). Default: datapixx",
)

parser.add_argument(
    "-sc",
    dest="scrn",
    type=str,
    default=1,
    help="Screen number. Default: 1",
)

parser.add_argument(
    "-wo",
    dest="wdth_offset",
    type=int,
    default=0,
    help="Horizontal offset for window."
    + " Useful for setups with a single Xscreen but multiple monitors (Xinerame). Default: 0",
)


def verify(args):
    parsed_args = parser.parse_args(args)

    lut = parsed_args.lut

    # Starting timer
    start = timer()

    # Initializing HRL
    filename = parsed_args.flnm
    headers = ["Intensity"] + ["Luminance" + str(i) for i in range(parsed_args.nsmps)]

    graphics = parsed_args.graphics
    photometer = parsed_args.photometer
    screen = parsed_args.scrn
    screen_width = parsed_args.wd
    screen_height = parsed_args.hg
    width_offset = parsed_args.wdth_offset
    background_intensity = parsed_args.bg

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

    intensities = np.linspace(parsed_args.mn, parsed_args.mx, parsed_args.stps)
    if parsed_args.rndm:
        shuffle(intensities)
    if parsed_args.rvs:
        intensities = intensities[::-1]

    (patch_width, patch_height) = (screen_width * parsed_args.sz, screen_height * parsed_args.sz)
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
        for i in range(parsed_args.nsmps):
            samples.append(ihrl.photometer.readLuminance(5, parsed_args.slptm))

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
