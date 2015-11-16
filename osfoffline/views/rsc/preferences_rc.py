# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'osfoffline/views/rsc/gui/preferences_gui/preferences.ui'
#
# Created by: PyQt5 UI code generator 5.4.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Settings(object):
    def setupUi(self, Settings):
        Settings.setObjectName("Settings")
        Settings.resize(704, 485)
        self.gridLayout_3 = QtWidgets.QGridLayout(Settings)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.tabWidget = QtWidgets.QTabWidget(Settings)
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.gridLayout_7 = QtWidgets.QGridLayout(self.tab)
        self.gridLayout_7.setObjectName("gridLayout_7")
        self.groupBox = QtWidgets.QGroupBox(self.tab)
        self.groupBox.setObjectName("groupBox")
        self.desktopNotifications = QtWidgets.QCheckBox(self.groupBox)
        self.desktopNotifications.setGeometry(QtCore.QRect(10, 20, 541, 22))
        self.desktopNotifications.setChecked(True)
        self.desktopNotifications.setObjectName("desktopNotifications")
        self.startOnStartup = QtWidgets.QCheckBox(self.groupBox)
        self.startOnStartup.setGeometry(QtCore.QRect(10, 40, 541, 22))
        self.startOnStartup.setChecked(True)
        self.startOnStartup.setObjectName("startOnStartup")
        self.gridLayout_7.addWidget(self.groupBox, 0, 0, 1, 1)
        self.groupBox_6 = QtWidgets.QGroupBox(self.tab)
        self.groupBox_6.setObjectName("groupBox_6")
        self.changeFolderButton = QtWidgets.QPushButton(self.groupBox_6)
        self.changeFolderButton.setGeometry(QtCore.QRect(440, 20, 99, 31))
        self.changeFolderButton.setObjectName("changeFolderButton")
        self.containingFolderTextEdit = QtWidgets.QTextEdit(self.groupBox_6)
        self.containingFolderTextEdit.setGeometry(QtCore.QRect(20, 20, 331, 31))
        self.containingFolderTextEdit.setObjectName("containingFolderTextEdit")
        self.gridLayout_7.addWidget(self.groupBox_6, 1, 0, 1, 1)
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.gridLayout = QtWidgets.QGridLayout(self.tab_2)
        self.gridLayout.setObjectName("gridLayout")
        self.groupBox_2 = QtWidgets.QGroupBox(self.tab_2)
        self.groupBox_2.setObjectName("groupBox_2")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.groupBox_2)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.label = QtWidgets.QLabel(self.groupBox_2)
        self.label.setObjectName("label")
        self.gridLayout_2.addWidget(self.label, 0, 0, 1, 1)
        self.accountLogOutButton = QtWidgets.QPushButton(self.groupBox_2)
        self.accountLogOutButton.setObjectName("accountLogOutButton")
        self.gridLayout_2.addWidget(self.accountLogOutButton, 0, 1, 1, 1)
        self.gridLayout.addWidget(self.groupBox_2, 0, 0, 1, 1)
        self.groupBox_4 = QtWidgets.QGroupBox(self.tab_2)
        self.groupBox_4.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.groupBox_4.setAutoFillBackground(False)
        self.groupBox_4.setAlignment(QtCore.Qt.AlignCenter)
        self.groupBox_4.setObjectName("groupBox_4")
        self.gridLayout_5 = QtWidgets.QGridLayout(self.groupBox_4)
        self.gridLayout_5.setObjectName("gridLayout_5")
        self.groupBox_5 = QtWidgets.QGroupBox(self.groupBox_4)
        self.groupBox_5.setObjectName("groupBox_5")
        self.gridLayout_4 = QtWidgets.QGridLayout(self.groupBox_5)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.pushButton_2 = QtWidgets.QPushButton(self.groupBox_5)
        self.pushButton_2.setObjectName("pushButton_2")
        self.gridLayout_4.addWidget(self.pushButton_2, 0, 1, 1, 1)
        self.pushButton = QtWidgets.QPushButton(self.groupBox_5)
        self.pushButton.setObjectName("pushButton")
        self.gridLayout_4.addWidget(self.pushButton, 0, 0, 1, 1)
        self.treeWidget = QtWidgets.QTreeWidget(self.groupBox_5)
        self.treeWidget.setToolTipDuration(-1)
        self.treeWidget.setObjectName("treeWidget")
        self.gridLayout_4.addWidget(self.treeWidget, 1, 0, 1, 2)
        self.changeFolderButton_2 = QtWidgets.QPushButton(self.groupBox_5)
        self.changeFolderButton_2.setObjectName("changeFolderButton_2")
        self.gridLayout_4.addWidget(self.changeFolderButton_2, 1, 2, 1, 1)
        self.gridLayout_5.addWidget(self.groupBox_5, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.groupBox_4, 1, 0, 1, 1)
        self.tabWidget.addTab(self.tab_2, "")
        self.tab_5 = QtWidgets.QWidget()
        self.tab_5.setObjectName("tab_5")
        self.gridLayout_6 = QtWidgets.QGridLayout(self.tab_5)
        self.gridLayout_6.setObjectName("gridLayout_6")
        self.textEdit_2 = QtWidgets.QTextEdit(self.tab_5)
        self.textEdit_2.setObjectName("textEdit_2")
        self.gridLayout_6.addWidget(self.textEdit_2, 0, 0, 1, 1)
        self.tabWidget.addTab(self.tab_5, "")
        self.horizontalLayout.addWidget(self.tabWidget)
        self.gridLayout_3.addLayout(self.horizontalLayout, 0, 0, 1, 1)

        self.retranslateUi(Settings)
        self.tabWidget.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(Settings)

    def retranslateUi(self, Settings):
        _translate = QtCore.QCoreApplication.translate
        Settings.setWindowTitle(_translate("Settings", "Settings"))
        self.groupBox.setTitle(_translate("Settings", "System"))
        self.desktopNotifications.setText(_translate("Settings", "Show Desktop Notifications"))
        self.startOnStartup.setText(_translate("Settings", "Start OSF Offline on Computer Startup"))
        self.groupBox_6.setTitle(_translate("Settings", "Choose folder to Place OSF folder in "))
        self.changeFolderButton.setText(_translate("Settings", "Change"))
        self.containingFolderTextEdit.setHtml(_translate("Settings", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'.Helvetica Neue DeskInterface\'; font-size:13pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Ubuntu\'; font-size:11pt;\">/home/himanshu/somefolder/My Project</span></p></body></html>"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("Settings", "General"))
        self.groupBox_2.setTitle(_translate("Settings", "Account"))
        self.label.setText(_translate("Settings", "User name"))
        self.accountLogOutButton.setText(_translate("Settings", "Log Out"))
        self.groupBox_4.setTitle(_translate("Settings", "Project"))
        self.groupBox_5.setTitle(_translate("Settings", "Choose Projects to Sync With"))
        self.pushButton_2.setText(_translate("Settings", "Sync None"))
        self.pushButton.setText(_translate("Settings", "Sync All"))
        self.treeWidget.headerItem().setText(0, _translate("Settings", "Sync"))
        self.treeWidget.headerItem().setText(1, _translate("Settings", "Projects"))
        self.changeFolderButton_2.setText(_translate("Settings", "Apply Settings"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("Settings", "OSF"))
        self.textEdit_2.setHtml(_translate("Settings", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'.Helvetica Neue DeskInterface\'; font-size:13pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Ubuntu\'; font-size:11pt;\">This is OSF OFFLINE. Please go ahead and use it and make more software based off of it. Please and Thank You. </span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'Ubuntu\'; font-size:11pt;\"><br /></p>\n"
"<p align=\"center\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Ubuntu\'; font-size:11pt;\">© Center for Open Science</span></p></body></html>"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_5), _translate("Settings", "About"))

