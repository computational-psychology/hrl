import argparse

import numpy as np

parser = argparse.ArgumentParser(
    prog="hrl-util lut smooth",
    description="""
    This script applies a kernel smoothing algorithm to the data contained in
    the file 'measure.csv' and generates 'smooth.csv' as a result.

    The first part of this script gathers the given data into an array, clear
    out useless rows, and average points at the same intensity. The second part
    uses a simple smoothing kernel to fit the gamma function.

    A critical part of applying this function is to make sure that the data set
    has been evenly sampled across the intensity range, as internally the
    algorithm has no idea how far apart in intensity each sample is, and
    implicitly assumes each step size to be the same.

    Right now the kernel can be directly changed but it looks like this:
    [0.2,0.2,0.2,0.2,0.2]. Use the other parameters to experiment with
    different smoothing parameters.
    """,
)

parser.add_argument(
    "-o",
    dest="ordr",
    default=0,
    type=int,
    help="The number of times (order) to smooth the data. Default: 0 (no smoothing, just averaging",
)


def smooth(args):
    parsed_args = parser.parse_args(args)

    # Load measurement data
    files = ["measure.csv"]
    measurements = [np.genfromtxt(fl, skip_header=1, delimiter=",") for fl in files]

    # Concatenate measurements into one big intensity to luminances map
    luminance_map = {}
    for table in measurements:
        for row in table:
            if row[0] in luminance_map:
                luminance_map[row[0]] = np.concatenate([luminance_map[row[0]], row[1:]])
            else:
                luminance_map[row[0]] = row[1:]

    # Average measurements at each intensity, removing NaNs and outliers
    for intensity_value, luminance_measurements in luminance_map.items():
        luminance_measurements = luminance_measurements[~np.isnan(luminance_measurements)]

        # Only perform outlier detection if there are multiple measurements
        if len(luminance_measurements) > 1:
            # set outliers to NaN. Outliers are values that are more than 0.05 cd
            # or more than 0.5% of their value from the closest measurement at the
            # same intensity.
            min_diff = np.empty_like(luminance_measurements)
            for i in range(len(luminance_measurements)):
                idx = np.ones(len(luminance_measurements), dtype=bool)
                idx[i] = False
                min_diff[i] = np.min(
                    np.abs(luminance_measurements[idx] - luminance_measurements[i])
                )
            luminance_measurements[
                (min_diff > 0.075) & (min_diff / luminance_measurements > 0.0075)
            ] = np.nan

        luminance_map[intensity_value] = np.mean(
            luminance_measurements[~np.isnan(luminance_measurements)]
        )

        if np.isnan(luminance_map[intensity_value]):
            raise RuntimeError(f"no valid measurement for {intensity_value:.4f}")

    table = np.array([list(luminance_map.keys()), list(luminance_map.values())]).transpose()
    table = table[table[:, 0].argsort()]
    print(table.shape)

    # Smooth LUT
    kernel = [0.2, 0.2, 0.2, 0.2, 0.2]
    smoothed = table[:, 1]
    for i in range(parsed_args.ordr):
        smoothed = np.hstack((np.ones(2) * smoothed[0], smoothed, np.ones(2) * smoothed[-1]))
        smoothed = np.convolve(smoothed, kernel, "valid")

    # Save smoothed LUT to file
    print("Saving to File...")
    out_filename = "smooth.csv"
    table[:, 1] = smoothed
    out_file = open(out_filename, "w")
    out_file.write("intensity_in,luminance\n")
    np.savetxt(out_file, table, delimiter=",")
    out_file.close()
