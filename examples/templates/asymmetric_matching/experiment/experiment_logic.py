import random
import time

import adjustment
import data_management
import stimuli
from asymmetric_matching import matching_field, perturb_array

# big and small steps during adjustment
STEP_SIZES = (0.02, 0.002)


def run_trial(ihrl, context, r, trial):
    # function written by Torsten and edited by Christiane, reused by GA

    # use these variable values to define test stimulus (name corresponds to design matrix and name of saved image)
    stim_name = f"../stimuli/{data_management.participant}/{trial}_{context}_{r:.2f}"

    # load stimlus image and convert from png to numpy array
    stimulus_image = stimuli.image_to_array(stim_name)

    # texture creation in buffer : stimulus
    checkerboard_stimulus = ihrl.graphics.newTexture(stimulus_image)

    # starting intensity of matching field: random between 0 and 1
    match_intensity_start = random.random()

    # create matching field (variegated checkerboard)
    variegated_array = perturb_array(stimuli.VARIEGATED_ARRAY, seed=trial)

    matching_field_stim = matching_field(
        variegated_array=variegated_array,
        ppd=stimuli.PPD,
        field_size=(1, 1),
        field_intensity=match_intensity_start,
        check_visual_size=(0.5, 0.5),
    )

    # Show stimulus (and matching field)
    t1 = time.time()
    stimuli.show_stimulus(
        ihrl,
        stimulus_texture=checkerboard_stimulus,
        matching_field_stim=matching_field_stim,
        match_intensity=match_intensity_start,
    )

    # adjust the matching field intensity
    match_intensity = adjust_loop(
        ihrl,
        stimulus_texture=checkerboard_stimulus,
        matching_field_stim=matching_field_stim,
        match_intensity=match_intensity_start,
    )

    # Record response time
    t2 = time.time()
    resptime = t2 - t1

    # Save variegated array
    save_variegated(variegated_array)

    # clean checkerboard texture
    checkerboard_stimulus.delete()

    return {
        "match_intensity": match_intensity,
        "match_intensity_start": match_intensity_start,
        "stim_name": stim_name,
        "resptime": resptime,
    }


def adjust_loop(ihrl, match_intensity, stimulus_texture, matching_field_stim):
    accept = False
    while not accept:
        match_intensity, accept = adjustment.adjust(
            ihrl=ihrl, value=match_intensity, step_size=STEP_SIZES
        )
        stimuli.show_stimulus(
            ihrl=ihrl,
            stimulus_texture=stimulus_texture,
            matching_field_stim=matching_field_stim,
            match_intensity=match_intensity,
        )

    print(f"Match intensity = {match_intensity}")

    return match_intensity


def save_variegated(variegated_array):
    # surround information of matching patch should be written together with matched value
    with open(
        f"{data_management.results_dir}/{data_management.participant}_{data_management.session_id}_all-match-surr.txt",
        "a",
    ) as fid_all_match:
        fid_all_match.write(
            "%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n"
            % (
                variegated_array[0, 0],
                variegated_array[0, 1],
                variegated_array[0, 2],
                variegated_array[0, 3],
                variegated_array[0, 4],
                variegated_array[1, 0],
                variegated_array[1, 1],
                variegated_array[1, 2],
                variegated_array[1, 3],
                variegated_array[1, 4],
                variegated_array[2, 0],
                variegated_array[2, 1],
                variegated_array[2, 3],
                variegated_array[2, 4],
                variegated_array[3, 0],
                variegated_array[3, 1],
                variegated_array[3, 2],
                variegated_array[3, 3],
                variegated_array[3, 4],
                variegated_array[4, 0],
                variegated_array[4, 1],
                variegated_array[4, 2],
                variegated_array[4, 3],
                variegated_array[4, 4],
            )
        )

    # screenshooting
    # gl.glReadBuffer(gl.GL_FRONT)
    # pixels = gl.glReadPixels(0,0, WIDTH, HEIGHT, gl.GL_RGB, gl.GL_UNSIGNED_BYTE)

    # image = Image.fromstring("RGB", (WIDTH, HEIGHT), pixels)
    # image = image.transpose( Image.FLIP_TOP_BOTTOM)
    # image.save('screenshot_%d.png' % trl)
