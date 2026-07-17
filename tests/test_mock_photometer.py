"""Test that the MockPhotometer class behaves as expected."""

import numpy as np
import pytest

from hrl.photometer.photometer import MockPhotometer


def test_identity_lut(identity_lut):
    # identity_lut: luminance == intensity_in (k=1, dark=0, gamma=1)
    phot = MockPhotometer(luminance_mapping=identity_lut)

    phot.current_intensity = 0.5
    assert phot.readLuminance() == 0.5


def test_lut_array(nonlinear_lut):
    # 3-column LUT: MockPhotometer should use luminance column
    phot = MockPhotometer(luminance_mapping=nonlinear_lut)

    phot.current_intensity = 0.0
    assert phot.readLuminance() == nonlinear_lut[0, -1]

    phot.current_intensity = 1.0
    assert phot.readLuminance() == nonlinear_lut[-1, -1]


def test_lut_callable():
    phot = MockPhotometer(luminance_mapping=lambda x: x * 200.0)
    phot.current_intensity = 0.25
    assert phot.readLuminance() == 50.0


## NOISY "MEASUREMENTS"
def test_noiseless_is_deterministic(linear_lut):
    phot = MockPhotometer(luminance_mapping=linear_lut, noise=0.0)
    phot.current_intensity = 0.3
    assert phot.readLuminance() == phot.readLuminance()


def test_noise_adds_variance(linear_lut):
    phot = MockPhotometer(luminance_mapping=linear_lut, noise=1.0, rng=0)
    phot.current_intensity = 0.5
    readings = [phot.readLuminance(n=1) for _ in range(20)]
    assert np.std(readings) > 0.0


def test_noise_mean_close_to_true(linear_lut):
    # linear_lut: luminance = 150 * intensity + 2, so 0.5 -> 77.0
    phot = MockPhotometer(luminance_mapping=linear_lut, noise=0.5, rng=42)
    phot.current_intensity = 0.5
    readings = [phot.readLuminance(n=10) for _ in range(50)]
    assert np.mean(readings) == pytest.approx(77.0, abs=1.0)
