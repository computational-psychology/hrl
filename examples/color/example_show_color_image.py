from hrl import HRL
from hrl.graphics import graphics
from socket import gethostname
import os
import sys
import numpy as np
from PIL import Image

inlab_viewpixx = True if "viewpixx" in gethostname() else False

if inlab_viewpixx:
    # size of Siements monitor
    WIDTH = 1920
    HEIGHT = 1080
else:
    WIDTH = 1024
    HEIGHT = 768

# center of screen
whlf = WIDTH / 2.0
hhlf = HEIGHT / 2.0


def show_stim(hrl):
    
    
    fname = 'huilohuilo.png'
    
    im = np.array(Image.open(fname)) # RGB image as uint8
    
    im = im/255 # normalized between 0 -1
    
    # texture creation in buffer : stimulus
    stimulus = hrl.graphics.newTexture(im)
    
    # Show stimlus
    stimulus.draw((whlf - stimulus.wdth / 2, hhlf - stimulus.hght / 2))

    # flip everything
    hrl.graphics.flip(clr=True)  # clr= True to clear buffer

    # delete texture from buffer
    del stimulus



def run_experiment():
    #lut = os.path.dirname(os.path.abspath(__file__)) + "/lut.csv"

    if inlab_viewpixx:
        hrl = HRL(
            graphics="viewpixx",
            inputs="responsepixx",
            photometer=None,
            wdth=WIDTH,
            hght=HEIGHT,
            bg=0.2,
            scrn=1,
            lut=lut,
            db=True,
            fs=True,
        )

    else:
        hrl = HRL(
            graphics="gpu",
            inputs="keyboard",
            photometer=None,
            wdth=WIDTH,
            hght=HEIGHT,
            bg=0.5,
            scrn=1,
            lut=None,
            db=True,
            fs=False,
            mode='color24',
        )

    show_stim(hrl)

    btn, t1 = hrl.inputs.readButton()
            

if __name__ == "__main__":
    run_experiment()
