from unittest import TestCase
import os

from osfoffline.database_handler.models import User, Node, File
from tests.fixtures.factories import common
from tests.fixtures.factories.osfoffline import common
from tests.fixtures.factories.factories import UserFactory, NodeFactory, FileFactory
from tests import TEST_DIR







# todo: make the assert statements in the models actually be custom exceptions.
# todo:     They might allow you to use nosetests properly

class TestModels(TestCase):
    def setUp(self):
        self.session = common.Session()

    def tearDown(self):
        self.session.rollback()
        self.session.query(User).delete()
        self.session.query(Node).delete()
        self.session.query(File).delete()
        common.Session.remove()

    def test_create_user(self):
        u = UserFactory()
        self.session.flush()
        self.assertEqual([u], self.session.query(User).all())

    def test_delete_user(self):
        u = UserFactory()
        self.assertEqual([u],self.session.query(User).all())
        self.session.delete(u)
        self.assertEqual([], self.session.query(User).all())


    def test_delete_user_with_top_level_nodes(self):
        u = UserFactory()
        tp_node = NodeFactory()
        u.nodes.append(tp_node)
        self.assertEqual([tp_node], self.session.query(User).one().top_level_nodes)

        self.session.delete(u)
        #node should have been deleted as soon as user was deleted
        self.assertEqual([], self.session.query(Node).all())

    def test_delete_user_with_no_top_level_nodes(self):
        u = UserFactory()

        self.assertEqual([], self.session.query(User).one().top_level_nodes)

        self.session.delete(u)
        #node should have been deleted as soon as user was deleted
        self.assertEqual([], self.session.query(Node).all())


    def test_delete_users_files_and_nodes(self):
        u = UserFactory()
        node = NodeFactory(user=u)
        file = FileFactory(node=node,user=u )


        self.assertEqual([file], u.files)
        self.assertEqual([node], u.nodes)
        self.session.commit()

        self.session.delete(u)
        self.session.commit()

        self.assertEqual([], self.session.query(File).all())
        self.assertEqual([], self.session.query(Node).all())


    def test_get_users_top_level_nodes(self):
        u = UserFactory()
        tp_node = NodeFactory( user=u)
        node = NodeFactory( user=u, parent=tp_node)



        self.assertTrue(node in u.nodes)
        self.assertTrue(tp_node in u.nodes)
        self.assertEqual(len(u.nodes),2)
        self.assertEqual([tp_node], u.top_level_nodes)



    def test_delete_top_level_nodes(self):
        u = UserFactory()
        tp_node = NodeFactory( user=u)
        node = NodeFactory( user=u, parent=tp_node)
        tp_node2 = NodeFactory(user=u)

        self.assertEqual(len(u.nodes),3)
        self.assertTrue(node in u.nodes)
        self.assertTrue(tp_node in u.nodes)
        self.assertTrue(tp_node2 in u.nodes)

        self.assertEqual(len(u.top_level_nodes),2)
        self.assertTrue(tp_node in u.top_level_nodes)
        self.assertTrue(tp_node2 in u.top_level_nodes)

        self.assertEqual([node], tp_node.child_nodes)
        self.assertEqual([], tp_node2.child_nodes)


        # delete tp_node
        # need to flush to db before we can delete node
        self.session.flush()
        self.session.delete(tp_node)
        self.session.refresh(u)

        self.assertEqual([tp_node2], u.nodes)
        self.assertEqual([tp_node2], u.top_level_nodes)

        # delete node
        # self.assertWarns(SAWarning, self.session.delete, node)


        # delete tp_node2
        self.session.flush()
        self.session.delete(tp_node2)
        self.session.refresh(u)

        self.assertEqual([], u.nodes)
        self.assertEqual([], u.top_level_nodes)



    def test_delete_nodes_with_files(self):
        u = UserFactory()
        tp_node = NodeFactory(user=u)
        folder = FileFactory(user=u, node=tp_node)
        file = FileFactory(user=u, node=tp_node, parent=folder)

        # delete node
        self.session.flush()
        self.session.delete(tp_node)
        self.session.refresh(u)


        # check node doesnt exist
        self.assertEqual([], self.session.query(Node).all())
        self.assertEqual([], u.top_level_nodes)

        # check files dont exist
        self.assertEqual([], u.files)
        self.assertEqual([], self.session.query(File).all())

    # fixme: raise IntegrityError Exception, NOT general Exception.



    def test_node_without_user(self):

        with self.assertRaises(Exception):
            NodeFactory()
            self.session.flush()


    def test_node_without_parent(self):
        u = UserFactory()
        node = NodeFactory(user=u)
        self.assertTrue(node.top_level)


    def test_file_without_node(self):
        user = UserFactory()
        self.session.flush()
        with self.assertRaises(Exception):
            FileFactory(user=user)
            self.session.flush()


    def test_file_without_user(self):
        user = UserFactory()
        node = NodeFactory(user=user)
        self.session.flush()
        with self.assertRaises(Exception):
            FileFactory(node=node)
            self.session.flush()

    def test_file_without_parent(self):
        u = UserFactory()
        node = NodeFactory(user=u)
        file = FileFactory(user=u, node=node)
        self.assertFalse(file.has_parent)
        
        
    def test_add_file_to_folder_that_is_of_diff_node(self):
        u = UserFactory()
        node1 = NodeFactory(user=u)
        node2 = NodeFactory(user=u)
        folder1 = FileFactory(user=u, node=node1)
        # going to flush to make sure the error wasnt from something before this.
        self.session.flush()
        with self.assertRaises(Exception):
            folder2 = FileFactory(user=u, node=node2, parent=folder1)
            self.session.flush()

    def test_add_folder_that_is_of_diff_node_but_same_hierarchy(self):
        u = UserFactory()
        node1 = NodeFactory(user=u)
        node2 = NodeFactory(user=u, parent=node1)
        folder1 = FileFactory(user=u, node=node1)
        # going to flush to make sure the error wasnt from something before this.
        self.session.flush()
        with self.assertRaises(Exception):
            folder2 = FileFactory(user=u, node=node2, parent=folder1)
            self.session.flush()


    def test_add_subfile_to_file(self):
        u = UserFactory()
        node = NodeFactory(user=u)
        file = FileFactory(user=u, node=node, type=File.FILE)

        # going to flush to make sure the error wasnt from something before this.
        self.session.flush()
        with self.assertRaises(Exception):
            FileFactory(user=u, node=node, parent=file, type=File.FILE)
            self.session.flush()

    def test_add_subfolder_to_file(self):
        u = UserFactory()
        node = NodeFactory(user=u)
        file = FileFactory(user=u, node=node, type=File.FILE)

        # going to flush to make sure the error wasnt from something before this.
        self.session.flush()
        with self.assertRaises(Exception):
            FileFactory(user=u, node=node, parent=file, type=File.FOLDER)
            self.session.flush()




class TestModelPath(TestCase):
    def setUp(self):
        self.session = common.Session()
        self.osf_dir = os.path.join(TEST_DIR, "OSF")
        self.user = UserFactory(osf_local_folder_path = self.osf_dir)
        self.node = NodeFactory(user=self.user )
        self.file = FileFactory(user=self.user, node=self.node)
        self.session.flush()


    def tearDown(self):
        self.session.rollback()
        self.session.query(User).delete()
        self.session.query(Node).delete()
        self.session.query(File).delete()
        common.Session.remove()


    def test_path_for_user(self):
        self.assertEqual(self.user.osf_local_folder_path, self.osf_dir)

    def test_path_for_node(self):
        node_path = os.path.join(self.osf_dir, self.node.title)
        self.assertEqual(node_path, self.node.path)

    def test_path_for_three_level_node(self):
        node2 = NodeFactory(user=self.user, parent=self.node)
        node3 = NodeFactory(user=self.user, parent=node2)
        node_path = os.path.join(self.osf_dir, self.node.title, node2.title, node3.title)
        self.assertEqual(node_path, node3.path)
        

    def test_path_for_three_level_node_with_3_level_file(self):
        node2 = NodeFactory(user=self.user, parent=self.node)
        node3 = NodeFactory(user=self.user, parent=node2)
        file1 = FileFactory(user=self.user, node=node3)
        file2 = FileFactory(user=self.user, node=node3, parent=file1)
        file3 = FileFactory(user=self.user, node=node3, parent=file2)
        
        file_path = os.path.join(
            self.osf_dir,
            self.node.title, 
            node2.title, 
            node3.title,
            file1.name,
            file2.name,
            file3.name
        )
        self.assertEqual(file_path, file3.path)

        

    def test_file_path(self):
        file_path = os.path.join(self.osf_dir, self.node.title, self.file.name)
        self.assertEqual(file_path, self.file.path)

    def test_node_path_when_file_deleted(self):
        self.session.delete(self.file)
        self.session.refresh(self.user)
        node_path = os.path.join(self.osf_dir, self.node.title)
        self.assertEqual(node_path, self.node.path)

    def test_node_path_when_file_added_to_folder(self):
        new_file = FileFactory(user=self.user, node=self.node, parent=self.file)
        folder_path = os.path.join(self.osf_dir, self.node.title, self.file.name)
        new_file_path = os.path.join(self.osf_dir, self.node.title,self.file.name, new_file.name)
        self.assertEqual(folder_path, self.file.path)
        self.assertEqual(new_file_path, new_file.path)

