"""
The Input module provides classes which allow the reading of input from a subject in
HRL.

"""

# OpenGL
from OpenGL.GL import *

# PyGame
import pygame as pg
from pygame.locals import *

# Unqualified Imports
import abc


### Classes ###

    def readButton(self,to=3600):
        """
        Reads a value from the ResponsePixx, returning a (colour,time)
        pair, where colour is the colour of the botton pressed, and time
        is the delay between the initial call and the eventual button
        press.
        
        readButton also depends on an initial list of buttons. Only the
        provided button colours will register as a button press. If an
        unlisted colour is pressed, HRL will ignore it and the delay
        clock will keep counting.

        readButton also accepts a timeout, causing readButton to return
        none if this time is exceeded.

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
        if self._dpx != None:
            (btn,tm) = buttonLoop(self._dpx,self._bts,timeout=to)
            return (btn,tm*1000.0)

        else:
            return keyboardLoop(self._bts,timeout=to*1000)

    def checkEscape(self):
        """
        A simple function which queries pygame as to whether the Escape key
        has been pressed since the last call, and returns true if it
        has. This function be used within the core loop of the program,
        to allow the user to trigger an event which quits the loop, e.g.
        if hrl.checkEscape(): break
        """
        eventlist = pg.event.get()
        for event in eventlist:
            if event.type == QUIT \
               or event.type == KEYDOWN and event.key == K_ESCAPE:
                return True

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

def keyboardLoop(btns,timeout):
    """
    keyboardLoop reads a button off the keyboard, returning the time and
    the corresponding colour pressed. However, if the the pressed button
    is not in the HRL's button list, the button pressed will be ignored
    and the clock will keep ticking.
    """
    t0 = pg.time.get_ticks()
    btn = None
    while pg.time.get_ticks() - t0 < timeout:
        event = pg.event.wait()
        if event.type == KEYDOWN:
            btn = checkKey(event.key,btns)
            if btn != None: break
    t = pg.time.get_ticks()
    return (btn,t-t0)

def checkKey(ky,btns):
    """
    Takes a pygame event.key type, a list of button colours (corresponding to the
    ResponsePixx) and returns a button colour, or None a list key wasn't
    pressed.
    """
    up = 'Yellow'
    right = 'Red'
    down = 'Blue'
    left = 'Green'
    space = 'White'

    if (ky == K_UP) & (btns.count(up) > 0): return up
    if (ky == K_RIGHT) & (btns.count(right) > 0): return right
    if (ky == K_DOWN) & (btns.count(down) > 0): return down
    if (ky == K_LEFT) & (btns.count(left) > 0): return left
    if (ky == K_SPACE) & (btns.count(space) > 0): return space
    return None
    
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



## Graphics Class ##

class Graphics(object):
    __metaclass__ = abc.ABCMeta

    # Abstract Methods #

    def greyToChannels(self,gry):
        """
        Converts a single normalized greyscale value (i.e. between 0 and 1)
        into a 4 colour channel representation specific to the particular graphics
        backend.
        """
        return

    # Concrete Methods #

    def __init__(self,w,h,bg,fs,db):
        """
        The Graphics constructor defines the basic OpenGL initializations that must be
        performed besides operations specific to particular backends.
        """

        # Here we can add other options like fullscreen
        dbit = pg.OPENGL
        if fs: dbit = dbit | pg.FULLSCREEN
        if db: dbit = dbit | pg.DOUBLEBUF
        pg.display.set_mode((w,h), dbit)
        pg.mouse.set_visible(False)
        # Here we can change the default color e.g. to grey
        glClearColor(bg,bg,bg,1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        glDisable(GL_DEPTH_TEST)

        # Set Matrix style coordinate system.
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity();
        glOrtho(0,w,h,0,-1,1)
        glMatrixMode(GL_MODELVIEW)

        # Enable texturing
        glEnable(GL_TEXTURE_2D)
        # Enable blending
        glEnable(GL_BLEND)
        # Blend settings. Blending is unrelated to e.g. magnification.
        # Blending is how the colours from transluscent objects are
        # combined, and is therefore largely irrelevant.
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def newTexture(self,grys,shape='square'):
        """
        Given a numpy array of values between 0 and 1, returns a new
        Texture object. The texture object comes equipped with the draw
        method for obvious purposes.

        Parameters
        ----------
        txt : The greyscale numpy array
        shape : The shape to 'cut out' of the given greyscale array. A square
            will render the entire array. Available: 'square', 'circle'
            Default: 'square'

        Returns
        -------
        Texture object

        """
        byts = channelsToInt(self.greyToChannels(grys[::-1,])).tostring()
        wdth = len(grys[0])
        hght = len(grys[:,0])

        return Texture(byts,wdth,hght,shape)

    def flip(self,clr=True):
        """
        Flips in the image backbuffer. In general, one will want to draw
        a set of textures and then call flip to draw them all to the
        screen at once.

        Takes a clr argument which causes the back buffer to clear after
        the flip. When off, textures will be drawn on top of the
        displayed buffer.

        Parameters
        ----------
        clr : Whether to clear the back buffer after flip.

        Returns
        -------
        None
        """
        pg.display.flip()
        if clr: glClear(GL_COLOR_BUFFER_BIT)

    def changeBackground(bg):
        mx = float(2**8-1)
        (r,g,b,a) = greyToChannels(bg)
        glClearColor(r/mx,g/mx,b/mx,a/mx)
        glClear(GL_COLOR_BUFFER_BIT)

## Texture Class ##

class Texture:
    """
    The Texture class is a wrapper object for a compiled texture in
    OpenGL. It's only method is the draw method, which allows a number
    of transformation to be performed on the image before it is
    displayed (e.g. translation, rotation).
    """
    def __init__(self,byts,wdth,hght,shape):
        self._txid, self.wdth, self.hght = loadTexture(byts,wdth,hght)
        if shape == 'square':
            self._dlid = createSquareDL(self._txid,self.wdth,self.hght)
        elif shape == 'circle':
            self._dlid = createCircleDL(self._txid,self.wdth,self.hght)
        else:
            raise NameError('Invalid Shape')

    def __del__(self):
        if self._txid != None:
            deleteTexture(self._txid)
            self._txid = None
        if self._dlid != None:
            deleteTextureDL(self._dlid)
            self._dlid = None

    def draw(self,pos=None,sz=None,rot=0,rotc=None):
        """
        This method draws the texture based on the coordinate system of
        the HRL object from which this texture was generated.

        Parameters
        ----------
        pos : A tuple representing the position of the image in the chosen coordinate
            system.
        sz : A tuple representing the size of the image in the chosen coordinate system.
            None causes the natural width and height of the image to be used, which
            prevents an blending of the image.
        rot : Rotation applied to the image. May result in scaling/interpolation.
        rotc : Defines the centre of the rotation.

        Returns
        -------
        None
        """
        if pos:
            glLoadIdentity()
            glTranslate(pos[0],pos[1],0)

        if rot != 0:
            if rotc == None:
                rotc = (self.wdth / 2, self.hght / 2)
            (w,h) = rotc
            glTranslate(rotc[0],rotc[1],0)
            glRotate(rot,0,0,-1)
            glTranslate(-rotc[0],-rotc[1],0)

        if sz:
            (wdth,hght) = sz
            glScalef(wdth/(self.wdth*1.0), hght/(self.hght*1.0),1.0)

        glCallList(self._dlid)


### OpenGL Functions ###


## OpenGL Texture Functions ##

def channelsToInt((r,g,b,a)):
    """
    Takes a channel representation and returns a corresponding unsigned 32 bit int.
    Running the tostring method on a 2d array which has had this function applied to it
    will produce a bytestring appropriate for use as a texture with openGL.
    """
    R = 2**0
    G = 2**8
    B = 2**16
    A = 2**24
    return r*R + g*G + b*B + a*A

def loadTexture(byts,wdth,hght):
    """
    LoadTexture takes a bytestring representation of a Processed Greyscale array and loads
    it into OpenGL texture memory.

    In this function we also define our texture minification and
    magnification functions, of which there are many options. Take great
    care when shrinking, blowing up, or rotating an image. The resulting
    interpolations can effect experimental results.
    """
    txid = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, txid)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, wdth, hght, 0, GL_RGBA, GL_UNSIGNED_BYTE, byts)

    return txid,wdth,hght

def deleteTexture(txid):
    """
    deleteTexture removes the texture from the OpenGL texture memory.
    """
    glDeleteTextures(txid)

## OpenGL Display List Functions ##

def createSquareDL(txid,wdth,hght):
    """
    createSquareDL takes a texture id with width and height and
    generates a display list - an precompiled set of instructions for
    rendering the image. This speeds up image display. The instructions
    compiled are essentially creating a square and binding the texture
    to it.
    """
    dlid = glGenLists(1)
    glNewList(dlid,GL_COMPILE)
    glBindTexture(GL_TEXTURE_2D, txid)

    glBegin(GL_QUADS)
    glTexCoord2f(0, 0); glVertex2f(0, 0)
    glTexCoord2f(0, 1); glVertex2f(0, hght)
    glTexCoord2f(1, 1); glVertex2f(wdth, hght)
    glTexCoord2f(1, 0); glVertex2f(wdth, 0)
    glEnd()
    glFinish()

    glEndList()

    return dlid

def createCircleDL(txid,wdth,hght):
    """
    createCircleDL takes a texture id with width and height and
    generates a display list - an precompiled set of instructions for
    rendering the image. This speeds up image display. The instructions
    compiled are essentially creating a circle and binding the texture
    to it.
    """
    dlid = glGenLists(1)
    glNewList(dlid,GL_COMPILE)
    glBindTexture(GL_TEXTURE_2D, txid)

    glBegin(GL_TRIANGLE_FAN)

    for ang in np.linspace(0,2*np.pi,360):
        (x,y) = ((np.cos(ang))/2,(np.sin(ang))/2)
        glTexCoord2f(x, y); glVertex2f(x*wdth,y*hght)

    glEnd()
    glFinish()

    glEndList()

    return dlid

def deleteTextureDL(dlid):
    """
    deleteTextureDL removes the given display list from memory.
    """
    glDeleteLists(dlid,1)
