from nipype.interfaces import fsl
from nipype.interfaces import utility as util
from nipype.pipeline import engine as pe

def get_brightness_threshold(thresh):
    return [0.75 * val for val in thresh]

def get_brightness_threshold_double(thresh):
    return [2 * 0.75 * val for val in thresh]

def cartesian_product(fwhms, in_files, usans, btthresh):
    from nipype.utils.filemanip import ensure_list
    # ensure all inputs are lists
    in_files = ensure_list(in_files)
    fwhms = [fwhms] if isinstance(fwhms, (int, float)) else fwhms
    # create cartesian product lists (s_ = single element of list)
    cart_in_file = [s_in_file for s_in_file in in_files for s_fwhm in fwhms]
    cart_fwhm = [s_fwhm for s_in_file in in_files for s_fwhm in fwhms]
    cart_usans = [s_usans for s_usans in usans for s_fwhm in fwhms]
    cart_btthresh = [s_btthresh for s_btthresh in btthresh for s_fwhm in fwhms]
    return cart_in_file, cart_fwhm, cart_usans, cart_btthresh

def getusans(x):
    return [[tuple([val[0], 0.5 * val[1]])] for val in x]
