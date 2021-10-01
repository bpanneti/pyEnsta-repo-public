import numpy as np
from PyQt5.QtCore import QDateTime
from point import Position, enu_to_ecef, enu_to_ecefMatrix, REFERENCE_POINT
from orientation import Orientation
from scan import Plot, Scan, PLOTType
from numpy.linalg import inv
from math import atan2, sqrt
from target import TARGET_TYPE
from itertools import count
from copy import deepcopy as deepCopy

from tool_tracking.estimator import TRACKER_TYPE
from tool_tracking.motionModel import MotionModel, StateType 
import tool_tracking.ekf as EKF
import tool_tracking.cmkf as CMKF
import tool_tracking.imm as IMM
#import tool_tracking.sir as SIR
#import tool_tracking.pf as PF
from tool_tracking.BiasProcessing.corrector.roadLms import RoadLms

class CostPlot:
    def __init__(self):
        self.plot   = None
        self.cost   = np.Inf
        self.state  = None

def sigmas(x, P, c):
    #Sigma points around reference point
    #Inputs:
    #       x: reference point
    #       P: covariance
    #       c: coefficient
    #Output:
    #      X: Sigma points

    A = c * (np.linalg.cholesky(P)).T
    Y = np.tile(x, [1, x.shape[0]])
    X = np.concatenate((x, Y+A, Y-A), axis=1)

    return np.array(X)

class State(object):
    "Classe état"
    __cnt = count(0)
    def __init__(self, time = QDateTime(), plot = Plot(), dim = StateType.UNKNOWN, cov = 0, state = 0, extent=0, ftype = 0, filters=[], filterType = TRACKER_TYPE.UNKNOWN, estimatorInfos=[]):
        self.id                  = next(self.__cnt)
        self.idTrack             = -1
        self.idPere              = -1
        self.startedTime         = time
        self.time                = time
        self.mode                = dim
        self.idNode              = '127.0.0.1'
        self.periode             = 0
        self.classe              = TARGET_TYPE.UNKNOWN
        self.classeProbabilities = np.zeros((1, 1))
        self.state               = None
        self.covariance          = None
        self.xPred               = None
        self.pPred               = None
        self.X                   = None
        self.location            = Position()
        self.covarianceWGS84     = None
        self.heading             = 0 #direction dans le sens anti-horaire
        self.velocity            = 0 #vitesse en m/s
        self.sigmaX              = -1
        self.sigmaY              = -1
        self.angle               = -1
        self.cost                = 0
        self.filter              = filters 
        self.timeWithoutPlot     = 0 #in sec
        self.estimatorInfos      = estimatorInfos
        self.isEstimated         = False
        self.stateSavedInDb      = False
        self.filterType          = filterType
        self.idPlots             = []
        self.addtionnalInfo      = []

        if dim == StateType.XY:
            if ftype == 0:
                self.state              = np.zeros((4,1))
                self.covariance         = 10*np.identity(4)
                self.state[0]           = plot.z_XY[0]
                self.state[2]           = plot.z_XY[1]
                self.covariance[0,0]    = 2* plot.R_XY[0, 0]
                self.covariance[2,0]    = 2* plot.R_XY[1, 0]
                self.covariance[0,2]    = 2* plot.R_XY[0, 1]
                self.covariance[2,2]    = 2* plot.R_XY[1, 1]
                self.xPred              = self.state
                self.pPred              = self.covariance
                if self.filterType == TRACKER_TYPE.IMM:
                   self.stateModel                  = np.zeros((4,len(filters)))
                   self.covarianceModel             = np.zeros((4,4,len(filters)))
                   self.xPredModel                  = np.zeros((4,len(filters)))
                   self.pPredModel                  = np.zeros((4,4,len(filters)))
                   self.Mu                          = np.zeros((len(filters),1))
                   self.cbar                        = np.zeros((len(filters),1))
                   self.Mu_mixed                    = np.zeros((len(filters),len(filters)))
                   self.P_transition                = np.zeros((len(filters),len(filters)))
                   self.P_transition
                   for ind,model in enumerate(self.filter): 
                       self.stateModel[:,[ind]]                = self.state 
                       self.covarianceModel[:,:, ind]          = self.covariance
                       self.xPredModel[:,[ind]]                = self.state 
                       self.pPredModel[:,:, ind ]              = self.covariance
                       self.Mu[ind]                            = model[2]
                       self.P_transition[ind,:]                = model[3]
                   self.cbar        =  self.P_transition@self.Mu 
                   self.Mu_mixed    =  self.P_transition
            else:
                self.state          = np.copy(state)
                self.covariance     = np.copy(cov)
                self.xPred          = np.copy(state)
                self.pPred          = np.copy(cov)
                if ftype == 2:
                    self.X = np.copy(extent)
                    
            self.location.setXYZ(float(self.state[0]), float(self.state[2]), 0.0, 'ENU')
            self.updateCovariance()
        elif dim == StateType.XYZ:
            self.state              = np.zeros((6, 1))
            self.covariance         = np.identity(6)

    def __str__(self):
        return 'state n°' + str(self.id)
    def toJson(self,rank=0,numberofTracks=0):
         state = self.getStateECEF()
         cov = self.getCovarianceECEF()
         jsonCov = ''
         for i in range(6):
           for j in range(6): 
             jsonCov+= str(cov[i][j])+','
         jsonCov = jsonCov[:-1]          
         jsonClassif = ''
         for i in range(len(self.classeProbabilities)):
             jsonClassif  += str(float(self.classeProbabilities[i]))+',' 
         jsonClassif = jsonClassif[:-1]
         json='{'+\
		           '"trackNumber":'+ str(self.idTrack)+','+\
                   '"trackInScan":"'+ str(rank)+'/'+str(numberofTracks)+'",'+\
                   '"hsotility": "UNKNOWN",'+\
                   '"state": "CONFIRMED",'+\
                   '"node":"' + str(self.idNode) + '",' +\
                   '"position": {'+'"format":"ECEF","x":'+str(float(state[0]))+',"y":'+str(float(state[2]))+',"z":'+str(float(state[4]))+'},'+\
                   '"velocity": {'+'"format":"ECEF","x":'+str(float(state[1]))+',"y":'+str(float(state[3]))+',"z":'+str(float(state[5]))+'},'+\
                   '"date": "'+self.time.toUTC().toString("yyyy-MM-dd HH:mm:ss.z") +'",'+\
                   '"associatedPLots": [],'+\
                   '"trackClassification":"{'+jsonClassif+'}",'+\
                   '"precision":{'+'"format":"ECEF","col":6,"row":6,"components":"xvxyvyzvz","covariance":"'+jsonCov+'"},'+\
                   '"additionalInfo":['
         for inf in self.addtionnalInfo:
             json+='{"'+str(inf[0])+'":'+str(inf[1])+'},' 
         json =json[:-1]  
         json+= ']}'
         return json;
    def computeMixingProbabilities(self):
 
        self.cbar =  self.P_transition@self.Mu    
        
        for i,model_1 in enumerate(self.filter): 
            for j,model_2 in enumerate(self.filter):
                self.Mu_mixed[j,i] = (self.P_transition[i, j]*self.Mu[j]) / self.cbar[j]
                
    
    def getClassProbabilities(self):
        return self.classeProbabilities

    def getCovarianceECEF(self):
        covariance = np.identity(6)
        for j in range(2):
            for i in range(2):
                covariance[i][j] = self.covariance[i][j]
    
        P = enu_to_ecefMatrix(covariance,REFERENCE_POINT.latitude,REFERENCE_POINT.longitude,REFERENCE_POINT.altitude )
        return P

    def getStateECEF(self):
        state = np.zeros((6,1))

        x, y, z    = enu_to_ecef(float(self.state[0]), float(self.state[2]), 0.0, REFERENCE_POINT.latitude, REFERENCE_POINT.longitude, REFERENCE_POINT.altitude)
        vx, vy, vz = enu_to_ecef(float(self.state[1]), float(self.state[3]), 0.0, REFERENCE_POINT.latitude, REFERENCE_POINT.longitude, REFERENCE_POINT.altitude)
        ox, oy, oz = enu_to_ecef(0.0, 0.0, 0.0, REFERENCE_POINT.latitude, REFERENCE_POINT.longitude, REFERENCE_POINT.altitude)

        state[0] = x
        state[1] = vx - ox
        state[2] = y
        state[3] = vy - oy
        state[4] = z
        state[5] = vz - oz
        return np.array(state)

    def setTime(self, time=QDateTime()):
        self.time = time
        
    def updateLocation(self):
        self.location.setXYZ(float(self.state[0]), float(self.state[2]), 0.0, 'ENU')
        self.getStateECEF()

    def validity(self, time = QDateTime()):
       
        if self.timeWithoutPlot > 3 : 
            return False
        return True
    def prediction(self, time=QDateTime, flagChange=True):
        if  self.filterType == TRACKER_TYPE.EKF  :
            EKF.ekf.predictor(self,time , flagChange)
        elif  self.filterType == TRACKER_TYPE.CMKF : 
            CMKF.cmkf.predictor(self,time , flagChange)
        elif  self.filterType == TRACKER_TYPE.IMM : 
            IMM.imm.predictor(self,time , flagChange)
            
            
                
    def gating(self, plot=Plot(), threshold=0): #NSTA : modification
        self.prediction(plot.dateTime, False)
        x = self.xPred
        P = self.pPred
        cost = CostPlot()
        cost.plot = plot
        lambda_c = np.inf

        if plot.type == PLOTType.POLAR and self.mode == StateType.XY:
            H = np.zeros([2, 4])
            H[0, 0] = 1
            H[1, 2] = 1

            innovation = plot.z_XY - np.dot(H, x)

            S = plot.R_XY + np.dot(H, np.dot(P, H.T))

            lambda_c = innovation.T@np.linalg.inv(S)@innovation
        elif plot.type == PLOTType.ANGULAR and self.mode == StateType.XY:
            #ENTA TO DO
            #EKF idem 
            
            lambda_c = innovation.T@np.linalg.inv(S)@innovation
            pass
            
        if lambda_c <= threshold:
            cost.cost     = lambda_c
            cost.state    = self
            
            #print(['---> in state gating',lambda_c])
            return [True, cost]

        return [False, cost]
    def classification(self,plot):
        #ToDoENSTA
        
        pass
    
    def updateCovariance(self):
        #update heading et velocity en même temps

        self.heading    = (np.pi/2 - atan2(self.state[3], self.state[1]))*180/np.pi #direction dans le sens anti-horaire
        self.velocity   = float(np.sqrt(np.power(self.state[1], 2.0) + np.power(self.state[3], 2.0)))

        lmbda, u = np.linalg.eig(self.covariance)
#        print('-------')
#        print('updateCovariance')
#        print(self.covariance)
        idx = lmbda.argsort()[::-1]   
        lmbda = lmbda[idx]
        u = u[:,idx]
        
        Point = Position()
        Point.setXYZ(float(self.state[0] + sqrt(np.abs(lmbda[0]))), float(self.state[2] + sqrt(np.abs(lmbda[2]))), 0.0)
        Point2 = Position()
        Point2.setXYZ(float(self.state[0]), float(self.state[2]), 0.0)

        self.sigmaX = Point.latitude  - Point2.latitude
        self.sigmaY = Point.longitude - Point2.longitude
#        print(self.sigmaX)
#        print(self.sigmaY)
        if self.sigmaX > self.sigmaY:
            self.angle = atan2(u[2, 0], u[0, 0])
        else:
            self.angle = atan2(u[2, 2], u[0, 2])
#        print(self.angle)
#        print('-------')
        if self.mode == StateType.XY:
            Point                        = Position()
            Point.setXYZ( float(self.state[1] + sqrt(np.abs(lmbda[1]))), float(self.state[3] + sqrt(np.abs(lmbda[3]))), 0.0)
            Point2                       = Position()
            Point2.setXYZ( float(self.state[1] ), float(self.state[3]), 0.0)
            self.sigmaVX                 = Point.latitude - Point2.latitude
            self.sigmaVY                 = Point.longitude - Point2.longitude
            self.covarianceWGS84         = np.zeros((4, 4))
            self.covarianceWGS84[0, 0]   = self.sigmaX**2
            self.covarianceWGS84[1, 1]   = self.sigmaVX**2
            self.covarianceWGS84[2, 2]   = self.sigmaY**2
            self.covarianceWGS84[3, 3]   = self.sigmaVY**2
            self.covarianceWGS84         = u@np.diag([self.sigmaX**2, self.sigmaVX**2, self.sigmaY**2, self.sigmaVY**2])@u.T 
         
    def setVelocity(self,velocity):
        

        
        if len(velocity) == 2 and self.mode == StateType.XY:
            self.state[1] = velocity[0]
            self.state[3] = velocity[1]
            if self.filterType == TRACKER_TYPE.IMM:
                for ind,model in enumerate(self.filter): 
                       self.stateModel[1,[ind]]                = velocity[0] 
                       self.stateModel[3,[ind]]                = velocity[1] 
           
            
                   
        if len(velocity) == 3 and self.mode == StateType.XYZ:
            self.state[1] = velocity[0]
            self.state[3] = velocity[1]
            self.state[5] = velocity[2]
            if self.filterType == TRACKER_TYPE.IMM:
                for ind,model in enumerate(self.filter): 
                       self.stateModel[1,[ind]]                = velocity[0] 
                       self.stateModel[3,[ind]]                = velocity[1]
                       self.stateModel[5,[ind]]                = velocity[2]

    def estimation(self, plot, filterType=TRACKER_TYPE.UNKNOWN, posCapteur=Position(), orientationCapteur=Orientation()):
        self.timeWithoutPlot = 0
        self.isEstimated = True

        if not isinstance(posCapteur, Position):
            print("\n[Error] posCapteur should be a Position instance.\n")
            return
        if not isinstance(orientationCapteur, Orientation):
            print("\n[Error] orientationCapteur should be a Orientation instance.\n")
            return
        if filterType == TRACKER_TYPE.UNKNOWN:
            print("\n[Error] estimation no type provided.\n")
            return

        if plot.type == PLOTType.ANGULAR and self.mode == StateType.XY:
               #==============================
               # UKF
               #==============================
            print('-----> ukf')
            return
        elif  filterType == TRACKER_TYPE.EKF and plot.type == PLOTType.POLAR and self.mode == StateType.XY:
            EKF.ekf.estimator(plot, self, posCapteur, orientationCapteur)
        elif filterType == TRACKER_TYPE.CMKF  and (plot.type == PLOTType.POLAR or plot.type == PLOTType.SPHERICAL) and self.mode == StateType.XY:
              CMKF.cmkf.estimator(plot, self, posCapteur, orientationCapteur)
        elif filterType == TRACKER_TYPE.IMM  and (plot.type == PLOTType.POLAR or plot.type == PLOTType.SPHERICAL) and self.mode == StateType.XY:
              IMM.imm.estimator(plot, self, posCapteur, orientationCapteur)      
#            elif filterType == TRACKER_TYPE.SIR:
#                SIR.Sir.estimator(plot, self, posCapteur, orientationCapteur)
#            elif filterType == TRACKER_TYPE.KPF:
#                PF.pf.estimator(plot, self, posCapteur, orientationCapteur)
        else:
            print("\nThis type of estimation isn't available.\n")

    def getLocationWGS84(self):
        M = np.zeros((1, 2))
        WGS84  = np.zeros((1, 2))
        if self.mode == StateType.XY:
            M = [self.state[0, 0], self.state[2, 0]]
        elif self.mode == StateType.XY:
            M = [self.state[0, 0], self.state[2, 0], self.state[4, 0]]
        pt = Position()
        pt.setXYZ(float(M[0]), float(M[1]), 0.0)
        WGS84 = [pt.longitude, pt.latitude]
        return WGS84
        
    def getLocation(self):
        M = np.zeros((1, 2))
        if self.mode == StateType.XY:
            M = [self.state[0, 0], self.state[2, 0]]
        elif self.mode == StateType.XY:
            M = [self.state[0, 0], self.state[2, 0], self.state[4, 0]]
        return M
    
    def getVelocity(self):
        M = np.zeros((1, 2))
        if self.mode == StateType.XY:
            M = [self.state[1, 0], self.state[3, 0]]
        elif self.mode == StateType.XYZ:
            M = np.zeros((1, 3))
            M = [self.state[1, 0], self.state[3, 0], self.state[5, 0]]
        return np.linalg.norm(M) 

    def getHeading(self):
        M = np.zeros((1, 2))
        M = [self.state[1, 0], self.state[3, 0]]
        return 90 - np.arctan2(M[1], M[0]) * 180/np.pi

    def getDeltaTime(self):
        return self.startedTime.msecsTo(self.time)/1000

    @staticmethod
    def copyState(previousState):
        startedTime = previousState.startedTime
        actualState = deepCopy(previousState)
        actualState.id = next(State.__cnt)
        actualState.stateSavedInDb = False
        actualState.startedTime = startedTime
        return actualState
