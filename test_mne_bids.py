#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 10 13:35:52 2022

@author: simon
"""

import mne
from mne_bids import BIDSPath, write_raw_bids
edf_path="/media/simon/DATADRIVE2/openscience/requetes/eeg_recording/ma0844az_1-1+.edf"

raw = mne.io.read_raw_edf(edf_path, preload=False)

task='simon'

bids_path = BIDSPath(subject='66', session='077', run='99',
                         datatype='eeg', task=task, root='./bids_dataset')
write_raw_bids(raw, bids_path=bids_path)

print("OK")
