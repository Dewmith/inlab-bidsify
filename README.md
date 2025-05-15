# BIDS Converter for EEG

This script automatically converts EEG recordings in `.bdf` format into a standardized [BIDS](https://bids.neuroimaging.io/) structure using the [MNE-BIDS](https://mne.tools/mne-bids/) library. It relies on a configuration file (`bids_configurator.txt`) to define paths, tasks, runs, and dataset metadata.

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

(Optionally) activate the environment:

```bash
source .venv_bidsif/bin/activate    # Linux/macOS
.venv_bidsif\Scripts\activate       # Windows
```

## 🚀 Usage

1. Place your `.bdf` EEG files in subject-specific folders inside the directory defined as `input_path`.
2. Create a `bids_configurator.txt` file (see example below).
3. Run the conversion script:

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

[task_stim]
keywords = stim, trial

[run_1]
keywords = session1, run1

[run_2]
keywords = session2, run2

[DATASET_DESCRIPTION]
Name = ExampleDataset
BIDSVersion = 1.8.0
Authors = Alice Dupont, John Smith
Acknowledgements = Thanks to all participants
Funding = Funded by the ANR project
ReferencesAndLinks = https://example.org
DatasetType = raw
```

## 📂 Features

* Automatically builds a BIDS-compliant folder structure
* Detects sessions based on `.bdf` file creation date
* Infers task and run labels based on filename keywords
* Generates:

  * `participants.tsv` (maps original folder names to BIDS subject IDs)
  * `dataset_description.json` (updated with user metadata)
  * JSON sidecar files per run including the original filename

## ⚠️ Notes

* Task and run keywords must not overlap across sections.
* The script will only update `dataset_description.json` if it already exists — it will not create one from scratch.
* Only `.bdf` files are supported.

## 👨‍💻 Author

Developed by [A.-Sophie Dubarry](mailto:anne-sophie.dubarry@univ-amu.fr) based on previous versions (Arnaud Weill & Simon Moré)
