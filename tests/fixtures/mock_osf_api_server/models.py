__author__ = 'himanshu'
import hashlib
import datetime
import os
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
            "id": str(self.id),
            "type": "users",
            "attributes": {
                "full_name": self.fullname,
                "given_name": "",
                "middle_names": "",
                "family_name": "",
                "suffix": "",
                "date_registered": "2015-09-11T18:19:01.860000",
                "profile_image_url": "https://secure.gravatar.com/avatar/2b40121791d6946b6cdd805dc2ea4b7c?d=identicon"
            },
            "relationships": {
                "nodes": {
                    "links": {
                        "related": "http://localhost:5000/v2/users/{}/nodes/".format(self.id)
                    }
                }
            },
            "links": {
                "self": "http://localhost:5000/v2/users/{}/".format(self.id),
                "html": "https://staging2.osf.io/m5e83/"
            }
        }



    def __repr__(self):
        return "<User(fullname={})>".format(
            self.fullname)



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
            "type": "nodes",
            "attributes": {
                "title": self.title,
                "description": None,
                "category": self.category,
                "date_created": "2015-07-24T14:52:22.359000",
                "date_modified": "2015-08-26T15:44:49.395000",
                "tags": [],
                "registration": True,  # todo
                "collection": False,  # todo
                "dashboard": False,  # todo
                "public": True  # todo
            },
            "relationships": {
                "children": {
                    "links": {
                        "related": {
                            "href": "http://localhost:5000/v2/nodes/{}/children/".format(self.id),
                            "meta": {
                                "count": len(self.child_nodes)
                            }
                        }
                    }
                },
                "contributors": {
                    "links": {
                        "related": {
                            "href": "https://staging2-api.osf.io/v2/nodes/243u7/contributors/",
                            "meta": {
                                "count": 1
                            }
                        }
                    }
                },
                "files": {
                    "links": {
                        "related": "http://localhost:5000/v2/nodes/{}/files/".format(self.id)
                    }
                },
                "node_links": {
                    "links": {
                        "related": {
                            "href": "https://staging2-api.osf.io/v2/nodes/243u7/node_links/",
                            "meta": {
                                "count": 0
                            }
                        }
                    }
                },
                "parent": {
                    "links": {
                        "related":{
                            'href': None if self.top_level else 'http://localhost:5000/v2/nodes/{}/'.format(self.parent_id),
                            'meta':{}
                        }
                    }
                },
                "registrations": {
                    "links": {
                        "related": {
                            "href": "http://localhost:5000/v2/nodes/{}/registrations/".format(self.id),
                            "meta": {
                                "count": 0
                            }
                        }
                    }
                }
            },
            "links": {
                "self": "http://localhost:5000/v2/nodes/{}/".format(self.id),
                "html": "https://staging2.osf.io/243u7/"
            }
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
    checked_out = Column(Boolean, default=False)


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
    def path(self):
        if self.has_parent:
            temp = '/{}'.format(self.id)
            if self.is_folder:
                temp += '/'
            return temp
        else:
            return '/'

    @hybrid_property
    def has_parent(self):
        return self.parent is not None

    @hybrid_property
    def is_provider(self):
        return self.is_folder and not self.has_parent

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
            "id": str(self.id),
            "type": 'files',
            "attributes": {
                "name": str(self.name),
                "kind": 'file' if self.is_file else 'folder',
                "path": self.path,
                "provider": "osfstorage",
                "last_touched": None,
                "size": len(self.contents) if self.is_file else None

            },
            "relationships": {
                "checkout": {
                    "links": {
                        "related": None # todo: handle checkouts
                    }
                },
                "files": {
                    "links": {
                        "related": {
                            'href': "http://localhost:5000/v2/nodes/{node_id}/files/osfstorage{file_path}".format(node_id=self.node.id, file_path=self.path) if self.is_folder else None,
                            'meta':{}
                        }
                    }
                },
                "versions": {
                    "links": {
                        "related": None # todo: handle versions
                    }
                }
            },
            "links": {
                "info": "http://localhost:5000/v2/files/{}/".format(self.id),
                "download": "http://localhost:5000/v1/resources/{}/providers/{}/{}/".format(self.node_id, self.provider, self.id) if self.is_file else None,
                "delete": "http://localhost:5000/v1/resources/{}/providers/{}/{}/".format(self.node_id, self.provider, self.id),
                "move": "http://localhost:5000/v1/resources/{}/providers/{}/{}/".format(self.node_id, self.provider, self.id),
                "upload": "http://localhost:5000/v1/resources/{}/providers/{}/{}/".format(self.node_id, self.provider, self.id),
                "new_folder": 'http://localhost:5000/v1/resources/{}/providers/{}/{}/?kind=folder'.format(self.node_id, self.provider, self.id) if self.is_folder else None
            }
        }
        if not self.has_parent:
            resp['attributes']['node'] = str(self.node_id)
        return resp

    def __repr__(self):
        return "<File ({}), type={}, name={}, path={}, parent_id={}>".format(
            self.id, self.type, self.name, self.path, self.parent
        )



