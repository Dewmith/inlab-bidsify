import os
import mne
import shutil
import pandas as pd

def create_bids_structure(input_path, output_path, config):
    """
    Creates BIDS structure from the raw EEG data found in input_path, according to the configuration.
    """
    # Ensure the output path exists
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # Create a dictionary to store subject metadata
    participants_data = []

    # Get the subject directories inside input_path
    subject_dirs = [sub_dir for sub_dir in os.listdir(input_path) if os.path.isdir(os.path.join(input_path, sub_dir)) and sub_dir.startswith("sub-")]

    for subject in subject_dirs:
        print(f"Processing {subject}...")

        subject_input_path = os.path.join(input_path, subject)
        
        # Add subject metadata to participants_data
        participants_data.append({
            'participant_id': subject,
            'age': 'unknown',  # Placeholder, adjust as needed based on available data
            'sex': 'unknown',  # Placeholder, adjust as needed based on available data
            'session_id': 'unknown'  # Placeholder for session-specific info
        })

        # Iterate over the sessions, tasks, and runs from config
        for section in config.sections():
            if section.startswith("session_"):
                session_label = config.get(section, "label")
                session_keywords = config.get(section, "keywords").split(",")
                
                # Check if session's keywords are in the folder or filename (based on your needs)
                if any(keyword in subject for keyword in session_keywords):
                    session_folder = os.path.join(output_path, session_label)
                    if not os.path.exists(session_folder):
                        os.makedirs(session_folder)

                    # Now check tasks within the session
                    for task_section in config.sections():
                        if task_section.startswith("task_"):
                            task_label = config.get(task_section, "label")
                            task_keywords = config.get(task_section, "keywords").split(",")
                            
                            # Look for task in filenames (similar to session handling)
                            for filename in os.listdir(subject_input_path):
                                if any(keyword in filename for keyword in task_keywords):
                                    # Handle the raw data (BDF files)
                                    raw_bdf_path = os.path.join(subject_input_path, filename)
                                    if os.path.exists(raw_bdf_path):
                                        raw_data = mne.io.read_raw_bdf(raw_bdf_path, preload=True)

                                        # Save the data in BIDS format (using raw_bdf, without converting to FIF)
                                        bids_filename = os.path.join(session_folder, f"{subject}_{session_label}_{task_label}_run-01.bdf")
                                        raw_data.save(bids_filename, overwrite=True)
                                    else:
                                        print(f"Warning: {raw_bdf_path} not found")
                else:
                    print(f"Session {session_label} does not match subject folder: {subject}")

    # Create participants.tsv file
    participants_df = pd.DataFrame(participants_data)
    participants_df.to_csv(os.path.join(output_path, "participants.tsv"), sep='\t', index=False)
    print(f"Created participants.tsv at {output_path}")

