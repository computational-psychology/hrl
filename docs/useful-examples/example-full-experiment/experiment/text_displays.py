import numpy as np
from PIL import Image, ImageDraw, ImageFont

def create_text_texture(text, 
                        intensity_text=0.0,
                        intensity_background=0.5,
                        fontsize=28,
                        align="center",
                        ):
    """ Draw given text into a (numpy) image-array 
    
    It uses Pillow in mode "F", that is, a mode using floating point
    values and only one channel (grayscale).
    

    Parameters
    ----------
    text : str
        Text to draw
    intensity_text : float, optional
        intensity of text in range (0.0; 1.0), by default 0.0
    intensity_background : float, optional
        intensity value of background in range (0.0; 1.0), by default 0.5
    fontsize : int, optional
        font size, by default 36
    align : "left", "center" (default), "right"
        alignment of text, by default "center"

    Returns
    -------
    numpy array 
       containing the text as an image
        
    """
    # Get font
    font = ImageDraw.ImageDraw.font
    if not font:
        try:
            # Not all machines will have Arial installed...
            font = ImageFont.truetype(
                "arial.ttf",
                fontsize,
                encoding="unic",
            )
        except OSError:
            font = ImageFont.load_default()
    
    # Determine dimensions of total text
    n_lines = len(text.split("\n"))
    max_length = 0
    for line in text.split("\n"):
        max_length = max(int(font.getlength(line)), max_length)
    _, top, _, bottom = font.getbbox(text)
    text_width = max_length
    text_height = int(top + bottom) * n_lines
    text_shape = (text_height, text_width)

    # Instantiate grayscale image of correct shape (in pixels)
    img = Image.new("F", (text_width, text_height), intensity_background)
    draw = ImageDraw.Draw(img)

    # Draw text into this image
    draw.text(
        (0, 0),
        text,
        fill=intensity_text,
        font=font,
        align=align,
    )
    
    return img
    
    
def display_text(
    ihrl,
    text,
    fontsize=28,
    intensity_text=0.0,
    intensity_background=None,
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
        intensity of the background in range (0.0; 1.0), if None (default): ihrl.background
    """

    bg = ihrl.background if (intensity_background is None) else intensity_background

    # Clear current screen
    ihrl.graphics.flip()

    # Draw each line of text, one at a time
    textures = []
    for line_nr, line in enumerate(text):
        # Generate image-array, OpenGL texture
        if line == "":
            line = " "

        text_arr = create_text_texture(
            text=line,
            intensity_text=intensity_text,
            intensity_background=bg,
            fontsize=fontsize,
        )
        
        textline = ihrl.graphics.newTexture(text_arr)

        # Determine position where to draw
        window_shape = (ihrl.height, ihrl.width)
        text_pos = (
            (window_shape[1] - textline.wdth) // 2,
            ((window_shape[0] // 2) - ((len(text) // 2) - line_nr) * (textline.hght + 10)),
        )

        # Draw the line
        textline.draw(pos=text_pos)

    # Display
    ihrl.graphics.flip()

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
    
    lines = ["You can take a break now.",
            " ",
            f"You have completed {trial} out of {total_trials} trials.",
            " ",
            "When you are ready, press the middle button."]

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

    lines = ["You can take a break now.",
            " ",
            f"You have completed {block} out of {total_blocks} blocks.",
            " ",
            "To continue, press the right or middle button,",
            "to finish, press the left button."]

    display_text(ihrl, text=lines, **kwargs)
    btn, _ = ihrl.inputs.readButton(btns=("Escape", "Space", "Left", "Right"))

    if btn in ("Escape", "Left"):
        sys.exit("Participant terminated experiment")
    elif btn in ("Space", "Right"):
        return
