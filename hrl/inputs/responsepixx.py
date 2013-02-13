def buttonLoop(dpx,btns,timeout):
    """
    buttonLoop reads a button off the responsePixx, returning the
    time and the colour pressed. However, if the the pressed button
    is not in the HRL's button list, the button pressed will be
    ignored and the clock will keep ticking.
    """
    rspns = dpx.waitButton(timeout)
    if rspns == None:
        return (None, timeout)
    else:
        (clr,tm) = rspns
        clr = buttonName(clr)
        if btns.count(clr) > 0:
            return (clr,tm)
        else:
            timeout -= tm
            (clr1,tm1) = buttonLoop(dpx,btns,timeout)
            return (clr1,tm1 + tm)

def buttonName(nm):
    """
    Translates a number from the responsePixx into a string
    (corresponding to the colour pressed).
    """
    if nm == 0: return 'Nothing'
    elif nm == 1: return 'Red'
    elif nm == 2: return 'Yellow'
    elif nm == 4: return 'Green'
    elif nm == 8: return 'Blue'
    elif nm == 16: return 'White'


