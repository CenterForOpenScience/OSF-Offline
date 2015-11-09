from unittest import TestCase
import os

from watchdog.observers import Observer

from osfoffline.utils.path import ProperPath
from osfoffline.filesystem_manager.sync_local_filesytem_and_db import LocalDBSync
from osfoffline.exceptions.local_db_sync_exceptions import LocalDBBothNone
from tests import TEST_DIR
from tests.fixtures.factories import common
from tests.fixtures.factories.factories import UserFactory, NodeFactory, FileFactory
from osfoffline.database_manager.models import User, Node, File, Base
from watchdog.events import (
    DirCreatedEvent,
    DirModifiedEvent,
    DirMovedEvent,
    DirDeletedEvent,
    FileCreatedEvent,
    FileDeletedEvent,
    FileModifiedEvent,
    FileMovedEvent
)

#todo: probably a good idea to have it so that the desired folder structure is dynamically created and then deleted after the function call...

class TestLocalDBSyncUnitTests(TestCase):

    def assertContains(self, a_list, a_item):
        if a_item in a_list:
            return
        else:
            msg = "{a_item} not found inside list".format(aitem=a_item)
            raise self.failureException(msg)

    def assert_get_children_folder_equals_local(self, folder_name):
        project_folder = os.path.join(self.osf_dir,folder_name)
        project_folder_proper = ProperPath(project_folder,True)
        children = self.sync._get_children(project_folder_proper)
        for_sure_children = []
        for file_folder in os.listdir(project_folder_proper.full_path):
            path_to_child = os.path.join(project_folder_proper.full_path, file_folder)
            # handle Components Folder
            if file_folder == LocalDBSync.COMPONENTS_FOLDER_NAME:
                for component in os.listdir(path_to_child):
                    component_path = os.path.join(path_to_child, component)
                    is_dir = os.path.isdir(component_path)
                    if is_dir:
                       for_sure_children += [ProperPath(component_path, is_dir)]
            else:
                is_dir = os.path.isdir(path_to_child)
                for_sure_children += [ProperPath(path_to_child, is_dir)]
        self.assertEquals(set(children),set(for_sure_children))

    def setUp(self):
        self.session = common.Session()

        self.osf_dir = os.path.join(TEST_DIR,"fixtures","mock_projects","OSF")
        self.user = UserFactory(osf_local_folder_path=self.osf_dir)
        self.top_level_node1 = NodeFactory(user=self.user)
        self.top_level_node2 = NodeFactory(user=self.user)
        self.node_1_1 = NodeFactory(user=self.user, parent=self.top_level_node1)
        self.node_1_2 = NodeFactory(user=self.user, parent=self.top_level_node1)
        self.node_1_3 = NodeFactory(user=self.user, parent=self.top_level_node1)
        self.node_2_1 = NodeFactory(user=self.user, parent=self.top_level_node2)
        self.node_2_2 = NodeFactory(user=self.user, parent=self.top_level_node2)
        self.node_2_3 = NodeFactory(user=self.user, parent=self.top_level_node2)
        self.node_2_3_1 = NodeFactory(user=self.user, parent=self.node_2_3)

        self.folder_1 = FileFactory(user=self.user, node=self.node_1_1, type=File.FOLDER)
        self.folder_1_1 = FileFactory(user=self.user, node=self.node_1_1, parent=self.folder_1, type=File.FOLDER)
        self.file1 = FileFactory(user=self.user, node=self.node_1_1, parent=self.folder_1, type=File.FILE)
        self.file2 = FileFactory(user=self.user, node=self.node_1_1, parent=self.folder_1, type=File.FILE)




        observer = Observer()
        self.sync = LocalDBSync(self.user.osf_local_folder_path, observer, self.user)

        # self.path1 = os.path.join('fake','path','1')
        # self.path2 = os.path.join('fake','path','2')
        # self.path3 = os.path.join('fake','path','3')
        # self.path4 = os.path.join('fake','path','4')
        # self.evil_path1 = os.path.join('/','.','bad')
        # self.evil_path2 = os.path.join('.','.','bad')
        # self.evil_path3 = os.path.join('<>','<>')
        # self.evil_path4 = os.path.join('///','<<>>')
        # self.evil_path5 = os.path.join('rocko','c://')

    def tearDown(self):
        self.session.rollback()
        self.session.query(User).delete()
        self.session.query(Node).delete()
        self.session.query(File).delete()
        common.Session.remove()

    # todo: check edge case of 1
    # todo: check make_local_db_tuple_list with only files (no Components folder)
    # todo: check make_local_db_tuple_list with files and empty Components Folder
    # todo: check make_local_db_tuple_list with files and non-empty Components Folder
    # todo: check make_local_db_tuple_list with only empty Components Folder
    # todo: check make_local_db_tuple_list with only non-empty Components Folder


    def test__make_local_db_tuple_list_both_None(self):
        local = None
        db = None
        with self.assertRaises(LocalDBBothNone):
            self.sync._make_local_db_tuple_list(local, db)

    def test__make_local_db_tuple_list_db_is_None(self):
        local = ProperPath(self.osf_dir, True)
        db = None
        local_db = self.sync._make_local_db_tuple_list(local, db)
        local_dirs = [os.path.join(self.osf_dir, dir) for dir in os.listdir(self.osf_dir)]
        self.assertEqual(len(local_dirs), len(local_db))
        for dir in local_dirs:
            proper_dir = ProperPath(dir, os.path.isdir(dir))
            self.assertTrue((proper_dir, None) in local_db)

    def test__make_local_db_tuple_list_local_is_None(self):
        local = None

        NodeFactory(user=self.user)
        NodeFactory(user=self.user)
        NodeFactory(user=self.user)
        db = self.user

        local_db = self.sync._make_local_db_tuple_list(local, db)

        self.assertEqual(len(self.user.top_level_nodes), len(local_db))
        for node in self.user.top_level_nodes:
            self.assertTrue((None, node) in local_db)

    def test__make_local_db_tuple_list_db_both_exist_but_are_all_diff(self):
        local = ProperPath(self.osf_dir, True)

        NodeFactory(user=self.user, title='nonexistant project 1')
        NodeFactory(user=self.user, title='nonexistant project 2')
        NodeFactory(user=self.user, title='nonexistant project 3')
        db = self.user

        local_db = self.sync._make_local_db_tuple_list(local, db)

        local_dirs = [os.path.join(self.osf_dir, dir) for dir in os.listdir(self.osf_dir)]
        db_dirs = self.user.top_level_nodes

        self.assertEqual(len(local_dirs) + len(db_dirs), len(local_db))
        for dir in local_dirs:
            proper_dir = ProperPath(dir, os.path.isdir(dir))
            self.assertTrue((proper_dir, None) in local_db)
        for dir in db_dirs:
            self.assertTrue((None, dir) in local_db)

    def test__make_local_db_tuple_list_db_both_exist_but_are_all_same(self):
        user = UserFactory(osf_local_folder_path=self.osf_dir)
        local = ProperPath(self.osf_dir,True)
        local_dirs = [os.path.join(self.osf_dir, dir) for dir in os.listdir(self.osf_dir)]

        for dir in local_dirs:
            NodeFactory(user=user, title=dir)
        db = user

        self.assertEqual(len(local_dirs), len(user.top_level_nodes))

        local_db = self.sync._make_local_db_tuple_list(local, db)

        self.assertEqual(len(local_dirs), len(local_db))
        for local, db in local_db:
            self.assertEqual(local, ProperPath(db.path, True))


    def test__make_local_db_tuple_list_db_both_exist_exactly_1_is_same(self):
        local = ProperPath(self.osf_dir,True)
        local_dirs = [os.path.join(self.osf_dir, dir) for dir in os.listdir(self.osf_dir)]

        NodeFactory(user=self.user, title=local_dirs[0])
        db = self.user


        local_db = self.sync._make_local_db_tuple_list(local, db)

        db_top_level_nodes = self.user.top_level_nodes

        self.assertEqual(len(local_dirs) + len(db_top_level_nodes) - 1, len(local_db))
        self.check_local_db_list(local_db)


    def test__make_local_db_tuple_list_db_with_files(self):
        local = ProperPath(self.osf_dir,True)
        local_dirs = [os.path.join(self.osf_dir, dir) for dir in os.listdir(self.osf_dir)]

        NodeFactory(user=self.user, title=local_dirs[0])
        db = self.user

        local_db = self.sync._make_local_db_tuple_list(local, db)

        db_top_level_nodes = self.user.top_level_nodes

        self.assertEqual(len(local_dirs) + len(db_top_level_nodes) - 1, len(local_db))
        self.check_local_db_list(local_db)

    # """
    # test with:
    #     files
    #     File and NODE
    #     only File
    #     only Node
    #     make sure isnt going an extra level deep
    #     empty (instead of None)
    #     only 1 thing inside
    # """

    def check_local_db_list(self, local_db):
        for local, db in local_db:
            if local is not None and db is not None:
                self.assertEqual(self.sync._get_proper_path(local) , self.sync._get_proper_path(db))
            elif local is not None:
                self.assertFalse(db)
                self.assertTrue(isinstance(local, ProperPath))
            elif db is not None:
                self.assertFalse(local)
                self.assertTrue(isinstance(db, Base))
            else:
                self.fail("both are None")

    def test__get_children_None(self):
        self.assertEqual([], self.sync._get_children(None))

    def test__get_children_Empty_dir(self):
        dir = os.path.join(self.osf_dir,"empty_project")
        proper_dir = ProperPath(dir, True)
        self.assertEqual([], self.sync._get_children(proper_dir))

    def test__get_children_file(self):
        file = os.path.join(self.osf_dir,"test_normal_project","b")
        proper_file = ProperPath(file, False)
        self.assertEqual([], self.sync._get_children(proper_file))

    def test__get_children_empty_models(self):
        user = UserFactory()
        self.assertEqual([], self.sync._get_children(user))

        node = NodeFactory(user=user)
        self.assertEqual([], self.sync._get_children(node))

        subnode = NodeFactory(user=user, parent=node)
        self.assertEqual([], self.sync._get_children(subnode))

        folder = FileFactory(user=user, node=node)
        self.assertEqual([], self.sync._get_children(folder))

        subfolder = FileFactory(user=user, node=node, parent=folder)
        self.assertEqual([], self.sync._get_children(subfolder))

        model_file1 = FileFactory(user=user, node=node, parent=subfolder)
        self.assertEqual([], self.sync._get_children(model_file1))

        model_file2 = FileFactory(user=user, node=node, parent=folder)
        self.assertEqual([], self.sync._get_children(model_file2))




    # tetodo: get_children_local_folder more tests with more varying combinations of adjacent file folders and components

    def test__get_children_local_for_empty_folder(self):
        self.assert_get_children_folder_equals_local('empty_project')

    def test__get_children_local_for_folder_with_file(self):
        self.assert_get_children_folder_equals_local('contains_single_file')

    def test__get_children_local_for_folder_with_file_and_folder(self):
        self.assert_get_children_folder_equals_local('file_and_folder')

    def test__get_children_local_for_folder_with_nonempty_folder_and_file(self):
        self.assert_get_children_folder_equals_local('nonempty_folder_and_file')

    def test__get_children_local_for_folder_with_nonempty_components_folder(self):
        self.assert_get_children_folder_equals_local('nonempty_components_folder')

    def test__get_children_local_for_folder_with_empty_components_folder(self):
        self.assert_get_children_folder_equals_local('empty_components_folder')

    def test__get_children_local_for_folder_with_nonempty_components_folder_and_adjacent_file_folders(self):
        self.assert_get_children_folder_equals_local('nonempty_components_folder_with_adjacent_file_folders')



    def test__get_children_local_folder_normal(self):
        project_folder = os.path.join(self.osf_dir,"test_project_normal")
        children = self.sync._get_children(ProperPath(project_folder,True))
        local_dirs = [os.path.join(project_folder, dir) for dir in os.listdir(project_folder)]
        proper_local_dirs = [ProperPath(dir, os.path.isdir(dir)) for dir in local_dirs]
        self.assertEqual(len(local_dirs), len(children))
        for child in children:
            self.assertContains(proper_local_dirs, child)

    def test__get_children_model_file(self):
        children = self.sync._get_children(self.file1)
        self.assertEqual([], children)

    def test__get_children_model_folder(self):
        children = self.sync._get_children(self.folder_1)
        self.assertEqual(len(children), len(self.folder_1.files))
        for child in children:
            self.assertContains(self.folder_1.files, child)

    def test__get_children_model_user(self):
        children = self.sync._get_children(self.user)
        self.assertEqual(len(children), len(self.user.top_level_nodes))
        for child in children:
            self.assertContains(self.user.top_level_nodes, child)

    def test__get_children_model_top_level_node(self):
        children = self.sync._get_children(self.top_level_node1)
        for_sure_children = self.top_level_node1.child_nodes + self.top_level_node1.top_level_file_folders
        self.assertEqual(len(children), len(for_sure_children))
        for child in children:
            self.assertContains(for_sure_children, child)

    def test__get_children_model_inner_node(self):
        children = self.sync._get_children(self.node_2_3)
        for_sure_children = self.node_2_3.child_nodes + self.node_2_3.top_level_file_folders
        self.assertEqual(len(children), len(for_sure_children))
        for child in children:
            self.assertTrue(child in for_sure_children)

    def test__get_children_model_nodes_with_files(self):
        children = self.sync._get_children(self.node_1_1)
        for_sure_children = self.node_1_1.child_nodes + self.node_1_1.top_level_file_folders
        self.assertEqual(len(children), len(for_sure_children))
        for child in children:
            self.assertTrue(child in for_sure_children)

    def test__determine_event_type_both_None(self):
        with self.assertRaises(LocalDBBothNone):
            self.sync._determine_event_type(None, None)

    def test__determine_event_type_local_None(self):
        db = self.user
        with self.assertRaises(TypeError):
            self.sync._determine_event_type(None, db)

    def test__determine_event_type_db_None(self):
        dir = os.path.join(self.osf_dir,"test_project_normal")
        with self.assertRaises(TypeError):
            event = self.sync._determine_event_type(dir,None)

    def test__determine_event_type_local_top_level_node_only(self):
        #todo: implement me!
        pass

    # def test__determine_event_type_local_node_only(self):
    #     self.fail()
    # def test__determine_event_type_local_folder_only(self):
    #     self.fail()
    # def test__determine_event_type_local_file_only(self):
    #     self.fail()
    # def test__determine_event_type_db_top_level_node_only(self):
    #     self.fail()
    # def test__determine_event_type_db_top_level_node_only(self):
    #     self.fail()
    # def test__determine_event_type_db_node_only(self):
    #     self.fail()
    # def test__determine_event_type_db_file_only(self):
    #     self.fail()
    # def test__determine_event_type_db_folder_only(self):
    #     self.fail()
    # def test__determine_event_type_both_top_level_node_changed(self):
    #     self.fail()
    # def test__determine_event_type_both_top_level_node_changed(self):
    #     self.fail()
    # def test__determine_event_type_both_top_level_node_changed(self):
    #     self.fail()
    # def test__determine_event_type_both_top_level_node_changed(self):
    #     self.fail()

    # def test__get_proper_path(self):
    #     self.fail()
    #
    # def test__represent_same_values(self):
    #     self.fail()
    #
    # def test__emit_new_events(self):
    #     self.fail()













































