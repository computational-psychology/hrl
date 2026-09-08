import importlib

__all__ = [
    "new_photometer",
    "ALIASES",
]

ALIASES = {
    "optical": "optical.OptiCAL",
    "minolta": "minolta.Minolta",
}


def new_photometer(photometer_alias, device="/dev/ttyUSB0", timeout=10):
    """Factory function to create a new photometer instance based on the provided name.

    Parameters
    ----------
    photometer_alias : str
        alias for the desired photometer. Valid options can be found in the
        hrl.photometer.ALIASES.keys().
    device : str, optional
        device path to the photometer, by default "/dev/ttyUSB0".
    timeout : int, optional
        timeout in seconds for communication with the photometer, by default 10.

    Returns
    -------
    Photometer
        instance of the photometer subclass corresponding to the provided alias

    Raises
    ------
    ValueError
        if the provided photometer_alias does not match any known photometer device

    """
    # Lazy import the photometer class based on alias
    if photometer_alias in ALIASES:
        module_name, class_name = ALIASES[photometer_alias].rsplit(".", 1)
        module = importlib.import_module(f".{module_name}", package=__name__)
        photometer_class = getattr(module, class_name)
    else:
        raise ValueError(
            f"Unknown photometer device '{photometer_alias}'. Valid options are: "
            f"{', '.join(list(ALIASES.keys()))}"
        )

    return photometer_class(device, timeout=timeout)
