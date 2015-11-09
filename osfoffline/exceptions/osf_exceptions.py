# OSF ERROR
class OSFError(Exception):
    pass


class OSFAuthError(OSFError):
    pass


class NodeNoAccess(OSFAuthError):
    pass


class FileNoAccess(OSFAuthError):
    pass


class AlreadyOnOSFError(OSFError):
    pass


class NewFileAlreadyOnOSF(AlreadyOnOSFError):
    pass


class NewNodeAlreadyOnOSF(AlreadyOnOSFError):
    pass


class NotFound(OSFError):
    pass


class FileNotFound(NotFound):
    pass


class NodeNotFound(NotFound):
    pass


class StateError(Exception):
    pass


class LocalAndRemoteNone(StateError):
    pass
