import numpy as np
from PIL import Image

PPD = 32


VARIEGATED_ARRAY = np.loadtxt("matchsurround.txt")


def image_to_array(fname, in_format="png"):
    # Function written by Marianne
    """
    Reads the specified image file (default: png), converts it to grayscale
    and into a numpy array

    Input:
    ------
    fname       - name of image file
    in_format   - extension (png default)

    Output:
    -------
    numpy array
    """
    im = Image.open(f"{fname}.{in_format}").convert("L")
    temp_matrix = [im.getpixel((y, x)) for x in range(im.size[1]) for y in range(im.size[0])]
    temp_matrix = np.array(temp_matrix).reshape(im.size[1], im.size[0])
    im_matrix = np.array(temp_matrix.shape, dtype=np.float64)
    im_matrix = temp_matrix / 255.0
    # print im_matrix
    return im_matrix


def show_stimulus(
    ihrl,
    stimulus_texture,
    matching_field_stim,
    match_intensity,
):
    # Draw the stimulus
    stimulus_texture.draw(
        (
            (ihrl.width // 2) - stimulus_texture.wdth / 2,
            (ihrl.height // 2) - stimulus_texture.hght / 2,
        )
    )

    # Update matching field intensity
    matching_field_stim["img"] = np.where(
        matching_field_stim["field_mask"], match_intensity, matching_field_stim["img"]
    )

    # Draw the matching field
    matching_texture = ihrl.graphics.newTexture(matching_field_stim["img"])
    matching_texture.draw(
        ((ihrl.width // 2) - matching_texture.wdth / 2, ((ihrl.height // 2)) / 4 - 50)
    )

    # flip everything
    ihrl.graphics.flip(clr=False)  # clr= True to clear buffer
