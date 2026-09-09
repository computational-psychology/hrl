import sys

import numpy as np
import stimuli
from text_displays import texts

stim_names = stimuli.stims.keys()

rng = np.random.default_rng()


RESPONSE_OPTIONS = [
    "Left target is definitely brighter",
    "Left target is maybe brighter",
    "Targets are equally bright",
    "Right target is maybe brighter",
    "Right target is definitely brighter",
]
FONTSIZE = 25


def display_stim(ihrl, stim, response_selection):
    """Display stimulus with specified target, context intensities

    Parameters
    ----------
    ihrl : hrl-object
        hrl-interface object to use for display
    stim : str
        which stimulus to display, "sbc" or "whites"
    intensity_target : float
        intensity value for the targets
    """
    stimulus = stimuli.stims[stim]

    # Convert the stimulus image(matrix) to an OpenGL texture
    stim_texture = ihrl.graphics.newTexture(stimulus["img"])

    # Determine position: we want the stimulus in the center of the frame
    window_center = (ihrl.height // 2, ihrl.width // 2)  # Center of the drawing window
    pos = (
        window_center[1] - (stim_texture.wdth // 2),
        window_center[0] - (stim_texture.hght // 2),
    )

    # Create a display: draw texture on the frame buffer
    stim_texture.draw(pos=pos, sz=(stim_texture.wdth, stim_texture.hght))

    # Draw Likert-scale options
    draw_options(ihrl, response_selection)

    # Display: flip the frame buffer
    ihrl.graphics.flip(clr=True)  # also `clear` the frame buffer


# %% DRAW LIKERT OPTIONS
def draw_options(ihrl, selection, ppd=stimuli.resolution["ppd"]):
    txt_ints = [0.0] * len(RESPONSE_OPTIONS)
    txt_ints[selection - 1] = 1.0

    # Generate textures
    response_textures = []
    for i, response in enumerate(RESPONSE_OPTIONS):
        response_texture = ihrl.graphics.newTexture(
            texts.text(
                response,
                ppd=ppd,
                intensity_background=ihrl.background,
                intensity_text=txt_ints[i],
                fontsize=FONTSIZE,
            )["img"],
            "square",
        )
        response_textures.append(response_texture)

    # align top of textures, such that tallest texture has 10px bottom clearance
    max_height = 0
    # max_width = 0
    for texture in response_textures:
        if texture.hght > max_height:
            max_height = texture.hght
        # if texture.wdth > max_width:
        #     max_width = texture.wdth
    vertical_position = ihrl.height - max_height - 10
    width = ihrl.width // len(RESPONSE_OPTIONS)

    # Draw
    for i, texture in enumerate(response_textures):
        horizontal_position = width * i + ((width - texture.wdth) // 2)
        texture.draw((horizontal_position, vertical_position))


def select(ihrl, value, range):
    """Allow participant to select a value from a range of options

    Parameters
    ----------
    ihrl : hrl-object
        HRL-interface object to use for display
    value : int
        currently selected option
    range : (int, int)
        min and max values to select. If one value is given, assume min=0

    Returns
    -------
    int
        currently selected option
    bool
        whether this option was confirmed

    Raises
    ------
    SystemExit
        if participant/experimenter terminated by pressing Escape
    """
    try:
        len(range)
    except:
        range = (0, range)

    accept = False

    press, _ = ihrl.inputs.readButton(btns=("Left", "Right", "Escape", "Space"))

    if press == "Escape":
        # Raise SystemExit Exception
        sys.exit("Participant terminated experiment.")
    elif press == "Left":
        value -= 1
        value = max(value, range[0])
    elif press == "Right":
        value += 1
        value = min(value, range[1])
    elif press == "Space":
        accept = True

    return value, accept


def run_trial(ihrl, stim, **kwargs):
    response_position = 3

    # Run adjustment
    accept = False
    while not accept:
        display_stim(
            ihrl,
            stim,
            response_selection=response_position,
        )
        response_position, accept = select(ihrl, value=response_position, range=(1, 5))

    return {"response": response_position}
