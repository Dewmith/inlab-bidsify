#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
This function is part of the BIDSIF project
 
This software is distributed under the terms of the GNU General Public License
as published by the Free Software Foundation. Further details on the GPLv3
license can be found at http://www.gnu.org/copyleft/gpl.html.

FOR RESEARCH PURPOSES ONLY. THE SOFTWARE IS PROVIDED "AS IS," AND IN THE
HOPE THAT IT WILL BE USEFUL BUT WITHOUT ANY WARRANTY, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO WARRANTIES OF MERCHANTABILITY AND FITNESS FOR 
A PARTICULAR PURPOSE, NOR DO THEY ASSUME ANY LIABILITY OR RESPONSIBILITY
FOR THE USE OF THIS SOFTWARE.

=============================================================================
Authors: Arnaud Weill, Anne-Sophie Dubarry, Jean-Luc Blanc

Created on Tue July 9th 2024

This code allows creating a BIDS file from multiple BDF files.
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

        
