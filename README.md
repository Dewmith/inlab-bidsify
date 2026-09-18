# BDF to BIDS Converter

This Python script converts EEG recordings in **BioSemi BDF format** into a **BIDS-compliant dataset** using [MNE-BIDS](https://mne.tools/mne-bids/).

It reads `bids_configurator.txt` from the input dataset directory. This file controls:
- Task and run labeling based on keywords found in filenames
- Optional metadata descriptions

Input and output directories are supplied as command-line arguments.

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

1. Place your `.bdf` EEG files in subject-specific folders inside your input directory.
2. Copy `bids_configurator.example.txt` from this repository into your input directory, rename it to `bids_configurator.txt`, and customize its rules and metadata for your dataset (see example below).
3. Run the conversion script:

Activate the virtual environment if it is not activated (see above) and execute:
```bash
python bidsify.py --input "/path/to/raw_data" --output "/path/to/bids_dataset"
```

For example, on Windows (PowerShell), quote paths that contain spaces:

```powershell
python bidsify.py --input "C:\Data\raw recordings" --output "C:\Data\bids dataset"
```

This command reads `C:\Data\raw recordings\bids_configurator.txt` automatically.
Each dataset must have its own `bids_configurator.txt` directly inside the directory
passed to `--input`. Only that configuration is read; there is no fallback to a file
in the working directory or the code directory. The script does not create this file.

Both options are required. The input directory must exist; the output directory is
created if needed. Converted data will be saved to the directory passed to `--output`.
Relative paths are resolved from the current working directory.

Run `python bidsify.py --help` for usage information. Missing arguments or configuration,
invalid paths, and conversion failures result in a nonzero exit status.

If you have an older configuration, move it into your input dataset directory as
`bids_configurator.txt` and remove `input_path` and `output_path` from
`[DEFAULT]` (and remove that section if it is empty). These legacy defaults are
ignored; the paths must always be supplied on the command line.

## 📂 Example input data structure

For `--input "/path/to/raw_data"`, organize your recordings as follows:

```text
raw_data/
├── bids_configurator.txt
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
- The configuration file at the dataset root is not treated as a participant or recording.
- With the configuration below, filenames containing `rest` map to task `restingtask`, and filenames containing `stim` map to task `stimtask`.
- `block1` and `block2` map to `run-01` and `run-02`, respectively. Filename keyword matching is case-sensitive.

## 📝 Example `bids_configurator.txt`

```ini
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

## 🧪 Tests

With the project dependencies installed, run the CLI and configuration tests from
the project directory:

```bash
python -m unittest discover -s tests -v
```

These tests use temporary directories and do not require EEG recordings.

## 📄 License

This project is licensed under the **GNU General Public License v3.0 (GPLv3)**.
See the [LICENSE](./LICENSE) file for details.
