import subprocess
import os

# pip install sentry-sdk
# curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.38.0/install.sh | bash
# sudo apt  install curl
# nvm install node 
# npm install -g bids-validator

def run_fmriprep(bids_dir, output_dir, work_dir, participant_label, freesurfer_license):
    # Construct the fMRIPrep command as a string
    fmriprep_cmd = (
        f"fmriprep {bids_dir} {output_dir} participant "
        f"--participant-label {participant_label} "
        f"--fs-license-file {freesurfer_license} "
        f"--work-dir {work_dir} "
        # Add any other desired fMRIPrep options here
    )
    
    # Run the command
    subprocess.run(fmriprep_cmd, shell=True, check=True)

# Paths (replace with your actual paths)
bids_dir = 'data/ds000030'
output_dir = "data/ds000030/jobs/out"
work_dir = "data"
participant_label = "sub-10159"  # Replace with the participant's label
freesurfer_license = ".freesurfer_license/license.txt"

# Run fMRIPrep
run_fmriprep(bids_dir, output_dir, work_dir, participant_label, freesurfer_license)

