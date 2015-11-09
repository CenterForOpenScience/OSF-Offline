from sqlalchemy import orm, create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from .models import Base
import os
url = 'sqlite:///{}'.format(os.path.join(os.path.dirname(__file__),'db_dir','mock_osf_api.db'))
engine = create_engine(url, connect_args={'check_same_thread': False})
Base.metadata.create_all(engine)
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)