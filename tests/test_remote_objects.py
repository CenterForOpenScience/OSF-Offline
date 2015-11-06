__author__ = 'himanshu'
import json
from furl import furl
from osfoffline.settings import API_BASE
from unittest import TestCase
import requests
from tests.utils.url_builder import api_user_url, api_user_nodes, api_file_children,api_node_files
from osfoffline.polling_osf_manager.remote_objects import RemoteFile,RemoteFileFolder,RemoteObject,RemoteFolder,RemoteNode,RemoteUser

from tests.fixtures.mock_httpretty_responses.osf_api import (
    create_new_user,
    create_new_top_level_node,
    get_user, get_user_nodes,
    create_provider_folder,
    get_providers_for_node,
    create_new_folder,
    create_new_file,
    get_children_for_folder
)

import httpretty

class TestRemoteObjects(TestCase):

    def register_user_url(self, user):
        httpretty.register_uri(
            httpretty.GET,
            api_user_url(user.id),
            body=get_user,
            content_type="application/json"
        )

    def register_user_nodes_url(self, user):

        httpretty.register_uri(
            httpretty.GET,
            api_user_nodes(user.id),
            body=get_user_nodes,
            content_type="application/json"
        )

    def register_node_providers_url(self, node):
        httpretty.register_uri(
            httpretty.GET,
            api_node_files(node.id),
            body=get_providers_for_node,
            content_type="application/json"
        )

    def register_folder_children_url(self, folder):

        httpretty.register_uri(
            httpretty.GET,
            api_file_children(folder.node.id, folder.path, folder.provider),
            body=get_children_for_folder,
            content_type="application/json"
        )

    @httpretty.activate
    def setUp(self):
        user = create_new_user()

        self.register_user_url(user)

        headers = {'Authorization':'Bearer {}'.format(user.id)}
        self.user_resp = requests.get(api_user_url(user.id), headers=headers).json()['data']

        node = create_new_top_level_node(user)
        self.register_user_nodes_url(user)

        self.node_resp = requests.get(self.user_resp['links']['nodes']['relation'], headers=headers).json()['data'][0]

        provider_folder = create_provider_folder(node)
        self.register_node_providers_url(node)
        self.folder_provider_resp = requests.get(self.node_resp['links']['files']['related'], headers=headers).json()['data'][0]

        folder1 = create_new_folder(provider_folder)
        folder2 = create_new_folder(provider_folder)
        file = create_new_file(folder2)
        self.register_folder_children_url(provider_folder)
        self.register_folder_children_url(folder1)
        self.register_folder_children_url(folder2)
        # http://localhost:8000/v2/nodes/1/files?path=/&provider=osfstorage
        self.folder2_resp =requests.get(self.folder_provider_resp['links']['related'], headers=headers).json()['data'][1]


        self.file_resp = requests.get(self.folder2_resp['links']['related'], headers=headers).json()['data'][0]


    def test_object(self):
        RemoteObject(self.user_resp)
        RemoteObject(self.node_resp)
        RemoteObject(self.folder_provider_resp)
        RemoteObject(self.folder2_resp)
        RemoteObject(self.file_resp)

    def test_user(self):
        RemoteUser(self.user_resp)

    def test_node(self):
        RemoteNode(self.node_resp)

    def test_file_folder(self):
        RemoteFileFolder(self.folder_provider_resp)
        RemoteFileFolder(self.folder2_resp)
        RemoteFileFolder(self.file_resp)

    def test_file(self):
        RemoteFile(self.file_resp)

    def test_folder(self):
        RemoteFolder(self.folder_provider_resp)
        RemoteFolder(self.folder2_resp)