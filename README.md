# API data-repositories

Try to use different API to request different data repositories

targets :
- zenodo : https://zenodo.org/
- openNeuro : https://openneuro.org/
- Nakala : https://nakala.fr/
- G-node : https://gin.g-node.org/
- RechercheDataGouv : ?
- EOSC : ?


Sources : 
- https://gist.github.com/slint
- https://gist.github.com/slint/d30fc0f415300876facbbeb8a0989ab2




# MNE-BIDS

source : https://mne.tools/mne-bids/stable/index.html

MNE BIDS can be used to to create a BIDS-compatible directory of EEG or iEEG data.
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



Becareful !  
MNE-BIDS create good file organization, and create metadatafiles required for BIDS-validator, but some metadata are very poor and incomplete : just what's needed to validate. 
THat's why it generate warnings from BIDS-validator.

A dataset generated with BIDS-MNE without metadata completed by humans can't be reused( critical informations will be missing).  

Humans need to complete 
-description.json file (taskname, task description, manufacturer, software (version),powerline frequency,eegground,eeg reference)  
-participants.json and participants.tsv  
-readme
