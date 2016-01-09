import  requests
from osfoffline.client.osf import User, Node, NodeStorage
import tests.acceptance.settings as settings
import json
from decorator import decorator
import time
import os
import shutil

user = None # todo: authorize client
headers = {'Authorization':'Bearer {}'.format(user.oauth_token)}

session = requests.Session()
session.headers.update(headers)

# for manipulate local
def create_new_node(title, parent=None):
    """

    :param title: title of new node to create
    :param parent: make new node a child of parent. Can be None
    :return: the id of the new node
    """
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

    ret = requests.post(Node.get_url(), data=json.dumps(body), headers=headers)
    return ret.json()['data']['id']

nid1 = create_new_node(settings.base_project_name)

@decorator
def repeat_until_success(func, *args, **kwargs):
    """
    Retry the assertion until it becomes true. Keep retrying for settings.REPEAT_TIME

    :param func: an assertion function
    :param args: args given to assertion function
    :param kwargs: kwards given to assertion function

    :raise if the assertion function is ever true, then just end. If the assertion function is returning
     False even after settings.REPEAT_TIME, then raise TestFail

    """
    for i in range(20):
        if func(*args, **kwargs):
            return
        else:
            time.sleep(5)
    raise TestFail


def create_local(*args, file_name=None):
    """
    usage:
        to create a folder: create_local('path','to','folder')
        to create a file:   create_local('path', 'to', 'folder', filename='myfile')
    :param args: folder path
    :param file_name: optionally create a file at this path
    :return: if creating a file, return the contents of the file
    """
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
    """
    :param args: folder path
    :return:
    """
    return os.path.join(settings.project_path, *args)



class TestFail(Exception):
    pass


def get_node_file_folders(node_id):
    """
    get the file folders given a node id.
    This makes 2 get requests. First for the osfstorage and then for the files/folders inside that.
    Thus it is abstracting out the osfstorage step for us.
    :param node_id:
    :return: [file_folder_as_json]
    """
    node_files_url = Node.get_url(node_id) + 'files/'
    resp = session.get(node_files_url)

    assert resp.ok
    osf_storage_folder = resp.json()['data'][0]
    assert osf_storage_folder['attributes']['name'] == 'osfstorage'
    children_resp = session.get(osf_storage_folder['relationships']['files']['links']['related']['href'])
    assert children_resp.ok
    return [file_folder for file_folder in children_resp.json()['data']]

def get_children_file_folders(parent_folder):
    url = parent_folder['relationships']['files']['links']['related']['href']
    resp = session.get(url)
    assert resp.ok
    return [file_folder for file_folder in resp.json()['data']]

def in_list(name, remote_list, is_dir):
    """
    determine if the given file or folder is in the remote list
    :param name: name of file or folder
    :param remote_list:
    :param is_dir: is the given input a file or folder
    :return:
    """
    file_or_folder = 'folder' if is_dir else 'file'
    for remote in remote_list:
        if remote['type']==file_or_folder and remote['attributes']['name'] == name:
            return True
    return False

def get_from_list(name, remote_list, is_dir):
    """
    get the desired file or folder from the remote list. You only input the file/folder name
    :param name: name of file or folder
    :param remote_list:
    :param is_dir: is the given input a file or folder
    :return:
    """
    file_or_folder = 'folder' if is_dir else 'file'
    for remote in remote_list:
        if remote['type']==file_or_folder and remote['attributes']['name'] == name:
            return remote
    assert FileNotFoundError

# Assertions

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
        resp = session.get(file['links']['download'])
        assert resp.ok
        assert resp.content == contents
        return True
    return False


@repeat_until_success
def assert_file_not_exist(name, nid, parent_folder=None):
        return _assert_file_folder_not_exist(name, nid, False, parent_folder)

@repeat_until_success
def assert_folder_not_exist(name, nid, parent_folder=None):
    return _assert_file_folder_not_exist(name, nid, True, parent_folder)

def _assert_file_folder_not_exist(name, nid, is_folder, parent_folder):
    if parent_folder:
        children = get_children_file_folders(parent_folder)
    else:
        children = get_node_file_folders(nid)
    return not in_list(name, children, is_folder)



def get_remote(name, nid, is_dir, parent=None):
    if parent:
        children = get_children_file_folders(parent)
    else:
        children = get_node_file_folders(nid)

    file_or_folder = 'folder' if is_dir else 'file'
    for child in children:
        if child['type']==file_or_folder and child['attributes']['name'] == name:
            return child
    raise FileNotFoundError



def delete_all_local():
    for file_folder in os.listdir(settings.project_path):
        path = os.path.join(settings.project_path, file_folder)
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
    if not os.path.isdir(settings.project_path):
        assert TestFail


# for manipulate osf


def wb_move_url(node_id, file_id):
    # todo: this can be done in a better way
    import osfoffline.settings as settings
    return '{}/v1/resources/{}/providers/osfstorage/{}'.format(settings.FILE_BASE, node_id, file_id)

def create_osf_folder(folder_name, nid, parent=None):
    if parent:
        path = parent['path'] + folder_name
    else:
        path = '/{}'.format(folder_name)
    params = {
        'path': path,
        'provider': 'osfstorage',
        'nid': nid
    }
    files_url = NodeStorage.get_url(nid)

    resp = session.post(files_url, params=params)

    assert resp.ok
    return resp.json()

def create_osf_file(file_name, nid, parent=None):
    if parent:
        path = parent['path'] + file_name
    else:
        path = '/{}'.format(file_name)
    params = {
        'path': path,
        'provider': 'osfstorage',
        'nid': nid
    }
    files_url = NodeStorage.get_url(nid)
    path_to_file = os.path.join(settings.files_dir_path, file_name)
    file = open(path_to_file, 'rb')
    resp = session.put(files_url, params=params, data=file)
    assert resp.ok
    return resp.json()

def rename_osf_file_folder(rename_to, nid, file_id):
    #todo: determine how to get move url
    url = wb_move_url(nid, file_id)
    #todo: this is old way to move. The new data params are much simpler
    data = {
        'action': 'rename',
        'rename': rename_to
    }

    resp = session.post(url, data=json.dumps(data))
    assert resp.ok
    return resp.json()

def update_osf_file(file,new_content_file_name, nid):

    params = {
        'path': file['path'],
        'provider': 'osfstorage',
        'nid': nid
    }
    files_url = NodeStorage.get_url(nid) + 'files/'
    path_to_file_with_new_content = os.path.join(settings.files_dir_path, new_content_file_name)
    content = open(path_to_file_with_new_content, 'rb')
    resp = session.put(files_url, params=params, data=content)
    assert resp.ok
    return resp.json()

def move_osf_file_folder(file_folder_to_move, nid, folder_to_move_under=None):

    url = wb_move_url(nid, folder_to_move_under['path'] if folder_to_move_under else '/')
    data = {
        'action':'move',
        'path':file_folder_to_move['path'] if folder_to_move_under else '/',
        'rename': file_folder_to_move['name'],
        'conflict': 'replace',
    }

    resp = session.post(url, data=json.dumps(data))
    assert resp.ok
    return resp.json()



def delete_osf_file_folder(file_folder, nid):
    # http://localhost:7777/file?path=/&nid=dz5mg&provider=osfstorage
    url = NodeStorage.get_url(nid)+'files/'+file_folder['path']
    resp = session.delete(url)
    resp.close()

def get_node_by_node_id(node_id):
    url = NodeStorage.get_url(node_id)
    resp = session.get(url)
    assert resp.ok
    return resp.json()['data']

def create_osf_node(title, parent=None):
    if parent:
        url = api_create_node(parent.id)
        resp = session.post(url, data={'title':title})
        assert resp.ok

        base = furl(resp.headers['Location'])
        new_node_id = base.path.segments[0]
        url = api_node_self(new_node_id)
        resp = session.get(url)
        assert resp.ok
        new_node_dict = resp.json()['data']
        return dict_to_remote_object(new_node_dict)
    else:
        url = api_create_node()
        resp = session.post(url, data={'title':title})
        assert resp.ok
        return dict_to_remote_object(resp.json()['data'])



def build_path(*args):
    return os.path.join(project_path, *args)

# usage: nosetests /path/to/manipulate_osf.py -x



class TestFail(Exception):
    pass

def assertTrue(func, arg):
    """
    checks for condition every 5 seconds. If eventually True then good. else TestFail
    """
    for i in range(20):
        if func(arg):
            return
        else:
            time.sleep(5)
    raise TestFail

def assertFalse(func, arg):
    """
    checks for condition every 5 seconds. If eventually False then good. else TestFail
    """
    for i in range(20):
        if not func(arg):
            return
        else:
            time.sleep(5)
    raise TestFail

def _delete_all_local():
    for file_folder in os.listdir(project_path):
        path = os.path.join(project_path, file_folder)
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
def _delete_all_remote():
    remote_file_folders = get_node_file_folders(nid1)
    for file_folder in remote_file_folders:
        url = wb_file_url(path=file_folder.id,nid=nid1,provider='osfstorage')
        resp = session.delete(url)
        resp.close()