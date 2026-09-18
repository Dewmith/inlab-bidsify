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
import configparser
import json
import sys
from datetime import datetime
from mne_bids import BIDSPath, write_raw_bids
import mne

# Read conversion rules and metadata from the configuration file
def read_config(config_file):
    config = configparser.ConfigParser()
    config.optionxform = str  # Preserve case for keys
    try:
        with open(config_file, encoding="utf-8") as config_stream:
            config.read_file(config_stream)
    except (OSError, UnicodeError, configparser.Error) as e:
        raise ValueError(f"Cannot read configuration file '{config_file}': {e}") from e

    # Legacy path defaults must not be inherited by dataset metadata.
    config.remove_option(config.default_section, "input_path")
    config.remove_option(config.default_section, "output_path")

    return config

# Check for conflicting keywords across config sections
# This helps avoid ambiguity in how files are categorized
def check_conflicting_keywords(config):
    keyword_map = {}
    for section in config.sections():
        if 'keywords' in config[section]:
            keywords = [k.strip() for k in config.get(section, "keywords").split(',')]
            for keyword in keywords:
                if keyword in keyword_map:
                    raise ValueError(f"Keyword '{keyword}' found in both '{keyword_map[keyword]}' and '{section}'.")
                keyword_map[keyword] = section
 
def parse_value(value):
    value = value.strip().strip('"').strip("'")

    if "," in value:
        return [v.strip() for v in value.split(",") if v.strip()]

    return value

def validate_dataset_type(config):
    """Return the normalized raw dataset type or reject incompatible metadata."""
    configured_value = config.get("DATASET_DESCRIPTION", "DatasetType", fallback="raw")
    value = configured_value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        value = value[1:-1].strip()
    if value != "raw":
        raise ValueError(
            f"Invalid DatasetType {configured_value!r} in [DATASET_DESCRIPTION]. "
            "This converter writes raw EEG BIDS datasets; set DatasetType = raw "
            "(or omit it)."
        )
    return value

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
    if config.has_section("DATASET_DESCRIPTION"):
        for key, value in config.items("DATASET_DESCRIPTION"):
            if key != "DatasetType":
                dataset_description[key] = parse_value(value)
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
    validate_dataset_type(config)

    if os.path.exists(output_path) and not os.path.isdir(output_path):
        raise NotADirectoryError(f"Output path '{output_path}' is not a directory.")
    os.makedirs(output_path, exist_ok=True)

    # Ensure keywords in config are not reused across different sections
    check_conflicting_keywords(config)

    # Map tasks from config
    tasks = {t: config.get(t, "keywords").split(',') for t in config.sections() if t.startswith("task_")}

    # Map runs from config
    runs_config = {int(r.split("_")[1]): config.get(r, "keywords").split(',') for r in config.sections() if r.startswith("run_")}
    if runs_config and sorted(runs_config.keys()) != list(range(1, len(runs_config)+1)):
        raise ValueError("Run numbers must be consecutive starting from 1.")

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
                    if config.has_section(task_section) and config.has_option(task_section, "description"):
                        metadata["TaskDescription"] = config.get(task_section, "description")

                    # Add run description if matched_run is not None and a description exists
                    if matched_run:
                        run_section = f"run_{matched_run}"
                        if config.has_section(run_section) and config.has_option(run_section, "description"):
                            metadata["RunDescription"] = config.get(run_section, "description")

                    jf.seek(0)
                    json.dump(metadata, jf, indent=4)
                    jf.truncate()

    # Update the description-dataset.jsdon according to the config
    update_dataset_description(output_path, config)

# Main entry point to read config and launch processing
def main(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Convert BioSemi BDF recordings to BIDS using bids_configurator.txt "
            "in the input directory."
        )
    )
    parser.add_argument(
        "--input", required=True, metavar="DIRECTORY",
        help="Existing directory containing bids_configurator.txt and subject folders with BDF recordings.",
    )
    parser.add_argument(
        "--output", required=True, metavar="DIRECTORY",
        help="BIDS output directory; created if it does not exist.",
    )
    args = parser.parse_args(argv)
    config_file = os.path.join(args.input, "bids_configurator.txt")

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
