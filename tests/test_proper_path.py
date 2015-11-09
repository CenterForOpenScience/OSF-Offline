__author__ = 'himanshu'
from unittest import TestCase

from osfoffline.utils.path import ProperPath
from osfoffline.exceptions.path_exceptions import InvalidPathError


__author__ = 'himanshu'


class TestProperPath(TestCase):

    def test_name_file(self):
        path = ProperPath('/this/is/a/long/path', False)
        self.assertEquals(path.name , 'path')

    def test_name_folder(self):
        path = ProperPath('/this/is/a/long/path', True)
        self.assertEquals(path.name, 'path')

    def test_name_file_with_slash(self):
        with self.assertRaises(InvalidPathError):
          path = ProperPath('/this/is/a/long/path/', False)

    def test_name_folder_with_slash(self):
        path = ProperPath('/this/is/a/long/path/', True)
        self.assertEquals(path.name , 'path')

    def test_parent_file(self):
        path = ProperPath('/this/is/a/long/path', False)
        self.assertEquals(path.parent.name, 'long')
        self.assertEquals(path.parent, ProperPath('/this/is/a/long', True))

    def test_parent_folder(self):
        path = ProperPath('/this/is/a/long/path', True)
        self.assertEquals(path.parent.name, 'long')
        self.assertEquals(path.parent, ProperPath('/this/is/a/long', True))

    def test_parent_folder_with_slash(self):
        path = ProperPath('/this/is/a/long/path/', True)
        self.assertEquals(path.parent.name, 'long')
        self.assertEquals(path.parent, ProperPath('/this/is/a/long', True))

    def test_input_isdir_determines_dir(self):
        self.assertTrue(ProperPath('/this/is/folder', True).is_dir)
        self.assertTrue(ProperPath('/this/is/folder/', True).is_dir)

        self.assertFalse(ProperPath('/this/is/folder', False).is_dir)
        with self.assertRaises(InvalidPathError):
            resp = ProperPath('/this/is/folder/', False).is_dir

    def test_input_isdir_determines_file(self):
        self.assertFalse(ProperPath('/this/is/folder', True).is_file)
        self.assertFalse(ProperPath('/this/is/folder/', True).is_file)

        self.assertTrue(ProperPath('/this/is/folder', False).is_file)
        with self.assertRaises(InvalidPathError):
            resp = ProperPath('/this/is/folder/', False).is_file


    def test_is_root(self):
        self.assertTrue(ProperPath('/',True).is_root)
        with self.assertRaises(InvalidPathError):
            resp = ProperPath('/',False).is_root

        self.assertFalse(ProperPath('/this/folder',True).is_root)
        self.assertFalse(ProperPath('/this/folder',False).is_root)


class TestValidation(TestCase):

    def test_double_slash_is_invalid(self):
        with self.assertRaises(InvalidPathError):
            resp = ProperPath('/hi//this', True)
        with self.assertRaises(InvalidPathError):
            resp = ProperPath('//hi/this', True)
        with self.assertRaises(InvalidPathError):
            resp = ProperPath('/hi/this//',True)

    def test_cant_be_empty(self):
        with self.assertRaises(InvalidPathError):
            resp = ProperPath('',True)

    def test_file_cant_end_with_slash(self):
        with self.assertRaises(InvalidPathError):
            resp =ProperPath('/hi/this/is/file/',False)

    def test_root_cant_be_file(self):
        with self.assertRaises(InvalidPathError):
            resp = ProperPath('/', False)

    def test_cant_have_dotdot(self):
        with self.assertRaises(InvalidPathError):
            resp = ProperPath('..',True)
        with self.assertRaises(InvalidPathError):
            resp = ProperPath('/hi/../as',True)
        with self.assertRaises(InvalidPathError):
            resp = ProperPath('../',True)
        with self.assertRaises(InvalidPathError):
            resp = ProperPath('/..',True)

    def test_should_expand_tilde(self):
        with self.assertRaises(InvalidPathError):
            resp = ProperPath('~/mydir/', True)
        with self.assertRaises(InvalidPathError):
            resp = ProperPath('~/mydir', False)

