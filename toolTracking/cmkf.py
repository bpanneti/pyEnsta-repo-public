# -*- coding: utf-8 -*-
"""
Created on Thu Aug 15 09:51:33 2019

@author: bpanneti
"""

from toolTracking.utils import MotionModel, StateType, F, Q
from toolTracking.estimator import Estimator
from point import Position
from orientation import Orientation
import numpy as np
import toolTracking as tr
from copy import deepcopy as deepCopy 

# def parameters():
#     global parameters
#     return parameters


 
    


class cmkf(Estimator):
    __metaclass__ = Estimator
    
    _parameters = {}
    _parameters              = {}
    _parameters['dimension'] = 'XY'# StateType.XY
    _parameters['algorithm'] = 'CMKF'
    _parameters['models']    = []
    model                   = {}
    model['noise']          = 0.1
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
 
    def updateTrack(self, plot=None, unUpdatedTrack = [],track=None):
        super().updateTrack(plot, unUpdatedTrack, track)

        track.update([plot])    
 
    def initializeTrack(self, plot):   
        super().initializeTrack(plot)
 
 
        # initialisation d'une nouvelle piste
        self.message.emit('initialize a new track with cmkf')
        self.currentTrack = tr.track.Track(_parameters = self.parameters) 
        self.currentTrack.initialize(plot)
        self.tracks.append(self.currentTrack)
        self.tracks[-1].groundTruth = plot.idTarget
 
    @staticmethod
    def predictor(currState, time, parameters, flagChange):
   
        periode                        =  currState.time.msecsTo(time)/1000
        currState.xPred                =  F(periode, currState.xEst.shape[0],  parameters['models'][0]['type'])@currState.xEst #np.matrix(np.dot(F(periode, self.state.shape[0]), self.state))
        currState.PPred                =  F(periode, currState.xEst.shape[0],  parameters['models'][0]['type'])@currState.PEst@ F(periode, currState.xEst.shape[0],parameters['models'][0]['type']).T + Q(periode,currState.xEst.shape[0],parameters['models'][0]['type'],parameters['models'][0]['noise'])
        currState.timeWithoutPlot     += periode

        if flagChange:
            currState.xEst = currState.xPred
            currState.PEst = currState.PPred

            currState.time = time

            currState.updateLocation()
            currState.updateCovariance() 
        
    @staticmethod
    def estimator(plot, currState, posCapteur=Position(), orientationCapteur=Orientation()):
  
        #print('track {} updated with plot {}'.format(currState.idTrack,plot.idTarget))
        H = np.zeros([2,4])
        H[0,0] = 1
        H[1,2] = 1

        z = np.zeros([2,1])
        z[0] = plot.z_XY[0]
        z[1] = plot.z_XY[1]
        
        R = np.zeros([2,2])
        R[0:2,0:2]    = plot.R_XY[0:2,0:2]

        In = z - np.dot(H,currState.xPred) 

        S  =  R + np.dot(H, np.dot(currState.PPred, H.T))

        K  = np.dot(currState.PPred, np.dot(H.T, np.linalg.inv(S)))
        currState.xEst          = np.array(currState.xPred + np.dot(K, In))
        currState.PEst         = np.array(np.dot(np.dot(np.identity(currState.xPred.shape[0]) - np.dot(K,H), currState.PPred), (np.identity(currState.xPred.shape[0]) - np.dot(K, H)).T) + np.dot(K, np.dot(R, K.T)))
    
        currState.location.setXYZ(float(currState.xEst[0]),float(currState.xEst[2]), 0.0, 'ENU')
        currState.updateCovariance()
        currState.likelihood    = 1/np.linalg.det(2*np.pi*S)*np.exp(-0.5*In.T @np.linalg.inv(S)@In)
   
    def run(self):

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
     
             self.scan = None
 
                  
         return
