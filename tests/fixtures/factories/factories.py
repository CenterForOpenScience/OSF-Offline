__author__ = 'himanshu'
from factory.alchemy import SQLAlchemyModelFactory
from factory import Sequence

from osfoffline.database_manager.models import User, Node, File
from tests.fixtures.factories.common import Session




# class User(Base):
#     """ A SQLAlchemy simple model class who represents a user """
#     __tablename__ = 'UserTable'
#
#     id = Column(Integer(), primary_key=True)
#     name = Column(Unicode(20))
#
# Base.metadata.create_all(engine)



class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session = Session   # the SQLAlchemy session object

    id = Sequence(lambda n: n)
    full_name = Sequence(lambda n: u'User %d' % n)
    osf_login = Sequence(lambda n: u'osf_login %d' % n)
    osf_password = Sequence(lambda n: u'osf_password %d' % n)
    oauth_token = Sequence(lambda n: u'oauth_token %d' % n)
    osf_id = Sequence(lambda n: u'osf_id %d' % n)
    osf_local_folder_path = Sequence(lambda n: u'fake/osf/folder/path %d' % n)

    logged_in = False


class NodeFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Node
        sqlalchemy_session = Session   # the SQLAlchemy session object

    id = Sequence(lambda n: n)
    title = Sequence(lambda n: u'Node %d' % n)
    osf_id = Sequence(lambda n: u'osf_id %d' % n)



class FileFactory(SQLAlchemyModelFactory):
    class Meta:
        model = File
        sqlalchemy_session = Session   # the SQLAlchemy session object

    id = Sequence(lambda n: n)
    name = Sequence(lambda n: u'Node %d' % n)
    osf_id = Sequence(lambda n: u'osf_id %d' % n)
    type = File.FOLDER



