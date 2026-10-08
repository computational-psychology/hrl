"""Tests for hrl.cluts.measure using MockColorimeter."""

import numpy as np
import pytest

from hrl.cluts.calibrate import measure, read_measurements
from hrl.cluts.triplets import channel_sweeps
from tests.cluts.conftest import display_xyz, mock_draw


@pytest.mark.parametrize("n_steps,n_samples", [(16, 1), (32, 2)])
def test_measure_returns_expected_xyz(n_steps, n_samples, mock_hrl):
    triplets = np.repeat(channel_sweeps(n_steps), n_samples, axis=0)
    ihrl = mock_hrl(noise=0.0)

    measurements, _ = measure(ihrl, triplets=triplets, stim_draw_func=mock_draw)

    assert measurements.shape == (len(triplets), 6)
    np.testing.assert_array_equal(measurements[:, :3], triplets)

    expected_xyz = display_xyz(triplets)
    np.testing.assert_allclose(measurements[:, 3:], expected_xyz, atol=1e-12)


def test_measure_csv_output(tmp_path, mock_hrl):
    triplets = np.repeat(channel_sweeps(16), 2, axis=0)
    out_file = tmp_path / "measurements.csv"
    ihrl = mock_hrl(noise=0.0)

    measure(ihrl, triplets=triplets, stim_draw_func=mock_draw, out_file=out_file)

    measured_csv = np.genfromtxt(out_file, delimiter=",", skip_header=1)
    assert measured_csv.shape == (len(triplets), 6)
    np.testing.assert_allclose(measured_csv[:, :3], triplets, atol=1e-12)


def test_measure_repeats_each_triplet_n_samples_times(mock_hrl):
    triplets = channel_sweeps(4)

    measurements, _ = measure(mock_hrl(), triplets=triplets, stim_draw_func=mock_draw, n_samples=3)

    np.testing.assert_array_equal(measurements[:, :3], np.repeat(triplets, 3, axis=0))


@pytest.mark.parametrize("order", ["shuffle", "reverse"])
def test_measure_orders_the_repeated_triplets(order, mock_hrl):
    triplets = channel_sweeps(4)
    np.random.seed(0)

    measurements, _ = measure(
        mock_hrl(), triplets=triplets, stim_draw_func=mock_draw, n_samples=2, **{order: True}
    )

    given = np.repeat(triplets, 2, axis=0)
    assert not np.array_equal(measurements[:, :3], given)
    if order == "reverse":
        np.testing.assert_array_equal(measurements[:, :3], given[::-1])
    # every triplet still measured twice, and each reading belongs to its own triplet
    np.testing.assert_array_equal(np.sort(measurements[:, :3], axis=0), np.sort(given, axis=0))
    expected = display_xyz(measurements[:, :3])
    np.testing.assert_allclose(measurements[:, 3:], expected, atol=1e-12)


def test_measure_writes_labels_and_reads_them_back(tmp_path, mock_hrl):
    triplets = channel_sweeps(3)
    labels = ["red"] * 3 + ["green"] * 3 + ["blue"] * 3
    out_file = tmp_path / "measurements.csv"

    measurements, measured_labels = measure(
        mock_hrl(),
        triplets,
        labels=labels,
        stim_draw_func=mock_draw,
        out_file=out_file,
        n_samples=2,
    )

    assert out_file.read_text().splitlines()[0] == "R,G,B,X,Y,Z,label"
    read, read_labels = read_measurements(out_file)
    np.testing.assert_allclose(read, measurements, rtol=1e-15)
    np.testing.assert_array_equal(read_labels, np.repeat(labels, 2))
    np.testing.assert_array_equal(measured_labels, read_labels)


def test_labels_follow_their_triplets_when_shuffled(mock_hrl):
    triplets = channel_sweeps(4)
    labels = [f"{t[0]:.2f} {t[1]:.2f} {t[2]:.2f}" for t in triplets]
    np.random.seed(1)

    measurements, measured_labels = measure(
        mock_hrl(), triplets, labels=labels, stim_draw_func=mock_draw, shuffle=True
    )

    for row, label in zip(measurements, measured_labels):
        assert label == f"{row[0]:.2f} {row[1]:.2f} {row[2]:.2f}"


def test_reads_measurements_without_labels(tmp_path, mock_hrl):
    out_file = tmp_path / "measurements.csv"
    measurements, labels = measure(
        mock_hrl(), channel_sweeps(3), stim_draw_func=mock_draw, out_file=out_file
    )

    read, read_labels = read_measurements(out_file)

    np.testing.assert_allclose(read, measurements, rtol=1e-15)
    assert (read_labels == "").all() and (labels == "").all()
