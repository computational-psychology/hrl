import sys

from text_displays import display_text


def adjust(ihrl, value, step_size=(0.05, 0.01)):
    """Allow participant to adjust (stimulus)value

    Parameters
    ----------
    ihrl : hrl-object
        hrl-interface object to use for display
    value : float
        value to adjust, e.g., target intensity
    step_size : tuple, optional
        step sizes of adjustment, big (Up/Down) and small (Left/Right),
        by default (0.05, 0.01)

    Returns
    -------
    float
        value after adjustment
    bool
        flag for whether value has been accepted
    """

    # Wait for key
    key, _ = ihrl.inputs.readButton(btns=("Escape", "Up", "Down", "Left", "RightSpace"))

    # Process
    accept = False
    if key == "Escape":
        sys.exit("Participant terminated experiment")
    elif key == "Space":
        accept = True
    elif key == "Up":
        value += step_size[0]
    elif key == "Right":
        value += step_size[1]
    elif key == "Down":
        value -= step_size[0]
    elif key == "Left":
        value -= step_size[1]

    # Stay in gamut
    if value > 1:
        value = min(1, value)
        warning_max(ihrl)
    if value < 0:
        value = max(0, value)
        warning_min(ihrl)

    return value, accept


def warning_min(ihrl, lang="en"):
    """Indicate that adjustment has reached the minimum value

    Parameters
    ----------
    ihrl : hrl-object
        hrl-interface object to use for display
    lang : str
        language-id to display message in

    Raises
    ------
    NotImplementedError
        if lang is not available
    """

    ihrl.graphics.flip(clr=True)
    if lang == "de":
        lines = [
            "Minimum erreicht!",
            " ",
            "Zum Weitermachen, drücke die mittlere Taste.",
        ]

    elif lang == "en":
        lines = [
            "Reached minimum!",
            " ",
            "To continue, increase, or press the middle button.",
        ]
    else:
        raise NotImplementedError(f'Language "{lang}" not available')

    display_text(ihrl, lines)
    ihrl.inputs.readButton(btns=("Down", "Left", "Space"))


def warning_max(ihrl, lang="en"):
    """Indicate that adjustment has reached the maximum value

    Parameters
    ----------
    ihrl : hrl-object
        hrl-interface object to use for display
    lang : str
        language-id to display message in

    Raises
    ------
    NotImplementedError
        if lang is not available
    """
    ihrl.graphics.flip(clr=True)

    if lang == "de":
        lines = [
            "Maximum erreicht!",
            " ",
            "Zum Weitermachen, drücke die mittlere Taste.",
        ]

    elif lang == "en":
        lines = [
            "Reached maximum!",
            " ",
            "To continue, decrease, or press the middle button.",
        ]
    else:
        raise NotImplementedError(f'Language "{lang}" not available')

    display_text(ihrl, lines)
    ihrl.inputs.readButton(btns=("Down", "Left", "Space"))
