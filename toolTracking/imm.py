#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov  5 10:27:33 2022

@author: benjamin
"""


from toolTracking.utils import MotionModel, StateType, F, Q
from toolTracking.estimator import Estimator
from point import Position
from orientation import Orientation
import numpy as np
import toolTracking as tr
from copy import deepcopy as deepCopy 

class imm(Estimator):
    __metaclass__ = Estimator
    _parameters = {}
    _parameters              = {}
    _parameters['dimension'] = 'XY'# StateType.XY
    _parameters['algorithm'] = 'IMM'
    _parameters['models']    = []
    model                   = {}
    model['noise']          = 0.1
    model['type']           = 'CV' # MotionModel.CV
    model['proba']          = 0.8
    model['Ptransition_vector'] = [0.8,0.2] 
    _parameters['models'].append(model)    
    model2                  = {}
    model2['noise']         = 2
    model2['type']          = 'CV' # MotionModel.CV
    model2['proba']         = 0.2
    model2['Ptransition_vector'] = [0.3,0.7] 
    _parameters['models'].append(model2)      
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
                if 'Ptransition_vector' in self.parameters['models'][_mod]:
                    
                    self.parameters['models'][_mod]['Ptransition_vector'] = np.array(self.parameters['models'][_mod]['Ptransition_vector'])
                    
                if _type.name == self.parameters['models'][_mod]['type']:
                    self.parameters['models'][_mod]['type'] = _type

    def changeParameters(self,_params) :

       self._parameters = _params
       
       self.updateParameters()
    def initializeTrack(self, plot):

        # initialisation d'une nouvelle piste
        self.message.emit('initialize a new track with imm')
        self.currentTrack = tr.track.Track(_parameters = self.parameters) 
        self.currentTrack.initialize(plot)
        self.tracks.append(self.currentTrack)
        self.tracks[-1].groundTruth = plot.idTarget


    def updateTrack(self, plot, unUpdatedTrack, track):
        super().updateTrack(plot, unUpdatedTrack, track)

        track.update([plot])

    @staticmethod
    def predictor(currState, time , parameters, flagChange):
        periode                        =  currState.time.msecsTo(time)/1000
        
        #etat estime précédent pour le modele i : currState.stateModel[:,[i]]
        #covarianece estimee précédente  pour le modele i :currState.covarianceModel[:,:, i ]
        #===============================================
        # Mixage 
        #===============================================
        xs = np.zeros((currState.xEst.shape[0],len(parameters['models'])))
        Ps = np.zeros((currState.xEst.shape[0],currState.xEst.shape[0],len(parameters['models'])))
        
      
 
        for ind,  fil in enumerate( parameters['models']):
            x = np.zeros((currState.xEst.shape[0],1))
            for ind2,  fil2 in enumerate( parameters['models'] ):
                x +=  currState.xModel[:,[ind2]]*currState.Mu_mixed[ind2,ind]
            xs[:,[ind]] = x
            
            P = np.zeros((currState.xEst.shape[0],currState.xEst.shape[0]))
            for ind2,  fil2 in enumerate( parameters['models']):
                y = currState.xModel[:,[ind2]] - x
                P += currState.Mu_mixed[ind2,ind] * (np.outer(y, y) + currState.pModel[:,:, ind2 ])
            Ps[:,:,ind] = P
    
        #===============================================
        # Prediction 
        #===============================================      
        
        for ind,model in enumerate(parameters['models']): 
            currState.xPredModel[:, [ind]] =  F(periode, currState.xEst.shape[0], model['type'])@xs[:,[ind]] #np.matrix(np.dot(F(periode, self.state.shape[0]), self.state)) 
            currState.pPredModel[:,:, ind ] =  F(periode, currState.xEst.shape[0], model['type'])@Ps[:,:, ind ] @ F(periode, currState.xEst.shape[0],model['type']).T + Q(periode,currState.xEst.shape[0],model['type'],model['noise']) 
   
        currState.timeWithoutPlot     += periode

        currState.xPred      = np.zeros((currState.xEst.shape[0],1))
        currState.PPred      = np.zeros((currState.xEst.shape[0],currState.xEst.shape[0]))
        
        for ind,model in enumerate(parameters['models']):
            currState.xPred+= currState.Mu[ind]*currState.xPredModel[:,[ind]]
                 
        for ind,model in enumerate(parameters['models']):         
            y = currState.xPredModel[:, [ind]] - currState.xPred
            currState.PPred  += currState.Mu[ind]* (np.outer(y, y) + currState.pPredModel[:,:, ind ])
                
        if flagChange:
            
#            print('---> in prediction')
#            print('================')
#            print(currState.pPredModel[:,:, 0 ])
#            print('================')
#            print(currState.pPredModel[:,:, 1 ])
#            print('================')
#            print(currState.pPred)
#            print('================')
            currState.xEst       = currState.xPred
            currState.PEst       = currState.PPred

 
            currState.time = time

            currState.updateLocation()
            currState.updateCovariance() 
        
    @staticmethod
    def estimator(plot, currState, posCapteur=Position(), orientationCapteur=Orientation(),parameters = None):
  
        H = np.zeros([2,4])
        H[0,0] = 1
        H[1,2] = 1

        z = np.zeros([2,1])
        z[0] = plot.z_XY[0]
        z[1] = plot.z_XY[1]
        
        R = np.zeros([2,2])

        R[0:2,0:2]    = plot.R_XY[0:2,0:2]
      
        #print('-----> in estimator')
        likelihood = np.zeros((len(parameters['models']),1))
        for ind,model in enumerate(parameters['models']):
            In = z - np.dot(H,currState.xPredModel[:,[ind]]) 

            #S  =  R + H@currState.pPredModel[:,:, ind ]@ H.T
            S  =  R + np.dot(H, np.dot(currState.pPredModel[:,:, ind ], H.T))
            #K  = currState.pPredModel[:,:,ind]@ H.T@ np.linalg.inv(S)
            K  = np.dot(currState.pPredModel[:,:,ind], np.dot(H.T, np.linalg.inv(S)))
            likelihood[ind] = In.T@np.linalg.inv(S)@In
            
            currState.xModel[:,[ind]] = currState.xPredModel[:,[ind]] + K@In

            currState.pModel[:,:,ind] = (np.identity(currState.xPredModel[:,[ind]].shape[0]) - K@H)@currState.pPredModel[:,:,ind]@(np.identity(currState.xPredModel[:,[ind]].shape[0]) - K@H).T + K@R@K.T

        #mise à jour des probabilités
      


        currState.Mu = currState.cbar *  likelihood
        currState.Mu /= np.sum(currState.Mu)

        currState.computeMixingProbabilities()

 
    
        #combinaison
        currState.xEst          = np.zeros((currState.xEst.shape[0],1))
        currState.PEst          = np.zeros((currState.xEst.shape[0],currState.xEst.shape[0]))
   
        for ind,model in enumerate(parameters['models']):
            currState.xEst += currState.Mu[ind] * currState.xModel[:,[ind]]
        for ind,model in enumerate(parameters['models']):
            y = currState.xModel[:,[ind]] - currState.xEst 
            currState.PEst += currState.Mu[ind]*(currState.pModel[:,:,ind] + y@y.T)

#        print(likelihood)
#        print(currState.state)
#        print(currState.covariance)
#     
        currState.location.setXYZ(float(currState.xEst[0]),float(currState.xEst[2]), 0.0, 'ENU')
        currState.updateCovariance()
        for ind,model in enumerate(parameters['models']): 
            currState.likelihood += currState.Mu[ind]*likelihood[ind] 
        
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