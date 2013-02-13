from inputs import Input
import pygame as pg
import time

## Class ##

class Keyboard(Input):

    def readButton(self,timeout=3600,btns=None):
        """
        keyboardLoop reads a button off the keyboard, returning the time and
        the corresponding colour pressed. However, if the pressed button
        is not in the HRL's button list, the button pressed will be ignored
        and the clock will keep ticking.
        """
        t0 = time.clock()
        if btns == None: btns = self.btns
        btn = None
        while time.clock() - t0 < timeout:
            event = pg.event.wait()
            if event.type == KEYDOWN:
                btn = checkKey(event.key,btns)
                if btn != None: break
        t = time.clock()
        return (btn,t-t0)

## Additional Functions ##

    def checkKey(ky,btns):
        """
        Takes a pygame event.key type, a list of button colours (corresponding to the
        ResponsePixx) and returns a button colour, or None a list key wasn't
        pressed.
        """
        up = 'Up'
        right = 'Right'
        down = 'Down'
        left = 'Left'
        space = 'Space'

        if (ky == K_UP) & (btns.count(up) > 0): return up
        if (ky == K_RIGHT) & (btns.count(right) > 0): return right
        if (ky == K_DOWN) & (btns.count(down) > 0): return down
        if (ky == K_LEFT) & (btns.count(left) > 0): return left
        if (ky == K_SPACE) & (btns.count(space) > 0): return space
        return None



