from concurrent.futures import ThreadPoolExecutor
from enum import Enum
import logging
import os
from pathlib import Path

from osfoffline import settings
from osfoffline.client.osf import OSFClient
from osfoffline.database import Session
from osfoffline.database.models import Node, File
from osfoffline.tasks import operations
from osfoffline.tasks.operations import OperationContext
from osfoffline.utils import hash_file
from osfoffline.utils.authentication import get_current_user


logger = logging.getLogger(__name__)


class Location(Enum):
    LOCAL = 0
    REMOTE = 1


class EventType(Enum):
    CREATE = 0
    DELETE = 1
    MOVE = 2
    UPDATE = 3


# Meant to emulate the watchdog FileSystemEvent
# May want to subclass in the future
class ModificationEvent:

    def __init__(self, location, event_type, contexts, src_path, dest_path=None):
        if dest_path:
            self.dest_path = dest_path
        self.location = location
        self.src_path = src_path
        self.event_type = event_type
        self.contexts = contexts
        self.context = contexts[0]
        self.is_directory = src_path.endswith(os.path.sep) or not src_path

    def operation(self):
        location = Location.LOCAL if self.location == Location.REMOTE else Location.REMOTE
        return getattr(
            operations,
            ''.join([
                location.name.capitalize(),
                self.event_type.name.capitalize(),
                'Folder' if self.is_directory else 'File'
            ])
        )(*self.contexts)

    @property
    def key(self):
        return (self.event_type, self.src_path, self.is_directory)

    def __eq__(self, event):
        return self.__class__ == event.__class__ and self.key == event.key

    def __ne__(self, event):
        return self.key != event.key

    def __hash__(self):
        return hash(self.key)


class Audit(object):
    """Store data about a file"""
    def __init__(self, fid, sha256, fobj):
        """
        :param str fid: id of file object
        :param str sha256: sha256 of file object
        :param fobj: the local, db, or remote representation of a file object
         :type fobj: pathlib.Path or models.File or client.osf.StorageObject
        """
        self.fid = fid
        self.sha256 = sha256
        self.fobj = fobj

    @property
    def info(self):
        return (self.fid, self.sha256, self.fobj)

NULL_AUDIT = Audit(None, None, None)


class Auditor:

    def __init__(self):
        self.user_folder = get_current_user().folder + os.path.sep

    def audit(self):
        db_map = self.collect_all_db()
        remote_map = self.collect_all_remote()
        local_map = self.collect_all_local(db_map)

        def context_for(paths):
            if not isinstance(paths, tuple):
                paths = (paths, )
            return [
                OperationContext(
                    local=self.user_folder / Path(path),
                    db=db_map.get(path, NULL_AUDIT).fobj,
                    remote=remote_map.get(path, NULL_AUDIT).fobj
                ) for path in paths
            ]

        diffs = {
            Location.LOCAL: self._diff(local_map, db_map),
            Location.REMOTE: self._diff(remote_map, db_map),
        }

        modifications = {}
        for location, changes in diffs.items():
            modifications[location] = {}
            for event_type in EventType:
                for change in changes[event_type]:
                    if not isinstance(change, tuple):
                        change = (change, )
                    for s in change:
                        parts = s.split(os.path.sep)
                        while not parts[-1] == settings.OSF_STORAGE_FOLDER:
                            parts.pop(-1)
                            path = os.path.sep.join(parts + [''])
                            if path not in modifications[location]:
                                modifications[location][path] = ModificationEvent(
                                    location,
                                    EventType.UPDATE,
                                    context_for(path),
                                    path
                                )
                        # *change always adds the src_path kwarg and sometime adds dest_path
                        modifications[location][s] = ModificationEvent(
                            location,
                            event_type,
                            context_for(change),
                            *change
                        )
        return modifications[Location.LOCAL], modifications[Location.REMOTE]

    def collect_all_db(self):
        """Return {rel_path: Audit} pairs for every file known in the DB.

        In order to compare local vs remote objects effectively (when the filename may be saved as an alias due to
          OS limitations), db_map keys on both the actual path, and any aliases used for that file on the local
          filesystem.
        """
        res = {}
        for entry in Session().query(File):
            audit = Audit(
                entry.id,
                entry.sha256,
                entry
            )
            res[entry.rel_path_unaliased] = audit
            if entry.alias is not None:
                # Aliases are guaranteed to be unique, so this should not override any existing DB filenames
                res[entry.rel_path] = audit

        return res

    def collect_all_remote(self):
        ret = {}
        with ThreadPoolExecutor(max_workers=5) as tpe:
            # first get top level nodes selected in settings
            for node in Session().query(Node).filter(Node.sync):
                try:
                    remote_node = OSFClient().get_node(node.id)
                except Exception as e:
                    # If the node can't be reached, skip auditing of this project and go on to the next node
                    # TODO: The client should be made smart enough to check return code before parsing and yield a custom exception
                    # TODO: The user should be notified about projects that failed to sync, and given a way to deselect them
                    logger.exception(e)
                    continue
                remote_files = remote_node.get_storage(id='osfstorage')
                rel_path = os.path.join(
                    node.rel_path,
                    settings.OSF_STORAGE_FOLDER
                )
                tpe.submit(
                    self._collect_node_remote,
                    remote_files,
                    ret,
                    rel_path,
                    tpe
                )
                try:
                    stack = remote_node.get_children(lazy=False)
                except Exception as e:
                    # If the node can't be reached, skip auditing of this project and go on to the next node
                    # TODO: The client should be made smart enough to check return code before parsing and yield a custom exception
                    # TODO: The user should be notified about projects that failed to sync, and given a way to deselect them
                    logger.exception(e)
                    continue
                while len(stack):
                    remote_child = stack.pop(0)
                    child_files = remote_child.get_storage(id='osfstorage')
                    # RemoteSyncWorker's _preprocess_node guarantees a db entry exists
                    # for each Node in the remote project hierarchy. Use the db Node's
                    # path representation to ensure consistent path naming conventions.
                    child_path = Session().query(Node).filter(
                        Node.id == remote_child.id
                    ).one().rel_path
                    tpe.submit(
                        self._collect_node_remote,
                        child_files,
                        ret,
                        os.path.join(
                            child_path,
                            settings.OSF_STORAGE_FOLDER
                        ),
                        tpe
                    )
                    try:
                        stack = stack + remote_child.get_children(lazy=False)
                    except Exception as e:
                        # If the node can't be reached, skip auditing of this project and go on to the next node
                        # TODO: The client should be made smart enough to check return code before parsing and yield a custom exception
                        # TODO: The user should be notified about projects that failed to sync, and given a way to deselect them
                        logger.exception(e)
                        continue
            tpe._work_queue.join()
        return ret

    def _collect_node_remote(self, root, acc, rel_path, tpe):
        """

        :param client.osf.StorageObject root: Remote storage data
        :param dict acc: A dictionary to which results will be added
        :param str rel_path: Filesystem path from user folder to this item
        :param ThreadPoolExecutor tpe:
        :return:
        """
        if root.parent:
            rel_path = os.path.join(rel_path, root.name)

        acc[rel_path + os.path.sep] = Audit(
            root.id,
            None if root.is_dir else root.extra['hashes']['sha256'],
            root
        )

        for child in root.get_children():
            # TODO replace with pattern matching
            if child.name in settings.IGNORED_NAMES:
                continue
            if child.kind == 'folder':
                tpe.submit(self._collect_node_remote, child, acc, rel_path, tpe)
            else:
                acc[os.path.join(rel_path, child.name)] = Audit(
                    child.id,
                    child.extra['hashes']['sha256'],
                    child
                )
        tpe._work_queue.task_done()

    def collect_all_local(self, db_map):
        """
        Collect data about all files in all nodes selected for sync
        :param db_map:
        :return: a dictionary of {rel_path: Audit} pairs for each file under a given node
        """
        ret = {}
        for node in Session().query(Node).filter(Node.sync):
            node_path = Path(os.path.join(node.path, settings.OSF_STORAGE_FOLDER))
            self._collect_node_local(node_path, ret, db_map)

            stack = [c for c in node.children]
            while len(stack):
                child = stack.pop(0)
                child_path = Path(
                    os.path.join(
                        child.path,
                        settings.OSF_STORAGE_FOLDER
                    )
                )
                self._collect_node_local(child_path, ret, db_map)
                stack = stack + child.children
        return ret

    def _collect_node_local(self, root, acc, db_map):
        """
        Return audit data about all files within a given node folder.

        :param Path root: Represent the path on disk of a given child node
        :param dict acc: Stores results output by this function
        :param dict db_map: DB data associated with various file paths
        :return:
        """
        rel_path = str(root).replace(self.user_folder, '') + os.path.sep
        acc[rel_path] = Audit(
            db_map.get(rel_path, NULL_AUDIT).fid,
            None,
            rel_path
        )

        for child in root.iterdir():
            # TODO replace with pattern matching
            if child.name in settings.IGNORED_NAMES:
                continue
            if child.is_dir():
                self._collect_node_local(child, acc, db_map)
            else:
                rel_path = str(child).replace(self.user_folder, '')
                db_entry = db_map.get(rel_path, NULL_AUDIT)
                # Local file may be aliased. If there is a matching DB object, use that to key local file audits
                #   on the original name, to facilitate comparison with remote files.
                rel_path = db_entry.fobj.rel_path_unaliased if db_entry.fobj is not None else rel_path
                acc[rel_path] = Audit(
                    db_entry.fid,
                    hash_file(child),
                    rel_path
                )
        return acc

    def _diff(self, source, target):
        # source == snapshot
        # target == ref
        id_target = {v.fid: k for k, v in target.items()}
        id_source = {v.fid: k for k, v in source.items()}

        created = set(source.keys()) - set(target.keys())
        deleted = set(target.keys()) - set(source.keys())

        for i in set(source.keys()) & set(target.keys()):
            if source[i].fid != target[i].fid:
                created.add(i)
                deleted.add(i)

        moved = set()
        for path in set(deleted):
            fid = target[path].fid
            if fid in id_source:
                deleted.remove(path)
                moved.add((path, id_source[fid]))

        for path in set(created):
            fid = source[path].fid
            if fid in id_target:
                created.remove(path)
                moved.add((id_target[fid], path))

        modified = set()
        for path in set(target.keys()) & set(source.keys()):
            if target[path].sha256 != source[path].sha256:
                modified.add(path)

        for (src, dest) in moved:
            if target[src].sha256 != source[dest].sha256:
                modified.add(src)

        return {
            EventType.CREATE: created,
            EventType.DELETE: deleted,
            EventType.MOVE: moved,
            EventType.UPDATE: modified,
        }
