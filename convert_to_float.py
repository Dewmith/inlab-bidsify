#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thursday, July 11, 2024

This code adds the custom metadata to the JSON of the run.

@author: A. Weill
"""

def convert_to_float(value):
    try:
        # Essayer de convertir en flottant
        return float(value)
    except ValueError:
        # Retourner la valeur originale si ce n'est ni un entier ni un flottant
        return value
