__author__ = 'himanshu'
import json

from unittest import TestCase
import requests
from osfoffline.polling_osf_manager.remote_objects import *
from osfoffline.polling_osf_manager.api_url_builder import api_url_for, USERS, NODES, FILES, CHILDREN

class TestRemoteObjects(TestCase):


    def setUp(self):

        self.created_user = RemoteUser(requests.post(api_url_for(USERS),data={'fullname':'hi'}).json()['data'])
        assert self.created_user.name == 'hi'
        headers = {'Authorization':'Bearer {}'.format(self.created_user.id)}

        self.session = requests.Session()
        self.session.headers.update(headers)

        self.user_resp = self.session.get(api_url_for(USERS, user_id=self.created_user.id)).json()['data']
        self.created_node = RemoteNode(self.session.post(api_url_for(NODES), data={'title':'new_node'}).json()['data'])
        assert self.created_node.name == 'new_node'

        self.node_resp = self.session.get(self.user_resp['relationships']['nodes']['links']['related']).json()['data'][0]

        self.folder_provider_resp = self.session.get(self.node_resp['relationships']['files']['links']['related'], headers=headers).json()['data'][0]

        params = {
            'name':'FUN_FOLDER'
        }
        self.created_folder= RemoteFolder(
            self.session.put(self.folder_provider_resp['links']['new_folder'], params=params, headers=headers).json()['data']
        )
        assert self.created_folder.name == 'FUN_FOLDER'

        #create another folder
        self.session.put(self.folder_provider_resp['links']['new_folder'],params={'name':'another folder'}, headers=headers).json()['data']

        self.folder_resp = self.session.get(self.folder_provider_resp['relationships']['files']['links']['related']['href'], headers=headers).json()['data'][0]
        self.folder2_resp =self.session.get(self.folder_provider_resp['relationships']['files']['links']['related']['href'], headers=headers).json()['data'][1]

        #create file with contents
        self.file_contents = ''.join(chr(x) for x in range(128))
        self.session.put(self.folder2_resp['links']['upload'], headers=headers, params={'name':'myfile.txt'}, data=self.file_contents).json()

        self.file_resp = self.session.get(self.folder2_resp['relationships']['files']['links']['related']['href'], headers=headers).json()['data'][0]


    def test_object(self):
        RemoteObject(self.user_resp)
        RemoteObject(self.node_resp)
        RemoteObject(self.folder_provider_resp)
        RemoteObject(self.folder2_resp)
        RemoteObject(self.file_resp)

    def test_user(self):
        temp = RemoteUser(self.user_resp)
        assert self.created_user.id == temp.id

    def test_node(self):
        temp = RemoteNode(self.node_resp)
        assert self.created_node.id == temp.id

    def test_file_folder(self):
        RemoteFileFolder(self.folder_provider_resp)
        RemoteFileFolder(self.folder2_resp)
        RemoteFileFolder(self.file_resp)

    def test_file(self):
        file = RemoteFile(self.file_resp)
        # download_request = self.session.get(file.download_url)
        # print(str(download_request.content))
        # print(str(self.file_contents))
        # assert download_request.content == self.file_contents
        # todo: check to make sure that file contents are the same as what we originally wanted

    def test_folder(self):
        RemoteFolder(self.folder_provider_resp)
        RemoteFolder(self.folder2_resp)