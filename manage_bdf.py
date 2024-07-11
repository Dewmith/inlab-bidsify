#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue July 9th 2024

This code allows modifying a BIDS directory from a BDF file.

@author: A. Weill
"""

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
        raise ValueError('le nom du sujet du fichier "' + bdf_file + '" ne correspond pas au dossier "' + subject_folder + '" !')

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

