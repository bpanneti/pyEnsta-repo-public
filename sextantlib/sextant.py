# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'sextant.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets
from sextantlib.SAFIRSettings_ui import ADRESS_IP,TCP_PORT

class Ui_Dialog(object):

    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(657, 482)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setObjectName("label")
        self.horizontalLayout_2.addWidget(self.label)
        self.lineEdit_IPAdress = QtWidgets.QLineEdit(Dialog)
        self.lineEdit_IPAdress.setObjectName("lineEdit_IPAdress")
        self.horizontalLayout_2.addWidget(self.lineEdit_IPAdress)
        self.label_2 = QtWidgets.QLabel(Dialog)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_2.addWidget(self.label_2)
        self.lineEdit_Port = QtWidgets.QLineEdit(Dialog)
        self.lineEdit_Port.setObjectName("lineEdit_Port")
        self.horizontalLayout_2.addWidget(self.lineEdit_Port)
        self.lineEdit_IPAdress.editingFinished.connect(self.readIP)
        self.lineEdit_Port.editingFinished.connect(self.readPort)
        self.pushButton_connect = QtWidgets.QPushButton(Dialog)
        self.pushButton_connect.setObjectName("pushButton_connect")
        self.horizontalLayout_2.addWidget(self.pushButton_connect)
        self.pushButton = QtWidgets.QPushButton(Dialog)
        #self.pushButton.setEnabled(False)
        self.pushButton.setObjectName("pushButton")
        self.horizontalLayout_2.addWidget(self.pushButton)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.checkBox_Java = QtWidgets.QCheckBox(Dialog)
        self.checkBox_Java.setObjectName("checkBox_Java")
        self.verticalLayout_2.addWidget(self.checkBox_Java)
        self.groupBox = QtWidgets.QGroupBox(Dialog)
        #self.groupBox.setEnabled(True)
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.groupBox)
        self.verticalLayout.setObjectName("verticalLayout")
        self.textEdit_Chat = QtWidgets.QTextEdit(self.groupBox)
        self.textEdit_Chat.setReadOnly(True)
        self.textEdit_Chat.setObjectName("textEdit_Chat")
        self.verticalLayout.addWidget(self.textEdit_Chat)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.lineEdit_chatMessage = QtWidgets.QLineEdit(self.groupBox)
        self.lineEdit_chatMessage.setObjectName("lineEdit_chatMessage")
        self.horizontalLayout.addWidget(self.lineEdit_chatMessage)
        self.pushButton_sendMessage = QtWidgets.QPushButton(self.groupBox)
        self.pushButton_sendMessage.setObjectName("pushButton_sendMessage")
        self.horizontalLayout.addWidget(self.pushButton_sendMessage)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.verticalLayout_2.addWidget(self.groupBox)
        self.groupBox_Command = QtWidgets.QGroupBox(Dialog)
        self.groupBox_Command.setObjectName("groupBox_Command")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout(self.groupBox_Command)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.pushButton_NTP = QtWidgets.QPushButton(self.groupBox_Command)
        self.pushButton_NTP.setObjectName("pushButton_NTP")
        self.horizontalLayout_4.addWidget(self.pushButton_NTP)
        self.pushButton_SendConfiguation = QtWidgets.QPushButton(self.groupBox_Command)
        self.pushButton_SendConfiguation.setObjectName("pushButton_SendConfiguation")
        self.horizontalLayout_4.addWidget(self.pushButton_SendConfiguation)
        self.pushButton_QuitSafir = QtWidgets.QPushButton(self.groupBox_Command)
        self.pushButton_QuitSafir.setObjectName("pushButton_QuitSafir")
        self.horizontalLayout_4.addWidget(self.pushButton_QuitSafir)
        self.pushButton_SendJson = QtWidgets.QPushButton(self.groupBox_Command)
        self.pushButton_SendJson.setObjectName("pushButton_SendJson")
        #self.horizontalLayout_4.addWidget(self.pushButton_SendJson)

        self.groupBoxJson  = QtWidgets.QGroupBox(Dialog)
        self.groupBoxJson.setEnabled(True)
        self.groupBoxJson.setObjectName("groupBox")
        self.verticalLayoutJSON = QtWidgets.QVBoxLayout(self.groupBoxJson)
        self.verticalLayoutJSON.setObjectName("verticalLayout")
        
        #self.verticalLayout.addWidget( QtWidgets.QVBoxLayout(self.groupBoxJson))
        
        self.textEdit_Json = QtWidgets.QTextEdit(self.groupBoxJson)
        #self.textEdit_Json.setReadOnly(True)
        self.textEdit_Json.setObjectName("textEdit_JSON")
        self.verticalLayoutJSON.addWidget(self.textEdit_Json)
        self.verticalLayoutJSON.addWidget(self.pushButton_SendJson)
        self.verticalLayout_2.addWidget(self.groupBoxJson)
        self.verticalLayout_2.addWidget(self.groupBox_Command)
        
        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)
    def readIP(self):
         ADRESS_IP = self.lineEdit_IPAdress.text()
         #ADRESS_IP    = ADRESS_IP.encode('utf-8')
   
    def readPort(self):
           TCP_PORT  = int(self.lineEdit_Port.text())
    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.label.setText(_translate("Dialog", "IP adress"))
        self.label_2.setText(_translate("Dialog", "port"))
        self.pushButton_connect.setText(_translate("Dialog", "connect"))
        self.pushButton.setText(_translate("Dialog", "disconnect"))
        self.checkBox_Java.setText(_translate("Dialog", "ICD java "))
        self.groupBox.setTitle(_translate("Dialog", "Tchat"))
        self.groupBoxJson.setTitle(_translate("Dialog", "json message"))
        self.pushButton_sendMessage.setText(_translate("Dialog", "send"))
        self.pushButton_SendJson.setText(_translate("Dialog", "send Json"))
        self.groupBox_Command.setTitle(_translate("Dialog", "Command"))
        self.pushButton_NTP.setText(_translate("Dialog", "synchronization"))
        self.pushButton_QuitSafir.setText(_translate("Dialog", "exit SAFIR NG"))
        self.pushButton_SendConfiguation.setText(_translate("Dialog", "send configuration"))

