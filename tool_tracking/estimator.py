# -*- coding: utf-8 -*-
"""
Created on Mon Apr 06 08:44:00 2020

@author: rgomescardoso
"""
from enum import Enum
from abc import ABCMeta, abstractmethod

import tool_tracking as tr

from PyQt5.QtCore import QThread, pyqtSignal, QMutex,QObject

class TRACKER_TYPE(Enum):
    UNKNOWN     = 0
    CMKF        = 1
    EKF         = 2
    IMM         = 3
    CMKF_GNNSF  = 4
    IMM_GNNSF   = 5
    RMKF        = 11
    SIR         = 12
    KPF         = 9
    UKF         = 8
    CMKF_PDAF   = 7
    CMKF_JPDAF  = 10
    GMPHD       = 6
    

class Estimator(QObject):
    __metaclass__ = ABCMeta
    # Messagerie
    message = pyqtSignal('QString')

    # list des pistes
    updatedTracks = pyqtSignal(list)

    def __init__(self, parent=None, infos=None):
        super(Estimator, self).__init__()
        
        #QThread.__init__(self, parent)
   
        #self.thread.started.connect(self.run)
        # liste des pistes
        self.tracks         = []
        self.infos      = infos

        self.type       = TRACKER_TYPE.UNKNOWN

        # liste des id cibles à pister
        self.targets    = []

        # scan courant
        self.scan       = None

        # current track
        self.myTrack     = None
        
       


  
    def setTargets(self, targets):
        self.targets = targets

    def clear(self):
#        self.terminate()
#        while not self.isFinished():
#            pass

        for track in self.tracks:
            track.undisplay()
            del track

        self.tracks = []
        self.scan = None

    def isTracked(self, idTarget):
        # retourne vrai si le plot est associé à une cible à tracker
        for target in self.targets:
            if target == idTarget:
                return True

        return False

    def searchTrack(self, idTarget):
        for track in self.tracks:
            if track.groundTruth == idTarget:
                return track

        return None

    def receiveScan(self, scan):
 
        self.scan = scan
        self.run()
         
    def getTracks(self):
        return self.tracks

    def copyTracks(self):
        tracks = []
        for u in self.tracks:
            tracks.append(u)
        return tracks

    @abstractmethod
    def initializeTrack(self, plot):
        # initialisation d'une nouvelle piste
        self.message.emit('initialize a new track')
        self.myTrack = tr.track.Track(self.type)

    @abstractmethod
    def updateTrack(self, plot, unUpdatedTrack, track):
        unUpdatedTrack.remove(track)

    @staticmethod
    @abstractmethod
    def predictor(currState, time , flagChanger):
        pass
    
    @staticmethod
    @abstractmethod
    def estimator(plot, currState, posCapteur, orientationCapteur):
        pass

    @abstractmethod
    def run(self):

      
#        if self.mutex.tryLock()==False:
#            return 
        if self.scan != None:
 
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
