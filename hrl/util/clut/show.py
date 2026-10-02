import argparse
from pathlib import Path

import numpy as np

import hrl.cluts
from hrl import HRL
from hrl.util.clut.measure import rgb_graphics_argparser

parser = argparse.ArgumentParser(
    prog="show",
    description="""
    Show what a CLUT says the display can do, as a visual check of the
    calibration. Its screens, stepped through with Left and Right:

    gamut: every chromaticity the display can show, each at its brightest.

    What each screen shows, and what to look for, is printed in the terminal.
    Escape quits.
    """,
    add_help=False,
    parents=[rgb_graphics_argparser],
)
parser.add_argument(
    "-l",
    "--lut",
    type=Path,
    default="clut.csv",
    help="path to the CLUT to show, by default 'clut.csv'",
)
parser.add_argument(
    "-Y",
    "--luminance",
    type=float,
    default=None,
    help="luminance of the grey background, by default half of white's",
)


def _enlarge(image, factor):
    """Enlarge an image by repeating each pixel, so no colors are blended."""
    return np.repeat(np.repeat(image, factor, axis=0), factor, axis=1)


def gamut_image(clut, background_rgb, size=160, samples=400):
    """Every chromaticity the display can show, each at its brightest, in CIE 1931 xy.

    The brightest color of a chromaticity has at least one channel at full input. So
    this samples the three faces of the RGB input cube where one channel is at 1,
    works out each sample's color with `RGB_to_XYZ` (per level), and places it by its x, y. Where
    several samples land on one pixel, the brightest is kept.

    Parameters
    ----------
    clut : Array[float]
        the CLUT, shape (L, 13)
    background_rgb : array-like
        input RGB for pixels outside the gamut, shape (3,)
    size : int, optional
        pixels along each side, by default 160
    samples : int, optional
        samples along each edge of each cube face, by default 400

    Returns
    -------
    image : numpy.ndarray
        input RGB, shape (size, size, 3); x increases rightwards, y upwards
    extent : tuple
        ``(x_min, x_max, y_min, y_max)`` the image spans
    white : tuple
        pixel (row, column) of the display's white
    """
    # The three cube faces with one channel at full input
    a, b = np.meshgrid(np.linspace(0, 1, samples), np.linspace(0, 1, samples))
    a, b, one = a.ravel(), b.ravel(), np.ones(a.size)
    rgb = np.vstack(
        [np.column_stack([one, a, b]), np.column_stack([a, one, b]), np.column_stack([a, b, one])]
    )

    # The color of each sample, and its chromaticity
    xyz = hrl.cluts.RGB_to_XYZ(rgb, clut, per_level=True)
    xy = xyz[:, :2] / xyz.sum(axis=1, keepdims=True)

    # A square region around the samples, with a small margin
    low, high = xy.min(axis=0), xy.max(axis=0)
    centre, half = (low + high) / 2, 0.52 * (high - low).max()
    extent = (centre[0] - half, centre[0] + half, centre[1] - half, centre[1] + half)

    def pixel(points):
        """Row and column of each x, y; y increases upwards."""
        column = ((points[:, 0] - extent[0]) / (2 * half) * size).astype(int)
        row = ((extent[3] - points[:, 1]) / (2 * half) * size).astype(int)
        return np.clip(row, 0, size - 1), np.clip(column, 0, size - 1)

    # An image of the background, with each sample drawn at its chromaticity; where
    # several land on one pixel, the brightest, by drawing them from dimmest to brightest
    order = np.argsort(xyz[:, 1])
    rows, columns = pixel(xy[order])
    image = np.tile(np.asarray(background_rgb, dtype=float), (size, size, 1))
    image[rows, columns] = rgb[order]

    # Where the display's white lands
    white_xyz = hrl.cluts.RGB_to_XYZ(np.ones(3), clut, per_level=True)
    white_row, white_column = pixel(white_xyz[None, :2] / white_xyz.sum())

    return image, extent, (int(white_row[0]), int(white_column[0]))


### SCREENS
# Each returns what to draw -- (input RGB image, (x, y) of its top-left corner) -- the
# background to draw it on, and what to print about it. `state` holds the settings,
# such as the luminance.


def _fit(size, width, height, share=0.85):
    """The largest whole-number enlargement of `size` pixels that fits the screen."""
    return max(1, int(share * min(width, height) // size))


def _centred(image, width, height):
    return image, ((width - image.shape[1]) // 2, (height - image.shape[0]) // 2)


def gamut_screen(clut, state, background_rgb, width, height):
    image, extent, (row, column) = gamut_image(clut, background_rgb)

    # Mark white with a dark ring
    rows, columns = np.ogrid[: image.shape[0], : image.shape[1]]
    distance = np.hypot(rows - row, columns - column)
    image[(distance >= 3) & (distance < 4.5)] = 0.0

    image = _enlarge(image, _fit(image.shape[0], width, height))
    text = [
        "Every chromaticity this display can show, each at its brightest,",
        f"placed by CIE 1931 x (rightwards, {extent[0]:.2f} to {extent[1]:.2f}) and "
        f"y (upwards, {extent[2]:.2f} to {extent[3]:.2f}).",
        "The dark ring marks white. Outside the colored region are chromaticities",
        "the display cannot show.",
    ]
    return [_centred(image, width, height)], background_rgb, text


SCREENS = [
    ("gamut", gamut_screen),
]


def command(parsed_args):
    clut = np.genfromtxt(parsed_args.lut, delimiter=",", skip_header=1)
    white_Y = hrl.cluts.RGB_to_XYZ(np.ones(3), clut, per_level=True)[1]
    state = {
        "screen": 0,
        "luminance": parsed_args.luminance or white_Y / 2,
    }

    ihrl = HRL(
        graphics=parsed_args.graphics,
        lut=parsed_args.lut,
        inputs="keyboard",
        photometer=None,
        wdth=parsed_args.width,
        hght=parsed_args.height,
        bg=parsed_args.background,
        fs=True,
        wdth_offset=parsed_args.width_offset,
        db=True,
        scrn=parsed_args.screen,
    )
    width, height = ihrl.graphics.width, ihrl.graphics.height

    # Computed screens, by what they depend on, so going back to one is immediate
    computed = {}

    while True:
        name, screen = SCREENS[state["screen"]]
        print(f"\n[{state['screen'] + 1}/{len(SCREENS)}] {name}")

        setting = (name, state["luminance"])
        if setting not in computed:
            print("computing ...")
            grey = hrl.cluts.achromatic_RGB(clut, state["luminance"], per_level=True)
            computed[setting] = screen(clut, state, grey, width, height)
        items, background_rgb, text = computed[setting]

        ihrl.graphics.changeBackground(background_rgb.reshape(1, 1, 3))
        textures = [ihrl.graphics.newTexture(image) for image, _ in items]
        for texture, (_, position) in zip(textures, items):
            texture.draw(position)
        ihrl.graphics.flip()

        print("\n".join(text))
        print("Left / Right: previous / next screen. Escape: quit.")

        key, _ = ihrl.inputs.readButton(btns=["Left", "Right", "Escape"])
        for texture in textures:
            texture.delete()

        if key == "Escape":
            break
        if key in ("Left", "Right"):
            state["screen"] = (state["screen"] + (1 if key == "Right" else -1)) % len(SCREENS)

    ihrl.close()


if __name__ == "__main__":
    command(parser.parse_args())
