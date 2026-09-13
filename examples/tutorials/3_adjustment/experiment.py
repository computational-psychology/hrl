import numpy as np
from hrl import HRL

from adjustment import adjust
from stimuli import whites
from text_displays import display_text

# Define window parameters
SHAPE = (1024, 1024)  # Desired shape of the drawing window
CENTER = (SHAPE[0] // 2, SHAPE[1] // 2)  # Center of the drawing window
BACKGROUND = 0.2

rng = np.random.default_rng()


def display_instructions(ihrl):
    """Display instructions to the participant

    Parameters
    ----------
    ihrl : hrl-object
        hrl-interface object to use for display
    """
    instructions = [
        "In this experiment, you will see a stimulus",
        "consisting of a black and white grating.",
        "",
        "On one side, there is a gray target patch.",
        "",
        "Your task is to adjust the gray patch",
        "until its brightness is midway",
        "between the black and white.",
    ]
    display_text(ihrl=ihrl, text=instructions)


def display_stim(ihrl, intensity_target=0.5):
    """Display stimulus with specified target intensitiy

    Parameters
    ----------
    ihrl : hrl-object
        hrl-interface object to use for display
    intensity_target : float, optional
        intensity value for the adjustable target, by default 0.5
    """
    stim = whites(intensity_target=intensity_target)

    # Convert the stimulus image(matrix) to an OpenGL texture
    stim_texture = ihrl.graphics.newTexture(stim["img"])

    # Determine position: we want the stimulus in the center of the frame
    pos = (CENTER[1] - (stim_texture.wdth // 2), CENTER[0] - (stim_texture.hght // 2))

    # Create a display: draw texture on the frame buffer
    stim_texture.draw(pos=pos, sz=(stim_texture.wdth, stim_texture.hght))

    # Display: flip the frame buffer
    ihrl.graphics.flip(clr=True)  # also `clear` the frame buffer


def display_accept(ihrl, intensity_target):
    """Display message that participant accepted a value

    Parameters
    ----------
    ihrl : hrl-object
        hrl-interface object to use for display
    intensity_target : float
        intensity value of the target that participant accepted
    """
    message = ["You accepted a value!", "", f"You picked {intensity_target}"]
    display_text(ihrl=ihrl, text=message)


def experiment_main(ihrl):
    """Run adjustment experiment on specified display

    Parameters
    ----------
    ihrl : hrl-object
        hrl-interface object to use for display

    Raises
    ------
    SystemExit
        if participant terminates experiment
    """

    # Display instructions
    display_instructions(ihrl)
    ihrl.inputs.readButton(btns="Space")

    while True:
        # Main loop
        try:
            # Random starting value
            intensity_target = rng.random()

            # Run adjustment
            accept = False
            while not accept:
                display_stim(ihrl, intensity_target=intensity_target)
                intensity_target, accept = adjust(ihrl, value=intensity_target)

            # Show accept response screen
            display_accept(ihrl, intensity_target=intensity_target)
            ihrl.inputs.readButton(btns="Space")

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
        bg=BACKGROUND,  # background intensity (black=0.0; white=1.0)
    )
    experiment_main(ihrl)
    ihrl.close()
