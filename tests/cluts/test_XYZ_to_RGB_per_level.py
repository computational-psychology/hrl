"""Tests for `XYZ_to_RGB` (per level), which finds the input that shows a wanted color.

The measured-like CLUT below is built through the whole pipeline from noisy simulated
readings, because that is the case that is hard: a clean parametric CLUT inverts
trivially.
"""

import numpy as np
import pytest

from hrl.cluts import RGB_to_XYZ, XYZ_to_RGB
from hrl.cluts.calibrate import (
    average,
    linearize,
    make_monotonic,
    remove_outliers,
    smooth,
)
from hrl.cluts.triplets import channel_sweeps
from tests.cluts.conftest import DISPLAY_CLUT, display_xyz


def _measured_like_clut(noise=0.02, seed=0, width=9):
    """A CLUT built the way a real one is: noisy readings, outliers out, smoothed, made
    monotonic, linearized.

    The noise and smoothing width are chosen to leave the channel curves strictly
    increasing, which is what the inverse needs; `test_the_inverse_is_only_as_good_as
    _the_fit` covers what happens when they are not.
    """
    triplets = np.repeat(channel_sweeps(256), 5, axis=0)
    xyz = 100.0 * display_xyz(triplets)
    xyz = xyz * (1.0 + np.random.default_rng(seed).normal(0.0, noise, size=xyz.shape))
    measurements = np.column_stack([triplets, xyz])
    return linearize(make_monotonic(smooth(average(remove_outliers(measurements)), width=width)))


CLUTS = {
    "parametric": DISPLAY_CLUT,
    "measured-like": _measured_like_clut(),
}


@pytest.fixture(params=sorted(CLUTS))
def clut(request):
    return CLUTS[request.param]


def test_recovers_the_input_a_target_was_made_from(clut):
    rgb = np.random.default_rng(0).uniform(0.0, 1.0, size=(2000, 3))

    solved, error = XYZ_to_RGB(RGB_to_XYZ(rgb, clut, per_level=True), clut, per_level=True)

    assert error.max() < 1e-6, f"worst error {error.max():.2e}"
    np.testing.assert_allclose(solved, rgb, atol=1e-6)


def test_reaches_every_corner_of_the_input_cube(clut):
    """The corners are the gamut extremes, and the hardest place to land."""
    corners = np.array(list(np.ndindex(2, 2, 2)), dtype=float)

    solved, error = XYZ_to_RGB(RGB_to_XYZ(corners, clut, per_level=True), clut, per_level=True)

    assert error.max() < 1e-6, f"worst corner error {error.max():.2e}"
    np.testing.assert_allclose(solved, corners, atol=1e-6)


def test_error_is_zero_for_anything_the_display_can_show(clut):
    rgb = np.random.default_rng(1).uniform(0.0, 1.0, size=(500, 3))

    _, error = XYZ_to_RGB(RGB_to_XYZ(rgb, clut, per_level=True), clut, per_level=True)

    assert np.all(error < 1e-6)


def test_error_is_the_distance_to_the_closest_colour_it_can_show(clut):
    """For an unreachable target, the error says how far outside the gamut it is."""
    white = RGB_to_XYZ(np.ones(3), clut, per_level=True)
    beyond = np.stack([white * factor for factor in (1.01, 1.1, 1.5, 3.0)])

    solved, error = XYZ_to_RGB(beyond, clut, per_level=True)

    achieved = RGB_to_XYZ(solved, clut, per_level=True)
    np.testing.assert_allclose(error, np.linalg.norm(achieved - beyond, axis=1), atol=1e-9)
    assert np.all(np.diff(error) > 0), "further outside should mean a larger error"


def test_a_target_just_outside_the_gamut_has_a_small_error(clut):
    """There is no sharp line: the error is a distance, and it goes to zero smoothly."""
    white = RGB_to_XYZ(np.ones(3), clut, per_level=True)

    _, just_outside = XYZ_to_RGB(white * 1.001, clut, per_level=True)
    _, far_outside = XYZ_to_RGB(white * 2.0, clut, per_level=True)

    assert just_outside < far_outside / 100


def test_unreachable_targets_stay_in_range_and_finite(clut):
    absurd = np.array([[1e6, 1e6, 1e6], [-1e3, 5.0, 5.0], [0.0, 0.0, 0.0]])

    solved, error = XYZ_to_RGB(absurd, clut, per_level=True)

    assert np.all(np.isfinite(solved)) and np.all(np.isfinite(error))
    assert solved.min() >= 0.0 and solved.max() <= 1.0


def test_accepts_a_single_triplet_and_a_batch(clut):
    one, one_error = XYZ_to_RGB(
        RGB_to_XYZ(np.array([0.3, 0.6, 0.4]), clut, per_level=True), clut, per_level=True
    )
    many, many_error = XYZ_to_RGB(
        RGB_to_XYZ(np.full((4, 3), 0.5), clut, per_level=True), clut, per_level=True
    )

    assert one.shape == (3,) and one_error.shape == ()
    assert many.shape == (4, 3) and many_error.shape == (4,)


def test_black_and_white_solve_to_the_ends_of_the_range(clut):
    solved, error = XYZ_to_RGB(
        RGB_to_XYZ(np.array([[0.0] * 3, [1.0] * 3]), clut, per_level=True), clut, per_level=True
    )

    assert error.max() < 1e-6
    np.testing.assert_allclose(solved[0], 0.0, atol=1e-6)
    np.testing.assert_allclose(solved[1], 1.0, atol=1e-6)


def test_the_inverse_is_only_as_good_as_the_fit():
    """Where the fitted curve is flat, several inputs give the same light.

    Then there is no single input to solve for, and the error says so. This is the
    reason `smooth` runs before `linearize`: a non-decreasing fit to an unsmoothed
    noisy measurement pools long stretches into one value.
    """
    rgb = np.random.default_rng(2).uniform(0.0, 1.0, size=(500, 3))

    unsmoothed = _measured_like_clut(noise=0.06, width=1)
    smoothed = _measured_like_clut(noise=0.06, width=25)

    _, rough_error = XYZ_to_RGB(
        RGB_to_XYZ(rgb, unsmoothed, per_level=True), unsmoothed, per_level=True
    )
    _, fine_error = XYZ_to_RGB(RGB_to_XYZ(rgb, smoothed, per_level=True), smoothed, per_level=True)

    assert rough_error.max() > 1.0, "expected an unsmoothed CLUT to be hard to invert"
    assert fine_error.max() < 1e-9


def test_matches_the_forward_model():
    """Whatever comes back, running it forward must give what the error claims."""
    clut = CLUTS["measured-like"]
    targets = np.random.default_rng(3).uniform(0.0, 250.0, size=(300, 3))

    solved, error = XYZ_to_RGB(targets, clut, per_level=True)

    np.testing.assert_allclose(
        error, np.linalg.norm(RGB_to_XYZ(solved, clut, per_level=True) - targets, axis=1), atol=1e-9
    )
