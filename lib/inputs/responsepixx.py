from inputs import Input

## Class ##

class RESPONSEPixx(Input):
    """
    An implementation of Input for the RESPONSEPixx box. Accepted keys are 'Up',
    'Down', 'Left', 'Right', 'Space', and 'Escape' which correspond to the
    colours of the RESPONSEPixx, or the actual Escape key in the case of
    'Escape'. These names were chosen to be uniform with the Keyboard
    implementation.
    """

    def __init__(self,dpx):
        super(RESPONSEPixx,self).__init__()
        self.dpx = dpx

    def readButton(self,btns=None,to=3600):
        if checkEscape():
            return 'Escape'

        rspns = self.dpx.waitButton(to)
        if rspns == None:
            return (None, to)
        else:
            (ky,tm) = rspns
            ky = keyMap(ky)
            if (btns == None) or (btns.count(ky) > 0):
                return (ky,tm)
            else:
                to -= tm
                (ky1,tm1) = self.readButton(to,btns)
                return (ky1,tm1 + tm)

## Additional Functions ##

def keyMap(nm):
    """
    Translates a number from the responsePixx into a string
    (corresponding to the colour pressed).
    """
    if nm == 0: return 'Nothing'
    elif nm == 1: return 'Right'
    elif nm == 2: return 'Up'
    elif nm == 4: return 'Left'
    elif nm == 8: return 'Down'
    elif nm == 16: return 'Space'

def checkEscape():
    """
    A simple function which queries pygame as to whether the Escape key
    has been pressed since the last call, and returns true if it has. This
    function can be used within the core loop of a program to allow the user
    to trigger an event which quits the loop, e.g:

        if inputs.checkEscape(): break

    Returns
    -------
    A boolean indicating whether escape has been pressed since the last
        call.
    """
    eventlist = pg.event.get()
    for event in eventlist:
        if event.type == pg.QUIT \
           or event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
            return True
        else:
            return False
