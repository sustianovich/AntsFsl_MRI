import nipype.interfaces.fsl as fsl
import nipype.interfaces.ants as ants
from nipype import Node, Workflow, MapNode
from os.path import abspath

# Input file paths
patient_01 = '/home/sus/Documents/VS_CODE/AntsFsl_MRI_github/AntsFsl_MRI/data/ds000030/sub-10159/anat/sub-10159_T1w.nii.gz'
patient_02 = '/home/sus/Documents/VS_CODE/AntsFsl_MRI_github/AntsFsl_MRI/data/ds000030/sub-10171/anat/sub-10171_T1w.nii.gz'
input_files = [patient_01, patient_02]  # Add paths to your subject images
output_dir = '/home/sus/Documents/VS_CODE/AntsFsl_MRI_github/AntsFsl_MRI/output'
mni_template = '/home/sus/Documents/VS_CODE/AntsFsl_MRI_github/AntsFsl_MRI/data/template/MNI152_T1_1mm_brain.nii.gz'

# Create Nodes
bet = MapNode(fsl.BET(frac=0.3), name='bet', iterfield=['in_file'])
segmentation = MapNode(fsl.FAST(), name='segmentation', iterfield=['in_files'])

# Ensure RegistrationSynQuick has iterfield set for moving_image
registration = MapNode(ants.RegistrationSynQuick(transform_type='s',
                                                 fixed_image=mni_template),
                       name='registration',
                       iterfield=['moving_image'])

# Workflow
wf = Workflow(name='nucleus_extraction', base_dir=output_dir)

# Connect nodes
wf.connect([
    (bet, segmentation, [('out_file', 'in_files')]),
    # Ensure moving_image is set from the output of a previous node
    (segmentation, registration, [('restored_image', 'moving_image')])
])

# Set input files directly on the bet node
bet.inputs.in_file = input_files

# Run the workflow
wf.run('MultiProc', plugin_args={'n_procs': 2})
