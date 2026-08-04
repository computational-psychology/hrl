"""Tests for processing colorimetric measurements (remove_outliers, average)."""

import numpy as np

from hrl.cluts import average, remove_outliers


def _base_measurements(n=16):
    intensities = np.linspace(0.0, 1.0, n)

    rows = []
    for c in range(3):
        for i in intensities:
            triplet = np.zeros(3)
            triplet[c] = i
            xyz = np.array([0.8, 1.0, 0.9]) * (i**2.0) + np.array([0.01, 0.012, 0.015])
            rows.append(np.concatenate([triplet, xyz]))

    return np.array(rows)


def test_remove_outliers_flags_obvious_outliers():
    measurements = _base_measurements(32)

    # Skip near-black rows so abs_tol is exceeded by construction.
    candidate = measurements[np.max(measurements[:, :3], axis=1) > 0.2]

    close_rows = candidate[::7].copy()
    close_rows[:, 3:] += 0.001

    outlier_rows = candidate[::7].copy()
    outlier_rows[:, 3:] *= 1.30

    stacked = np.vstack([measurements, close_rows, outlier_rows])
    result = remove_outliers(stacked)

    nan_rows = np.isnan(result[:, 3:]).all(axis=1)
    assert np.sum(nan_rows) >= len(outlier_rows) - 2


def test_remove_outliers_keeps_close_measurements():
    measurements = _base_measurements(32)

    close_rows = measurements[::5].copy()
    close_rows[:, 3:] += 0.001

    stacked = np.vstack([measurements, close_rows])
    result = remove_outliers(stacked)

    assert not np.isnan(result[:, 3:]).any()


def test_average_reduces_duplicates_to_unique_triplets():
    measurements = _base_measurements(24)

    duplicate_1 = measurements.copy()
    duplicate_1[:, 3:] += 0.01
    duplicate_2 = measurements.copy()
    duplicate_2[:, 3:] -= 0.01

    stacked = np.vstack([measurements, duplicate_1, duplicate_2])
    result = average(stacked)

    expected = average(measurements)

    assert result.shape[0] == expected.shape[0]
    np.testing.assert_allclose(result[:, :3], expected[:, :3], atol=1e-12)
    np.testing.assert_allclose(result[:, 3:], expected[:, 3:], atol=1e-12)


def test_average_ignores_nan_rows():
    measurements = _base_measurements(24)

    with_nan = measurements.copy()
    with_nan[::9, 3:] = np.nan

    stacked = np.vstack([measurements, with_nan])
    result = average(stacked)

    expected = average(measurements)

    np.testing.assert_allclose(result[:, :3], expected[:, :3], atol=1e-12)
    np.testing.assert_allclose(result[:, 3:], expected[:, 3:], atol=1e-12)
