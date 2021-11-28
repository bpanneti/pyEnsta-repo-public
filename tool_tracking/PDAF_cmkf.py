# -*- coding: utf-8 -*-
"""
Created on Thu Aug 15 09:51:33 2019

@author: bpanneti
"""

import tool_tracking.track as tr
from tool_tracking.motionModel import MotionModel
from tool_tracking.estimator import Estimator
from scan import Plot, Scan, PLOTType
import numpy as np
from scipy.optimize import linear_sum_assignment
from tool_tracking.estimator import TRACKER_TYPE
from tool_tracking.clustering import Compress, clustering
from point import Position
from orientation import Orientation
from sensor import Sensor
 
import sys

class PDAF_cmkf(Estimator):# ENSTA  A modifier ici : changement de classe
    __metaclass__ = Estimator
    
    def __init__(self, parent=None, infos=None):
        super().__init__(parent, infos)
        self.type   = TRACKER_TYPE.CMKF_PDAF  
        self.debug  = True 
    def gating(self):    
        
        _plots = self.scan.plots
        #==========================================
        # ensemble des plots validés
        #==========================================
        _plotsValides = []
     
        for j,_plot in zip(range(0,len(_plots)),_plots):
            for i,_track in zip(range(0,len(self.tracks)),self.tracks):
                if _track.validate(_plot):   #PDAF il n'y a qu'une track
                    _plotsValides.append(_plot)
                   
        return _plotsValides
    
    @staticmethod
    def  estimator(plots, currState, posCapteur=Position(), orientationCapteur=Orientation()):
 
     
        print('-----> in pdaf estimator : non-parametric version')
        if plots==[]:
            return
    
        
        H = np.zeros([2,4])
        H[0,0] = 1
        H[1,2] = 1
            
        likelihood              = np.zeros((len(plots)+1,1))
        beta                    = np.zeros((len(plots)+1,1)) 
        state                   = np.zeros((currState.xPred.shape[0],len(plots)+1))
        covariance              = np.zeros((currState.xPred.shape[0],currState.xPred.shape[0],len(plots)+1))
  
        state[:,[0]]            = currState.xPred
        covariance[:,:,0]     = currState.pPred 
        
        #Valeur par défaut
        Pd      = 0.9
        Pg      = 0.9
        Volume  = 1000
        
        b  = (1 -Pd*Pg) / Pd * len(plots)/Volume
    
        print('-----> in pdaf estimator : number of validated measures {0}'.format(len(plots)))
        
        for ind,_plot in zip(range(0,len(plots)),plots) : 
            z                           = np.zeros([2,1])
            z[0]                        = _plot.z_XY[0]
            z[1]                        = _plot.z_XY[1]     
            R                           = np.zeros([2,2])
            R[0:2,0:2]                  = _plot.R_XY[0:2,0:2]
            
            
            In                          =   z - np.dot(H,currState.xPred) 
            S                           =   R + np.dot(H, np.dot(currState.pPred, H.T))
            K                           =   np.dot(currState.pPred, np.dot(H.T, np.linalg.inv(S)))
            likelihood[ind+1]           =   In.T@np.linalg.inv(S)@In
            
            state[:,[ind+1]]            =   currState.xPred+ K@In
            covariance[:,:,ind+1]       =   np.array(np.dot(np.dot(np.identity(currState.xPred.shape[0]) - np.dot(K,H), currState.pPred), (np.identity(currState.xPred.shape[0]) - np.dot(K, H)).T) + np.dot(K, np.dot(R, K.T))) 

        
        for ind in range(0,len(plots)+1):
            if ind == 0:
                beta[ind] = b/(b+np.sum(likelihood))
            else:
                beta[ind] = likelihood[ind]/(b+np.sum(likelihood))

                #combinaison
        currState.state         = np.zeros((currState.state.shape[0],1))
        currState.covariance    = np.zeros((currState.state.shape[0],currState.state.shape[0]))
   
        for ind in range(0,len(plots)+1):
            currState.state +=  beta[ind] * state[:,[ind]]
        for ind in range(0,len(plots)+1):
            y = state[:,[ind]] - currState.state 
            currState.covariance += beta[ind]*(covariance[:,:,ind] + y@y.T)
            
        currState.location.setXYZ(float(currState.state[0]),float(currState.state[2]), 0.0, 'ENU')
        currState.updateCovariance()    
            
    def run(self):
   
        if self.scan != None:
 
            
            print('in run')
            #=================================================
            # PDAF
            #=================================================
            
            _plotsValides = self.gating()
 
            #=========================
            # Mise à jour de la piste
            #=========================
            
            if (self.tracks!=[]) :
            
                if len(_plotsValides)>0:
                    for _track in self.tracks:
                        _track.update(_plotsValides)
                elif len(_plotsValides)==0:
                    for _track in self.tracks:
                        _track.prediction(self.scan.dateTime) 
            
            # =========================
            # initialisation
            # =========================
   
            if (self.tracks==[]):
              for plot in self.scan.plots:
                if( self.isTracked(plot.idTarget)): #uniquement pour l'initialisation
                    myTrack =  tr.Track(TRACKER_TYPE.CMKF_PDAF)    
                    myTrack.initialize([plot], self.scan.dateTime, 0, 0, 0, [], [], [
                                   MotionModel.CV, 1])          
                    self.tracks.append(myTrack)
                    if self.debug:
                        print(['initialisation d''une nouvelle track ', myTrack.id])   
            # ==========================================================
            # emission des pistes pour affichage et/ou enregistrement
            # ==========================================================
            if self.tracks != []:
                self.updatedTracks.emit(self.tracks)

            self.scan = None
