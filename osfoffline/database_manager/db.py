from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from osfoffline.database_manager.models import Base
from osfoffline.settings import PROJECT_DB_FILE


URL = 'sqlite:///{}'.format(PROJECT_DB_FILE)

# sqlite+pysqlcipher://:passphrase/file_path
# URL = 'sqlite+pysqlcipher://:PASSWORD/{DB_FILE_PATH}'.format(DB_FILE_PATH=DB_FILE_PATH)

engine = create_engine(
    URL,
    # poolclass=SingletonThreadPool,
    connect_args={'check_same_thread': False},
)
Base.metadata.create_all(engine)
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

session = Session()
