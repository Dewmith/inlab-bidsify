# BDF to BIDS Converter

This Python script converts EEG recordings in **BioSemi BDF format** into a **BIDS-compliant dataset** using [MNE-BIDS](https://mne.tools/mne-bids/).

It reads a configuration file (`bids_configurator.txt`) which controls:
- Input/output paths
- Task and run labeling based on keywords found in filenames
- Optional metadata descriptions
- Dataset-wide metadata

## 📦 Installation

This project uses [`uv`](https://github.com/astral-sh/uv) for dependency and virtual environment management. To get started:

Install `uv` (if not already installed):

```bash
curl -Ls https://astral.sh/uv/install.sh | sh
````

Create a virtual environment and install dependencies from `requirements.txt`:

```bash
uv venv_bidsif
uv pip install -r requirements.txt
```

## 🚀 Usage

1. Place your `.bdf` EEG files in subject-specific folders inside the directory defined as `input_path`.
2. Create a `bids_configurator.txt` file (see example below).
3. Run the conversion script:

Activate the virtual environment:

```bash
source .venv_bidsif/bin/activate    # Linux/macOS
.venv_bidsif\Scripts\activate       # Windows
```
and execute:
```bash
python bidsify.py
```

Converted data will be saved to the BIDS directory defined by `output_path`.

## 📝 Example `bids_configurator.txt`

```ini
[DEFAULT]
input_path = /path/to/raw_data
output_path = /path/to/bids_dataset

[task_rest]
keywords = rest, baseline
description = Participants rest with eyes closed.

[task_stim]
keywords = stim
description = Visual stimuli presented every 2 seconds.

[run_1]
keywords = block1, run1
description = First run before break.

[run_2]
keywords = block2, run2
description = Second run after break.


[DATASET_DESCRIPTION]
Name = ExampleDataset
BIDSVersion = 1.8.0
Authors = Alice Dupont, John Smith
Acknowledgements = Thanks to all participants
Funding = Funded by the ANR project
ReferencesAndLinks = https://example.org
DatasetType = raw
```

## ⚙️ Features

* Automatically builds a BIDS-compliant folder structure
* Detects **sessions** based on `.bdf` file creation date
* Infers **task** and **run** labels based on filename keywords
* Task and run names are extracted from the section headers:
  e.g. `[task_rest]` → `task-rest` in filenames and BIDS paths
  `[run_1]` → `run-01` in filenames and BIDS paths

* Run identifiers **must** be numeric and consecutive (`run_1`, `run_2`, ...)
* Generates:

## 📁 Output

* BIDS-compliant folder
* `participants.tsv` lists each participant and their original folder name
* For each recording:

  * Raw data is copied to `sub-XX/ses-YY/eeg/`
  * JSON Sidecar files are created `*_eeg.json` including:

    * `"OriginalFilename"` — the original `.bdf` filename
    * `"TaskDescription"` — if defined in config
    * `"RunDescription"` — if defined in config

* `dataset_description.json` (updated with user metadata)

## ⚠️ Notes

* Task and run keywords must not overlap across sections.
* The script will only update `dataset_description.json` if it already exists — it will not create one from scratch.
* Only `.bdf` files are supported.

## 👨‍💻 Author

Developed by [A.-Sophie Dubarry](mailto:anne-sophie.dubarry@univ-amu.fr) based on previous versions (Arnaud Weill & Simon Moré)
