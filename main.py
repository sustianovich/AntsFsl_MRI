from nipype.interfaces import fsl
from nilearn.plotting import plot_anat
import numpy as np
import os
import matplotlib.pyplot as plt


path_t1 = 'data/sub-1/sub-1_ses-timepoint1_run-1_T1w.nii.gz'
path_figures = 'figures'

def bet(in_file, frac = 0.40, robust = True):
    fsl.FSLCommand.set_default_output_type('NIFTI_GZ')
    skullstrip = fsl.BET()
    in_file = in_file
    skullstrip.inputs.in_file = os.path.abspath(in_file)
    skullstrip.inputs.out_file = os.path.abspath(
                                in_file.replace('.nii.gz',
                                                f'_{frac}_brain.nii.gz')
                                )
    skullstrip.inputs.frac = frac
    skullstrip.inputs.robust = robust
    return skullstrip


fracs = np.arange(0.3,0.75,0.05)
for frac in fracs:
    skullstrip = bet(path_t1,frac = round(frac,2),)
    print(skullstrip.cmdline)

fracs = np.arange(0.35,0.38,0.01)
for frac in fracs:
    skullstrip = bet(path_t1,frac = round(frac,2),)
    print(skullstrip.cmdline)
    skullstrip.run()
    fig,ax = plt.subplots(figsize=(12,12))
    plot_anat(skullstrip.inputs.out_file,
              title = f'frac = {frac:.2f}',
              threshold = 0,
              draw_cross = False,
#              display_mode = 'z',
#              cut_coords = np.arange(-40,41,5),
              cut_coords = (0,0,0),
              black_bg = True,
              figure = fig,
              axes = ax,)
    fig.savefig(os.path.join(path_figures,
                             f"bet_{frac:.2f}.png"),
    dpi = 300,
    facecolor = 'k',
    edgecolor = 'k',)
    plt.close('all')