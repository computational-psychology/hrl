#!/usr/bin/env python
"""
Script to display a set of stimuli in the experimental monitor

GA.

"""

from hrl import HRL
import numpy as np
from PIL import Image, ImageFont, ImageDraw
import glob
from socket import gethostname

inlab_siemens = True if "vlab" in gethostname() else False
inlab_viewpixx =  True if "viewpixx" in gethostname() else False

if inlab_siemens:
    # size of Siements monitor
    WIDTH = 1024
    HEIGHT = 768
    bg_blank = 0.1 # corresponding to 50 cd/m2 approx
    
elif inlab_viewpixx:
    # size of VPixx monitor
    WIDTH = 1920
    HEIGHT = 1080
    bg_blank = 0.27 # corresponding to 50 cd/m2 approx
    
else:
    WIDTH = 1024
    HEIGHT = 768
    bg_blank = 0.27

# center of screen
whlf = WIDTH / 2.0
hhlf = HEIGHT / 2.0
weht = WIDTH/8.0
heht = HEIGHT/8.0
    

def draw_text(text, bg=bg_blank, text_color=0, fontsize=48):
    # function from Thorsten
    """ create a numpy array containing the string text as an image. """

    bg *= 255
    text_color *= 255
    font = ImageFont.truetype(
            "/usr/share/fonts/truetype/msttcorefonts/arial.ttf", fontsize,
            encoding='unic')
    text_width, text_height = font.getsize(text)
    im = Image.new('L', (text_width, text_height), bg)
    draw = ImageDraw.Draw(im)
    draw.text((0,0), text, fill=text_color, font=font)
    return np.array(im) / 255.
    
    
def main():

        # We create the HRL object with parameters that depend on the setup we are using    
    if inlab_siemens:
        # create HRL object
        hrl = HRL(
            graphics="datapixx",
            inputs="responsepixx",
            photometer=None,
            wdth=WIDTH,
            hght=HEIGHT,
            bg=bg_blank,
            scrn=1,
            lut='lut.csv',
            db=True,
            fs=True,
        )
    elif inlab_viewpixx:
        
        hrl = HRL(
            graphics="viewpixx",
            inputs="responsepixx",
            photometer=None,
            wdth=WIDTH,
            hght=HEIGHT,
            bg=bg_blank,
            scrn=1,
            lut='lut_viewpixx.csv',
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
            bg=bg_blank,
            scrn=0,
            lut=None,
            db=True,
            fs=False,
        )

        
    # texture creation in buffer, input is numpy array [0-1]
    white = hrl.graphics.newTexture(np.array([[1]]))
    black = hrl.graphics.newTexture(np.array([[0]]))
    
    s = 150
    white.draw((whlf - s, hhlf - s),(s, s))
    black.draw((whlf, hhlf - s),(s, s))
    white.draw((whlf, hhlf),(s, s))
    black.draw((whlf - s, hhlf),(s, s))

    hrl.graphics.flip(clr=False)   
    
    #######################################
    while True:
        #hrl.graphics.flip(clr=True)   # clr= True to clear buffer
        
        (btn,t1) = hrl.inputs.readButton()
        #print btn
        
        if btn == 'Space':
             break
            
    # closing window
    hrl.close()



if __name__ == '__main__':
    
    main()
    
    
# EOF
    
