from inputs import Input
import pygame as pg

## Class ##

class Keyboard(Input):
    """
    A Input implementation for a standard PC keyboard. Permitted keys are 'Up',
    'Down', 'Left', 'Right', and 'Space'.
    """
    def readButton(self,btns=None,to=0):
        t0 = pg.time.get_ticks()
        btn = None
        while (to == 0) or (pg.time.get_ticks() - t0 < to):
            event = pg.event.wait()
            if event.type == pg.KEYDOWN:
                btn = checkKey(event.key,btns)
                if btn != None: break
        t = pg.time.get_ticks()
        return (btn,(t-t0)/1000.0)

## Additional Functions ##

def checkKey(ky,btns):
    kynm = keyMap(ky)
    if (btns.count(kynm) > 0):
        return kynm
    else:
        return None

def keyMap(ky):
    if (ky == pg.K_UP):
        return 'Up'
    elif (ky == pg.K_RIGHT):
        return 'Right'
    elif (ky == pg.K_DOWN):
        return 'Down'
    elif (ky == pg.K_LEFT):
        return 'Left'
    elif (ky == pg.K_SPACE):
        return 'Space'
    else:
        return None
