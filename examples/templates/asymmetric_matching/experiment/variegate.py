import random

import numpy as np

INTENSITY_VALUES = np.array([5, 10, 17, 27, 42, 57, 75, 96, 118, 137, 152, 178, 202])


def position_constraint(random_array):
    """
    constraint 2: not 2 identical reflectances next to each other
    """
    n_rep = 0
    cnt = 1
    while cnt > 0:
        cnt = 0
        for j in np.arange(len(random_array)):
            ## check identity of adjacent reflectances for all but last and first
            if j < (len(random_array) - 1):
                if random_array[j] == random_array[j + 1]:
                    cnt = cnt + 1
            ## check identity of adjacent reflectances for last and first
            elif j == (len(random_array) - 1):
                if random_array[j] == random_array[0]:
                    cnt = cnt + 1

            # print 'idx %d, count %d' %(j, cnt)
        if cnt > 0:
            random.shuffle(random_array)
            n_rep = n_rep + 1
        else:
            break
    print(n_rep)
    return random_array


def position_constraint2(ext_surround, dir_surround):
    """
    constraint 2: not 2 identical reflectances next to each other
    """
    a = np.array((1, 2, 3, 5, 6, 7, 9, 10, 11, 13, 14, 15))
    b = np.array((0, 1, 2, 2, 3, 4, 4, 5, 6, 6, 7, 0))
    n_rep = 0
    cnt = 1
    while cnt > 0:
        cnt = 0
        cnt2 = 0
        for j in np.arange(len(ext_surround)):
            ## check identity of adjacent reflectances for all but last and first
            if j < (len(ext_surround) - 1):
                if ext_surround[j] == ext_surround[j + 1]:
                    cnt = cnt + 1
            ## check identity of adjacent reflectances for last and first
            elif j == (len(ext_surround) - 1):
                if ext_surround[j] == ext_surround[0]:
                    cnt = cnt + 1
            if j in a:
                if ext_surround[a[cnt2]] == dir_surround[b[cnt2]]:
                    cnt = cnt + 1

                cnt2 = cnt2 + 1

        # print cnt
        # print 'idx %d, count %d' %(j, cnt)
        if cnt > 0:
            random.shuffle(ext_surround)
            n_rep = n_rep + 1
        else:
            print("yes")
            break
    # print n_rep

    return ext_surround


def check_match_surrounds(surround_values):
    ext_surround = np.concatenate(
        (
            surround_values[0,],
            surround_values[1:4, 4],
            surround_values[4, range(4, -1, -1)],
            surround_values[range(3, 0, -1), 0],
        )
    )
    dir_surround = np.concatenate(
        (
            surround_values[1, 1:4],
            surround_values[2:4, 3],
            surround_values[3, range(2, 0, -1)],
            surround_values[range(2, 1, -1), 1],
        )
    )

    dir_surround = position_constraint(dir_surround)
    ext_surround = position_constraint2(ext_surround, dir_surround)

    surround_values[0,] = ext_surround[0:5]
    surround_values[1:4, 4] = ext_surround[5:8]
    surround_values[4, range(4, -1, -1)] = ext_surround[8:13]
    surround_values[range(3, 0, -1), 0] = ext_surround[13:16]

    surround_values[1, 1:4] = dir_surround[0:3]
    surround_values[2:4, 3] = dir_surround[3:5]
    surround_values[3, range(2, 0, -1)] = dir_surround[5:7]
    surround_values[range(2, 1, -1), 1] = dir_surround[7]

    return surround_values


def generate_variegated_array(values=np.array([]), board_shape=(5, 5)):
    """
    return a side_length x side_length numpy array consisting of nr_int different values between min_in and max_int that are randomly arranged
    :input:
    --------
    values      - array of intensities from which to sample
    side_length - default=10

    :output:
    ---------
    numpy array
    """

    # Generate random array of indices
    index = np.random.randint(0, len(values), board_shape[0] * board_shape[1])

    # Map indices to coordinates (e.g., d4)
    a = map(chr, range(97, 97 + board_shape[1]))
    coordinates = {}
    cnt = 0
    for letters in a:
        for numbers in np.arange(1, 1 + board_shape[0]):
            coordinates[letters + str(numbers)] = index[cnt]
            cnt = cnt + 1

    # Extract direct surround indices
    key_direct_surround = ["b2", "c2", "d2", "d3", "d4", "c4", "b4", "b3"]
    direct_surround = []
    for key in key_direct_surround:
        direct_surround.append(coordinates[key])

    # Check that no two identical gray values are next to each other
    direct_surround = position_constraint(np.array(direct_surround))
    for idx, key in enumerate(key_direct_surround):
        coordinates[key] = direct_surround[idx]

    # Lookup intensities from indices at coordinates
    surround_intensities = np.zeros(shape=board_shape)
    for col, letters in enumerate(map(chr, range(97, 97 + board_shape[1]))):
        for row, numbers in enumerate(np.arange(1, 1 + board_shape[0])):
            surround_intensities[row, col] = values[coordinates[letters + str(numbers)]]

    # Sub-dict for immediate surround only
    direct_surround_dict = {key: coordinates[key] for key in key_direct_surround}

    return surround_intensities, direct_surround_dict


def generate_variegated_array2(intensity_values=INTENSITY_VALUES, board_shape=(5, 5)):
    """
    Also checks that the mean of the overall array,
    as well as the mean of the immediate surround,
    is (approx.) equal to the mean of the given intensity values
    """

    valid = False
    while not valid:
        surround_values, direct_surround = generate_variegated_array(intensity_values, board_shape)
        surround_values = check_match_surrounds(surround_values)

        # the center check should not add to the mean, therefore it is replaced by the mean
        adj_surr = np.array(
            (
                surround_values[1, 1],
                surround_values[1, 2],
                surround_values[1, 3],
                surround_values[2, 1],
                surround_values[2, 3],
                surround_values[3, 1],
                surround_values[3, 2],
                surround_values[3, 3],
            )
        )
        surround_values[2, 2] = round(np.mean(intensity_values))
        match_mean = round(np.mean(surround_values))
        surround_mean = round(np.mean(adj_surr))
        if match_mean == round(np.mean(intensity_values)) and surround_mean == round(
            np.mean(intensity_values)
        ):
            valid = True

    return surround_values
