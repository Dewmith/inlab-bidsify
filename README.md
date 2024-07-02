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

A solution needs to be defined to collect meteadata (eLabW? standalone tool?)
