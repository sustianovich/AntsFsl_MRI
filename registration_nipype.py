import nipype.interfaces.fsl as fsl
import nipype.interfaces.ants as ants
from nipype import Node, Workflow, MapNode
from os.path import abspath

# Input file paths
patient_01 = abspath('./data/ds000030/sub-10159/anat/sub-10159_T1w.nii.gz')
patient_02 = abspath('./data/ds000030/sub-10171/anat/sub-10171_T1w.nii.gz')
input_files = [patient_01, patient_02]  # Add paths to your subject images
output_dir = abspath('./output')
mni_template = abspath('./data/template/MNI152_T1_1mm_brain.nii.gz')

# Create Nodes
bet = MapNode(fsl.BET(frac=0.3), name='bet', iterfield=['in_file'])

segmentation = MapNode(fsl.FAST(), name='segmentation', iterfield=['in_files'])

# Create a custom registration node using SimpleITK through ANTs
registration = MapNode(ants.Registration(), name='registration', iterfield=['moving_image'])
registration.inputs.fixed_image = mni_template
registration.inputs.transforms = ['Rigid']
registration.inputs.transform_parameters = [(0.1,)]
registration.inputs.metric = ['MI']
registration.inputs.sampling_strategy = ['Regular']
registration.inputs.sampling_percentage = [0.05]
registration.inputs.dimension = 3

# Workflow
wf = Workflow(name='nucleus_extraction', base_dir=output_dir)

# Connect nodes
wf.connect([
    (bet, segmentation, [('out_file', 'in_files')]),
    (segmentation, registration, [('restored_image', 'moving_image')])
])

# Set input files directly on the bet node
bet.inputs.in_file = input_files

# Run the workflow
wf.run('MultiProc', plugin_args={'n_procs': 1})
