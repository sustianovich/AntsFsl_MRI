import nilearn.image as nli
import nilearn.plotting as plot
import matplotlib.pyplot as plt

# Specify paths to your T1w image and the MNI152 template
t1w_image_path = 'data/ds000114/sub-01/ses-test/anat/sub-01_ses-test_T1w.nii.gz'
mni_template_path = 'data/template/MNI152_T1_1mm_brain.nii.gz'

# Load the images
t1w_image = nli.load_img(t1w_image_path)
mni_template = nli.load_img(mni_template_path)

# Resample the T1w image to the MNI template
resampled_t1w = nli.resample_to_img(source_img=t1w_image, target_img=mni_template, interpolation='continuous')

# Plot the original and resampled images for visual inspection
plot.plot_anat(t1w_image, title='Original T1w')
plot.plot_anat(resampled_t1w, title='Resampled T1w')
plt.show()
