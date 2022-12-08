# -*- coding: utf-8 -*-
"""
Created on Mon Apr 06 08:44:00 2020

@author: rgomescardoso
"""
 
from abc import ABCMeta, abstractmethod

#import tool_tracking as tr

from PyQt5.QtCore import QThread, pyqtSignal, QMutex,QObject

import toolTracking as tr

class Estimator(QObject):
    __metaclass__ = ABCMeta
    # Messagerie
    message = pyqtSignal('QString')

    # list des pistes
    updatedTracks = pyqtSignal(list)

    def __init__(self, parent=None):
        super(Estimator, self).__init__()
        
        #QThread.__init__(self, parent)
   
        #self.thread.started.connect(self.run)
        # liste des pistes
        self.tracks         = []

        # liste des id cibles à pister
        self.targets    = []

        # scan courant
        self.scan       = None
 
        # current track
        self.currentTrack     = None
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
    def updateParameters(self):
       
       pass
    @abstractmethod
    def initializeTrack(self, plot):
       
       pass
 
    @abstractmethod
    def updateTrack(self, plot, unUpdatedTrack, track):
        unUpdatedTrack.remove(track)
        pass

    @staticmethod
    @abstractmethod
    def predictor(currState, time ,parameters, flagChanger):
        pass
    
    @staticmethod
    @abstractmethod
    def estimator(plot, currState, posCapteur, orientationCapteur):
        pass
    @staticmethod
    @abstractmethod
    def classification(plot, currState):
        pass
    @abstractmethod
    def run(self):
        pass
 