from unittest import TestCase
import os

from appdirs import user_data_dir

import osfoffline.database_handler.db as db
from osfoffline.database_handler.models import User,Node,File


class TestDBSetup(TestCase):
    def setUp(self):
        self.db_dir = user_data_dir(appname='test-app-name-setup', appauthor='test-app-author-setup')
        # creates a new db each time
        db.setup_db(self.db_dir)



        def session_work(input_session=None):
            # get session
            session = input_session if input_session else db.get_session()

            # add to db
            user = User()
            node = Node(user=user)
            file = File(user=user, node=node)
            session.add(user)
            session.add(node)
            session.add(file)
            session.commit()

            # query from db
            user = session.query(User).all()[0]
            node = session.query(Node).all()[0]
            file = session.query(File).all()[0]

            # remove from db
            session.delete(user)
            session.delete(node)
            session.delete(file)
            session.commit()

            # query again
            session.query(User).all()
            session.query(Node).all()
            session.query(File).all()

        self.session_work = session_work

    def tearDown(self):
        db.remove_db()


    def test_setup_db_exists(self):
        osf_db_path = os.path.join(self.db_dir, 'osf.db')
        self.assertTrue(os.path.isfile(osf_db_path))

    # def test_db_encrypted(self):
    #     self.fail()

    def test_all_models_exist(self):
        self.session_work()

    # def test_same_session_in_multiple_threads(self):
    #     t1 = threading.Thread(target=self.session_work)
    #     t2 = threading.Thread(target=self.session_work)
    #     t3 = threading.Thread(target=self.session_work)
    #
    #     t1.start()
    #     t2.start()
    #     t3.start()
    #
    #     t1.join()
    #     t2.join()
    #     t3.join()


    # def test_multiple_sessions_in_single_thread(self):
    #     session1 = get_session()
    #     session2 = get_session()
    #     session3 = get_session()
    #     self.session_work(session1)
    #     self.session_work(session2)
    #     self.session_work(session3)

    # def test_multiple_sessions_in_multiple_thread(self):
    #     t1 = threading.Thread(target=self.session_work, args=[get_session()])
    #     t2 = threading.Thread(target=self.session_work, args=[get_session()])
    #     t3 = threading.Thread(target=self.session_work, args=[get_session()])
    #
    #     t1.start()
    #     t2.start()
    #     t3.start()
    #
    #     t1.join()
    #     t2.join()
    #     t3.join()
