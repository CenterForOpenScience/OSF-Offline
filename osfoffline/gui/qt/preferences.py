import logging
import os
import sys
import configparser
from distutils.dir_util import copy_tree

from PyQt5 import QtCore
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QTreeWidgetItem
from sqlalchemy.orm.exc import NoResultFound

import osfoffline
from osfoffline import language
from osfoffline.application.background import BackgroundHandler
from osfoffline.client.osf import OSFClient
from osfoffline.database import Session
from osfoffline.database.models import User, Node
from osfoffline.gui.qt.generated.preferences import Ui_Settings

logger = logging.getLogger(__name__)

WINDOWS_RUN_PATH = 'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run'
# sys.platform will be win32 regardless of the bitness of the underlying Windows system
# see http://svn.python.org/view/python/trunk/PC/pyconfig.h?view=markup line 334
ON_WINDOWS = sys.platform == 'win32'
ON_MAC = sys.platform == 'darwin'
MAC_PLIST_FILE_PATH = os.path.expanduser('~/Library/LaunchAgents/io.cos.osfsync.plist')
MAC_PLIST_FILE_CONTENTS = """
<?xml version="1.0" encoding="UTF-8"?>
<plist version="1.0">
  <dict>
    <key>RunAtLoad</key>
    <true />
    <key>Label</key>
    <string>io.cos.osfsync</string>
    <key>ProgramArguments</key>
    <array>
      <string>{}</string>
    </array>
  </dict>
</plist>
""".format(sys.argv[0])


def get_parent_id(node):
    try:
        parent = node.raw['relationships']['parent']
    except KeyError:
        return None

    return parent['links']['related']['href'].split('/')[-2]


class Preferences(QDialog, Ui_Settings):
    """
    This class is a wrapper for the Ui_Preferences and its controls
    """
    GENERAL = 0
    OSF = 1
    ABOUT = 2

    PROJECT_NAME_COLUMN = 1
    PROJECT_SYNC_COLUMN = 0

    preferences_closed_signal = pyqtSignal()
    containing_folder_updated_signal = pyqtSignal((str,))

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.containing_folder = ''
        self._translate = QCoreApplication.translate

        self.changeFolderButton_2.clicked.connect(self.update_sync_nodes)
        self.changeFolderButton.clicked.connect(self.update_containing_folder)
        self.pushButton.clicked.connect(self.sync_all)
        self.pushButton_2.clicked.connect(self.sync_none)
        self.tabWidget.currentChanged.connect(self.selector)
        self.optOutLogging.stateChanged.connect(self.change_logging)
        self.labelVersion.setText('OSF Sync v{}'.format(osfoffline.__version__))

        if ON_WINDOWS:
            self.winRegistryRunKey = QSettings(WINDOWS_RUN_PATH, QSettings.NativeFormat)
            self.startAtBoot.setChecked(self.winRegistryRunKey.contains('OSF Sync'))
        elif ON_MAC:
            self.startAtBoot.setChecked(os.path.exists(MAC_PLIST_FILE_PATH))

        self.tree_items = []
        self.selected_nodes = []

        self._executor = QtCore.QThread()
        self.node_fetcher = NodeFetcher()

    def change_logging(self):
        config = configparser.ConfigParser()
        # path relative to start.py
        user_setting_file = 'osfoffline/settings/user-settings.ini'

        config.read(user_setting_file)
        if self.optOutLogging.isChecked():
            config.set('main', 'allow', 'False')
        else:
            config.set('main', 'allow', 'True')

        with open(user_setting_file, 'w') as fp:
                config.write(fp)

    def on_first_boot(self):
        self.startAtBoot.setChecked(True)

    def update_containing_folder(self):
        self.set_containing_folder(save_setting=True)

    def closeEvent(self, event):

        if set(self.selected_nodes) != set([node.id for tree_item, node in self.tree_items
                                            if tree_item.checkState(self.PROJECT_SYNC_COLUMN) == Qt.Checked]):
            if self.selected_nodes and not self.tree_items:
                return
            else:
                reply = QMessageBox()
                reply.setText('Unsaved changes')
                reply.setIcon(QMessageBox.Warning)
                reply.setInformativeText(language.UNSAVED_CHANGES)
                default = reply.addButton('Exit without saving', QMessageBox.YesRole)
                reply.addButton('Review changes', QMessageBox.NoRole)
                reply.setDefaultButton(default)
                if reply.exec_() != 0:
                    return event.ignore()
        self.reset_tree_widget()

        with Session() as session:
            user = session.query(User).one_or_none()
            if user:
                user.first_boot = False
                session.add(user)
                session.commit()

        if ON_WINDOWS:
            if self.startAtBoot.isChecked():
                self.winRegistryRunKey.setValue('OSF Sync', sys.argv[0])
            else:
                self.winRegistryRunKey.remove('OSF Sync')
        elif ON_MAC:
            if self.startAtBoot.isChecked():
                with open(MAC_PLIST_FILE_PATH, 'w+') as file:
                    file.write(MAC_PLIST_FILE_CONTENTS)
            elif os.path.exists(MAC_PLIST_FILE_PATH):
                os.remove(MAC_PLIST_FILE_PATH)

        event.accept()

    def set_containing_folder(self, save_setting=False):
        with Session() as session:
            user = session.query(User).one()

        logger.warning('Changing containing folder')
        res = QFileDialog.getExistingDirectory(caption='Choose where to place OSF folder')
        if not res:
            return
        containing_folder = os.path.abspath(res)
        folder = os.path.join(containing_folder, 'OSF')

        if save_setting:
            logger.debug('Copy files into new OSF folder.')
            # copy the synced folders from the old to new location
            # so OSF doesn't think they were deleted
            copy_tree(user.folder, folder)

        user.folder = folder

        self.containingFolderTextEdit.setText(self._translate("Preferences", self.containing_folder))
        self.open_window(tab=Preferences.GENERAL)  # todo: dynamically update ui????
        self.containing_folder_updated_signal.emit(folder)

        if save_setting:
            with Session() as session:
                session.add(user)
                session.commit()
            self.update_sync_nodes()

    def update_sync_nodes(self):
        self.selected_nodes = []

        with Session() as session:
            user = session.query(User).one()
            for tree_item, node in self.tree_items:
                checked = tree_item.checkState(self.PROJECT_SYNC_COLUMN) == Qt.Checked
                try:
                    db_node = session.query(Node).filter(Node.id == node.id).one()
                except NoResultFound:
                    db_node = None

                if checked:
                    self.selected_nodes.append(node.id)
                    if not db_node:
                        session.add(
                            Node(id=node.id, title=node.title, user=user, sync=True)
                        )
                    else:
                        db_node.sync = True
                elif db_node:
                    session.delete(db_node)
            session.commit()
        BackgroundHandler().sync_now()
        self.close()

    def sync_all(self):
        for tree_item, node in self.tree_items:
            tree_item.setCheckState(self.PROJECT_SYNC_COLUMN, Qt.Checked)

    def sync_none(self):
        for tree_item, node in self.tree_items:
            tree_item.setCheckState(self.PROJECT_SYNC_COLUMN, Qt.Unchecked)

    def open_window(self, *, tab=GENERAL):
        if self.isVisible():
            self.tabWidget.setCurrentIndex(tab)
            self.selector(tab)
        else:
            self.tabWidget.setCurrentIndex(tab)
            self.selector(tab)
            self.show()
        self.raise_()
        self.activateWindow()

    def selector(self, selected_index):
        with Session() as session:
            user = session.query(User).one()
        if selected_index == self.GENERAL:
            containing_folder = os.path.dirname(user.folder)
            self.containingFolderTextEdit.setText(self._translate("Preferences", containing_folder))
        elif selected_index == self.OSF:
            self.label.setText(self._translate("Preferences", user.full_name))
            self._executor = QtCore.QThread()
            self.node_fetcher = NodeFetcher()
            self.treeWidget.setStyleSheet("background-color: grey")
            self.treeWidget.setCursor(QtCore.Qt.BusyCursor)
            self.node_fetcher.finished[list].connect(self.populate_item_tree)
            self.node_fetcher.finished[int].connect(self.item_load_error)
            self.node_fetcher.moveToThread(self._executor)
            self._executor.started.connect(self.node_fetcher.fetch)
            self._executor.start()

    def reset_tree_widget(self):
        self.tree_items.clear()
        self.treeWidget.clear()

    @QtCore.pyqtSlot(list)
    def populate_item_tree(self, nodes):
        self.reset_tree_widget()
        _translate = QCoreApplication.translate
        self.selected_nodes = []
        with Session() as session:
            all_selected_nodes = [n.id for n in session.query(Node)]
            for n in session.query(Node):
                if n.parent_id not in all_selected_nodes and n.id not in self.selected_nodes:
                    self.selected_nodes.append(n.id)

        for node in sorted(nodes, key=lambda n: n.title):
            tree_item = QTreeWidgetItem(self.treeWidget)
            tree_item.setCheckState(self.PROJECT_SYNC_COLUMN,
                                    Qt.Checked if node.id in self.selected_nodes else Qt.Unchecked)
            tree_item.setText(self.PROJECT_NAME_COLUMN,
                              _translate('Preferences', '{} - {}'.format(node.title, node.id)))

            self.tree_items.append((tree_item, node))

        self.treeWidget.resizeColumnToContents(self.PROJECT_SYNC_COLUMN)
        self.treeWidget.resizeColumnToContents(self.PROJECT_NAME_COLUMN)
        self.treeWidget.unsetCursor()
        self.treeWidget.setStyleSheet("background-color: white")

    @QtCore.pyqtSlot(int)
    def item_load_error(self, error_code):
        """If the list of nodes does not load, warn the user, then close prefs panel without saving changes"""
        # TODO: Is there a more elegant way to pass errors across signal or thread boundaries?
        QMessageBox.critical(None,
                             'Error fetching projects',
                             language.ITEM_LOAD_ERROR)
        self.reset_tree_widget()
        self.reject()


class NodeFetcher(QtCore.QObject):
    finished = QtCore.pyqtSignal([list], [int])

    def fetch(self):
        """Fetch the list of nodes associated with a user. Returns either a list, or an (int) error code."""
        try:
            client = OSFClient()
            client_user = client.get_user()
            user_nodes = client_user.get_nodes()
        except:
            logger.exception('Error fetching list of nodes')
            result = -1
        else:
            nodes_id = [n.id for n in user_nodes]
            result = []
            for node in user_nodes:
                if 'parent' not in node.raw['relationships'] or get_parent_id(node) not in nodes_id:
                    result.append(node)

        self.finished[type(result)].emit(result)
