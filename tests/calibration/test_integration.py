"""Tests for the complete measurement → smooth → linearize pipeline."""

import types
from pathlib import Path

import numpy as np
import pytest

from hrl.calibration.measurement import (
    average,
    combine,
    linearize,
    measure_lut,
    remove_outliers,
    smooth,
)
from hrl.luts import create_lut
from hrl.photometer.mock import MockPhotometer

TEST_DIR = Path(__file__).parent


def _make_mock_hrl(lut, noise=0.0, rng=None):
    ihrl = types.SimpleNamespace()
    ihrl.photometer = MockPhotometer(lut=lut, noise=noise, rng=rng)
    ihrl.graphics = types.SimpleNamespace(gamma_correct=lambda x: x)
    ihrl.inputs = None
    return ihrl


def mock_draw(ihrl, intensity):
    ihrl.photometer.current_intensity = intensity


TEST_DIR = Path(__file__).parent


def test_full_pipeline():
    """Complete pipeline from created LUT, through measurements, smoothing and linearization.

    The physical monitor response is simulated via create_lut (gamma=2.2).

    Starting point: 256 intensity measurements with gamma~2.2 nonlinearity
    Pipeline: measure_lut → combine → remove_outliers → average → smooth(order=0) → linearize
    Validates: mock + pipeline produces exactly the same LUT as linearize(gamma_curve) directly.
    Pipeline: smooth with order=0 (averaging) → linearize at 8-bit resolution
    Validates: Final LUT matches expected values from unit tests
    """
    # Setup

    # Synthetic physical response: intensity → luminance  (256 points, gamma=2.2)
    # create_lut columns: (intensity_in, intensity_out, luminance)
    # intensity_out is the raw, unlinearized value sent to the monitor — it has the
    # gamma relationship with luminance.  Pass lut[:,1:] so the mock maps
    # intensity_out → luminance.
    raw_lut = create_lut(n=256, gamma=2.2, k=100.0, dark=1.0)

    # Configure noiseless mock with the gamma response (intensity_out → luminance)
    ihrl = _make_mock_hrl(raw_lut, noise=0.0)

    # Step 0: simulate measurements at the raw (intensity_out) intensities, noiseless, 1 sample each
    measurements = measure_lut(
        ihrl,
        intensities=raw_lut[:, 1],
        stim_draw_func=mock_draw,
        n_samples=1,
    )

    # Step 0b: combine measurements table(s) into luminance map
    lum_map = combine([measurements])

    # Step 1: remove outliers
    lum_map = remove_outliers(lum_map)

    # Step 2: average
    table = average(lum_map)

    # Step 3: smooth (optional)
    table[:, 1] = smooth(table[:, 1], order=0)

    # Step 4: linearize to create LUT
    result_lut = linearize(table, bit_depth=8)

    # Verify
    np.testing.assert_array_almost_equal(result_lut, raw_lut, decimal=10)


@pytest.mark.parametrize("bit_depth", [8, 16])
def test_regression(bit_depth):
    """Regression test: pipeline on saved measurements reproduces the ground-truth LUT.

    Input: noiseless intensity measurements (1 sample each)
    Pipeline: combine → remove_outliers → average → smooth(order=0) → linearize
    Validates: Final LUT matches the ground-truth LUT exactly
    """
    measurements = np.genfromtxt(
        TEST_DIR / f"measurements_{bit_depth}bit.csv", skip_header=1, delimiter=","
    )

    lum_map = combine([measurements])
    lum_map = remove_outliers(lum_map)
    table = average(lum_map)
    table[:, 1] = smooth(table[:, 1], order=0)
    result_lut = linearize(table, bit_depth=bit_depth)

    expected_lut = np.genfromtxt(
        TEST_DIR / f"lut_{bit_depth}bit.csv", skip_header=1, delimiter=","
    )
    np.testing.assert_array_almost_equal(result_lut, expected_lut, decimal=10)


def test_pipeline_preserves_luminance_range():
    """Pipeline preserves original luminance range from measurements to final LUT.

    Input: 80 intensity measurements with gamma~2.0 nonlinearity, 2.5-150 cd/m² range
    Pipeline: smooth with 1 kernel iteration → linearize at 8-bit resolution
    Validates: Final LUT matches expected values and preserves min/max luminance within 5%
    """
    # Setup
    lum_min, lum_max = 2.5, 150.0
    measurements = np.genfromtxt(
        TEST_DIR / "measurements_lumrange.csv", skip_header=1, delimiter=","
    )

    # Step 0: combine measurements table(s) into luminance map
    lum_map = combine([measurements])

    # Step 1: remove outliers
    lum_map = remove_outliers(lum_map)

    # Step 2: average
    table = average(lum_map)

    # Step 3: smooth (optional)
    table[:, 1] = smooth(table[:, 1], order=1)

    # Step 4: linearize to create LUT
    result_lut = linearize(table, bit_depth=8)

    # Verify luminance range preserved within 5%
    assert np.isclose(result_lut[0, 2], lum_min, rtol=0.05)
    assert np.isclose(result_lut[-1, 2], lum_max, rtol=0.05)

    # Verify values
    expected_lut = np.genfromtxt(TEST_DIR / "lut_lumrange.csv", skip_header=1, delimiter=",")
    np.testing.assert_array_almost_equal(result_lut, expected_lut, decimal=10)


def test_pipeline_combines_multiple_sessions():
    """Merging measurements from two sessions gives the same result as one session.

    Input: 256 intensity measurements split into two interleaved sessions
    Pipeline: combine([session1, session2]) → remove_outliers → average → smooth(order=0) → linearize (8-bit)
    Validates: Multi-session combine path produces the same LUT as a single session
    """
    # Setup: split by interleaving so each intensity appears in exactly one session
    measurements = np.genfromtxt(TEST_DIR / "measurements_8bit.csv", skip_header=1, delimiter=",")
    session1 = measurements[::2]
    session2 = measurements[1::2]

    # Step 0: combine two sessions into luminance map
    lum_map = combine([session1, session2])

    # Step 1: remove outliers
    lum_map = remove_outliers(lum_map)

    # Step 2: average
    table = average(lum_map)

    # Step 3: smooth
    table[:, 1] = smooth(table[:, 1], order=0)

    # Step 4: linearize to create LUT
    result_lut = linearize(table, bit_depth=8)

    # Verify: result matches the single-session LUT
    expected_lut = np.genfromtxt(TEST_DIR / "lut_8bit.csv", skip_header=1, delimiter=",")
    np.testing.assert_array_almost_equal(result_lut, expected_lut, decimal=10)
