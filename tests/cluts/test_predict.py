"""Tests for `predict`: the color a CLUT expects for measured inputs."""

import numpy as np

from hrl.cluts import differences
from hrl.cluts.calibrate import predict
from tests.cluts.conftest import BLACK_POINT, DISPLAY_CLUT, PRIMARIES_MATRIX

CLUT = DISPLAY_CLUT

# Each channel on its own, at levels between the CLUT's tabulated inputs as well as on them
LEVELS = np.random.default_rng(0).uniform(0.0, 1.0, size=20)
INPUTS = np.vstack([np.eye(3)[channel] * LEVELS[:, None] for channel in range(3)])


def _readings(inputs, scale=(1.0, 1.0, 1.0)):
    """What the display this CLUT describes reads, with the CLUT applied, scaled per axis.

    With its CLUT applied, a channel of this parametric display adds light in a straight
    line with its input: black plus the input times its primary.
    """
    inputs = np.asarray(inputs, dtype=float)
    return np.column_stack(
        [inputs, (BLACK_POINT + inputs @ PRIMARIES_MATRIX.T) * np.asarray(scale)]
    )


# --- predict, from a CLUT -------------------------------------------------------------------


def test_a_display_the_CLUT_describes_exactly_is_predicted_exactly():
    readings = _readings(INPUTS)

    np.testing.assert_allclose(predict(readings, CLUT), readings[:, 3:], atol=1e-9)


def test_predicts_row_for_row_without_averaging():
    readings = np.vstack([_readings(INPUTS), _readings(INPUTS[:5])])

    assert predict(readings, CLUT).shape == (len(INPUTS) + 5, 3)


def test_black_is_predicted_by_the_first_row():
    np.testing.assert_allclose(predict(np.zeros((1, 3)), CLUT)[0], CLUT[0, 4:7], atol=1e-12)


def test_a_uniformly_brighter_display_differs_only_in_luminance():
    readings = _readings(INPUTS, scale=(1.02, 1.02, 1.02))

    _, luminance, chromaticity = differences(readings[:, 3:], predict(readings, CLUT)).T

    np.testing.assert_allclose(luminance, 0.02, atol=1e-9)
    np.testing.assert_allclose(chromaticity, 0.0, atol=1e-9)
