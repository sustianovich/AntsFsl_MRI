from os.path import join as opj
from nipype.interfaces.fsl import MCFLIRT, FLIRT
from nipype.interfaces.afni import Resample
from nipype.interfaces.spm import Smooth
from nipype.interfaces.utility import IdentityInterface
from nipype.interfaces.io import SelectFiles, DataSink
from nipype.pipeline.engine import Workflow, Node

experiment_dir = 'output'
output_dir = 'datasink'
working_dir = 'data/ds000114'

# list of subject identifiers
subject_list = ['sub-01', 'sub-02', 'sub-03']

# list of session identifiers
session_list = ['ses-test']

# Smoothing widths to apply
fwhm = [4, 8]


# MCFLIRT - motion correction
mcflirt = Node(MCFLIRT(mean_vol=True,
                       save_plots=True,
                       output_type='NIFTI'),
               name="mcflirt")

# Resample - resample anatomy to 3x3x3 voxel resolution
resample = Node(Resample(voxel_size=(3, 3, 3),
                         outputtype='NIFTI'),
                name="resample")

# FLIRT - coregister functional images to anatomical images
coreg_step1 = Node(FLIRT(output_type='NIFTI'), name="coreg_step1")
coreg_step2 = Node(FLIRT(output_type='NIFTI',
                         apply_xfm=True), name="coreg_step2")

# Smooth - image smoothing
smooth = Node(Smooth(), name="smooth")
smooth.iterables = ("fwhm", fwhm)

# Infosource - a function free node to iterate over the list of subject names
infosource = Node(IdentityInterface(fields=['subject_id', 'session_id']),
                  name="infosource")
infosource.iterables = [('subject_id', subject_list),
                        ('session_id', session_list)]

# SelectFiles - to grab the data (alternativ to DataGrabber)
anat_file = opj('{subject_id}', 'anat', '{subject_id}_T1w.nii.gz')

templates = {'anat': anat_file}
selectfiles = Node(SelectFiles(templates,
                               base_directory='data/ds000114'),
                   name="selectfiles")
selectfiles = 'data/ds000114/sub-01/ses-test/anat/sub-01_ses-test_T1w.nii.gz'

# Datasink - creates output folder for important outputs
datasink = Node(DataSink(base_directory=experiment_dir,
                         container=output_dir),
                name="datasink")

# Use the following DataSink output substitutions
substitutions = [('_subject_id', ''),
                 ('_session_id_', ''),
                 ('_task-flanker', ''),
                 ('_mcf.nii_mean_reg', '_mean'),
                 ('.nii.par', '.par'),
                 ]
subjFolders = [('%s_%s/' % (sess, sub), '%s/%s' % (sub, sess))
               for sess in session_list
               for sub in subject_list]
subjFolders += [('%s_%s' % (sub, sess), '')
                for sess in session_list
                for sub in subject_list]
subjFolders += [('%s%s_' % (sess, sub), '')
                for sess in session_list
                for sub in subject_list]
substitutions.extend(subjFolders)
datasink.inputs.substitutions = substitutions

# Create a preprocessing workflow
preproc = Workflow(name='preproc')
preproc.base_dir = opj(experiment_dir, working_dir)

# Connect all components of the preprocessing workflow
preproc.connect([(infosource, selectfiles, [('subject_id', 'subject_id'),
                                            ('session_id', 'session_id')]),
                 (selectfiles, mcflirt, [('func', 'in_file')]),
                 (selectfiles, resample, [('anat', 'in_file')]),

                 (mcflirt, coreg_step1, [('mean_img', 'in_file')]),
                 (resample, coreg_step1, [('out_file', 'reference')]),

                 (mcflirt, coreg_step2, [('out_file', 'in_file')]),
                 (resample, coreg_step2, [('out_file', 'reference')]),
                 (coreg_step1, coreg_step2, [('out_matrix_file',
                                              'in_matrix_file')]),

                 (coreg_step2, smooth, [('out_file', 'in_files')]),

                 (mcflirt, datasink, [('par_file', 'preproc.@par')]),
                 (resample, datasink, [('out_file', 'preproc.@resample')]),
                 (coreg_step1, datasink, [('out_file', 'preproc.@coregmean')]),
                 (smooth, datasink, [('smoothed_files', 'preproc.@smooth')]),
                 ])

preproc.run('MultiProc', plugin_args={'n_procs': 2})