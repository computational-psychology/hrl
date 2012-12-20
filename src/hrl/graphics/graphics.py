"""
The Graphics module provides classes which allow the presentation of images in
HRL. Image presentation in HRL can be understood as a multi step process as
follows:

    Bitmap image -> Greyscale Array -> Processed Greyscale Array -> OpenGL
    Texture

The conversion of Bitmaps to Greyscale arrays is handled by functions in
'hrl.graphics.auxilliary', though it is recommended when possible to work directly
with numpy arrays.

The conversion of Greyscale Arrays to Processed Greyscale Arrays is handled by
the base 'hrl' class, and consists primarily of gamma correction and contrast
range selection.

Finally, the conversion of Processed Greyscale Arrays to OpenGL textures is
handled by the functionality provided by this module.

The 'Texture' class is essentially an OpenGL wrapper for the display of 2d
images. The abstract class 'Graphics' on the other hand specifies the interface for
graphics hardware in HRL. All graphical backends (e.g. gpu or datapixx) must
satisfy the given interface.

Texture objects are not meant to be created on their own, but are instead
created via the 'newTexture' method of Graphics. Graphics.newTexture will take
the given Processed Greyscale Array (with other optional arguments as well)
and transform it into a Texture object which will be displayed by OpenGL on the
appropriate hardware (e.g. gpu or datapixx).

The openGL code was based largely on a great tutorial by a mysterious tutor
here: http://disruption.ca/gutil/introduction.html
"""

# OpenGL
from OpenGL.GL import *
from OpenGL.GLU import *

# PyGame
import pygame as pg
from pygame.locals import *

# Unqualified Imports
import abc


### Classes ###


class Graphics(object):
    __metaclass__ = abc.ABCMeta

    ## Abstract Methods ##

    def greyToChannels(self,grey):
        """
        Converts a single normalized greyscale value (i.e. between 0 and 1)
        into a 4 colour channel representation appropriate to the graphics
        device.
        """
        return

    def channelsToInt(self,(r,g,b,a)):
        """
        Converts a 4 channel representation of a colour to an integer.
        """
        return

    ## Concrete Methods ##

    def newTexture(self,txt,shape='square'):
        """
        Given a numpy array of values between 0 and 1, returns a new
        Texture object. The texture object comes equipped with the draw
        method for obvious purposes. If a gamma table has been given,
        the texture will be adjusted by inverting the gamma
        function.

        Parameters
        ----------
        txt : The numpy corresponding to the texture.
        shape : The shape 'cut out' of the texture to show. A square
            will show the whole thing. Available: 'square', 'circle'
            Default: 'square'

        Returns
        -------
        Texture object

        """
        return Texture(txt,shape,self._gammainv,self._coords,self._flipper
                       ,self._dpx != None)


    def flip(self,clr=True,dur=None):
        """
        Flips in the image backbuffer. In general, one will want to draw
        a set of textures and then call flip to draw them all to the
        screen at once.

        Takes a clr argument which causes the back buffer to clear after
        the flip. When off, textures will be drawn on top of the
        displayed buffer.

        Also takes an optional duration (dur) argument. If dur != None,
        then the flip command will pause execution for the specified
        number of milliseconds, and then flip the empty buffer forward.
        i.e. if you don't use any other draw commands while it is
        waiting, it will blank the screen after the specified amount of
        time has elapsed.

        Parameters
        ----------
        clr : Whether to clear the back buffer after flip.
        dur : How long to wait before performing a second flip.

        Returns
        -------
        None
        """
        pg.display.flip()
        if clr: glClear(GL_COLOR_BUFFER_BIT)
        if dur != None:
            pg.time.delay(dur)
            pg.display.flip()

    def initialize(self,w,h,bg,coords,fs,db):
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
        (r,g,b,a) = greyToChans(bg)
        glClearColor(r/mx,g/mx,b/mx,a/mx)
        glClear(GL_COLOR_BUFFER_BIT)

### OpenGL Functions ###

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

def loadTexture(gar,dpxBool):
    """
    LoadTexture is the first step in displaying an image. It takes a
    filename and opens it, or a numpy array, and loads it into the
    OpenGL texture memory.

    In this function we also define our texture minification and
    magnification functions, of which there are many options. Take great
    care when shrinking, blowing up, or rotating an image. The resulting
    interpolations can effect experimental results.
    """
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
