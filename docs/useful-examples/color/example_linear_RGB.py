from pathlib import Path
from socket import gethostname

import numpy as np

from hrl import HRL


def show_stim(igraphics):
    # Create stimulus texture in buffer
    stimulus = igraphics.newTexture(im)

    # Center texture on screen
    stimulus.draw(
        (
            igraphics.width / 2 - stimulus.wdth / 2,
            igraphics.height / 2 - stimulus.hght / 2,
        )
    )

    # Display: flip buffer to screen
    igraphics.flip(clr=True)  # clr= True to clear buffer

    # Delete texture from buffer
    stimulus.delete()
    del stimulus


def instantiate_hrl():
    lut = Path(__file__).parent / "example_clut.csv"

    if "viewpixx" in gethostname():
        ihrl = HRL(
            graphics="viewpixx_RGB",
            inputs="responsepixx",
            wdth=1920,
            hght=1080,
            bg=0.2,
            scrn=1,
            lut=lut,  # Use example CLUT for gamma correction
            db=True,
            fs=True,
        )
    elif "vlab" in gethostname():
        raise RuntimeError("Cannot run RGB on Datapixx setup")

    else:
        ihrl = HRL(
            graphics="gpu_RGB",
            inputs="keyboard",
            wdth=1024,
            hght=768,
            bg=0.5,
            scrn=1,
            lut=lut,  # Use example CLUT for gamma correction
            db=True,
            fs=False,
        )

    return ihrl


if __name__ == "__main__":
    from PIL import Image

    # Load image from file
    fname = Path(__file__).parent / "huilohuilo.png"
    im = np.array(Image.open(fname))  # RGB image as uint8
    im = im / 255  # normalized between 0 -1

    # Startup HRL
    ihrl = instantiate_hrl()

    # Show stimulus
    show_stim(ihrl.graphics)

    # Wait for button press
    _ = ihrl.inputs.readButton()

    # Close HRL
    ihrl.close()
