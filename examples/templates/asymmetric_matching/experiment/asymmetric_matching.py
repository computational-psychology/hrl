import copy
import random
import warnings
from pathlib import Path

import numpy as np
import stimupy
from PIL import Image
from variegate import generate_variegated_array

INTENSITY_VALUES = np.array([5, 10, 17, 27, 42, 57, 75, 96, 118, 137, 152, 178, 202])
# INTENSITY_VALUES = np.array([5, 10, 17, 27, 41, 57, 74, 92, 124, 150, 176, 200])


def matching_field(
    variegated_array,
    ppd,
    field_size,
    field_intensity=0.5,
    check_visual_size=(1, 1),
    field_position=None,
):
    """Produce matching field stimulus: patch on variegated checkerboard

    Parameters
    ----------
    variegated_array : numpy.ndarray
        array of intensity values to use for checkerboard, one per check
    ppd : Sequence[Number, Number], Number, or None (default)
        pixels per degree (vertical, horizontal)
    field_size : Sequence[Number, Number], Number, or None (default)
        visual size of matching patch (height, width) in degrees visual angle
    field_intensity : Number
        intensity value of matching patch, by default .5
    check_visual_size : Sequence[Number, Number], Number, or None (default)
        visual size of a single check (height, width) in degrees visual angle, by default (1, 1)
    field_position : Number, Sequence[Number, Number], or None (default)
        position of the patch (relative to checkerboard), in degrees visual angle.
        If None, patch will be placed in center of image.

    Returns
    -------
    dict[str: Any]
        dict with the stimulus (key: "img"),
        mask with integer index for the shape (key: "field_mask"),
        and additional keys containing stimulus parameters
    """
    board_shape = variegated_array.shape

    # Generate checkerboard
    checkerboard = stimupy.checkerboards.checkerboard(
        board_shape=board_shape, check_visual_size=check_visual_size, ppd=ppd
    )

    # Apply variegation
    checkerboard["img"] = stimupy.components.draw_regions(
        checkerboard["checker_mask"], intensities=variegated_array.flatten() / 255.0
    )

    # Overlay matching field
    field = stimupy.components.shapes.rectangle(
        visual_size=checkerboard["visual_size"],
        ppd=ppd,
        rectangle_size=field_size,
        intensity_rectangle=field_intensity,
        rectangle_position=field_position,
    )
    combined = copy.deepcopy(checkerboard)
    combined["field_mask"] = field["rectangle_mask"]
    combined["img"] = np.where(combined["field_mask"], field["img"], checkerboard["img"])
    combined["variegated_array"] = copy.deepcopy(variegated_array)

    return combined


def perturb_array(variegated_array, seed=0):
    """Randomly flip/rotate a variegated array

    "Randomizes" a variegated array, keeping the variegation intact.

    Parameters
    ----------
    variegated_array : numpy.ndarray
        array to perturb
    seed : int, optional
        seed for the random generator, see `random.seed`, by default 0

    Returns
    -------
    numpy.ndarray
        perturbed copy of input array
    """
    random.seed(seed)

    perturbed_array = variegated_array.copy()

    # Flip
    if random.choice((True, False)):
        perturbed_array = np.fliplr(perturbed_array)
    if random.choice((True, False)):
        perturbed_array = np.flipud(perturbed_array)

    # Rotate
    perturbed_array = np.rot90(perturbed_array, k=random.choice((1, 2, 3)))

    return perturbed_array


### ---------------------------------------------------------------- ###
##                          UNUSED FUNCTIONS                         ##
### -------------------------------------------------------------- ###
def gen_matching_fields_range(
    variegated_array,
    ppd,
    field_size,
    check_visual_size=(1, 1),
    intensity_values=np.linspace(0, 1, 256),
    field_position=None,
):
    """Generate matching field stimuli for a range of intensity values

    Parameters
    ----------
    variegated_array : numpy.ndarray
        array of intensity values to use for checkerboard, one per check
    ppd : Sequence[Number, Number], Number, or None
        pixels per degree (vertical, horizontal)
    field_size : Sequence[Number, Number], Number, or None
        visual size of matching patch (height, width) in degrees visual angle
    check_visual_size : Sequence[Number, Number], Number, or None (default)
        visual size of a single check (height, width) in degrees visual angle, by default (1, 1)
    intensity_values : Sequence[float]
        intensity values for matching patch to generate, by default 256 linear spaced values [0, 1]
    field_position : Number, Sequence[Number, Number], or None (default)
        position of the patch (relative to checkerboard), in degrees visual angle.
        If None, patch will be placed in center of image.

    Returns
    -------
    dict[float: dict]
        dict mapping each intensity value to a matching stimulus with that field intensity

    See also
    --------
        export_matching_fields
    """
    warnings.warn(
        "This function has been deprecated, and should no longer be used. [2023]",
        DeprecationWarning,
    )
    # Base matching field
    field = matching_field(
        variegated_array=variegated_array,
        ppd=ppd,
        field_size=field_size,
        field_intensity=0,
        field_position=field_position,
        check_visual_size=check_visual_size,
    )

    # Generate matching fields for range of intensities of center patch
    matches = {}
    for intensity in intensity_values:
        this_field = copy.deepcopy(field)
        this_field["img"] = np.where(field["field_mask"], intensity, field["img"])
        matches[intensity] = this_field

    return matches


def matching_fields_to_images(filedir, matching_fields):
    """Save matching field stimuli to `.bmp` files

    Files will be named `"match_<intensity>.bmp"`,
    where `<intensity>` is formatted with 3 post-decimal digits, e.g., `.003`

    Parameters
    ----------
    filedir : Path or str
        (full) Path to directory to save `.bmp` files in
    matching_fields : dict[float: dict]
        dict mapping intensity value to a matching stimulus with that field intensity

    See also
    --------
        gen_matching_fields_range
    """
    warnings.warn(
        "This function has been deprecated, and should no longer be used. [2023]",
        DeprecationWarning,
    )
    # Check that output dir exists
    if not Path(filedir).exists():
        Path(filedir).mkdir(parents=True, exist_ok=True)

    # Export
    for intensity, matching_field in matching_fields.items():
        filename = f"match_{intensity:.3f}.bmp"
        stimupy.utils.array_to_image(matching_field["img"], Path(filedir) / filename, norm=True)


def direct_surround_from_image(filename):
    """Read out surround intensity values from matching stimulus image file

    Legacy function for matches which were not saved upon generation.
    Assumes a (5, 5) checkerboard, with ppd=30 (?)

    Parameters
    ----------
    filename : Path or str
        (full) Path to image-file to read surround checks from

    Returns
    -------
    dict[str: float]
        dict mapping "coordinate" (e.g., `"c2"`) to intensity at that check
    """
    warnings.warn(
        "This function has been deprecated, and should no longer be used. [2023]",
        DeprecationWarning,
    )
    surround_pos = {
        "b2": (30, 30),
        "c2": (30, 60),
        "d2": (30, 90),
        "d3": (60, 90),
        "d4": (90, 90),
        "c4": (90, 60),
        "b4": (90, 30),
        "b3": (60, 30),
    }
    curr_stim = np.array(Image.open(filename).convert("L"))
    direct_surround_dict = {}
    for key, pos in surround_pos.iteritems():
        direct_surround_dict[key] = curr_stim[pos[0], pos[1]]
    return direct_surround_dict


if __name__ == "__main__":
    warnings.warn(
        "Running this module as a script is deprecated, and should not be done [2023]",
        DeprecationWarning,
    )
    board_shape = (5, 5)
    ppd = 24
    field_size = 50 / ppd

    with Path("stimuli/match/trials_matchsurr.txt").open("w") as file:
        file.write("b2\tc2\td2\td3\td4\tc4\tb4\tb3\n")

        for trl_nr in np.arange(240):
            # Generate variegated array
            surround_values, direct_surround_dict = generate_variegated_array(
                INTENSITY_VALUES, board_shape
            )

            # Generate all possible matching intensities
            matching_fields = gen_matching_fields_range(
                intensity_values=np.linspace(0, 1, 256),
                variegated_array=surround_values,
                field_size=field_size,
                ppd=24,
                field_position=None,
            )

            # Export matching fields
            filedir = f"stimuli/match/trl_{trl_nr:03d}"
            matching_fields_to_images(
                filedir=filedir,
                matching_fields=matching_fields,
            )

            # Record direct surround
            file.write(
                "%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n"
                % (
                    direct_surround_dict["b2"],
                    direct_surround_dict["c2"],
                    direct_surround_dict["d2"],
                    direct_surround_dict["d3"],
                    direct_surround_dict["d4"],
                    direct_surround_dict["c4"],
                    direct_surround_dict["b4"],
                    direct_surround_dict["b3"],
                )
            )
