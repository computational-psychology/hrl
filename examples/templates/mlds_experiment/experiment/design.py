import data_management
import numpy as np
import pandas as pd
import itertools
import random

DEBUG = False

# design 1: GA
nl = 10
luminances = np.linspace(0.1, 0.9, nl).round(3)

if DEBUG:
    print('luminances: ', luminances)

def generate_session(Nrepeats=2, shuffle=True):
    """ 
    Generates design files for one session.
    We think of one session corresponding to several blocks of trials.
    You set up how many repeats you do per session with the argument
    Nrepeats
    """
    
    for i in range(Nrepeats):
        block = generate_block(shuffle=shuffle)
        block_id = f"mlds-{i}"

        # Save to file
        filepath = data_management.design_filepath(block_id)
        block.to_csv(filepath)


def generate_block(shuffle=True):
    """ 
    Experimental design for one block of trials. 
    Here you define how many trials one block will contain, which
    will depend on the number of conditions you have. 
    """
    
    stimuli_design = list(itertools.combinations(luminances, 3))
    
    trials = []
    for t in stimuli_design:
        
        t = list(t)
        if DEBUG:
            print()
            print(t)
            
        # Randomy shuffle order L-R-Down
        if random.randint(0, 1):
            t1, t2, t3 = t
        else:
            t3, t2, t1 = t
        
        if DEBUG:
            print(t)
        
        line = [t1, t2, t3]
        trials.append(line)

    # creates dataframe with all trials
    block = pd.DataFrame(
        trials,
        columns=['l1', 'l2', 'l3'],
    )    
    
    if shuffle:
        # Shuffle trial order
        block = block.reindex(np.random.permutation(block.index))
    block.reset_index(drop=True, inplace=True)
    block.index.name = "trial"

    return block


if __name__ == "__main__":
    
    
    #generate_session() # so called during the experiment
    
    #generate session for luminance measurement
    generate_session(Nrepeats=1, shuffle=False)
    
