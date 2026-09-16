# BDF to BIDS Converter

This Python script converts EEG recordings in **BioSemi BDF format** into a **BIDS-compliant dataset** using [MNE-BIDS](https://mne.tools/mne-bids/).

It reads a configuration file (`bids_configurator.txt`) which controls:
- Input/output paths
- Task and run labeling based on keywords found in filenames
- Optional metadata descriptions

## 📦 Installation

This project uses [`uv`](https://github.com/astral-sh/uv) for dependency and virtual environment management. To get started:

Install `uv` (if not already installed) using one of the following methods:

**On Linux/macOS:**

```bash
curl -Ls https://astral.sh/uv/install.sh | sh
```

**On Windows (PowerShell):**

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**From [PyPI](https://pypi.org/project/uv/) with pip:**

```bash
pip install uv
```

See the [official uv installation guide](https://docs.astral.sh/uv/getting-started/installation/) for details.

Create a virtual environment :

```bash
uv venv .venv_bidsif --python 3.10.0
```

Activate the virtual environment using the command for your shell:

**On Linux/macOS:**

```bash
source .venv_bidsif/bin/activate
```

**On Windows (PowerShell):**

```powershell
.\.venv_bidsif\Scripts\Activate.ps1
```

**On Windows (Command Prompt):**

```bat
.venv_bidsif\Scripts\activate.bat
```

Install dependencies from `requirements.txt`

```bash
uv pip install -r requirements.txt
```

## 🚀 Usage

1. Place your `.bdf` EEG files in subject-specific folders inside the directory defined as `input_path`.
2. Create a `bids_configurator.txt` file (see example below).
3. Run the conversion script:

Activate the virtual environment if it is not activated (see above) and execute:
```bash
python bidsify.py
```

Converted data will be saved to the BIDS directory defined by `output_path`.

## 📂 Example input data structure

For `input_path = /path/to/raw_data`, organize your recordings as follows:

```text
raw_data/
├── participant_001/
│   ├── rest.bdf
│   ├── block1.bdf
│   └── stim.bdf
├── participant_002/
│   ├── rest.bdf
│   ├── block1.bdf
    ├── block2.bdf
│   └── stim.bdf
```

- Each folder directly inside `raw_data` represents one participant. Folder names are sorted and assigned BIDS IDs: `participant_001` becomes `sub-01`, and `participant_002` becomes `sub-02` in this example.
- Place `.bdf` files directly inside each participant folder; nested folders are not scanned.
- With the configuration below, filenames containing `rest` map to task `restingtask`, and filenames containing `stim` map to task `stimtask`.
- `block1` and `block2` map to `run-01` and `run-02`, respectively. Filename keyword matching is case-sensitive.

## 📝 Example `bids_configurator.txt`

```ini
[DEFAULT]
input_path = /path/to/raw_data
output_path = /path/to/bids_dataset

[task_restingtask]
keywords = rest, baseline
description = Participants rest with eyes closed.

[task_stimtask]
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
* Task and run names are extracted from the section headers:
  e.g. `[task_restingtask]` → one task `restingtask` in filenames and BIDS paths
  `[run_1]` → one run `run-01` in filenames and BIDS paths
* Infers **task** and **run** labels based on filename keywords (e.g. ParticipantID_rest.bdf will be detected and saved in BIDS as a `restingtask`)


## 📁 Output

* BIDS-compliant dataset
* `dataset_description.json` (updated with user metadata)
* `participants.tsv` lists each participant and their original folder name
* For each recording:

  * Raw data is copied to `sub-XX/ses-YY/eeg/`
  * JSON Sidecar files are created `*_eeg.json` including:

    * `"OriginalFilename"` — the original `.bdf` filename
    * `"TaskDescription"` — if defined in config
    * `"RunDescription"` — if defined in config

## ⚠️ Notes

* Task and run keywords must not overlap across sections.
* Run identifiers **must** be numeric and consecutive (`run_1`, `run_2`, ...)
* The script will only update `dataset_description.json` if it already exists — it will not create one from scratch.
* Only `.bdf` files are supported.

## 📄 License

This project is licensed under the **GNU General Public License v3.0 (GPLv3)**.
See the [LICENSE](./LICENSE) file for details.
