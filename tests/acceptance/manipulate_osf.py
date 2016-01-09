
# usage: nosetests /path/to/manipulate_osf.py -x

from nose.tools import set_trace;
from tests.utils.url_builder import wb_file_url, wb_move_url, api_create_node, api_node_files,api_node_self
from osfoffline.polling_osf_manager.remote_objects import RemoteFile, RemoteFolder, RemoteFileFolder, dict_to_remote_object,RemoteNode
import os
import json
import requests
import time
import shutil
from unittest import TestCase
from nose import with_setup
from furl import furl


def setup():
    _delete_all_local()
    _delete_all_remote()
    assertTrue(os.path.isdir, build_path('Components'))

def teardown():
    _delete_all_local()
    _delete_all_remote()
    assertTrue(os.path.isdir, build_path('Components'))


@with_setup(setup, teardown)
def test_create_folder():
    folder = create_osf_folder('folder1', nid1)
    assertTrue(os.path.isdir, build_path('folder1') )

    delete_osf_file_folder(folder, nid1)
    assertFalse(os.path.exists, build_path('folder1'))

@with_setup(setup, teardown)
def test_create_file():
    file = create_osf_file('file1', nid1)
    assertTrue(os.path.isfile, build_path('file1'))

    delete_osf_file_folder(file, nid1)
    assertFalse(os.path.exists, build_path('file1'))

@with_setup(setup, teardown)
def test_create_nested_folders_with_same_name():
    folder1 = create_osf_folder('folder', nid1)
    assertTrue(os.path.isdir, build_path('folder') )

    folder1_1 = create_osf_folder('folder', nid1, folder1)
    assertTrue(os.path.isdir, build_path('folder','folder'))

    folder1_1_1 = create_osf_folder('folder', nid1, folder1_1)
    assertTrue(os.path.isdir, build_path('folder','folder','folder'))

    delete_osf_file_folder(folder1, nid1)
    assertFalse(os.path.exists, build_path('folder'))

@with_setup(setup, teardown)
def test_create_nested_file():
    folder1 = create_osf_folder('folder1', nid1)
    assertTrue(os.path.isdir, build_path('folder1') )

    file = create_osf_file('file1', nid1, folder1)
    assertTrue(os.path.isfile, build_path('folder1','file1'))

    folder1_1 = create_osf_folder('folder1.1', nid1, folder1)
    assertTrue(os.path.isdir, build_path('folder1', 'folder1.1'))

    file2 = create_osf_file('file2', nid1, folder1_1)
    assertTrue(os.path.isfile, build_path('folder1','folder1.1','file2'))

    delete_osf_file_folder(folder1, nid1)
    assertFalse(os.path.exists, build_path('folder1'))

#fails
# def test_file_folder_with_same_name():
#     file = create_osf_folder('file1', nid1)
#     assertTrue(os.path.isdir, build_path('file1'))
#
#     folder=create_osf_file('file1', nid1)
#     assertTrue(os.path.isfile, build_path('file1'))
#
#     delete_osf_file_folder(file, nid1)
#     delete_osf_file_folder(folder, nid1)
#     assertFalse(os.path.exists, build_path('file1'))

@with_setup(setup, teardown)
def test_nested_file_with_same_name_as_containing_folder():
    folder = create_osf_folder('file1', nid1)
    assertTrue(os.path.isdir, build_path('file1'))

    create_osf_file('file1', nid1, folder)
    assertTrue(os.path.isfile, build_path('file1','file1'))

    delete_osf_file_folder(folder,nid1)
    assertFalse(os.path.exists, build_path('file1'))
@with_setup(setup, teardown)
def test_renaming_folder():
    folder = create_osf_folder('f1', nid1)
    assertTrue(os.path.isdir, build_path('f1'))

    rename_osf_file_folder('f2', folder['path'], nid1)
    assertTrue(os.path.isdir, build_path('f2'))

    delete_osf_file_folder(folder,nid1)
    assertFalse(os.path.exists, build_path('f2'))
    assertFalse(os.path.exists, build_path('f1'))
@with_setup(setup, teardown)
def test_renaming_folder_with_stuff_in_it():
    folder = create_osf_folder('f1', nid1)
    assertTrue(os.path.isdir, build_path('f1'))

    subfolder = create_osf_folder('ff1', nid1, folder)
    assertTrue(os.path.isdir, build_path('f1','ff1'))

    subfile = create_osf_file('file2', nid1, folder)
    assertTrue(os.path.isfile, build_path('f1','file2'))

    rename_osf_file_folder('f2', folder['path'], nid1)
    assertTrue(os.path.isdir, build_path('f2'))
    assertTrue(os.path.isdir, build_path('f2','ff1'))
    assertTrue(os.path.isfile, build_path('f2','file2'))


    delete_osf_file_folder(folder,nid1)
    assertFalse(os.path.exists, build_path('f2'))

@with_setup(setup, teardown)
def test_rename_file():
    file = create_osf_file('file1',nid1)
    assertTrue(os.path.isfile, build_path('file1'))

    rename_osf_file_folder('renamed_file', file['path'], nid1)
    assertTrue(os.path.isfile, build_path('renamed_file'))

    delete_osf_file_folder(file,nid1)
    assertFalse(os.path.exists, build_path('renamed_file'))

@with_setup(setup, teardown)
def test_update_file():
    file = create_osf_file('file1', nid1)
    assertTrue(os.path.isfile, build_path('file1'))

    new_contents_file_path = os.path.join(files_directory, 'NEWCONTENTS')
    should_be_contents = open(new_contents_file_path,'r+').read()
    update_osf_file(file,'NEWCONTENTS', nid1)
    def same_contents(should_be_contents):
        new_contents = open(build_path('file1'),'r+').read()
        return new_contents == should_be_contents
    assertTrue(same_contents, should_be_contents)

    delete_osf_file_folder(file,nid1)
    assertFalse(os.path.exists, build_path('file1'))
@with_setup(setup, teardown)
def test_update_nested_file():
    folder = create_osf_folder('myfolder', nid1)
    assertTrue(os.path.isdir, build_path('myfolder'))

    file = create_osf_file('file1', nid1, folder)
    assertTrue(os.path.isfile, build_path('myfolder','file1'))

    path_to_file = os.path.join(files_directory,'NEWCONTENTS')
    should_be_contents = open(path_to_file,'r+').read()
    update_osf_file(file,'NEWCONTENTS', nid1)
    def same_contents(should_be_contents):
        new_contents = open(build_path('myfolder','file1'),'r+').read()
        return new_contents == should_be_contents
    assertTrue(same_contents, should_be_contents)

    delete_osf_file_folder(folder,nid1)
    assertFalse(os.path.exists, build_path('myfolder'))



@with_setup(setup, teardown)
def test_move_file_from_top_to_folder():
    folder1 = create_osf_folder('f1', nid1)
    assertTrue(os.path.isdir, build_path('f1'))

    file = create_osf_file('file1', nid1)
    assertTrue(os.path.isfile, build_path('file1'))

    move_osf_file_folder(file, nid1, folder1)
    assertTrue(os.path.isfile, build_path('f1','file1'))
    assertFalse(os.path.exists, build_path('file1'))

    delete_osf_file_folder(folder1,nid1)
    assertFalse(os.path.exists, build_path('f1'))

@with_setup(setup, teardown)
def test_move_file_from_folder1_to_folder2():
    folder1 = create_osf_folder('f1', nid1)
    assertTrue(os.path.isdir, build_path('f1'))

    file = create_osf_file('file1', nid1, folder1)
    assertTrue(os.path.isfile, build_path('f1','file1'))

    folder2 = create_osf_folder('f2', nid1)
    assertTrue(os.path.isdir, build_path('f2'))

    move_osf_file_folder(file,nid1, folder2 )
    assertTrue(os.path.isfile, build_path('f2','file1'))
    assertFalse(os.path.exists, build_path('f1','file1'))

    delete_osf_file_folder(folder1,nid1)
    assertFalse(os.path.exists, build_path('f1'))

    delete_osf_file_folder(folder2,nid1)
    assertFalse(os.path.exists, build_path('f2'))

@with_setup(setup, teardown)
def test_move_folder1_under_folder2():
    folder1 = create_osf_folder('f1', nid1)
    assertTrue(os.path.isdir, build_path('f1'))

    folder2 = create_osf_folder('f2', nid1)
    assertTrue(os.path.isdir, build_path('f2'))

    move_osf_file_folder(folder1,nid1, folder2 )
    assertTrue(os.path.isdir, build_path('f2','f1'))
    assertFalse(os.path.exists, build_path('f1'))

    delete_osf_file_folder(folder2,nid1)
    assertFalse(os.path.exists, build_path('f2'))

@with_setup(setup, teardown)
def test_move_folder1_with_stuff_in_it_under_folder2():
    folder1 = create_osf_folder('f1', nid1)
    assertTrue(os.path.isdir, build_path('f1'))

    afolder = create_osf_folder('afolder',nid1, folder1)
    assertTrue(os.path.isdir, build_path('f1','afolder'))

    afile = create_osf_file('file2',nid1, folder1)
    assertTrue(os.path.isfile, build_path('f1','file2'))


    folder2 = create_osf_folder('f2', nid1)
    assertTrue(os.path.isdir, build_path('f2'))

    move_osf_file_folder(folder1,nid1, folder2 )
    assertTrue(os.path.isdir, build_path('f2','f1'))
    assertTrue(os.path.isdir, build_path('f2','f1','afolder'))
    assertTrue(os.path.isfile, build_path('f2','f1','file2'))
    assertFalse(os.path.exists, build_path('f1'))

    delete_osf_file_folder(folder2, nid1)
    assertFalse(os.path.exists, build_path('f2'))

@with_setup(setup, teardown)
def test_move_folder1_under_folder2_with_stuff_in_it():
    folder1 = create_osf_folder('f1', nid1)
    assertTrue(os.path.isdir, build_path('f1'))


    folder2 = create_osf_folder('f2', nid1)
    assertTrue(os.path.isdir, build_path('f2'))

    afolder = create_osf_folder('afolder',nid1, folder2)
    assertTrue(os.path.isdir, build_path('f2','afolder'))

    afile = create_osf_file('file2',nid1, folder2)
    assertTrue(os.path.isfile, build_path('f2','file2'))


    move_osf_file_folder(folder1,nid1, folder2 )
    assertTrue(os.path.isdir, build_path('f2','f1'))
    assertTrue(os.path.isdir, build_path('f2','afolder'))
    assertTrue(os.path.isfile, build_path('f2','file2'))
    assertFalse(os.path.exists, build_path('f1'))

    delete_osf_file_folder(folder2,nid1)
    assertFalse(os.path.exists, build_path('f2'))

@with_setup(setup, teardown)
def test_move_folder1_with_stuff_under_folder2_with_stuff():
    folder1 = create_osf_folder('f1', nid1)
    assertTrue(os.path.isdir, build_path('f1'))

    folder2 = create_osf_folder('f2', nid1)
    assertTrue(os.path.isdir, build_path('f2'))

    junkfolder1 = create_osf_folder('junkfolder1',nid1, folder1)
    assertTrue(os.path.isdir, build_path('f1','junkfolder1'))

    junkfile1 = create_osf_file('file1',nid1, folder1)
    assertTrue(os.path.isfile, build_path('f1','file1'))

    junkfolder2 = create_osf_folder('junkfolder2',nid1, folder2)
    assertTrue(os.path.isdir, build_path('f2','junkfolder2'))

    junkfile2 = create_osf_file('file2',nid1, folder2)
    assertTrue(os.path.isfile, build_path('f2','file2'))

    move_osf_file_folder(folder1,nid1, folder2 )
    assertTrue(os.path.isdir, build_path('f2','f1'))
    assertTrue(os.path.isdir, build_path('f2','junkfolder2'))
    assertTrue(os.path.isfile, build_path('f2','file2'))
    assertTrue(os.path.isdir, build_path('f2', 'f1','junkfolder1'))
    assertTrue(os.path.isfile, build_path('f2', 'f1','file1'))
    assertFalse(os.path.exists, build_path('f1'))

    delete_osf_file_folder(folder2,nid1)
    assertFalse(os.path.exists, build_path('f2'))

@with_setup(setup, teardown)
def test_move_folder_to_toplevel():
    folder1 = create_osf_folder('f1', nid1)
    assertTrue(os.path.isdir, build_path('f1'))

    folder1_1 = create_osf_folder('f1.1', nid1, folder1)
    assertTrue(os.path.isdir, build_path('f1','f1.1'))

    move_osf_file_folder(folder1_1, nid1)
    assertTrue(os.path.isdir, build_path('f1'))
    assertTrue(os.path.isdir, build_path('f1.1'))
    assertFalse(os.path.exists, build_path('f1','f1.1'))

    delete_osf_file_folder(folder1,nid1)
    assertFalse(os.path.exists, build_path('f1'))

    delete_osf_file_folder(folder1_1,nid1)
    assertFalse(os.path.exists, build_path('f1.1'))

@with_setup(setup, teardown)
def test_move_folder_with_stuff_in_it_to_toplevel():
    folder1 = create_osf_folder('f1', nid1)
    assertTrue(os.path.isdir, build_path('f1'))

    folder1_1 = create_osf_folder('f1.1', nid1, folder1)
    assertTrue(os.path.isdir, build_path('f1','f1.1'))

    folder1_1_junk = create_osf_folder('junk', nid1, folder1_1)
    assertTrue(os.path.isdir, build_path('f1','f1.1','junk'))

    file1_1_junk = create_osf_file('file1', nid1, folder1_1)
    assertTrue(os.path.isfile, build_path('f1','f1.1','file1'))

    move_osf_file_folder(folder1_1, nid1)
    assertTrue(os.path.isdir, build_path('f1'))
    assertTrue(os.path.isdir, build_path('f1.1'))
    assertFalse(os.path.exists, build_path('f1','f1.1'))
    assertTrue(os.path.isdir, build_path('f1.1','junk'))
    assertTrue(os.path.isfile, build_path('f1.1','file1'))

    delete_osf_file_folder(folder1,nid1)
    assertFalse(os.path.exists, build_path('f1'))

    delete_osf_file_folder(folder1_1,nid1)
    assertFalse(os.path.exists, build_path('f1.1'))

@with_setup(setup, teardown)
def test_move_file_to_toplevel():
    folder1 = create_osf_folder('myfolder', nid1)
    assertTrue(os.path.isdir, build_path('myfolder'))

    file = create_osf_file('file1', nid1, folder1)
    assertTrue(os.path.isfile, build_path('myfolder','file1'))

    move_osf_file_folder(file, nid1)
    assertTrue(os.path.isdir, build_path('myfolder'))
    assertTrue(os.path.isfile, build_path('file1'))
    assertFalse(os.path.exists, build_path('myfolder','file1'))

    delete_osf_file_folder(folder1,nid1)
    assertFalse(os.path.exists, build_path('myfolder'))

    delete_osf_file_folder(file,nid1)
    assertFalse(os.path.exists, build_path('file1'))

@with_setup(setup, teardown)
def test_cant_sync_osf_components_folder():
    components_folder = create_osf_folder('Components', nid1)
    assertTrue(os.path.isdir, build_path('Components'))

    create_osf_folder('a_folder', nid1, components_folder)
    assertFalse(os.path.exists, build_path('Components', 'a_folder'))

    create_osf_file('file1', nid1, components_folder)
    assertFalse(os.path.exists, build_path('Components', 'file1'))




def test_create_child_node():
    cur_project = get_node_by_node_id(nid1)
    new_node = create_osf_node('new_node', cur_project)
    path = os.path.join(project_path,'Components','new_node')
    assertTrue(os.path.isdir, path)

def test_create_three_level_down_child_node():
    cur_project = get_node_by_node_id(nid1)
    new_node = create_osf_node('new_node', cur_project)
    path = os.path.join(project_path,'Components','new_node')
    assertTrue(os.path.isdir, path)
    assertTrue(os.path.isdir, os.path.join(path, 'Components'))

    three_levels = create_osf_node('third', new_node)
    third_path = os.path.join(project_path, 'Components','new_node','Components','third')
    assertTrue(os.path.isdir, third_path)

def test_create_node_same_name():
    original_node = create_osf_node('same_name')
    path = os.path.join(osf_path, 'same_name')
    assertTrue(os.path.isdir, path)

    new_node = create_osf_node('same_name')
    path = os.path.join(osf_path, 'same_name ({})'.format(new_node.id))
    assertTrue(os.path.isdir, path)

    original_path_changed = os.path.join(osf_path, 'same_name ({})'.format(original_node.id))
    assertTrue(os.path.isdir, original_path_changed)

def test_create_node_same_name_children_of_main_project():
    main_node = get_node_by_node_id(nid1)
    original_node = create_osf_node('same_name', main_node)
    path = os.path.join(project_path,'Components','same_name')
    assertTrue(os.path.isdir, path)

    new_node = create_osf_node('same_name', main_node)
    path = os.path.join(project_path, 'Components','same_name ({})'.format(new_node.id))
    assertTrue(os.path.isdir, path)

    original_path_changed = os.path.join(project_path,'Components', 'same_name ({})'.format(original_node.id))
    assertTrue(os.path.isdir, original_path_changed)

















