#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue July 9th 2024

This code allows reading the configuration file used by the scripts.

@author: A. Weill
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
