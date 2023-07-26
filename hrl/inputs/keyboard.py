import pygame

from .inputs import Input

debug = False


## Class ##
class Keyboard(Input):
    """
    A Input implementation for a standard PC keyboard. Permitted keys are 'Up',
    'Down', 'Left', 'Right', 'Space', and 'Escape'.
    """

    def readButton(self, btns=None, to=0):
        t0 = pygame.time.get_ticks()
        btn = None
        while (to == 0) or (pygame.time.get_ticks() - t0 < to):
            if debug:
                print("waiting for key press")
            event = pygame.event.wait(1)  # waits for only 1 ms
            if event.type == pygame.KEYDOWN:
                if debug:
                    print("key pressed")
                btn = checkKey(event.key, btns)
                if btn != None:
                    break
        t = pygame.time.get_ticks()
        return (btn, (t - t0) / 1000.0)


## Additional Functions ##


def checkKey(ky, btns):
    kynm = keyMap(ky)
    if btns == None or btns.count(kynm) > 0:
        return kynm
    else:
        return None


def keyMap(ky):
    if ky == pygame.K_UP:
        return "Up"
    elif ky == pygame.K_RIGHT:
        return "Right"
    elif ky == pygame.K_DOWN:
        return "Down"
    elif ky == pygame.K_LEFT:
        return "Left"
    elif ky == pygame.K_SPACE:
        return "Space"
    elif ky == pygame.K_ESCAPE:
        return "Escape"
    else:
        return None
