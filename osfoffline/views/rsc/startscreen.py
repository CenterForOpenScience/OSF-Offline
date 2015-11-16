# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'osfoffline/views/rsc/gui/startscreen_gui/startscreen.ui'
#
# Created by: PyQt5 UI code generator 5.5.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_startscreen(object):
    def setupUi(self, startscreen):
        startscreen.setObjectName("startscreen")
        startscreen.resize(280, 177)
        self.gridLayout = QtWidgets.QGridLayout(startscreen)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setObjectName("gridLayout")
        self.groupBox_7 = QtWidgets.QGroupBox(startscreen)
        self.groupBox_7.setObjectName("groupBox_7")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.groupBox_7)
        self.gridLayout_2.setContentsMargins(11, 11, 11, 11)
        self.gridLayout_2.setSpacing(6)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.passwordEdit = QtWidgets.QLineEdit(self.groupBox_7)
        self.passwordEdit.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.passwordEdit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.passwordEdit.setObjectName("passwordEdit")
        self.gridLayout_2.addWidget(self.passwordEdit, 1, 1, 1, 1)
        self.label_7 = QtWidgets.QLabel(self.groupBox_7)
        self.label_7.setObjectName("label_7")
        self.gridLayout_2.addWidget(self.label_7, 1, 0, 1, 1)
        self.usernameEdit = QtWidgets.QLineEdit(self.groupBox_7)
        self.usernameEdit.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.usernameEdit.setObjectName("usernameEdit")
        self.gridLayout_2.addWidget(self.usernameEdit, 0, 1, 1, 1)
        self.logInButton = QtWidgets.QPushButton(self.groupBox_7)
        self.logInButton.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.logInButton.setObjectName("logInButton")
        self.gridLayout_2.addWidget(self.logInButton, 2, 1, 1, 1)
        self.label_6 = QtWidgets.QLabel(self.groupBox_7)
        self.label_6.setObjectName("label_6")
        self.gridLayout_2.addWidget(self.label_6, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.groupBox_7, 1, 0, 1, 1)
        self.label = QtWidgets.QLabel(startscreen)
        font = QtGui.QFont()
        font.setPointSize(20)
        self.label.setFont(font)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.retranslateUi(startscreen)
        QtCore.QMetaObject.connectSlotsByName(startscreen)
        startscreen.setTabOrder(self.usernameEdit, self.passwordEdit)
        startscreen.setTabOrder(self.passwordEdit, self.logInButton)

    def retranslateUi(self, startscreen):
        _translate = QtCore.QCoreApplication.translate
        startscreen.setWindowTitle(_translate("startscreen", "OSF-Offline | Log in"))
        self.groupBox_7.setTitle(_translate("startscreen", "Log in"))
        self.label_7.setText(_translate("startscreen", "Password:"))
        self.logInButton.setText(_translate("startscreen", "Log In"))
        self.label_6.setText(_translate("startscreen", " Email:"))
        self.label.setText(_translate("startscreen", "Welcome to OSF Offline"))
