import sys

import numpy as np
from hrl.graphics import graphics
from PIL import Image, ImageDraw, ImageFont

LANG = "en"


def text_to_arr(text, intensity_text=0.0, intensity_background=0.2, fontsize=36):
    """Draw given text into a (numpy) image-array

    Parameters
    ----------
    text : str
        Text to draw
    intensity_text : float, optional
        intensity of the text in range (0.0; 1.0), by default 0.0
    intensity_background : float, optional
        intensity of the background in range (0.0; 1.0), by default 0.2
    fontsize : int, optional
        font size, by default 36

    Returns
    -------
    np.ndarray
        image-array with text drawn into it,
        intensities in range (0.0; 1.0)
    """

    # @author: Torsten Betz; Joris Vincent

    # Try to load the font
    try:
        # Not all machines will have Arial installed...
        font = ImageFont.truetype(
            "arial.ttf",
            fontsize,
            encoding="unic",
        )
    except IOError:
        # On Ubuntu, should have the Ubuntu Mono fonts
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/Ubuntu/UbuntuMono-R.ttf",
            fontsize,
            encoding="unic",
        )

    # Determine dimensions of total text
    # text_width, text_height = font.getsize(text)
    # Determine dimensions of total text
    text_width = int(font.getlength(text))
    left, top, right, bottom = font.getbbox(text)
    text_height = int(top + bottom)

    # Instantiate grayscale image of correct dimensions and background
    img = Image.new("L", (text_width, text_height), int(intensity_background * 255))

    # Draw text into this image
    draw = ImageDraw.Draw(img)
    draw.text((0, 0), text, fill=int(intensity_text * 255), font=font)

    # Downscale image-array to be in range (0.0; 1.0)
    return np.array(img) / 255.0


def display_text(
    ihrl,
    text,
    fontsize=36,
    intensity_text=0.0,
    intensity_background=0.2,
    window_shape=(1024, 768),
):
    """Display a screen with given text, waiting for participant to press button

    Text will be center horizontally.

    Parameters
    ----------
    ihrl : hrl
        HRL-interface object to use for display and input
    text : str, list[str]
        text to display, can be multiple lines
    fontsize : int, optional
        font size, by default 36
    intensity_text : float, optional
        intensity of the text in range (0.0; 1.0), by default 0.0
    intensity_background : float, optional
        intensity of the background in range (0.0; 1.0), by default 0.2
    window_shape : (int, int)
        shape (in pixels) of the HRL window, by default (1024, 768)
    """

    # Clear current screen
    ihrl.graphics.flip(clr=True)

    # Draw each line of text, one at a time
    for line_nr, line in enumerate(text):
        # Generate image-array, OpenGL texture
        if line == "":
            line = " "
        text_arr = text_to_arr(
            text=line,
            intensity_text=intensity_text,
            intensity_background=intensity_background,
            fontsize=fontsize,
        )
        textline = ihrl.graphics.newTexture(text_arr)

        # Determine position
        text_pos = (
            (window_shape[1] - textline.wdth) // 2,
            ((window_shape[0] // 2) - ((len(text) // 2) - line_nr) * (textline.hght + 10)),
        )

        # Draw line
        textline.draw(pos=text_pos)

    # Display
    ihrl.graphics.flip(clr=True)

    # Cleanup: delete texture
    del textline

    return


def block_break(ihrl, trial, total_trials, **kwargs):
    """Display a (mid-block) break message to participant.

    List how many trials out of total (in this block) have been completed.
    Participant needs to press button to continue.

    Parameters
    ----------
    ihrl : hrl
        HRL-interface object to use for display and input
    trial : int
        current trial
    total_trials : int
        total number of trials (in this block)
    """

    # @author: Torsten Betz; Joris Vincent
    if LANG == "de":
        lines = [
            "Du kannst jetzt eine Pause machen.",
            " ",
            f"Du hast {trial} von {total_trials} Durchgängen geschafft.",
            " ",
            "Wenn du bereit bist, drücke die mittlere Taste.",
        ]
    elif LANG == "en":
        lines = [
            "You can take a break now.",
            " ",
            f"You have completed {trial} out of {total_trials} trials.",
            " ",
            "When you are ready, press the middle button.",
        ]
    else:
        raise ("LANG not available")

    display_text(ihrl, text=lines, **kwargs)
    btn, _ = ihrl.inputs.readButton(btns=("Escape", "Space"))

    if btn in ("Escape", "Left"):
        sys.exit("Participant terminated experiment")
    elif btn in ("Space", "Right"):
        return


def block_end(ihrl, block, total_blocks, **kwargs):
    """Display a (mid-session) break message to participant.

    List how many blocks out of total (in this session) have been completed.
    Participant needs to press button to continue.

    Parameters
    ----------
    ihrl : hrl
        HRL-interface object to use for display and input
    block : int
        current block
    total_blocks : int
        total number of blocks (in this session)
    """

    # @author: Torsten Betz; Joris Vincent
    if LANG == "de":
        lines = [
            "Du kannst jetzt eine Pause machen.",
            " ",
            f"Du hast {block} von {total_blocks} blocks geschafft.",
            " ",
            "Zum Weitermachen, druecke die rechte Taste,",
            "zum Beenden druecke die linke/mittlere Taste.",
        ]
    elif LANG == "en":
        lines = [
            "You can take a break now.",
            " ",
            f"You have completed {block} out of {total_blocks} blocks.",
            " ",
            "To continue, press the right button,",
            "to finish, press the left or middle button.",
        ]
    else:
        raise ("LANG not available")

    display_text(ihrl, text=lines, **kwargs)
    btn, _ = ihrl.inputs.readButton(btns=("Escape", "Space", "Left", "Right"))

    if btn in ("Escape", "Left"):
        sys.exit("Participant terminated experiment")
    elif btn in ("Space", "Right"):
        return

    
