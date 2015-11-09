# -*- coding: utf-8 -*-
import hashlib
import datetime
import os

from osfoffline.database_manager.json_type import JSONEncodedDict
from sqlalchemy import ForeignKey, Enum
from sqlalchemy.orm import relationship, backref, validates
from sqlalchemy import Column, Integer, Boolean, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    full_name = Column(String)
    # osf_login = Column(String, unique=True)  # TODO: Re-enable when username/password login is done
    osf_password = Column(String)
    osf_local_folder_path = Column(String)
    oauth_token = Column(String)
    osf_id = Column(String, unique=True, nullable=True, default=None)  # multiple things allowed to be null

    logged_in = Column(Boolean, default=False)

    guid_for_top_level_nodes_to_sync = Column(JSONEncodedDict(512), default=[])

    nodes = relationship(
        "Node",
        backref=backref('user'),
        cascade="all, delete-orphan"
    )

    files = relationship(
        "File",
        backref=backref('user'),
        cascade="all, delete-orphan"
    )

    @hybrid_property
    def top_level_nodes(self):
        top_nodes = []
        for node in self.nodes:
            if node.top_level:
                top_nodes.append(node)
        return top_nodes

    def __repr__(self):
        return "<User(fullname={}, osf_local_folder_path={})>".format(
            self.full_name, self.osf_local_folder_path)


# todo: make locally_created, locally_deleted enum's in a EVENTS fields rather than custom variables
class Node(Base):
    __tablename__ = "node"

    PROJECT = 'project'
    COMPONENT = 'component'

    id = Column(Integer, primary_key=True)
    title = Column(String)
    hash = Column(String)
    category = Column(Enum(PROJECT, COMPONENT))
    date_modified = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    osf_id = Column(String, unique=True, nullable=True, default=None)  # multiple things allowed to be null

    locally_created = Column(Boolean, default=False)
    locally_deleted = Column(Boolean, default=False)
    locally_moved = Column(Boolean, default=False)

    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    parent_id = Column(Integer, ForeignKey('node.id'))
    child_nodes = relationship(
        "Node",
        backref=backref('parent', remote_side=[id]),
        cascade="all"
    )
    files = relationship(
        "File",
        backref=backref('node'),
        cascade="all, delete-orphan"
    )

    # fixme: this feels wrong. self.top_level?? should recursively update all child nodes. then validate.
    @hybrid_property
    def should_sync(self):
        return self.top_level and (self.osf_id in self.user.guid_for_top_level_nodes_to_sync)

    @hybrid_property
    def top_level(self):
        return self.parent is None

    @hybrid_property
    def path(self):
        """Recursively walk up the path of the node. Top level node joins with the osf folder path of the user
        """
        # +os.path.sep+ instead of os.path.join: http://stackoverflow.com/a/14504695

        if self.parent:
            return os.path.join(self.parent.path, 'Components', self.title)
        else:

            return os.path.join(self.user.osf_local_folder_path, self.title)

    def locally_create_children(self):
        self.locally_created = True
        self.osf_id = None
        for node in self.child_nodes:
            node.locally_create_children()
        for file_folder in self.files:
            file_folder.locally_created = True

    @hybrid_property
    def top_level_file_folders(self):
        file_folders = []
        for file_folder in self.files:
            if file_folder.parent is None:
                file_folders.append(file_folder)
        return file_folders

    @validates('path')
    def validate_path(self, key, path):
        if not self.parent:
            assert self.user.osf_local_folder_path
        return path

    @validates('top_level')
    def validate_top_level(self, key, top_level):
        if top_level:
            assert self.parent is None
        else:
            assert self.parent is not None
        return top_level

    def __repr__(self):
        return "<Node ({}), category={}, title={}, path={}, parent_id={}>".format(
            self.id, self.category, self.title, self.path, self.parent_id
        )


class File(Base):
    __tablename__ = "file"

    FOLDER = 'folder'
    FILE = 'file'

    DEFAULT_PROVIDER = 'osfstorage'

    id = Column(Integer, primary_key=True)
    name = Column(String)

    hash = Column(String)
    type = Column(Enum(FOLDER, FILE), nullable=False)
    date_modified = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    # todo: osf_id and osf_path are duplicates right now. One needs to be removed.
    osf_id = Column(String, nullable=True,
                    default=None)  # multiple things allowed to be null. #todo: unique=True (handle moved on osf)
    provider = Column(String, default=DEFAULT_PROVIDER)

    # NOTE: this is called path. It is not any type of file/folder path. Think of it just as an id.
    osf_path = Column(String, nullable=True,
                      default=None)  # todo: unique=True. (can't right now due to duplicates when moved on osf)

    locally_created = Column(Boolean, default=False)
    locally_deleted = Column(Boolean, default=False)
    locally_renamed = Column(Boolean, default=False)
    locally_moved = Column(Boolean, default=False)

    previous_node_osf_id = Column(String, nullable=True, default=None)
    previous_provider = Column(String, default=DEFAULT_PROVIDER)

    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    node_id = Column(Integer, ForeignKey('node.id'), nullable=False)
    parent_id = Column(Integer, ForeignKey('file.id'))

    # remote_side=[id] makes it so that when someone calls myFile.parent, we can determine what variable to
    # match myFile.parent_id with. We go through all File's that are not myFile and then match them on their id field
    # to determine which has the same id as myFile.parent_id.
    #
    # Consider remote_side=[rocko]. calling myFile.parent would then query all others Files and check which has a field
    # rocko which matches with myFile.parent_id
    #
    # remote_side is ONLY used with hierarchical relationships such as this.

    files = relationship(
        "File",
        backref=backref('parent', remote_side=[id]),
        cascade="all",
    )

    @hybrid_property
    def is_provider(self):
        return (self.name == self.provider) and (self.parent is None) and (self.is_folder)

    @hybrid_property
    def is_file(self):
        return self.type == File.FILE

    @hybrid_property
    def is_folder(self):
        return self.type == File.FOLDER

    @hybrid_property
    def has_parent(self):
        return self.parent is not None

    @hybrid_property
    def path(self):
        """Recursively walk up the path of the file/folder. Top level file/folder joins with the path of the containing node.
        """
        # +os.path.sep+ instead of os.path.join: http://stackoverflow.com/a/14504695
        if self.parent:
            return os.path.join(self.parent.path, self.name)
        else:
            return os.path.join(self.node.path, self.name)

    def update_hash(self, block_size=2 ** 20):
        if self.is_file:
            m = hashlib.md5()
            with open(self.path, "rb") as f:
                while True:
                    buf = f.read(block_size)
                    if not buf:
                        break
                    m.update(buf)
            self.hash = m.hexdigest()

    @hybrid_property
    def size(self):
        try:
            return os.stat(self.path).st_size
        except FileNotFoundError:  # file was deleted locally
            return 0

    def locally_create_children(self):
        self.locally_created = True
        if self.is_folder:
            for file_folder in self.files:
                file_folder.locally_create_children()

    @validates('parent_id')
    def validate_parent_id(self, key, parent_id):
        if self.parent:
            assert self.parent.node == self.node
        return parent_id

    @validates('node_id')
    def validate_node_id(self, key, node_id):
        if self.parent:
            assert self.parent.node == self.node
        return node_id

    @validates('files')
    def validate_files(self, key, files):
        if self.is_file:
            assert self.files == []
        return files

    @validates('osf_id')
    def validate_osf_id(self, key, osf_id):
        # if self is provider or self does not have an osf id then all good.
        if (self.is_provider) or (not self.osf_id):
            return osf_id
        else:
            for peer in self.parent.files:
                if self.id != peer.id:
                    # peers cannot have same osf_id as self
                    assert self.osf_id != peer.osf_id

    @validates('locally_moved')
    def validate_locally_moved(self, key, locally_moved):
        if locally_moved:
            assert self.previous_node_osf_id
            assert self.previous_provider
        return locally_moved

    def __repr__(self):
        return "<File ({}), type={}, name={}, path={}, parent_id={}>".format(
            self.id, self.type, self.name, self.path, self.parent
        )
