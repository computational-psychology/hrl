"""Test that the LUT is properly applied"""

from pathlib import Path

import numpy as np
import pytest

import hrl.graphics


@pytest.mark.graphics
@pytest.mark.parametrize("lut", argvalues=["lut_8bit.csv", "lut_10bit.csv", "lut_oldformat.csv"])
def test_lut_applied(lut):
    """Test that the LUT is properly applied by checking that the output values match expected values."""
    lut_path = Path(__file__).parent / lut

    # Create a GPU_grey instance with the LUT
    igraphics = hrl.graphics.new_graphics(
        graphics_alias="gpu", width=64, height=64, background=0.5, lut=lut_path
    )

    # Check that LUT is properly loaded
    assert igraphics._lut is not None
    assert igraphics._lut.shape[1] == 3  # Expecting 3 columns: input, output, luminance

    # Run through a range of input intensities and get the output values after applying the LUT
    input_intensities = igraphics._lut[:, 0]  # Input intensities from the LUT
    expected_output_intensities = igraphics._lut[:, 1]  # Expected output
    output_intensities = np.array([igraphics.gamma_correct(i) for i in input_intensities])

    # Check that the actual output matches the expected output within a tolerance
    np.testing.assert_allclose(output_intensities, expected_output_intensities, atol=1e-5)
