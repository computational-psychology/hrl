from stimupy.components import texts

LANG = "en"


def display_text(
    ihrl,
    text,
    ppd=32,
    fontsize=36,
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

    bg = ihrl.background if intensity_background is None else intensity_background

    # Clear current screen
    ihrl.graphics.flip(clr=True)

    # Draw each line of text, one at a time
    textures = []
    for line_nr, line in enumerate(text):
        # Generate image-array, OpenGL texture
        if line == "":
            line = " "
        text_arr = texts.text(
            text=line,
            ppd=ppd,
            intensity_text=intensity_text,
            intensity_background=bg,
            fontsize=fontsize,
        )["img"]
        textline = ihrl.graphics.newTexture(text_arr)

        # Determine position
        window_shape = (ihrl.height, ihrl.width)
        text_pos = (
            (window_shape[1] - textline.wdth) // 2,
            ((window_shape[0] // 2) - ((len(text) // 2) - line_nr) * (textline.hght + 10)),
        )

        # Draw line
        textline.draw(pos=text_pos)

        # Accumulate
        textures.append(textline)

    # Display
    ihrl.graphics.flip(clr=True)

    # Cleanup: delete texture
    for texture in textures:
        texture.delete()

    return
