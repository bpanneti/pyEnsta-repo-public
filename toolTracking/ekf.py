# -*- coding: utf-8 -*-
"""
Created on Thu Aug 15 09:51:33 2019

@author: bpanneti
"""

 
from toolTracking.utils import MotionModel, StateType, F, Q, h
from point import Position
from toolTracking.estimator import Estimator
from orientation import Orientation
import toolTracking as tr
 
import numpy as np
from copy import deepcopy as deepCopy 
class ekf(Estimator):
    __metaclass__ = Estimator
    _parameters = {}
    _parameters              = {}
    _parameters['dimension'] = 'XY'# StateType.XY
    _parameters['algorithm'] = 'EKF'
    _parameters['models']    = []
    model                   = {}
    model['noise']          = 1
    model['type']           = 'CV' # MotionModel.CV
    _parameters['models'].append(model)    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.updateParameters()
        
    def updateParameters(self):

         self.parameters = deepCopy(self._parameters)
         
         for _dim in StateType:
             if _dim.name == self.parameters['dimension'] :
                 
                 self.parameters['dimension'] = _dim
         for _mod in range(len(self.parameters['models'])):
             for _type in MotionModel:
                 if _type.name == self.parameters['models'][_mod]['type']:
                     self.parameters['models'][_mod]['type'] = _type
    def changeParameters(self,_params) :
   
         self._parameters = _params
         
         self.updateParameters()
    def initializeTrack(self, plot):
        super().initializeTrack(plot)

        # initialisation d'une nouvelle piste
        self.message.emit('initialize a new track with ekf')
        self.currentTrack = tr.track.Track(_parameters = self.parameters) 
        self.currentTrack.initialize(plot)
        self.tracks.append(self.currentTrack)
        self.tracks[-1].groundTruth = plot.idTarget
        
    def updateTrack(self, plot, unUpdatedTrack, track):
        super().updateTrack(plot, unUpdatedTrack, track)
 
        track.update([plot],self.scan.sensorPosition,self.scan.sensorOrientation )
    @staticmethod
    def predictor(currState, time , parameters,flagChange):
       periode                        =  currState.time.msecsTo(time)/1000
 
       currState.xPred                =  F(periode, currState.xEst.shape[0],  parameters['models'][0]['type'])@currState.xEst #np.matrix(np.dot(F(periode, self.state.shape[0]), self.state))
       currState.PPred                =  F(periode, currState.xEst.shape[0],  parameters['models'][0]['type'])@currState.PEst@ F(periode, currState.xEst.shape[0],parameters['models'][0]['type']).T + Q(periode,currState.xEst.shape[0],parameters['models'][0]['type'],parameters['models'][0]['noise'])
       currState.timeWithoutPlot     += periode

       if flagChange:
            currState.state = currState.xPred
            currState.covariance = currState.PPred

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

        #----> TODO ENSTA H[0,0] = 
        # H[0,2] =  
        # H[1,0] =  
        # H[1,2] = 
        
        S  =  R + np.dot(H, np.dot(currState.PPred, H.T)) 
        K  = np.dot(currState.PPred, np.dot(H.T, np.linalg.inv(S)))
        
        currState.xEst = currState.xPred + K@In 

        currState.PEst = np.dot(np.dot(np.identity(currState.xPred.shape[0]) - np.dot(K,H),currState.PPred), (np.identity(currState.xPred.shape[0]) - np.dot(K,H)).T) + np.dot(K,np.dot(R, K.T))

        currState.location.setXYZ(float(currState.xEst[0]), float(currState.xEst[2]),0.0, 'ENU')
        currState.updateCovariance()
        currState.likelihood = 1/np.linalg.det(2*np.pi*S)*np.exp(-0.5*np.transpose(In)@np.linalg.inv(S)@In)
   
    def run(self):

 
#        if self.mutex.tryLock()==False:
#            return 
        if self.scan != None and self.scan !=[]:
 
            unUpdatedTrack = self.copyTracks()
            
            for plot in self.scan.plots:
                if self.isTracked(plot.idTarget):
                    track = self.searchTrack(plot.idTarget)
    
                    if track == None:
                        self.initializeTrack(plot)
                    else:
                        self.updateTrack(plot, unUpdatedTrack, track)
    
            for track in unUpdatedTrack:
                track.prediction(self.scan.dateTime)
    
#            if self.tracks != None:
#                self.updatedTracks.emit(self.tracks)
               
            self.scan = None
        #self.mutex.unlock()
        return
