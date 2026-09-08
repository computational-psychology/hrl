import importlib

__all__ = [
    "new_input",
    "ALIASES",
]

ALIASES = {
    "keyboard": "keyboard.Keyboard",
    "responsepixx": "responsepixx.RESPONSEPixx",
}


def new_input(input_alias, device=None):
    """Factory function to create appropriate Input subclass based on provided alias.

    Parameters
    ----------
    input_alias : str
        alias for the desired input device. Valid options can be found in the
        hrl.inputs.ALIASES.keys().

    Returns
    -------
    Input
        an instance of the Input subclass corresponding to the provided alias

    Raises
    ------
    ValueError
        if the provided input_alias does not match any known input device

    """
    # Lazy import the input class based on alias
    if input_alias in ALIASES:
        module_name, class_name = ALIASES[input_alias].rsplit(".", 1)
        module = importlib.import_module(f".{module_name}", package=__name__)
        input_class = getattr(module, class_name)
    else:
        raise ValueError(
            f"Unknown input device '{input_alias}'. Valid options are: "
            f"{', '.join(list(ALIASES.keys()))}"
        )

    input_device = input_class()
    input_device.device = device
    return input_device
