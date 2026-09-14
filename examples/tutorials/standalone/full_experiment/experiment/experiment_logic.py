import sys
from stimuli import sbc


def display_stim(ihrl, intensity_target_left, intensity_target_right,
                 intensity_bg_left, intensity_bg_right):
    """Display stimulus with specified target, context intensities

    Parameters
    ----------
    ihrl : hrl-object
        hrl-interface object to use for display
    intensity_target_left : float
        intensity value for the left target
    intensity_target_right : float
        intensity value for the right target
    intensity_bg_left : float
        intensity value for the left context
    intensity_bg_right : float
        intensity value for the right context
    """
    stimulus = sbc(intensity_target_left, 
                   intensity_target_right, 
                   intensity_bg_left, 
                   intensity_bg_right)

    # Convert the stimulus image(matrix) to an OpenGL texture
    stim_texture = ihrl.graphics.newTexture(stimulus)

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


def run_trial(ihrl, intensity_target_left, intensity_target_right, 
              intensity_bg_left, intensity_bg_right, **kwargs):
    """Run single trial of this experiment

    This function defines the structure and procedure for a single trial in this experiment.

    Parameters
    ----------
    ihrl : hrl-object
        hrl-interface object to use for display
    intensity_target_left : float
        intensity value for the left target
    intensity_target_right : float
        intensity value for the right target
    intensity_bg_left : float
        intensity value for the left context
    intensity_bg_right : float
        intensity value for the right context

    Returns
    -------
    dict(str: Any)
        trail results: raw resonse, and converted/processed result.
        Will be added to the trial dict, before saving.
    """
    display_stim(ihrl, intensity_target_left, intensity_target_right, intensity_bg_left, intensity_bg_right)
    response = respond(ihrl)

    if response == "Left":
        result = 'left' # or a number, for example 0
    elif response == "Right":
        result = 'right' # or a number, for example 1

    return {"response": response, "result": result}
