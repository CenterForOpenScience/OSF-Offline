import os


def validate_containing_folder(containing_folder):
    if (not containing_folder) or (containing_folder == ''):
        return False

    try:
        if os.path.isdir(containing_folder):
            osf_path = os.path.join(containing_folder, "OSF")
            if os.path.isfile(osf_path):
                return False
            return True
        return False
    except ValueError:
        return False
