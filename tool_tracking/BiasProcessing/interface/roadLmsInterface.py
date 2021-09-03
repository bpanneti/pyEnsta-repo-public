from enum import Enum
from tool_tracking.BiasProcessing.interface.biasCorrectorInterface import BiasCorrectorInterface
from tool_tracking.BiasProcessing.corrector.roadLms import RoadLms
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QLineEdit, QLabel

class INTERFACE(Enum):
    NAME = 0
    SENSORS = 1
    INTEGRATION = 2
    THRESHOLD = 3

class RoadLmsInterface(BiasCorrectorInterface):
    def __init__(self, node, biasTreeInterface):
        super(RoadLmsInterface, self).__init__(node, biasTreeInterface)
        self.integrationMax = 10000
        self.name = "Road LMS"
        self.thresholdMax = 10000

    def onInit(self):
        self.editor.append(QLineEdit())
        self.labels.append(QLabel('Integration time (s)'))
        self.setIntegrationTime()

        self.editor.append(QLineEdit())
        self.labels.append(QLabel('Max projection threshold (m)'))
        self.setThreshold()

    def chooseBiasCorrector(self):
        super(RoadLmsInterface, self).chooseBiasCorrector()
        name = self.nameChoosed()
        integration = int(self.editor[INTERFACE.INTEGRATION.value].text())
        threshold = int(self.editor[INTERFACE.THRESHOLD.value].text())

        self.node.biasCorrector = RoadLms(self.node, name, integration, threshold)

    def setIntegrationTime(self):
        self.editor[INTERFACE.INTEGRATION.value].setValidator(QIntValidator(0, self.integrationMax))
        self.editor[INTERFACE.INTEGRATION.value].setText(str(self.node.biasCorrector.integration))

    def setThreshold(self):
        self.editor[INTERFACE.THRESHOLD.value].setValidator(QIntValidator(0, self.thresholdMax))
        self.editor[INTERFACE.THRESHOLD.value].setText(str(self.node.biasCorrector.threshold))

    def onValidate(self):
        pass