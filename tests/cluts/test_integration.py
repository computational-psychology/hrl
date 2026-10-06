"""Integration tests for the CLUT pipeline: measure -> remove_outliers -> average -> smooth -> linearize."""

from pathlib import Path

import numpy as np

from hrl.cluts.calibrate import (
    average,
    channel_sweeps,
    linearize,
    measure,
    remove_outliers,
    smooth,
)
from tests.cluts.conftest import BLACK_POINT, DISPLAY_GAMMA, PRIMARIES_MATRIX, mock_draw

TEST_DIR = Path(__file__).parent


def test_full_clut_pipeline_with_repeats_and_outliers(mock_hrl):
    ihrl = mock_hrl(noise=0.0, rng=42)
    triplets = np.repeat(channel_sweeps(256), 3, axis=0)

    measurements = measure(ihrl, triplets=triplets, stim_draw_func=mock_draw)

    cleaned = remove_outliers(measurements)
    averaged = average(cleaned)
    clut = linearize(averaged, bit_depth=8)

    assert clut.shape == (256, 13)
    assert np.all(np.isfinite(clut))

    # Validate recovered gamma correction is close to the expected inverse monitor gamma.
    x = clut[:, 0]
    expected = np.column_stack(
        [
            x ** (1.0 / DISPLAY_GAMMA[0]),
            x ** (1.0 / DISPLAY_GAMMA[1]),
            x ** (1.0 / DISPLAY_GAMMA[2]),
        ]
    )

    np.testing.assert_allclose(clut[:, 1:4], expected, atol=8e-3)

    # Validate each channel's XYZ: black at input 0, black plus its primary at full input.
    for channel in range(3):
        alone = clut[:, 4 + 3 * channel : 7 + 3 * channel]
        np.testing.assert_allclose(alone[0], BLACK_POINT, atol=5e-3)
        np.testing.assert_allclose(alone[-1], BLACK_POINT + PRIMARIES_MATRIX[:, channel], atol=2e-2)


def test_pipeline_regression_from_saved_measurements():
    """Regression: saved measurements run through full pipeline to known-good CLUT."""
    measurements = np.genfromtxt(TEST_DIR / "measurements_8bit.csv", skip_header=1, delimiter=",")

    result = linearize(smooth(average(remove_outliers(measurements))), bit_depth=8)
    expected = np.genfromtxt(TEST_DIR / "clut_8bit.csv", skip_header=1, delimiter=",")

    np.testing.assert_array_almost_equal(result, expected, decimal=10)
