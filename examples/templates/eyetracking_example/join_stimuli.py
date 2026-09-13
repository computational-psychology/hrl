#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Joins two checkerboard stimuli created separatedely in one big image which is going to be
shown in the eye tracker monitor

@author: GA Jan 2023
"""

import glob
import numpy as np
import pandas as pd
from PIL import Image


obs = 'demo'

# screen specifications
WIDTH = 1920
HEIGHT = 1080

whlf = int(WIDTH / 2.0)
hhlf = int(HEIGHT / 2.0)

middlegap = 150 # between images, in pixels
   
bg_value = int(0.271 * 255) 


# getting all design files
files = sorted(glob.glob('design/%s/block_*.csv' % obs))

for f in files:

    # reading a design file
    df = pd.read_csv(f)
    
    block =  int(f.split('.csv')[0].split('_')[-1])
    print('block ', block)
    
    for i, row in df.iterrows():
            
        # current trial variables
        thistrial = int(row['Trial'])
        tau1 = float(row['tau1'])
        tau2 = float(row['tau2'])
        alpha1 = float(row['alpha1'])
        alpha2 = float(row['alpha2'])
        
        print('..trial ', thistrial)
        
        trialname1 = '%d_a_%.2f_tau_%.2f' % (thistrial, alpha1, tau1)
        stim_name1 = 'stimuli/%s/block_%d_%s_cropped.png' % (obs, block, trialname1)
    
        trialname2 = '%d_a_%.2f_tau_%.2f' % (thistrial, alpha2, tau2)
        stim_name2 = 'stimuli/%s/block_%d_%s_cropped.png' % (obs, block, trialname2)
        
        im1 = Image.open(stim_name1).convert('L')
        im2 = Image.open(stim_name2).convert('L')
        
        bg = np.ones((HEIGHT, WIDTH))*bg_value
        bg = bg.astype('int8')
        
        im = Image.fromarray(bg, mode='L')    
        im.paste(im1, (int(whlf - im1.width - middlegap/2), int(hhlf - im1.height/2)))
        im.paste(im2, (int(whlf + middlegap/2), int(hhlf - im2.height/2)))    
        
        # saving image 
        im.convert('RGB').save('stimuli/%s/block_%d_%d.png' % (obs, block, thistrial))

    
# EOF  
