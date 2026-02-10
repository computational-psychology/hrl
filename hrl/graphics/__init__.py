"""HRL Graphics module - display device interfaces."""

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

    return graphics_class(
        width=width,
        height=height,
        background=background,
        fullscreen=fullscreen,
        double_buffer=double_buffer,
        lut=lut,
        mouse=mouse,
    )
