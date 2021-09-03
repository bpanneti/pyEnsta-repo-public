# -*- coding: utf-8 -*-
"""
Created on Thu Mar 25 16:36:13 2021

@author: bpanneti
"""

import tool_tracking as tr
from tool_tracking.motionModel import MotionModel
from tool_tracking.Gaussian import Gaussian
import numpy as np
from scipy.optimize import linear_sum_assignment
from tool_tracking.estimator import TRACKER_TYPE
from tool_tracking.clustering import Compress, clustering

import sys

class Infos:
    def __init__(self, samplesNumber, threshold):
        self.samplesNumber = samplesNumber

        self.weight = np.zeros((self.samplesNumber))+1/self.samplesNumber
        self.init = True

        self.randomSample = np.random.RandomState(np.random.randint(100000))
        self.randomResampling = np.random.RandomState(np.random.randint(100000))
        self.threshold = threshold
        
class GMPHD(Gaussian):# ENSTA  A modifier ici : changement de classe
    __metaclass__ = Gaussian
    
    def __init__(self,  infos=None):
        super().__init__( infos)
        self.type   = TRACKER_TYPE.GMPHD # ENSTA  A modifier ici 
        self.debug  = False 
        self.sensors    = []
        
        p_birth     = 0.1
        p_survival  = 0.99
        p_detection = 0.98
        min_weight  = 0.00001
        lambfa_fa   = 0.00000015
        volume      = 1 
        seuil_merging = 0.9
        seuil_gating  = 0.9
        J_Max         = 100
        if infos !=None:
            polygons      =  [infos.toPolygon()]
            volume        =  infos.toVolume()
        else:
            polygons  = None
        model         =  [MotionModel.CV, 5]
        dist          = 100
        self.display  = False 
    
        self.parameters(p_birth,p_survival,p_detection,min_weight,lambfa_fa*volume,seuil_gating,seuil_merging,dist,polygons,model,J_Max)
        #self.displaySituation()
    def clustering(self):    
        pass

    def clear(self):
        pass
#        self.destroyGausssian()
#        self.unDisplaySituation()
    def getTracks(self):
        return self.tracks;
    def getGauss(self):
 
        return self.gm
    def run(self):
   
        if self.scan != None:

         
            
            #print('in GMPHD')
           
             
            #=======================================
            # prediction des gaussiennes existantes
            #=======================================
         
            self.prediction(self.scan.dateTime)
            #print('----------> after prediction')
            #elf.gaussianInfos()
            #=======================================
            # génération des gaussiennes naissantes
            #=======================================
            
            self.birthTarget(1000)
    
            #=======================================
            # mise à jour des gaussiennes 
            #=======================================
        
            self.update(self.scan.plots)
            #print('----------> after update')
            #print('----------> after update')
            #self.gaussianInfos()
            #=======================================
            # prunning
            #=======================================
    
            self.prunning()
            #print('----------> after prunning')
            #self.gaussianInfos()
            #=======================================
            # merging
            #=======================================
            
            
            self.merging()
            #print('----------> after merging')
            #self.gaussianInfos()
        
            #=======================================
            # compute mean measurement
            #=======================================
            
            
            self.meanMeasurement()
            
            #=======================================
            # GIW
            #=======================================
            print('---------------------------------  GIW')
            self.GIW(self.scan.dateTime)
            print('--------------------------------- after GIW')
            
#            print('----------> after merging')
#            self.gaussianInfos()
            
            #self.widget.displayGaussians( self.gm)
#            
#            if self.gm != []:
#                self.displayGaussian.emit(self.gm)
         
               
            self.scan = None
            
            
            
 

      