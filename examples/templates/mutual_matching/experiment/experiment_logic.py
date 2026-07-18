import numpy as np
import stimuli
from adjustment import adjust

rng = np.random.default_rng()


def display_stim(ihrl, intensity_target, target_side, intensity_match):
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
    stimulus = stimuli.whites(
        intensity_target=intensity_target, target_side=target_side, intensity_match=intensity_match
    )

    # Convert the stimulus image(matrix) to an OpenGL texture
    stim_texture = ihrl.graphics.newTexture(stimulus["img"])

    # Determine position: we want the stimulus in the center of the frame
    center = (ihrl.height // 2, ihrl.width // 2)
    pos = (center[1] - (stim_texture.wdth // 2), center[0] - (stim_texture.hght // 2))

    # Create a display: draw texture on the frame buffer
    stim_texture.draw(pos=pos, sz=(stim_texture.wdth, stim_texture.hght))

    # Display: flip the frame buffer
    ihrl.graphics.flip(clr=True)  # also `clear` the frame buffer

    return


def run_trial(ihrl, intensity_target, target_side, **kwargs):
    # Pick random starting intensity for matching field
    intensity_match = rng.random()

    # Run adjustment
    accept = False
    while not accept:
        display_stim(
            ihrl,
            intensity_target=intensity_target,
            target_side=target_side,
            intensity_match=intensity_match,
        )
        intensity_match, accept = adjust(ihrl, value=intensity_match)

    return {"intensity_match": intensity_match}
