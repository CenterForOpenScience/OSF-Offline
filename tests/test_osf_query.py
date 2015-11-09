__author__ = 'himanshu'

from unittest import TestCase
from osfoffline.polling_osf_manager.remote_objects import RemoteFile,RemoteFileFolder,RemoteObject,RemoteFolder,RemoteNode,RemoteUser
from osfoffline.polling_osf_manager.osf_query import OSFQuery
import asyncio
from tests.utils.decorators import async
from osfoffline.polling_osf_manager.api_url_builder import api_url_for, NODES, USERS, CHILDREN
class TestRemoteObjects(TestCase):

    def setUp(self):
        # fixme: currently this is static. Need to make this work in general. ONCE you have a mock response thing working.
        self.user_id = '5bqt9'
        self._loop = asyncio.new_event_loop()
        self.osf_query = OSFQuery(self._loop, self.user_id)

    def tearDown(self):
        self.osf_query.close()

    @async
    def test_get_all_paginated_users(self):
        url = api_url_for(NODES,related_type=CHILDREN, node_id=1)
        print(url)
        children = yield from self.osf_query._get_all_paginated_members(url)
        self.assertEquals(children, [])