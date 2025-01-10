# BIDSIF

## Project decription

This code aims at bidsifying the EEG data recorded at CRPN.
The code was developed by S. Moré and A.-S Dubarry

## Ressource

Documentation sur BIDS EEG : https://bids-specification.readthedocs.io/en/stable/modality-specific-files/electroencephalography.html

[MNE BIDS](https://mne.tools/mne-bids/stable/index.html) is used to create a BIDS-compatible directory of EEG or iEEG data.
MNE can load different data format :

BrainVision (.vhdr, .vmrk, .eeg)
European data format (.edf)
BioSemi data format (.bdf)
General data format (.gdf)
Neuroscan CNT (.cnt)
EGI simple binary (.egi)
EGI MFF (.mff)
EEGLAB files (.set, .fdt)
Nicolet (.data)
eXimia EEG data (.nxe)
Persyst EEG data (.lay, .dat)
Nihon Kohden EEG data (.eeg, .21e, .pnt, .log)
XDF data (.xdf, .xdfz)
see here for more details : see here https://mne.tools/stable/auto_tutorials/io/20_reading_eeg_data.html#sphx-glr-auto-tutorials-io-20-reading-eeg-data-py

**Warning! **
MNE-BIDS create good file organization, and create metadatafiles required for [BIDS-validator](https://bids-standard.github.io/bids-validator/), but some metadata are very poor and incomplete : just what's needed to validate.
THat's why it generate warnings from BIDS-validator.

A dataset generated with BIDS-MNE without metadata completed by humans can't be reused( critical informations will be missing).

# What's next?

In the current state of the project humans need to complete

-description.json file (taskname, task description, manufacturer, software (version),powerline frequency,eegground,eeg reference)
-participants.json and participants.tsv
-readme

A solution needs to be defined to collect meteadata (standalone tool)

# How to install et execute

Under Linux, in the project folder:

- Install pip:
  `sudo apt update sudo apt install python3-pip`
- Install the module for python virtual environments:
  sudo apt install python3-venv` python3 -m venv .penv3.12` (for Python version 3.12)
  `source .penv3.12/bin/activate`
- Once the virtual environment has been activated, install mne:
  `pip install mne pip install mne_bids`
- Modify the “bids_configurator.txt” file for the “input_path” (subNN folder containing .bdf files) and “out_path” (bids folder) variables.
  *WARNING: paths must not be relative!*

To execute the code:`python3 create_bids_fron_n_bdf.py`

For Windows and Mac, the procedure should be roughly similar.
