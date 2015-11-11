# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'osfoffline\views\rsc\gui\preferences_gui\preferences.ui'
#
# Created by: PyQt5 UI code generator 5.5.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Preferences(object):
    def setupUi(self, Preferences):
        Preferences.setObjectName("Preferences")
        Preferences.resize(590, 356)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(Preferences)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.tabWidget = QtWidgets.QTabWidget(Preferences)
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.groupBox = QtWidgets.QGroupBox(self.tab)
        self.groupBox.setGeometry(QtCore.QRect(10, 20, 551, 80))
        self.groupBox.setObjectName("groupBox")
        self.desktopNotifications = QtWidgets.QCheckBox(self.groupBox)
        self.desktopNotifications.setGeometry(QtCore.QRect(10, 20, 541, 22))
        self.desktopNotifications.setChecked(True)
        self.desktopNotifications.setObjectName("desktopNotifications")
        self.startOnStartup = QtWidgets.QCheckBox(self.groupBox)
        self.startOnStartup.setGeometry(QtCore.QRect(10, 40, 541, 22))
        self.startOnStartup.setChecked(True)
        self.startOnStartup.setObjectName("startOnStartup")
        self.groupBox_6 = QtWidgets.QGroupBox(self.tab)
        self.groupBox_6.setGeometry(QtCore.QRect(10, 110, 561, 61))
        self.groupBox_6.setObjectName("groupBox_6")
        self.changeFolderButton = QtWidgets.QPushButton(self.groupBox_6)
        self.changeFolderButton.setGeometry(QtCore.QRect(440, 20, 99, 31))
        self.changeFolderButton.setObjectName("changeFolderButton")
        self.containingFolderTextEdit = QtWidgets.QTextEdit(self.groupBox_6)
        self.containingFolderTextEdit.setGeometry(QtCore.QRect(20, 20, 331, 31))
        self.containingFolderTextEdit.setObjectName("containingFolderTextEdit")
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.groupBox_2 = QtWidgets.QGroupBox(self.tab_2)
        self.groupBox_2.setGeometry(QtCore.QRect(10, 0, 541, 51))
        self.groupBox_2.setObjectName("groupBox_2")
        self.label = QtWidgets.QLabel(self.groupBox_2)
        self.label.setGeometry(QtCore.QRect(20, 20, 411, 31))
        self.label.setObjectName("label")
        self.accountLogOutButton = QtWidgets.QPushButton(self.groupBox_2)
        self.accountLogOutButton.setGeometry(QtCore.QRect(440, 20, 99, 31))
        self.accountLogOutButton.setObjectName("accountLogOutButton")
        self.groupBox_4 = QtWidgets.QGroupBox(self.tab_2)
        self.groupBox_4.setGeometry(QtCore.QRect(10, 60, 541, 241))
        self.groupBox_4.setObjectName("groupBox_4")
        self.groupBox_5 = QtWidgets.QGroupBox(self.groupBox_4)
        self.groupBox_5.setGeometry(QtCore.QRect(10, 20, 521, 211))
        self.groupBox_5.setObjectName("groupBox_5")
        self.changeFolderButton_2 = QtWidgets.QPushButton(self.groupBox_5)
        self.changeFolderButton_2.setGeometry(QtCore.QRect(420, 100, 99, 31))
        self.changeFolderButton_2.setObjectName("changeFolderButton_2")
        self.treeWidget = QtWidgets.QTreeWidget(self.groupBox_5)
        self.treeWidget.setGeometry(QtCore.QRect(10, 60, 311, 151))
        self.treeWidget.setToolTipDuration(-1)
        self.treeWidget.setObjectName("treeWidget")
        self.pushButton = QtWidgets.QPushButton(self.groupBox_5)
        self.pushButton.setGeometry(QtCore.QRect(10, 20, 115, 32))
        self.pushButton.setObjectName("pushButton")
        self.pushButton_2 = QtWidgets.QPushButton(self.groupBox_5)
        self.pushButton_2.setGeometry(QtCore.QRect(130, 20, 115, 32))
        self.pushButton_2.setObjectName("pushButton_2")
        self.tabWidget.addTab(self.tab_2, "")
        self.tab_5 = QtWidgets.QWidget()
        self.tab_5.setObjectName("tab_5")
        self.textEdit_2 = QtWidgets.QTextEdit(self.tab_5)
        self.textEdit_2.setGeometry(QtCore.QRect(20, 20, 551, 251))
        self.textEdit_2.setObjectName("textEdit_2")
        self.tabWidget.addTab(self.tab_5, "")
        self.horizontalLayout.addWidget(self.tabWidget)
        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.retranslateUi(Preferences)
        self.tabWidget.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(Preferences)

    def retranslateUi(self, Preferences):
        _translate = QtCore.QCoreApplication.translate
        Preferences.setWindowTitle(_translate("Preferences", "Preferences"))
        self.groupBox.setTitle(_translate("Preferences", "System"))
        self.desktopNotifications.setText(_translate("Preferences", "Show Desktop Notifications"))
        self.startOnStartup.setText(_translate("Preferences", "Start OSF Offline on Computer Startup"))
        self.groupBox_6.setTitle(_translate("Preferences", "Choose folder to Place OSF folder in "))
        self.changeFolderButton.setText(_translate("Preferences", "Change"))
        self.containingFolderTextEdit.setHtml(_translate("Preferences", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Ubuntu\'; font-size:11pt;\">/home/himanshu/somefolder/My Project</span></p></body></html>"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("Preferences", "General"))
        self.groupBox_2.setTitle(_translate("Preferences", "Account"))
        self.label.setText(_translate("Preferences", "User name"))
        self.accountLogOutButton.setText(_translate("Preferences", "Log Out"))
        self.groupBox_4.setTitle(_translate("Preferences", "Project"))
        self.groupBox_5.setTitle(_translate("Preferences", "Choose Projects to Sync With"))
        self.changeFolderButton_2.setText(_translate("Preferences", "Update"))
        self.treeWidget.headerItem().setText(0, _translate("Preferences", "Sync"))
        self.treeWidget.headerItem().setText(1, _translate("Preferences", "Projects"))
        self.pushButton.setText(_translate("Preferences", "Sync All"))
        self.pushButton_2.setText(_translate("Preferences", "Sync None"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("Preferences", "OSF"))
        self.textEdit_2.setHtml(_translate("Preferences", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Ubuntu\'; font-size:11pt;\">This is OSF OFFLINE. Please go ahead and use it and make more software based off of it. Please and Thank You. </span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'Ubuntu\'; font-size:11pt;\"><br /></p>\n"
"<p align=\"center\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Ubuntu\'; font-size:11pt;\">© Center for Open Science</span></p></body></html>"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_5), _translate("Preferences", "About"))

