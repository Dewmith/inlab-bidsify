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
import csv
import os
import json
import sys
import tempfile
import warnings
from datetime import datetime
from mne_bids import BIDSPath, write_raw_bids
import mne
import tomlkit
from tomlkit.exceptions import ParseError

# Add types here once their MNE and MNE-BIDS mappings are supported and tested.
EXTERNAL_CHANNEL_TYPES = frozenset({"eog", "ecg", "emg", "gsr", "resp", "misc"})


def parse_external_channels(external):
    """Normalize external-channel tables (or legacy names) without mutating input."""
    if not isinstance(external, list):
        raise ValueError("[CHANNELS].external must be a TOML array of tables or channel names.")
    normalized = []
    seen_names = set()
    for index, entry in enumerate(external, 1):
        field = f"[CHANNELS].external entry {index}"
        if isinstance(entry, str):
            entry = {"name": entry}
        if not isinstance(entry, dict):
            raise ValueError(f"{field} must be a table or a channel name.")
        name = entry.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"{field}.name is required and must be a nonblank string.")
        name = name.strip()
        if name.casefold() in seen_names:
            raise ValueError(f"{field}: duplicate external channel {name!r}.")
        seen_names.add(name.casefold())

        channel_type = entry.get("type", "misc")
        if not isinstance(channel_type, str) or channel_type.strip().lower() not in EXTERNAL_CHANNEL_TYPES:
            raise ValueError(
                f"{field}.type {channel_type!r} is not a supported MNE channel type. "
                f"Choose from: {', '.join(sorted(EXTERNAL_CHANNEL_TYPES))}."
            )
        description = entry.get("description")
        if description is not None:
            if not isinstance(description, str):
                raise ValueError(f"{field}.description must be a string.")
            description = description if description.strip() else None
            # MNE-BIDS reads TSV fields without CSV quoting, so embedded field
            # or row separators cannot be represented safely.
            if description and any(character in description for character in "\t\r\n"):
                raise ValueError(f"{field}.description must be a single line without tabs.")
        normalized.append({"name": name, "type": channel_type.strip().lower(), "description": description})
    return normalized


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


def validate_channel_config(config):
    """Require a known electrode layout and an optional external-channel list."""
    channels = config.get("CHANNELS")
    if not isinstance(channels, dict):
        raise ValueError("[CHANNELS] is required and must be a TOML table.")
    montage = channels.get("montage")
    if not isinstance(montage, str) or not montage.strip():
        raise ValueError("[CHANNELS].montage must name an MNE built-in montage.")
    montage = montage.strip()
    if montage not in mne.channels.get_builtin_montages():
        raise ValueError(
            f"Unknown [CHANNELS].montage {montage!r}. Choose an MNE built-in "
            "montage matching the recording's electrode layout; list available "
            "names with mne.channels.get_builtin_montages()."
        )
    external = parse_external_channels(channels.get("external", []))
    return {**channels, "montage": montage, "external": external}


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
    normalized["CHANNELS"] = validate_channel_config(config)
    return normalized


def classify_channels(raw, montage, external, recording_name):
    """Set signal types using an electrode-name reference, preserving triggers."""
    external = parse_external_channels(external)
    eeg_names = {name.strip().casefold() for name in montage.ch_names}
    external_by_name = {channel["name"].casefold(): channel for channel in external}
    recorded_names = {name.strip().casefold() for name in raw.ch_names}
    channel_types = {}
    automatic_misc = []
    trigger_conflicts = []

    for name, current_type in zip(raw.ch_names, raw.get_channel_types()):
        normalized_name = name.strip().casefold()
        if current_type == "stim":
            if normalized_name in external_by_name:
                trigger_conflicts.append(name)
            continue
        if normalized_name in external_by_name:
            channel_types[name] = external_by_name[normalized_name]["type"]
        elif normalized_name in eeg_names:
            channel_types[name] = "eeg"
        else:
            channel_types[name] = "misc"
            automatic_misc.append(name)

    if "eeg" not in channel_types.values():
        raise ValueError(
            f"Recording {recording_name!r} has no EEG channels after classification. "
            "Check [CHANNELS].montage against the recording's channel names and "
            "check that [CHANNELS].external does not exclude all EEG channels."
        )

    # MISC and some sensor types have different MNE units. Only metadata changes; the BDF's
    # original units remain available to MNE-BIDS and samples are not modified.
    raw.set_channel_types(channel_types, on_unit_change="ignore")

    messages = []
    if automatic_misc:
        messages.append(
            "Channels absent from the configured montage were automatically set "
            f"to MISC: {', '.join(automatic_misc)}."
        )
    absent_external = [
        channel["name"] for name, channel in external_by_name.items()
        if name not in recorded_names
    ]
    if absent_external:
        messages.append(
            f"Configured external channels are absent: {', '.join(absent_external)}."
        )
    if trigger_conflicts:
        messages.append(
            "Channels listed as external are recognized triggers and were kept "
            f"as TRIG: {', '.join(trigger_conflicts)}."
        )
    if messages:
        warnings.warn(
            f"Recording {recording_name!r}: {' '.join(messages)}",
            UserWarning,
            stacklevel=2,
        )


def update_channel_descriptions(bids_path, external):
    """Replace only explicitly configured descriptions in MNE-BIDS' channels TSV."""
    descriptions = {
        channel["name"].casefold(): channel["description"]
        for channel in parse_external_channels(external) if channel["description"] is not None
    }
    if not descriptions:
        return

    channels_path = bids_path.copy().update(suffix="channels", extension=".tsv").fpath
    with open(channels_path, encoding="utf-8-sig", newline="") as stream:
        # Keep every value as text, including units, n/a, and numeric formatting.
        rows = list(csv.reader(stream, delimiter="\t", quoting=csv.QUOTE_NONE))
    if not rows or "name" not in rows[0] or "description" not in rows[0]:
        raise ValueError(f"Channels TSV {str(channels_path)!r} must contain name and description columns.")
    header = rows[0]
    if len(set(header)) != len(header) or any(len(row) != len(header) for row in rows[1:]):
        raise ValueError(f"Channels TSV {str(channels_path)!r} has malformed columns or rows.")
    name_index, description_index = header.index("name"), header.index("description")
    changed = False
    for row in rows[1:]:
        description = descriptions.get(row[name_index].strip().casefold())
        if description is not None and row[description_index] != description:
            row[description_index] = description
            changed = True
    if not changed:
        return

    # Replace atomically so a failed write leaves the generated sidecar intact.
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8-sig", newline="", dir=channels_path.parent,
            suffix=".tmp", delete=False,
        ) as stream:
            temporary_path = stream.name
            writer = csv.writer(stream, delimiter="\t", quoting=csv.QUOTE_NONE, quotechar=None, lineterminator="\n")
            writer.writerows(rows)
        os.replace(temporary_path, channels_path)
    finally:
        if temporary_path is not None and os.path.exists(temporary_path):
            os.unlink(temporary_path)


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
    montage = mne.channels.make_standard_montage(config["CHANNELS"]["montage"])

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

                # Read channel metadata without preloading recording samples.
                recording_path = os.path.join(subject_path, bdf)
                raw = mne.io.read_raw_bdf(recording_path, preload=False)
                classify_channels(raw, montage, config["CHANNELS"]["external"], recording_path)

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
                update_channel_descriptions(bids_path, config["CHANNELS"]["external"])

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
