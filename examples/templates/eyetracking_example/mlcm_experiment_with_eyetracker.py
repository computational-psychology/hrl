#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Template code for an experiment with the Eyelink eyetracker.

Basd on MLCM experiment template

Uses HRL on python 3

@author: GA Jan 2023

"""
# needed for Eyelink eyetracker.
# Install Eyelink Developer Kit and pylink with pip
# See official documentation from SR Research
import pylink
from CalibrationGraphicsPygame import CalibrationGraphics

# Package Imports
from hrl import HRL
from hrl.graphics import graphics
import OpenGL.GL as gl
import pygame

import numpy as np
from PIL import Image, ImageFont, ImageDraw
import sys, os, time
from string import ascii_letters, digits
from socket import gethostname

inlab_siemens = True if "vlab" in gethostname() else False
inlab_viewpixx =  True if "viewpixx" in gethostname() else False

### Eyetracker
dummy_mode = False # True or False. Dummy mode=True is to debug the code without using eyetracker
#######

if inlab_siemens:
    # size of Siements monitor
    WIDTH = 1024
    HEIGHT = 768
    bg_blank = 0.1 # corresponding to 50 cd/m2 approx

elif inlab_viewpixx:
    # size of VPixx monitor
    WIDTH = 1920
    HEIGHT = 1080
    bg_blank = 0.271 # corresponding to 50 cd/m2 approx

else:
    WIDTH = 1920
    HEIGHT = 1080
    bg_blank = 0.271

# center of screen
whlf = WIDTH / 2.0
hhlf = HEIGHT / 2.0

# 2 seconds stimulus time
stim_time = 5000 # in miliseconds


def image_to_array(fname, in_format = 'png'):
    # Function written by Marianne
    """
    Reads the specified image file (default: png), converts it to grayscale 
    and into a numpy array
    
    Input:
    ------
    fname       - name of image file
    in_format   - extension (png default)
    
    Output:
    -------
    numpy array
    """
    im = Image.open('%s.%s' %(fname, in_format)).convert('L')
    temp_matrix  = [ im.getpixel(( y, x)) for x in range(im.size[1]) for y in range(im.size[0])]
    temp_matrix  = np.array(temp_matrix).reshape(im.size[1], im.size[0])
    im_matrix    = np.array(temp_matrix.shape,dtype=np.float64)
    im_matrix    = temp_matrix/255.0
    #print im_matrix
    return im_matrix
    

def read_design(fname):
    # function written by Marianne

    design = open(fname)
    header = design.readline().strip('\n').split()
    print(header)
    data   = design.readlines()

    new_data = {}

    for k in header:
        new_data[k] = []
    for l in data:
        curr_line = l.strip().split()
        for j, k in enumerate(header):
            new_data[k].append(curr_line[j])
    return new_data


def read_design_csv(fname):


    design = open(fname)
    header = design.readline().strip('\n').split(',')
    #print header
    data   = design.readlines()

    new_data = {}

    for k in header:
        new_data[k] = []
    for l in data:
        curr_line = l.strip().split(',')
        for j, k in enumerate(header):
            new_data[k].append(curr_line[j])
    return new_data


def get_last_trial(vp_id,sess):
    try:
        rfl =open('results/%s/block_%d.csv' % (vp_id,  sess), 'r')
    except IOError:
        print('result file not found, starting at trial 0')
        return 0

    for line in rfl:
        try:
            last_trl = int(line.split(',')[1])
        except ValueError:
            pass

    rfl.close()

    if last_trl>0:
        last_trl=last_trl+1

    return last_trl

def draw_text(text, bg=bg_blank, text_color=0, fontsize=48):
    # function from Thorsten
    """ create a numpy array containing the string text as an image. """

    bg *= 255
    text_color *= 255
    font = ImageFont.truetype(
            "/usr/share/fonts/truetype/msttcorefonts/arial.ttf", fontsize,
            encoding='unic')
    text_width, text_height = font.getsize(text)
    im = Image.new('L', (text_width, text_height), int(bg))
    draw = ImageDraw.Draw(im)
    draw.text((0,0), text, fill=text_color, font=font)
    return np.array(im) / 255.


def show_continue(hrl, b, nb):
    # Function from Thorsten
    hrl.graphics.flip(clr=True)
    if LANG=='de':
        lines = [u'Du kannst jetzt eine Pause machen.',
                 u' ',
                 u'Du hast %d von %d blocks geschafft.' % (b, nb),
                 u' ',
                 u'Zum Weitermachen, druecke die rechte Taste,',
                 u'zum Beenden druecke die linke Taste.'
                 ]
    elif LANG=='en':
        lines = [u'You can take a break now.',
                 u' ',
                 u'You have completed %d out of %d blocks.' % (b, nb),
                 u' ',
                 u'To continue, press the right button,',
                 u'to finish, press the left button.'
                 ]
    else:
        raise('LANG not available')

    for line_nr, line in enumerate(lines):
        textline = hrl.graphics.newTexture(draw_text(line, bg=bg_blank, fontsize=36))
        textline.draw(((WIDTH - textline.wdth) / 2,
                       (HEIGHT / 2 - (4 - line_nr) * (textline.hght + 10))))
    hrl.graphics.flip(clr=True)
    btn = None
    while not (btn == 'Left' or btn == 'Right'):
        (btn,t1) = hrl.inputs.readButton()

    # clean text
    graphics.deleteTextureDL(textline._dlid)

    return btn



def show_break(hrl,trial, total_trials):
    # Function from Thorsten
    hrl.graphics.flip(clr=True)

    if LANG=='de':
        lines = [u'Du kannst jetzt eine Pause machen.',
             u' ',
             u'Du hast %d von %d Durchgängen geschafft.' % (trial,
                 total_trials),
             u' ',
             u'Wenn du bereit bist, drücke die mittlere Taste.'
             ]
    elif LANG=='en':
         lines = [u'You can take a break now.',
             u' ',
             u'You have completed %d out of %d trials.' % (trial,
                 total_trials),
             u' ',
             u'When you are ready, press the middle button.'
             ]
    else:
        raise('LANG not available')

    for line_nr, line in enumerate(lines):
        textline = hrl.graphics.newTexture(draw_text(line, bg=bg_blank, fontsize=36))
        textline.draw(((WIDTH - textline.wdth) / 2,
                       (HEIGHT / 2 - (4 - line_nr) * (textline.hght + 10))))
    hrl.graphics.flip(clr=True)
    btn = None
    while btn != 'Space':
        (btn,t1) = hrl.inputs.readButton()
    # clean text
    graphics.deleteTextureDL(textline._dlid)


def run_trial(hrl,trl, block,start_trl, end_trl):
    
    hrl.graphics.flip(clr=True)
    
    print("TRIAL =", trl)

    #show a break screen automatically after so many trials
    if (trl-start_trl)%80==0 and (trl-start_trl)!=0:
        show_break(hrl,trl, (start_trl + (end_trl-start_trl)))

    # current trial design variables
    thistrial = int(design['Trial'][trl])
    tau1 = float(design['tau1'][trl])
    tau2 = float(design['tau2'][trl])
    alpha1 = float(design['alpha1'][trl])
    alpha2 = float(design['alpha2'][trl])

    print(tau1)
    print(alpha1)
    print(tau2)
    print(alpha2)

    # stimuli
    stim_name = 'stimuli/%s/block_%d_%d' % (vp_id, block, thistrial)
    
    # Preloading images before we start eyetracking recording
    # load stimlus image and convert from png to numpy array
    curr_image = image_to_array(stim_name)
    
    # texture creation in buffer : stimulus
    checkerboard = hrl.graphics.newTexture(curr_image)
    
        
    ###################################################################
    # get a reference to the currently active EyeLink connection
    el_tracker = pylink.getEYELINK()

    # put the tracker in the offline mode first
    el_tracker.setOfflineMode()

    # clear the host screen before we draw the backdrop
    el_tracker.sendCommand('clear_screen 0')

    # show a backdrop image on the Host screen, imageBackdrop() the recommended
    # function, if you do not need to scale the image on the Host
    # parameters: image_file, crop_x, crop_y, crop_width, crop_height,
    #             x, y on the Host, drawing options
    el_tracker.imageBackdrop('%s.png' % stim_name,
                             0, 0, WIDTH, HEIGHT, 0, 0,
                             pylink.BX_MAXCONTRAST)

    # If you need to scale the backdrop image on the Host, use the old Pylink
    # bitmapBackdrop(), which requires an additional step of converting the
    # image pixels into a recognizable format by the Host PC.
    # pixels = [line1, ...lineH], line = [pix1,...pixW], pix=(R,G,B)
    #
    # the bitmapBackdrop() command takes time to return, not recommended
    # for tasks where the ITI matters, e.g., in an event-related fMRI task
    # parameters: width, height, pixel, crop_x, crop_y,
    #             crop_width, crop_height, x, y on the Host, drawing options
    #
    # Use the code commented below to convert the image and send the backdrop
    #
    #pixels = [[img.get_at((i, j))[0:3] for i in range(scn_width)]
    #         for j in range(scn_height)]
    #el_tracker.bitmapBackdrop(scn_width, scn_height, pixels,
    #                         0, 0, scn_width, scn_height,
    #                         0, 0, pylink.BX_MAXCONTRAST)
    
    # send a "TRIALID" message to mark the start of a trial, see Data
    # Viewer User Manual, "Protocol for EyeLink Data to Viewer Integration"
    el_tracker.sendMessage('TRIALID %d' % trl)

    # record_status_message : show some info on the Host PC
    # here we show how many trial has been tested
    status_msg = 'TRIAL number %d' % trl
    el_tracker.sendCommand("record_status_message '%s'" % status_msg)

    # drift check
    # we recommend drift-check at the beginning of each trial
    # the doDriftCorrect() function requires target position in integers
    # the last two arguments:
    # draw_target (1-default, 0-draw the target then call doDriftCorrect)
    # allow_setup (1-press ESCAPE to recalibrate, 0-not allowed)
    #
    # Skip drift-check if running the script in Dummy Mode
    while not dummy_mode:
        # terminate the task if no longer connected to the tracker or
        # user pressed Ctrl-C to terminate the task
        if (not el_tracker.isConnected()) or el_tracker.breakPressed():
            terminate_task()
            return pylink.ABORT_EXPT

        # drift-check and re-do camera setup if ESCAPE is pressed
        try:
            error = el_tracker.doDriftCorrect(int(WIDTH/2.0),
                                              int(HEIGHT/2.0), 1, 1)
            # break following a success drift-check
            if error is not pylink.ESC_KEY:
                break
        except:
            pass

    # put tracker in idle/offline mode before recording
    el_tracker.setOfflineMode()

    # Start recording
    # arguments: sample_to_file, events_to_file, sample_over_link,
    # event_over_link (1-yes, 0-no)
    try:
        el_tracker.startRecording(1, 1, 1, 1)
    except RuntimeError as error:
        print("ERROR:", error)
        abort_trial()
        return pylink.TRIAL_ERROR

    # Allocate some time for the tracker to cache some samples
    pylink.pumpDelay(100)
    
    ###################################################################
    
    # draws fixation dot in the middle
    frm1 = hrl.graphics.newTexture(np.ones((2, 2))*0.0)
    frm1.draw(( whlf, hhlf))
    hrl.graphics.flip(clr=True)

    # sleeps for 250 ms
    #time.sleep(0.25)

    # Show stimulus
    # draw the checkerboard s
    checkerboard.draw((0,0))

    # flip everything
    hrl.graphics.flip(clr=False)   # clr= True to clear buffer
    
    # recording onset time for eyetracker
    onset_time = pygame.time.get_ticks()  # image onset time

    # send over a message to mark the onset of the image
    el_tracker.sendMessage('image_onset')
    
    # Send a message to clear the Data Viewer screen, get it ready for
    # drawing the pictures during visualization
    #el_tracker.sendMessage('!V CLEAR 128 128 128')

    # send over a message to specify where the image is stored relative
    # to the EDF data file, see Data Viewer User Manual, "Protocol for
    # EyeLink Data to Viewer Integration"
    #bg_image = '../../images/' + pic
    #imgload_msg = '!V IMGLOAD CENTER %s %d %d %d %d' % (bg_image,
    #                                                    int(scn_width/2.0),
    #                                                    int(scn_height/2.0),
    #                                                    int(scn_width),
    #                                                    int(scn_height))
    #el_tracker.sendMessage(imgload_msg)

    # loop for waiting a response
    btn = None
    response = None
    
    while btn == None or btn == 'Left' or btn == 'Right' or  btn == 'Space':
        # present the picture for a maximum of stim_time seconds
        if pygame.time.get_ticks() - onset_time >= stim_time:
            el_tracker.sendMessage('time_out')
            response = None 
            print('time out')
            break
            
        # abort the current trial if the tracker is no longer recording
        error = el_tracker.isRecording()
        if error is not pylink.TRIAL_OK:
            el_tracker.sendMessage('tracker_disconnected')
            abort_trial()
            return error

        (btn,t1) = hrl.inputs.readButton(to=1) # polls every 50 ms
        
        if  btn == 'Right':
            response = 1
            print("btn =", btn)
            t1 = pygame.time.get_ticks() - onset_time
            # send over a message to log the key press
            el_tracker.sendMessage('key_pressed')
            break
            
        elif btn == 'Left':
            response = 0
            print("btn =", btn)
            t1 = pygame.time.get_ticks() - onset_time
            # send over a message to log the key press
            el_tracker.sendMessage('key_pressed')
            break
            
        elif btn == 'Escape':
            el_tracker.sendMessage('trial_skipped_by_user')
            print('Escape pressed, exiting experiment!!')
            el_tracker.sendMessage('terminated_by_user')
            terminate_task()
            return pylink.ABORT_EXPT
            
            #hrl.close()
            #sys.exit(0)
            
    # clear screen
    hrl.graphics.flip(clr=True)
    
    # finishing trial successfully after a button press
    ########################################################################
    el_tracker.sendMessage('blank_screen')
    # send a message to clear the Data Viewer screen as well
    el_tracker.sendMessage('!V CLEAR 128 128 128')

    # stop recording; add 100 msec to catch final events before stopping
    pylink.pumpDelay(100)
    el_tracker.stopRecording()

    # record trial variables to the EDF data file, for details, see Data
    # Viewer User Manual, "Protocol for EyeLink Data to Viewer Integration"
    el_tracker.sendMessage('!V TRIAL_VAR block %s' % sess)
    el_tracker.sendMessage('!V TRIAL_VAR trial %s' % trl)
    el_tracker.sendMessage('!V TRIAL_VAR response %s' % response)
    el_tracker.sendMessage('!V TRIAL_VAR RT %d' % t1)

    # send a 'TRIAL_RESULT' message to mark the end of trial, see Data
    # Viewer User Manual, "Protocol for EyeLink Data to Viewer Integration"
    el_tracker.sendMessage('TRIAL_RESULT %d' % pylink.TRIAL_OK)
    #######################################################################

    # saving button presses results
    line = ','.join([str(block), str(trl), str(alpha1), str(alpha2), str(tau1),
                    str(tau2), str(response), str(t1), str(time.time())])

    line +='\n'
    rfl.write(line)
    rfl.flush()

    # clean checkerboard texture from buffer
    # (needed! Specially if hundreds of trials are presented, if not
    # cleared they accummulate in buffer)
    graphics.deleteTextureDL(checkerboard._dlid)


    return response


###########################################################################
def terminate_task():
    """ Terminate the task gracefully and retrieve the EDF data file

    file_to_retrieve: The EDF on the Host that we would like to download
    win: the current window used by the experimental script
    """

    # disconnect from the tracker if there is an active connection
    el_tracker = pylink.getEYELINK()

    if el_tracker.isConnected():
        # Terminate the current trial first if the task terminated prematurely
        error = el_tracker.isRecording()
        if error == pylink.TRIAL_OK:
            abort_trial()

        # Put tracker in Offline mode
        el_tracker.setOfflineMode()

        # Clear the Host PC screen and wait for 500 ms
        el_tracker.sendCommand('clear_screen 0')
        pylink.msecDelay(500)

        # Close the edf data file on the Host
        el_tracker.closeDataFile()

        # Show a file transfer message on the screen
        print('EDF data is transferring from EyeLink Host PC...')

        # Download the EDF data file from the Host PC to a local data folder
        # parameters: source_file_on_the_host, destination_file_on_local_drive
        local_edf = os.path.join(session_folder, edf_file)
        try:
            el_tracker.receiveDataFile(edf_file, local_edf)
        except RuntimeError as error:
            print('ERROR:', error)


def abort_trial():
    """Ends recording

    We add 100 msec to catch final events
    """

    # get the currently active tracker object (connection)
    el_tracker = pylink.getEYELINK()

    # Stop recording
    if el_tracker.isRecording():
        # add 100 ms to catch final trial events
        pylink.pumpDelay(100)
        el_tracker.stopRecording()

    # clear the screen
    hrl.graphics.flip(clr=True)
    
    # Send a message to clear the Data Viewer screen
    el_tracker.sendMessage('!V CLEAR 128 128 128')

    # send a message to mark trial end
    el_tracker.sendMessage('TRIAL_RESULT %d' % pylink.TRIAL_ERROR)

    return pylink.TRIAL_ERROR

###########################################################################  

def prepare_eyetracker_for_recording_block(edf_fname, firstblock=False):
    """
    Preparing the Eyetracker for a new recording. A new EDF file is setup
    and open, and all parameters are passed to the Eyetracker.
    Every block is a new file, so we call this function before every block.
    
    Code adapted from picture.py example included in official SR Research 
    documentation
    
    """
    
    # Step 2: Open an EDF data file on the Host PC
    edf_file = edf_fname + ".EDF"
    print('Eyetracking data being saved in file: ', edf_file)
    
    try:
        el_tracker.openDataFile(edf_file)
    except RuntimeError as err:
        print('ERROR:', err)
        # close the link if we have one open
        if el_tracker.isConnected():
            el_tracker.close()
        sys.exit()

    # Add a header text to the EDF file to identify the current experiment name
    # This is OPTIONAL. If your text starts with "RECORDED BY " it will be
    # available in DataViewer's Inspector window by clicking
    # the EDF session node in the top panel and looking for the "Recorded By:"
    # field in the bottom panel of the Inspector.
    preamble_text = 'RECORDED BY %s' % os.path.basename(__file__)
    el_tracker.sendCommand("add_file_preamble_text '%s'" % preamble_text)

    #### Configuring the eye tracker
    #
    # Put the tracker in offline mode before we change tracking parameters
    el_tracker.setOfflineMode()

    # Get the software version:  1-EyeLink I, 2-EyeLink II, 3/4-EyeLink 1000,
    # 5-EyeLink 1000 Plus, 6-Portable DUO
    eyelink_ver = 0  # set version to 0, in case running in Dummy mode
    if not dummy_mode:
        vstr = el_tracker.getTrackerVersionString()
        eyelink_ver = int(vstr.split()[-1].split('.')[0])
        # print out some version info in the shell
        print('Running experiment on %s, version %d' % (vstr, eyelink_ver))


    # File and Link data control
    # what eye events to save in the EDF file, include everything by default
    file_event_flags = 'LEFT,RIGHT,FIXATION,SACCADE,BLINK,MESSAGE,BUTTON,INPUT'
    # what eye events to make available over the link, include everything by default
    link_event_flags = 'LEFT,RIGHT,FIXATION,SACCADE,BLINK,BUTTON,FIXUPDATE,INPUT'
    
    # what sample data to save in the EDF data file and to make available
    # over the link, include the 'HTARGET' flag to save head target sticker
    # data for supported eye trackers
    if eyelink_ver > 3:
        file_sample_flags = 'LEFT,RIGHT,GAZE,HREF,RAW,AREA,HTARGET,GAZERES,BUTTON,STATUS,INPUT'
        link_sample_flags = 'LEFT,RIGHT,GAZE,GAZERES,AREA,HTARGET,STATUS,INPUT'
    else:
        file_sample_flags = 'LEFT,RIGHT,GAZE,HREF,RAW,AREA,GAZERES,BUTTON,STATUS,INPUT'
        link_sample_flags = 'LEFT,RIGHT,GAZE,GAZERES,AREA,STATUS,INPUT'
    el_tracker.sendCommand("file_event_filter = %s" % file_event_flags)
    el_tracker.sendCommand("file_sample_data = %s" % file_sample_flags)
    el_tracker.sendCommand("link_event_filter = %s" % link_event_flags)
    el_tracker.sendCommand("link_sample_data = %s" % link_sample_flags)

    # Optional tracking parameters
    # Sample rate, 250, 500, 1000, or 2000, check your tracker specification
    el_tracker.sendCommand("sample_rate 1000")
    # Choose a calibration type, H3, HV3, HV5, HV13 (HV = horizontal/vertical),
    el_tracker.sendCommand("calibration_type = HV9")
    
    # Pass the display pixel coordinates (left, top, right, bottom) to the tracker
    # see the EyeLink Installation Guide, "Customizing Screen Settings"
    el_coords = "screen_pixel_coords = 0 0 %d %d" % (WIDTH - 1, HEIGHT - 1)
    el_tracker.sendCommand(el_coords)

    # Write a DISPLAY_COORDS message to the EDF file
    # Data Viewer needs this piece of info for proper visualization, see Data
    # Viewer User Manual, "Protocol for EyeLink Data to Viewer Integration"
    dv_coords = "DISPLAY_COORDS  0 0 %d %d" % (WIDTH - 1, HEIGHT - 1)
    el_tracker.sendMessage(dv_coords)

    # Configure a graphics environment (genv) for tracker calibration
    # only if we are in the first block. 
    if firstblock:
        genv = CalibrationGraphics(el_tracker, hrl.graphics)


        # Set background and foreground colors
        # parameters: foreground_color, background_color
        foreground_color = 0.0
        background_color = bg_blank
        genv.setCalibrationColors(foreground_color, background_color)

        # Set up the calibration target
        #
        # The target could be a "circle" (default) or a "picture",
        # To configure the type of calibration target, set
        # genv.setTargetType to "circle", "picture", e.g.,
        # genv.setTargetType('picture')
        #
        # Use gen.setPictureTarget() to set a "picture" target, e.g.,
        # genv.setPictureTarget(os.path.join('images', 'fixTarget.bmp'))

        # Use a picture as the calibration target
        genv.setTargetType('picture')
        genv.setPictureTarget('fixTarget.bmp')

        # Configure the size of the calibration target (in pixels)
        # genv.setTargetSize(24)

        # Beeps to play during calibration, validation and drift correction
        # parameters: target, good, error
        #     target -- sound to play when target moves
        #     good -- sound to play on successful operation
        #     error -- sound to play on failure or interruption
        # Each parameter could be ''--default sound, 'off'--no sound, or a wav file
        # e.g., genv.setCalibrationSounds('type.wav', 'qbeep.wav', 'error.wav')
        genv.setCalibrationSounds('', '', '')

        # Request Pylink to use the Pygame window we opened above for calibration
        pylink.openGraphicsEx(genv)
    
    return edf_file
    
    
    

### Run Main ###
if __name__ == '__main__':

    LANG ='en' # 'de' or 'en'

    # log file name and location
    ## this is the design matrix which is loaded
    vp_id   = input ('Please input the observer name (e.g. demo): ')

    ## determines which blocks to run
    # reads block order
    blockorder = read_design_csv('design/%s/experiment_order.csv' % vp_id)

    # check if results folder exist, if not, creates
    results_folder = 'results'
    if not os.path.exists(results_folder):
        os.makedirs(results_folder)

    results_folder = 'results/%s' % vp_id
    if not os.path.exists(results_folder):
        os.makedirs(results_folder)

    # reads the blocks already done
    try:
        blocksdone = read_design_csv('results/%s/blocks_done.csv' % vp_id)

        # determine which blocks are left to run
        next = len(blocksdone['number'])
        blockstorun = {'number': blockorder['number'][next:], 'block': blockorder['block'][next:]}

    except IOError:
        blocksdone  = None
        blockstorun = blockorder  # all blocks to run

    # if all is done
    if len(blockstorun['number']) == 0:
        print("All BLOCKS are DONE, exiting.")


    # opens block file to write
    bfl = open('results/%s/blocks_done.csv'% vp_id,'a')
    if blocksdone == None:
        block_headers = ['number', 'block']
        bfl.write(','.join(block_headers)+'\n')
        bfl.flush()

    ###########################################################################
    #### Connect to the EyeLink Host PC
    if dummy_mode:
        el_tracker = pylink.EyeLink(None)
    else:
        try:
            el_tracker = pylink.EyeLink("100.1.1.1")
        except RuntimeError as error:
            print('ERROR:', error)
            sys.exit()    
    ###########################################################################

    # We create the HRL object with parameters that depend on the setup we are using
    if inlab_siemens:
        # create HRL object
        hrl = HRL(
            graphics="datapixx",
            inputs="responsepixx",
            photometer=None,
            wdth=WIDTH,
            hght=HEIGHT,
            bg=bg_blank,
            scrn=1,
            lut='lut.csv',
            db=True,
            fs=True,
        )
    elif inlab_viewpixx:

        hrl = HRL(
            graphics="viewpixx",
            inputs="responsepixx",
            photometer=None,
            wdth=WIDTH,
            hght=HEIGHT,
            bg=bg_blank,
            scrn=1,
            lut='lut_viewpixx.csv',
            db=True,
            fs=True,
        )

    else:
        hrl = HRL(
            graphics="gpu",
            inputs="keyboard",
            photometer=None,
            wdth=WIDTH,
            hght=HEIGHT,
            bg=bg_blank,
            scrn=0,
            lut=None,
            db=True,
            fs=False,
        )

    ###########################################################################   
    # #Iterate across all blocks that need to be presented
    for i in range(len(blockstorun['number'])):

        sess = int(blockstorun['number'][i])
        print(sess)
        bl = blockstorun['block'][i]

        print("Block %d " % sess)

        start_trl = get_last_trial(vp_id, sess)


        # log file name and location
        design = read_design_csv('design/%s/block_%d.csv' %(vp_id, sess))
        rfl    = open('results/%s/block_%d.csv' % (vp_id, sess), 'a')

        #  get end trial
        end_trl   = len(design['Trial'])


        if start_trl == 0:
            result_headers = ['block', 'trial', 'alpha1', 'alpha2', 'tau1', 'tau2', 'Response', 'resp.time', 'timestamp']
            rfl.write(','.join(result_headers)+'\n')


        ########################################################################### 
        #### SET UP NEW EDF file FOR EVERY BLOCK
        # For the eyetracker we need to set a EDF filename, length no more than 8 characthers
        # and no special characthers
        edf_fname = '%s%.2d' % (vp_id, sess)
        
        
        # check if the filename is valid (length <= 8 & no special char)
        allowed_char = ascii_letters + digits + '_'
        if not all([c in allowed_char for c in edf_fname]):
            raise(RuntimeError, 'ERROR: Invalid EDF filename')
        elif len(edf_fname) > 8:
            raise(RuntimeError, 'ERROR: EDF filename should not exceed 8 characters')

        # We download EDF data file from the EyeLink Host PC to the local hard
        # drive at the end of each testing session, here we rename the EDF to
        # include session start date/time
        session_identifier = time.strftime("%Y_%m_%d_%H_%M", time.localtime())
        
        # create a folder for the current testing session in the "results" folder
        session_folder = os.path.join(results_folder, 'EDF')
        if not os.path.exists(session_folder):
            os.makedirs(session_folder)
            
        firstblock = True if i==0 else False
        
        edf_file = prepare_eyetracker_for_recording_block(edf_fname, firstblock=firstblock)
        
        ########## Go into calibration mode before every block  #################   
        # skip this step if running the script in Dummy Mode
        if not dummy_mode:
            try:
                el_tracker.doTrackerSetup()
            except RuntimeError as err:
                print('ERROR:', err)
                el_tracker.exitCalibration()

        ###########################################################################    
        # loop over trials in one block
        for trl in np.arange(start_trl, end_trl):
            ret = run_trial(hrl, trl, sess,  start_trl, end_trl) # function that executes the experiment
            if not (ret == 0 or ret==1):
                break

        # close result file for this block
        rfl.close()
        
        # Step 7: disconnect, download the EDF file, then terminate the task
        terminate_task()
    
        # save the block just done
        if trl==(end_trl-1):
            bfl.write('%d,%s\n' %(sess, bl))
            bfl.flush()


        # continue?
        if i < len(blockstorun['number']) - 1 :
            print("continue with next block?")
            btn = show_continue(hrl, i+1, len(blockstorun['number']))
            if btn == 'Left':
                break

    
    # close block done file
    bfl.close()

    # finishes Eyelink connection
    if el_tracker.isConnected():
        # Close the link to the tracker.
        el_tracker.close()
    
    # finishes everything
    hrl.close()
    print("Session exited")
    



# EOF
