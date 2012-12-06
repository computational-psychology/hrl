# Local Imports
import datapixx as dpx
import pyoptical as pop

# OpenGL Imports
from OpenGL.GL import *
from OpenGL.GLU import *
import pygame as pg
from pygame.locals import *

# Qualified Imports
import numpy as np
import Image as im


"""
Note that the openGL code was based largely on a great tutorial by a
mysterious tutor here: http://disruption.ca/gutil/introduction.html
"""


### OpenGL Functions ###


def initializeOpenGL(w,h,bg,coords,fs,db):
    """
    InitializeOpenGL is the first function that should be run before other
    openGL calls. It sets a bunch of basic OpenGL commands, notably the
    coordinate system, which has the input dimensions with the origin in
    the lower left corner.
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

    # Set Cartesian coordinate system.
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity();
    (l,r,b,t) = coords
    gluOrtho2D(int(l*w),int(r*w),int(b*h),int(t*h))
    glMatrixMode(GL_MODELVIEW)

    # Enable texturing
    glEnable(GL_TEXTURE_2D)
    # Enable blending
    glEnable(GL_BLEND)
    # Blend settings. Blending is unrelated to e.g. magnification.
    # Blending is how the colours from transluscent objects are
    # combined.
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

def changeBackground(bg,dpxBool):
    mx = float(2**8-1)
    (r,g,b,a) = floatToChans(bg,dpxBool)
    glClearColor(r/mx,g/mx,b/mx,a/mx)
    glClear(GL_COLOR_BUFFER_BIT)

def loadTexture(gar,gammainv,dpxBool):
    """
    LoadTexture is the first step in displaying an image. It takes a
    filename and opens it, or a numpy array, and loads it into the
    OpenGL texture memory.

    In this function we also define our texture minification and
    magnification functions, of which there are many options. Take great
    care when shrinking, blowing up, or rotating an image. The resulting
    interpolations can effect experimental results.
    """
    if type(gar) == str:
        gar = fileToGreyArray(gar)

    gar = gammainv(gar)
    wdth = len(gar[0])
    hght = len(gar[:,0])
    txbys = chansToInt(floatToChans(gar[::-1,],dpxBool)).tostring()

    txid = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, txid)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, wdth, hght, 0, GL_RGBA, GL_UNSIGNED_BYTE, txbys)

    return txid,wdth,hght

def deleteTexture(txid):
    """
    deleteTexture removes the texture from the OpenGL texture memory.
    """
    glDeleteTextures(txid)

def createSquareDL(txid,wdth,hght,coords):
    """
    createSquareDL takes a texture id with width and height and
    generates a display list - an precompiled set of instructions for
    rendering the image. This speeds up image display. The instructions
    compiled are essentially creating a square and binding the texture
    to it.
    """
    lsid = glGenLists(1)
    glNewList(lsid,GL_COMPILE)
    glBindTexture(GL_TEXTURE_2D, txid)
    (l,r,b,t) = coords
    
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0); glVertex2f(l*wdth, b*hght)
    glTexCoord2f(0, 1); glVertex2f(l*wdth, t*hght)
    glTexCoord2f(1, 1); glVertex2f(r*wdth, t*hght)
    glTexCoord2f(1, 0); glVertex2f(r*wdth, b*hght)
    glEnd()
    glFinish()

    glEndList()

    return lsid

def createCircleDL(txid,wdth,hght,coords):
    """
    createCircleDL takes a texture id with width and height and
    generates a display list - an precompiled set of instructions for
    rendering the image. This speeds up image display. The instructions
    compiled are essentially creating a circle and binding the texture
    to it.
    """
    lsid = glGenLists(1)
    glNewList(lsid,GL_COMPILE)
    glBindTexture(GL_TEXTURE_2D, txid)

    (l,r,b,t) = coords
    xstch = r - l
    ystch = t - b
    xtrns = (r + l)/2
    ytrns = (t + b)/2

    glBegin(GL_TRIANGLE_FAN)

    for ang in np.linspace(0,2*np.pi,360):
        (x,y) = ((np.cos(ang))/2,(np.sin(ang))/2)
        glTexCoord2f(x, y); glVertex2f(x*wdth*xstch + xtrns,y*hght*ystch + ytrns)

    glEnd()
    glFinish()

    glEndList()

    return lsid

def deleteTextureDL(lsid):
    """
    deleteTextureDL removes the given display list from memory.
    """
    glDeleteLists(lsid,1)


### OpenGL Classes ###


class Texture:
    """
    The Texture class is a wrapper object for a compiled texture in
    OpenGL. It's only method is the draw method, which allows a number
    of transformation to be performed on the image before it is
    displayed (e.g. translation, rotation).
    """
    def __init__(self,tx,shape,gammainv,coords,flipper,dpxBool):
        self._txid, self.wdth, self.hght = loadTexture(tx,gammainv,dpxBool)
        if shape == 'square':
            self._lsid = createSquareDL(self._txid,self.wdth,self.hght,coords)
        elif shape == 'circle':
            self._lsid = createCircleDL(self._txid,self.wdth,self.hght,coords)
        else:
            raise NameError('Invalid Shape')
        self._flipper = flipper

    def __del__(self):
        if self._txid != None:
            deleteTexture(self._txid)
            self._txid = None
        if self._lsid != None:
            deleteTextureDL(self._lsid)
            self._lsid = None

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
        if pos != None: pos = self._flipper(pos)
        if sz != None: sz = self._flipper(sz)

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

        glCallList(self._lsid)


### DATAPixx functions ###


def initializeDPX():
    """
    InitializeDPX performs a few DataPixx operations in order to ready
    the presentation of images. It returns the datapixx object, which
    must be maintained in order to continue using DataPixx.
    """
    # Open datapixx.
    dpixx = dpx.open()

    # set videomode: Concatenate Red and Green into a 16 bit luminance
    # channel.
    dpixx.setVidMode(dpx.DPREG_VID_CTRL_MODE_M16)

    # Demonstrate successful initialization.
    dpixx.blink(dpx.BWHITE | dpx.BBLUE | dpx.BGREEN
                | dpx.BYELLOW | dpx.BRED)
    return dpixx


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


### PyOptical Functions ###


def initializeOptiCAL(dev,timeout=5):
    return pop.OptiCAL(dev,timeout=timeout)

def tryReadLuminance(phtm,trs,slptm):
    """ Note that reading the optiCAL ocassionally fails. It's worth
    testing a few times. """
    for n in range(trs):
        try: 
            pg.time.delay(slptm)
            lm = phtm.read_luminance()
            print 'Recorded Luminance:',lm
            return lm
        except:
            print 'error while reading OptiCAL' 

    return np.nan


### Miscellaneous Functions ###


# ResponsePixx Helpers

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

# Datapixx Helpers

def fileToGreyArray(fl):
    """
    fileToGreyArray uses PIL to convert an image into a numpy array of floats between 0
    and 1. Note that we assume that the colour resolution is 3*8-bit.
    """
    pic = im.open(fl)
    div = 255.0
    pix = np.array(pic.getdata())
    pix = pix.reshape(pic.size[1], pic.size[0], pix.shape[1])
    return np.mean(pix[:,:,:3],2)/div

def chansToInt((r,g,b,a)):
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

def floatToChans(x,dpxBool):
    """
    Takes a floating point number and a dpx boolean and returns the appropriate channel
    representation for the given greyscale value.
    """
    if dpxBool == False:
        return nodpxFloatToChans(x)
    else:
        return dpxFloatToChans(x)

def dpxFloatToChans(flt):
    """
    Takes a floating point number between 0 and 1 and returns a
    4-channel * 8-bit representation in the datapixx R-G concatenated
    format.
    """
    return dpxIntToChans(np.uint32(flt * (2**16 - 1)))

def dpxIntToChans(n):
    """
    Takes a 16-bit integer and returns a 4-channel * 8-bit
    representation in the datapixx R-G concatenated format.
    """
    return (n / (2**8),n % (2**8),0,2**8 - 1)

def nodpxFloatToChans(flt):
    """
    Takes a floating point number and returns a 4 channel representation
    in a normal, 8 bit, greyscale format.
    """
    return nodpxIntToChans(np.uint32(flt * (2**8 - 1)))

def nodpxIntToChans(n):
    """
    Takes an 8-bit integer and returns the 4-channel representation for a normal monitor
    (i.e. R=G=B=x)
    """
    return (n,n,n,2**8 - 1)
