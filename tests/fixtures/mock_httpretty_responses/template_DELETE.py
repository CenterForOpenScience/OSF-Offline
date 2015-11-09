# __author__ = 'himanshu'
# import json
# from osfoffline.polling_osf_manager.api_url_builder import api_user_nodes, api_file_children, wb_file_url
# import furl
# from osfoffline.settings import API_BASE, WB_BASE
#
# ############################  User #####################
# GENERIC_USER={
#     "data": {
#         "id": "1",
#         "fullname": "himanshu",
#         "given_name": "himanshu",
#         "middle_name": "",
#         "family_name": "",
#         "suffix": "",
#         "date_registered": "2015-07-06T17:51:22.833000",
#         "gravatar_url": "https://secure.gravatar.com/avatar/7241b93c02e7d393e5f118511880734a?d=identicon&size=40",
#         "employment_institutions": [],
#         "educational_institutions": [],
#         "social_accounts": {},
#         "links": {
#             "nodes": {
#                 "relation": "http://localhost:8000/v2/users/5bqt9/nodes/"
#             },
#             "html": "http://localhost:5000/5bqt9/",
#             "self": "http://localhost:8000/v2/users/5bqt9/"
#         },
#         "type": "users"
#     }
# }
# class User(object):
#     INDEX = -1
#     def __init__(self, id):
#         self.id = id
#         self.fullname = 'User {}'.format(self.id)
#         self.top_level_node_ids = []
#
#     def to_json(self):
#         u = GENERIC_USER['data']
#         u['id'] = self.id
#         u['fullname']=self.fullname
#         u['given_name']=self.fullname
#         u['links']['nodes']['relation'] = api_user_nodes(self.id)
#         base = furl.furl(WB_BASE)
#         base.path.segments = [str(self.id)]
#         u['links']['html'] = base.url
#         base = furl.furl(API_BASE)
#         base.path.segments = ['v2','users',str(self.id)]
#         u['links']['self'] = base.url
#         resp = {
#            'data':u
#         }
#         return json.dumps(resp)
#
#     @classmethod
#     def new_user(cls):
#         cls.INDEX += 1
#         id = 'UID_{}'.format(cls.INDEX)
#         return cls(id)
#
# ############################  Node  #####################
# GENERIC_NODE= {
#             "id": "dz5mg",
#             "title": "new_test_project",
#             "description": "",
#             "category": "project",
#             "date_created": "2015-07-24T15:56:27.851000",
#             "date_modified": "2015-07-24T19:35:16.502000",
#             "tags": {
#                 "system": [],
#                 "user": []
#             },
#             "links": {
#                 "files": {
#                     "related": "http://localhost:8000/v2/nodes/dz5mg/files/"
#                 },
#                 "parent": {
#                     "self": None
#                 },
#                 "contributors": {
#                     "count": 1,
#                     "related": "http://localhost:8000/v2/nodes/dz5mg/contributors/"
#                 },
#                 "pointers": {
#                     "count": 0,
#                     "related": "http://localhost:8000/v2/nodes/dz5mg/pointers/"
#                 },
#                 "registrations": {
#                     "count": 0,
#                     "related": "http://localhost:8000/v2/nodes/dz5mg/registrations/"
#                 },
#                 "self": "http://localhost:8000/v2/nodes/dz5mg/",
#                 "html": "http://localhost:5000/dz5mg/",
#                 "children": {
#                     "count": 0,
#                     "related": "http://localhost:8000/v2/nodes/dz5mg/children/"
#                 }
#             },
#             "properties": {
#                 "dashboard": False,
#                 "collection": False,
#                 "registration": False
#             },
#             "public": False,
#             "type": "nodes"
# }
#
# class Node(object):
#     INDEX = -1
#     def __init__(self, id, user_id, parent_id, category='project'):
#         self.id = id
#         self.user_id = user_id
#         self.title = 'Node {}'.format(self.id)
#         self.category = category
#         self.child_nodes = []
#         self.provider_folder_id = None
#         self.parent_id = parent_id
#
#     def to_dict(self):
#         u = GENERIC_NODE
#         u['id'] = self.id
#         u['title'] = self.title
#         u['category']=self.category
#         u['links']['files']['related'] = api_file_children(self.user_id, self.provider_folder_id.path, self.provider_folder_id.provider)
#         # http://localhost:8000/v2/nodes/dz5mg/children/
#         base = furl.furl(API_BASE)
#         base.path.segments = ['v2','nodes',str(self.id), 'children']
#         u['links']['children']['related'] = base.url
#
#         base = furl.furl(API_BASE)
#         base.path.segments = ['v2','users',str(self.id)]
#         u['links']['self'] = base.url
#
#         u['links']['parent']['self'] = self.parent_id
#
#         resp = {
#            'data':u
#         }
#         return resp
#
#     def to_json(self):
#         return json.dumps(self.to_dict())
#
#     @classmethod
#     def new_node(cls, user_id,parent_id, category='project'):
#         cls.INDEX +=1
#         return cls('NODE_ID_{}'.format(cls.INDEX), user_id,parent_id, category)
#
# ############################  Folder #####################
# GENERIC_FOLDER={
#             "provider": "osfstorage",
#             "path": "/",
#             "item_type": "folder",
#             "name": "osfstorage",
#             "metadata": {},
#             "links": {
#                 "self_methods": [
#                     "POST"
#                 ],
#                 "self": "http://localhost:7777/file?path=/&nid=dz5mg&provider=osfstorage&cookie=55b293744122ea78d77796a9.2eJIuhNAejbfwWK2GmazhkfFKYY",
#                 "related": "http://localhost:8000/v2/nodes/dz5mg/files/?path=/&provider=osfstorage"
#             },
#             "type": "files"
# }
#
# class Folder(object):
#     INDEX = -1
#     def __init__(self, id, nid, user_id, is_provider=False):
#         self.id = id
#         self.provider = 'osfstorage'
#         self.nid = nid
#         self.user_id=user_id
#         if is_provider:
#             self.path = '/'
#             self.name = self.provider
#         else:
#             self.path =  'PATH {}'.format(self.id)
#             self.name = 'Folder {}'.format(self.id)
#
#         self.children=[]
#
#     def to_json(self):
#         u = GENERIC_FOLDER['data']
#         u['provider'] = self.provider
#         u['path'] = self.path
#         u['name']=self.name
#         u['links']['self'] = wb_file_url(nid=self.nid, path=self.path, provider=self.provider)
#         u['links']['self'] = api_file_children(self.user_id, self.path, self.provider)
#
#         resp = {
#            'data':u
#         }
#
#         return json.dumps(resp)
#
#     @classmethod
#     def new_folder(cls, nid, user_id, is_provider=False):
#         cls.INDEX +=1
#         return cls(cls.INDEX, nid, user_id, is_provider)
#
# ############################  File #####################
# GENERIC_FILE= {
#             "provider": "osfstorage",
#             "path": "/55b290134122ea78d7779656",
#             "item_type": "file",
#             "name": "mydoc",
#             "metadata": {
#                 "size": 12,
#                 "modified": None,
#                 "content_type": None,
#                 "extra": {
#                     "downloads": 5,
#                     "version": 2
#                 }
#             },
#             "links": {
#                 "self_methods": [
#                     "GET",
#                     "POST",
#                     "DELETE"
#                 ],
#                 "self": "http://localhost:7777/file?path=/55b290134122ea78d7779656&nid=dz5mg&provider=osfstorage&cookie=55b293744122ea78d77796a9.2eJIuhNAejbfwWK2GmazhkfFKYY",
#                 "related": "http://localhost:8000/v2/nodes/dz5mg/files/?path=/55b290134122ea78d7779656&provider=osfstorage"
#             },
#             "type": "files"
# }
#
# class File(object):
#     INDEX=-1
#     def __init__(self, id, user_id, nid):
#         self.id = id
#         self.provider = 'osfstorage'
#         self.path = 'PATH {}'.format(self.id)
#         self.name = 'FILE {}'.format(self.id)
#         self.size = 0
#         self.modified = None
#         self.user_id = user_id
#         self.nid = nid
#
#
#     def to_json(self):
#         file = GENERIC_FILE
#         file['provider']=self.provider
#         file['path']=self.path
#         file['name']=self.name
#         file['metadata']['size'] = self.size
#         file['metadata']['modified'] = self.modified
#         file['links']['self']= wb_file_url(path=self.path, nid=self.nid, provider=self.provider)
#         file['links']['related'] = api_file_children(self.user_id, self.path, self.provider)
#
#     @classmethod
#     def new_file(cls, user_id, nid):
#         cls.INDEX +=1
#         return cls(cls.INDEX, user_id, nid)