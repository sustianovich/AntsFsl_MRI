from nilearn import plotting

from nipype import Node, Workflow

# Create the workflow here
# Hint: use 'base_dir' to specify where to store the working directory

preproc = Workflow(name='work_preproc', base_dir='output/')

from nipype.algorithms.misc import Gunzip
from nipype.interfaces.fsl import ExtractROI

'''
In the figure above, we see that at the very beginning there are extreme values,
which hint to the fact that steady state wasn't reached yet.
Therefore, we want to exclude the dummy scans from the original data. This can be achieved with FSL's `ExtractROI`.
'''

extract = Node(ExtractROI(t_min=4, t_size=-1, output_type='NIFTI'), 
               name="extract")

from nipype.interfaces.fsl import MCFLIRT

mcflirt = Node(MCFLIRT(mean_vol=True,
                       save_plots=True),
               name="mcflirt")

from nipype.algorithms.rapidart import ArtifactDetect

'''
The parameters bellow mean the following:
- `norm_threshold` - Threshold to use to detect motion-related outliers when composite motion is being used
- `zintensity_threshold` - Intensity Z-threshold use to detection images that deviate from the mean
- `mask_type` - Type of mask that should be used to mask the functional data. *spm_global* uses an spm_global like calculation to determine the brain mask
- `parameter_source` - Source of movement parameters
- `use_differences` - If you want to use differences between successive motion (first element) and intensity parameter (second element) estimates in order to determine outliers
'''

art = Node(ArtifactDetect(norm_threshold=0.6,
                          zintensity_threshold=2.2,
                          mask_type='spm_global',
                          parameter_source='FSL',
                          use_differences=[True, False],
                          plot_type='svg'),
           name="art")

preproc.connect([(mcflirt, art, [('out_file', 'realigned_files'),
                                 ('par_file', 'realignment_parameters')])
                 ])


from nipype.interfaces.spm import NewSegment

'''
### Segmentation of anatomical image

Now let's work on the anatomical image.
In particular, let's use SPM's `NewSegment` to create probability maps
for the gray matter, white matter tissue and CSF.
Initiate NewSegment node here
'''

# Use the following tissue specification to get a GM and WM probability map
tpm_img ='data/template/TPM.nii'
tissue1 = ((tpm_img, 1), 1, (True,False), (False, False))
tissue2 = ((tpm_img, 2), 1, (True,False), (False, False))
tissue3 = ((tpm_img, 3), 2, (True,False), (False, False))
tissue4 = ((tpm_img, 4), 3, (False,False), (False, False))
tissue5 = ((tpm_img, 5), 4, (False,False), (False, False))
tissue6 = ((tpm_img, 6), 2, (False,False), (False, False))
tissues = [tissue1, tissue2, tissue3, tissue4, tissue5, tissue6]

segment = Node(NewSegment(tissues=tissues), name='segment')

# Specify example input file
anat_file = 'data/template/MNI152_T1_1mm_brain_mask.nii.gz'

# Initiate Gunzip node
gunzip_anat = Node(Gunzip(in_file=anat_file), name='gunzip_anat')

# Connect NewSegment node to the other nodes here
preproc.connect([(gunzip_anat, segment, [('out_file', 'channel_files')])])

from nipype.interfaces.fsl import FLIRT

'''
Compute Coregistration Matrix

As a next step, we will make sure that the functional images are coregistered to the anatomical image. For this, we will use FSL's `FLIRT` function. As we just created a white matter probability map, we can use this together with the Boundary-Based Registration (BBR) cost function to optimize the image coregistration. As some helpful notes...
- use a degree of freedom of 6
- specify the cost function as `bbr`
- use the `schedule='/usr/share/fsl/5.0/etc/flirtsch/bbr.sch'`
'''

# Initiate FLIRT node here
coreg = Node(FLIRT(dof=6,
                   cost='bbr',
                   schedule='/home/sus/fsl/src/fsl-flirt/flirtsch/bbr.sch',
                   output_type='NIFTI'),
             name="coreg")

# Connect FLIRT node to the other nodes here
preproc.connect([(gunzip_anat, coreg, [('out_file', 'reference')]),
                 (mcflirt, coreg, [('mean_img', 'in_file')])
                 ])

'''
`bbr` routine can use the subject-specific white matter probability map
to guide the coregistration.
But for this, we need to create a binary mask out of the WM probability map. This can easily be done by FSL's `Threshold` interface.
'''

from nipype.interfaces.fsl import Threshold

# Threshold - Threshold WM probability image
threshold_WM = Node(Threshold(thresh=0.5,
                              args='-bin',
                              output_type='NIFTI'),
                name="threshold_WM")

'''
Now, to select the WM probability map that the `NewSegment` node created, we need some helper function.
Because the output field `partial_volume_files` form the segmentation node, will give us a list of files,
i.e. `[[GM_prob], [WM_prob], [], [], [], []]`. Therefore, using the following function, we can select only the last element of this list.
'''

# Select WM segmentation file from segmentation output
def get_wm(files):
    return files[1][0]

# Connecting the segmentation node with the threshold node
preproc.connect([(segment, threshold_WM, [(('native_class_images', get_wm),
                                           'in_file')])])

# Connect Threshold node to coregistration node above here
preproc.connect([(threshold_WM, coreg, [('out_file', 'wm_seg')])])

# Import the SelectFiles
from nipype import SelectFiles
subject_id = 'aaa0001'
ses_id = '001'
# String template with {}-based strings
templates = {'anat': 'sub-{subject_id}/'
                     'sub-{subject_id}_ses_{ses_id}_T1w.nii.gz',
             'anat': 'sub-{subject_id}/'
                     'sub-{subject_id}_ses_{ses_id}_T2.nii.gz',}

# Create SelectFiles node
sf = Node(SelectFiles(templates,
                      base_directory='data/ds000001',
                      sort_filelist=True),
          name='selectfiles')
sf.inputs.ses_id='test'
sf.inputs.task_id='fingerfootlips'

subject_list = ['aaa0001']
sf.iterables = [('subject_id', subject_list)]

preproc.connect([(sf, gunzip_anat, [('anat', 'in_file')])])

from IPython.display import Image

preproc.write_graph()
# Create preproc output graph
preproc.write_graph(graph2use='colored', dotfilename='output/work_preproc/graph_colored.dot', format='png', simple_form=True)

# Visualize the graph
from IPython.display import Image
Image(filename='output/work_preproc/graph_colored.png', width=750)

preproc.run('MultiProc', plugin_args={'n_procs': 3})

# #%%
# !tree output/work_preproc/ -I '*js|*json|*pklz|_report|*dot|*html|*txt|*.m'

# Plot the motion paramters
import numpy as np
import matplotlib.pyplot as plt
par = np.loadtxt('/output/work_preproc/_subject_id_AAA0001/mcflirt/'
                 'asub-07_ses-test_task-fingerfootlips_bold_roi_mcf.nii.gz.par')
fig, axes = plt.subplots(2, 1, figsize=(15, 5))
axes[0].set_ylabel('rotation (radians)')
axes[0].plot(par[0:, :3])
axes[1].plot(par[0:, 3:])
axes[1].set_xlabel('time (TR)')
axes[1].set_ylabel('translation (mm)');