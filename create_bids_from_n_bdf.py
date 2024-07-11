#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue July 9th 2024

This code allows creating a BIDS file from multiple BDF files.

@author: A. Weill
"""

import os
from read_config import read_config
from manage_subject import manage_subject

config = read_config('./bids_configurator.txt')

# Parcourir les dossiers de chaque sujet
for subject_folder in os.listdir(config['input_path']):

    subject_path = os.path.join(config['input_path'], subject_folder)

    if os.path.isdir(subject_path) and subject_folder.startswith('sub'):

        manage_subject(subject_path, subject_folder, config)

        
