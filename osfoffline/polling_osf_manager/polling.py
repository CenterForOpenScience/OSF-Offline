import os
import asyncio
import time
import logging

import aiohttp
import iso8601
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

import osfoffline.alerts as AlertHandler
from osfoffline.database_manager.models import User, Node, File, Base
from osfoffline.database_manager.db import session
from osfoffline.database_manager.utils import save
from osfoffline.exceptions.item_exceptions import InvalidItemType
from osfoffline.polling_osf_manager.api_url_builder import api_url_for, USERS, NODES
from osfoffline.polling_osf_manager.osf_query import OSFQuery
from osfoffline.polling_osf_manager.remote_objects import RemoteObject, RemoteNode, RemoteFile, RemoteFileFolder
from osfoffline.polling_osf_manager.polling_events import (CreateFile, CreateFolder, RenameFile, RenameFolder,
                                                           DeleteFile, DeleteFolder, UpdateFile)
from osfoffline.settings import POLL_DELAY


logger = logging.getLogger(__name__)


class Poll(object):
    def __init__(self, user, loop):
        assert isinstance(user, User)
        self._keep_running = True

        self.user = user

        self._loop = loop
        self.poll_job = None
        self.process_job = None
        self.osf_query = OSFQuery(loop=self._loop, oauth_token=self.user.oauth_token)

    def stop(self):
        logger.info('OSF polling requested to stop.')

        # Stop was called before start could complete
        if not self.poll_job or not self.process_job:
            return

        # If these futures are complete an exception has been raised in them
        if self.poll_job.done():
            raise self.poll_job.exception()
        if self.process_job.done():
            raise self.process_job.exception()

        # Other wise cancel them, the event loop will clean up for us
        self.poll_job.cancel()
        self.process_job.cancel()
        self.osf_query.close()
        logger.info('OSF polling requested stopped.')

    def handle_exception(self, future):
        # Note: The actual futures never exit, if they do an exception is raised
        try:
            raise future.exception()
        except (aiohttp.ClientError, asyncio.TimeoutError):
            logger.error('Unable to connect to the internet')
            AlertHandler.warn('Unable to connection to OSF, we\'ll try again later.')
        except asyncio.CancelledError:
            # Cancellations just mean this thread is exiting
            return

        # Make sure all our jobs are cancelled
        if future == self.poll_job:
            self.process_job.cancel()
        else:
            self.poll_job.cancel()

        logger.info('Restarting polling in 5 seconds')
        # Finally restart our watcher thread in 5 seconds
        self._loop.call_later(5, self.start)

    def start(self):
        remote_user = self._loop.run_until_complete(self.get_remote_user())

        self.queue = asyncio.Queue(maxsize=15)

        self.process_job = asyncio.ensure_future(self.process_queue())
        self.poll_job = asyncio.ensure_future(self.check_osf(remote_user))

        self.poll_job.add_done_callback(self.handle_exception)
        self.process_job.add_done_callback(self.handle_exception)

        return True

    @asyncio.coroutine
    def process_queue(self):
        while True:
            job = yield from self.queue.get()
            logger.info('Running {}'.format(job))
            yield from job.run()
            self.queue.task_done()

    @asyncio.coroutine
    def get_remote_user(self):
        url = api_url_for(USERS, user_id=self.user.osf_id)
        logger.debug(url)
        sleep_time = 0
        while True:
            try:
                return (yield from self.osf_query.make_request(url, get_json=True))['data']
            except aiohttp.ClientError:
                pass
            sleep_time += 5
            logger.error('Unable to fetch user from OSF, sleeping for {} seconds'.format(sleep_time))
            yield from asyncio.sleep(sleep_time)

    def get_id(self, item):
        """
        This function determines the rules to get the id for a local or remote representation of nodes/files.
        The ways to get the id differ based on the input item type:
            local node -> osf_id ( this is node id (nid) on the OSF )
            local file -> osf_path (this is osf_path)hash(node.osf_id, provider name, osf path)
                ( note, osf path is the 'path' variable provided by waterbutler. It is represented as '/<unique waterbutler identifier>'
            remote node -> id (this is the node if (nid) on the OSF )
            remote file -> path ( this is the path ( '/<unique waterbutler identifier>' ) on the OSF )

        :param item: local (sql alchemy Base object) or remote (dict) representation of a node or file
        :return: the input items id
        """
        # if node/file is remote
        if isinstance(item, RemoteObject):
            return item.id
        elif isinstance(item, Base):
            if item.osf_id:
                return item.osf_id
            else:
                assert item.locally_created
                return "FAKE{}FAKE".format(item.id)
        else:
            raise InvalidItemType

    def make_local_remote_tuple_list(self, local_list, remote_list):
        """
        Create a list of tuples where the local and remote representation of the node/file are grouped together.
        This allows us to determine differences between the local and remote versions and perform appropriate functions
        on them. This tuple list is the backbone behind the polling scheme in this file.

        Notably, the connection between the local and remote is made in differing manners depending on whether
        the input is a node or file. Each input is given an id, as determined by the get function above.
        These id's are then matched to create a tuple. If an id has no match, it is matched with None.


        :param local_list: list of local node or file sql alchemy objects
        :param remote_list: list of dicts from the osf v2 api representing nodes or files
        :return: list of tuples with the left being the local version of node or file and
                 the right being the remote version. aka. [ (local, remote),... ]
        """
        assert None not in local_list
        assert None not in remote_list

        local_files = {}
        remote_files = {}

        for local in local_list:
            assert isinstance(local, Base)
            if isinstance(local, File) and local.name == '.DS_Store':
                continue
            local_files[local.osf_id] = local

        for remote in remote_list:
            assert isinstance(remote, RemoteObject)
            remote_files[remote.id] = remote

        return [
            (local_files.get(fid), remote_files.get(fid))
            for fid in set(list(local_files.keys()) + list(remote_files.keys()))
        ]

    @asyncio.coroutine
    def check_osf(self, remote_user):
        assert isinstance(remote_user, dict)
        assert remote_user['type'] == 'users'

        remote_user_id = remote_user['id']
        nodes_url = api_url_for(USERS, related_type=NODES, user_id=remote_user_id)

        while True:
            logger.info('Begining OSF poll')
            # get local top level nodes
            local_projects = self.user.top_level_nodes

            remote_projects = yield from self.osf_query.get_top_level_nodes(nodes_url)

            paired_projects = self.make_local_remote_tuple_list(local_projects, remote_projects)

            session.refresh(self.user)

            sync_list = self.user.guid_for_top_level_nodes_to_sync
            logger.debug('sync list is: {}'.format(sync_list))

            for local, remote in paired_projects:
                if not remote or remote.id not in sync_list:
                    continue
                yield from self.check_node(local, remote, local_parent_node=None)

            yield from self.queue.join()

            AlertHandler.up_to_date()
            logger.debug('---------SHOULD HAVE ALL OSF FILES---------')

            yield from asyncio.sleep(POLL_DELAY)

    @asyncio.coroutine
    def check_node(self, local_node, remote_node, local_parent_node):
        """
        Responsible for checking whether local node values are same as remote node.
        Values to be checked include: files and folders, name, metadata, child nodes

        VARIOUS STATES (update as neccessary):
        (None, None) -> Error                       --
        (None, remote) -> create local              --
        (local.create, None) -> create remote       --
        (local.create, remote) -> ERROR             --
        (local.delete, None) -> ERROR               --
        (local.delete, remote) - > delete remote    --
        (local, None) -> delete local               --
        (local, remote) -> check modifications      --

        """
        logger.debug('checking node')
        assert (local_node is not None) or (remote_node is not None)  # both shouldnt be none.
        assert (local_parent_node is None) or isinstance(local_parent_node, Node)

        if local_node is None:
            local_node = yield from self.create_local_node(remote_node, local_parent_node)
        elif local_node is not None and remote_node is None:
            yield from self.delete_local_node(local_node)
            return
        elif local_node is not None and remote_node is not None:
            if local_node.title != remote_node.name:
                yield from self.modify_local_node(local_node, remote_node)

        # handle file_folders for node
        yield from self.check_file_folder(local_node, remote_node)

        # ensure that local node has Components folder
        yield from self._ensure_components_folder(local_node)

        # recursively handle node's children
        remote_children = yield from self.osf_query.get_child_nodes(remote_node)

        local_remote_nodes = self.make_local_remote_tuple_list(local_node.child_nodes, remote_children)
        for local, remote in local_remote_nodes:
            yield from self.check_node(local, remote, local_parent_node=local_node)

    @asyncio.coroutine
    def check_file_folder(self, local_node, remote_node):
        logger.debug('checking file_folder')
        # todo: probably can put this step into get_child_files for nodes.
        # fixme: doesnt handle multiple providers right now...

        try:
            remote_node_files = yield from self.osf_query.get_child_files(remote_node)
        except aiohttp.errors.HttpBadRequest:
            AlertHandler.warn(
                'could not access files for node {}. Node might have been deleted.'.format(remote_node.name))
            return

        assert len(remote_node_files) >= 1
        for node_file in remote_node_files:
            if node_file.name == 'osfstorage':
                osfstorage_folder = node_file
        assert osfstorage_folder

        try:
            remote_node_top_level_file_folders = yield from self.osf_query.get_child_files(osfstorage_folder)
        except aiohttp.errors.HttpBadRequest:
            AlertHandler.warn(
                'could not access files for node {}. Node might have been deleted.'.format(remote_node.name))
            return

        local_remote_files = self.make_local_remote_tuple_list(
            local_node.top_level_file_folders,
            remote_node_top_level_file_folders
        )

        for local, remote in local_remote_files:
            yield from self._check_file_folder(
                local,
                remote,
                local_parent_file_folder=None,
                local_node=local_node
            )

    @asyncio.coroutine
    def _check_file_folder(self,
                           local_file_folder,
                           remote_file_folder,
                           local_parent_file_folder,
                           local_node):
        """
        VARIOUS STATES (update as neccessary):
        (None, None) -> Error                                     --
        (None, remote) ->
            if locally moved -> do nothing
            else -> create local
        (local.create, None) -> create remote                     --
        (local.create, remote) -> ERROR                           --
        (local.delete, None) -> ERROR                             --
        (local.delete, remote) - > delete remote                  --
        (local, None) ->
            if locally moved -> move
            else -> delete local
        (local, remote) -> check modifications                    --

        """

        assert local_file_folder or remote_file_folder  # both shouldnt be None.
        logger.debug('checking file_folder internal')
        if local_file_folder is None:
            locally_moved = yield from self.is_locally_moved(remote_file_folder)
            if locally_moved:
                return
            else:
                local_file_folder = yield from self.create_local_file_folder(
                    remote_file_folder,
                    local_parent_file_folder,
                    local_node
                )
        elif local_file_folder.locally_created and remote_file_folder is None:
            if not local_file_folder.is_provider:
                remote_file_folder = yield from self.create_remote_file_folder(local_file_folder, local_node)
            return
        elif local_file_folder.locally_created and remote_file_folder is not None:
            raise ValueError('newly created local file_folder was already on server')
        elif local_file_folder.locally_deleted and remote_file_folder is None:
            session.delete(local_file_folder)
            save(session)
            logger.warning('local file_folder is to be deleted, however, it was never on the server.')
            return
        elif local_file_folder.locally_deleted and remote_file_folder is not None:
            yield from self.delete_remote_file_folder(local_file_folder, remote_file_folder)
            return
        elif local_file_folder is not None and remote_file_folder is None:
            if local_file_folder.locally_moved:
                # todo: we are ignoring return value for now because to start going down new tree would require
                # todo: us to have the new node. we currently use the head node instead of dynamically determining
                # todo: node. This is problematic. And Bad. FIX IT.
                remote_file_folder = yield from self.move_remote_file_folder(local_file_folder)
                return
            else:
                logger.warning('delete_local_file_folder called on {}'.format(local_file_folder.name))
                yield from self.delete_local_file_folder(local_file_folder)
                return
        elif local_file_folder is not None and remote_file_folder is not None:
            possibly_new_remote_file_folder = yield from self.modify_file_folder_logic(local_file_folder,
                                                                                       remote_file_folder)
            # if we do not need to modify things, remote file folder and local file folder does not change
            # we do not need to get a new local file folder because it is updated internally by the db
            if possibly_new_remote_file_folder:
                remote_file_folder = possibly_new_remote_file_folder
        else:
            raise ValueError('in some weird state. figure it out.')

        assert local_file_folder is not None
        assert remote_file_folder is not None

        # recursively handle folder's children
        if local_file_folder.is_folder:

            remote_children = yield from self.osf_query.get_child_files(remote_file_folder)

            local_remote_file_folders = self.make_local_remote_tuple_list(local_file_folder.files, remote_children)

            for local, remote in local_remote_file_folders:
                yield from self._check_file_folder(
                    local,
                    remote,
                    local_parent_file_folder=local_file_folder,
                    local_node=local_node
                )

                    # if we are unable to get children, then we do not try to get and manipulate children

    # Create
    @asyncio.coroutine
    def create_local_node(self, remote_node, local_parent_node):
        logger.debug('create_local_node')
        assert isinstance(remote_node, RemoteNode)
        assert isinstance(local_parent_node, Node) or local_parent_node is None

        # create local node in db
        category = Node.PROJECT if remote_node.category == 'project' else Node.COMPONENT
        new_node = Node(
            title=remote_node.name,
            category=category,
            osf_id=remote_node.id,
            user=self.user,
            parent=local_parent_node
        )
        save(session, new_node)

        if local_parent_node:
            yield from self._ensure_components_folder(local_parent_node)
        yield from self.queue.put(CreateFolder(new_node.path))
        yield from self._ensure_components_folder(new_node)

        assert local_parent_node is None or (new_node in local_parent_node.child_nodes)
        return new_node

    @asyncio.coroutine
    def create_local_file_folder(self, remote_file_folder, local_parent_folder, local_node):
        logger.debug('creating local file folder')
        assert remote_file_folder is not None
        assert isinstance(remote_file_folder, RemoteFileFolder)
        assert isinstance(local_parent_folder, File) or local_parent_folder is None
        assert local_parent_folder is None or (local_parent_folder.is_folder)
        assert isinstance(local_node, Node)

        # NOTE: develop is not letting me download files. dont know why.

        # create local file folder in db
        file_type = File.FILE if isinstance(remote_file_folder, RemoteFile) else File.FOLDER
        new_file_folder = File(
            name=remote_file_folder.name,
            type=file_type,
            osf_id=remote_file_folder.id,
            provider=remote_file_folder.provider,
            osf_path=remote_file_folder.id,
            user=self.user,
            parent=local_parent_folder,
            node=local_node
        )
        save(session, new_file_folder)

        if file_type == File.FILE:
            event = CreateFile(
                path=new_file_folder.path,
                download_url=remote_file_folder.download_url,
                osf_query=self.osf_query
            )
            yield from self.queue.put(event)
        elif file_type == File.FOLDER:
            yield from self.queue.put(CreateFolder(new_file_folder.path))
        else:
            raise ValueError('file type is unknown')

        return new_file_folder

    @asyncio.coroutine
    def create_remote_file_folder(self, local_file_folder, local_node):
        logger.debug('create_remote_file_folder')
        assert local_file_folder is not None
        assert isinstance(local_file_folder, File)
        assert local_node is not None
        assert isinstance(local_node, Node)
        assert local_file_folder.locally_created

        if local_file_folder.is_folder:
            remote_file_folder = yield from self.osf_query.upload_folder(local_file_folder)
        elif local_file_folder.is_file:
            try:
                remote_file_folder = yield from self.osf_query.upload_file(local_file_folder)
            except FileNotFoundError:
                logger.warning('file not created on remote server because does not exist locally: {}'.format(
                    local_file_folder.name))
                return

        local_file_folder.osf_id = remote_file_folder.id
        local_file_folder.osf_path = remote_file_folder.id
        local_file_folder.locally_created = False

        save(session, local_file_folder)

        return remote_file_folder

    # Modify
    @asyncio.coroutine
    def modify_local_node(self, local_node, remote_node):
        logger.debug('modify_local_node')
        assert isinstance(local_node, Node)
        assert isinstance(remote_node, RemoteNode)
        assert remote_node.id == local_node.osf_id

        old_path = local_node.path
        local_node.title = remote_node.name

        local_node.category = remote_node.category

        save(session, local_node)

        yield from self.queue.put(RenameFolder(old_path, local_node.path))

    @asyncio.coroutine
    def modify_file_folder_logic(self, local_file_folder, remote_file_folder):
        assert isinstance(local_file_folder, File)
        assert isinstance(remote_file_folder, RemoteFileFolder)

        updated_remote_file_folder = None
        # this handles both files and folders being renamed
        if local_file_folder.name != remote_file_folder.name:
            # TODO: we are using a heuristic to determine if a folder is renamed. The heuristic is
            # TODO: that there is a flag set locally when a folder is renamed. If the flag is set, then
            # TODO: we update the remote folder. The issue occurs when both the local folder and remote
            # TODO: folder are renamed. Which is newer? We don't know.

            # TODO: this is also the case for files because a change in a file name does NOT warrant
            # TODO: updating the modified field on the OSF.
            if local_file_folder.locally_renamed:
                updated_remote_file_folder = yield from self.rename_remote_file_folder(local_file_folder,
                                                                                       remote_file_folder)
            else:
                yield from self.rename_local_file_folder(local_file_folder, remote_file_folder)

        # if file size is different, then only do you  bother checking whether to upload or to download
        if local_file_folder.is_file and local_file_folder.size != remote_file_folder.size:  # todo: local_file_folder.hash != remote_file_folder.size
            if (yield from self.local_file_is_newer(local_file_folder, remote_file_folder)):
                updated_remote_file_folder = yield from self.update_remote_file(local_file_folder, remote_file_folder)
            elif (yield from self.remote_file_is_newer(local_file_folder, remote_file_folder)):
                yield from self.update_local_file(local_file_folder, remote_file_folder)

        # want to have the remote file folder continue to be the most recent version.
        return updated_remote_file_folder

    @asyncio.coroutine
    def rename_local_file_folder(self, local_file_folder, remote_file_folder):
        logger.debug('rename_local_file_folder')
        assert isinstance(local_file_folder, File)
        assert isinstance(remote_file_folder, RemoteFileFolder)
        assert remote_file_folder.id == local_file_folder.osf_path

        # handle renaming local file and local folder
        old_path = local_file_folder.path
        # update model
        local_file_folder.name = remote_file_folder.name

        save(session, local_file_folder)

        if local_file_folder.is_folder:
            yield from self.queue.put(RenameFolder(old_path, local_file_folder.path))
        elif local_file_folder.is_file:
            yield from self.queue.put(RenameFile(old_path, local_file_folder.path))

    @asyncio.coroutine
    def update_local_file(self, local_file, remote_file):
        assert isinstance(local_file, File)
        assert isinstance(remote_file, RemoteFile)
        assert remote_file.id == local_file.osf_path

        # update model
        # nothing to update. size, hash are all updated internally as the event occurs.

        # update local file system
        event = UpdateFile(
            path=local_file.path,
            download_url=remote_file.download_url,
            osf_query=self.osf_query
        )
        yield from self.queue.put(event)

    @asyncio.coroutine
    def update_remote_file(self, local_file, remote_file):
        logger.debug('update_remote_file')
        assert isinstance(local_file, File)
        assert isinstance(remote_file, RemoteFile)
        assert remote_file.id == local_file.osf_path

        try:
            new_remote_file = yield from self.osf_query.upload_file(local_file)
        except FileNotFoundError:
            logger.warning(
                'file not reuploaded on remote server because does not exist locally. inside create_remote_file_folder')
            return remote_file

        return new_remote_file

    @asyncio.coroutine
    def rename_remote_file_folder(self, local_file_folder, remote_file_folder):
        logger.debug('rename_remote_file_folder.')
        assert isinstance(local_file_folder, File)
        assert isinstance(remote_file_folder, RemoteFileFolder)
        assert remote_file_folder.id == local_file_folder.osf_path
        assert local_file_folder.name != remote_file_folder.name

        if local_file_folder.is_file:
            new_remote_file_folder = yield from self.osf_query.rename_remote_file(local_file_folder, remote_file_folder)
        else:  # if local_file_folder.is_folder:
            new_remote_file_folder = yield from self.osf_query.rename_remote_folder(local_file_folder,
                                                                                    remote_file_folder)

        return new_remote_file_folder

    @asyncio.coroutine
    def move_remote_file_folder(self, local_file_folder):
        logger.debug('move_remote_file_folder.')
        assert isinstance(local_file_folder, File)

        if local_file_folder.is_file:
            new_remote_file_folder = yield from self.osf_query.move_remote_file(local_file_folder)
        else:  # if local_file_folder.is_folder:
            new_remote_file_folder = yield from self.osf_query.move_remote_folder(local_file_folder)

        return new_remote_file_folder

    # Delete
    @asyncio.coroutine
    def delete_local_node(self, local_node):
        logger.debug('delete_local_node')
        assert isinstance(local_node, Node)

        path = local_node.path

        # delete model
        session.delete(local_node)
        save(session)

        yield from self.queue.put(DeleteFolder(path))

    @asyncio.coroutine
    def delete_local_file_folder(self, local_file_folder):
        logger.debug('delete_local_file_folder')
        assert isinstance(local_file_folder, File)

        path = local_file_folder.path
        is_folder = local_file_folder.is_folder
        # delete model
        session.delete(local_file_folder)
        save(session)

        # delete from local
        if is_folder:
            yield from self.queue.put(DeleteFolder(path))
        else:
            yield from self.queue.put(DeleteFile(path))

    @asyncio.coroutine
    def delete_remote_file_folder(self, local_file_folder, remote_file_folder):
        logger.debug('delete_remote_file_folder')
        assert local_file_folder is not None
        assert remote_file_folder is not None
        assert local_file_folder.osf_id == self.get_id(remote_file_folder)
        assert local_file_folder.locally_deleted

        if local_file_folder.is_file:
            yield from self.osf_query.delete_remote_file(remote_file_folder)
        elif local_file_folder.is_folder:
            yield from self.osf_query.delete_remote_folder(remote_file_folder)

        local_file_folder.deleted = False
        session.delete(local_file_folder)
        save(session)

    @asyncio.coroutine
    def _get_local_remote_times(self, local, remote):
        assert isinstance(local, File)
        assert isinstance(remote, RemoteFile)

        local_time = local.date_modified.replace(tzinfo=iso8601.iso8601.Utc())
        # NOTE; waterbutler does NOT update time when a file or folder is RENAMED.
        # thus cannot accurately determine when file/folder was renamed.
        # thus, going to have to go with local is pretty much always newer.
        # NOTE: based on above note, it is a better idea to go with the .locally_renamed idea.
        remote_time = remote.last_modified

        return local_time, remote_time

    # NOTE: waterbutler does not give a 'modified' time to something that has been created.
    # THUS, if we are modifying something and remote is None, the modification MUST be coming from local.

    @asyncio.coroutine
    def local_file_is_newer(self, local, remote):
        assert isinstance(local, File)
        assert isinstance(remote, RemoteFile)

        try:
            local_time, remote_time = yield from self._get_local_remote_times(local, remote)
            return local_time > remote_time
        except iso8601.ParseError:
            # TODO: if there are parsing issues with the time then we fall back to comparing sizes.
            return local.size > remote.size

    @asyncio.coroutine
    def remote_file_is_newer(self, local, remote):
        assert isinstance(local, File)
        assert isinstance(remote, RemoteFile)

        try:
            local_time, remote_time = yield from self._get_local_remote_times(local, remote)
            return local_time < remote_time
        except iso8601.ParseError:
            # TODO: if there are parsing issues with the time then we fall back to comparing sizes.
            return local.size < remote.size

    @asyncio.coroutine
    def is_locally_moved(self, remote):
        assert isinstance(remote, RemoteObject)
        try:
            local = yield from self.get_local_from_remote(remote)
            return local.locally_moved
        except (MultipleResultsFound, NoResultFound):
            return False

    @asyncio.coroutine
    def get_local_from_remote(self, remote):
        assert isinstance(remote, RemoteObject)

        if isinstance(remote, RemoteNode):
            cls = Node
        elif isinstance(remote, RemoteFileFolder):
            cls = File
        else:
            raise InvalidItemType

        return session.query(cls).filter(cls.osf_id == remote.id).one()

    @asyncio.coroutine
    def _ensure_components_folder(self, local_node):
        assert isinstance(local_node, Node)
        if local_node.child_nodes:
            yield from self.queue.put(
                CreateFolder(
                    os.path.join(local_node.path, 'Components')
                )
            )
