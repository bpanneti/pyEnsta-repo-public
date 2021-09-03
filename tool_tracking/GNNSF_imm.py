# -*- coding: utf-8 -*-
"""
Created on Thu Aug 15 09:51:33 2019

@author: rGomesCardoso & rYune
"""

import tool_tracking as tr
from tool_tracking.motionModel import MotionModel
from tool_tracking.estimator import Estimator
import numpy as np
from scipy.optimize import linear_sum_assignment
from tool_tracking.estimator import TRACKER_TYPE
from tool_tracking.clustering import Compress, clustering

import sys

class GNNSF_imm(Estimator):
    __metaclass__ = Estimator
    
    def __init__(self, parent=None, infos=None):
        super().__init__(parent, infos)
        self.type   = TRACKER_TYPE.IMM_GNNSF
        self.debug  = False 
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
                if _track.validate(_plot):
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
                                flag,gatingPlot = _track.gating(_plot)
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
                               
                                
#                                if _track.taillePiste() == 1 :
#                                    # correction de l'état initial
#                                    _track.update([_plot])
#                             
#                                else:
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
  
                myTrack = tr.track.Track(TRACKER_TYPE.IMM)
                Mu = np.array([0.9, 0.1])
                PTransition = np.array([[0.95, 0.05], [0.05, 0.95]])
    
                filter1 = [MotionModel.CV, 0.1,Mu[0],PTransition[0,:]]
                filter2 = [MotionModel.CV, 2  ,Mu[1],PTransition[1,:]]
    
                filters = [filter1, filter2]
    
                myTrack.initialize([plot], self.scan.dateTime, 0, 0, 0, Mu, PTransition, filters)
                self.tracks.append(myTrack)
                if self.debug:
                    print(['initialisation d''une nouvelle track ', myTrack.id])   
            # ==========================================================
            # emission des pistes pour affichage et/ou enregistrement
            # ==========================================================
            if self.tracks != []:
                self.updatedTracks.emit(self.tracks)

            self.scan = None
