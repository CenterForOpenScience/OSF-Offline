import asyncio
import json
import concurrent
import logging

import aiohttp

from osfoffline.polling_osf_manager.remote_objects \
    import (dict_to_remote_object, RemoteFolder, RemoteFile, RemoteNode)
from osfoffline.database_manager.models import File
from osfoffline.polling_osf_manager.api_url_builder import api_url_for, NODES, RESOURCES, FILES
import osfoffline.alerts as AlertHandler

OK = 200
CREATED = 201
ACCEPTED = 202


class OSFQuery(object):
    def __init__(self, loop, oauth_token):
        self.headers = {
            'Authorization': 'Bearer {}'.format(oauth_token),
        }
        self.request_session = aiohttp.ClientSession(loop=loop, headers=self.headers)

    @asyncio.coroutine
    def _get_all_paginated_members(self, remote_url):
        remote_children = []

        # this is for the case that a new folder is created so does not have the proper links.
        if remote_url is None:
            return remote_children

        resp = yield from self.make_request(remote_url, get_json=True)

        remote_children.extend(resp['data'])
        while resp['links']['next']:
            resp = yield from self.make_request(resp['links']['next'], get_json=True)

            remote_children.extend(resp['data'])

        for child in remote_children:
            assert isinstance(child, dict)

        return remote_children

    @asyncio.coroutine
    def get_top_level_nodes(self, url):
        assert isinstance(url, str)
        all_remote_nodes = yield from self._get_all_paginated_members(url)
        remote_top_level_nodes = []
        for remote in all_remote_nodes:
            as_remote_node = RemoteNode(remote)

            if as_remote_node.is_top_level:
                remote_top_level_nodes.append(as_remote_node)
        for node in remote_top_level_nodes:
            assert node.is_top_level
        return remote_top_level_nodes

    @asyncio.coroutine
    def get_child_nodes(self, remote_node):
        assert isinstance(remote_node, RemoteNode)
        nodes = yield from self._get_all_paginated_members(remote_node.child_nodes_url)
        return [dict_to_remote_object(node) for node in nodes]

    @asyncio.coroutine
    def get_child_files(self, remote_node_or_folder):
        assert isinstance(remote_node_or_folder, RemoteNode) or isinstance(remote_node_or_folder, RemoteFolder)
        file_folders = yield from self._get_all_paginated_members(remote_node_or_folder.child_files_url)
        return [dict_to_remote_object(file_folder) for file_folder in file_folders]

    @asyncio.coroutine
    def download_file(self, remote_file):
        assert isinstance(remote_file, RemoteFile)
        file = yield from self.make_request(remote_file.download_url)
        return dict_to_remote_object(file)

    @asyncio.coroutine
    def upload_folder(self, local_folder):
        assert isinstance(local_folder, File)
        assert local_folder.is_folder
        # PUT /v1/resources/6/providers/osfstorage/21/?kind=folder&name=FUN_FOLDER HTTP/1.1" 200 -

        params = {
            'kind': 'folder',
            'name': local_folder.name,
        }
        files_url = api_url_for(
            RESOURCES,
            node_id=local_folder.node.osf_id,
            provider=local_folder.provider,
            file_id=local_folder.parent.osf_id if local_folder.has_parent else None
        )
        resp_json = yield from self.make_request(files_url, method="PUT", params=params, get_json=True)
        AlertHandler.info(local_folder.name, AlertHandler.UPLOAD)

        # todo: determine whether uploaded folder will contain api url for its children
        new_file_id = resp_json['data']['id'].split('/')[1]
        children_url = api_url_for(NODES, related_type=FILES, node_id=local_folder.node.osf_id,
                                   provider=local_folder.provider, file_id=new_file_id)
        resp_json['data']['relationships'] = {
            'files': {
                'links': {
                    'related': {
                        'href': children_url
                    }
                }
            }
        }
        # https://staging-api.osf.io/v2/nodes/4e6k8/files/osfstorage/562134f1029bdb6c230f2874/
        # ['relationships']['files']['links']['related']['href']

        return dict_to_remote_object(resp_json['data'])

    @asyncio.coroutine
    def upload_file(self, local_file):
        """
        THROWS FileNotFoundError !!!!!!
        :param local_file:
        :return:
        """
        assert isinstance(local_file, File)
        assert local_file.is_file
        # /v1/resources/6/providers/osfstorage/21/?kind=file&name=FUN_FILE HTTP/1.1" 200 -
        params = {
            'provider': local_file.provider,
            'name': local_file.name
        }

        parent_osf_id = local_file.parent.osf_id if local_file.has_parent else None
        files_url = api_url_for(RESOURCES, node_id=local_file.node.osf_id, provider=local_file.provider,
                                file_id=parent_osf_id)
        file = open(local_file.path, 'rb')
        resp_json = yield from self.make_request(files_url, method="PUT", params=params, data=file, get_json=True)
        AlertHandler.info(local_file.name, AlertHandler.UPLOAD)

        return RemoteFile(resp_json['data'])

    @asyncio.coroutine
    def rename_remote_file(self, local_file, remote_file):
        assert isinstance(local_file, File)
        assert local_file.is_file
        assert isinstance(remote_file, RemoteFile)

        return (yield from self._rename_remote(local_file, remote_file))

    @asyncio.coroutine
    def rename_remote_folder(self, local_folder, remote_folder):
        assert isinstance(local_folder, File)
        assert local_folder.is_folder
        assert isinstance(remote_folder, RemoteFolder)
        AlertHandler.info(local_folder.name, AlertHandler.MODIFYING)
        return (yield from self._rename_remote(local_folder, remote_folder))

    @asyncio.coroutine
    def _rename_remote(self, local, remote):
        url = remote.move_url

        data = {
            'action': 'rename',
            'rename': local.name
        }

        resp = yield from self.make_request(url, method="POST", data=json.dumps(data))
        resp.close()

        remote.name = local.name
        return remote

    # todo: evaluate merging move code with rename code?

    @asyncio.coroutine
    def move_remote_folder(self, local_folder):
        assert isinstance(local_folder, File)
        assert local_folder.is_folder
        assert local_folder.locally_moved
        assert not local_folder.is_provider
        AlertHandler.info(local_folder.name, AlertHandler.MOVING)
        return (yield from self._move_remote_file_folder(local_folder))

    @asyncio.coroutine
    def move_remote_file(self, local_file):
        assert isinstance(local_file, File)
        assert local_file.is_file
        assert local_file.locally_moved
        assert not local_file.is_provider
        AlertHandler.info(local_file.name, AlertHandler.MOVING)
        return (yield from self._move_remote_file_folder(local_file))

    @asyncio.coroutine
    def _move_remote_file_folder(self, local_file_folder):

        url = api_url_for(RESOURCES, node_id=local_file_folder.node.osf_id, provider=local_file_folder.provider,
                          file_id=local_file_folder.osf_id)

        data = {
            'action': 'move',
            'path': local_file_folder.parent.osf_path if local_file_folder.parent else '{}:{}'.format(
                local_file_folder.node_id, local_file_folder.provider),
            'rename': local_file_folder.name
        }

        resp = yield from self.make_request(url, method="POST", data=json.dumps(data))
        resp.close()

        local_file_folder.locally_moved = False

        # get the updated remote folder

        # inner_response = requests.get(remote_file_folder['links']['self'], headers=self.headers).json()
        # we know exactly what changed, so its faster to just change the remote dictionary rather
        # than making a new api call.

        # todo: can get the file folder from the osf by making request to parent file folder (local.parent.osf_id,)
        # todo: and then searching for the correct child based on osf_id.

        # todo: move can change NODE. THUS, need to REMOVE local_node=local_node in check_file_folder code...

        # for now, just going to stop synching this things children... NOT PROPER!!!!!
        # new_remote_file_folder = ...

        return None

    @asyncio.coroutine
    def delete_remote_file(self, remote_file):
        assert isinstance(remote_file, RemoteFile)
        yield from self._delete_file_folder(remote_file)
        AlertHandler.info(remote_file.name, AlertHandler.DELETING)

    @asyncio.coroutine
    def delete_remote_folder(self, remote_folder):
        assert isinstance(remote_folder, RemoteFolder)
        yield from self._delete_file_folder(remote_folder)
        AlertHandler.info(remote_folder.name, AlertHandler.DELETING)

    @asyncio.coroutine
    def _delete_file_folder(self, remote_file_folder):
        assert isinstance(remote_file_folder, RemoteFile) or isinstance(remote_file_folder, RemoteFolder)
        url = remote_file_folder.delete_url
        resp = yield from self.make_request(url, method='DELETE')
        resp.close()

    @asyncio.coroutine
    def make_request(self, url, method=None, params=None, expects=None, get_json=False, timeout=180, data=None):
        if method is None:
            method = 'GET'

        request = self.request_session.request(
            url=url,
            method=method.upper(),
            params=params,
            data=data
        )
        try:
            response = yield from asyncio.wait_for(request, timeout)
        except (
                aiohttp.errors.ClientTimeoutError, aiohttp.errors.ClientConnectionError,
                concurrent.futures._base.TimeoutError):
            # internally, if a timeout occurs, aiohttp tries up to 3 times. thus we already technically have retries in.
            AlertHandler.warn("Bad Internet Connection")
            raise
        except aiohttp.errors.BadHttpMessage:

            raise
        except aiohttp.errors.HttpMethodNotAllowed:

            raise
        except asyncio.TimeoutError:
            request.cancel()
            return


        if expects:
            if response.status not in expects:
                raise aiohttp.errors.BadStatusLine(response.status)
        elif 400 <= response.status < 600:
            content = yield from response.read()
            error_message = '[status code: {}]:: {} @url {}'.format(response.status, content, url)
            logging.error(error_message)
            self.close()
            raise aiohttp.errors.HttpBadRequest(error_message)

        if get_json:
            json_response = yield from response.json()
            return json_response
        return response

    def close(self):
        self.request_session.close()
