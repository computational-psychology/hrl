import numpy as np
import pytest


@pytest.mark.graphics
def test_gpu_init():
    from hrl.graphics.gpu import GPU_RGB

    igraphics = GPU_RGB(
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
def test_gpu_background_triplet():
    from hrl.graphics.gpu import GPU_RGB

    igraphics = GPU_RGB(
        width=200,
        height=200,
        background=[1, 0, 0],
        fullscreen=False,
        double_buffer=True,
        mouse=True,
        lut=None,
    )
    igraphics.flip()


@pytest.mark.graphics
def test_gpu_texture():
    from hrl.graphics.gpu import GPU_RGB

    igraphics = GPU_RGB(
        width=200,
        height=200,
        background=[0.5, 0.5, 0.5],
        fullscreen=False,
        double_buffer=True,
        mouse=True,
        lut=None,
    )
    igraphics.flip()
    arr = np.random.random((100, 100, 3))
    itexture = igraphics.newTexture(arr)
    itexture.draw(pos=(50, 50), sz=arr.shape[:2])
    igraphics.flip()
