"""
Minimal example of how to use mouse events in HRL 3.

@author: G. Aguilar, July 2022

"""

from hrl import HRL

# size of Siements monitor
WIDTH = 1024
HEIGHT = 768


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
    mouse=True)


last_pos = (None, None)


while True:
    # we check if a mouse button has been pressed
    mp, mbtn, mpos = hrl.inputs.check_mouse_press(thr=0.2) 
    # thr: 'threshold' in s. Any button press happening in less than thr seconds gets ignored.
    # this is necessary as the function reports many times the same single button press
    
    # we wait for a keyboard / responsepixx button press for only 10 ms
    # default is indefinite time, so we pass the parameter timeout (to) in seconds.
    btn, t1 = hrl.inputs.readButton(to=0.020) 
    
    # checking if something has been pressed
    # keyboard / responsepixx press
    if btn != None:
        print(btn)
     
    # mouse pressed?
    if mp:
        print(mbtn)
        print(mpos)

    if btn=='Escape':
        break

    
hrl.close()
