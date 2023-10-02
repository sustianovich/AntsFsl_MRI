from nipype.interfaces import fsl
from nilearn.plotting import plot_anat
import numpy as np
import os
import matplotlib.pyplot as plt

def brain_extraction_fsl(path_file):
    path_figures = 'figures'

    def bet(in_file, frac = 0.40, robust = True):
        fsl.FSLCommand.set_default_output_type('NIFTI_GZ')
        skullstrip = fsl.BET()
        _frac = "{:02}".format(int(frac * 100))
        in_file = in_file
        skullstrip.inputs.in_file = os.path.abspath(in_file)
        skullstrip.inputs.out_file = os.path.abspath(
                                    in_file.replace('.nii.gz',
                                                    f'_0{_frac}_brain.nii.gz')
                                    )
        skullstrip.inputs.frac = frac
        skullstrip.inputs.robust = robust
        return skullstrip

    fracs = np.arange(0.40,0.41,0.01) # in the example the range wasn 0.30,0.75
    for frac in fracs:
        skullstrip = bet(path_file,frac = round(frac,2),)
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

        