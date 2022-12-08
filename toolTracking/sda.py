# -*- coding: utf-8 -*-
"""
Created on Thu Aug 15 09:51:33 2019

@author: bpanneti
"""

from toolTracking.utils import MotionModel, StateType, F, Q,Compress, clustering, TrackState
from toolTracking.estimator import Estimator
from point import Position
from orientation import Orientation
import numpy as np
import toolTracking as tr
from scipy.optimize import linear_sum_assignment
    
from scipy.stats.distributions import chi2
from copy import deepcopy as deepCopy 

class sda(Estimator):
    __metaclass__ = Estimator
    _parameters              = {}
    _parameters['dimension'] = 'XY'
    _parameters['algorithm'] = 'SDA'
    _parameters['threshold_gating'] = 0.95
    _parameters['models']    = []
    model                   = {}
    model['noise']          = 0.1
    model['type']           = 'CV'
    _parameters['models'].append(model)
    _parameters['timeWithoutPlot']          = 3.0 #duree de vie tolérée d'une piste sans plot
    _parameters['S-Dimensional']            = 2   #S-Dimensionnal
    _parameters['trackLifeConfirmation']    = 4   #durée nécessaire avant que la piste soit confirmée
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parameters = deepCopy(self._parameters)
        
        for _dim in StateType:
            if _dim.name == self.parameters['dimension'] :
                
                self.parameters['dimension'] = _dim
        for _mod in range(len(self.parameters['models'])):
            for _type in MotionModel:
                if _type.name == self.parameters['models'][_mod]['type']:
                    self.parameters['models'][_mod]['type'] = _type
 

        self.debug                          = False 
        self.threshold                      = 14
        self.updateParameters()
    def changeParameters(self,_params) :
 
       self._parameters = _params
       
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
           
        if self.parameters['dimension'] == StateType.XY:
            self.threshold          = chi2.ppf(self.parameters['threshold_gating'], df=2)     # 11.07
    

    
     
    def updateTrack(self, plot=None, unUpdatedTrack = [],track=None):
        super().updateTrack(plot, unUpdatedTrack, track)

        track.update([plot])  
    def clusteringStep(self,_plots=[]):    
 
        
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
               
               if _track.validate(_plot,self.threshold ):  
                   _Omega[i,j] = 1
        
       Omega_Compress, Track_indices, Measurement_Indices = Compress(_Omega)
       
       cluster = clustering(Omega_Compress)
       
       return cluster,Track_indices, Measurement_Indices,_Omega     
    def estimationStep(self):
            
            from toolTracking.tree import Tree 
            _plots = self.scan.plots
            # print("plots", _plots)
            unUsedDetections = list(np.copy(_plots))
        
            clusters,trackIndices,measuresIndices,Omega = self.clusteringStep(_plots)

            if len(self.tracks)>0 and len(_plots)>0:

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
                        
                        # ==============
                        # Munkres
                        # ==============
                        MAX_VALUE  = 500
                        costMatrix = MAX_VALUE * np.ones([len(_trackInCluster), len(_plotInCluster)])                
                     
                        for i,_trackIndice in zip(range(0,len(_trackInCluster)),_trackInCluster):
                                _track = self.tracks[_trackIndice]                            
                                currentStates = []           
                                _track.tree.getChilds(currentStates)
                                
                                for cState in currentStates:
                                    #test association
                                    for j,_plotIndice in zip(range(0,len(_plotInCluster)),_plotInCluster):
                                        _plot  = _plots[_plotIndice]
                                        
                                        flag,gatingPlot                 = cState.data.gating(_plot,self.threshold )  # ENSTA  A modifier ici pour la fusion radar optro
                                
                                        #flageFeature,gatingFeature      = cState.gatingFeature(_plot,self.thresholdFeature,self._featuresDistance)  
                                
                                    
                                        if flag==True :#and flageFeature==True:
                                            #association ok
                                            #print('----->')
                                            estate = tr.state.State.copyState(cState.data)
                                       
                                            cState.addChild(Tree(data=estate,markToDelete=True))
                                            #estate.prediction(dateTime)
                                            estate.estimation([_plot], self.scan.sensorPosition,self.scan.sensorOrientation)
                                    
 
                                           
                                            # print(estate.id)
                                            # print(_plot.id)
                                            #costMatrix[i,j] = estate.likelihood
                                    #cas aucune association
                                    
                                    if  True:#_track.trackState == TrackState.Confirmed :
                                             estate = tr.state.State.copyState(cState.data)
                                             estate.plot = None
                                             
                                             cState.addChild(Tree(data=estate,markToDelete=True))
                                             
                                             estate.prediction(self.scan.dateTime)
                                             #estate.estimation(None)
                                             
                                                                                         
                                         # print('########')
                                         # print(estate.id)
                        # print('================================================')
                        # print('end updated step track :',self.parameters['S-Dimensional'] )
                        # print('================================================')
                        # for i,_trackIndice in zip(range(0,len(_trackInCluster)),_trackInCluster):
                        #     _track = self.tracks[_trackIndice]  
                        #     #_track.showTree()
                        #     _track.showTree(self.parameters['S-Dimensional'] )
                        #============================================================
                        #construction de la matrice d'association et des tuples
                        #============================================================
                        
                        #list of tuple possibilities

                        U = np.array(-1*np.ones((1,self.parameters['S-Dimensional'] )))
              

                        for i,_trackIndice in zip(range(0,len(_trackInCluster)),_trackInCluster):
                                _track = self.tracks[_trackIndice]    
                                U = _track.getSDMeasurements(self.parameters['S-Dimensional'] ,U)
                      
      
                        #print('liste des tuples de mesures')
                        U = U[1:,:]
                        #print(U)
                        
                        #============================================================
                        #Compute LLR on SD side
                        #============================================================
                        
                        for i,_trackIndice in zip(range(0,len(_trackInCluster)),_trackInCluster):
                                _track = self.tracks[_trackIndice]  
                                _track.computeLLR(self.parameters['S-Dimensional'] )
                        _pp = []
                        for i,_trackIndice in zip(range(0,len(_trackInCluster)),_trackInCluster):   
                                _track = self.tracks[_trackIndice] 
                                _pp.append(_track.id)
                                #_track.showTree(self.parameters['S-Dimensional'] )
                                #_track.showGlobalTree()
                        #print("tracksin cluster")
                        #print(_pp)    
                        #print('fin')
                        #print("cost Matrix")
                        #print(costMatrix)
                        
                        costMatrix = MAX_VALUE * np.ones([len(_trackInCluster), np.shape(U)[0]])     
                        for i,_trackIndice in zip(range(0,len(_trackInCluster)),_trackInCluster):
                                _track = self.tracks[_trackIndice]   
                                currentStates = []           
                                _track.tree.getChilds(currentStates)
                                
                                for t in range(0,np.shape(U)[0]):
                                    
                                    cState = _track.findHypothesis(U[t,:])
                                    if cState!=None:
                                        costMatrix[i,t] = - cState.data.LLR
                                        
                        
                        # print('fin de calcul des coûts pour tous les tuples')
                              
                        # print(costMatrix)
                        
                        # print('fin')
                                    
             
                        
                        if self.debug:
                            print(costMatrix)
                   
                        rowInd, colInd = linear_sum_assignment(costMatrix)
                        for cnt in range(0, len(rowInd)):
                            row    = rowInd[cnt]
                            column = colInd[cnt]
                            _tuplePlots = U[column,:]
                          
                            for j,_plotIndice in zip(range(0,len(_plotInCluster)),_plotInCluster):
                                if _plots[_plotIndice].id==_tuplePlots[-1]:
                                    _plot = _plots[_plotIndice]
                                    
                            if   costMatrix[row][column] != MAX_VALUE:
         
                                self.tracks[_trackInCluster[row]].maintainHypothesis(_tuplePlots)
                                
                                if _plot in unUsedDetections:
                                    unUsedDetections.remove(_plot)

                            #self.tracks[_trackInCluster[row]].removeHypothesis(None)

                                    
                        for i,_trackIndice in zip(range(0,len(_trackInCluster)),_trackInCluster):
                            _track = self.tracks[_trackIndice]  
                        #     #_track.showTree()
                        #     #print('================================================')
                        #     #print('clean track')
                        #     #print('================================================')
                            _track.cleanTrack()  
                        #     _track.showTree(10)
                     
                            
                                
                    
                                
                                #unUsedTracks.remove(_track)

            return unUsedDetections       
    def predictionStep(self,time):
            for _track in self.tracks:
                _track.prediction(time)
                
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
        currState.PEst          = np.array(np.dot(np.dot(np.identity(currState.xPred.shape[0]) - np.dot(K,H), currState.PPred), (np.identity(currState.xPred.shape[0]) - np.dot(K, H)).T) + np.dot(K, np.dot(R, K.T)))
    
        currState.location.setXYZ(float(currState.xEst[0]),float(currState.xEst[2]), 0.0, 'ENU')
        currState.updateCovariance()
        currState.likelihood    = float(1/np.linalg.det(2*np.pi*S)*np.exp(-0.5*In.T @np.linalg.inv(S)@In))
  
        
    def trackManagement(self):
         
         removeTracks = []
         
         for _track in self.tracks:
             if not _track.trackValidity(self.scan.dateTime):
                 removeTracks.append(_track)
                 _track.trackState = TrackState.Deleted
         u = []  #uniquement pour le debug  
         if self.debug: 
                print('liste des pistes supprimées par le trackManagement:')
       
         for _rT in list(removeTracks):
             
             self.tracks.remove(_rT)
             u.append(_rT.id)
             del _rT
         
         #print("liste des îstes supprimées",u)
         if self.debug: 
             print(u) 
             
         for _track in self.tracks:
             _track.trackClassification(self.parameters['trackLifeConfirmation'])
         
    def merging(self):
         
    
         for _track1 in list(self.tracks):
             for _track2 in list(self.tracks):
                  if _track1 != _track2:
                      _track1.merging(_track2)
                      
         '''             
         u = []  #uniquement pour le debug       
         if self.debug: 
                            print('liste des pistes supprimées par le merging:')
                            
                            
         for _track  in list(self.tracks):  
             
             _track.cleanTrack()
             if _track.isMarkedToDelete()==True:
                       self.tracks.remove(_track)
                       u.append(_track.id)
                       del _track
                       
         '''        
         if self.debug: 
                    print(u)                 
    def initStep(self,_plots=[]):
         for _plot in _plots :
             self.initializeTrack(_plot)
             
    def run(self):
   
            if self.scan != None:
                #=======================================
                # prediction des pistes existantes
                #=======================================
    
                self.predictionStep(self.scan.dateTime)
    
                #=======================================
                # mise à jour des pistes
                #=======================================
    
                unUsedDetections = self.estimationStep()
    
                #=======================================
                # prunning
                #=======================================
        
                #self.prunning()
               
                #=======================================
                # merging
                #=======================================
                
                self.merging()
                
                #======================================
                # gestion de pistes
                #======================================
                
                self.trackManagement()
    
                #=======================================
                # merging
                #=======================================
    
                self.initStep(unUsedDetections)
                
                
                # ==========================================================
                # emission des pistes pour affichage et/ou enregistrement
                # ==========================================================
                if self.tracks != []:
                    self.updatedTracks.emit(self.tracks)

            self.scan = None