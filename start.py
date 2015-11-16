import sys

from PyQt5.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon

from osfoffline import utils
from osfoffline import settings
from osfoffline.application.main import OSFOffline
from osfoffline.views.start_screen import LoginScreen


def running_warning():
    warn_app = QApplication(sys.argv)
    QMessageBox.information(
        None,
        "Systray",
        "OSF-Offline is already running. Check out the system tray."
    )
    warn_app.quit()
    sys.exit(0)


def start():
    # Start logging all events
    utils.start_app_logging()
    if sys.platform == 'win32':
        from server import SingleInstance
        single_app = SingleInstance()

        if single_app.already_running():
            running_warning()

    app = QApplication(sys.argv)

    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(
            None,
            "Systray",
            "Could not detect a system tray on this system"
        )
        sys.exit(1)

    QApplication.setQuitOnLastWindowClosed(False)

    login = LoginScreen()
    user = login.get_user()
    login.hide()

    if user is None:
        return sys.exit(1)

    osf = OSFOffline(user, app)

    osf.ensure_folder()

    osf.show()

    ret = app.exec_()
    if ret == settings.LOGOUT_CODE:
        del app  # Force all existing windows to close
        start()
    else:
        sys.exit(ret)


if __name__ == "__main__":
    start()
