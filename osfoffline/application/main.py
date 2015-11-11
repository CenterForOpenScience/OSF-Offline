#!/usr/bin/env python
import logging
import os

from sqlalchemy.orm.exc import MultipleResultsFound
from sqlalchemy.orm.exc import NoResultFound

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QFileDialog

from osfoffline.application.background import BackgroundWorker
from osfoffline.database_manager.db import session
from osfoffline.database_manager.models import User
from osfoffline.database_manager.utils import save
from osfoffline.utils.debug import debug_trace
from osfoffline.utils.validators import validate_containing_folder
from osfoffline.views.preferences import Preferences
from osfoffline.views.start_screen import StartScreen
from osfoffline.views.system_tray import SystemTray
import osfoffline.alerts as AlertHandler


# RUN_PATH = "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"

logger = logging.getLogger(__name__)


class OSFApp(QDialog):
    login_signal = pyqtSignal()
    start_tray_signal = pyqtSignal()
    containing_folder_updated_signal = pyqtSignal()

    def __init__(self):
        super().__init__()

        # settings

        self.app_name = "OSFOffline"
        self.app_author = "COS"

        # views
        self.start_screen = StartScreen()
        self.tray = SystemTray()
        self.preferences = Preferences()
        AlertHandler.setup_alerts(self.tray.tray_icon, self.tray.tray_alert_signal)

        # connect all signal-slot pairs
        self.setup_connections()
        self.background_worker = BackgroundWorker()

    def setup_connections(self):
        # [ (signal, slot) ]
        signal_slot_pairs = [

            # system tray
            (self.tray.open_osf_folder_action.triggered, self.tray.open_osf_folder),
            (self.tray.launch_osf_action.triggered, self.tray.start_osf),
            # (self.tray.currently_synching_action.triggered, self.controller.currently_synching),
            (self.tray.preferences_action.triggered, self.open_preferences),
            (self.tray.about_action.triggered, self.start_about_screen),

            (self.tray.quit_action.triggered, self.quit),
            (self.tray.tray_alert_signal, self.tray.update_currently_synching),

            # main events
            (self.login_signal, self.start_screen.open_window),
            (self.start_tray_signal, self.tray.start),

            # preferences
            (self.preferences.preferences_window.desktopNotifications.stateChanged, self.preferences.alerts_changed),
            (self.preferences.preferences_window.startOnStartup.stateChanged, self.preferences.startup_changed),
            (self.preferences.preferences_window.changeFolderButton.clicked, self.preferences.set_containing_folder),
            (self.preferences.preferences_closed_signal, self.resume),
            (self.preferences.preferences_window.accountLogOutButton.clicked, self.logout),
            (self.preferences.containing_folder_updated_signal, self.tray.set_containing_folder),
            # (self.preferences.containing_folder_updated_signal, self.preferences.update_containing_folder_text_box),

            # start screen
            (self.start_screen.done_logging_in_signal, self.start),
            (self.start_screen.quit_application_signal, self.quit),

        ]
        for signal, slot in signal_slot_pairs:
            signal.connect(slot)

    def _can_restart_background_worker(self):
        try:
            user = self.get_current_user()
        except:
            return False
        if not user.logged_in:
            return False
        if not os.path.isdir(user.osf_local_folder_path):
            return False
        if not self.background_worker:
            return False
        if self.background_worker.is_alive():
            return False

        return True

    def start(self):
        logger.debug('Start in main called.')

        # todo: HANDLE LOGIN FAILED
        try:
            user = self.get_current_user()
        except MultipleResultsFound:
            debug_trace()
            self._logout_all_users()
            self.login_signal.emit()
            return
        except NoResultFound:
            self.login_signal.emit()
            return

        containing_folder = os.path.dirname(user.osf_local_folder_path)
        while not validate_containing_folder(containing_folder):
            logger.warning('Invalid containing folder: {}'.format(containing_folder))
            AlertHandler.warn('Invalid containing folder. Please choose another.')
            containing_folder = os.path.abspath(self.set_containing_folder_initial())

        user.osf_local_folder_path = os.path.join(containing_folder, 'OSF')

        save(session, user)
        self.tray.set_containing_folder(containing_folder)

        if not os.path.isdir(user.osf_local_folder_path):
            os.makedirs(user.osf_local_folder_path)

        self.start_tray_signal.emit()
        logger.debug('starting background worker from main.start')

        self.background_worker = BackgroundWorker()
        self.background_worker.start()

    def resume(self):
        logger.debug('resuming')
        # todo: properly pause the background thread
        # I am recreating the background thread everytime for now.
        # I was unable to correctly pause the background thread
        # thus took this route for now.
        if self.background_worker.is_alive():
            raise RuntimeError('Resume called without first calling pause')
            # self.background_worker.stop()
        # self.background_worker.start()
        self.background_worker = BackgroundWorker()
        # if self._can_restart_background_worker():
        #     # stop previous
        #     self.background_worker.stop()
        #     self.background_worker.join()

        #     # start new
        #     self.background_worker = BackgroundWorker()
        #     self.background_worker.start()
        # else:
        #     # todo: what goes here, if anything?
        #     logger.info('wanted to but could not resume background worker')

    def pause(self):
        logger.debug('pausing')
        if self.background_worker and self.background_worker.is_alive():
            self.background_worker.stop()

    def quit(self):
        try:
            if self.background_worker.is_alive():
                print('Stopping background worker')
                self.background_worker.stop()

            print('Setting user session')
            user = session.query(User).filter(User.logged_in).one()
            save(session, user)
            session.close()
        finally:
            print('Exiting application')
            QApplication.instance().quit()
        # except Exception as e:
        #     # FIXME: Address this issue
        #     logger.warning('quit broke. stopping anyways. Exception was {}'.format(e))
        #     # quit() stops gui and then quits application
        #     QApplication.instance().quit()

    def _logout_all_users(self):
        for user in session.query(User):
            user.logged_in = False
            save(session, user)

    def get_current_user(self):
        return session.query(User).filter(User.logged_in).one()

    def set_containing_folder_initial(self):
        return QFileDialog.getExistingDirectory(self, "Choose where to place OSF folder")

    def logout(self):
        user = self.get_current_user()
        user.logged_in = False
        save(session, user)
        if self.preferences.isVisible():
            self.preferences.close()
        self.pause()
        self.login_signal.emit()

    def open_preferences(self):
        logger.debug('pausing for preference modification')
        self.pause()
        logger.debug('opening preferences')
        self.preferences.open_window(Preferences.GENERAL)

    def start_about_screen(self):
        self.pause()
        self.preferences.open_window(Preferences.ABOUT)
