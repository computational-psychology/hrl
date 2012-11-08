### Imports ###

# Package Imports
from hrl import HRL

# Qualified Imports
import numpy as np
import argparse as ap
import sys
import os

# Unqualified Imports
from random import uniform


### Argument Parser ###


prsr = ap.ArgumentParser(description= "This is an experiment. It takes an argument in the form of a subject name, which it will use to name the result file. The experiment involves asking subjects to set a central circle to the luminance in between two other circles. Fine and coarse controls are provided by directional keys, and the selected luminance is entered with space/white.")

prsr.add_argument('sbj',default='subject',nargs='?',help="The name of the subject of the experiment. Default: subject")


### Main ###


def main():

    # Parse args
    args = prsr.parse_args()

    # HRL parameters
    wdth = 1024
    hght = 768

    # Section the screen - used by Core Loop
    wqtr = wdth/8.0

    # IO Stuff
    dpxBool = True
    dfl = 'design.csv'
    rfl = 'results/' + args.sbj + '.csv'
    flds = ['SelectedMunsell','LeftMunsell','RightMunsell','Trial','TrialTime'
            ,'FramePresent','LeftLuminance','RightLuminance','InitialLuminance'
            ,'InitialMunsell','SelectedLuminance']
    btns = ['Yellow','Red','Blue','Green','White']

    # Central Coordinates (the origin of the graphics buffers is at the centre of the
    # screen. Change this if you don't want a central coordinate system. If you delete
    # this part the default will be a matrix style coordinate system.
    coords = (-0.5,0.5,-0.5,0.5)
    flipcoords = False

    # Pass this to HRL if we want to use gamma correction.
    lut = 'lut.txt'
    # If fs is true, we must provide a way to exit with e.g. checkEscape().
    fs = True

    # Step sizes for luminance changes
    smlstp = 0.005
    bgstp = 0.05

    # HRL Init
    hrl = HRL(wdth,hght,0,dpx=dpxBool,dfl=dfl,rfl=rfl,rhds=flds
              ,btns=btns,fs=fs,coords=coords,lut=lut,flipcoords=flipcoords)

    hrl.rmtx['Trial'] = 0

    # Core Loop
    for dsgn in hrl.dmtx:

        # Load Trial
        lmns = float(dsgn['LeftMunsell'])
        rmns = float(dsgn['RightMunsell'])
        rds = float(dsgn['Radius'])
        frm = bool(dsgn['FramePresent'])

        # Draw frame (or not)
        if hrl.rmtx['Trial'] is 0 and frm:
            hrl.newTexture(np.array([[0]])).draw((0,0),(wdth,hght))
            hrl.newTexture(np.array([[1]])).draw((0,0),(0.525*wdth,0.525*hght))
            hrl.newTexture(np.array([[0]])).draw((0,0),(0.5*wdth,0.5*hght))

        # Create Patches
        llm = munsell2luminance(np.array([[lmns]]))
        rlm = munsell2luminance(np.array([[rmns]]))

        cmns = uniform(0.0,1.0)
        clm = munsell2luminance(np.array([[cmns]]))

        hrl.newTexture(llm,'circle').draw((-wqtr,0),(2*rds,2*rds))
        hrl.newTexture(rlm,'circle').draw((wqtr,0),(2*rds,2*rds))
        hrl.newTexture(clm,'circle').draw((0,0),(2*rds,2*rds))

        # Record some initial values for the result matrix
        hrl.rmtx['Trial'] += 1
        hrl.rmtx['FramePresent'] = frm
        hrl.rmtx['LeftLuminance'] = llm[0,0]
        hrl.rmtx['LeftMunsell'] = lmns
        hrl.rmtx['RightLuminance'] = rlm[0,0]
        hrl.rmtx['RightMunsell'] = rmns
        hrl.rmtx['InitialLuminance'] = clm[0,0]
        hrl.rmtx['InitialMunsell'] = cmns

        # Draw but don't clear the back buffer
        hrl.flip(clr=False)

        # Prepare Core Loop logic
        btn = None
        t = 0.0
        escp = False

        # Note the trial
        print hrl.rmtx['Trial']

        # Adjust central patch
        while ((btn != 'White') & (escp != True)):

            (btn,t1) = hrl.readButton()
            t += t1

            if btn == 'Yellow':
                cmns += bgstp
            elif btn == 'Red':
                cmns += smlstp
            elif btn == 'Blue':
                cmns -= bgstp
            elif btn == 'Green':
                cmns -= smlstp

            # Bound Checking
            if cmns > 1: cmns = 1
            if cmns < 0: cmns = 0

            # Update display
            clm = munsell2luminance(np.array([[cmns]]))
            hrl.newTexture(clm,'circle').draw((0,0),(2*rds,2*rds))
            hrl.flip(clr=False)

            if hrl.checkEscape(): escp = True

        # Save results of trial
        hrl.rmtx['TrialTime'] = t/1000
        hrl.rmtx['SelectedLuminance'] = clm[0,0]
        hrl.rmtx['SelectedMunsell'] = cmns
        hrl.writeResultLine()

        # Check if escape has been pressed
        if escp: break

    # Experiment is over!
    hrl.close()


### Functions copied from stimuli/utils.py ###


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
