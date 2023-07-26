import warnings

import numpy as np
import OpenGL.GL as opengl


class Texture:
    """
    The Texture class is a wrapper object for a compiled texture in
    OpenGL. It's only method is the draw method.
    """

    def __init__(self, byts, wdth, hght, shape):
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
        self._txid, self.wdth, self.hght = loadTexture(byts, wdth, hght)
        if shape == "square":
            self._dlid = createSquareDL(self._txid, self.wdth, self.hght)
        elif shape == "circle":
            self._dlid = createCircleDL(self._txid, self.wdth, self.hght)
        else:
            raise NameError("Invalid Shape")

    def draw(self, pos=None, sz=None, rot=0, rotc=None):
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
            opengl.glLoadIdentity()
            opengl.glTranslate(pos[0], pos[1], 0)

        if rot != 0:
            if rotc == None:
                rotc = (self.wdth / 2, self.hght / 2)
            (w, h) = rotc
            opengl.glTranslate(rotc[0], rotc[1], 0)
            opengl.glRotate(rot, 0, 0, -1)
            opengl.glTranslate(-rotc[0], -rotc[1], 0)

        if sz:
            (wdth, hght) = sz
            opengl.glScalef(wdth / (self.wdth * 1.0), hght / (self.hght * 1.0), 1.0)

        opengl.glCallList(self._dlid)

    # JV: Why are we not using this automatic __del__ method?
    # GA: Python's garbage collection was not working properly somehow,
    # that's why I explicitly called the functions to delete textures.
    def __del__(self):
        self.delete()
        
    def delete(self):
        """Remove this texture from the OpenGL texture memory"""
        if self._txid != None:
            opengl.glDeleteTextures(self._txid)
            self._txid = None
        if self._dlid != None:
            opengl.glDeleteLists(self._dlid, 1)
            self._dlid = None


def loadTexture(byts, wdth, hght):
    """
    LoadTexture takes a bytestring representation of a Processed Greyscale array
    and loads it into OpenGL texture memory.

    In this function we also define our texture minification and
    magnification functions, of which there are many options. Take great
    care when shrinking, blowing up, or rotating an image. The resulting
    interpolations can effect experimental results.
    """
    txid = opengl.glGenTextures(1)
    opengl.glBindTexture(opengl.GL_TEXTURE_2D, txid)
    opengl.glTexParameteri(opengl.GL_TEXTURE_2D, opengl.GL_TEXTURE_MAG_FILTER, opengl.GL_LINEAR)
    opengl.glTexParameteri(opengl.GL_TEXTURE_2D, opengl.GL_TEXTURE_MIN_FILTER, opengl.GL_LINEAR)
    opengl.glTexImage2D(
        opengl.GL_TEXTURE_2D,
        0,
        opengl.GL_RGBA,
        wdth,
        hght,
        0,
        opengl.GL_RGBA,
        opengl.GL_UNSIGNED_BYTE,
        byts,
    )

    return txid, wdth, hght


## OpenGL Display List Functions ##


def createSquareDL(txid, wdth, hght):
    """
    createSquareDL takes a texture id with width and height and
    generates a display list - an precompiled set of instructions for
    rendering the image. This speeds up image display. The instructions
    compiled are essentially creating a square and binding the texture
    to it.
    """
    dlid = opengl.glGenLists(1)
    opengl.glNewList(dlid, opengl.GL_COMPILE)
    opengl.glBindTexture(opengl.GL_TEXTURE_2D, txid)

    opengl.glBegin(opengl.GL_QUADS)
    opengl.glTexCoord2f(0, 0)
    opengl.glVertex2f(0, 0)
    opengl.glTexCoord2f(0, 1)
    opengl.glVertex2f(0, hght)
    opengl.glTexCoord2f(1, 1)
    opengl.glVertex2f(wdth, hght)
    opengl.glTexCoord2f(1, 0)
    opengl.glVertex2f(wdth, 0)
    opengl.glEnd()
    opengl.glFinish()

    opengl.glEndList()

    return dlid


def createCircleDL(txid, wdth, hght):
    """
    createCircleDL takes a texture id with width and height and
    generates a display list - an precompiled set of instructions for
    rendering the image. This speeds up image display. The instructions
    compiled are essentially creating a circle and binding the texture
    to it.
    """
    dlid = opengl.glGenLists(1)
    opengl.glNewList(dlid, opengl.GL_COMPILE)
    opengl.glBindTexture(opengl.GL_TEXTURE_2D, txid)

    opengl.glBegin(opengl.GL_TRIANGLE_FAN)

    for ang in np.linspace(0, 2 * np.pi, 360):
        (x, y) = ((np.cos(ang)) / 2, (np.sin(ang)) / 2)
        opengl.glTexCoord2f(x, y)
        opengl.glVertex2f(x * wdth, y * hght)

    opengl.glEnd()
    opengl.glFinish()

    opengl.glEndList()

    return dlid


def deleteTexture(txid):
    """
    deleteTexture removes the texture from the OpenGL texture memory.
    """
    warnings.warn(
        "The function deleteTexture() will be deprecated -- use the Texture.delete() method instead",
        FutureWarning,
    )
    opengl.glDeleteTextures(txid)


def deleteTextureDL(dlid):
    """
    deleteTextureDL removes the given display list from memory.
    """
    warnings.warn(
        "The function deleteTextureDL() will be deprecated -- use the Texture.delete() method instead",
        FutureWarning,
    )
    opengl.glDeleteLists(dlid, 1)
