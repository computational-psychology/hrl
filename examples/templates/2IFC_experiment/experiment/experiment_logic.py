import sys
import time

import numpy as np
import stimuli
import text_displays


def display_fixation_cross(ihrl, intensity=0):
    ihrl.graphics.flip(clr=True)
    fix = ihrl.graphics.newTexture(np.ones((5, 5)) * intensity)
    fix.draw((ihrl.width // 2, ihrl.height // 2))
    ihrl.graphics.flip()
    return


def run_trial(
    ihrl,
    sf,
    orientation,
    phase,
    contrast_interval1,
    contrast_interval2,
    correct,
    feedback,
    **kwargs
):
    """Function that runs sequence of events during one trial"""

    window_center = (ihrl.height // 2, ihrl.width // 2)  # Center of the drawing window

    # Fixation cross
    display_fixation_cross(ihrl)

    # Create textures before showing
    gabor1 = stimuli.gabor(sf,
                           contrast=contrast_interval1,
                           sigma=0.5, 
                           orientation=orientation, # in degrees
                           phase=phase, # in degrees
                           )

    gabor2 = stimuli.gabor(sf,
                           contrast=contrast_interval2,
                           sigma=0.5, 
                           orientation=orientation, 
                           phase=phase,
                           )
                           

    # Convert the stimulus image(matrix) to an OpenGL texture
    gabor1_texture = ihrl.graphics.newTexture(gabor1["img"])
    gabor2_texture = ihrl.graphics.newTexture(gabor2["img"])

    # Determine position: we want the stimulus in the center of the frame
    pos = (window_center[1] - (gabor1_texture.wdth // 2),
           window_center[0] - (gabor1_texture.hght // 2))
    
    time.sleep(0.5)
    
    ### 1st interval
    # draw and flip first interval
    gabor1_texture.draw(pos=pos, sz=(gabor1_texture.wdth, gabor1_texture.hght))
    ihrl.graphics.flip(clr=True)  # flips the frame buffer to show everything
    ihrl.sounds[0].play(loops=0, maxtime=int(0.5*1000)) # stim time in ms
    time.sleep(0.5) 
    
    ### ISI
    display_fixation_cross(ihrl)
    time.sleep(0.25)
    
    ### 2nd interval
    # draw and flip second interval
    gabor2_texture.draw(pos=pos, sz=(gabor1_texture.wdth, gabor1_texture.hght))
    ihrl.graphics.flip(clr=True) # flips the frame buffer to show everything
    ihrl.sounds[1].play(loops=0, maxtime=int(0.5*1000)) # stim time in ms
    time.sleep(0.5)
    
    ### wait for response
    display_fixation_cross(ihrl, intensity=0)
    btn, t1 = ihrl.inputs.readButton(btns=["Left", "Right", "Escape", "Space"])
    
    if (btn=="Left" and correct==1) or (btn=="Right" and correct==2):
        response_correct = 1
        if feedback:
            ihrl.sounds[2].play(loops=0, maxtime=100)  # maxtime in ms
    else:
        response_correct = 0
        if feedback:
            ihrl.sounds[3].play(loops=0, maxtime=100)  # maxtime in ms
    

    # Raise SystemExit Exception
    if (btn == "Escape") or (btn == "Space"):
        sys.exit("Participant terminated experiment.")

    # end trial
    return {"response": btn, "response_correct": response_correct, "resp.time": t1}


def display_instructions(ihrl):
    """Display instructions to the participant

    Parameters
    ----------
    ihrl : hrl-object
        hrl-interface object to use for display
    """
    lines = [
        "Contrast detection task",
        "Please select in which interval you saw the stimulus",
        "Press either:",
        "LEFT or RIGHT",
        "for",
        "FIRST or SECOND INTERVAL, respectively",
        "Press MIDDLE button to start",
    ]

    text_displays.display_text(
        ihrl=ihrl, text=lines, intensity_background=ihrl.graphics.background
    )

    return
