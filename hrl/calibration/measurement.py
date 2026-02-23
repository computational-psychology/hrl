import numpy as np


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
