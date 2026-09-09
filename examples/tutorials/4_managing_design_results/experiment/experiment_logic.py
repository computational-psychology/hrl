import sys

import stimuli


def display_stim(ihrl, stim, intensity_target, intensity_left, intensity_right):
    """Display stimulus with specified target, context intensities

    Parameters
    ----------
    ihrl : hrl-object
        hrl-interface object to use for display
    stim : str
        which stimulus to display, "sbc" or "whites"
    intensity_target : float
        intensity value for the targets
    intensity_left : float
        intensity value for the left context
    intensity_right : float
        intensity value for the right context
    """
    if stim == "sbc":
        stimulus = stimuli.sbc(intensity_target, intensity_left, intensity_right)
    elif stim == "whites":
        stimulus = stimuli.whites(intensity_target, intensity_left, intensity_right)

    # Convert the stimulus image(matrix) to an OpenGL texture
    stim_texture = ihrl.graphics.newTexture(stimulus["img"])

    # Determine position: we want the stimulus in the center of the frame
    CENTER = (ihrl.height // 2, ihrl.width // 2)  # Center of the drawing window
    pos = (CENTER[1] - (stim_texture.wdth // 2), CENTER[0] - (stim_texture.hght // 2))

    # Create a display: draw texture on the frame buffer
    stim_texture.draw(pos=pos, sz=(stim_texture.wdth, stim_texture.hght))

    # Display: flip the frame buffer
    ihrl.graphics.flip(clr=True)  # also `clear` the frame buffer

    return


def respond(ihrl):
    press, _ = ihrl.inputs.readButton(btns=("Left", "Right", "Escape", "Space"))

    if press in ("Escape", "Space"):
        # Raise SystemExit Exception
        sys.exit("Participant terminated experiment.")
    else:
        return press


def run_trial(ihrl, stim, intensity_target, intensity_left, intensity_right, **kwargs):
    """Run single trial of this experiment

    This function defines the structure and procedure for a single trial in this experiment.

    Parameters
    ----------
    ihrl : hrl-object
        hrl-interface object to use for display
    stim : str
        which stimulus to display, "sbc" or "whites"
    intensity_target : float
        intensity value for the targets
    intensity_left : float
        intensity value for the left context
    intensity_right : float
        intensity value for the right context

    Returns
    -------
    dict(str: Any)
        trail results: raw resonse, and converted/processed result.
        Will be added to the trial dict, before saving.
    """
    display_stim(ihrl, stim, intensity_target, intensity_left, intensity_right)
    response = respond(ihrl)

    if response == "Left":
        result = intensity_left
    elif response == "Right":
        result = intensity_right

    return {"response": response, "result": result}
