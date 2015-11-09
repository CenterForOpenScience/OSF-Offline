class local_db_sync_exception(Exception):
    pass


class LocalDBBothNone(local_db_sync_exception):
    pass


class IncorrectLocalDBMatch(local_db_sync_exception):
    pass
