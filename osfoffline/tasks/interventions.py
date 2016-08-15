import abc
import enum
import logging
import threading

from osfoffline.tasks import operations
from osfoffline.utils import EventType
from osfoffline.utils import Singleton

logger = logging.getLogger(__name__)


class Decision(enum.Enum):
    Keep_Mine = 0
    Keep_Theirs = 1
    Keep_Both = 2
    Cancel = 3
    Restore_Folder = 4


# Use the naming convention <LOCATION><ACTION>
# IE: RemoteCreated, BothDeleted, etc
class BaseIntervention(abc.ABC):
    def __init__(self, local, remote):
        self.local = local
        self.remote = remote
        self.decision = None
        self.event = threading.Event()
        logger.info('Created Intervention {}'.format(self.__class__.__name__))

    def set_result(self, decision):
        logger.info('Resolved Intervention {}: {}'.format(self.__class__.__name__, decision))
        self.decision = decision
        self.event.set()

    @abc.abstractmethod
    def resolve(self):
        raise NotImplementedError


# class LocalFileDeleted(BaseIntervention):

#     DEFAULT_DECISION = Decision.THEIRS

#     def __init__(self, auditor):
#         super().__init__(auditor)
#         self.title = 'Local File Deleted'
#         self.description = 'This is the description'
#         self.options = (Decision.MINE, Decision.THEIRS)

#     def resolve(self):
#         if self.decision == Decision.MINE:
#             return [operations.RemoteDeleteFile(self.remote.context)]
#         elif self.decision == Decision.THEIRS:
#             return [
#                 operations.DatabaseDeleteFile(self.remote.context),
#                 operations.LocalCreateFile(self.remote.context),
#             ]
#         raise ValueError('Unknown decision')


# class LocalFolderDeleted(BaseIntervention):

#     DEFAULT_DECISION = Decision.THEIRS

#     def __init__(self, local, remote, remote_children):
#         super().__init__(local, remote)
#         self.title = 'Local Folder Deleted'
#         self.description = 'The Local Folder \'{}\' was Deleted, however it still exists in the Remote Project {}.\n' \
#             '\n' \
#             'The Remote Folder contains {} objects.'.format(self.remote.db.path, self.remote.node.id, len(remote_children))
#         self.options = (Decision.MINE, Decision.THEIRS)

#     def resolve(self):
#         if self.decision == Decision.MINE:
#             return [operations.RemoteDeleteFolder(self.remote)]
#         elif self.decision == Decision.THEIRS:
#             return [operations.LocalCreateFolder(self.remote)]
#         raise ValueError('Unknown decision')


# class RemoteFileDeleted(BaseIntervention):

#     DEFAULT_DECISION = Decision.MINE

#     def __init__(self, local, remote):
#         super().__init__(local, remote)
#         self.title = 'Remote File Deleted'
#         self.description = 'This is the description'
#         self.options = (Decision.MINE, Decision.THEIRS)

#     def resolve(self):
#         if self.decision == Decision.MINE:
#             return [operations.RemoteCreateFile(self.local)]
#         elif self.decision == Decision.THEIRS:
#             return [operations.LocalDeleteFile(self.local)]
#         raise ValueError('Unknown decision')


class RemoteLocalFileConflict(BaseIntervention):
    DEFAULT_DECISION = Decision.Keep_Both

    def __init__(self, local, remote):
        super().__init__(local, remote)
        self.title = 'Remote Local File Conflict'
        self.description = ('This file "' +
                            self.local.context.local.stem +
                            '" conflicts with the remote file, which copy do you want to keep?')
        self.options = (Decision.Keep_Mine, Decision.Keep_Theirs, Decision.Keep_Both)

    def resolve(self):
        from osfoffline.sync.remote import RemoteSyncWorker

        if self.decision == Decision.Keep_Mine:
            if self.local.event_type == EventType.CREATE and self.remote.event_type == EventType.CREATE:
                return [
                    operations.DatabaseCreateFile(self.local.context),
                    operations.RemoteUpdateFile(self.local.context),
                ]
            return [operations.RemoteUpdateFile(self.local.context)]
        elif self.decision == Decision.Keep_Theirs:
            if self.local.event_type == EventType.CREATE and self.remote.event_type == EventType.CREATE:
                return [
                    operations.DatabaseCreateFile(self.remote.context),
                    operations.LocalUpdateFile(self.remote.context),
                ]
            return [operations.LocalUpdateFile(self.remote.context)]
        elif self.decision == Decision.Keep_Both:
            parent = self.local.context.local.parent
            i = 1
            while True:
                new = (parent / '{} ({}){}'.format(self.local.context.local.stem, i, self.local.context.local.suffix))
                if not new.exists():
                    break
                i += 1
            self.local.context.local.rename(new)
            RemoteSyncWorker().sync_now()
            if self.local.event_type == EventType.CREATE:
                return []
            return [operations.DatabaseDeleteFile(self.remote.context)]
        raise ValueError('Unknown decision')


class RemoteFolderDeleted(BaseIntervention):
    DEFAULT_DECISION = Decision.Restore_Folder

    def __init__(self, local, remote, local_events, remote_events):
        super().__init__(local, remote)
        self.changed = []
        self.deleted = []
        self.local_events = local_events
        self.remote_events = remote_events

        for event in remote_events.values():
            if event.src_path.startswith(remote.src_path) and event.event_type == EventType.DELETE:
                self.deleted.append(event)

        for event in local_events.values():
            if event.src_path.startswith(local.src_path) and event.event_type in (EventType.UPDATE, EventType.CREATE):
                self.changed.append(event)

        self.title = 'Remote Folder Deleted'
        self.description = ('Folder "' +
                            self.local.context.local.stem +
                            '"has been removed from "' +
                            self.local.context.local.parts[5])
        self.options = (Decision.Cancel, Decision.Restore_Folder)

    def resolve(self):
        from osfoffline.sync.remote import RemoteSyncWorker

        if self.decision == Decision.Restore_Folder:
            for event in self.changed:
                del self.local_events[event.src_path]
            for event in self.deleted:
                del self.remote_events[event.src_path]
        elif self.decision == Decision.Cancel:
            for event in self.changed:
                del self.local_events[event.src_path]
            for event in self.deleted:
                del self.remote_events[event.src_path]
            return []
        # elif self.decision == Decision.Keep_Theirs:
        #     for event in self.changed:
        #         del self.local_events[event.src_path]
        #     self.remote_events[self.remote.src_path] = self.remote
        #     return []
        # elif self.decision == Decision.MERGE:
        #     for event in self.changed:
        #         del self.local_events[event.src_path]
        #         self.remote_events.pop(event.src_path, None)

        RemoteSyncWorker().sync_now()
        return [operations.DatabaseDeleteFolder(self.remote.context)]


class Intervention(metaclass=Singleton):
    def set_callback(self, cb):
        self.cb = cb

    def resolve(self, intervention):
        self.cb(intervention)
        intervention.event.wait()
        return intervention.resolve()
