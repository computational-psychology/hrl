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
        if self.checkEscape():
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
                (ky1,tm1) = self.readButton(btns,to)
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
