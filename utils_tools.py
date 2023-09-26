import os

def find_files(words, start_dir='.', extension='.nii.gz'):
    """Search for files containing specific words (in any order) and a specific extension in all subdirectories."""
    matches = []

    # Convert words to a set for faster lookups and to lowercase for case-insensitivity
    words_set = set(word.lower() for word in words)

    # Walk through all subdirectories of start_dir
    for root, dirs, files in os.walk(start_dir):
        for file in files:
            # Convert file name to lowercase and then check if all words appear in the file's name
            # Also check if the file has the right extension
            if all(word in file.lower() for word in words_set) and file.endswith(extension):
                matches.append(os.path.join(root, file))

    return matches


if __name__ == "__main__":
    pass

    



