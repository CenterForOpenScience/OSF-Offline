__author__ = 'himanshu'
import hashlib
import datetime
import os
from tests.utils.url_builder import api_user_nodes, api_user_url, api_file_children, api_node_children, api_node_files, api_file_self
from sqlalchemy import create_engine, ForeignKey, Enum
from sqlalchemy.orm import sessionmaker, relationship, backref, scoped_session, validates
from sqlalchemy import Column, Integer, Boolean, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    fullname = Column(String)


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

    def as_dict(self):
        return {
                "id": self.id,
                "fullname": self.fullname,
                "given_name": self.fullname,
                "middle_name": "",
                "family_name": "",
                "suffix": "",
                "date_registered": "2015-07-06T17:51:22.833000",
                "gravatar_url": "https://secure.gravatar.com/avatar/7241b93c02e7d393e5f118511880734a?d=identicon&size=40",
                "employment_institutions": [],
                "educational_institutions": [],
                "social_accounts": {},
                "links": {
                    "nodes": {
                        "relation": 'http://localhost:8000/v2/users/{}/nodes/'.format(self.id)
                    },
                    "html": 'http://localhost:5000/5bqt9/',
                    "self": api_user_url(self.id)
                },
                "type": "users"
            }



    def __repr__(self):
        return "<User(fullname={}, osf_password={}, osf_local_folder_path={})>".format(
            self.full_name, self.osf_password, self.osf_local_folder_path)



class Node(Base):
    __tablename__ = "node"

    PROJECT = 'project'
    COMPONENT = 'component'

    id = Column(Integer, primary_key=True)
    title = Column(String)

    category = Column(Enum(PROJECT, COMPONENT), default=COMPONENT)
    date_modified = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    parent_id = Column(Integer, ForeignKey('node.id'))
    child_nodes = relationship(
        "Node",
        backref=backref('parent', remote_side=[id]),
        cascade="all, delete-orphan"
    )
    files = relationship(
        "File",
        backref=backref('node'),
        cascade="all, delete-orphan"
    )

    @hybrid_property
    def top_level(self):
        return self.parent is None


    @hybrid_property
    def providers(self):
        file_folders = []
        for file_folder in self.files:
            if file_folder.parent is None and file_folder.is_folder:
                file_folders.append(file_folder)
        return file_folders

    def as_dict(self):
        return {
            "id": str(self.id),
            "title": self.title,
            "description": "",
            "category": self.category,
            "date_created": str(self.date_modified),
            "date_modified": str(self.date_modified),
            "tags": {
                "system": [],
                "user": []
            },
            "links": {
                "files": {
                    "related":'http://localhost:8000/v2/nodes/{}/files/'.format(self.id)
                },
                "parent": {
                    "self": None
                },
                "contributors": {
                    "count": 1,
                    "related": "http://localhost:8000/v2/nodes/dz5mg/contributors/"
                },
                "pointers": {
                    "count": 0,
                    "related": "http://localhost:8000/v2/nodes/dz5mg/pointers/"
                },
                "registrations": {
                    "count": 0,
                    "related": "http://localhost:8000/v2/nodes/dz5mg/registrations/"
                },
                "self": "http://localhost:8000/v2/nodes/dz5mg/",
                "html": "http://localhost:5000/dz5mg/",
                "children": {
                    "count": 0,
                    "related": 'http://localhost:8000/v2/nodes/{}/children/'.format(self.id)
                }
            },
            "properties": {
                "dashboard": False,
                "collection": False,
                "registration": False
            },
            "public": False,
            "type": "nodes"
        }

    def __repr__(self):
        return "<Node ({}), category={}, title={}, parent_id={}>".format(
            self.id, self.category, self.title, self.parent_id
        )


class File(Base):
    __tablename__ = "file"

    FOLDER = 'folder'
    FILE = 'file'

    DEFAULT_PROVIDER = 'osfstorage'

    id = Column(Integer, primary_key=True)
    name = Column(String)

    type = Column(Enum(FOLDER, FILE), nullable=False)
    date_modified = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    provider = Column(String, default=DEFAULT_PROVIDER)
    path = Column(String, default='/')



    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    node_id = Column(Integer, ForeignKey('node.id'), nullable=False)
    parent_id = Column(Integer, ForeignKey('file.id'))
    contents = Column(String)


    files = relationship(
        "File",
        backref=backref('parent', remote_side=[id]),
        cascade="all, delete-orphan",
    )


    @hybrid_property
    def is_file(self):
        return self.type == File.FILE
    @hybrid_property
    def is_folder(self):
        return self.type == File.FOLDER

    @hybrid_property
    def has_parent(self):
        return self.parent is not None


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

    @validates('contents')
    def validate_contents(self, key, contents):
        if self.is_folder:
            assert self.contents is None
        return contents

    def as_dict(self):

        resp = {
                "provider": self.provider,
                "path": self.path,
                "item_type": self.type,
                "name": self.name,
                "metadata": {},
                "links": {
                    "self_methods": [
                        "POST"
                    ],
                    "self": 'http://localhost:7777/file?path={}&nid={}&provider={}'(self.path,self.node.id, self.provider),
                    "related": 'http://localhost:8000/v2/nodes/{}/files/?path={}/&provider={}'(self.node.id, self.path, self.provider)
                },
                "type": "files"
            }
        if self.is_file:
            metadata =  {
                "size": 12,
                "modified": None,
                "content_type": None,
                "extra": {
                    "downloads": 5,
                    "version": 2
                }
            }
            resp['metadata'] = metadata
            resp['links']['self_methods'].append('GET')
            resp['links']['self_methods'].append('DELETE')

        return resp

    def __repr__(self):
        return "<File ({}), type={}, name={}, path={}, parent_id={}>".format(
            self.id, self.type, self.name, self.path, self.parent
        )



