#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue July 9th 2024

This code allows creating a BIDS file from multiple BDF files.

@author: A. Weill
"""

import os
from manage_bdf import manage_bdf

def manage_subject(subject_path, subject_folder, config):

    # le sujet est le nom du dossier
    subject = subject_folder.lower()

    # Enumérer la liste des BDF
    bdf_files = [os.path.join(subject_path, f) for f in os.listdir(subject_path) if f.endswith('.bdf') and not(f.startswith('.'))]
    
    for run_index, bdf_file in enumerate(bdf_files, start=1):

        # Modifier le BIDS à partir du BDF
        manage_bdf(subject, run_index, bdf_file, config)

        