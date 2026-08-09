"""Test that CLUTs are properly applied by RGB graphics objects."""

from pathlib import Path

import numpy as np
import pytest

import hrl.graphics
from hrl.cluts import RGB_to_XYZ
from hrl.photometer.photometer import MockColorimeter


@pytest.mark.graphics
@pytest.mark.parametrize("clut", argvalues=["clut_8bit.csv", "clut_10bit.csv"])
def test_clut_applied(clut):
    """Check that RGB gamma correction matches CLUT output columns."""
    clut_path = Path(__file__).parent / clut

    # Create an RGB graphics instance with the CLUT.
    igraphics = hrl.graphics.new_graphics(
        graphics_alias="RGB", width=64, height=64, background=[0.5, 0.5, 0.5], lut=clut_path
    )

    # Check that CLUT is loaded in expected 13-column format.
    assert igraphics._lut is not None
    assert igraphics._lut.shape[1] == 13

    # Probe grayscale triplets across CLUT input intensities.
    # For each input intensity x, expected output is [R_out(x), G_out(x), B_out(x)].
    input_intensities = igraphics._lut[:, 0]
    input_triplets = np.repeat(input_intensities[:, None], 3, axis=1).reshape(-1, 1, 3)
    expected_output_triplets = igraphics._lut[:, 1:4]

    output_triplets = igraphics.gamma_correct(input_triplets).reshape(-1, 3)

    np.testing.assert_allclose(output_triplets, expected_output_triplets, atol=1e-5)


@pytest.mark.graphics
@pytest.mark.parametrize("clut", argvalues=["clut_8bit.csv", "clut_10bit.csv"])
def test_clut_verified_via_mock_colorimeter_measurement(clut):
    """Verify CLUT use by graphics via MockColorimeter XYZ measurements.

    The mock colorimeter measures emitted RGB -> XYZ using the full
    per-level CLUT forward model, treating its input as an already-driven
    signal (`gamma_correct=False`) -- that's what a real colorimeter would
    be pointed at. If graphics applies the CLUT correctly, measured XYZ
    should match the XYZ predicted from the CLUT-corrected RGB, and deviate
    from the uncorrected (raw RGB) prediction.
    """
    clut_path = Path(__file__).parent / clut
    clut_table = np.genfromtxt(clut_path, skip_header=1, delimiter=",")

    igraphics = hrl.graphics.new_graphics(
        graphics_alias="RGB", width=64, height=64, background=[0.5, 0.5, 0.5], lut=clut_path
    )

    def emitted_rgb_to_xyz(r, g, b):
        triplet = np.array([r, g, b], dtype=float)
        xyz = RGB_to_XYZ(triplet, clut_table, gamma_correct=False)
        return tuple(xyz[0])

    colorimeter = MockColorimeter(color_mapping=emitted_rgb_to_xyz)

    probe_intensities = np.linspace(0.0, 1.0, 17)
    raw_triplets = np.repeat(probe_intensities[:, None], 3, axis=1)

    corrected_triplets = igraphics.gamma_correct(raw_triplets.reshape(-1, 1, 3)).reshape(-1, 3)

    measured_xyz = []
    for triplet in corrected_triplets:
        colorimeter.current_triplet = triplet
        measured_xyz.append(colorimeter.readTristimulus())
    measured_xyz = np.array(measured_xyz)

    expected_xyz_with_clut = RGB_to_XYZ(
        corrected_triplets, clut_table, gamma_correct=False
    )

    expected_xyz_without_clut = RGB_to_XYZ(raw_triplets, clut_table, gamma_correct=False)

    np.testing.assert_allclose(measured_xyz, expected_xyz_with_clut, atol=1e-7)

    # Mid-range points should differ from the no-CLUT prediction for non-identity CLUTs.
    mid = (probe_intensities > 0.1) & (probe_intensities < 0.9)
    diff_no_clut = np.abs(measured_xyz[mid] - expected_xyz_without_clut[mid])
    assert np.max(diff_no_clut) > 1e-3
