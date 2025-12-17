import numpy as np
import pytest

pytestmark = [pytest.mark.graphics, pytest.mark.inputs, pytest.mark.interactive]


def test_keyboard():
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
    _ = ihrl.inputs.readButton(btns=["Space"], to=5000)  # 5 second timeout


def test_mouse():
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

    # Draw a circle
    arr = np.zeros((100, 100))
    y, x = np.ogrid[-50:50, -50:50]
    mask = x**2 + y**2 <= 40**2
    arr[mask] = 1.0
    itexture = ihrl.graphics.newTexture(arr)
    itexture.draw(pos=(50, 50), sz=arr.shape)
    ihrl.graphics.flip()

    while not ihrl.inputs.checkEscape():
        # we need to continously check whether the mouse and
        # keyboard/responsepixx has been active. We need to check both
        # in alternation.

        # here we check if a mouse button has been pressed
        # thr: 'threshold' in seconds. Any button press happening in less
        # than this time is ignored. This is necessary as the function
        # reports many times the same single button press
        mouse_pressed, mouse_button, mouse_position = ihrl.inputs.check_mouse_press(thr=0.2)

        # here we check if the keyboard / responsepixx has been pressed.
        # we wait for only 10 ms, so the loop can continue.
        # Default is indefinite time, so we pass the parameter timeout
        # (to) in seconds
        kb_button, _ = ihrl.inputs.readButton(to=0.010)

        # Note: depending on the rest of your code (stimuli rendering etc),
        # you might have to adjust these 'timing' values manually. You need
        # to check it for your specific case.

        # if something has been pressed, we print
        # keyboard / responsepixx pressed?
        if kb_button is not None or ihrl.inputs.checkEscape():
            assert mouse_pressed

        # mouse pressed?
        if mouse_pressed:
            assert mouse_button in ["leftbutton", "middlebutton", "rightbutton"]
            assert len(mouse_position) == 2
            break
