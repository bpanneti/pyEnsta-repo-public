# -*- coding: utf-8 -*-
"""
Created on Mon Oct  7 11:35:32 2019

@author: bpanneti
"""

import tool_tracking as tr
from tool_tracking.randomMatrice import group
from tool_tracking.motionModel import MotionModel
from tool_tracking.estimator import Estimator, TRACKER_TYPE

#attention le Kalman filter Random Matrices n'est configuré que pour un seul groupe
    
class rmkf(Estimator):
    __metaclass__ = Estimator

    def run(self):
        if self.scan != None:
            unUpdatedTrack = []
            for u in  self.tracks  :
                    unUpdatedTrack.append(u) 
            
            _cluster =[]            
            for _plot in self.scan.plots:
                if self.isTracked(_plot.idTarget):
                        _cluster.append(_plot)
                    #recherce d'une piste existante associée à la cible
            
            if self.tracks ==[]:
                        #initialisation d'une nouvelle piste
                        self.message.emit('initialize a new Group')

                        myTrack = tr.track.Track()
                        myTrack.initialize( _cluster )
                        self.tracks.append(myTrack)
                    
            else:
                        #forcément q'une seule track dans ce mode
                        _track = self.tracks[0]
                        #mise à jour
                        unUpdatedTrack.remove(_track)
                        _track.update(_cluster)
                        
            for tracks in  unUpdatedTrack  :
                    #print('only prediction')
                    tracks.prediction(self.scan.dateTime)
    
            if self.tracks != []:
                self.updatedTracks.emit(self.tracks)
            
            self.scan = None
