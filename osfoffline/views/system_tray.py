# -*- coding: utf-8 -*-
import logging
import os
import subprocess
import sys
import webbrowser

from PyQt5.Qt import QIcon
from PyQt5.QtWidgets import (QDialog, QSystemTrayIcon,
                             QAction, QMenu)
import osfoffline.alerts as AlertHandler
from osfoffline.utils.validators import validate_containing_folder
import osfoffline.views.rsc.resources  # need this import for the logo to work properly.

from PyQt5.QtCore import pyqtSignal


class SystemTray(QDialog):
    tray_alert_signal = pyqtSignal((str,))

    def __init__(self):
        super().__init__()
        self.create_actions()
        self.create_tray_icon()
        self.containing_folder = ''

    def create_actions(self):
        # menu items
        self.open_osf_folder_action = QAction("Open OSF Folder", self)
        self.launch_osf_action = QAction("Launch OSF", self)
        self.currently_synching_action = QAction("Up to date", self)
        self.currently_synching_action.setDisabled(True)
        self.preferences_action = QAction("Preferences", self)
        self.about_action = QAction("&About", self)
        self.quit_action = QAction("&Quit", self)

    def create_tray_icon(self):
        self.tray_icon_menu = QMenu(self)
        self.tray_icon_menu.addAction(self.open_osf_folder_action)
        self.tray_icon_menu.addAction(self.launch_osf_action)
        self.tray_icon_menu.addSeparator()
        self.tray_icon_menu.addAction(self.currently_synching_action)
        self.tray_icon_menu.addSeparator()
        self.tray_icon_menu.addAction(self.preferences_action)
        self.tray_icon_menu.addAction(self.about_action)
        self.tray_icon_menu.addSeparator()
        self.tray_icon_menu.addAction(self.quit_action)
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setContextMenu(self.tray_icon_menu)

        # todo: do we have a better icon for use with desktop apps?
        icon = QIcon(':/cos_logo_backup.png')
        self.tray_icon.setIcon(icon)

    def start(self):
        self.tray_icon.show()

    def update_currently_synching(self, val):
        self.currently_synching_action.setText(str(val))
        self.tray_icon.show()

    def set_containing_folder(self, new_containing_folder):
        logging.debug("setting new containing folder is :{}".format(self.containing_folder))
        self.containing_folder = new_containing_folder

    def start_osf(self):
        url = "http://osf.io"
        webbrowser.open_new_tab(url)

    def open_osf_folder(self):
        # fixme: containing folder not being updated.
        import logging
        logging.debug("containing folder is :{}".format(self.containing_folder))
        if validate_containing_folder(self.containing_folder):
            if sys.platform == 'win32':
                os.startfile(self.containing_folder)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', self.containing_folder])
            else:
                try:
                    subprocess.Popen(['xdg-open', self.containing_folder])
                except OSError:
                    raise NotImplementedError
        else:
            AlertHandler.warn('osf folder is not set')
