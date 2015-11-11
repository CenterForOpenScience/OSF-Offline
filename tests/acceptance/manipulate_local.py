__author__ = 'himanshu'
from decorator import decorator
import unittest
from nose import with_setup
import os
import json
import shutil
import requests
import time
from osfoffline.polling_osf_manager.api_url_builder import api_url_for, NODES, FILES, USERS
from osfoffline.polling_osf_manager.remote_objects import RemoteFile, RemoteFolder, RemoteFileFolder, dict_to_remote_object, RemoteUser, RemoteNode
osf_path = '/Users/himanshu/Desktop/OSF/'
base_project_name = 'new_test_project'
project_path = os.path.join(osf_path, base_project_name)
USER_ID = 'k92s7' # SET ME

# headers = {'Authorization':'Bearer {}'.format(USER_ID)}
headers={'Cookie':'osf_staging=55fc5f29029bdb53541b5cda.wTLtvhA3IyD-UGpB3pr7YXIWHvc;'}
session = requests.Session()
session.headers.update(headers)
files_dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'files')
def create_new_node(title, parent=None):
    #todo: relate to parent node
    body = {
            "data": {
                "type": "nodes", # required
                "attributes": {
                    "title":    title,         # required
                    "category": 'Project',      # required
                }
            }
    }

    headers['Content-Type']='application/json'
    headers['Accept']='application/json'
    headers['Cookie']='osf_staging=55fc5f29029bdb53541b5cda.wTLtvhA3IyD-UGpB3pr7YXIWHvc;'
    ret = requests.post(api_url_for(NODES), data=json.dumps(body), headers=headers)
    return RemoteNode(ret.json()['data']).id

nid1 = '4e6k8' #create_new_node(base_project_name)

@decorator
def repeat_until_success(func, *args, **kwargs):
    for i in range(20):
        if func(*args, **kwargs):
            return
        else:
            time.sleep(5)
    raise TestFail


def create_local(*args, file_name=None):
    path = build_path(*args)
    if not os.path.exists(path):
        os.makedirs(path)
    if file_name:
        file_path = os.path.join(path, file_name)
        file = open(file_path, 'w+')
        contents = 'some text inside file {}'.format(file_path)
        file.write(contents)
        file.close()
        return contents.encode('utf-8')



def build_path(*args):
    return os.path.join(project_path, *args)

# usage: nosetests /path/to/manipulate_osf.py -x

class TestFail(Exception):
    pass


def get_node_file_folders(node_id):
    node_files_url = api_url_for(NODES, related_type=FILES, node_id=node_id)
    resp = session.get(node_files_url)

    assert resp.ok
    osf_storage_folder = RemoteFolder(resp.json()['data'][0])
    assert osf_storage_folder.provider == osf_storage_folder.name
    children_resp = session.get(osf_storage_folder.child_files_url)
    assert children_resp.ok
    return [dict_to_remote_object(file_folder) for file_folder in children_resp.json()['data']]

def get_children_file_folders(parent_folder):
    assert isinstance(parent_folder, RemoteFolder)
    url = parent_folder.child_files_url
    resp = session.get(url)
    assert resp.ok
    return [dict_to_remote_object(file_folder) for file_folder in resp.json()['data']]

def in_list(name, remote_object_list, is_dir):
    cls = RemoteFolder if is_dir else RemoteFile
    for remote_object in remote_object_list:
        if isinstance(remote_object, cls) and remote_object.name == name:
            return True
    return False

def get_from_list(name, remote_object_list, is_dir):
    cls = RemoteFolder if is_dir else RemoteFile
    for remote_object in remote_object_list:
        if isinstance(remote_object, cls) and remote_object.name == name:
            return remote_object
    assert FileNotFoundError

@repeat_until_success
def assert_contains_folder(name, nid, parent_folder=None):
    if parent_folder:
        children = get_children_file_folders(parent_folder)
    else:
        children = get_node_file_folders(nid)

    return in_list(name, children, True)

@repeat_until_success
def assert_contains_file(name, contents, nid, parent_folder=None):
    if parent_folder:
        children = get_children_file_folders(parent_folder)
    else:
        children = get_node_file_folders(nid)

    if in_list(name, children, False):
        file = get_from_list(name, children, False)
        resp = session.get(file.download_url)
        assert resp.ok
        assert resp.content == contents
        return True
    return False


@repeat_until_success
def assert_file_not_exist(name, nid, parent_folder=None):
    if parent_folder:
        children = get_children_file_folders(parent_folder)
    else:
        children = get_node_file_folders(nid)

    return not in_list(name, children, False)

@repeat_until_success
def assert_folder_not_exist(name, nid, parent_folder=None):
    if parent_folder:
        children = get_children_file_folders(parent_folder)
    else:
        children = get_node_file_folders(nid)
    return not in_list(name, children, True)


def get_remote(name, nid, is_dir, parent=None):
    if parent:
        children = get_children_file_folders(parent)
    else:
        children = get_node_file_folders(nid)
    cls = RemoteFolder if is_dir else RemoteFile
    for child in children:
        if isinstance(child, cls) and child.name==name:
            return child
    raise FileNotFoundError



def delete_all_local():
    for file_folder in os.listdir(project_path):
        path = os.path.join(project_path, file_folder)
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)

@repeat_until_success
def assert_node_has_no_file_folders(nid):
    file_folders = get_node_file_folders(nid)
    return len(file_folders)==0

@repeat_until_success
def assert_local_has_components_folder():
    return os.path.isdir(build_path('Components'))

def assert_contains_project():
    if not os.path.isdir(project_path):
        assert TestFail

def setUp():
    assert_contains_project()
    delete_all_local()
    assert_node_has_no_file_folders(nid1)
    assert_local_has_components_folder()


def teardown():
    delete_all_local()
    assert_node_has_no_file_folders(nid1)
    assert_local_has_components_folder()

@with_setup(setUp, teardown)
def test_create_local_folder():
    create_local('new_folder')
    assert_contains_folder('new_folder', nid1)

@with_setup(setUp, teardown)
def test_create_local_file():
    contents = create_local(file_name='new_file')
    assert_contains_file('new_file', contents, nid1)

@with_setup(setUp, teardown)
def test_create_local_nested_folders():
    create_local('f')
    assert_contains_folder('f', nid1)
    f_folder = get_remote('f', nid1, is_dir=True)

    create_local('f','a')
    assert_contains_folder('a', nid1, f_folder)
    f_a_folder = get_remote('a', nid1,True,parent=f_folder)

    create_local('f','a','a')
    assert_contains_folder('a', nid1, f_a_folder)
    f_a_a_folder = get_remote('a', nid1,True,parent=f_a_folder)

    create_local('f','a','a','a')
    assert_contains_folder('a', nid1, f_a_a_folder)

@with_setup(setUp, teardown)
def test_create_nested_file():
    create_local('folder')
    assert_contains_folder('folder', nid1)
    folder = get_remote('folder',nid1, True)
    contents = create_local('folder',file_name='rock')
    assert_contains_file('rock', contents, nid1, folder)


def test_create_folder_and_file():
    create_local('something')
    assert_contains_folder('something', nid1)
    contents = create_local(file_name='something')
    assert_contains_file('something', contents, nid1)

# @with_setup(setUp, teardown)
# def test_rename_folder():
#     create_local('original')
#     assert_contains_folder('original', nid1)
#
#     os.rename(build_path('original'), build_path('renamed'))
#     assert_contains_folder('renamed', nid1)
#
#     assert_folder_not_exist('original', nid1)
#
# @with_setup(setUp, teardown)
# def test_rename_folder_with_parents():
#     create_local('original')
#     assert_contains_folder('original', nid1)
#     original = get_remote('original', nid1, is_dir=True)
#
#     create_local('original', 'child')
#     assert_contains_folder('child', nid1, original)
#
#     os.rename(build_path('original','child'), build_path('original','renamed'))
#     assert_contains_folder('renamed', nid1, original)
#
#     assert_folder_not_exist('child', nid1,original)
#
# @with_setup(setUp, teardown)
# def test_rename_folder_with_children():
#     create_local('parent')
#     assert_contains_folder('parent', nid1)
#
#     parent = get_remote('parent', nid1, True)
#     create_local('parent','child')
#     assert_contains_folder('child', nid1,parent)
#
#
#     os.rename(build_path('parent'), build_path('renamed'))
#     assert_contains_folder('renamed', nid1)
#     renamed = get_remote('renamed', nid1, True)
#     assert_contains_folder('child', nid1, renamed)
#
#     assert_folder_not_exist('original', nid1)
#
#
# @with_setup(setUp, teardown)
# def test_rename_middle():
#     create_local('a')
#     assert_contains_folder('a', nid1)
#     a = get_remote('a',nid1,True)
#
#     create_local('a','b')
#     assert_contains_folder('b', nid1,a)
#     b = get_remote('b',nid1,True,a)
#
#     create_local('a','b','c')
#     assert_contains_folder('c', nid1,b)
#     c = get_remote('c',nid1,True,b)
#
#
#     os.rename(build_path('a','b'), build_path('a','MIDDLE'))
#     assert_contains_folder('MIDDLE', nid1,a)
#     renamed = get_remote('MIDDLE', nid1, True,a)
#     assert_contains_folder('c', nid1, renamed)
#
#     assert_folder_not_exist('b', nid1,a)
#
#
#
# @with_setup(setUp, teardown)
# def test_rename_file():
#     contents = create_local(file_name='a')
#     assert_contains_file('a',contents, nid1)
#
#     os.rename(build_path('a'), build_path('renamed'))
#     assert_contains_file('renamed', contents, nid1)
#
#     assert_file_not_exist('a', nid1)
#
# @with_setup(setUp, teardown)
# def test_renamed_nested_file():
#     create_local('a')
#     assert_contains_folder('a', nid1)
#     a = get_remote('a', nid1, True)
#
#     content = create_local('a',file_name='file')
#     assert_contains_file('file', content, nid1, a)
#
#     os.rename(build_path('a','file'), build_path('a','renamed'))
#     assert_contains_file('renamed', content, nid1,a)
#
#     assert_file_not_exist('file', nid1, a)
#
# @with_setup(setUp, teardown)
# def test_delete_folder():
#     create_local('a')
#     assert_contains_folder('a', nid1)
#
#     shutil.rmtree(build_path('a'))
#     assert_folder_not_exist('a',nid1)
#
# @with_setup(setUp, teardown)
# def test_delete_file():
#     content = create_local(file_name='myfile')
#     assert_contains_file('myfile',content, nid1)
#
#     os.remove(build_path('myfile'))
#     assert_file_not_exist('myfile',nid1)
#
# @with_setup(setUp, teardown)
# def test_delete_nested_folder():
#     create_local('a')
#     assert_contains_folder('a', nid1)
#     a = get_remote('a',nid1, True)
#     create_local('a','b')
#     assert_contains_folder('b', nid1,a)
#
#     shutil.rmtree(build_path('a','b'))
#     assert_folder_not_exist('b',nid1, a)
#     assert_contains_folder('a',nid1)
#
# @with_setup(setUp, teardown)
# def test_delete_nested_file():
#     create_local('a')
#     assert_contains_folder('a', nid1)
#     a = get_remote('a',nid1, True)
#     create_local('a','b')
#     assert_contains_folder('b', nid1,a)
#
#     shutil.rmtree(build_path('a','b'))
#     assert_folder_not_exist('b',nid1, a)
#     assert_contains_folder('a',nid1)
#
# @with_setup(setUp, teardown)
# def test_delete_middle_folder():
#     create_local('a','b','c')
#     assert_contains_folder('a',nid1)
#     a = get_remote('a',nid1, True)
#
#     assert_contains_folder('b', nid1, a)
#     b = get_remote('b',nid1, True, a)
#
#     assert_contains_folder('c', nid1, b)
#
#     shutil.rmtree(build_path('a','b'))
#     assert_folder_not_exist('b',nid1, a)
#
#     assert_contains_folder('a', nid1)

# @with_setup(setUp, teardown)
# def test_move_folder_from_top_to_subfolder():
#     create_local('a')
#     assert_contains_folder('a',nid1)
#     a = get_remote('a',nid1, True)
#
#     create_local('b')
#     assert_contains_folder('b',nid1)
#     b = get_remote('b',nid1, True)
#
#     shutil.move(build_path('b'), build_path('a'))
#
#     assert_folder_not_exist('b',nid1)
#     assert_contains_folder('b',nid1, a)
#
# @with_setup(setUp, teardown)
# def test_move_folder_from_top_to_three_levels_down_subfolder():
#     create_local('a')
#     assert_contains_folder('a',nid1)
#     a = get_remote('a',nid1, True)
#
#     create_local('a','b')
#     assert_contains_folder('b',nid1,a)
#     b = get_remote('b',nid1, True,a)
#
#     create_local('a','b','c')
#     assert_contains_folder('c',nid1,b)
#     c = get_remote('c',nid1, True,b)
#
#     create_local('to_move')
#     assert_contains_folder('to_move',nid1)
#     to_move = get_remote('to_move',nid1, True)
#
#
#     shutil.move(build_path('to_move'), build_path('a','b','c'))
#
#     assert_folder_not_exist('to_move',nid1)
#     assert_contains_folder('to_move',nid1, c)
#
#
# @with_setup(setUp, teardown)
# def test_move_folder_from_top_non_empty_subfolder():
#     create_local('a')
#     assert_contains_folder('a',nid1)
#     a = get_remote('a',nid1, True)
#
#     create_local('a','b')
#     assert_contains_folder('b',nid1,a)
#     b = get_remote('b',nid1, True,a)
#
#     create_local('a','b','c')
#     assert_contains_folder('c',nid1,b)
#     c = get_remote('c',nid1, True,b)
#
#     create_local('a','b',file_name='a_fun_file')
#
#     create_local('to_move')
#     assert_contains_folder('to_move',nid1)
#     # to_move = get_remote('to_move',nid1, True)
#
#
#     shutil.move(build_path('to_move'), build_path('a','b','c'))
#
#     assert_folder_not_exist('to_move',nid1)
#     assert_contains_folder('to_move',nid1, c)
#
# @with_setup(setUp, teardown)
# def test_move_non_empty_folder_from_top_to_subfolder():
#     create_local('a')
#     assert_contains_folder('a',nid1)
#     a = get_remote('a',nid1, True)
#     create_local('a','b')
#     assert_contains_folder('b',nid1,a)
#     contents = create_local('a', file_name='myfile')
#     assert_contains_file('myfile', contents, nid1,a)
#
#     create_local('other_folder')
#     assert_contains_folder('other_folder',nid1)
#     other_folder = get_remote('other_folder',nid1, True)
#
#     shutil.move(build_path('a'), build_path('other_folder'))
#
#     assert_contains_folder('a', nid1, other_folder)
#     moved_a = get_remote('a', nid1, True,other_folder)
#     assert_contains_folder('b', nid1, moved_a)
#     assert_contains_file('myfile',contents,nid1, moved_a)
#
#     assert_folder_not_exist('a',nid1)
#
#
# @with_setup(setUp, teardown)
# def test_move_non_empty_folder_from_top_to_nonempty_subfolder():
#     create_local('a')
#     assert_contains_folder('a',nid1)
#     a = get_remote('a',nid1, True)
#     create_local('a','b')
#     assert_contains_folder('b',nid1,a)
#     contents = create_local('a', file_name='myfile')
#     assert_contains_file('myfile', contents, nid1,a)
#
#     create_local('other_folder')
#     assert_contains_folder('other_folder',nid1)
#     other_folder = get_remote('other_folder',nid1, True)
#
#     shutil.move(build_path('a'), build_path('other_folder'))
#
#     assert_contains_folder('a', nid1, other_folder)
#     moved_a = get_remote('a', nid1, True,other_folder)
#     assert_contains_folder('b', nid1, moved_a)
#     assert_contains_file('myfile',contents,nid1, moved_a)
#
#     assert_folder_not_exist('a',nid1)
#
# @with_setup(setUp, teardown)
# def test_move_subfolder_to_top():
#     create_local('a')
#     assert_contains_folder('a',nid1)
#     a = get_remote('a', nid1, True)
#     create_local('a','b')
#     assert_contains_folder('b',nid1, a)
#
#     shutil.move(build_path('a','b'), build_path())
#
#     assert_contains_folder('a',nid1)
#     assert_contains_folder('b',nid1)
#     assert_folder_not_exist('b',nid1, a)
#
# @with_setup(setUp, teardown)
# def test_move_nonempty_subfolder_to_top():
#     create_local('a')
#     assert_contains_folder('a',nid1)
#     a = get_remote('a', nid1, True)
#
#     create_local('a','b')
#     assert_contains_folder('b',nid1,a)
#     b = get_remote('b', nid1, True,a)
#
#     create_local('a','b','c')
#     assert_contains_folder('c',nid1,b)
#     c = get_remote('c', nid1, True,b)
#
#     contents = create_local('a','b',file_name='a_file.txt')
#
#
#     shutil.move(build_path('a','b'), build_path())
#
#     assert_contains_folder('a',nid1)
#     assert_contains_folder('b',nid1)
#     new_b = get_remote('b',nid1, True)
#     assert_folder_not_exist('b',nid1, a)
#     assert_contains_file('a_file.txt', contents, new_b)
#     assert_contains_folder('c',nid1,new_b)



# @with_setup(setUp, teardown)
# def test_no_subfolder_is_called_components():
#     create_local('a','Components')
#     assert_contains_folder('a', nid1)
#     a_folder = get_remote('a', nid1, True)
#
#     assert_folder_not_exist('Components',nid1, a_folder)
#
#     create_local('a','a','Components')
#     assert_contains_folder('a', nid1, a_folder)
#     aa_folder = get_remote('a', nid1, True, a_folder)
#     assert_folder_not_exist('Components', nid1, aa_folder)
#
#
# @with_setup(setUp, teardown)
# def test_no_subfile_is_called_components():
#     create_local('a','Components')
#     assert_contains_folder('a', nid1)
#     a_folder = get_remote('a', nid1, True)
#
#     assert_file_not_exist('Components',nid1, a_folder)
#
#     create_local('a','a','Components')
#     assert_contains_folder('a', nid1, a_folder)
#     aa_folder = get_remote('a', nid1, True, a_folder)
#     assert_file_not_exist('Components', nid1, aa_folder)
#
#
# #todo: what do we do when a user creates a local FILE called Components
# #probably, just give user an alert that says Components folder must exist to sync components.
# # and then dont sync components...
# @with_setup(setUp, teardown)
# def test_what_happens_when_user_creates_local_file_called_Components():
#     pass