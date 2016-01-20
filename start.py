#!/usr/bin/env python
import logging
import sys
import signal
import time
import urllib

from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QSystemTrayIcon

from osfoffline.database import drop_db
from osfoffline.gui.qt import OSFOfflineQT
from osfoffline import settings
from osfoffline.utils.log import start_logging
from osfoffline.utils.singleton import SingleInstance

logger = logging.getLogger(__name__)

if settings.DEBUG:
    signal.signal(signal.SIGINT, signal.SIG_DFL)


def running_warning():
    warn_app = QApplication(sys.argv)
    QMessageBox.information(None, 'Systray', 'OSF-Offline is already running. Check out the system tray.')
    warn_app.quit()


def check_connections(has_connection=False):
    try:
        urllib.urlopen("http://www.google.com")
    except urllib.URLError:
        logger.infoe('Internet is down')
    else:
        logger.info("Internet is up and running.")
        has_connection = True
    return has_connection


def start():
    start_logging()
    singleton = SingleInstance(callback=running_warning)  # will end application if an instance is already running

    # Start logging all events
    if '--drop' in sys.argv:
        drop_db()


    app = QApplication(sys.argv)

    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, 'Systray', 'Could not detect a system tray on this system')
        sys.exit(1)

    QApplication.setQuitOnLastWindowClosed(False)

    has_connection = check_connections()

    if not OSFOfflineQT(app).start():
        return sys.exit(1)
    return sys.exit(app.exec_())


if __name__ == "__main__":
    start()
