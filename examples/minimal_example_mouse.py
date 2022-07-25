"""
Minimal example of how to use mouse events in HRL 3.

@author: G. Aguilar, July 2022

"""

from hrl import HRL
from socket import gethostname

# size of Siements monitor
WIDTH = 1024
HEIGHT = 768

# Figure out if we're running in the vision lab
inlab = True if "vlab" in gethostname() else False


if inlab:
    hrl = HRL(
        graphics="datapixx",
        inputs="responsepixx",
        photometer=None,
        wdth=WIDTH,
        hght=HEIGHT,
        bg=0.5,
        scrn=1,
        db=True,
        fs=False,
        mouse=True)  # need to be passed as True, so the cursor is visible
        
else:
    hrl = HRL(
        graphics="gpu",
        inputs="keyboard",
        photometer=None,
        wdth=WIDTH,
        hght=HEIGHT,
        bg=0.5,
        scrn=1,
        db=True,
        fs=False,
        mouse=True)  # need to be passed as True, so the cursor is visible
        
           



while True:
    # we need to continously check whether the mouse and
    # keyboard/responsepixx has been active. We need to check both
    # in alternation.
    
    # here we check if a mouse button has been pressed
    # thr: 'threshold' in seconds. Any button press happening in less 
    # than this time is ignored. This is necessary as the function 
    # reports many times the same single button press
    mp, mbtn, mpos = hrl.inputs.check_mouse_press(thr=0.2) 


    # here we check if the keyboard / responsepixx has been pressed.
    # we wait for only 10 ms, so the loop can continue. 
    # Default is indefinite time, so we pass the parameter timeout 
    # (to) in seconds 
    btn, t1 = hrl.inputs.readButton(to=0.010) 
    
    # Note: depending on the rest of your code (stimuli rendering etc),
    # you might have to adjust these 'timing' values manually. You need
    # to check it for your specific case. 
 
    
    # if something has been pressed, we print
    # keyboard / responsepixx pressed?
    if btn != None:
        print(btn)

    if btn=='Escape' or hrl.inputs.checkEscape():
        break

    # mouse pressed?
    if mp:
        print(mbtn)
        print(mpos)

    
hrl.close()


# EOF
