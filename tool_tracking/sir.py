# -*- coding: utf-8 -*-
"""
Created on Thu Aug 15 09:51:33 2019

@author: bpanneti
"""

import numpy as np
from scipy.stats import multivariate_normal
from tool_tracking.motionModel import MotionModel, StateType, F
from tool_tracking.estimator import Estimator, TRACKER_TYPE

from point import Position
from orientation import Orientation

class Infos:
    def __init__(self, samplesNumber, threshold):
        self.samplesNumber = samplesNumber

        self.weight = np.zeros((self.samplesNumber))+1/self.samplesNumber
        self.init = True

        self.randomSample = np.random.RandomState(np.random.randint(100000))
        self.randomResampling = np.random.RandomState(np.random.randint(100000))
        self.threshold = threshold

class Sir(Estimator):
    __metaclass__ = Estimator

    def __init__(self, parent=None, infos=None):
        super().__init__(parent, infos)
        self.type = TRACKER_TYPE.SIR

    def initializeTrack(self, plot):
        super().initializeTrack(plot)

        if isinstance(self.infos, Infos):
            self.myTrack.initialize([plot], self.scan.dateTime, 0, 0, 0, [], [], [MotionModel.CV, 1],self.infos)
        self.tracks.append(self.myTrack)

    def updateTrack(self, plot, unUpdatedTrack, track):
        super().updateTrack(plot, unUpdatedTrack, track)

        track.update([plot], self.scan.sensor.node.Position, self.scan.sensor.node.Orientation)

    @staticmethod
    def estimator(plot, currState, posCapteur=Position(), orientationCapteur=Orientation()):
        #Create samples and update weight
        samples = currState.estimatorInfos.randomSample.multivariate_normal(currState.xPred.reshape(currState.xPred.size,), currState.pPred, currState.estimatorInfos.samplesNumber)
        vraisemblance = np.array(multivariate_normal.pdf(np.transpose(np.array([samples[:,0], samples[:,2]])), plot.z_XY[:,0], plot.R_XY[:2,:2]))
        currState.estimatorInfos.weight = currState.estimatorInfos.weight * vraisemblance
        normWeight = currState.estimatorInfos.weight / np.sum(currState.estimatorInfos.weight)

        if not currState.estimatorInfos.init:
            samplesEff = 1/np.sum(np.square(normWeight))
            
            #Effective samples verification and resampling
            if samplesEff < currState.estimatorInfos.threshold:
                samples = Sir.reSampling(normWeight, samples, currState.estimatorInfos.randomResampling)
                currState.estimatorInfos.weight = np.zeros((currState.estimatorInfos.samplesNumber))+1/currState.estimatorInfos.samplesNumber
                normWeight = currState.estimatorInfos.weight

        else:
            currState.estimatorInfos.init = False
            
        #Estimator
        currState.state = np.transpose(samples)@normWeight
        currState.covariance = np.transpose(normWeight.reshape(currState.estimatorInfos.samplesNumber,1)*(samples-currState.state))@(samples-currState.state)

        #Update
        currState.location.setXYZ(float(currState.state[0]),float(currState.state[2]), 0.0, 'ENU')
        currState.updateCovariance()
    
    @staticmethod
    def reSampling(pdf, samples, randomResampling):
        newSamples = np.zeros(np.shape(samples))
        cdf = np.cumsum(pdf)/np.max(pdf)
        sampleWeight = randomResampling.uniform(0,1,pdf.size)

        for cnt, weight in enumerate(sampleWeight):
            if weight != 1:
                ind = np.argmax(cdf > weight)
            else:
                ind = pdf.size-1
            newSamples[cnt] = samples[ind]
        
        return newSamples
