import numpy as np
import pytest


def test_import():
    import hrl


@pytest.mark.graphics
def test_gpu_init():
    from hrl.graphics.gpu import GPU

    igraphics = GPU(
        width=200,
        height=200,
        background=0.5,
        fullscreen=False,
        double_buffer=True,
        mouse=True,
        lut=None,
    )
    igraphics.flip()


@pytest.mark.graphics
def test_gpu_texture():
    from hrl.graphics.gpu import GPU

    igraphics = GPU(
        width=200,
        height=200,
        background=0.5,
        fullscreen=False,
        double_buffer=True,
        mouse=True,
        lut=None,
    )
    igraphics.flip()
    arr = np.random.random((100, 100))
    itexture = igraphics.newTexture(arr)
    itexture.draw(pos=(50, 50), sz=arr.shape)
    igraphics.flip()


@pytest.mark.inputs
def test_keyboard():
    from hrl.inputs.keyboard import Keyboard

    ikeyboard = Keyboard()
    btns, _ = ikeyboard.readButton(btns=["Left", "Right"], to=0.01)
    assert btns is None


@pytest.mark.graphics
@pytest.mark.inputs
def test_hrl_class():
    from hrl import HRL

    ihrl = HRL(
        graphics="gpu",
        inputs="keyboard",
        wdth=200,
        hght=200,
        bg=0.5,
        fs=False,
        db=True,
        mouse=True,
        lut=None,
    )

    # Test texture drawing
    arr = np.random.random((100, 100))
    itexture = ihrl.graphics.newTexture(arr)
    itexture.draw(pos=(50, 50), sz=arr.shape)
    ihrl.graphics.flip()

    # Test keyboard input
    btns, _ = ihrl.inputs.readButton(btns=["Left", "Right"], to=0.01)
    assert btns is None
