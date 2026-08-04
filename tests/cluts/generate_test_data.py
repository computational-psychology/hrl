#!/usr/bin/env python
"""Generate static regression fixtures for CLUT calibration tests.

The generated files mirror the LUT test-data style but for color calibration:
- measurements_8bit.csv
- measurements_duplicates.csv
- measurements_outliers.csv
- averaged_measurements_duplicates.csv
- averaged_measurements_outliers.csv
- clut_8bit.csv
- clut_10bit.csv
"""

import argparse
import sys
from pathlib import Path

import numpy as np

from hrl.cluts import average, linearize, remove_outliers
from hrl.cluts.calibrate import channel_sweeps
from tests.cluts.conftest import display_xyz

TEST_DIR = Path(__file__).parent


def _save_csv(path, array):
    np.savetxt(
        path,
        array,
        delimiter=",",
        header=(
            "R,G,B,X,Y,Z"
            if array.shape[1] == 6
            else "intensity_in,R_out,G_out,B_out,R_X,R_Y,R_Z,G_X,G_Y,G_Z,B_X,B_Y,B_Z"
        ),
        comments="",
        fmt="%.18e",
    )


def _expected_header(array):
    if array.shape[1] == 6:
        return "R,G,B,X,Y,Z"
    return "intensity_in,R_out,G_out,B_out,R_X,R_Y,R_Z,G_X,G_Y,G_Z,B_X,B_Y,B_Z"


def _assert_csv_matches(path, expected_array):
    if not path.exists():
        raise AssertionError(f"Missing fixture file: {path}")

    loaded = np.genfromtxt(path, delimiter=",", skip_header=1)
    if loaded.shape != expected_array.shape:
        raise AssertionError(
            f"Shape mismatch for {path.name}: expected {expected_array.shape}, got {loaded.shape}"
        )

    np.testing.assert_allclose(loaded, expected_array, rtol=0.0, atol=1e-12)


def _build_fixtures():
    # Base 8-bit measurement table: one noiseless sample per channel-isolated triplet
    triplets_8bit = channel_sweeps(256)
    measurements_8bit = np.column_stack([triplets_8bit, display_xyz(triplets_8bit)])

    # Repeated measurements with small noise for averaging regression
    rng = np.random.default_rng(42)
    triplets_dupes = np.repeat(channel_sweeps(256), 3, axis=0)
    measurements_duplicates = np.column_stack([triplets_dupes, display_xyz(triplets_dupes)])
    measurements_duplicates[:, 3:] += rng.normal(
        0.0, 0.002, size=measurements_duplicates[:, 3:].shape
    )
    averaged_duplicates = average(measurements_duplicates)

    # Repeated measurements with injected outliers for outlier-removal regression
    measurements_outliers = measurements_duplicates.copy()
    # Boost one sample every 5 triplets by 30% in XYZ.
    outlier_idx = np.arange(0, len(measurements_outliers), 15)
    measurements_outliers[outlier_idx, 3:] *= 1.30
    averaged_outliers = average(remove_outliers(measurements_outliers))

    # Final linearized CLUT fixtures
    clut_8bit = linearize(average(remove_outliers(measurements_8bit)), bit_depth=8)

    clut_10bit = linearize(average(remove_outliers(measurements_8bit)), bit_depth=10)

    return {
        "measurements_8bit.csv": measurements_8bit,
        "measurements_duplicates.csv": measurements_duplicates,
        "measurements_outliers.csv": measurements_outliers,
        "averaged_measurements_duplicates.csv": averaged_duplicates,
        "averaged_measurements_outliers.csv": averaged_outliers,
        "clut_8bit.csv": clut_8bit,
        "clut_10bit.csv": clut_10bit,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate or validate CLUT regression fixtures.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Do not write files; fail if generated fixtures differ from committed CSV files.",
    )
    args = parser.parse_args(argv)

    fixtures = _build_fixtures()

    if args.check:
        mismatches = []
        for filename, data in fixtures.items():
            path = TEST_DIR / filename
            try:
                _assert_csv_matches(path, data)
            except AssertionError as exc:
                mismatches.append(str(exc))

        if mismatches:
            print("CLUT fixture drift detected:", file=sys.stderr)
            for message in mismatches:
                print(f"- {message}", file=sys.stderr)
            return 1

        print("CLUT fixtures are up to date.")
        return 0

    for filename, data in fixtures.items():
        _save_csv(TEST_DIR / filename, data)

    print("CLUT fixtures regenerated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
