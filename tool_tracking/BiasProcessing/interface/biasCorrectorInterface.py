from abc import ABCMeta, abstractmethod
from enum import Enum
from tool_tracking.BiasProcessing.corrector.biasCorrector import BiasCorrector, BIAS_CORRECTORS_TYPE
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QComboBox, QListWidget, QGridLayout, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

#tuple (1, 2) where :
#1 : corrector type
#2 : associated corrector gui

class INTERFACE(Enum):
    NAME = 0
    SENSORS = 1

class BiasCorrectorInterface:
    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(self, node, biasTreeInterface):
        self.biasTreeInterface = biasTreeInterface
        self.node = node
        self.name = "Bias Corrector"
        self.window = QDialog()
        self.layout = QVBoxLayout()
        self.editor = [QLineEdit(), QListWidget()]
        self.labels = [
            QLabel('{} name'.format(self.name)),
            QLabel('Sensor\'s list to work on')
        ]
        self.icone = 'icones/tracker.png'
        
    def initWindow(self):
        self.setName()
        self.setSensors()
        self.onInit()

        self.setLayout()

        self.setWindowProperties()

        self.window.exec_()

    def setName(self):
        if self.node.biasCorrector:
            self.editor[INTERFACE.NAME.value].setText(self.node.biasCorrector.name)

    def setSensors(self):
        for sensor in self.node.sensors:
            self.editor[INTERFACE.SENSORS.value].addItem("Sensor : {} {}".format(str(sensor.id),str(sensor.name)))

        rowSize = self.editor[INTERFACE.SENSORS.value].sizeHintForRow(0)
        
        if rowSize:
            self.editor[INTERFACE.SENSORS.value].setMaximumHeight(rowSize*2)
    
    def setLayout(self):
        grid = QGridLayout()
        grid.setSpacing(10)

        for i in range (len(self.labels)):
            grid.addWidget(self.labels[i], i+1, 0)
            grid.addWidget(self.editor[i], i+1, 1)

        self.layout.addLayout(grid)

        buttonLayout = QHBoxLayout()

        self.addButton(self.onOk, buttonLayout, "Ok")
        self.addButton(self.onCancel, buttonLayout, "Cancel")

        self.layout.addLayout(buttonLayout)

        self.window.setLayout(self.layout)

    def setWindowProperties(self):
        self.window.setGeometry(300, 300, 350, 300)
        self.window.setWindowTitle("Edit {}".format(self.name))
        self.window.setWindowIcon(QIcon(self.icone))
        self.window.setWindowModality(Qt.ApplicationModal)

    def addButton(self, handle, layout, text = ""):
        button = QPushButton(text)
        layout.addWidget(button)
        button.clicked.connect(handle)

    def nameChoosed(self):
        return self.editor[INTERFACE.NAME.value].text()

    @abstractmethod
    def chooseBiasCorrector(self):
        pass

    def onOk(self):
        self.onValidate()
        self.chooseBiasCorrector()
        self.biasTreeInterface.receiveItem(self.node.biasCorrector)

        self.window.close()

    def onCancel(self):
        self.window.close()

    @abstractmethod
    def onInit(self):
        pass

    @abstractmethod
    def onValidate(self):
        pass