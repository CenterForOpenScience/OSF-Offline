import asyncio
import logging

from PyQt5.QtWidgets import QDialog, QMessageBox
from sqlalchemy.orm.exc import NoResultFound

from osfoffline.database_manager.db import session
from osfoffline.database_manager.models import User
from osfoffline.exceptions import AuthError
from osfoffline.utils.authentication import AuthClient
from osfoffline.views.rsc.startscreen import Ui_startscreen


logger = logging.getLogger(__name__)


class LoginScreen(QDialog, Ui_startscreen):
    """
    This class is a wrapper for the Ui_startscreen and its controls
    """

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.user = None
        self.usernameEdit.setFocus()
        self.logInButton.clicked.connect(self.log_in)

    def get_user(self):
        self.raise_()  # Bring Screen to front

        try:
            self.user = session.query(User).one()
            if self.user.logged_in:
                return asyncio.get_event_loop().run_until_complete(
                    AuthClient().populate_user_data(self.user)
                )
        except NoResultFound:
            logger.warning('Not user currenly logged in.')
        except AuthError:
            logger.exception('Logged in user could not be authenticated')

        # 'Remember me' functionality
        if getattr(self.user, 'osf_login', None):
            self.usernameEdit.setText(self.user.osf_login)
            self.passwordEdit.setFocus()
        else:
            self.usernameEdit.setFocus()

        self.exec_()

        self.usernameEdit.setText('')
        self.passwordEdit.setText('')

        if self.user.logged_in:
            return self.user

        return None

    def log_in(self):
        logger.debug('attempting to log in')
        # self.logInButton.setEnabled(True)
        username = self.usernameEdit.text().strip()
        password = self.passwordEdit.text().strip()
        auth_client = AuthClient()

        try:
            self.user = asyncio.get_event_loop().run_until_complete(auth_client.log_in(user=self.user, username=username, password=password))
        except AuthError as e:
            logging.exception(e.message)
            QMessageBox.warning(
                None,
                'Log in Failed',
                e.message
            )
        else:
            logger.info('Successfully logged in user: {}'.format(self.user))
            self.done(self.Accepted)
