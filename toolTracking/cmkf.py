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

 
    


class cmkf(Estimator):
    __metaclass__ = Estimator

    def __init__(self, parent=None):
        super().__init__(parent)
 
        self.parameters              = {}
        self.parameters['dimension'] = StateType.XY
        self.parameters['algorithm'] = 'CMKF'
        self.parameters['models']    = []
        model                   = {}
        model['noise']          = 0.1
        model['type']           = MotionModel.CV
        self.parameters['models'].append(model)
        
        

        
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
        currState.xPred                #---- >  =
        currState.pPred                #---- >  =

        if flagChange:
            currState.xEst = currState.xPred
            currState.PEst = currState.pPred

            currState.time = time

            currState.updateLocation()
            currState.updateCovariance() 
        
    @staticmethod
    def estimator(plot, currState, posCapteur=Position(), orientationCapteur=Orientation()):
  
        #---- > estimation du cmkf
        H = np.zeros([2,4])
        H[0,0] = 1
        H[1,2] = 1

        z = np.zeros([2,1])
        z[0] = plot.z_XY[0]
        z[1] = plot.z_XY[1]
        
        #----> 
        #----> currState.location.setXYZ(float(currState.xEst[0]),float(currState.xEst[2]), 0.0, 'ENU')
        #----> currState.updateCovariance()
        #----> currState.likelihood    =  
   
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