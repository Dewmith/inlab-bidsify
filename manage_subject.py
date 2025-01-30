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
Authors: Arnaud Weill, Anne-Sophie Dubarry

Created on Tue July 11th 2024

This code allows creating a BIDS file from multiple BDF files.
"""

import sys
print(f"Python utilisé dans {__file__}: {sys.executable}")
print(f"Chemins de recherche : {sys.path}")

import os
from manage_bdf import manage_bdf
from update_dataset_description import update_dataset_description

def manage_subject(subject_path, subject_folder, config):

    # le sujet est le nom du dossier
    subject = subject_folder.lower()

    # Enumérer la liste des BDF
    bdf_files = [os.path.join(subject_path, f) for f in os.listdir(subject_path) if f.endswith('.bdf') and not(f.startswith('.'))]
    
    for run_index, bdf_file in enumerate(bdf_files, start=1):

        # Modifier le BIDS à partir du BDF
        manage_bdf(subject, run_index, bdf_file, config)

    # Ajouter les auteurs une fois le dossier BIDS créé
    # pour que le fichier "dataset_description.json" soit créé
    # donc après les appels à manage_bdf()
    update_dataset_description(config)