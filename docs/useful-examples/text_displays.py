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
        
        # Accumulate
        textures.append(textline)

    # Display
    ihrl.graphics.flip()
        
    # Cleanup: delete texture
    for texture in textures:
        texture.delete()
        

    return
