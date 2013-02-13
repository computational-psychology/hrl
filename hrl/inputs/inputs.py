"""
The Input module provides classes which allow the reading of simple input from a subject
in HRL. Typical valid inputs are 'Up', 'Down', 'Left', 'Right', and 'Space'. Devices
implementing the Input interface should map these inputs to appropriate keys, or provide a
different keymap with a clear explanation.
"""

# PyGame
import pygame as pg
from pygame.locals import *

# Unqualified Imports
import abc


### Classes ###

class Input(object):
    __metaclass__ = abc.ABCMeta

    # Abstract Methods #

    def readButton(self,to,btns):
        """
        Reads a value from the input device, returning a (button,time)
        pair, where button is the name of the botton pressed, and time
        is the delay between the initial call and the eventual button
        press.
        
        readButton also depends on the provided list of buttons. Only the
        provided button colours will register as a button press. If an
        unlisted colour is pressed, HRL will ignore it and the delay
        clock will keep counting.

        readButton also accepts a timeout, causing readButton to return
        None if this time is exceeded.

        Parameters
        ----------
        to : How long the readButton will wait for a response in
        seconds, returning None if it fails. default = 3600.

        Returns
        -------
        (button,time) where button is the colour name of the
        button pressed, and time is the amount of time in milliseconds
        it took from the initial call to the press.
        """
        return

    # Concrete Methods #

    def __init__(self,btns):
        """
        The Input constructor.

        Parameters
        ----------
        btns : The list of valid button presses.
        """
        self.btns = btns
        pg.init()

    def checkEscape(self):
        """
        A simple function which queries pygame as to whether the Escape key
        has been pressed since the last call, and returns true if it
        has. This function be used within the core loop of the program,
        to allow the user to trigger an event which quits the loop, e.g:

        if in.checkEscape(): break
        """
        eventlist = pg.event.get()
        for event in eventlist:
            if event.type == QUIT \
               or event.type == KEYDOWN and event.key == K_ESCAPE:
                return True
