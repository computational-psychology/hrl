def new_input(input_alias, device=None):
    """Factory function to create appropriate Input subclass based on configuration.

    This function can be extended to read from a configuration file or environment
    variables to determine which input device to instantiate (e.g., Keyboard, RESPONSEPixx).

    Parameters
    ----------
    input_alias : str
        alias for the desired input device. Valid options: 'keyboard', 'responsepixx'.

    Returns
    -------
    Input
        an instance of the appropriate Input subclass.
    """
    if input_alias == "keyboard":
        from .keyboard import Keyboard as input_class
    elif input_alias == "responsepixx":
        from .responsepixx import RESPONSEPixx as input_class
    else:
        raise ValueError(
            f"Unknown input device '{input_alias}'. Valid options are: 'keyboard', 'responsepixx'"
        )

    input_device = input_class()
    input_device.device = device
    return input_device
