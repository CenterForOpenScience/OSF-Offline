import os

from osfoffline.exceptions.path_exceptions import InvalidPathError


class ProperPath(object):
    """
    A standardized and validated path.
    """

    def generic_path_validation(self, path):
        """Validates a specific path, e.g. /folder/file.txt, /folder/
        Rules for a path:
        1) path string must exist
        2) do not allow shortcuts in path
        3) path must be an absolute path


        :param str path: a path
        """
        if not path:
            raise InvalidPathError('Must specify path')
        if not isinstance(path, str):
            raise InvalidPathError("input path must be of type str")
        if '//' in path or '..' in path:
            raise InvalidPathError('Invalid path \'{}\' specified'.format(path))

        # don't allow shortcuts
        expanded_absolute_path = os.path.expanduser(os.path.abspath(path))

        if self.is_dir:
            if self.full_path != os.path.join(expanded_absolute_path, ''):
                raise InvalidPathError('Invalid path \'{}\' specified'.format(path))
        else:
            if self.is_root:
                raise InvalidPathError('Invalid path \'{}\' specified'.format(path))
            if self.full_path != expanded_absolute_path:
                raise InvalidPathError('Invalid path \'{}\' specified'.format(path))

        if self.is_file and path.endswith(os.sep):
            raise InvalidPathError('file ends with slash')

    def __init__(self, path, is_dir):
        self._orig_path = path
        self._is_dir = is_dir

        self.generic_path_validation(path)

    @property
    def is_dir(self):
        return self._is_dir

    @property
    def is_file(self):
        return not self._is_dir

    @property
    def name(self):
        if self._is_dir:
            without_trailing_sep = os.path.dirname(self.full_path)
            return os.path.basename(without_trailing_sep)
        else:
            return os.path.basename(self.full_path)

    @property
    def ext(self):
        if self.is_file:
            return os.path.splitext(self.full_path)[1]
        else:
            return ''

    @property
    def is_root(self):
        return self.full_path == os.sep

    @property
    def full_path(self):
        """
        A full_path is a absolute path. It is validated.
        If it is a folder, it ends with a slash.
        If its a file, it ends with no slash.
        :return: string full path
        """
        if self.is_dir:
            return os.path.join(self._orig_path, '')  # add trailing slash if not already there
        else:
            if self._orig_path.endswith(os.sep):
                return self._orig_path[0:-1 * len(os.sep)]  # remove separator
            else:
                return self._orig_path

    @property
    def parent(self):
        if self.is_root:
            raise InvalidPathError('path is already root. no parent.')
        else:
            if self.is_dir:
                without_trailing_sep = os.path.dirname(self.full_path)
                parent_path = os.path.dirname(without_trailing_sep)
                return ProperPath(parent_path, True)
            else:
                parent_path = os.path.dirname(self.full_path)
                return ProperPath(parent_path, True)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.is_dir == other.is_dir and str(self) == str(other)

    def __hash__(self):
        return hash(self.is_dir) + hash(str(self))

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return self.full_path

    def __repr__(self):
        return self.full_path


def ensure_folders(path):
    """Ensure that the specified folder (and all folders in path) exists"""
    if not os.path.exists(path):
        os.makedirs(path)
