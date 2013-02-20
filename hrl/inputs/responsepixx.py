from inputs import Input

## Class ##

class RESPONSEPixx(Input):

    def __init__(self,btns,dpx):
        super(RESPONSEPixx,self).__init__(btns)
        self.dpx = dpx

    def readButton(self,timeout=3600,btns=None):
        """
        buttonLoop reads a button off the responsePixx, returning the
        time and the colour pressed. However, if the the pressed button
        is not in the HRL's button list, the button pressed will be
        ignored and the clock will keep ticking.
        """
        if btns == None: btns = self.btns
        rspns = self.dpx.waitButton(timeout)
        if rspns == None:
            return (None, timeout)
        else:
            (clr,tm) = rspns
            clr = buttonName(clr)
            if btns.count(clr) > 0:
                return (clr,tm)
            else:
                timeout -= tm
                (clr1,tm1) = self.readButton(timeout,btns)
                return (clr1,tm1 + tm)

## Additional Functions ##

def buttonName(nm):
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

