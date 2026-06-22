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
    elif ky == pygame.K_0 or ky == pygame.K_KP0:
        return "0"
    elif ky == pygame.K_1 or ky == pygame.K_KP1:
        return "1"
    elif ky == pygame.K_2 or ky == pygame.K_KP2:
        return "2"
    elif ky == pygame.K_3 or ky == pygame.K_KP3:
        return "3"
    elif ky == pygame.K_4 or ky == pygame.K_KP4:
        return "4"
    elif ky == pygame.K_5 or ky == pygame.K_KP5:
        return "5"
    elif ky == pygame.K_6 or ky == pygame.K_KP6:
        return "6"
    elif ky == pygame.K_7 or ky == pygame.K_KP7:
        return "7"
    elif ky == pygame.K_8 or ky == pygame.K_KP8:
        return "8"
    elif ky == pygame.K_9 or ky == pygame.K_KP9:
        return "9"
    else:
        return None
