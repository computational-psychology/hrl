def new_photometer(photometer_alias, device="/dev/ttyUSB0", timeout=10):
    """Factory function to create a new photometer instance based on the provided name.

    Parameters
    ----------
    photometer_alias : str
        name of the photometer to create. Valid options: 'optical', 'minolta'.
    device : str, optional
        device path to the photometer, by default "/dev/ttyUSB0".
    timeout : int, optional
        timeout in seconds for communication with the photometer, by default 10.

    Returns
    -------
    Photometer
        instance of the photometer corresponding to the provided alias.

    Raises
    ------
    ValueError
        If the provided photometer_alias does not match any known photometer.

    """
    if photometer_alias == "optical":
        from .optical import OptiCAL as photometer_class
    elif photometer_alias == "minolta":
        from .minolta import Minolta as photometer_class
    else:
        raise ValueError(
            f"Unknown photometer: {photometer_alias}. Valid options are: 'optical', 'minolta'"
        )

    return photometer_class(device, timeout=timeout)
