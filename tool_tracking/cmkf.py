# -*- coding: utf-8 -*-
"""
Created on Thu Aug 15 09:51:33 2019

@author: bpanneti
"""

from tool_tracking.motionModel import MotionModel, StateType, F, Q
from tool_tracking.estimator import Estimator, TRACKER_TYPE
import tool_tracking as tr 

from point import Position
from orientation import Orientation
import numpy as np

 

class cmkf(Estimator):
    __metaclass__ = Estimator

    def __init__(self, parent=None, infos=None):
        super().__init__(parent, infos)
        self.type = TRACKER_TYPE.CMKF

    def initializeTrack(self, plot):
        super().initializeTrack(plot)

        self.myTrack.initialize([plot], self.scan.dateTime, 0, 0, 0, [], [], [MotionModel.CV, 1])
        self.tracks.append(self.myTrack)
        
    def updateTrack(self, plot, unUpdatedTrack, track):
        super().updateTrack(plot, unUpdatedTrack, track)

        track.update([plot])
        
    @staticmethod
    def predictor(currState, time , flagChange):
        periode                        =  currState.time.msecsTo(time)/1000
     
        currState.xPred                =  F(periode, currState.state.shape[0], currState.filter[0])@currState.state #np.matrix(np.dot(F(periode, self.state.shape[0]), self.state))
        currState.pPred                =  F(periode, currState.state.shape[0], currState.filter[0])@currState.covariance@ F(periode, currState.state.shape[0],currState.filter[0]).T + Q(periode,currState.state.shape[0],currState.filter[0],currState.filter[1])
        currState.timeWithoutPlot     += periode

        if flagChange:
            currState.state = currState.xPred
            currState.covariance = currState.pPred

            currState.time = time

            currState.updateLocation()
            currState.updateCovariance() 
        
    @staticmethod
    def estimator(plot, currState, posCapteur=Position(), orientationCapteur=Orientation()):
  
        H = np.zeros([2,4])
        H[0,0] = 1
        H[1,2] = 1

        z = np.zeros([2,1])
        z[0] = plot.z_XY[0]
        z[1] = plot.z_XY[1]
        
        R = np.zeros([2,2])
        R[0:2,0:2]    = plot.R_XY[0:2,0:2]

        In = z - np.dot(H,currState.xPred) 

        S  =  R + np.dot(H, np.dot(currState.pPred, H.T))

        K  = np.dot(currState.pPred, np.dot(H.T, np.linalg.inv(S)))
        currState.state          = np.array(currState.xPred + np.dot(K, In))
        currState.covariance     = np.array(np.dot(np.dot(np.identity(currState.xPred.shape[0]) - np.dot(K,H), currState.pPred), (np.identity(currState.xPred.shape[0]) - np.dot(K, H)).T) + np.dot(K, np.dot(R, K.T)))
    
        currState.location.setXYZ(float(currState.state[0]),float(currState.state[2]), 0.0, 'ENU')
        currState.updateCovariance()