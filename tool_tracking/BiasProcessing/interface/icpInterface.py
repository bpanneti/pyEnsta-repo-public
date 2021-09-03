from enum import Enum
from tool_tracking.BiasProcessing.interface.roadLmsInterface import RoadLmsInterface
from tool_tracking.BiasProcessing.corrector.icp import Icp
from PyQt5.QtGui import QDoubleValidator, QIntValidator
from PyQt5.QtWidgets import QLineEdit, QLabel

class INTERFACE(Enum):
    NAME = 0
    SENSORS = 1
    INTEGRATION = 2
    THRESHOLD = 3
    MAX_ITERATION = 4
    TOLERANCE = 5

class IcpInterface(RoadLmsInterface):
    def __init__(self, node, biasTreeInterface):
        super(IcpInterface, self).__init__(node, biasTreeInterface)
        self.maxIntegration = 10000
        self.maxTolerance = 1
        self.name = "ICP"

    def onInit(self):
        super(IcpInterface, self).onInit()
        self.editor.extend([QLineEdit(), QLineEdit()])
        self.labels.extend([QLabel('Max iteration icp'), QLabel('Error tolerance (max 1)')])
        self.setMaxIteration()
        self.setTolerance()
        self.setThreshold()

    def chooseBiasCorrector(self):
        name = self.nameChoosed()
        threshold = int(self.editor[INTERFACE.THRESHOLD.value].text())
        integration = int(self.editor[INTERFACE.INTEGRATION.value].text())
        maxIteration = int(self.editor[INTERFACE.MAX_ITERATION.value].text())
        tolerance = float(self.editor[INTERFACE.TOLERANCE.value].text())

        self.node.biasCorrector = Icp(self.node, name, integration, maxIteration, tolerance, threshold)

    def setMaxIteration(self):
        self.editor[INTERFACE.MAX_ITERATION.value].setValidator(QIntValidator(0, self.maxIntegration))
        self.editor[INTERFACE.MAX_ITERATION.value].setText(str(self.node.biasCorrector.maxIteration))

    def setTolerance(self):
        self.editor[INTERFACE.TOLERANCE.value].setValidator(QDoubleValidator(0, 10, self.maxIntegration))
        self.editor[INTERFACE.TOLERANCE.value].setText(str(self.node.biasCorrector.tolerance))

    def onValidate(self):
        pass