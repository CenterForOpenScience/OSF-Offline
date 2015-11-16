# TODO: migrate all exceptions to this file

class OSFOfflineException(Exception):
    """ Base exception from which all others should inherit
    """
    def __init__(self, msg=None):
        self.message = msg

class AuthError(OSFOfflineException):
    pass
