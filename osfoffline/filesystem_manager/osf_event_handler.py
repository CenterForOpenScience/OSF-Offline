"""
This is the most important file in the system. OSFEventHandler is responsible for updating the models,
storing the data into the db, and then sending a request to the remote server.
"""
import asyncio
import logging
import os

from sqlalchemy.exc import SQLAlchemyError
from watchdog.events import FileSystemEventHandler, DirModifiedEvent, DirCreatedEvent, FileCreatedEvent

from osfoffline.database_manager.models import Node, File, User
from osfoffline.database_manager.db import session
from osfoffline.database_manager.utils import save
from osfoffline.utils.path import ProperPath
from osfoffline.exceptions.item_exceptions import ItemNotInDB
import osfoffline.alerts as AlertHandler

EVENT_TYPE_MOVED = 'moved'
EVENT_TYPE_DELETED = 'deleted'
EVENT_TYPE_CREATED = 'created'
EVENT_TYPE_MODIFIED = 'modified'


class OSFEventHandler(FileSystemEventHandler):
    """
    Base file system event handler that you can override methods from.
    """

    def __init__(self, osf_folder, loop):
        super().__init__()
        self._loop = loop or asyncio.get_event_loop()
        self.osf_folder = ProperPath(osf_folder, True)
        self.user = session.query(User).filter(User.logged_in).one()

    @asyncio.coroutine
    def on_any_event(self, event):
        pass

    @asyncio.coroutine
    def on_moved(self, event):
        """Called when a file or a directory is moved or renamed.

        :param event:
            Event representing file/directory movement.
        :type event:
            :class:`DirMovedEvent` or :class:`FileMovedEvent`
        """

        src_path = ProperPath(event.src_path, event.is_directory)
        dest_path = ProperPath(event.dest_path, event.is_directory)

        # determine and get what moved
        if not self._already_exists(src_path):
            try:
                self._get_parent_item_from_path(src_path)
            except ItemNotInDB:
                # This means it was put into a place on the hierarchy being watched but otherwise not attached to a
                # node, so it needs to be added just like a new event rather than as a move.

                new_event = DirCreatedEvent(event.dest_path) if event.is_directory else FileCreatedEvent(event.dest_path)
                yield from self._create_file_or_folder(new_event, src_path=dest_path)
                return
            logging.warning('Tried to move item that does not exist: {}'.format(src_path.name))
            return

        item = self._get_item_by_path(src_path)

        if isinstance(item, Node):
            AlertHandler.warn('Cannot manipulate components locally. {} will stop syncing'.format(item.title))
            return

        # File

        # rename
        if item.name != dest_path.name:
            item.name = dest_path.name
            item.locally_renamed = True
            save(session, item)
            logging.info("renamed a file {}".format(dest_path.full_path))
        # move
        elif src_path != dest_path:
            # check if file already exists in this moved location. If so, delete it from db.
            try:
                item_to_replace = self._get_item_by_path(dest_path)
                session.delete(item_to_replace)
                save(session)
            except ItemNotInDB:
                logging.info('file does not already exist in moved destination: {}'.format(dest_path.full_path))

            new_parent_item = self._get_parent_item_from_path(dest_path)

            # move item

            # set previous fields
            item.previous_provider = item.provider
            item.previous_node_osf_id = item.node.osf_id

            # update parent and node fields
            # NOTE: this line makes it so the file no longer exists in the database.
            # NOTE: item at this point is stale. Unclear why it matters though.
            # NOTE: fix is above: session.refresh(item)
            item.parent = new_parent_item if isinstance(new_parent_item, File) else None
            item.node = new_parent_item if isinstance(new_parent_item, Node) else new_parent_item.node

            # basically always osfstorage. this is just meant to be extendible in the future to other providers
            item.provider = new_parent_item.provider if isinstance(new_parent_item, File) else File.DEFAULT_PROVIDER

            # flags
            item.locally_moved = True

            save(session, item)
            logging.info('moved from {} to {}'.format(src_path.full_path, dest_path.full_path))

    @asyncio.coroutine
    def _create_file_or_folder(self, event, src_path):
        # assert: whats being created is a file folder
        try:
            containing_item = self._get_parent_item_from_path(src_path)
        except ItemNotInDB:
            logging.error('tried to create item {} for parent {} but parent does not exist'.format(src_path.full_path,
                                                                                                   src_path.parent.full_path))
            return

        if isinstance(containing_item, Node):
            node = containing_item
        else:  # file
            node = containing_item.node
        new_item = File(
            name=src_path.name,
            type=File.FOLDER if event.is_directory else File.FILE,
            user=self.user,
            locally_created=True,
            provider=File.DEFAULT_PROVIDER,
            node=node
        )
        containing_item.files.append(new_item)
        if new_item.is_file:
            try:
                new_item.update_hash()
            except FileNotFoundError:
                # if file doesnt exist just as we create it, then file is likely temp file. thus don't put it in db.
                return
        save(session, new_item, containing_item)
        logging.info("created new {} {}".format('folder' if event.is_directory else 'file', src_path.full_path))

    @asyncio.coroutine
    def on_created(self, event):
        """Called when a file or directory is created.

        :param event:
            Event representing file/directory creation.
        :type event:
            :class:`DirCreatedEvent` or :class:`FileCreatedEvent`
        """
        src_path = ProperPath(event.src_path, event.is_directory)

        # create new model
        if self._already_exists(src_path):
            return

        yield from self._create_file_or_folder(event, src_path=src_path)

    @asyncio.coroutine
    def on_modified(self, event):
        """Called when a file or directory is modified.

        :param event:
            Event representing file/directory modification.
        :type event:
            :class:`DirModifiedEvent` or :class:`FileModifiedEvent`
        """

        if isinstance(event, DirModifiedEvent):
            return
        src_path = ProperPath(event.src_path, event.is_directory)

        # get item
        try:
            item = self._get_item_by_path(src_path)
        except ItemNotInDB:
            # todo: create file folder
            logging.warning('file {} was modified but not already in db. create it in db.'.format(src_path))
            return  # todo: remove this once above is implemented

        # update hash
        item.update_hash()

        # save
        save(session, item)

    @asyncio.coroutine
    def on_deleted(self, event):
        """Called when a file or directory is deleted.

        :param event:
            Event representing file/directory deletion.
        :type event:
            :class:`DirDeletedEvent` or :class:`FileDeletedEvent`
        """
        src_path = ProperPath(event.src_path, event.is_directory)

        if not self._already_exists(src_path):
            return

        # get item
        item = self._get_item_by_path(src_path)

        # put item in delete state after waiting a second and
        # checking to make sure the file was actually deleted
        yield from asyncio.sleep(1)
        if not os.path.exists(item.path):
            item.locally_deleted = True
            # nodes cannot be deleted online. THUS, delete it inside database. It will be recreated locally.
            if isinstance(item, Node):
                session.delete(item)
                try:
                    save(session)
                except SQLAlchemyError as e:
                    logging.exception('Error deleting node from database.')
                return
            try:
                save(session, item)
            except SQLAlchemyError as e:
                logging.exception('Error deleting node from database.')
            else:
                logging.info('{} set to be deleted'.format(src_path.full_path))

    def dispatch(self, event):
        # basically, ignore all events that occur for 'Components' file or folder
        if self._event_is_for_components_file_folder(event):
            return

        _method_map = {
            EVENT_TYPE_MODIFIED: self.on_modified,
            EVENT_TYPE_MOVED: self.on_moved,
            EVENT_TYPE_CREATED: self.on_created,
            EVENT_TYPE_DELETED: self.on_deleted,
        }

        handlers = [self.on_any_event, _method_map[event.event_type]]
        for handler in handlers:
            # todo: could put items in asyncio.Queue right here.
            # todo: unclear how to make the Queue work with the parent thread....????
            self._loop.call_soon_threadsafe(
                asyncio.async,
                handler(event)
            )

    def _already_exists(self, path):
        try:
            self._get_item_by_path(path)
            return True
        except ItemNotInDB:
            return False

    def _get_parent_item_from_path(self, path):
        assert isinstance(path, ProperPath)
        containing_folder_path = path.parent

        if containing_folder_path == self.osf_folder:
            raise ItemNotInDB('item has path: {}'.format(path.full_path))

        return self._get_item_by_path(containing_folder_path)

    # todo: figure out how you can improve this
    def _get_item_by_path(self, path):
        assert isinstance(path, ProperPath)
        for node in session.query(Node):
            if ProperPath(node.path, True) == path:
                return node
        for file_folder in session.query(File):
            file_path = ProperPath(file_folder.path, file_folder.is_folder)
            if file_path == path:
                return file_folder
        raise ItemNotInDB('item has path: {}'.format(path.full_path))

    def _event_is_for_components_file_folder(self, event):
        if ProperPath(event.src_path, True).name == 'Components':
            return True
        try:
            if ProperPath(event.dest_path, True).name == 'Components':
                return True
            return False
        except AttributeError:
            return False
