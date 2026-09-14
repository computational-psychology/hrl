"""Tests for the examples/luminance_to_intensity.py helper script.

The script is not part of the installed package, so it is loaded from its
path. Expected values come from the definition of a linearized LUT: the
luminance column increases linearly with the intensity_in column, so the
mapping between them is an affine function that can be written down exactly.
"""

import importlib.util
from pathlib import Path

import numpy as np
import pytest

SCRIPT = Path(__file__).parent.parent / "examples" / "luminance_to_intensity.py"

L_MIN = 0.5
L_MAX = 500.5


def _load_module():
    spec = importlib.util.spec_from_file_location("luminance_to_intensity", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


lti = _load_module()


@pytest.fixture
def linear_lut():
    """A LUT that is exactly linearized: luminance is affine in intensity_in.

    The intensity_out column is deliberately given a nonlinear shape,
    so that a function which reads the wrong column will fail.
    """
    intensity_in = np.linspace(0.0, 1.0, 101)
    luminance = L_MIN + (L_MAX - L_MIN) * intensity_in
    intensity_out = intensity_in ** (1 / 2.2)
    return np.column_stack([intensity_in, intensity_out, luminance])


def _expected_intensity(luminance):
    """Invert luminance = L_MIN + (L_MAX - L_MIN) * intensity."""
    return (luminance - L_MIN) / (L_MAX - L_MIN)


def test_luminance_range_reports_measured_extremes(linear_lut):
    assert lti.luminance_range(linear_lut) == (L_MIN, L_MAX)


def test_intensity_at_endpoints(linear_lut):
    assert lti.intensity_for_luminance(linear_lut, L_MIN) == pytest.approx(0.0)
    assert lti.intensity_for_luminance(linear_lut, L_MAX) == pytest.approx(1.0)


def test_intensity_at_midpoint_of_luminance_range(linear_lut):
    midpoint = (L_MIN + L_MAX) / 2
    assert lti.intensity_for_luminance(linear_lut, midpoint) == pytest.approx(0.5)


def test_intensity_matches_analytic_inverse(linear_lut):
    """On a linearized LUT the mapping is affine, so it is known exactly."""
    luminances = np.array([1.0, 50.0, 123.45, 250.0, 400.0])
    expected = _expected_intensity(luminances)

    result = lti.intensity_for_luminance(linear_lut, luminances)

    np.testing.assert_allclose(result, expected, atol=1e-12)


def test_luminance_for_intensity_matches_definition(linear_lut):
    intensities = np.array([0.0, 0.1, 0.25, 0.5, 0.9, 1.0])
    expected = L_MIN + (L_MAX - L_MIN) * intensities

    result = lti.luminance_for_intensity(linear_lut, intensities)

    np.testing.assert_allclose(result, expected, atol=1e-12)


def test_round_trip_luminance_to_intensity_and_back(linear_lut):
    luminances = np.array([0.5, 10.0, 100.0, 333.0, 500.5])

    intensities = lti.intensity_for_luminance(linear_lut, luminances)
    back = lti.luminance_for_intensity(linear_lut, intensities)

    np.testing.assert_allclose(back, luminances, atol=1e-9)


def test_out_of_range_luminances_are_clipped(linear_lut):
    """numpy.interp clamps: below the range gives the first intensity."""
    assert lti.intensity_for_luminance(linear_lut, -100.0) == pytest.approx(0.0)
    assert lti.intensity_for_luminance(linear_lut, 10_000.0) == pytest.approx(1.0)


def test_scalar_input_gives_scalar_output(linear_lut):
    result = lti.intensity_for_luminance(linear_lut, 100.0)
    assert np.ndim(result) == 0


def test_array_input_preserves_shape(linear_lut):
    luminances = np.array([[1.0, 2.0], [3.0, 4.0]])
    result = lti.intensity_for_luminance(linear_lut, luminances)
    assert result.shape == luminances.shape


def test_load_lut_reads_comma_delimited(tmp_path, linear_lut):
    filepath = tmp_path / "lut.csv"
    with filepath.open("w") as out_file:
        out_file.write("intensity_in,intensity_out,luminance\n")
        np.savetxt(out_file, linear_lut, delimiter=",")

    loaded = lti.load_lut(filepath)

    np.testing.assert_allclose(loaded, linear_lut, atol=1e-12)


def test_load_lut_falls_back_to_whitespace_delimited(tmp_path, linear_lut):
    """Older LUT files in this lab are space-delimited."""
    filepath = tmp_path / "lut_legacy.csv"
    with filepath.open("w") as out_file:
        out_file.write("IntensityIn IntensityOut Luminance\n")
        np.savetxt(out_file, linear_lut)

    loaded = lti.load_lut(filepath)

    np.testing.assert_allclose(loaded, linear_lut, atol=1e-12)


def test_load_lut_rejects_a_file_that_is_not_a_table(tmp_path):
    filepath = tmp_path / "not_a_lut.csv"
    filepath.write_text("header\n1.0\n2.0\n3.0\n")

    with pytest.raises(ValueError):
        lti.load_lut(filepath)


def test_shipped_example_lut_is_readable_and_monotonic():
    """The lut.csv committed under examples/ must load and be linearized."""
    filepath = SCRIPT.parent / "lut.csv"
    lut = lti.load_lut(filepath)

    assert lut.shape[1] == 3
    assert np.all(np.diff(lut[:, 2]) > 0)  # luminance strictly increasing
    assert np.all(np.diff(lut[:, 0]) > 0)  # intensity_in strictly increasing
