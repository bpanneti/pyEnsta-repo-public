# -*- coding: utf-8 -*-
"""
Created on Thu Aug 15 09:51:33 2019

@author: bpanneti
"""

 
from tool_tracking.motionModel import MotionModel, StateType, F, Q, h
from tool_tracking.estimator import Estimator, TRACKER_TYPE
from point import Position
from orientation import Orientation

import tool_tracking as tr
import numpy as np

class ekf(Estimator):
    __metaclass__ = Estimator

    def __init__(self, parent=None, infos=None):
        super().__init__(parent, infos)
        self.type = TRACKER_TYPE.EKF

    def initializeTrack(self, plot):
        super().initializeTrack(plot)

        self.myTrack.initialize([plot], self.scan.dateTime, 0, 0, 0, [], [], [MotionModel.CV, 1])
        self.tracks.append(self.myTrack)

    def updateTrack(self, plot, unUpdatedTrack, track):
        super().updateTrack(plot, unUpdatedTrack, track)

        track.update([plot], self.scan.sensor.node.Position, self.scan.sensor.node.Orientation)
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
    def estimator(plot, currState, posCapteur, orientationCapteur):
        z = np.zeros([2, 1])
        z[0] = plot.rho
        z[1] = np.mod(np.pi/2 - orientationCapteur.yaw * np.pi/180  -  plot.theta * np.pi/180 + np.pi, 2*np.pi) - np.pi

        In = z - h(currState.xPred[0] - posCapteur.x_ENU, currState.xPred[2] - posCapteur.y_ENU)

        R = np.diag([plot.sigma_rho**2, (plot.sigma_theta * np.pi/180)**2])
        H = np.zeros([2, 4])   
        distance2 = np.power(currState.xPred[0] - posCapteur.x_ENU, 2.0) + np.power(currState.xPred[2] - posCapteur.y_ENU, 2.0)

        H[0,0] = (currState.xPred[0] - posCapteur.x_ENU) / np.sqrt(distance2)
        H[0,2] = (currState.xPred[2] - posCapteur.y_ENU) / np.sqrt(distance2)
        H[1,0] = -(currState.xPred[2] - posCapteur.y_ENU) / distance2
        H[1,2] =  (currState.xPred[0] - posCapteur.x_ENU) / distance2
        
        S  =  R + np.dot(H, np.dot(currState.pPred, H.T)) 
        K  = np.dot(currState.pPred, np.dot(H.T, np.linalg.inv(S)))
        
        currState.state = currState.xPred + K@In 

        currState.covariance = np.dot(np.dot(np.identity(currState.xPred.shape[0]) - np.dot(K,H),currState.pPred), (np.identity(currState.xPred.shape[0]) - np.dot(K,H)).T) + np.dot(K,np.dot(R, K.T))

        currState.location.setXYZ(float(currState.state[0]), float(currState.state[2]),0.0, 'ENU')
        currState.updateCovariance()
