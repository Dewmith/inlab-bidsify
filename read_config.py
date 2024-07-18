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

This code allows reading the configuration file used by the scripts.
"""

from convert_to_float import convert_to_float

# Fonction pour lire le fichier de configuration
def read_config(config_file):

    config = {}

    with open(config_file, 'r') as f:
    
        for line in f:
    
            line = line.strip()
    
            if line and not line.startswith('#'):
    
                key, value = line.split('=', 1)
                config[key.strip()] = convert_to_float(value.strip().strip("'").strip('"'))
                
    return config
