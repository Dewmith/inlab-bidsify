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

Created on Tue July 12th 2024

This function update name and authors in the JSON description dataset.
"""

import os
import json

def update_dataset_description(config):
    dataset_description_path = os.path.join(config['out_path'], "dataset_description.json")
    
    if not os.path.exists(dataset_description_path):
        raise ValueError(f"Le fichier {dataset_description_path} n'existe pas.")
    
    with open(dataset_description_path, 'r') as f:
        dataset_description = json.load(f)
    
    dataset_description['Authors'] = config['Authors'].split(', ')
    dataset_description['Name'] = config['Name']
    
    with open(dataset_description_path, 'w') as f:
        json.dump(dataset_description, f, indent=4)
