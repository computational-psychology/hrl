import hrl
import pygame as pg
from pygame.locals import *
from OpenGL.GL import *
from patterns import *
from random import shuffle, randint

ntls = 4
wdth = 1024
hght = 766


def circle(y, ptch):
    y = np.mod(y, 2) - 1
    x = np.sin(-np.pi * y) / 2 + 0.5
    y = np.abs(y)
    return np.round((wdth - ptch.wdth) * x), np.round((hght - ptch.hght) * y)


def circleTileDraw(pstd, ptst):
    itst = 2
    stp = 2.0 / ntls

    for n in range(ntls):
        if n == itst:
            ptst.draw(circle(stp * n, ptst))
        else:
            pstd.draw(circle(stp * n, pstd))


def main():
    pg.init()
    hrl.initializeOpenGL(1024, 766)
    dpx = hrl.initializeDPX()

    done = False

    im1 = hrl.Texture("data/alien.png")
    im2 = hrl.Texture("data/cow.png")
    # im = hrl.Texture(flatGradient(1024,766),dpx=True)
    # im = hrl.Texture('data/linear_rg_gradient.bmp')

    while not done:
        circleTileDraw(im1, im2)
        # im.draw()
        # im1.draw((0,0),300,300)
        # im1.draw((300,550),200,200)
        # im2.draw((550,300),200,200)
        # im2.draw((300,50),200,200)
        # im2.draw((50,300),200,200)

        pg.display.flip()

        eventlist = pg.event.get()
        for event in eventlist:
            if event.type == QUIT or event.type == KEYDOWN and event.key == K_ESCAPE:
                done = True


if __name__ == "__main__":
    main()

### pygame.time.Clock() objects can be used to measure the amount of time between events. ###
