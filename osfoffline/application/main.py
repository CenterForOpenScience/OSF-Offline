#!/usr/bin/env python
import logging
import os
import subprocess
import sys

import webbrowser

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import NoResultFound

from PyQt5.Qt import QIcon
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QSystemTrayIcon
from PyQt5.QtCore import pyqtSignal

from osfoffline import settings
from osfoffline.application.background import BackgroundWorker
from osfoffline.database_manager.db import session
from osfoffline.database_manager.models import User
from osfoffline.database_manager.utils import save
from osfoffline.utils.validators import validate_containing_folder
from osfoffline.views.preferences import Preferences
import osfoffline.alerts as AlertHandler

import osfoffline.views.rsc.resources  # noqa

# RUN_PATH = "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"

logger = logging.getLogger(__name__)


class OSFOffline(QSystemTrayIcon):
    alert_signal = pyqtSignal((str, ))

    def __init__(self, user, application):
        super().__init__(QIcon(':/cos_logo_backup.png'), application)

        self.user = user
        self.preferences = Preferences()
        self.status = QAction('Up to Date', self)
        self.status.setDisabled(True)
        AlertHandler.setup_alerts(self, self.alert_signal)

        # Build the system tray menu
        self.menu = QMenu()
        self.menu.addAction(QAction('Open OSF Folder', self, triggered=self.open_osf_folder))
        self.menu.addAction(QAction('Launch OSF', self, triggered=self.open_osf))
        self.menu.addSeparator()
        self.menu.addAction(self.status)
        self.menu.addSeparator()
        self.menu.addAction(QAction('Settings', self, triggered=self.show_settings))
        self.menu.addAction(QAction('About', self, triggered=self.show_about))
        self.menu.addSeparator()
        self.menu.addAction(QAction('Log Out', self, triggered=self.logout))
        self.menu.addAction(QAction('Quit', self, triggered=self.quit))

        # Set the menu
        self.setContextMenu(self.menu)

        self.setup_connections()

        logger.debug('starting background worker from main.start')

        self.background_worker = BackgroundWorker()
        self.background_worker.start()

    def open_osf_folder(self):
        logging.debug("containing folder is :{}".format(self.user.osf_local_folder_path))
        if sys.platform == 'win32':
            os.startfile(self.user.osf_local_folder_path)
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', self.user.osf_local_folder_path])
        else:
            try:
                subprocess.Popen(['xdg-open', self.user.osf_local_folder_path])
            except OSError:
                raise NotImplementedError

    def open_osf(self):
        webbrowser.open_new_tab(settings.OSF_URL)

    def show_settings(self):
        self.pause()
        self.preferences.open_window(Preferences.GENERAL)

    def show_about(self):
        self.pause()
        self.preferences.open_window(Preferences.ABOUT)

    def logout(self):
        try:
            if self.background_worker.is_alive():
                logger.info('Stopping background worker')
                self.background_worker.stop()
            try:
                user = session.query(User).filter(User.logged_in).one()
                user.logged_in = False
            except NoResultFound:
                pass
            else:
                try:
                    save(session, user)
                except SQLAlchemyError:
                    session.query(User).delete()
        finally:
            QApplication.instance().exit(settings.LOGOUT_CODE)

    def quit(self):
        try:
            if self.background_worker.is_alive():
                logger.info('Stopping background worker')
                self.background_worker.stop()

            try:
                user = session.query(User).filter(User.logged_in).one()
            except NoResultFound:
                pass
            else:
                logger.info('Saving user data')
                save(session, user)
            session.close()
        finally:
            logger.info('Quitting application')
            QApplication.instance().quit()

    def ensure_folder(self):
        if self.user.osf_local_folder_path:
            folder = os.path.dirname(self.user.osf_local_folder_path)
        else:
            folder = os.path.abspath(QFileDialog.getExistingDirectory(self, 'Choose where to place OSF folder'))

        while not validate_containing_folder(folder):
            logger.warning('Invalid containing folder: {}'.format(folder))
            AlertHandler.warn('Invalid containing folder. Please choose another.')
            folder = os.path.abspath(QFileDialog.getExistingDirectory(self, 'Choose where to place OSF folder'))

        self.user.osf_local_folder_path = os.path.join(folder, 'OSF')

        save(session, self.user)

    def resume(self):
        logger.debug('resuming')
        if self.background_worker.is_alive():
            raise RuntimeError('Resume called without first calling pause')

        self.background_worker = BackgroundWorker()
        self.background_worker.start()

    def pause(self):
        logger.debug('pausing')
        if self.background_worker and self.background_worker.is_alive():
            self.background_worker.stop()

    def update_status(self, val):
        self.status.setText(str(val))

    def setup_connections(self):
        signal_slot_pairs = [
            (self.alert_signal, self.update_status),

            # preferences
            (self.preferences.preferences_window.desktopNotifications.stateChanged, self.preferences.alerts_changed),
            (self.preferences.preferences_window.startOnStartup.stateChanged, self.preferences.startup_changed),
            (self.preferences.preferences_window.changeFolderButton.clicked, self.preferences.set_containing_folder),
            (self.preferences.preferences_closed_signal, self.resume),
            (self.preferences.preferences_window.accountLogOutButton.clicked, self.logout),
            # (self.preferences.containing_folder_updated_signal, self.tray.set_containing_folder),
        ]
        for signal, slot in signal_slot_pairs:
            signal.connect(slot)
