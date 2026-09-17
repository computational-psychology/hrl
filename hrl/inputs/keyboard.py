import pygame

from .inputs import Input

debug = False


## Class ##
class Keyboard(Input):
    """
    A Input implementation for a standard PC keyboard. Permitted keys are 'Up',
    'Down', 'Left', 'Right', 'Space', 'Escape', 'Enter', 'Backspace', the digits
    '0' to '9', and the symbols '+', '-', '*', '/', '.' and '='. Digits, symbols
    and 'Enter' are recognized both on the main keyboard and on the numeric
    keypad. All keys are returned as strings.
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


# Keys that produce the same symbol on the main keyboard and on the numeric
# keypad are mapped to the same name, so experiments do not need to care which
# part of the keyboard the participant used.
KEY_NAMES = {
    pygame.K_UP: "Up",
    pygame.K_RIGHT: "Right",
    pygame.K_DOWN: "Down",
    pygame.K_LEFT: "Left",
    pygame.K_SPACE: "Space",
    pygame.K_ESCAPE: "Escape",
    pygame.K_BACKSPACE: "Backspace",
    pygame.K_0: "0",
    pygame.K_KP0: "0",
    pygame.K_1: "1",
    pygame.K_KP1: "1",
    pygame.K_2: "2",
    pygame.K_KP2: "2",
    pygame.K_3: "3",
    pygame.K_KP3: "3",
    pygame.K_4: "4",
    pygame.K_KP4: "4",
    pygame.K_5: "5",
    pygame.K_KP5: "5",
    pygame.K_6: "6",
    pygame.K_KP6: "6",
    pygame.K_7: "7",
    pygame.K_KP7: "7",
    pygame.K_8: "8",
    pygame.K_KP8: "8",
    pygame.K_9: "9",
    pygame.K_KP9: "9",
    pygame.K_PLUS: "+",
    pygame.K_KP_PLUS: "+",
    pygame.K_MINUS: "-",
    pygame.K_KP_MINUS: "-",
    pygame.K_ASTERISK: "*",
    pygame.K_KP_MULTIPLY: "*",
    pygame.K_SLASH: "/",
    pygame.K_KP_DIVIDE: "/",
    pygame.K_PERIOD: ".",
    pygame.K_KP_PERIOD: ".",
    pygame.K_EQUALS: "=",
    pygame.K_KP_EQUALS: "=",
    pygame.K_RETURN: "Enter",
    pygame.K_KP_ENTER: "Enter",
}


def keyMap(ky):
    return KEY_NAMES.get(ky)
