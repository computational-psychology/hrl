from hrl import HRL
import numpy as np

# Define window parameters
SHAPE = (600, 800)  # Desired shape of the drawing window (height, width)
CENTER = (SHAPE[0] // 2, SHAPE[1] // 2)  # Center of the drawing window

def stimuli():
    """ Defines three random textures with low, mid and high contrast"""
    
    high = np.random.uniform(low=0.0, high=1.0, size=(256, 256)) 
    mid = np.random.uniform(low=0.2, high=0.8, size=(256, 256))
    low = np.random.uniform(low=0.35, high=0.65, size=(256, 256))
        
    stims = {'low contrast ': low,
             'mid contrast ': mid,
             'high contrast ': high}
             
    return stims  


def display_stim(ihrl, stim_image):
    """
    In this "experiment", we just display a collection of stimuli, one at a time.
    Here we define a function to display a single stimulus image centrally on the screen.
    """

    # Convert the stimulus image(matrix) to an OpenGL texture
    stim_texture = ihrl.graphics.newTexture(stim_image)

    # Determine position: we want the stimulus in the center of the frame
    pos = (CENTER[1] - (stim_texture.wdth // 2), CENTER[0] - (stim_texture.hght // 2))

    # Create a display: draw texture on the frame buffer
    stim_texture.draw(pos=pos, sz=(stim_texture.wdth, stim_texture.hght))

    # Display: flip the frame buffer
    ihrl.graphics.flip()  # also `clear` the frame buffer

    return

def select(ihrl, value, rng):
    """Allow participant to select a value from a range of options

    Parameters
    ----------
    ihrl : hrl-object
        HRL-interface object to use for display
    value : int
        currently selected option
    rng : (int, int)
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
        len(rng)
    except:
        rng = (0, rng)

    accept = False

    press, _ = ihrl.inputs.readButton(btns=("Left", "Right", "Escape", "Space"))

    if press == "Escape":
        # Raise SystemExit Exception
        sys.exit("Participant terminated experiment.")
    elif press == "Left":
        value -= 1
        value = max(value, rng[0])
    elif press == "Right":
        value += 1
        value = min(value, rng[1])
    elif press == "Space":
        accept = True

    return value, accept
    
 
def experiment_main(ihrl):
    stims = stimuli()
    stim_names = [*stims.keys()]
    print(f"Stimuli available: {stim_names}")

    stim_idx = 0
    while True:
        # Main loop
        try:
            # Display stimulus
            stim_name = stim_names[stim_idx]
            print(f"Showing {stim_name}")
            
            stim_image = stims[stim_name]
            display_stim(ihrl, stim_image)

            # Select next stim
            stim_idx, _ = select(ihrl, value=stim_idx, rng=len(stim_names) - 1)
            
        except SystemExit as e:
            # Cleanup
            print("Exiting...")
            ihrl.close()
            raise e    
    

if __name__ == "__main__":
    # Create HRL interface object
    ihrl = HRL(
        graphics="gpu",  # Use the default GPU as graphics device driver
        # graphics='datapixx',    # In the lab, we use the datapixx device driver
        inputs="keyboard",  # Use the keyboard as input device driver
        # inputs="responsepixx",  # In the lab, we use the responsepixx input device
        hght=SHAPE[0],
        wdth=SHAPE[1],
        scrn=1,  # Which screen (monitor) to use
        fs=False,  # Fullscreen?
        bg=0.5,  # background intensity (black=0.0; white=1.0)
    )
    experiment_main(ihrl)
    ihrl.close()   
    
