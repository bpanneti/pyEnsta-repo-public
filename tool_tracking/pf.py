# -*- coding: utf-8 -*-
"""
Created on Tue Apr 14 14:03:35 2020

@author: bpanneti
"""
from tool_tracking.motionModel import MotionModel
from tool_tracking.estimator import Estimator, TRACKER_TYPE
import tool_tracking as tr 

from point import Position
from orientation import Orientation
import numpy as np

class pf(Estimator):
    __metaclass__ = Estimator

    def __init__(self, parent=None, infos=None):
        super().__init__(parent, infos)
        self.type = TRACKER_TYPE.KPF

    def initializeTrack(self, plot):
        super().initializeTrack(plot)

        self.myTrack.initialize([plot], self.scan.dateTime, 0, 0, 0, [], [], [MotionModel.CV, 1])
        self.tracks.append(self.myTrack)

    def updateTrack(self, plot, unUpdatedTrack, track):
        super().updateTrack(plot, unUpdatedTrack, track)

        track.update([plot])

    @staticmethod
    def estimator(plot, currState, posCapteur=Position(), orientationCapteur=Orientation()):
        H = np.zeros([2,4])
        H[0,0] = 1
        H[1,2] = 1

        z = np.zeros([2,1])
        z[0] = plot.z_XY[0]
        z[1] = plot.z_XY[1]
        
        R = np.zeros([2,2])
        R[0:1,0:1]    = plot.R_XY[0:1,0:1]

        In = z - np.dot(H,currState.xPred) 

        S  =  R + np.dot(H, np.dot(currState.pPred, H.T))

        K  = np.dot(currState.pPred, np.dot(H.T, np.linalg.inv(S)))
        currState.state          = np.array(currState.xPred + np.dot(K, In))
        currState.covariance     = np.array(np.dot(np.dot(np.identity(currState.xPred.shape[0]) - np.dot(K,H), currState.pPred), (np.identity(currState.xPred.shape[0]) - np.dot(K, H)).T) + np.dot(K, np.dot(R, K.T)))
    
        currState.location.setXYZ(float(currState.state[0]),float(currState.state[2]), 0.0, 'ENU')
        currState.updateCovariance()