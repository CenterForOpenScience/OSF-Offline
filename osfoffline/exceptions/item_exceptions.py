__author__ = 'himanshu'


# Items
class ItemError(Exception):
    pass


class InvalidItemType(Exception):
    pass


class ItemNotInDB(ItemError):
    pass


class ItemNotInFileSystem(ItemError):
    pass


class FileNotinDB(ItemNotInDB):
    pass


class FolderNotInDB(ItemNotInDB):
    pass


class NodeNotinDB(ItemNotInDB):
    pass


class FileNotInFileSystem(ItemNotInFileSystem):
    pass


class FolderNotInFileSystem(ItemNotInFileSystem):
    pass


class NodeNotInFileSystem(ItemNotInFileSystem):
    pass
