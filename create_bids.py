#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue July 9th 2024

This code allows creating a BIDS file from multiple BDF files.

@author: A. Weill
"""

import mne
from mne_bids import BIDSPath, write_raw_bids
import os
from datetime import datetime

# le user directory
user_dir = os.path.expanduser('~')

# Chemin du dossier d'entrée contenant les dossiers de sujet
input_path = os.path.join(user_dir, 'Documents', 'Python-Scripts' ,'BIDSIF', 'Entree_Q1')
# Chemin de sortie pour le fichier BIDS
out_path = os.path.join(user_dir, 'Documents', 'Python-Scripts' ,'BIDSIF', 'Sortie_Q1')

# Informations générales
task = 'nback'

# Parcourir les dossiers de chaque sujet
for subject_folder in os.listdir(input_path):
    subject_path = os.path.join(input_path, subject_folder)

    if os.path.isdir(subject_path) and subject_folder.startswith('sub'):
        
        # le sujet est le nom du dossier
        subject = subject_folder.lower()

        # Lire et concaténer les fichiers BDF pour chaque sujet
        # (ne pas prendre les fichiers systèmes commençant par un point venant du Mac)
        bdf_files = [os.path.join(subject_path, f) for f in os.listdir(subject_path) if f.endswith('.bdf') and not(f.startswith('.'))]
        raw_list = [mne.io.read_raw_bdf(bdf_file, preload=True) for bdf_file in bdf_files]
        # raw_combined = mne.concatenate_raws(raw_list)

        num_file = 0

        scan_tsv_content = []

        for run_index, bdf_file in enumerate(bdf_files, start=1):

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

            # Créer un chemin BIDS unique pour chaque sujet
            bids_path = BIDSPath(subject=subject, session=session, run=run,
                                 datatype='eeg', task=task, root=out_path)
        
            # Écrire les données combinées en format BIDS
            write_raw_bids(raw_list[num_file], bids_path=bids_path, allow_preload=True, format='BDF')

            num_file = num_file + 1

            acq_time = datetime.now().isoformat()
            scan_tsv_content.append(f"eeg/sub-{subject}_ses-{session}_task-{task}_run-{run}_eeg.bdf\t{acq_time}")
                    
            # Créer le fichier JSON pour le run
            json_path = bids_path.copy().update(extension='.json')
            json_content = {
                "TaskName": task,
                "RunNumber": run_index,
                "RunDescription": f'session: {session} condition, run: nb. {run_index} desc "{run_desc}"'
            }
            with open(json_path, 'w') as f:
                json.dump(json_content, f, indent=4)
                
        # Créer le fichier scans.tsv
        scans_tsv_path = os.path.join(bids_path.directory, f"sub-{subject}_ses-{session}_scans.tsv")
        with open(scans_tsv_path, 'w') as f:
            f.write("filename\tacq_time\n")
            f.write("\n".join(scan_tsv_content))
