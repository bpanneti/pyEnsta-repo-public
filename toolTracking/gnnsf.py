# -*- coding: utf-8 -*-
"""
Created on Thu Aug 15 09:51:33 2019

@author: bpanneti
"""

from toolTracking.utils import MotionModel, StateType, F, Q,Compress, clustering
from toolTracking.estimator import Estimator
from point import Position
from orientation import Orientation
import numpy as np
import toolTracking as tr
from scipy.optimize import linear_sum_assignment
    
from scipy.stats.distributions import chi2
from copy import deepcopy as deepCopy 


class gnnsf(Estimator):
    __metaclass__ = Estimator
    _parameters              = {}
    _parameters['dimension'] = 'XY'
    _parameters['algorithm'] = 'GNNSF'
    _parameters['threshold_gating'] = 0.95
    _parameters['models']    = []
    model                   = {}
    model['noise']          = 0.1
    model['type']           = 'CV'
    _parameters['models'].append(model)
    _parameters['timeWithoutPlot'] = 3.0 #
    def __init__(self, parent=None):
        super().__init__(parent)
 
     
        self.debug  = False 
        
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

        if self.parameters['dimension'] == StateType.XY:
            self.threshold          = chi2.ppf(self.parameters['threshold_gating'], df=2)     # 11.07
    def changeParameters(self,_params) :
     
           self._parameters = _params
           
           self.updateParameters()
    def clustering(self):    
     
         _plots = self.scan.plots
         #==========================================
         # construction de la matrice Omega
         #==========================================
         _Omega = []
         if len(_plots)>0 and len(self.tracks)>0:
             _Omega = np.zeros(( len(self.tracks),len(_plots)))
         else:
             return [],[],[],[]
         for j,_plot in zip(range(0,len(_plots)),_plots):
             for i,_track in zip(range(0,len(self.tracks)),self.tracks):
                 if _track.validate(_plot,self.threshold):   # ENSTA  A modifier ici pour la fusion radar optro
                     _Omega[i,j] = 1
                    
         Omega_Compress, Track_indices, Measurement_Indices = Compress(_Omega)
             
         if self.debug:     
             print(_Omega)
             print(Measurement_Indices)
             print(Track_indices)
             
         cluster = clustering(Omega_Compress)
         
         if self.debug:     
             print('debug in clustering')
             print(cluster)
             print(Track_indices)
             print(Measurement_Indices)
         return cluster,Track_indices, Measurement_Indices,_Omega
        
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
        
    def run(self):
   
        if self.scan != None:
            #=================================================
            # toutes les mesures peuvent être considérées 
            # comme des nouvelles cibles
            #=================================================
            
            unUsedDetections = list(np.copy(self.scan.plots))
            unUsedTracks     = list(np.copy(self.tracks))
            #=================================================
            # clustering des pistes aux mesures
            #=================================================
            
            
            clusters,trackIndices,measuresIndices,Omega = self.clustering()
            
            
            #=================================================
            # calcule des coûts d'association
            #=================================================
      
            if len(trackIndices)>0 and len(measuresIndices)>0:
 
                for i_c in range(0,np.size(clusters,0)):
             
                    _cluster = clusters[i_c,:]
                    #sélection des plots concernés 
            
                    _plotInCluster = measuresIndices[np.where(_cluster!=0)[0]]
                    if self.debug: 
                        print('indice des plots dans le cluster')
                        print(_plotInCluster)
                        
                    #sélection des tracks concernées   
                    _trackInCluster = []
                    for _plot in _plotInCluster:
                        _indices = np.where(Omega[:,_plot]!=0)[0]
                        for _ind in _indices:
                            if _ind not in _trackInCluster:
                                _trackInCluster.append(_ind)
                    if self.debug: 
                        print('indice des tracks dans le cluster')
                        print(_trackInCluster)
                        
                    #calcul des couts d'association   
                    if len(_trackInCluster) > 0 and len(_plotInCluster) > 0:
                        MAX_VALUE = 500
                        costMatrix = MAX_VALUE * np.ones([len(_trackInCluster), len(_plotInCluster)])
                  
                        for i,_trackIndice in zip(range(0,len(_trackInCluster)),_trackInCluster):
                            for j,_plotIndice in zip(range(0,len(_plotInCluster)),_plotInCluster):
                            #gating a déjà été fait
                                _track = self.tracks[_trackIndice]
                                _plot  = self.scan.plots[_plotIndice]
                                flag,gatingPlot = _track.gating(_plot)  # ENSTA  A modifier ici pour la fusion radar optro
                                if flag == False:
                                    costMatrix[i, j] =  MAX_VALUE
#                                    print('error for he same threshold plot is not validated')
#                                    return
                                else: 
                                    costMatrix[i, j] = gatingPlot.cost
                        
                        if self.debug: 
                            print(costMatrix)
                        # ==============
                        # Munkres
                        # ==============
                        rowInd, colInd = linear_sum_assignment(costMatrix)
                        
                        for cnt in range(0, len(rowInd)):
                            row    = rowInd[cnt]
                            column = colInd[cnt]
                            if self.debug: 
                                print(['column :', column])
                                print(['row :', row])
                                print(costMatrix[row][column])
                                print(['len plots :', len(self.scan.plots)])
                            if costMatrix[row][column] != MAX_VALUE:
                                if self.debug: 
                                    print(_trackInCluster[row])
                                    
                                _track = self.tracks[_trackInCluster[row]]
                                _plot  = self.scan.plots[_plotInCluster[column]]
                               
                                #prediction 
                                #_track.prediction(self.scan.dateTime)
                                #estimation 
                                _track.update([_plot])
                                
                                unUsedDetections.remove(_plot)
                                unUsedTracks.remove(_track)

                    
            #==================================================
            
 
            deletedTrack =[]  
            for track in unUsedTracks:
   
                if track.trackValidity(self.scan.dateTime):
             
                    track.prediction(self.scan.dateTime)
                else:
                    deletedTrack.append(track)
                
            for track in deletedTrack:
                if self.debug:
                    print(['track to delete: ', track.id])
                track.undisplay()
                self.tracks.remove(track)

            deletedTrack.clear()

            # =========================
            # initialisation
            # =========================
   
            for plot in unUsedDetections:
  
                self.initializeTrack(plot)
                if self.debug:
                    print(['initialisation d''une nouvelle track ', myTrack.id])   
            # ==========================================================
            # emission des pistes pour affichage et/ou enregistrement
            # ==========================================================
            if self.tracks != []:
                self.updatedTracks.emit(self.tracks)

            self.scan = None