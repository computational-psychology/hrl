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

from hrl.cluts import (
    _setup_rgb_triplets,
    average,
    linearize,
    remove_outliers,
)

TEST_DIR = Path(__file__).parent

GAMMA_PHYS = np.array([2.0, 2.2, 1.8])
COLOR_MATRIX = np.array(
    [
        [0.80, 0.05, 0.02],
        [0.03, 0.90, 0.04],
        [0.02, 0.05, 0.88],
    ]
)
DARK_XYZ = np.array([0.01, 0.012, 0.015])


def _xyz_from_triplets(triplets):
    linear_rgb = triplets**GAMMA_PHYS
    return linear_rgb @ COLOR_MATRIX.T + DARK_XYZ


def _save_csv(path, array):
    np.savetxt(
        path,
        array,
        delimiter=",",
        header="R,G,B,X,Y,Z"
        if array.shape[1] == 6
        else "intensity_in,R_out,G_out,B_out,X_R,X_G,X_B,Y_R,Y_G,Y_B,Z_R,Z_G,Z_B",
        comments="",
        fmt="%.18e",
    )


def _expected_header(array):
    if array.shape[1] == 6:
        return "R,G,B,X,Y,Z"
    return "intensity_in,R_out,G_out,B_out,X_R,X_G,X_B,Y_R,Y_G,Y_B,Z_R,Z_G,Z_B"


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
    triplets_8bit = _setup_rgb_triplets(n_steps=256, n_samples=1)
    measurements_8bit = np.column_stack([triplets_8bit, _xyz_from_triplets(triplets_8bit)])

    # Repeated measurements with small noise for averaging regression
    rng = np.random.default_rng(42)
    triplets_dupes = _setup_rgb_triplets(n_steps=256, n_samples=3)
    measurements_duplicates = np.column_stack([triplets_dupes, _xyz_from_triplets(triplets_dupes)])
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
