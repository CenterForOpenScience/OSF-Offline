import os
import logging

from PyQt5.QtWidgets import (QDialog, QFileDialog, QTreeWidgetItem)
from PyQt5.QtCore import QCoreApplication, Qt
from PyQt5.QtCore import pyqtSignal
from osfoffline.views.rsc.preferences_rc import Ui_Preferences  # REQUIRED FOR GUI
from osfoffline.database_manager.db import session
from osfoffline.database_manager.models import User
from osfoffline.polling_osf_manager.api_url_builder import api_url_for, NODES, USERS
from osfoffline.polling_osf_manager.remote_objects import RemoteNode
import requests
import osfoffline.alerts as AlertHandler


class Preferences(QDialog):
    """
    This class is a wrapper for the Ui_Preferences and its controls
    """
    GENERAL = 0
    OSF = 1
    ABOUT = 2

    PROJECT_NAME_COLUMN = 0
    PROJECT_SYNC_COLUMN = 1

    preferences_closed_signal = pyqtSignal()
    containing_folder_updated_signal = pyqtSignal((str,))

    def __init__(self):
        super().__init__()
        self._translate = QCoreApplication.translate
        self.containing_folder = ''
        self.preferences_window = Ui_Preferences()
        self.preferences_window.setupUi(self)

        self.preferences_window.changeFolderButton_2.clicked.connect(self.update_sync_nodes)
        self.tree_items = []
        self.setup_slots()

    def closeEvent(self, event):
        logging.debug('closed...... preferences....')
        self.preferences_closed_signal.emit()
        event.accept()
        # if self.isVisible():
        #     self.hide()
        #     event.ignore()
        #     self.destroy()

    def alerts_changed(self):
        if self.preferences_window.desktopNotifications.isChecked():
            AlertHandler.show_alerts = True
        else:
            AlertHandler.show_alerts = False

    def startup_changed(self):
        # todo: probably should give notification to show that this setting has been changed.

        if self.preferences_window.startOnStartup.isChecked():
            # todo: make it so that this application starts on login
            # self.settings = QSettings(RUN_PATH, QSettings.NativeFormat)
            pass

        else:
            # todo: make it so that this application does NOT start on login
            pass

    def set_containing_folder(self):
        new_containing_folder = QFileDialog.getExistingDirectory(self, "Choose where to place OSF folder")
        osf_path = os.path.join(new_containing_folder, "OSF")

        if new_containing_folder == "":
            # cancel, closed, or no folder chosen
            return
        elif not os.path.exists(osf_path):
            os.makedirs(osf_path)
        elif os.path.isfile(osf_path):
            # FIXME: Consolidate redundant messages
            AlertHandler.warn(
                "An OSF file exists where you would like to create the OSF folder. Delete it, or choose a different location")
            logging.warning("An OSF file exists where you would like to create the OSF folder.")
            return

        user = session.query(User).filter(User.logged_in).one()
        user.osf_local_folder_path = os.path.join(osf_path)

        self.preferences_window.containingFolderTextEdit.setText(self._translate("Preferences", self.containing_folder))
        self.open_window(tab=Preferences.GENERAL)  # todo: dynamically update ui????
        self.containing_folder_updated_signal.emit(new_containing_folder)

    def update_sync_nodes(self):
        user = session.query(User).filter(User.logged_in).one()
        guid_list = []

        for tree_item in self.tree_items:
            for name, id in [(node.name, node.id) for node in self.remote_top_level_nodes]:
                if name == tree_item.text(self.PROJECT_NAME_COLUMN):
                    if tree_item.checkState(self.PROJECT_SYNC_COLUMN) == Qt.Checked:
                        guid_list.append(id)
        user.guid_for_top_level_nodes_to_sync = guid_list

    def open_window(self, tab=GENERAL):
        if self.isVisible():
            self.preferences_window.tabWidget.setCurrentIndex(tab)
            self.selector(tab)
        else:
            self.preferences_window.tabWidget.setCurrentIndex(tab)
            self.selector(tab)
            self.show()

    def selector(self, selected_index):
        if selected_index == self.GENERAL:
            user = session.query(User).filter(User.logged_in).one()
            containing_folder = os.path.dirname(user.osf_local_folder_path)
            self.preferences_window.containingFolderTextEdit.setText(self._translate("Preferences", containing_folder))
        elif selected_index == self.OSF:
            user = session.query(User).filter(User.logged_in).one()
            self.preferences_window.label.setText(self._translate("Preferences", user.full_name))
            self.create_tree_item_for_each_top_level_node()

    def reset_tree_widget(self):
        self.tree_items.clear()
        self.preferences_window.treeWidget.clear()

    def create_tree_item_for_each_top_level_node(self):
        self.remote_top_level_nodes = self.get_remote_top_level_nodes()
        self.reset_tree_widget()
        _translate = QCoreApplication.translate

        user = session.query(User).filter(User.logged_in).one()
        for node in self.remote_top_level_nodes:
            tree_item = QTreeWidgetItem(self.preferences_window.treeWidget)
            tree_item.setCheckState(self.PROJECT_SYNC_COLUMN, Qt.Unchecked)
            tree_item.setText(self.PROJECT_NAME_COLUMN, _translate("Preferences", node.name))

            if node.id in user.guid_for_top_level_nodes_to_sync:
                tree_item.setCheckState(self.PROJECT_SYNC_COLUMN, Qt.Checked)
            self.preferences_window.treeWidget.resizeColumnToContents(self.PROJECT_NAME_COLUMN)

            self.tree_items.append(tree_item)

    def get_remote_top_level_nodes(self):
        remote_top_level_nodes = []
        try:

            user = session.query(User).filter(User.logged_in).one()
            if user:
                user_nodes = []
                url = api_url_for(USERS, related_type=NODES, user_id=user.osf_id)
                headers = {'Authorization': 'Bearer {}'.format(user.oauth_token)}
                resp = requests.get(url, headers=headers).json()
                user_nodes.extend(resp['data'])
                while resp['links']['next']:
                    resp = requests.get(resp['links']['next'], headers=headers).json()
                    user_nodes.extend(resp['data'])
                for node in user_nodes:
                    verified_node = RemoteNode(node)
                    if verified_node.is_top_level:
                        remote_top_level_nodes.append(verified_node)
        except Exception as e:
            logging.warning(e)

        return remote_top_level_nodes

    def setup_slots(self):
        self.preferences_window.tabWidget.currentChanged.connect(self.selector)


def debug_trace():
    '''Set a tracepoint in the Python debugger that works with Qt'''
    from PyQt5.QtCore import pyqtRemoveInputHook

    from pdb import set_trace
    pyqtRemoveInputHook()
    set_trace()
