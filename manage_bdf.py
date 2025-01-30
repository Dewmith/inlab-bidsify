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

This code allows modifying a BIDS directory from a BDF file.
"""

import sys
print(f"Python utilisé dans {__file__}: {sys.executable}")
print(f"Chemins de recherche : {sys.path}")

import os
import mne
from mne_bids import BIDSPath, write_raw_bids
from add_custom_metadata import add_custom_metadata

def manage_bdf(subject, run_index, bdf_file, config):

    # récupérer le nom du sujet, la session et le run
    # Suppression de l'extension .bdf
    bdf_file_without_ext = os.path.basename(bdf_file)
    bdf_file_without_ext = os.path.splitext(bdf_file_without_ext)[0]
    
    # Division de la chaîne en utilisant le séparateur "-"
    # Attribution des parties aux variables
    sub, session, run_desc = bdf_file_without_ext.split("-")

    run = str(run_index)

    # est-ce que c'est le bon sujet ?
    if sub.lower() != subject:
        raise ValueError('le nom du sujet du fichier "' + bdf_file + '" ne correspond pas au dossier "' + subject + '" !')

    # Suppression du préfixe 'sub' si présent
    if subject.startswith('sub'):
        subject = subject[3:]

    # lire les données brutes du BDF
    # ne pas charger les données en mémoire (ce n'est pas nécessaire car on ne les traite pas)
    raw = mne.io.read_raw_bdf(bdf_file, preload=False)

    # Créer un chemin BIDS unique pour chaque sujet
    bids_path = BIDSPath(subject=subject, session=session, run=run,
                            datatype='eeg', task=config['task'], root=config['out_path'])

    # Écrire les données combinées en format BIDS
    # Utiliser format='EDF' pour spécifier explicitement le format de sortie
    # ('EDF' utilisé pour les données préchargées)
    # sinon 'auto' pour garder le même format
    write_raw_bids(raw, bids_path=bids_path, allow_preload=False, format='auto', overwrite=False)
        
    # Ajouter les métadonnées personnalisées au fichier JSON
    add_custom_metadata(bids_path, run_index, run_desc, session, config)

