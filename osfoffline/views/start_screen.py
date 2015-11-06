import asyncio
import concurrent
from flask import request
import logging

import aiohttp
import furl
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QDialog, QMessageBox
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from osfoffline import settings
from osfoffline.database_manager.db import session
from osfoffline.database_manager.utils import save
from osfoffline.database_manager.models import User
from osfoffline.exceptions.osf_exceptions import OSFAuthError
from osfoffline.polling_osf_manager.osf_query import OSFQuery
from osfoffline.polling_osf_manager.remote_objects import RemoteUser
from osfoffline.utils.debug import debug_trace
from osfoffline.views.rsc.startscreen import Ui_startscreen


class StartScreen(QDialog):
    """
    This class is a wrapper for the Ui_startscreen and its controls
    """

    done_logging_in_signal = pyqtSignal()
    quit_application_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.start_screen = Ui_startscreen()

    @asyncio.coroutine
    def log_in(self):
        logging.debug('attempting to log in')
        personal_access_token = self.start_screen.personalAccessTokenEdit.text().strip()
        url = settings.API_BASE + '/v2/users/me/'
        loop = asyncio.get_event_loop()
        osf = OSFQuery(loop, personal_access_token)
        logging.debug('url: {}'.format(url))
        try:
            resp = yield from osf.make_request(url, expects=[200])
        except (aiohttp.errors.ClientTimeoutError, aiohttp.errors.ClientConnectionError, aiohttp.errors.TimeoutError):
            # No internet connection
            QMessageBox.warning(
                None,
                "Log in Failed",
                "Unable to connect to server. Check your internet connection or try again later."
            )
        except (aiohttp.errors.HttpBadRequest, aiohttp.errors.BadStatusLine):
            # Invalid credentials
            QMessageBox.warning(
                None,
                "Log in Failed",
                "Invalid login credentials."
            )
        else:
            json_resp = yield from resp.json()
            remote_user = RemoteUser(json_resp['data'])

            try:
                user = session.query(User).filter(User.osf_id == remote_user.id).one()
            except MultipleResultsFound:
                logging.warning('multiple users with same username. deleting all users with this username. restarting function.')
                for user in session.query(User).filter(User.osf_id == remote_user.id).all():
                    session.delete(user)
                    try:
                        save(session, user)
                    except Exception as e:
                        logging.exception(e)
                        QMessageBox.warning(
                            None,
                            "Log in Failed",
                            "Unable to save user data. Please try again later."
                        )

                return self.log_in()
            except NoResultFound:
                logging.debug('user doesnt exist. Creating user. and logging them in.')
                user = User(
                    full_name=remote_user.name,
                    osf_id=remote_user.id,
                    osf_login='',  # TODO: email goes here when more auth methods are added, not currently returned by APIv2
                    osf_local_folder_path='',
                    oauth_token=personal_access_token,
                )
            else:
                if not user.oauth_token == personal_access_token:
                    user.oauth_token == personal_access_token

            user.logged_in = True
            try:
                save(session, user)
            except Exception as e:
                logging.exception(e)
                QMessageBox.warning(
                    None,
                    "Log in Failed",
                    "Unable to save user data. Please try again later."
                )

            self.close()

    def setup_slots(self):
        logging.debug('setting up start_screen slots')
        self.start_screen.logInButton.clicked.connect(lambda: asyncio.get_event_loop().run_until_complete(self.log_in()))

    def open_window(self):
        if not self.isVisible():
            self.start_screen.setupUi(self)
            self.setup_slots()
            self.show()

    def _user_logged_in(self):
        try:
            session.query(User).filter(User.logged_in).one()
            return True
        except:
            return False

    def closeEvent(self, event):
        """ If closeEvent occured by us, then it means user is properly logged in. Thus close.
            Else, event is by user without logging in. THUS, quit entire application.
        """
        if self._user_logged_in():
            self.done_logging_in_signal.emit()
        else:
            self.quit_application_signal.emit()
        event.accept()
