__author__ = 'himanshu'
import json

from unittest import TestCase
import requests
from tests.fixtures.mock_httpretty_responses.setup_fake_osf import setup_mock_osf_api
import httpretty
from osfoffline.polling_osf_manager.remote_objects import *

class TestRemoteObjects(TestCase):

    @httpretty.activate
    def setUp(self):
        setup_mock_osf_api()


        self.created_user = RemoteUser(requests.post('http://localhost:8000/v2/users/',data={'fullname':'hi'}).json()['data'])
        assert self.created_user.name == 'hi'
        headers = {'Authorization':'Bearer {}'.format(self.created_user.id)}
        self.user_resp = requests.get('http://localhost:8000/v2/users/{}/'.format(self.created_user.id), headers=headers).json()['data']
        self.created_node = RemoteNode(requests.post('http://localhost:8000/v2/nodes/', data={'title':'new_node'}, headers=headers).json()['data'])
        assert self.created_node.name == 'new_node'


        self.node_resp = requests.get(self.user_resp['links']['nodes']['relation'], headers=headers).json()['data'][0]



        self.folder_provider_resp = requests.get(self.node_resp['links']['files']['related'], headers=headers).json()['data'][0]

        params = {
            'path': '/FUN_FOLDER',
            'nid':self.created_node.id,
            'provider':'osfstorage'
        }
        self.created_folder= RemoteFolder(
            requests.post('http://localhost:7777/file',params=params, headers=headers).json()['data']
        )
        assert self.created_folder.name == 'FUN_FOLDER'

        self.folder_resp = requests.get(self.folder_provider_resp['links']['related'], headers=headers).json()['data'][0]
        # self.folder2_resp =requests.get(self.folder_provider_resp['links']['related'], headers=headers).json()['data'][1]

        # self.file_resp = requests.get(self.folder2_resp['links']['related'], headers=headers).json()['data'][0]

    @httpretty.activate
    def test_object(self):
        RemoteObject(self.user_resp)
        # RemoteObject(self.node_resp)
        # RemoteObject(self.folder_provider_resp)
        # RemoteObject(self.folder2_resp)
    #     RemoteObject(self.file_resp)
    #
    # def test_user(self):
    #     temp = RemoteUser(self.user_resp)
    #     assert self.created_user.id == temp.id
    #
    # def test_node(self):
    #     temp = RemoteNode(self.node_resp)
    #     assert self.created_node.id == temp.id
    #
    # def test_file_folder(self):
    #     RemoteFileFolder(self.folder_provider_resp)
    #     RemoteFileFolder(self.folder2_resp)
    #     RemoteFileFolder(self.file_resp)
    #
    # def test_file(self):
    #     RemoteFile(self.file_resp)
    #
    # def test_folder(self):
    #     RemoteFolder(self.folder_provider_resp)
    #     RemoteFolder(self.folder2_resp)