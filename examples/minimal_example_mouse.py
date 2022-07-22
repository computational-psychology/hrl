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
    mp, mbtn, mpos = hrl.inputs.check_mouse_press() # function without wait time by default
    
    # we wait for a keyboard / responsepixx button press for only 10 ms
    # default is indefinite time, so we pass the parameter timeout (to) in seconds.
    btn, t1 = hrl.inputs.readButton(to=0.010) 
    
    # checking if something has been pressed
    # keyboard / responsepixx press
    if btn != None:
        print(btn)
     
    # mouse pressed?
    if mp:
        # if mouse is pressed, we report only if it is a new position
        # so to avoid multiple reports for the same event
        # alteratively one could also filter the events according to time 
        # instead of position (a mininum time has to have passed since last press
        # this option is not implemented here but you could do it with time.time()
        if mpos != last_pos:
            print(mbtn)
            print(mpos)
            last_mbtn = mbtn
            last_pos = mpos

    if btn=='Escape':
        break

    
hrl.close()
