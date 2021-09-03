from enum import Enum
from abc import ABCMeta, abstractmethod
from itertools import count
import inspect
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from threading import Thread
import time


class BIAS_CORRECTORS_TYPE(Enum):
    NONE = -1
    ROAD_LMS  = 0
    ICP = 1

class BiasCorrector(QObject):
    __metaclass__ = ABCMeta

    __cnt = count(0)

    def __init__(self, parent, name = "Corrector"):
        QObject.__init__(self, None)
        self._thread = Thread(target=self.asyncUpdate)
        # self.moveToThread(self._thread)
        self.id = next(self.__cnt)
        self.parentId = int(parent.id)                          # Node Id
        self.parent = parent
        parent.biasCorrector = self
        self.name = name
        self.type = BIAS_CORRECTORS_TYPE.NONE
        self.xBiais = None
        self.yBiais = None
        self.yaw = None
        self.swap = False
        self.scale = None
        self.initialize()

    def initialize(self):
        print("Class {} function {}".format(self.__class__.__name__, inspect.currentframe().f_code.co_name))
        self.onInitialize()

    def update(self):
        print("Class {} function {}".format(self.__class__.__name__, inspect.currentframe().f_code.co_name))
        if not self._thread.isAlive():
            self._thread = Thread(target = self.asyncUpdate)
            self._thread.start()
        self.onDisplay()

    def lateUpdate(self):
        print("Class {} function {}".format(self.__class__.__name__, inspect.currentframe().f_code.co_name))
        self.onLateUpdate()

    def save(self, executeRequest, conn):
        command = []
        command.append("insert into biasCorrector_t values ")
        command.append("({}, '{}')".format(self.parentId, self.name))
        command = ''.join(command)

        executeRequest(conn, command)
        print('Bias corrector saved')

    def asyncUpdate(self):
        self.onUpdate()
        self.lateUpdate()

    def onDisplay(self):
        pass

    def fixedBias(self):
        print("Avant : \nYaw : {}\nPos X : {}\nPos Y : {}".format(self.parent.sensors[0].bias.orientation.yaw, self.parent.sensors[0].bias.position.x_ENU, self.parent.sensors[0].bias.position.y_ENU))
        self.parent.sensors[0].bias.orientation.setOrientation(self.parent.sensors[0].bias.orientation.yaw + self.yaw, 0, 0)
        self.parent.sensors[0].bias.position.setXYZ(self.parent.sensors[0].bias.position.x_ENU + self.xBiais, self.parent.sensors[0].bias.position.y_ENU + self.yBiais, 0, 'ENU')
        print("Après : \nYaw : {}\nPos X : {}\nPos Y : {}".format(self.parent.sensors[0].bias.orientation.yaw, self.parent.sensors[0].bias.position.x_ENU, self.parent.sensors[0].bias.position.y_ENU))

    @abstractmethod
    def onInitialize(self):
        pass

    @abstractmethod
    def onUpdate(self):
        pass

    @abstractmethod
    def onLateUpdate(self):
        pass
