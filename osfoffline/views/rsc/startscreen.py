# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './osfoffline/views/rsc/gui/startscreen_gui/startscreen.ui'
#
# Created by: PyQt5 UI code generator 5.5
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_startscreen(object):
    def setupUi(self, startscreen):
        startscreen.setObjectName("startscreen")
        startscreen.resize(642, 374)
        self.groupBox_7 = QtWidgets.QGroupBox(startscreen)
        self.groupBox_7.setGeometry(QtCore.QRect(100, 110, 441, 221))
        self.groupBox_7.setObjectName("groupBox_7")
        self.logInButton = QtWidgets.QPushButton(self.groupBox_7)
        self.logInButton.setGeometry(QtCore.QRect(330, 190, 99, 27))
        self.logInButton.setObjectName("logInButton")
        self.label_6 = QtWidgets.QLabel(self.groupBox_7)
        self.label_6.setGeometry(QtCore.QRect(10, 20, 141, 21))
        self.label_6.setObjectName("label_6")
        self.personalAccessTokenEdit = QtWidgets.QLineEdit(self.groupBox_7)
        self.personalAccessTokenEdit.setGeometry(QtCore.QRect(170, 20, 261, 31))
        self.personalAccessTokenEdit.setObjectName("personalAccessTokenEdit")
        self.label_7 = QtWidgets.QLabel(self.groupBox_7)
        self.label_7.setGeometry(QtCore.QRect(10, 70, 421, 111))
        self.label_7.setTextFormat(QtCore.Qt.PlainText)
        self.label_7.setObjectName("label_7")
        self.label = QtWidgets.QLabel(startscreen)
        self.label.setGeometry(QtCore.QRect(60, 30, 521, 60))
        font = QtGui.QFont()
        font.setPointSize(20)
        self.label.setFont(font)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")

        self.retranslateUi(startscreen)
        QtCore.QMetaObject.connectSlotsByName(startscreen)

    def retranslateUi(self, startscreen):
        _translate = QtCore.QCoreApplication.translate
        startscreen.setWindowTitle(_translate("startscreen", "startscreen"))
        self.groupBox_7.setTitle(_translate("startscreen", "Log in"))
        self.logInButton.setText(_translate("startscreen", "Log In"))
        self.label_6.setText(_translate("startscreen", "Personal Access Token"))
        self.label_7.setText(_translate("startscreen", "Note: Additional login methods will be available later. \n\n"
"To generate a personal access token, go to \n"
"http://osf.io/settings/tokens/create/ \n"
"The required scope for use with this application is osf.full_write. \n"
"The generated token will be displayed only once."))
        self.label.setText(_translate("startscreen", "Welcome to OSF Offline"))
