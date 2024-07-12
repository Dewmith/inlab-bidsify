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

Created on Tue July 11th 2024

This code adds the custom metadata to the JSON of the run.
"""

def convert_to_float(value):
    try:
        # Essayer de convertir en flottant
        return float(value)
    except ValueError:
        # Retourner la valeur originale si ce n'est ni un entier ni un flottant
        return value
