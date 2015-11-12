# -*- coding: utf-8 -*-
import os
import hashlib

from watchdog.events import (
    DirDeletedEvent,
    FileDeletedEvent,
    FileModifiedEvent,
    FileCreatedEvent,
    DirCreatedEvent,
)
from watchdog.observers import Observer
from osfoffline.database_manager.models import User, Node, File, Base
from osfoffline.exceptions.item_exceptions import InvalidItemType, FolderNotInFileSystem
from osfoffline.exceptions.local_db_sync_exceptions import LocalDBBothNone, IncorrectLocalDBMatch
from osfoffline.utils.path import ProperPath


class LocalDBSync(object):
    COMPONENTS_FOLDER_NAME = 'Components'

    def __init__(self, absolute_osf_dir_path, observer, user):
        if not isinstance(observer, Observer):
            raise TypeError
        if not isinstance(user, User):
            raise TypeError
        if not os.path.isdir(absolute_osf_dir_path):
            raise FolderNotInFileSystem

        self.osf_path = ProperPath(absolute_osf_dir_path, True)
        self.observer = observer
        self.user = user

    def emit_new_events(self):

        local_db_tuple_list = self._make_local_db_tuple_list(self.osf_path, self.user)
        for local, db in local_db_tuple_list:
            self._emit_new_events(local, db)

    def _make_local_db_tuple_list(self, local, db):
        # checks
        if local is None and db is None:
            raise LocalDBBothNone
        if local and db and self._get_proper_path(local) != self._get_proper_path(db):
            raise IncorrectLocalDBMatch
        if local and not isinstance(local, ProperPath):
            raise InvalidItemType

        out = []
        children = self._get_children(local) + self._get_children(db)
        # sort in order to get matching items next to each other.
        children = sorted(children, key=lambda c: self._get_proper_path(c).full_path)

        i = 0
        while i < len(children):
            if self._represent_same_values(children, i):
                if isinstance(children[i], Base):
                    to_add = (children[i + 1], children[i])
                else:
                    to_add = (children[i], children[i + 1])
                # add an extra 1 because skipping next value
                i += 1
            elif isinstance(children[i], Base):
                to_add = (None, children[i])
            else:
                to_add = (children[i], None)
            out.append(to_add)
            i += 1

        # assertions
        for local, db in out:
            if local is not None and db is not None:
                assert isinstance(local, ProperPath)
                assert isinstance(db, Base)
                assert local == self._get_proper_path(db)
            elif local is not None:
                assert db is None
                assert isinstance(local, ProperPath)
            elif db is not None:
                assert isinstance(db, Base)
                assert local is None
            else:
                assert False
        return out

    def _get_children(self, item):
        if item is None:
            return []

        # local
        if isinstance(item, ProperPath):
            if item.is_file:
                return []
            else:
                children = []
                for child in os.listdir(item.full_path):
                    child_item_path = os.path.join(item.full_path, child)
                    is_dir = os.path.isdir(child_item_path)
                    child_item = ProperPath(child_item_path, is_dir)

                    # handle the components folder
                    if child_item.name == LocalDBSync.COMPONENTS_FOLDER_NAME:
                        for component in os.listdir(child_item_path):
                            component_path = os.path.join(child_item_path, component)
                            component_is_dir = os.path.isdir(component_path)
                            # NOTE: making a concious decision here to ignore invalid file in components folder
                            # NOTE: this means the user is not getting an alert in this case
                            if component_is_dir:
                                children.append(ProperPath(component_path, component_is_dir))
                    else:
                        children.append(child_item)
                return children
        # db
        else:
            if isinstance(item, File):
                return item.files
            elif isinstance(item, Node):
                return item.child_nodes + item.top_level_file_folders
            elif isinstance(item, User):
                return item.top_level_nodes
            else:
                raise InvalidItemType('LocalDBSync._get_children does '
                                      'not handle items of t'
                                      'ype '
                                      '{item_type}'.format(item_type=type(item)))

    def _get_proper_path(self, item):
        if isinstance(item, ProperPath):
            return item
        elif isinstance(item, User):
            return ProperPath(item.osf_local_folder_path, True)
        elif isinstance(item, File) and item.is_file:
            return ProperPath(item.path, False)
        elif isinstance(item, Base):
            return ProperPath(item.path, True)
        elif isinstance(item, str):
            absolute = os.path.join(self.osf_path.full_path, item)
            return ProperPath(absolute, os.path.isdir(absolute))
        else:
            raise InvalidItemType('LocalDBSync._get_proper_path does '
                                  'not handle items of type '
                                  '{item_type}'.format(item_type=type(item)))

    def _represent_same_values(self, children, i):
        if i + 1 < len(children):
            return self._get_proper_path(children[i]) == self._get_proper_path(children[i + 1])
        else:
            return False

    def _make_hash(self, local):
        assert isinstance(local, ProperPath)
        m = hashlib.md5()
        with open(local.full_path, "rb") as f:
            while True:
                buf = f.read(2048)
                if not buf:
                    break
                m.update(buf)
        return m.hexdigest()

    def _determine_event_type(self, local, db):
        if not local and not db:
            raise LocalDBBothNone
        if local and not isinstance(local, ProperPath):
            raise TypeError
        if db and (not (isinstance(db, Node) or isinstance(db, File))):
            raise TypeError

        event = None
        if local and db:
            if self._get_proper_path(local) != self._get_proper_path(db):
                raise IncorrectLocalDBMatch
            if isinstance(db, File) and db.is_file and self._make_hash(local) != db.hash:
                event = FileModifiedEvent(self._get_proper_path(local).full_path)  # create changed event
                # folder modified event cannot happen. It will be a create and delete event.
        elif local is None:
            db_path = self._get_proper_path(db).full_path
            if isinstance(db, File) and db.is_file:
                event = FileDeletedEvent(db_path)  # delete event for file
            else:
                event = DirDeletedEvent(db_path)  # delete event for folder
        elif db is None:
            local_path = self._get_proper_path(local)
            if local_path.is_dir:
                event = DirCreatedEvent(local_path.full_path)
            else:
                event = FileCreatedEvent(local_path.full_path)
        return event

    def _emit_new_events(self, local, db):
        assert local or db
        event = self._determine_event_type(local, db)
        if event:
            emitter = next(iter(self.observer.emitters))
            emitter.queue_event(event)

        local_db_tuple_list = self._make_local_db_tuple_list(local, db)
        for local, db in local_db_tuple_list:
            self._emit_new_events(local, db)


# observer = Observer()  # create observer. watched for events on files.

# if __name__=='__main__':
#
#     setup_db('home/himanshu/.local/share/OSF Offline')
#     session = get_session()
#     osf_folder = '/home/himanshu/OSF-Offline/osfoffline/sandbox/dumbdir/OSF/'
#     user = User(osf_path= osf_folder)
#     session.add(user)
#     session.commit()
#     observer = Observer()
#
#     loop = asyncio.get_event_loop()
#
#     event_handler = OSFEventHandler(osf_folder, '','',loop)
#     observer.schedule(event_handler, osf_folder, recursive=True)
#
#
#     determine_new_events(user.osf_path, observer, user)
#     observer.start()
#     loop.run_forever()


"""
PLAN:


1) we will do the same match up the local filesystem with whats in the db in a [(local, db)]
2) get_id in this case will just be path. local.path, os.path.fullpath.
3) local: file/folder full path,
   db:
3) can create new event Event(. . .) then you can use observer.queue_event(event)
    will have to research how the Event is created to make it match what filesystem does.


NOTE: os.walk will give you local file system. can compare to db. BUT, this doesnt tell you if something exists in db and not in filesystem. THUS DONT DO THIS.
NOTE: local is going to be path because thats all you need for folders.
NOTE: when CHECKING, you check to see if db item is a file. If file, then you check to see if different from what db has using YOU CAN ACTUALLY USE HASH IN THIS CASE!!!!!!!!!!

ISSUES:
1)
2)

"""
