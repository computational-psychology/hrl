"""
This script implements a simple psychophysics experiment which makes use of all
the functionality of HRL. It forms a good basis from which to write your own
experiment.

The experiment involves three circles of different luminance, and the objective
is to set the middle circle to have a luminance in between the two other
circles. The luminance of the middle circle can be changed via Up and Down for
big steps, and Right and Left for small steps. When the subject feels that the
luminance is correct, Space can be pressed to save the results to a file and
move to the next round. Escape can be pressed at any time to quit the
experiment. Results will be saved in a file called 'results.csv'.
"""

### Imports ###

# Package Imports
from hrl import HRL

# Qualified Imports
import numpy as np
import sys
import os

# Unqualified Imports
from random import uniform
from socket import gethostname

inlab_siemens = True if "vlab" in gethostname() else False
inlab_viewpixx =  True if "viewpixx" in gethostname() else False


### Main ###
def main():


    ### HRL Parameters ###


    # Here we define all the paremeters required to instantiate an HRL object.

    # Which devices we wish to use in this experiment. See the
    # pydoc documentation for a list of # options.
    if inlab_siemens:
        graphics='datapixx'
        inputs='responsepixx'
        scrn=1
        fs = True  # fullscreen
        wdth = 1024  # Screen size
        hght = 768

    elif inlab_viewpixx:
        graphics='viewpixx'
        inputs='responsepixx'
        scrn=1
        fs = True  # fullscreen
        wdth = 1920  # Screen size
        hght = 1080
        
    else:
        graphics='gpu' # 'datapixx' is another option
        inputs='keyboard' # 'responsepixx' is another option
        scrn=1
        fs = False # not fullscreen: windowed
        wdth = 1024  # Screen size
        hght = 768


    photometer=None


    # Design and result matrix information. This allows us the to use the HRL
    # functionality for automatically reading a design matrix, and
    # automatically generating a result matrix. See 'pydoc hrl.hrl' for more
    # information about these.

    # Design and Result matrix files names
    dfl = 'design.csv'
    rfl = 'results.csv'

    # The names of the fields in the results matrix. In each loop of the
    # script, we write another line of values to results.csv under these
    # headings.
    rhds = ['SelectedMunsell','LeftMunsell','RightMunsell','Trial','TrialTime'
            ,'FramePresent','LeftLuminance','RightLuminance','InitialLuminance'
            ,'InitialMunsell','SelectedLuminance']

    # Pass this to HRL if we want to use gamma correction.
    lut = 'lut.csv'

    # Create the hrl object with the above fields. All the default argument names are
    # given just for illustration.
    hrl = HRL(graphics=graphics,inputs=inputs,photometer=photometer,
              wdth=wdth,hght=hght,bg=0,dfl=dfl,rfl=rfl,rhds=rhds,fs=fs,
              scrn=scrn)

    # hrl.results is a dictionary which is automatically created by hrl when
    # give a list of result fields. This can be used to easily write lines to
    # the result file, as will be seen later.
    hrl.results['Trial'] = 0

    
    ### Experiment setup ###


    # We are arranging circles and shapes around the screen, so it's helpful to
    # section the screen into eights and halves.
    whlf = wdth/2.0
    hhlf = hght/2.0
    weht = wdth/8.0
    heht = hght/8.0

    # These are the big and small step sizes for luminance changes
    smlstp = 0.005
    bgstp = 0.05

    # Here we load the square frame which contains the circles into the back
    # buffer. This is simply a white square covered by a slightly smaller black
    # square. The textures loaded are simply 1x1 pixel values, but then we use
    # the draw function to stretch them to the appropriate size. Since we never
    # draw these objects again, we don't bother saving the texture objects
    # returned by newTexture, but rather simply draw them right away and then
    # throw them away.
    frm1 = hrl.graphics.newTexture(np.array([[1]]))
    frm2 = hrl.graphics.newTexture(np.array([[0]]))

    frm1.draw((1.9*weht,1.9*heht),(0.525*wdth,0.525*hght))
    frm2.draw((2*weht,2*heht),(0.5*wdth,0.5*hght))

    hrl.graphics.flip(clr=False)

    frm1.draw((1.9*weht,1.9*heht),(0.525*wdth,0.525*hght))
    frm2.draw((2*weht,2*heht),(0.5*wdth,0.5*hght))


    ### Core Loop ###


    # hrl.designs is an iterator over all the lines in the specified design
    # matrix, which was loaded at the creation of the hrl object. Looping over
    # it in a for statement provides a nice way to run each line in a design
    # matrix. The fields of each design line (dsgn) are drawn from the design
    # matrix in the design file (design.csv).
    for dsgn in hrl.designs:

        # Here we save the values of the design line with appropriately cast
        # types and simple names.
        lmns = float(dsgn['LeftMunsell'])
        rmns = float(dsgn['RightMunsell'])
        rds = float(dsgn['Radius'])
        frm = bool(dsgn['FramePresent'])

        # And we randomly initialize the luminance of the central circle.
        cmns = uniform(0.0,1.0)

        # Here we create our circle textures. Again, they are simply 1x1 pixel
        # textures, but since they are uniform in colour, it serves simply to
        # stretch them to our desired dimensions.
        llm = munsell2luminance(np.array([[lmns]]))
        rlm = munsell2luminance(np.array([[rmns]]))
        clm = munsell2luminance(np.array([[cmns]]))

        # Here we draw the circles to the back buffer
        lcrc = hrl.graphics.newTexture(llm,'circle')
        rcrc = hrl.graphics.newTexture(clm,'circle')

        lcrc.draw((whlf-weht,hhlf),(2*rds,2*rds))
        rcrc.draw((whlf+weht,hhlf),(2*rds,2*rds))
        hrl.graphics.flip(clr=False)

        lcrc.draw((whlf-weht,hhlf),(2*rds,2*rds))
        rcrc.draw((whlf+weht,hhlf),(2*rds,2*rds))
        hrl.graphics.newTexture(rlm,'circle').draw((whlf,hhlf),(2*rds,2*rds))

        # Finally we load our frame and our circles to the screen. We don't
        # clear the back buffer because we don't want to redraw the frame, and
        # we'll simply draw new circles ontop of old ones.
        hrl.graphics.flip(clr=False)


        # And finally we preload some variables to prepare for our button
        # reading loop.

        # The button pressed
        btn = None
        # The time it took to decide on the mean luminance
        t = 0.0
        # Whether escape was pressed
        escp = False


        ### Input Loop ####
        
        # Until the user finalizes their luminance choice for the central
        # circle, or pressed escape...
        while ((btn != 'Space') & (escp != True)):

            # Read the next button press
            (btn,t1) = hrl.inputs.readButton()
            # Add the time it took to press to the decision time
            t += t1

            # Respond to the pressed button
            if btn == 'Up':
                cmns += bgstp
            elif btn == 'Right':
                cmns += smlstp
            elif btn == 'Down':
                cmns -= bgstp
            elif btn == 'Left':
                cmns -= smlstp
            elif btn == 'Escape':
                escp = True
                break

            # Make sure the luminance doesn't fall out of the range [0,1]
            if cmns > 1: cmns = 1
            if cmns < 0: cmns = 0

            # And update the display with the new value
            clm = munsell2luminance(np.array([[cmns]]))
            hrl.graphics.newTexture(clm,'circle').draw((whlf,hhlf),(2*rds,2*rds))
            hrl.graphics.flip(clr=False)

        # Once a value has been chosen by the subject, we save all the relevant
        # variables to the result file by loading it all into the hrl.results
        # dictionary, and then finally running hrl.writeResultLine().
        hrl.results['Trial'] += 1
        hrl.results['FramePresent'] = frm
        hrl.results['LeftLuminance'] = llm[0,0]
        hrl.results['LeftMunsell'] = lmns
        hrl.results['RightLuminance'] = rlm[0,0]
        hrl.results['RightMunsell'] = rmns
        hrl.results['InitialLuminance'] = clm[0,0]
        hrl.results['InitialMunsell'] = cmns
        hrl.results['TrialTime'] = t
        hrl.results['SelectedLuminance'] = clm[0,0]
        hrl.results['SelectedMunsell'] = cmns
        hrl.writeResultLine()

        # We print the trial number simply to keep track during an experiment
        print(hrl.results['Trial'])

        # If escape has been pressed we break out of the core loop
        if escp:
            print("Session cancelled")
            break

    # And the experiment is over!
    hrl.close()
    print("Session complete")


### Functions copied from stimuli/utils.py ###

# These functions are used to convert to and from the munsell scale.
# Understanding these is not particularly important for understanding how to
# use HRL to run this experiment.

def luminance2munsell(lum_values, reference_white=1.0):
    """
    Transform luminance values into Munsell values.
    The luminance values do not have to correspond to specific units, as long
    as they are in the same unit as the reference white, because Munsell values
    are a perceptually uniform scale of relative luminances.
    
    Parameters
    ----------
    lum_values : numpy-array
    reference_white : number

    Returns
    -------
    munsell_values : numpy-array

    Reference: H. Pauli, "Proposed extension of the CIE recommendation
    on 'Uniform color spaces, color difference equations, and metric color
    terms'," J. Opt. Soc. Am. 66, 866-867 (1976) 
    """

    x = lum_values / float(reference_white)
    idx = x <= (6. / 29) ** 3
    y1 = 841. / 108 * x[idx] + 4. / 29
    y2 = x[~idx] ** (1. / 3)
    y = np.empty(x.shape)
    y[idx] = y1
    y[~idx] = y2
    return (11.6 * y - 1.6) / 10

def munsell2luminance(munsell_values, reference_white=1.0):
    """
    Transform (normalized [0,1]) Munsell values to luminance values.
    The luminance values will be in the same unit as the reference white, which
    can be arbitrary as long as the scale is linear.

    Parameters
    ----------
    munsell_values : numpy-array
    reference_white : number

    Returns
    -------
    lum_values : numpy-array

    Reference: H. Pauli, "Proposed extension of the CIE recommendation
    on 'Uniform color spaces, color difference equations, and metric color
    terms'," J. Opt. Soc. Am. 66, 866-867 (1976) 
    """
    munsell_values *= 10
    lum_values = (munsell_values + 1.6) / 11.6
    idx = lum_values <= 6. / 29
    lum_values[idx] = (lum_values[idx] - 4. / 29) / 841 * 108
    lum_values[~idx] **= 3
    return lum_values * reference_white


### Run Main ###


if __name__ == '__main__':
    main()
