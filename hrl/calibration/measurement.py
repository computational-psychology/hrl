import numpy as np


def combine(measurements):
    # Concatenate measurements into one big intensity to luminances map
    luminance_map = {}
    for table in measurements:
        for row in table:
            if row[0] in luminance_map:
                luminance_map[row[0]] = np.concatenate([luminance_map[row[0]], row[1:]])
            else:
                luminance_map[row[0]] = row[1:]

    return luminance_map


def remove_outliers(luminance_map):
    # Remove outliers and NaNs
    # Outliers are values that are more than 0.05 cd or more than 0.5% of their value
    # from the closest measurement at the same intensity.
    for intensity, luminance_measurements in luminance_map.items():
        luminance_measurements = luminance_measurements[~np.isnan(luminance_measurements)]

        if len(luminance_measurements) > 1:
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

        luminance_map[intensity] = luminance_measurements

    return luminance_map


def average(luminance_map):
    # Average measurements at each intensity
    for intensity, luminance_measurements in luminance_map.items():
        luminance_map[intensity] = np.mean(
            luminance_measurements[~np.isnan(luminance_measurements)]
        )
        if np.isnan(luminance_map[intensity]):
            raise RuntimeError(f"no valid measurement for {intensity:.4f}")

    table = np.array([list(luminance_map.keys()), list(luminance_map.values())]).transpose()
    table = table[table[:, 0].argsort()]
    # print(table.shape)

    return table


def smooth(luminances, order):

    kernel = [0.2, 0.2, 0.2, 0.2, 0.2]

    smoothed = luminances
    for _ in range(order):
        smoothed = np.hstack((np.ones(2) * smoothed[0], smoothed, np.ones(2) * smoothed[-1]))
        smoothed = np.convolve(smoothed, kernel, "valid")

    return smoothed


def linearize(lut, bit_depth=16):
    """Sample a linear subset of the gamma table"""
    intensities = lut[:, 0]
    luminances = lut[:, 1]

    n_steps = 2**bit_depth

    idx = 0
    idxs = []
    sample_indices = np.zeros(n_steps, dtype=bool)
    for i, smp in enumerate(np.linspace(np.min(luminances), np.max(luminances), n_steps)):
        idx = np.nonzero(luminances >= smp)[0][0]
        if not len(idxs) or (idx != idxs[-1]):
            sample_indices[i] = True
            idxs.append(idx)

    linearized_lut = np.array(
        [np.linspace(0, 1, n_steps)[sample_indices], intensities[idxs], luminances[idxs]]
    ).transpose()

    return linearized_lut
    # return lambda x: np.interp(x,np.linspace(0,1,2**args.res),itss[idxs])
