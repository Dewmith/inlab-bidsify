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

Created on Tue July 9th 2024

This code adds the custom metadata to the JSON of the run.
"""

import os
import json

# Fonction pour ajouter des informations supplémentaires au fichier JSON
def add_custom_metadata(bids_path, run_index, run_desc, session, config):

    json_path = bids_path.copy().update(extension='.json')
    
    with open(json_path, 'r') as f:
        json_content = json.load(f)
    
    # Ajouter les informations manuelles
    # Pour que ça passe le BIDS Validator, 
    # j'utilise le champs autorisé "TaskDescription"
    # https://bids-specification.readthedocs.io/en/v1.3.0/04-modality-specific-files/03-electroencephalography.html
    # Ceux en commentaire sont automatiquement ajoutés par BIDS-MNE.
    json_content.update({
        "TaskDescription": f"{session} condition, run n. {run_index} - desc. '{run_desc}'",
        "TaskName": config['task'],
        "InstitutionName": config['InstitutionName'],
        "InstitutionAddress": config['InstitutionAddress'],
        # "Manufacturer": config['manufacturer'],
        "ManufacturersModelName": config['manufacturers_model_name'],
        # "EEGReference": config['eeg_reference'],
        # "EEGGround": config['eeg_ground'],
        # "EEGPlacementScheme": config['EEGPlacementScheme'],
        # "PowerLineFrequency": config['power_line_frequency'],
        # "SoftwareFilters": config['SoftwareFilters'],
        # "SamplingFrequency": config['SamplingFrequency'],
        # "RecordingType": config['RecordingType'],
        "SubjectArtefactDescription": config['SubjectArtefactDescription']        
    })

    with open(json_path, 'w') as f:
        json.dump(json_content, f, indent=4)

    