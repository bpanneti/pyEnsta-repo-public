# -*- coding: utf-8 -*-
"""
Created on Mon Nov 25 10:42:45 2019

@author: bpanneti
"""
import tool_tracking as tr
from tool_tracking.estimator import Estimator, TRACKER_TYPE
from tool_tracking.motionModel import MotionModel, StateType, F, Q
import numpy as np
from point import Position
from orientation import Orientation

class imm(Estimator):
    __metaclass__ = Estimator

    def __init__(self, parent=None, infos=None):
        super().__init__(parent, infos)
        self.type = TRACKER_TYPE.IMM

    def initializeTrack(self, plot):
        super().initializeTrack(plot)

        # initialisation de l'IMM
        Mu = np.array([0.9, 0.1])
        PTransition = np.array([[0.95, 0.05], [0.05, 0.95]])

        filter1 = [MotionModel.CV, 0.1,Mu[0],PTransition[0,:]]
        filter2 = [MotionModel.CV, 2  ,Mu[1],PTransition[1,:]]

        filters = [filter1, filter2]

        self.myTrack.initialize([plot], self.scan.dateTime, 0, 0, 0, Mu, PTransition, filters)
        self.tracks.append(self.myTrack)

    def updateTrack(self, plot, unUpdatedTrack, track):
        super().updateTrack(plot, unUpdatedTrack, track)

        track.update([plot])
    @staticmethod
    def predictor(currState, time , flagChange):
        periode                        =  currState.time.msecsTo(time)/1000
        
        #===============================================
        # Mixage 
        #===============================================
        xs = np.zeros((currState.state.shape[0],len(currState.filter)))
        Ps = np.zeros((currState.state.shape[0],currState.state.shape[0],len(currState.filter)))
        
        for ind,  fil in enumerate( currState.filter ):
            x = np.zeros((currState.state.shape[0],1))
            for ind2,  fil2 in enumerate( currState.filter ):
                x +=  currState.stateModel[:,[ind2]]*currState.Mu_mixed[ind2,ind]
            xs[:,[ind]] = x
            
            P = np.zeros((currState.state.shape[0],currState.state.shape[0]))
            for ind2,  fil2 in enumerate( currState.filter ):
                y = currState.stateModel[:,[ind2]] - x
                P += currState.Mu_mixed[ind2,ind] * (np.outer(y, y) + currState.covarianceModel[:,:, ind2 ])
            Ps[:,:,ind] = P
    
        #===============================================
        # Prediction 
        #===============================================      
        
        for ind,model in enumerate(currState.filter): 
            currState.xPredModel[:, [ind]]  =  F(periode, currState.state.shape[0], model[0])@xs[:,[ind]] #np.matrix(np.dot(F(periode, self.state.shape[0]), self.state)) 
            currState.pPredModel[:,:, ind ] =  F(periode, currState.state.shape[0], model[0])@Ps[:,:, ind ] @ F(periode, currState.state.shape[0],model[0]).T + Q(periode,currState.state.shape[0],model[0],model[1]) 
   
        currState.timeWithoutPlot     += periode

        currState.xPred      = np.zeros((currState.state.shape[0],1))
        currState.pPred      = np.zeros((currState.state.shape[0],currState.state.shape[0]))
        for ind,model in enumerate(currState.filter):
                 currState.xPred+= currState.Mu[ind]*currState.xPredModel[:,[ind]]
                 
        for ind,model in enumerate(currState.filter):         
                y = currState.xPredModel[:, [ind]] - currState.xPred
                currState.pPred  += currState.Mu[ind]* (np.outer(y, y) + currState.pPredModel[:,:, ind ])
                
        if flagChange:
            
#            print('---> in prediction')
#            print('================')
#            print(currState.pPredModel[:,:, 0 ])
#            print('================')
#            print(currState.pPredModel[:,:, 1 ])
#            print('================')
#            print(currState.pPred)
#            print('================')
            currState.state       = currState.xPred
            currState.covariance  = currState.pPred

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
        R[0:1,0:1]    = plot.R_XY[0:1,0:1]

        likelihood = np.zeros((len(currState.filter),1))
        for ind,model in enumerate(currState.filter):
            In = z - np.dot(H,currState.xPredModel[:,[ind]]) 

            S  =  R + H@currState.pPredModel[:,:, ind ]@ H.T

            K  = currState.pPredModel[:,:,ind]@ H.T@ np.linalg.inv(S)
            
            likelihood[ind]= In.T@np.linalg.inv(S)@In
            
            currState.stateModel[:,[ind]]       =   currState.xPredModel[:,[ind]] +  K@ In
            currState.covarianceModel[:,:,ind]    =   (np.identity(currState.xPred.shape[0]) - K@H)@ currState.pPredModel[:,:,ind]@ (np.identity(currState.xPred.shape[0]) - K@ H).T + K@R@K.T
    
                   
        #mise à jour des probabilités
      
        currState.Mu = currState.cbar *  likelihood
        currState.Mu /= np.sum(currState.Mu)  # normalize
        currState.computeMixingProbabilities()
         
       
     
        #combinaison
        currState.state         = np.zeros((currState.state.shape[0],1))
        currState.covariance    = np.zeros((currState.state.shape[0],currState.state.shape[0]))
   
        for ind,model in enumerate(currState.filter):
            currState.state          +=  currState.Mu[ind]*currState.stateModel[:,[ind]]
        for ind,model in enumerate(currState.filter):
            y = currState.stateModel[:,[ind]] - currState.state 
            currState.covariance     += currState.Mu[ind]* (np.outer(y, y) + currState.covarianceModel[:,:, ind ])
         
     
     
        currState.location.setXYZ(float(currState.state[0]),float(currState.state[2]), 0.0, 'ENU')
        currState.updateCovariance()