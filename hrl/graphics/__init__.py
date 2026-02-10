"""HRL Graphics module - display device interfaces."""

import os
import platform

__all__ = [
    "new_graphics",
    "Texture",
]


def new_graphics(
    graphics_alias,
    width,
    height,
    background=0.5,
    fullscreen=False,
    double_buffer=True,
    lut=None,
    mouse=False,
    screen=None,
    width_offset=0,
):
    """Factory function to create appropriate Graphics subclass based on configuration.

    This function can be extended to read from a configuration file or environment
    variables to determine which graphics device to instantiate (e.g., GPU, DataPixx, ViewPixx).

    Parameters
    ----------
    graphics_alias : str
        alias for the desired graphics device. Valid options include:
        'gpu', 'gpu_grey', 'grey', 'gray', 'gray8', 'gpu_RGB', 'RGB',
        'viewpixx', 'viewpixx_grey', 'viewpixx_gray', 'viewpixx_gray8',
        'viewpixx_RGB', 'viewpixx_color', 'viewpixx_colour',
        'datapixx', 'datapixx_grey', 'datapixx_gray', 'datapixx_gray8'.
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
    """
    # Lazy import the graphics class based on alias
    if graphics_alias in ["gpu", "gpu_grey", "grey", "gray", "gray8"]:
        from .gpu import GPU_grey as graphics_class
    elif graphics_alias in ["gpu_RGB", "RGB"]:
        from .gpu import GPU_RGB as graphics_class
    elif graphics_alias in ["viewpixx", "viewpixx_grey", "viewpixx_gray", "viewpixx_gray8"]:
        from .viewpixx import VIEWPixx_grey as graphics_class
    elif graphics_alias in ["viewpixx_RGB", "viewpixx_color", "viewpixx_colour"]:
        from .viewpixx import VIEWPixx_RGB as graphics_class
    elif graphics_alias in ["datapixx", "datapixx_grey", "datapixx_gray", "datapixx_gray8"]:
        from .datapixx import DATAPixx as graphics_class
    else:
        raise ValueError(
            f"Unknown graphics device '{graphics_alias}'. Valid options are: "
            f"'gpu', 'gpu_grey', 'grey', 'gray', 'gray8', 'gpu_RGB', 'RGB', "
            f"'viewpixx', 'viewpixx_grey', 'viewpixx_gray', 'viewpixx_gray8', "
            f"'viewpixx_RGB', 'viewpixx_color', 'viewpixx_colour', "
            f"'datapixx', 'datapixx_grey', 'datapixx_gray', 'datapixx_gray8'"
        )

    # Run screen setup for multiple monitor support
    screen_setup(screen=screen, window_width_offset=width_offset)

    return graphics_class(
        width=width,
        height=height,
        background=background,
        fullscreen=False,
        double_buffer=double_buffer,
        lut=lut,
        mouse=mouse,
    )


def screen_setup(screen, window_width_offset):
    ####### Setting up on which monitor to use
    # In older systems or systems with separate Xscreens, the naming is still :0.0 or :0.1.
    # For systems with only one screen, it is :1.
    if platform.system() == "Linux":
        print(f"Default screen number used by the OS: {os.environ['DISPLAY']}")

        if screen is not None:
            # legacy option for older configs or separate Xscreens
            if os.environ["DISPLAY"] == ":0":
                os.environ["DISPLAY"] = ":0." + str(screen)
            else:
                if isinstance(screen, str):
                    os.environ["DISPLAY"] = screen
                elif isinstance(screen, int):
                    os.environ["DISPLAY"] = ":" + str(screen)

            print(f"Display number changed to: {os.environ['DISPLAY']}")

        ## 11. Aug 2021
        # we add a wdth_offset to be able to run HRL in setups with a
        # single Xscreen but multiple monitors (a config with Xinerama enabled)
        os.environ["SDL_VIDEO_WINDOW_POS"] = f"{window_width_offset},0"
