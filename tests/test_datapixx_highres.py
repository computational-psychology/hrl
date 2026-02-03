import tempfile

import numpy as np
import pytest

from hrl.luts import create_lut

pytestmark = [pytest.mark.graphics, pytest.mark.interactive, pytest.mark.pixx]


def high_res_lut(bit_depth=16):
    """Linear LUT for high luminance resolution"""
    n_entries = 2**bit_depth
    return create_lut(gamma=1.0, k=1.0, dark=0.0, n=n_entries)


def grating_stim(high_res_lut, center_step=0.5, n_steps=17, grating_width=720, grating_height=80):
    # Pick steps around center intensity
    step_indices = range(int(center_step - n_steps // 2) - 1, int(center_step + n_steps // 2 + 1))
    center_indx = np.array(high_res_lut)[:, 0].searchsorted(center_step)
    selected_indices = center_indx + np.array(step_indices)

    # Calculate bar width from grating width and number of steps
    bar_width = grating_width // len(selected_indices)

    # Create grating texture
    grating_vals = np.array(high_res_lut)[selected_indices, 1]
    # Create bars: each value repeated to form grating_height x bar_width blocks
    grating_texture = np.repeat(grating_vals, bar_width).reshape(1, -1)
    grating_texture = np.tile(grating_texture, (grating_height, 1))

    # Add alternating black-white markers at the top and bottom
    marker_height = 5
    # Create marker pattern: alternating blocks of bar_width matching each bar
    marker_vals = np.tile([0.0, 1.0], len(grating_vals) // 2 + 1)[: len(grating_vals)]
    marker_pattern = np.repeat(marker_vals, bar_width)
    top_markers = np.tile(marker_pattern, (marker_height, 1))
    bottom_markers = top_markers.copy()
    grating_texture[:marker_height, :] = top_markers
    grating_texture[-marker_height:, :] = bottom_markers

    return grating_texture


def show_grating(ihrl, bit_depth=16):
    # Display test grating
    grating = grating_stim(
        high_res_lut(bit_depth=bit_depth),
        n_steps=bit_depth + 1,
        grating_height=int(ihrl.graphics.height // 2),
        grating_width=int(ihrl.graphics.width * 0.8),
    )
    itexture = ihrl.graphics.newTexture(grating)
    graphics_center = np.array((ihrl.graphics.height // 2, ihrl.graphics.width // 2))
    stim_center = np.array(grating.shape) // 2
    centralized = graphics_center - stim_center
    itexture.draw(pos=(centralized[1], centralized[0]), sz=(grating.shape[1], grating.shape[0]))
    ihrl.graphics.flip()


def test_datapixx_highres():
    from hrl import HRL

    bit_depth = 16

    # Save test LUT to tmp file
    tmpfile = tempfile.NamedTemporaryFile(suffix=".csv").name
    np.savetxt(
        tmpfile,
        high_res_lut(bit_depth=bit_depth),
        delimiter=" ",
        header="intensity_in,intensity_out,luminance",
        comments="",
    )

    # Initialize HRL with Datapixx graphics and test LUT
    ihrl = HRL(
        graphics="datapixx",
        inputs="responsepixx",
        scrn=1,
        wdth=1024,
        hght=768,
        bg=0.2,
        fs=False,
        db=True,
        lut=tmpfile,
    )

    # Show test grating
    show_grating(ihrl, bit_depth=bit_depth)

    # Wait for keypress
    print("Press a button to exit display")
    _ = ihrl.inputs.readButton(btns=["Space"], to=30000)  # 30 second timeout


def test_datapixx_lowres():
    from hrl import HRL

    bit_depth = 8

    # Save test LUT to tmp file
    tmpfile = tempfile.NamedTemporaryFile(suffix=".csv").name
    np.savetxt(
        tmpfile,
        high_res_lut(bit_depth=bit_depth),
        delimiter=" ",
        header="intensity_in,intensity_out,luminance",
        comments="",
    )

    # Initialize HRL with Datapixx graphics and test LUT
    ihrl = HRL(
        graphics="datapixx",
        inputs="responsepixx",
        scrn=1,
        wdth=1024,
        hght=768,
        bg=0.2,
        fs=False,
        db=True,
        lut=tmpfile,
    )

    # Show test grating
    show_grating(ihrl, bit_depth=bit_depth)

    # Wait for keypress
    print("Press a button to exit display")
    _ = ihrl.inputs.readButton(btns=["Space"], to=30000)  # 30 second timeout


def test_failure():
    from hrl import HRL

    bit_depth = 16

    # Save test LUT to tmp file
    tmpfile = tempfile.NamedTemporaryFile(suffix=".csv").name
    np.savetxt(
        tmpfile,
        high_res_lut(bit_depth=bit_depth),
        delimiter=" ",
        header="intensity_in,intensity_out,luminance",
        comments="",
    )

    # Initialize HRL with Datapixx graphics and test LUT
    ihrl = HRL(
        graphics="datapixx",
        inputs="responsepixx",
        scrn=1,
        wdth=1024,
        hght=768,
        bg=0.2,
        fs=False,
        db=True,
        lut=tmpfile,
    )

    # Set incorrect mode
    ihrl.device.setVideoMode("C24")
    ihrl.device.updateRegisterCache()
    print(f"Set mode to {ihrl.device.getVideoMode()}")

    # Show test grating
    show_grating(ihrl, bit_depth=bit_depth)

    # Wait for keypress
    print("Press a button to exit display")
    _ = ihrl.inputs.readButton(btns=["Space"], to=30000)  # 30 second timeout


if __name__ == "__main__":
    print("Test high resolution mode. Should see a smooth grating of 16(+1) bars")
    test_datapixx_highres()

    print("Test lower resolution mode. Should see a less smooth grating of 8(+1) bars")
    test_datapixx_lowres()

    print("Test failure/incorrect mode setting. Should see fewer bars")
    test_failure()
