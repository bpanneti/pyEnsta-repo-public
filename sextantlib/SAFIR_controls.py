# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'SAFIR_controls.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(400, 300)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.pushButton_synchronize = QtWidgets.QPushButton(Form)
        self.pushButton_synchronize.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("icones/clock.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_synchronize.setIcon(icon)
        self.pushButton_synchronize.setObjectName("pushButton_synchronize")
        self.horizontalLayout_4.addWidget(self.pushButton_synchronize)
        self.pushButton_sendConf = QtWidgets.QPushButton(Form)
        self.pushButton_sendConf.setText("")
        
   
        
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap("icones/send.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_sendConf.setIcon(icon1)
        self.pushButton_sendConf.setObjectName("pushButton_sendConf")
        self.horizontalLayout_4.addWidget(self.pushButton_sendConf)
        self.verticalLayout_2.addLayout(self.horizontalLayout_4)
        
        self.checkBox_javaOnly = QtWidgets.QCheckBox(Form)
        self.checkBox_javaOnly.setObjectName("checkBox_javaOnly")
        self.checkBox_javaOnly.setText("java message only")
        self.horizontalLayout_4.addWidget(self.checkBox_javaOnly)
        
        
        self.groupBox = QtWidgets.QGroupBox(Form)
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.groupBox)
        self.verticalLayout.setObjectName("verticalLayout")
        self.checkBox_activation = QtWidgets.QCheckBox(self.groupBox)
        self.checkBox_activation.setObjectName("checkBox_activation")
        self.verticalLayout.addWidget(self.checkBox_activation)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label = QtWidgets.QLabel(self.groupBox)
        self.label.setObjectName("label")
        self.horizontalLayout_3.addWidget(self.label)
        self.lineEdit_nbRuns = QtWidgets.QLineEdit(self.groupBox)
        self.lineEdit_nbRuns.setEnabled(False)
        self.lineEdit_nbRuns.setObjectName("lineEdit_nbRuns")
        self.horizontalLayout_3.addWidget(self.lineEdit_nbRuns)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_2 = QtWidgets.QLabel(self.groupBox)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_2.addWidget(self.label_2)
        self.lineEdit_Time = QtWidgets.QLineEdit(self.groupBox)
        self.lineEdit_Time.setEnabled(False)
        self.lineEdit_Time.setObjectName("lineEdit_Time")
        self.horizontalLayout_2.addWidget(self.lineEdit_Time)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.verticalLayout_2.addWidget(self.groupBox)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.pushButton_sendConf.setToolTip(_translate("Form", "send configuration"))
        self.groupBox.setTitle(_translate("Form", "Monte Carlo "))
        self.checkBox_activation.setText(_translate("Form", "activate"))
        self.label.setText(_translate("Form", "runs"))
        self.label_2.setText(_translate("Form", "Time duration (in sec)"))

