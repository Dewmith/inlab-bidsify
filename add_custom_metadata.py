#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue July 9th 2024

This code adds the custom metadata to the JSON of the run.

@author: A. Weill
"""

import os
import json

# Fonction pour ajouter des informations supplémentaires au fichier JSON
def add_custom_metadata(bids_path, run_index, run_desc, session, config):

    json_path = bids_path.copy().update(extension='.json')
    
    with open(json_path, 'r') as f:
        json_content = json.load(f)
    
    # Ajouter les informations manuelles
    json_content.update({
        "TaskName": config['task'],
        "InstitutionName": "CRPN - UMR 7077",
        "InstitutionAddress": "Aix-Marseille University / CNRS, CRPN - UMR 7077, Service Informatique, 3 Place Victor Hugo, 13331 Marseille cedex 3, France",
        "Manufacturer": config['manufacturer'],
        "ManufacturersModelName": config['manufacturers_model_name'],
        "EEGReference": config['eeg_reference'],
        "EEGGround": config['eeg_ground'],
        "PowerLineFrequency": config['power_line_frequency'],
        "SoftwareFilters": "n/a"
    })

    with open(json_path, 'w') as f:
        json.dump(json_content, f, indent=4)

    '''
    # Modifier le nom du fichier des informations non conformes
    json_run_path = os.path.join(os.path.dirname(json_path), f'run_description {session} condition, n. {run_index} - {run_desc}.json')
    
    # si le fichier existe, le charger
    if os.path.exists(json_run_path):

        with open(json_run_path, 'r') as f:
            json_run_content_2 = json.load(f)
    else:
        # sinon il commence vide
        json_run_content_2 = {}

    json_run_content_2.update({
        "RunNumber": run_index,
        "RunDescription": f'{session} condition, run n. {run_index} - "{run_desc}"'
    })

    with open(json_run_path, 'w') as f:
        json.dump(json_run_content_2, f, indent=4)
    '''