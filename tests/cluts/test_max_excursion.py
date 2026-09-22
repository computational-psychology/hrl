"""Tests for `max_excursion`, and for the assumption it rests on."""

import numpy as np
import pytest

from hrl.cluts import RGB_to_XYZ, XYZ_to_RGB, max_excursion
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
    triplets = np.repeat(channel_sweeps(256), 5, axis=0)
    xyz = 100.0 * display_xyz(triplets)
    xyz = xyz * (1.0 + np.random.default_rng(seed).normal(0.0, noise, size=xyz.shape))
    measurements = np.column_stack([triplets, xyz])
    return linearize(make_monotonic(smooth(average(remove_outliers(measurements)))))


CLUTS = {
    "parametric": DISPLAY_CLUT,
    "measured-like": _measured_like_clut(),
}


@pytest.fixture(params=sorted(CLUTS))
def clut(request):
    return CLUTS[request.param]


def test_reachable_along_a_ray_is_one_unbroken_stretch():
    """What a display can show along a straight line is one stretch, not several.

    The inputs it takes form a solid box, so this is true of the display. Whether it is
    true of what the solver *reports* is another matter, and that is what this measures.
    On a CLUT whose channel curves are smooth it holds exactly.
    """
    clut = CLUTS["parametric"]
    mid_grey = RGB_to_XYZ(np.full(3, 0.5), clut, per_level=True)
    rng = np.random.default_rng(0)

    for _ in range(20):
        direction = rng.normal(size=3)
        direction /= np.linalg.norm(direction)
        scales = np.linspace(-400.0, 400.0, 801)
        _, error = XYZ_to_RGB(mid_grey + scales[:, None] * direction, clut, per_level=True)
        inside = error <= 1e-6

        assert inside.any()
        edges = np.flatnonzero(np.diff(inside.astype(int)) != 0)
        assert len(edges) <= 2, f"reported as {len(edges) + 1} pieces along {direction}"


def test_an_isolated_solve_failure_does_not_shorten_the_answer():
    """Why the furthest hit is taken rather than the nearest miss.

    On a CLUT fitted from noisy measurements the solve occasionally settles a little
    short well inside the gamut -- a miss of order 1e-2 XYZ, which looks the same as
    being out of gamut. Halving the interval would stop at the first of those and
    report an edge far short of the real one.
    """
    clut = _measured_like_clut(noise=0.02, width=9)
    mid_grey = RGB_to_XYZ(np.full(3, 0.5), clut, per_level=True)
    direction = RGB_to_XYZ(np.array([1.0, 1.0, 0.0]), clut, per_level=True) - mid_grey

    scale = max_excursion(mid_grey, direction, clut, tol=1e-6, per_level=True)

    # Whatever it returns must genuinely be reachable, and going further must not be
    _, at_edge = XYZ_to_RGB(mid_grey + scale * direction, clut, per_level=True)
    assert at_edge <= 1e-6
    beyond = np.linspace(1.02, 2.0, 40)
    _, past = XYZ_to_RGB(mid_grey + (scale * beyond)[:, None] * direction, clut, per_level=True)
    assert np.all(past > 1e-6), "something past the reported edge was reachable"


def test_from_black_towards_white_reaches_white(clut):
    black = RGB_to_XYZ(np.zeros(3), clut, per_level=True)
    white = RGB_to_XYZ(np.ones(3), clut, per_level=True)

    scale = max_excursion(black, white - black, clut, per_level=True)

    # Never an overestimate, and within the scan's final step of the true edge
    assert scale <= 1.0
    assert scale == pytest.approx(1.0, abs=1e-3)


def test_stops_at_the_edge(clut):
    """Just inside is reachable, just outside is not."""
    mid_grey = RGB_to_XYZ(np.full(3, 0.5), clut, per_level=True)
    direction = RGB_to_XYZ(np.array([1.0, 0.0, 0.0]), clut, per_level=True) - mid_grey

    scale = max_excursion(mid_grey, direction, clut, per_level=True)

    _, at_edge = XYZ_to_RGB(mid_grey + scale * direction, clut, per_level=True)
    _, outside = XYZ_to_RGB(mid_grey + 1.05 * scale * direction, clut, per_level=True)
    assert at_edge <= 1e-6, "what it returned is not reachable"
    assert outside > 1e-6, "5% further is still reachable, so the edge is wrong"


def test_a_unit_direction_gives_a_distance_in_XYZ(clut):
    mid_grey = RGB_to_XYZ(np.full(3, 0.5), clut, per_level=True)
    direction = np.array([1.0, 0.0, 0.0])

    scale = max_excursion(mid_grey, direction, clut, per_level=True)

    achieved = XYZ_to_RGB(mid_grey + scale * direction, clut, per_level=True)
    assert np.linalg.norm((mid_grey + scale * direction) - mid_grey) == pytest.approx(scale)
    assert achieved[1] <= 1e-6


def test_the_two_signs_are_measured_separately(clut):
    """A background off-centre in some direction has more room one way than the other."""
    dim = RGB_to_XYZ(np.full(3, 0.25), clut, per_level=True)
    direction = RGB_to_XYZ(np.ones(3), clut, per_level=True) - RGB_to_XYZ(
        np.zeros(3), clut, per_level=True
    )
    direction /= np.linalg.norm(direction)

    up = max_excursion(dim, direction, clut, per_level=True)
    down = max_excursion(dim, -direction, clut, per_level=True)

    assert up > down, "a dim background should have more room upward than downward"


def test_an_unreachable_background_gives_zero(clut):
    far_outside = RGB_to_XYZ(np.ones(3), clut, per_level=True) * 10.0

    assert max_excursion(far_outside, np.array([1.0, 0.0, 0.0]), clut, per_level=True) == 0.0


def test_a_zero_direction_is_not_a_trap():
    clut = CLUTS["parametric"]
    mid_grey = RGB_to_XYZ(np.full(3, 0.5), clut, per_level=True)

    assert max_excursion(mid_grey, np.zeros(3), clut, limit=1e3, per_level=True) == 1e3
