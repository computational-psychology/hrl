"""HRL Graphics module - display device interfaces."""

from .datapixx import DATAPixx
from .gpu import GPU_RGB, GPU_grey
from .graphics import Graphics, Graphics_grey, Graphics_RGB
from .texture import Texture
from .viewpixx import VIEWPixx_grey, VIEWPixx_RGB

__all__ = [
    "Graphics",
    "Graphics_grey",
    "Graphics_RGB",
    "GPU_grey",
    "GPU_RGB",
    "DATAPixx",
    "VIEWPixx_grey",
    "VIEWPixx_RGB",
    "Texture",
]


ALIAS_MAP = {
    "GPU_grey": ["gpu", "gpu_grey", "grey", "gray", "gray8"],
    "GPU_RGB": ["gpu_RGB", "RGB"],
    "VIEWPixx_grey": ["viewpixx", "viewpixx_grey", "viewpixx_gray", "viewpixx_gray8"],
    "VIEWPixx_RGB": ["viewpixx_RGB", "viewpixx_color", "viewpixx_colour"],
    "DataPixx": ["datapixx", "datapixx_grey", "datapixx_gray", "datapixx_gray8"],
}


def new_graphics(
    graphics_alias,
    width,
    height,
    background=0.5,
    fullscreen=False,
    double_buffer=True,
    lut=None,
    mouse=False,
):
    """Factory function to create appropriate Graphics subclass based on configuration.

    This function can be extended to read from a configuration file or environment
    variables to determine which graphics device to instantiate (e.g., GPU, DataPixx, ViewPixx).

    Parameters
    ----------
    graphics_alias : str
        alias for the desired graphics device. Valid options are defined in ALIAS_MAP.
    width : int
        width of the screen in pixels.
    height : int
        height of the screen in pixels.
    background : float or tuple, optional
        background intensity value (0.0, 1.0), by default 0.5.
        For grayscale devices, this is a gray level;
        for color devices, can specify an RGB triplet.
    fullscreen : bool, optional
        run in Fullscreen, by default False
    double_buffer : bool, optional
        use double buffering, by default True.
    lut : Path or str, optional
        Path to Look-up Table, by default None.
    mouse : bool, optional
        enable mouse cursor, by default False.
    screen : int or str, optional
        which monitor to use, by default None (use the environment).
        Given as an integer (e.g., 0, 1),
        or as a string containing the X11 screen specification string (e.g., ":0.1" or ":1").
    width_offset : int, optional
        horizontal offset of the window, in pixels, by default 0.
        Useful for setups with multiple monitors but a single Xscreen session.

    Returns
    -------
    Graphics
        an instance of a concrete Graphics subclass appropriate for the specified hardware setup

    Raises
    ------
    ValueError
        if the provided graphics_alias does not match any known device aliases
        (see ALIAS_MAP for valid options)
    """
    if graphics_alias in ALIAS_MAP["GPU_grey"]:
        graphics_class = GPU_grey
    elif graphics_alias in ALIAS_MAP["GPU_RGB"]:
        graphics_class = GPU_grey
    elif graphics_alias in ALIAS_MAP["DataPixx"]:
        graphics_class = GPU_grey
    elif graphics_alias in ALIAS_MAP["VIEWPixx_grey"]:
        graphics_class = GPU_grey
    elif graphics_alias in ALIAS_MAP["VIEWPixx_RGB"]:
        graphics_class = GPU_grey
    else:
        raise ValueError(
            f"Unknown graphics device '{graphics_alias}'. Valid options are: {ALIAS_MAP.items()}"
        )

    return graphics_class(
        width=width,
        height=height,
        background=background,
        fullscreen=fullscreen,
        double_buffer=double_buffer,
        lut=lut,
        mouse=mouse,
    )
