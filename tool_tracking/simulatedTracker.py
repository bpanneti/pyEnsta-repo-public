# -*- coding: utf-8 -*-
"""
Created on Thu Sep  2 14:39:35 2021

@author: benja
"""



from tool_tracking.estimator import Estimator, TRACKER_TYPE
from point import Position
from orientation import Orientation

import tool_tracking as tr
import numpy as np

class SIMU_tracker(Estimator):
    __metaclass__ = Estimator

    def __init__(self, parent=None, infos=None):
        super().__init__(parent, infos)
        self.type = TRACKER_TYPE.SIMU_tracker

    def initializeTrack(self, plot):
        pass

    def updateTrack(self, plot, unUpdatedTrack, track):
        super().updateTrack(plot, unUpdatedTrack, track)

        track.update([plot], self.scan.sensor.node.Position, self.scan.sensor.node.Orientation)
    @staticmethod
    def predictor(currState, time , flagChange):
         pass   
    @staticmethod
    def estimator(plot, currState, posCapteur, orientationCapteur):
         pass