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
    isoluminant plane: every color at one luminance, around a grey of that
        luminance (Up and Down change the luminance).
    directions: ramps from the grey along single directions in color space:
        luminance, and colors at the grey's luminance.

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


# How far each color may be from what was asked for and still count as shown
_TOLERANCE = 1e-6


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


def isoluminant_plane_image(clut, luminance, background_rgb, size=161):
    """Every color at one luminance, around a grey of that luminance.

    Keeping luminance (Y) fixed leaves X and Z free: this is the plane they span, with
    the grey at its centre, X increasing rightwards and Z upwards, on the same scale.
    Each pixel's input is solved with `XYZ_to_RGB` (per level); colors the display cannot show at
    this luminance are left as the background.

    Parameters
    ----------
    clut : Array[float]
        the CLUT, shape (L, 13)
    luminance : float
        luminance (Y) of the plane
    background_rgb : array-like
        input RGB for colors out of reach, shape (3,)
    size : int, optional
        pixels along each side, by default 161; an odd number puts the grey on a pixel

    Returns
    -------
    image : numpy.ndarray
        input RGB, shape (size, size, 3)
    reachable : numpy.ndarray
        shape (size, size), whether the display can show each pixel's color
    half_width : float
        how far the plane extends from the grey, in X and in Z
    """
    grey = hrl.cluts.RGB_to_XYZ(
        hrl.cluts.achromatic_RGB(clut, luminance, per_level=True), clut, per_level=True
    )

    # Make the plane just wide enough for the furthest reachable color
    angles = np.linspace(0, 2 * np.pi, 16, endpoint=False)
    half_width = 1.05 * max(
        hrl.cluts.max_excursion(grey, np.array([np.cos(a), 0.0, np.sin(a)]), clut, per_level=True)
        for a in angles
    )

    offsets = np.linspace(-half_width, half_width, size)
    X, Z = np.meshgrid(offsets, offsets[::-1])  # Z increases upwards
    xyz = np.column_stack([grey[0] + X.ravel(), np.full(X.size, grey[1]), grey[2] + Z.ravel()])

    rgb, error = hrl.cluts.XYZ_to_RGB(xyz, clut, per_level=True)
    reachable = error <= _TOLERANCE
    rgb[~reachable] = background_rgb

    return rgb.reshape(size, size, 3), reachable.reshape(size, size), half_width


def directions(clut, luminance):
    """Directions from a grey, as XYZ differences: luminance, and four at the grey's luminance.

    Returns
    -------
    list of (str, numpy.ndarray)
        name, and direction (shape (3,)) as an XYZ difference
    """
    grey = hrl.cluts.RGB_to_XYZ(
        hrl.cluts.achromatic_RGB(clut, luminance, per_level=True), clut, per_level=True
    )
    found = [("luminance (the grey, brighter and darker)", grey / np.linalg.norm(grey))]
    for name, angle in [("+X", 0), ("+X +Z", 45), ("+Z", 90), ("-X +Z", 135)]:
        radians = np.deg2rad(angle)
        found.append(
            (f"{name} at the grey's luminance", np.array([np.cos(radians), 0.0, np.sin(radians)]))
        )
    return found


def direction_ramps(clut, luminance, steps=256):
    """Ramps from a grey along single directions, each as far as the display can go.

    Each ramp runs from the furthest reachable color on one side of the grey, through
    the grey in the middle, to the furthest on the other side; the two sides are not
    the same distance, so the grey is not always at the centre.

    Returns
    -------
    list of (str, numpy.ndarray)
        name of the direction, and the ramp's input RGB, shape (steps, 3)
    """
    grey = hrl.cluts.RGB_to_XYZ(
        hrl.cluts.achromatic_RGB(clut, luminance, per_level=True), clut, per_level=True
    )

    ramps = []
    for name, direction in directions(clut, luminance):
        down = hrl.cluts.max_excursion(grey, -direction, clut, per_level=True)
        up = hrl.cluts.max_excursion(grey, direction, clut, per_level=True)
        scales = np.linspace(-down, up, steps)
        rgb, _ = hrl.cluts.XYZ_to_RGB(grey + scales[:, None] * direction, clut, per_level=True)
        ramps.append((name, rgb))
    return ramps


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


def _tick_step(half_width):
    """A round step -- 1, 2 or 5 times a power of ten -- giving a few ticks either side."""
    rough = half_width / 4
    power = 10 ** np.floor(np.log10(rough))
    return float(min((1, 2, 5, 10), key=lambda m: abs(m * power - rough)) * power)


def _draw_axes(image, size, factor, half_width, step, tick=6):
    """Draw axes through the centre of an enlarged plane image, with ticks every `step`.

    The plane was computed on a `size` by `size` grid spanning `half_width` either side
    of its centre, and enlarged `factor` times; `size` is odd, so the centre is a pixel.
    """
    centre = (size // 2) * factor + factor // 2
    pixels_per_unit = factor * (size - 1) / (2 * half_width)

    image[centre, :] = 0.0
    image[:, centre] = 0.0
    for multiple in range(1, int(half_width // step) + 1):
        for sign in (-1, 1):
            at = int(round(centre + sign * multiple * step * pixels_per_unit))
            image[centre - tick : centre + tick + 1, at] = 0.0  # on the X axis
            image[at, centre - tick : centre + tick + 1] = 0.0  # on the Z axis
    return image


def plane_screen(clut, state, background_rgb, width, height):
    image, reachable, half_width = isoluminant_plane_image(clut, state["luminance"], background_rgb)
    size, factor = image.shape[0], _fit(image.shape[0], width, height)
    step = _tick_step(half_width)
    image = _draw_axes(_enlarge(image, factor), size, factor, half_width, step)
    text = [
        f"Every color the display can show at Y = {state['luminance']:.1f}, around a grey of",
        f"that luminance: X rightwards, Z upwards, each {half_width:.1f} either side of the",
        "grey, which is at the centre and blends into the background.",
        f"The axes cross at the grey; ticks are every {step:g} in X and in Z.",
        "For an observer like the CIE standard observer, nothing here should look",
        "brighter or darker than the background: only hue and saturation change.",
        "A particular viewer can differ; the stripes screen does not depend on that.",
        "Up / Down: luminance up or down by 5% of white's.",
    ]
    return [_centred(image, width, height)], background_rgb, text


def directions_screen(clut, state, background_rgb, width, height):
    ramps = direction_ramps(clut, state["luminance"])
    step = max(1, int(0.85 * width // len(ramps[0][1])))
    thickness = int(0.85 * height // (1.5 * len(ramps)))

    items, text = [], ["Ramps from the grey, as far as the display can go each way, top to bottom:"]
    top = (height - int(thickness * (1.5 * len(ramps) - 0.5))) // 2
    for index, (name, rgb) in enumerate(ramps):
        image = np.repeat(np.repeat(rgb[None], thickness, axis=0), step, axis=1)
        items.append((image, ((width - image.shape[1]) // 2, top + int(1.5 * index * thickness))))
        text.append(f"  {index + 1}. {name}")
    text += [
        "The first changes only luminance, so it should keep one hue throughout. The others",
        "keep the grey's luminance, so they should change only in hue and saturation, with",
        "no brightness step where they pass the grey (for a standard observer).",
    ]
    return items, background_rgb, text


SCREENS = [
    ("gamut", gamut_screen),
    ("isoluminant plane", plane_screen),
    ("directions", directions_screen),
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

        key, _ = ihrl.inputs.readButton(btns=["Left", "Right", "Up", "Down", "Escape"])
        for texture in textures:
            texture.delete()

        if key == "Escape":
            break
        if key in ("Left", "Right"):
            state["screen"] = (state["screen"] + (1 if key == "Right" else -1)) % len(SCREENS)
        elif name == "isoluminant plane":
            change = 0.05 * white_Y * (1 if key == "Up" else -1)
            state["luminance"] = float(
                np.clip(state["luminance"] + change, 0.05 * white_Y, 0.95 * white_Y)
            )

    ihrl.close()


if __name__ == "__main__":
    command(parser.parse_args())
