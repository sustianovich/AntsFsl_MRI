
from brain_extraction import brain_extraction_fsl

def main():
    path_t1 = 'data/ds000001/sub-aaa0001/sub-aaa0001_ses-001_T1w.nii.gz'
    brain_extraction_fsl(path_t1)

if __name__ == "__main__":
    main()