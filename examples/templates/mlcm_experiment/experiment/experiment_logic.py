import sys
import time

import numpy as np
import stimuli
import text_displays


def display_stim(
    ihrl,
    target_intensity_left,
    surround_intensity_left,
    target_intensity_right,
    surround_intensity_right,
):
    """Display stimulus for current trial"""

    stimulus = stimuli.sbc(
        intensity_targets=(target_intensity_left, target_intensity_right),
        intensity_contexts=(surround_intensity_left, surround_intensity_right),
    )

    # Convert the stimulus image(matrix) to an OpenGL texture
    stim_texture = ihrl.graphics.newTexture(stimulus["img"])

    # Determine position: we want the stimulus in the center of the frame
    window_center = (ihrl.height // 2, ihrl.width // 2)  # Center of the drawing window
    pos = (
        window_center[1] - (stim_texture.wdth // 2),
        window_center[0] - (stim_texture.hght // 2),
    )

    # Draw textures on the frame buffer
    draw_fixation_cross(ihrl)

    # Create a display: draw texture on the frame buffer
    stim_texture.draw(pos=pos, sz=(stim_texture.wdth, stim_texture.hght))

    # Display: flip the frame buffer
    ihrl.graphics.flip()  # flips the frame buffer to show everything

    return


def draw_fixation_cross(ihrl):
    # draws fixation dot in the middle
    # TODO: use stimupy to actually draw a cross and not a square.
    fix = ihrl.graphics.newTexture(np.ones((5, 5)) * 0.0)
    fix.draw((ihrl.width // 2, ihrl.height // 2))


def display_fixation_cross(ihrl):
    ihrl.graphics.flip(clr=True)
    draw_fixation_cross(ihrl)
    ihrl.graphics.flip()

    return


def run_trial(
    ihrl,
    target_intensity_left,
    surround_intensity_left,
    target_intensity_right,
    surround_intensity_right,
    **kwargs
):
    """Function that runs sequence of events during one trial"""

    # Fixation cross
    display_fixation_cross(ihrl)

    # sleeps for 250 ms # using system time (inaccurate)
    time.sleep(0.25)

    # Display stimuli
    display_stim(
        ihrl,
        target_intensity_left=target_intensity_left,
        surround_intensity_left=surround_intensity_left,
        target_intensity_right=target_intensity_right,
        surround_intensity_right=surround_intensity_right,
    )

    # Wait for answer
    btn, t1 = ihrl.inputs.readButton(btns=["Left", "Right", "Escape", "Space"])

    # Raise SystemExit Exception
    if (btn == "Escape") or (btn == "Space"):
        sys.exit("Participant terminated experiment.")

    # end trial
    return {"response": btn, "resp.time": t1}


def display_instructions(ihrl):
    """Display instructions to the participant

    Parameters
    ----------
    ihrl : hrl-object
        hrl-interface object to use for display
    """
    lines = [
        "Paired comparisons task",
        "Please select the stimulus that is",
        "BRIGHTER",
        "Press either:",
        "LEFT or RIGHT",
        "",
        "Press MIDDLE button to start",
    ]

    text_displays.display_text(
        ihrl=ihrl, text=lines, intensity_background=ihrl.graphics.background
    )

    return
