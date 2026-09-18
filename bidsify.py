# =============================================================================
# This function is part of the BIDSIF project
#  
# This software is distributed under the terms of the GNU General Public License
# as published by the Free Software Foundation. Further details on the GPLv3
# license can be found at http://www.gnu.org/copyleft/gpl.html.
#  
# FOR RESEARCH PURPOSES ONLY. THE SOFTWARE IS PROVIDED "AS IS," AND IN THE
# HOPE THAT IT WILL BE USEFUL BUT WITHOUT ANY WARRANTY, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO WARRANTIES OF MERCHANTABILITY AND FITNESS FOR 
# A PARTICULAR PURPOSE, NOR DO THEY ASSUME ANY LIABILITY OR RESPONSIBILITY
# FOR THE USE OF THIS SOFTWARE.
# 
# =============================================================================
# Authors: A.-Sophie Dubarry

import argparse
import os
import json
import sys
from datetime import datetime
from mne_bids import BIDSPath, write_raw_bids
import mne
import tomlkit
from tomlkit.exceptions import ParseError

# Read conversion rules and metadata from the configuration file
def read_config(config_file):
    """Read and validate a TOML configuration as ordinary Python values."""
    if os.path.splitext(os.fspath(config_file))[1].lower() != ".toml":
        raise ValueError("Configuration files must use the .toml extension.")
    try:
        with open(config_file, encoding="utf-8") as config_stream:
            config = tomlkit.parse(config_stream.read()).unwrap()
    except (OSError, UnicodeError, ParseError) as e:
        raise ValueError(f"Cannot read configuration file '{config_file}': {e}") from e

    try:
        return validate_config(config)
    except ValueError as e:
        raise ValueError(f"Invalid configuration file '{config_file}': {e}") from e

# Check for conflicting keywords across config sections
# This helps avoid ambiguity in how files are categorized
def check_conflicting_keywords(config):
    keyword_map = {}
    for section, values in config.items():
        if section.startswith(("task_", "run_")):
            for keyword in values["keywords"]:
                if keyword in keyword_map:
                    raise ValueError(f"Keyword '{keyword}' found in both '{keyword_map[keyword]}' and '{section}'.")
                keyword_map[keyword] = section

def validate_dataset_type(config):
    """Return the normalized raw dataset type or reject incompatible metadata."""
    metadata = config.get("DATASET_DESCRIPTION", {})
    if not isinstance(metadata, dict):
        raise ValueError("[DATASET_DESCRIPTION] must be a TOML table.")
    configured_value = metadata.get("DatasetType", "raw")
    if not isinstance(configured_value, str) or configured_value.strip() != "raw":
        raise ValueError(
            f"Invalid DatasetType {configured_value!r} in [DATASET_DESCRIPTION]. "
            'This converter writes raw EEG BIDS datasets; set DatasetType = "raw" '
            "(or omit it)."
        )
    return configured_value.strip()


def validate_config(config):
    """Validate conversion settings before any output is written."""
    validate_dataset_type(config)
    metadata = config.get("DATASET_DESCRIPTION", {})
    try:
        json.dumps(metadata, allow_nan=False)
    except (TypeError, ValueError) as e:
        raise ValueError(
            f"[DATASET_DESCRIPTION] values must be compatible with JSON: {e}"
        ) from e

    normalized = dict(config)
    run_numbers = []
    for section, values in config.items():
        if not section.startswith(("task_", "run_")):
            continue
        if not isinstance(values, dict):
            raise ValueError(f"[{section}] must be a TOML table.")
        keywords = values.get("keywords")
        if (
            not isinstance(keywords, list)
            or not keywords
            or any(not isinstance(keyword, str) or not keyword.strip() for keyword in keywords)
        ):
            raise ValueError(
                f"[{section}].keywords must be a nonempty TOML array of nonblank strings."
            )
        if "description" in values and not isinstance(values["description"], str):
            raise ValueError(f"[{section}].description must be a string.")
        normalized[section] = {**values, "keywords": [keyword.strip() for keyword in keywords]}

        if section.startswith("run_"):
            suffix = section.removeprefix("run_")
            if not suffix.isascii() or not suffix.isdecimal() or suffix != str(int(suffix)):
                raise ValueError("Run table names must use run_1, run_2, ...")
            run_numbers.append(int(suffix))

    if sorted(run_numbers) != list(range(1, len(run_numbers) + 1)):
        raise ValueError("Run numbers must be consecutive starting from 1.")
    check_conflicting_keywords(normalized)
    return normalized

def update_dataset_description(output_path, config):
    """
    Update or add entries to dataset_description.json using values from the
    [DATASET_DESCRIPTION] section of the config file.
    """
    dataset_type = validate_dataset_type(config)
    dataset_description_path  = os.path.join(output_path, "dataset_description.json")
    if not os.path.exists(dataset_description_path):
        print("Warning: dataset_description.json not found. Skipping update.")
        return

    with open(dataset_description_path, 'r') as f:
        dataset_description = json.load(f)

    # Replace or add keys from the config file
    dataset_description.update(config.get("DATASET_DESCRIPTION", {}))
    dataset_description["DatasetType"] = dataset_type
        
    with open(dataset_description_path, 'w') as f:
        json.dump(dataset_description, f, indent=4)

def validate_input_path(input_path):
    """Require an existing input directory before reading config or converting."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input path '{input_path}' not found.")
    if not os.path.isdir(input_path):
        raise NotADirectoryError(f"Input path '{input_path}' is not a directory.")


# Create the BIDS structure using logic for auto-sessions and config-based tasks
# Each session is automatically created based on the file creation date
# Task is inferred from config, and run is automatically enumerated
# A JSON sidecar file is created for each run recording the original filename
def create_bids_structure(input_path, output_path, config):
    validate_input_path(input_path)
    config = validate_config(config)

    if os.path.exists(output_path) and not os.path.isdir(output_path):
        raise NotADirectoryError(f"Output path '{output_path}' is not a directory.")
    os.makedirs(output_path, exist_ok=True)

    # Map tasks from config
    tasks = {t: values["keywords"] for t, values in config.items() if t.startswith("task_")}

    # Map runs from config
    runs_config = {int(r.split("_")[1]): values["keywords"] for r, values in config.items() if r.startswith("run_")}

    # Map subject folders to standardized BIDS IDs
    subject_folders = sorted([f for f in os.listdir(input_path) if os.path.isdir(os.path.join(input_path, f))])
    subject_map = {folder: f"{i+1:02}" for i, folder in enumerate(subject_folders)}

    # Write participants.tsv file for subject metadata
    participants_file = os.path.join(output_path, "participants.tsv")
    with open(participants_file, 'w') as pf:
        pf.write("participant_id\toriginal_folder\n")
        for original, sub_id in subject_map.items():
            pf.write(f"sub-{sub_id}\t{original}\n")

    # Process each subject folder
    for original_folder, sub_id in subject_map.items():
        subject_path = os.path.join(input_path, original_folder)
        bdf_files = [f for f in os.listdir(subject_path) if f.lower().endswith(".bdf") and not f.startswith("._")]
        
        # Group BDF files by file creation date (one session per day)
        date_grouped = {}
        for bdf in bdf_files:
            full_path = os.path.join(subject_path, bdf)
            creation_date = datetime.fromtimestamp(os.path.getmtime(full_path)).strftime("%Y%m%d")
            date_grouped.setdefault(creation_date, []).append(bdf)
        # Iterate over sessions (per date)
        for session_idx, (session_date, files) in enumerate(sorted(date_grouped.items()), 1):
            session_label = f"{session_idx:02}"
            run_counter = 1
            for bdf in sorted(files):
                task_label = None
                for task_key, task_keywords in tasks.items():
                    if any(k in bdf for k in task_keywords):
                        task_label = task_key.split("_", 1)[1]
                        break

                matched_run = None
                for run_num, run_keywords in runs_config.items():
                    if any(k in bdf for k in run_keywords):
                        matched_run = run_num
                        break

                run_label = f"{matched_run:02}" if matched_run else f"{run_counter:02}"
                run_counter += 1 if not matched_run else 0

                # Read raw BDF file with preload
                raw = mne.io.read_raw_bdf(os.path.join(subject_path, bdf), preload=False)

                # Create BIDS path with session, task, and run
                bids_path = BIDSPath(
                    subject=sub_id,
                    session=session_label,
                    task=task_label if task_label else "task",
                    run=run_label,
                    datatype="eeg",
                    extension=".bdf",
                    root=output_path
                )

                # Write data to BIDS format
                write_raw_bids(raw, bids_path, overwrite=True)

                # Save original BDF filename and task/run descriptions to JSON sidecar
                json_path = bids_path.copy().update(extension='.json').fpath
                with open(json_path, 'r+') as jf:
                    metadata = json.load(jf)
                    metadata["OriginalFilename"] = bdf

                    # Add task description if available
                    task_section = f"task_{task_label}"
                    if "description" in config.get(task_section, {}):
                        metadata["TaskDescription"] = config[task_section]["description"]

                    # Add run description if matched_run is not None and a description exists
                    if matched_run:
                        run_section = f"run_{matched_run}"
                        if "description" in config.get(run_section, {}):
                            metadata["RunDescription"] = config[run_section]["description"]

                    jf.seek(0)
                    json.dump(metadata, jf, indent=4)
                    jf.truncate()

    # Update dataset_description.json using the configured metadata
    update_dataset_description(output_path, config)

# Main entry point to read config and launch processing
def main(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Convert BioSemi BDF recordings to BIDS using bids_configurator.toml "
            "in the input directory."
        )
    )
    parser.add_argument(
        "--input", required=True, metavar="DIRECTORY",
        help="Existing directory containing bids_configurator.toml and subject folders with BDF recordings.",
    )
    parser.add_argument(
        "--output", required=True, metavar="DIRECTORY",
        help="BIDS output directory; created if it does not exist.",
    )
    args = parser.parse_args(argv)
    config_file = os.path.join(args.input, "bids_configurator.toml")

    try:
        validate_input_path(args.input)
        config = read_config(config_file)
        create_bids_structure(args.input, args.output, config)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
