__author__ = 'himanshu'
import os
import shutil

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from appdirs import user_data_dir

from osfoffline.database_manager.models import Base

DB_DIR = user_data_dir('test-app-name','test-app-author')
DB_FILE_PATH = os.path.join(DB_DIR,'osf.db')
URL = 'sqlite:///{}'.format(DB_FILE_PATH)


try:
    shutil.rmtree(DB_DIR)
except (NotADirectoryError, FileNotFoundError):
    pass
os.makedirs(DB_DIR)


engine = create_engine(URL)
Base.metadata.create_all(engine)
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)
