"""
This is the HRL submodule for handling subject input. Input methods (e.g.
keyboards or experiment specific hardware) must implement the Input abstract
base class, which defines common functions required for reading input and
measuring time.
"""

# PyGame
import pygame as pg

# Unqualified Imports
import abc


### Classes ###

class Input(object):
    """
    The Input abstract base class. New hardware inputs must instantiate
    this class. The core abstract method is 'readButton', which returns
    information about the key pressed and the amount of time taken.
    
    'Keys' will generally just be a string indicating the key pressed. Typical
    valid inputs are 'Up', 'Down', 'Left', 'Right', and 'Space', but the actual
    values are specific to the subclasses. Subclasses should come with a
    a clear explanation of the keymap if it deviates from this typical set.
    """
    __metaclass__ = abc.ABCMeta

    # Abstract Methods #

    def readButton(self,btns,to):
        """
        Reads a value from the input device, returning a (button,time) pair,
        where button is the name of the botton pressed, and time is the delay
        between the initial call and the eventual button press.

        readButton also depends on the provided list of buttons. Only the
        buttons indicated in this list will register as a button press. If an
        unlisted button is pressed, HRL will ignore it and the delay
        clock will keep counting. A value of 'None' indicates that all button
        presses are valid.

        readButton also accepts a timeout, causing readButton to return None if
        this time is exceeded. If to is equal to zero, then readButton will not
        time out. (For implementations where this isn't possible, the default
        wait time should be 1 hour.)

        Parameters
        ----------
        btns : The list of accepted buttons. A value of None indicates that all
            values are accepted. Default = None
        to : How long the readButton will wait for a response in seconds,
            returning None if this time elapses. to=0 indicates no timeout.
            Default = 0

        Returns
        -------
        (button,time) : Button is the name of the button pressed, and time is
            the amount of time in seconds it took from the initial call to the
            press.
        """
        return

    # Concrete Methods #

    def __init__(self):
        """
        The Input constructor.
        """
        pg.init()

    def checkEscape(self):
        """
        A simple function which queries pygame as to whether the Escape key
        has been pressed since the last call, and returns true if it has. This
        function can be used within the core loop of a program to allow the user
        to trigger an event which quits the loop, e.g:

            if in.checkEscape(): break

        Returns
        -------
        A boolean indicating whether escape has been pressed since the last
            call.
        """
        eventlist = pg.event.get()
        for event in eventlist:
            if event.type == pg.QUIT \
               or event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                return True
