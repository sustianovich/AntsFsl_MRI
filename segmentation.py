import os

from nilearn import plotting
from nipype import Node, Workflow
from nipype.algorithms.misc import Gunzip
from nipype.interfaces.fsl import ExtractROI
from nipype.interfaces.fsl import FLIRT
from nipype.interfaces.fsl import MCFLIRT
from nipype.interfaces.spm import NewSegment
from nipype.interfaces.fsl import Threshold
from niflow.nipype1.workflows.fmri.fsl.preprocess import create_susan_smooth
from nipype.interfaces.fsl import ApplyMask
from nipype import MapNode
from nipype.algorithms.confounds import TSNR
from nipype import SelectFiles
from IPython.display import Image

from utils_tools import find_files

words_to_search = ['t1w', 'brain']
paths_to_files = find_files(words_to_search)

home_directory = os.path.expanduser("~")

in_file = paths_to_files[0]

preproc = Workflow(name='work_preproc', base_dir=os.path.abspath(in_file))

extract = Node(ExtractROI(t_min=4, t_size=-1, output_type='NIFTI'), name="extract")

mcflirt = Node(MCFLIRT(mean_vol=True, save_plots=True), name="mcflirt")

# Use the following tissue specification to get a GM and WM probability map
tpm_img ='data/template/TPM.nii'

tissue1 = ((tpm_img, 1), 1, (True,False), (False, False))
tissue2 = ((tpm_img, 2), 1, (True,False), (False, False))
tissue3 = ((tpm_img, 3), 2, (True,False), (False, False))
tissue4 = ((tpm_img, 4), 3, (False,False), (False, False))
tissue5 = ((tpm_img, 5), 4, (False,False), (False, False))
tissue6 = ((tpm_img, 6), 2, (False,False), (False, False))
tissues = [tissue1, tissue2, tissue3, tissue4, tissue5, tissue6]

# Initiate NewSegment node here
segment = Node(NewSegment(tissues=tissues), name='segment')

# Specify example input file
anat_file = 'data/sub-001/ADNI/AD/sub-1_ses-timepoint1_run-1_T1w.nii.gz'
# Initiate Gunzip node
gunzip_anat = Node(Gunzip(in_file=anat_file), name='gunzip_anat')

preproc.connect([(gunzip_anat, segment, [('out_file', 'channel_files')])])

schedule_path = os.path.join(home_directory, 'fsl/src/fsl-flirt/flirtsch/bbr.sch')
coreg = Node(FLIRT(dof=6, cost='bbr', schedule=schedule_path, output_type='NIFTI'), name="coreg")

# Connect FLIRT node to the other nodes here

preproc.connect([(gunzip_anat, coreg, [('out_file', 'reference')]),
                 (mcflirt, coreg, [('mean_img', 'in_file')])
                 ])

# Threshold - Threshold WM probability image
threshold_WM = Node(Threshold(thresh=0.5,
                              args='-bin',
                              output_type='NIFTI'),
                name="threshold_WM")

# Select WM segmentation file from segmentation output
def get_wm(files):
    return files[1][0]

# Connecting the segmentation node with the threshold node
preproc.connect([(segment, threshold_WM, [(('native_class_images', get_wm),
                                           'in_file')])])


# Connect Threshold node to coregistration node above here

preproc.connect([(threshold_WM, coreg, [('out_file', 'wm_seg')])])

# ### Smoothing
# 
# Next step is image smoothing. The most simple way to do this is to use FSL's or SPM's `Smooth` function. But for learning purposes, let's use FSL's `SUSAN` workflow as it is implemented in Nipype. Note that this time, we are importing a workflow instead of an interface.

# If you type `create_susan_smooth?` you can see how to specify the input variables to the susan workflow. In particular, they are...
# - `fwhm`: set this value to 4 (or whichever value you want)
# - `mask_file`: will be created in a later step
# - `in_file`: will be handled while connection to other nodes in the preproc workflow


# Specify the isometric voxel resolution you want after coregistration
desired_voxel_iso = 4

# Apply coregistration warp to functional images
applywarp = Node(FLIRT(interp='spline',
                       apply_isoxfm=desired_voxel_iso,
                       output_type='NIFTI'),
                 name="applywarp")

# **<span style="color:red">Important</span>**: As you can see above, we also specified a variable `desired_voxel_iso`. This is very important at this stage, otherwise `FLIRT` will transform your functional images to a resolution of the anatomical image, which will dramatically increase the file size (e.g. to 1-10GB per file). If you don't want to change the voxel resolution, use the additional parameter `no_resample=True`. Important, for this to work, you still need to define `apply_isoxfm`.

# Connecting the ApplyWarp node to all the other nodes
preproc.connect([(mcflirt, applywarp, [('out_file', 'in_file')]),
                 (coreg, applywarp, [('out_matrix_file', 'in_matrix_file')]),
                 (gunzip_anat, applywarp, [('out_file', 'reference')])
                 ])
# Initiate SUSAN workflow here


susan = create_susan_smooth(name='susan')
susan.inputs.inputnode.fwhm = 4
# Connect Threshold node to coregistration node above here

preproc.connect([(applywarp, susan, [('out_file', 'inputnode.in_files')])])

# ### Create Binary Mask
# 
# There are many possible approaches on how you can mask your functional images. One of them is not at all, one is with a simple brain mask and one that only considers certain kind of brain tissue, e.g. gray matter.
# 
# For the current example, we want to create a dilated gray matter mask. For this purpose we need to:
# 1. Resample the gray matter probability map to the same resolution as the functional images
# 2. Threshold this resampled probability map at a specific value
# 3. Dilate this mask by some voxels to make the mask less conservative and more inclusive
# 
# The first step can be done in many ways (eg. using freesurfer's `mri_convert`, `nibabel`) but in our case, we will use FSL's `FLIRT`. The trick is to use the probability mask, as input file and a reference file.

# Initiate resample node
resample = Node(FLIRT(apply_isoxfm=desired_voxel_iso,
                      output_type='NIFTI'),
                name="resample")

# The second and third step can luckily be done with just one node. We can take almost the same `Threshold` node as above. We just need to add another additional argument: `-dilF` - which applies a maximum filtering of all voxels.

# Threshold - Threshold GM probability image
mask_GM = Node(Threshold(thresh=0.5,
                         args='-bin -dilF',
                         output_type='NIFTI'),
                name="mask_GM")

# Select GM segmentation file from segmentation output
def get_gm(files):
    return files[0][0]
# Now we can connect the resample and the gray matter mask node to the segmentation node and each other.
preproc.connect([(segment, resample, [(('native_class_images', get_gm), 'in_file'),
                                      (('native_class_images', get_gm), 'reference')
                                      ]),
                 (resample, mask_GM, [('out_file', 'in_file')])
                 ])

# This should do the trick.


# ### Apply the binary mask
# 
# Now we can connect this dilated gray matter mask to the susan node, as well as actually applying this to the resulting smoothed images.

# Connect gray matter Mask node to the susan workflow here

preproc.connect([(mask_GM, susan, [('out_file', 'inputnode.mask_file')])])

# Initiate ApplyMask node here

mask_func = MapNode(ApplyMask(output_type='NIFTI'),
                    name="mask_func", 
                    iterfield=["in_file"])

# Connect smoothed susan output file to ApplyMask node here


preproc.connect([(susan, mask_func, [('outputnode.smoothed_files', 'in_file')]),
                 (mask_GM, mask_func, [('out_file', 'mask_file')])
                 ])


# ### Remove linear trends in functional images
# 
# Last but not least. Let's use Nipype's `TSNR` module to remove linear and quadratic trends in the functionally smoothed images. For this, you only have to specify the `regress_poly` parameter in the node initiation.

# Initiate TSNR node here

detrend = Node(TSNR(regress_poly=2), name="detrend")

# Connect the detrend node to the other nodes here

preproc.connect([(mask_func, detrend, [('out_file', 'in_file')])])

# ## Datainput with `SelectFiles` and `iterables` 
# 
# This is all nice and well. But so far we still had to specify the input values for `gunzip_anat` and `gunzip_func` ourselves. How can we scale this up to multiple subjects and/or multiple functional images and make the workflow take the input directly from the BIDS dataset?
# 
# For this, we need `SelectFiles` and `iterables`! It's rather simple, specify a template and fill-up the placeholder variables.

# Import the SelectFiles

# String template with {}-based strings
'''
templates = {'AD': 'sub-{subject_id}/ses-{ses_id}/anat/'
                     'sub-{subject_id}_ses-test_T1w.nii.gz',
             'NC': 'sub-{subject_id}/ses-{ses_id}/func/'
                     'sub-{subject_id}_ses-{ses_id}_task-{task_id}_bold.nii.gz'}

# Create SelectFiles node
sf = Node(SelectFiles(templates,
                      base_directory='/data/ADNI/',
                      sort_filelist=True),
          name='selectfiles')
sf.inputs.ses_id='timepoint1_run-1'
sf.inputs.task_id='0.3_brain'
subject_list = ['1']
sf.iterables = [('subject_id', subject_list)]
'''

templates = dict(T1="sub-{subject_id}/ADNI/AD/sub-1_ses-timepoint1_run-1_T1w_0.3_brain.nii.gz",
                 T2="sub-{subject_id}/ADNI/AD/sub-1_ses-timepoint1_inplaneT2.nii.gz")

sf = Node(SelectFiles(templates,
                      base_directory='data',
                      sort_filelist=True),
          name='selectfiles')

# ## Visualize the workflow
# 
# Now that we're done. Let's look at the workflow that we just created.

# Create preproc output graph
preproc.write_graph(graph2use='colored', format='png', simple_form=True)

# Visualize the graph

# Image(filename='/data/sub-001/results/registration/graph.png', width=750)

# ##  Run the Workflow
# 
# Now we are ready to run the workflow! Be careful about the `n_procs` parameter if you run a workflow in `'MultiProc'` mode. `n_procs` specifies the number of jobs/cores your computer will use to run the workflow. If this number is too high your computer will try to execute too many things at once and will most likely crash.
# 
# **Note**: If  you're using a Docker container and FLIRT fails to run without any good reason, you might need to change memory settings in the Docker preferences (6 GB should be enough for this workflow).

preproc.run('MultiProc', plugin_args={'n_procs': 4})
