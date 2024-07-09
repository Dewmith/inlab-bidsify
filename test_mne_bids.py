#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 10 13:35:52 2022

@author: Simon More, A.-Sophie Dubarry, A. Weill
"""

import os
import mne
from mne_bids import BIDSPath, write_raw_bids

# raw_data="/Users/annesophiedubarry/Documents/0_projects/in_progress/DISC/ADOEFFORT_mgrosbras/data/sub00/sub00-nback.bdf"
# out_path="/Users/annesophiedubarry/Documents/0_projects/in_progress/DISC/ADOEFFORT_mgrosbras/data/bids_datasets"

user_dir = os.path.expanduser('~')
raw_data= os.path.join(user_dir, 'Documents', 'Python-Scripts' ,'BIDSIF', 'Entree_Q0', 'sub03', 'sub03-proactive-test.bdf')
out_path= os.path.join(user_dir, 'Documents', 'Python-Scripts' ,'BIDSIF', 'Sortie_Q0')

raw = mne.io.read_raw_bdf(raw_data, preload=False)

task='nback'

bids_path = BIDSPath(subject='s00', session='nback', run='1',
                         datatype='eeg', task=task, root=out_path)
write_raw_bids(raw, bids_path=bids_path)

print("BIDS data created at "+out_path)
