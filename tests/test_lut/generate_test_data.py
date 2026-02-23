#!/usr/bin/env python
"""Generate test data files for LUT processing tests.

This script creates measurement data files and their expected outputs for testing
the smooth and linearize functions.
"""

import subprocess
from pathlib import Path

import numpy as np

# Use hrl.luts to generate realistic measurement data
from hrl.luts import create_lut

TEST_DIR = Path(__file__).parent


def generate_measurement_8bit():
    """Generate measurement data with 256 points (full 8-bit range).

    Creates: measurements_8bit.csv with gamma~2.2 curve and small random noise.
    """
    print("Generating measurements_8bit.csv (256 points)...")

    # Generate 256 evenly spaced intensities
    n_points = 256
    intensities = np.linspace(0, 1, n_points)

    # Gamma ~2.2 curve with luminance range 1-101 cd/m²
    gamma = 2.2
    lum_min, lum_max = 1.0, 101.0
    luminances = lum_min + (lum_max - lum_min) * (intensities**gamma)

    # Add small random noise (~1%)
    np.random.seed(42)
    noise = np.random.normal(0, 0.01, n_points)
    luminances = luminances * (1 + noise)

    # Create duplicates at some intensities to test averaging
    # Keep original number of unique points but with slight measurement variations
    data = np.column_stack([intensities, luminances])

    # Save
    np.savetxt(
        TEST_DIR / "measurements_8bit.csv",
        data,
        header="intensity_in,luminance",
        comments="",
        fmt="%.18e",
    )
    print(f"  → {len(data)} measurement points")


def generate_measurement_16bit():
    """Generate measurement data with 65536 points (full 16-bit range).

    Creates: measurements_16bit.csv with gamma~2.2 curve and small random noise.
    """
    print("Generating measurements_16bit.csv (65536 points)...")

    # Generate 65536 evenly spaced intensities
    n_points = 65536
    intensities = np.linspace(0, 1, n_points)

    # Gamma ~2.2 curve with luminance range 1-101 cd/m²
    gamma = 2.2
    lum_min, lum_max = 1.0, 101.0
    luminances = lum_min + (lum_max - lum_min) * (intensities**gamma)

    # Add very small random noise (~0.1% for 16-bit precision)
    np.random.seed(42)
    noise = np.random.normal(0, 0.001, n_points)
    luminances = luminances * (1 + noise)

    data = np.column_stack([intensities, luminances])

    # Save
    np.savetxt(
        TEST_DIR / "measurements_16bit.csv",
        data,
        header="intensity_in,luminance",
        comments="",
        fmt="%.18e",
    )
    print(f"  → {len(data)} measurement points")


def generate_measurement_duplicates():
    """Generate measurement data with duplicates.

    Creates: measurements_duplicates.csv with 20 unique intensities, 3 measurements each.
    """
    print("Generating measurements_duplicates.csv...")

    # 20 unique intensities, each measured 3 times
    n_unique = 20
    n_repeats = 3
    intensities = np.linspace(0, 1, n_unique)

    gamma = 2.2
    lum_min, lum_max = 1.0, 101.0
    luminances = lum_min + (lum_max - lum_min) * (intensities**gamma)

    # Repeat each measurement 3 times with slight variations
    np.random.seed(42)
    all_intensities = []
    all_luminances = []

    for i, (intensity, lum) in enumerate(zip(intensities, luminances)):
        for _ in range(n_repeats):
            all_intensities.append(intensity)
            # Add small noise to each measurement (~1%)
            all_luminances.append(lum * (1 + np.random.normal(0, 0.01)))

    data = np.column_stack([all_intensities, all_luminances])

    # Save
    np.savetxt(
        TEST_DIR / "measurements_duplicates.csv",
        data,
        header="intensity_in,luminance",
        comments="",
        fmt="%.18e",
    )
    print(f"  → {len(data)} measurement points ({n_unique} unique intensities)")


def generate_measurement_outliers():
    """Generate measurement data with outliers.

    Creates: measurements_outliers.csv with 50 intensities, 3 measurements each,
    every 5th intensity has one outlier at 15% deviation.
    """
    print("Generating measurements_outliers.csv...")

    n_unique = 50
    intensities = np.linspace(0, 1, n_unique)

    gamma = 2.2
    lum_min, lum_max = 1.0, 101.0
    luminances = lum_min + (lum_max - lum_min) * (intensities**gamma)

    np.random.seed(42)
    all_intensities = []
    all_luminances = []

    for i, (intensity, lum) in enumerate(zip(intensities, luminances)):
        # Always 3 measurements per intensity
        n_meas = 3

        # Every 5th intensity will have an outlier
        has_outlier = i % 5 == 0

        for j in range(n_meas):
            all_intensities.append(intensity)

            if has_outlier and j == 0:
                # Outlier: 15% deviation (enough to trigger filter: > 0.75%)
                deviation = 0.15 if i % 2 == 0 else -0.15
                all_luminances.append(lum * (1 + deviation))
            else:
                # Normal measurement: very small deterministic noise to ensure consistency
                noise = 0.005 * (j - 1)  # -0.5%, 0%, +0.5%
                all_luminances.append(lum * (1 + noise))

    data = np.column_stack([all_intensities, all_luminances])

    # Save
    np.savetxt(
        TEST_DIR / "measurements_outliers.csv",
        data,
        header="intensity_in,luminance",
        comments="",
        fmt="%.18e",
    )
    print(f"  → {len(data)} measurement points ({n_unique} unique intensities)")


def generate_measurement_lumrange():
    """Generate measurement data with different luminance range.

    Creates: measurements_lumrange.csv with 80 intensities, gamma=2.0, 2.5-150 cd/m².
    """
    print("Generating measurements_lumrange.csv...")

    n_points = 80
    intensities = np.linspace(0, 1, n_points)

    # Different gamma and luminance range
    gamma = 2.0
    lum_min, lum_max = 2.5, 150.0
    luminances = lum_min + (lum_max - lum_min) * (intensities**gamma)

    # Add small random noise
    np.random.seed(42)
    noise = np.random.normal(0, 0.01, n_points)
    luminances = luminances * (1 + noise)

    data = np.column_stack([intensities, luminances])

    # Save
    np.savetxt(
        TEST_DIR / "measurements_lumrange.csv",
        data,
        header="intensity_in,luminance",
        comments="",
        fmt="%.18e",
    )
    print(f"  → {len(data)} measurement points")


def generate_expected_outputs():
    """Generate expected output files by running smooth and linearize."""
    print("\nGenerating expected smooth outputs...")

    # Order 2 (kernel smoothing) - tests kernel parameter
    subprocess.run(["cp", str(TEST_DIR / "measurements_8bit.csv"), "measure.csv"], check=True)
    print("  → smoothed_measurements_kernel.csv (order=2)")
    subprocess.run(["hrl-util", "lut", "smooth", "-o", "2"], check=True)
    subprocess.run(
        ["mv", "smooth.csv", str(TEST_DIR / "smoothed_measurements_kernel.csv")], check=True
    )

    # Duplicates
    subprocess.run(
        ["cp", str(TEST_DIR / "measurements_duplicates.csv"), "measure.csv"], check=True
    )
    print("  → smoothed_measurements_duplicates.csv")
    subprocess.run(["hrl-util", "lut", "smooth", "-o", "0"], check=True)
    subprocess.run(
        ["mv", "smooth.csv", str(TEST_DIR / "smoothed_measurements_duplicates.csv")], check=True
    )

    # Outliers
    subprocess.run(["cp", str(TEST_DIR / "measurements_outliers.csv"), "measure.csv"], check=True)
    print("  → smoothed_measurements_outliers.csv")
    subprocess.run(["hrl-util", "lut", "smooth", "-o", "0"], check=True)
    subprocess.run(
        ["mv", "smooth.csv", str(TEST_DIR / "smoothed_measurements_outliers.csv")], check=True
    )

    # Generate expected linearize outputs
    print("\nGenerating expected linearize outputs...")

    # Use measurements_8bit.csv as input for 8-bit LUT
    subprocess.run(["cp", str(TEST_DIR / "measurements_8bit.csv"), "smooth.csv"], check=True)
    print("  → lut_8bit.csv")
    subprocess.run(["hrl-util", "lut", "linearize", "-r", "8"], check=True)
    subprocess.run(["mv", "lut.csv", str(TEST_DIR / "lut_8bit.csv")], check=True)

    # Use measurements_16bit.csv as input for 10-bit and 16-bit LUTs
    subprocess.run(["cp", str(TEST_DIR / "measurements_16bit.csv"), "smooth.csv"], check=True)
    print("  → lut_10bit.csv")
    subprocess.run(["hrl-util", "lut", "linearize", "-r", "10"], check=True)
    subprocess.run(["mv", "lut.csv", str(TEST_DIR / "lut_10bit.csv")], check=True)

    subprocess.run(["cp", str(TEST_DIR / "measurements_16bit.csv"), "smooth.csv"], check=True)
    print("  → lut_16bit.csv")
    subprocess.run(["hrl-util", "lut", "linearize", "-r", "16"], check=True)
    subprocess.run(["mv", "lut.csv", str(TEST_DIR / "lut_16bit.csv")], check=True)

    # Lumrange test output (integration test runs smooth itself)
    subprocess.run(["cp", str(TEST_DIR / "measurements_lumrange.csv"), "measure.csv"], check=True)
    print("  → lut_lumrange.csv (via smooth order=1)")
    subprocess.run(["hrl-util", "lut", "smooth", "-o", "1"], check=True)
    subprocess.run(["hrl-util", "lut", "linearize", "-r", "8"], check=True)
    subprocess.run(["mv", "lut.csv", str(TEST_DIR / "lut_lumrange.csv")], check=True)

    # Cleanup
    subprocess.run(["rm", "-f", "measure.csv", "smooth.csv"], check=True)


if __name__ == "__main__":
    print("Generating test data files for LUT processing tests...")
    print("=" * 60)

    # Generate measurement files
    generate_measurement_8bit()
    generate_measurement_16bit()
    generate_measurement_duplicates()
    generate_measurement_outliers()
    generate_measurement_lumrange()

    # Generate expected outputs
    generate_expected_outputs()

    print("\n" + "=" * 60)
    print("Test data generation complete!")
    print("\nGenerated files:")
    print("  Measurements (raw test data):")
    print("    measurements_8bit.csv (256 pts) → lut_8bit.csv")
    print("    measurements_16bit.csv (65536 pts) → lut_10bit.csv, lut_16bit.csv")
    print("    measurements_duplicates.csv, measurements_outliers.csv, measurements_lumrange.csv")
    print("  Expected outputs for smooth tests:")
    print("    smoothed_measurements_kernel.csv (from measurements_8bit.csv, order=2)")
    print("    smoothed_measurements_duplicates.csv (from measurements_duplicates.csv)")
    print("    smoothed_measurements_outliers.csv (from measurements_outliers.csv)")
    print("  Expected outputs for linearize tests:")
    print("    lut_8bit.csv, lut_10bit.csv, lut_16bit.csv")
    print("  Expected outputs for integration tests:")
    print("    lut_lumrange.csv")
