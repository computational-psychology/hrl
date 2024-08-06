import sys
import numpy as np
from hrl import HRL
from text_displays import display_text

# Define window parameters
SHAPE = (600, 800)  # Desired shape of the drawing window (height, width)
CENTER = (SHAPE[0] // 2, SHAPE[1] // 2)  # Center of the drawing window
BACKGROUND = 0.5

DIRECTIONS = ["Left", "Right", "Up", "Down"]

# random generator
rng = np.random.default_rng()

def show_instructions(ihrl, direction):
    """Display instructions to the participant

    Parameters
    ----------
    ihrl : hrl-object
        hrl-interface object to use for display
    direction : str
        which key the participant should press
    """
    lines = [
        "Here's what you need to do.",
        "It's very simple.",
        "",
        f"Press {direction}.",
        "",
        "Do it now.",
    ]

    display_text(ihrl=ihrl, text=lines)

    return


def show_correct(ihrl):
    """Display message that participant pressed the correct button

    Parameters
    ----------
    ihrl : hrl-object
        hrl-interface object to use for display
    """
    lines = [
        "Yes, that was correct!",
        "",
        "Press SPACE to continue.",
    ]
    display_text(ihrl=ihrl, text=lines)


def process_response(ihrl, direction):
    """Process participant's keypress

    Parameters
    ----------
    ihrl : hrl-object
        hrl-interface object to use for display
    direction : str
        which key the participant should press

    Returns
    -------
    bool
       whether keypress was correct

    Raises
    ------
    SystemExit
        if participant/experimenter terminates experiment by pressing "Escape"
    """
    press, _ = ihrl.inputs.readButton()

    if press in ("Escape"):
        # Raise SystemExit Exception
        sys.exit("Participant terminated experiment.")
    elif press == direction:
        return True
    else:
        return False


def experiment_main(ihrl):
    """Run adjustment experiment on specified display

    Parameters
    ----------
    ihrl : hrl-object
        hrl-interface object to use for display

    Raises
    ------
    SystemExit
        if participant/experimenter terminates experiment
    """
    while True:
        # Main loop
        try:
            # Pick a direction, randomly
            idx = rng.integers(low=len(DIRECTIONS))
            direction = DIRECTIONS[idx]

            # Display text
            show_instructions(ihrl, direction)

            # Wait for key
            response_correct = False
            while not response_correct:
                response_correct = process_response(ihrl, direction)

            # Show correct response screen
            show_correct(ihrl)
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
