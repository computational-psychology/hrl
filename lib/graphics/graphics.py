"""
This is the HRL submodule for handling graphics devices and OpenGL. Graphics
devices in HRL instantiate the 'Graphics' abstract class, which defines the
common functions required for displaying greyscale images.

Image presentation in HRL can be understood as a multi step process as follows:

    Bitmap (The image written in an 8 bit, 4 channel format)
    -> Greyscale Array (A numpy array of doubles between 0 and 1)
    -> Processed Greyscale Array (A Gresycale Array remapped with a lookup table)
    -> Display List (An index to a stored texture in graphical memory)
    -> Texture (A python class instance which can be drawn) 

i) The conversion of Bitmaps to Greyscale arrays is handled by functions in
'hrl.extra' Where possible, it is recommended to bypass this step and work
directly with numpy arrays.

ii) The conversion of Greyscale Arrays to Processed Greyscale Arrays is handled by
the base 'hrl' class, and consists primarily of gamma correction and contrast
range selection.

iii) Saving a Processed Greyscale Array into graphics memory and interacting
with it as a Texture object is handled in this module.

The 'Texture' class is a wrapper for certain OpenGL functions designed to
simplify the display of individual 2d images.  The sole method of the Texture
class is 'draw'.

Texture objects are not meant to be created on their own, but are instead
created via the 'newTexture' method of Graphics. Graphics.newTexture will take
a given Processed Greyscale Array (with other optional arguments as well), and
return it as Texture object designed to be shown on the particular Graphics
object.

The openGL code was based largely on a great tutorial by a mysterious tutor
here: http://disruption.ca/gutil/introduction.html
"""

import OpenGL.GL as gl
import pygame as pg
import numpy as np
import abc


### Classes ###


## Graphics Class ##

class Graphics(object):
    """
    The Graphics abstract base class. New graphics hardware must instantiate
    this class. The key method is 'greyToChannels', which defines how to
    represent a greyscale value between 0 and 1 as a 4-tuple (r,g,b,a), so that
    the given grey value is correctly on the Graphics backend.
    """
    __metaclass__ = abc.ABCMeta

    # Abstract Methods #

    def greyToChannels(self,gry):
        """
        Converts a single greyscale value into a 4 colour channel representation
        specific to self (the graphics backend).

        Parameters
        ----------
        gry : The grey value

        Returns
        -------
        (r,g,b,a) the grey represented as a corresponding 4-tuple
        """
        return

    # Concrete Methods #

    def __init__(self,w,h,bg,fs=False,db=True,lut=None):
        """
        The Graphics constructor predefines the basic OpenGL initializations
        that must be performed regardless of the specific backends.

        Parameters
        ----------
        w : The width (in pixels) of the openGL window
        h : The height (in pixels) of the openGL window
        bg : The default background grey value (between 0 and 1)
        fs : Enable fullscreen display (Boolean) Default: False
        db : Enable double buffering (Boolean) Default: True

        Returns
        -------
        Graphics object
        """

        # Here we can add other options like fullscreen
        dbit = pg.OPENGL
        if db: dbit = dbit | pg.DOUBLEBUF
        if fs: dbit = dbit | pg.FULLSCREEN
        screen = pg.display.set_mode((w,h), dbit)

        pg.mouse.set_visible(False)

        # Disables this thing
        gl.glDisable(gl.GL_DEPTH_TEST)

        # Set Matrix style coordinate system.
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity();
        gl.glOrtho(0,w,h,0,-1,1)
        gl.glMatrixMode(gl.GL_MODELVIEW)

        # Enable texturing
        gl.glEnable(gl.GL_TEXTURE_2D)
        # Enable blending
        gl.glEnable(gl.GL_BLEND)
        # Blend settings. Blending is unrelated to e.g. magnification.
        # Blending is how the colours from transluscent objects are
        # combined, and is therefore largely irrelevant.
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

        # Gamma Function Correction
        self._lut = None
        self._gammainv = lambda x: x
        if lut != None:
            print "..using look-up table: %s" % lut
            self._lut = np.genfromtxt(lut,skip_header=1)
            self._gammainv = lambda x: np.interp(x,self._lut[:,0],self._lut[:,1])

        # Here we change the default color 
        self.changeBackground(bg)
        self.flip()

    def newTexture(self,grys0,shape='square'):
        """
        Given a numpy array of values between 0 and 1, returns a new
        Texture object. The texture object comes equipped with the draw
        method for obvious purposes.
        
        NB: Images in HRL are represented in matrix style coordinates. i.e. the
        origin is in the upper left corner, and increases to the right and
        downwards.

        Parameters
        ----------
        grys : The greyscale numpy array
        shape : The shape to 'cut out' of the given greyscale array. A square
            will render the entire array. Available: 'square', 'circle'
            Default: 'square'

        Returns
        -------
        Texture object
        """
        grys = np.flipud(grys0)     # flipping up-down necessary
        grys = self._gammainv(grys) # added gamma correction
        
        byts = channelsToInt(self.greyToChannels(grys[::-1,])).tostring()
        wdth = len(grys[0])
        hght = len(grys[:,0])

        return Texture(byts,wdth,hght,shape)

    def flip(self,clr=True):
        """
        Flips in the image backbuffer. In general, one will want to draw
        a set of Textures and then call flip to display them all at once.

        Takes a clr argument which causes the back buffer to clear after
        the flip. When off, textures will be drawn on top of the current back
        buffer. By default the back buffer will be cleared automatically, but in
        performance sensitive scenarios it may be worth turning this off.

        Parameters
        ----------
        clr : Whether to clear the back buffer after flip. Default: True
        """
        pg.display.flip()
        if clr: gl.glClear(gl.GL_COLOR_BUFFER_BIT)

    def changeBackground(self,bg):
        """
        Changes the current background grey value.

        Parameters
        ----------
        bg : The new gray value (between 0 and 1)
        """
        mx = float(2**8-1)
        (r,g,b,a) = self.greyToChannels(bg)
        gl.glClearColor(r/mx,g/mx,b/mx,a/mx)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

## Texture Class ##

class Texture:
    """
    The Texture class is a wrapper object for a compiled texture in
    OpenGL. It's only method is the draw method.
    """
    def __init__(self,byts,wdth,hght,shape):
        """
        The internal constructor for Textures. Users should use
        Graphics.newTexture to create textures rather than this constructor.

        Parameters
        ----------
        byts : A bytestring representation of the greyscale array
        wdth : The width of the array
        hght : The height of the array
        shape : The shape to 'cut out' of the given greyscale array. A square
            will render the entire array. Available: 'square', 'circle'

        Returns
        -------
        Texture object
        """
        self._txid, self.wdth, self.hght = loadTexture(byts,wdth,hght)
        if shape == 'square':
            self._dlid = createSquareDL(self._txid,self.wdth,self.hght)
        elif shape == 'circle':
            self._dlid = createCircleDL(self._txid,self.wdth,self.hght)
        else:
            raise NameError('Invalid Shape')

#   def __del__(self):
#       if self._txid != None:
#           deleteTexture(self._txid)
#           self._txid = None
#       if self._dlid != None:
#           deleteTextureDL(self._dlid)
#           self._dlid = None

    def draw(self,pos=None,sz=None,rot=0,rotc=None):
        """
        This method loads the Texture into the back buffer. Calling
        Graphics.flip will cause it to be drawn to the screen. It also allows a
        number of transformation to be performed on the image before it is
        loaded (e.g. translation, rotation)

        Parameters
        ----------
        pos : A pair (rows,columns) representing the the position in pixels in
            the Graphics window of the upper left corner (origin) of the Texture
        sz : A tuple (width,height) representing the size of the image in
            pixels.  None causes the natural width and height of the image to be
            used, which prevents an blending of the image.
        rot : Rotation applied to the image. May result in scaling/interpolation.
        rotc : Defines the centre of the rotation.

        Returns
        -------
        None
        """
        if pos:
            gl.glLoadIdentity()
            gl.glTranslate(pos[0],pos[1],0)

        if rot != 0:
            if rotc == None:
                rotc = (self.wdth / 2, self.hght / 2)
            (w,h) = rotc
            gl.glTranslate(rotc[0],rotc[1],0)
            gl.glRotate(rot,0,0,-1)
            gl.glTranslate(-rotc[0],-rotc[1],0)

        if sz:
            (wdth,hght) = sz
            gl.glScalef(wdth/(self.wdth*1.0), hght/(self.hght*1.0),1.0)

        gl.glCallList(self._dlid)


### Internal Functions ###


## OpenGL Texture Functions ##


def channelsToInt((r,g,b,a)):
    """
    Takes a channel representation and returns a corresponding unsigned 32 bit
    int.  Running the tostring method on a 2d array which has had this function
    applied to it will produce a bytestring appropriate for use as a texture
    with openGL.
    """
    R = 2**0
    G = 2**8
    B = 2**16
    A = 2**24
    return r*R + g*G + b*B + a*A

def loadTexture(byts,wdth,hght):
    """
    LoadTexture takes a bytestring representation of a Processed Greyscale array
    and loads it into OpenGL texture memory.

    In this function we also define our texture minification and
    magnification functions, of which there are many options. Take great
    care when shrinking, blowing up, or rotating an image. The resulting
    interpolations can effect experimental results.
    """
    txid = gl.glGenTextures(1)
    gl.glBindTexture(gl.GL_TEXTURE_2D, txid)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
    gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, wdth, hght, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, byts)

    return txid,wdth,hght

def deleteTexture(txid):
    """
    deleteTexture removes the texture from the OpenGL texture memory.
    """
    gl.glDeleteTextures(txid)

## OpenGL Display List Functions ##

def createSquareDL(txid,wdth,hght):
    """
    createSquareDL takes a texture id with width and height and
    generates a display list - an precompiled set of instructions for
    rendering the image. This speeds up image display. The instructions
    compiled are essentially creating a square and binding the texture
    to it.
    """
    dlid = gl.glGenLists(1)
    gl.glNewList(dlid,gl.GL_COMPILE)
    gl.glBindTexture(gl.GL_TEXTURE_2D, txid)

    gl.glBegin(gl.GL_QUADS)
    gl.glTexCoord2f(0, 0); gl.glVertex2f(0, 0)
    gl.glTexCoord2f(0, 1); gl.glVertex2f(0, hght)
    gl.glTexCoord2f(1, 1); gl.glVertex2f(wdth, hght)
    gl.glTexCoord2f(1, 0); gl.glVertex2f(wdth, 0)
    gl.glEnd()
    gl.glFinish()

    gl.glEndList()

    return dlid

def createCircleDL(txid,wdth,hght):
    """
    createCircleDL takes a texture id with width and height and
    generates a display list - an precompiled set of instructions for
    rendering the image. This speeds up image display. The instructions
    compiled are essentially creating a circle and binding the texture
    to it.
    """
    dlid = gl.glGenLists(1)
    gl.glNewList(dlid,gl.GL_COMPILE)
    gl.glBindTexture(gl.GL_TEXTURE_2D, txid)

    gl.glBegin(gl.GL_TRIANGLE_FAN)

    for ang in np.linspace(0,2*np.pi,360):
        (x,y) = ((np.cos(ang))/2,(np.sin(ang))/2)
        gl.glTexCoord2f(x, y); gl.glVertex2f(x*wdth,y*hght)

    gl.glEnd()
    gl.glFinish()

    gl.glEndList()

    return dlid

def deleteTextureDL(dlid):
    """
    deleteTextureDL removes the given display list from memory.
    """
    gl.glDeleteLists(dlid,1)
