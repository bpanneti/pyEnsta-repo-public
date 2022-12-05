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
from sensor import Sensor

from toolTracking.cmkf import cmkf
from toolTracking.ekf import ekf
from toolTracking.imm import imm
from toolTracking.gnnsf import gnnsf
from toolTracking.sda import sda
#==========================================================
# type de rtacker
#==========================================================

 
from toolTracking.utils   import StateType, trackerType 
 
#import tool_tracking.sir as SIR
#import tool_tracking.pf as PF

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
    def __init__(self, time = QDateTime(), plot = None,idTrack = -1, state = None,parameters = None,recorded =False):

 
        if parameters == None and recorded ==False:    
           print('[Error] no parameetrs defined in state.py')
           return
            
      
        self.id                  = next(self.__cnt)
        self.idTrack             = idTrack  
        self.idPere              = -1
        self.startedTime         = time
        self.time                = time
        self.idNode              = '127.0.0.1'
        self.parameters          = parameters
        #informations pour l'estimation
        
        self.periode             = 0
        self.xEst                = None
        self.PEst                = None
        self.xPred               = None
        self.PPred               = None
        self.cost                = 0
        self.likelihood          = 0
        self.LLR                 = 0
        self.PD                  = 0.9
        self.lambdaFA            = 0.0000001
        self.plot                = plot
        #informations pour la classification
                
        self.classe              = TARGET_TYPE.UNKNOWN
        self.classeProbabilities = np.zeros((1, 1))
        
        #informations pour affichage et sauvegarde
        self.location            = Position()
        self.covarianceWGS84     = None
        self.heading             = 0 #direction dans le sens anti-horaire
        self.velocity            = 0 #vitesse en m/s
        self.sigmaX              = -1
        self.sigmaY              = -1
        self.angle               = -1
        
        #informations pour la gestion des pistes
        
        self.timeWithoutPlot     = 0 #in sec
        self.isEstimated         = False
        self.stateSavedInDb      = False
        self.idPlots             = []
        self.addtionnalInfo      = []

        if parameters != None and parameters['dimension'] == StateType.XY:
                self.xEst               = np.zeros((4,1))
                self.PEst               = 10*np.identity(4)
                self.xEst[0]            = plot.z_XY[0]
                self.xEst[2]            = plot.z_XY[1]
                self.PEst[0,0]          = 2* plot.R_XY[0, 0]
                self.PEst[2,0]          = 2* plot.R_XY[1, 0]
                self.PEst[0,2]          = 2* plot.R_XY[0, 1]
                self.PEst[2,2]          = 2* plot.R_XY[1, 1]
                self.xPred              = self.xEst
                self.pPred              = self.PEst
                self.likelihood         = self.PD
                if parameters['algorithm']  == trackerType.IMM.name:
                   self.xModel                      = np.zeros((4,len(parameters['models'])))
                   self.pModel                      = np.zeros((4,4,len(parameters['models'])))
                   self.xPredModel                  = np.zeros((4,len(parameters['models'])))
                   self.pPredModel                  = np.zeros((4,4,len(parameters['models'])))
                   self.Mu                          = np.zeros((len(parameters['models']),1))
                   self.cbar                        = np.zeros((len(parameters['models']),1))
                   self.Mu_mixed                    = np.zeros((len(parameters['models']),len(parameters['models'])))
                   self.P_transition                = np.zeros((len(parameters['models']),len(parameters['models'])))

                   for ind,model in enumerate(parameters['models']): 
                       self.xModel[:,[ind]]                    = self.xEst 
                       self.pModel[:,:, ind]                   = self.PEst
                       self.xPredModel[:,[ind]]                = self.xEst 
                       self.pPredModel[:,:, ind ]              = self.PEst
                       self.Mu[ind]                            = model['proba']
                       self.P_transition[ind,:]                = model['Ptransition_vector']
                   
       
                   self.cbar        =  self.P_transition@self.Mu 
                   #self.cbar       /=np.sum(self.cbar )
                   self.Mu_mixed    =  np.copy(self.P_transition)
             
                self.location.setXYZ(float(self.xEst[0]), float(self.xEst[2]), 0.0, 'ENU')
                self.updateCovariance()
                
        elif parameters != None and parameters['dimension'] == StateType.XYZ:
            self.xEst              = np.zeros((6, 1))
            self.PEst              = np.identity(6)

    # def __str__(self):
    #     return 'state n°' + str(self.id)
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
         if self.addtionnalInfo!=[]:
             json =json[:-1]  
         json+= ']}'
         return json;
    def computeMixingProbabilities(self):
    
        self.cbar =  self.P_transition@self.Mu  
        #self.cbar       /=np.sum(self.cbar )
   
        
        for i,model_1 in enumerate(self.parameters['models']): 
            for j,model_2 in enumerate(self.parameters['models']):
   
                self.Mu_mixed[j,i] = (self.P_transition[i, j]*self.Mu[j]) / self.cbar[i]
      
 
 
    def getClassProbabilities(self):
        return self.classeProbabilities

    def getCovarianceECEF(self):
        covariance = np.identity(6)
        for j in range(2):
            for i in range(2):
                covariance[i][j] = self.PEst[i][j]
    
        P = enu_to_ecefMatrix(covariance,REFERENCE_POINT.latitude,REFERENCE_POINT.longitude,REFERENCE_POINT.altitude )
        return P

    def getStateECEF(self):
        state = np.zeros((6,1))

        x, y, z    = enu_to_ecef(float(self.xEst[0]), float(self.xEst[2]), 0.0, REFERENCE_POINT.latitude, REFERENCE_POINT.longitude, REFERENCE_POINT.altitude)
        vx, vy, vz = enu_to_ecef(float(self.xEst[1]), float(self.xEst[3]), 0.0, REFERENCE_POINT.latitude, REFERENCE_POINT.longitude, REFERENCE_POINT.altitude)
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

        self.location.setXYZ(float(self.xEst[0]), float(self.xEst[2]), 0.0, 'ENU')
        self.getStateECEF()

    def validity(self, time = QDateTime()):
        if self.timeWithoutPlot > self.parameters['timeWithoutPlot'] : 
            return False
        return True
    def prediction(self, time=QDateTime, flagChange=True):
        
        
        if  self.parameters['algorithm']  == trackerType.EKF.name  :
            ekf.predictor(self,time , self.parameters,flagChange)
        elif  self.parameters['algorithm'] == trackerType.CMKF.name:
            cmkf.predictor(self,time , self.parameters, flagChange)
        elif  self.parameters['algorithm'] == trackerType.IMM.name : 
            imm.predictor(self,time , self.parameters, flagChange)
        elif  self.parameters['algorithm'] == trackerType.GNNSF.name : 
             gnnsf.predictor(self,time , self.parameters, flagChange)           
        elif  self.parameters['algorithm'] == trackerType.SDA.name : 
             sda.predictor(self,time , self.parameters, flagChange)              

        self.likelihood = 1 - self.PD
        
    def gating(self, plot=Plot(), threshold=0): #NSTA : modification
        self.prediction(plot.dateTime, False)
        x = self.xPred
        P = self.pPred
        cost = CostPlot()
        cost.plot = plot
        lambda_c = np.inf

        if plot.type == PLOTType.POLAR and self.parameters['dimension'] == StateType.XY:
            H = np.zeros([2, 4])
            H[0, 0] = 1
            H[1, 2] = 1

            innovation = plot.z_XY - np.dot(H, x)

            S = plot.R_XY + np.dot(H, np.dot(P, H.T))

            lambda_c = innovation.T@np.linalg.inv(S)@innovation
        elif plot.type == PLOTType.ANGULAR and self.parameters['dimension'] == StateType.XY:
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

        self.heading    = (np.pi/2 - atan2(self.xEst[3], self.xEst[1]))*180/np.pi #direction dans le sens anti-horaire
        self.velocity   = float(np.sqrt(np.power(self.xEst[1], 2.0) + np.power(self.xEst[3], 2.0)))

        lmbda, u = np.linalg.eig(self.PEst)
#        print('-------') 
#        print('updateCovariance')
#        print(self.covariance)
        idx = lmbda.argsort()[::-1]   
        lmbda = lmbda[idx]
        u = u[:,idx]
        
        Point = Position()
        Point.setXYZ(float(self.xEst[0] + sqrt(np.abs(lmbda[0]))), float(self.xEst[2] + sqrt(np.abs(lmbda[2]))), 0.0)
        Point2 = Position()
        Point2.setXYZ(float(self.xEst[0]), float(self.xEst[2]), 0.0)

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
        if self.parameters!=None and self.parameters['dimension'] == StateType.XY:
            Point                        = Position()
            Point.setXYZ( float(self.xEst[1] + sqrt(np.abs(lmbda[1]))), float(self.xEst[3] + sqrt(np.abs(lmbda[3]))), 0.0)
            Point2                       = Position()
            Point2.setXYZ( float(self.xEst[1] ), float(self.xEst[3]), 0.0)
            self.sigmaVX                 = Point.latitude - Point2.latitude
            self.sigmaVY                 = Point.longitude - Point2.longitude
            self.covarianceWGS84         = np.zeros((4, 4))
            self.covarianceWGS84[0, 0]   = self.sigmaX**2
            self.covarianceWGS84[1, 1]   = self.sigmaVX**2
            self.covarianceWGS84[2, 2]   = self.sigmaY**2
            self.covarianceWGS84[3, 3]   = self.sigmaVY**2
            self.covarianceWGS84         = u@np.diag([self.sigmaX**2, self.sigmaVX**2, self.sigmaY**2, self.sigmaVY**2])@u.T 
         
    def setVelocity(self,velocity):
        

        
        if len(velocity) == 2 and self.parameters['dimension'] == StateType.XY:
            self.xEst[1] = velocity[0]
            self.xEst[3] = velocity[1]
            '''
            if self.parameters['algorithm'] == trackerType.IMM.name:
                for ind,model in enumerate(self.filter): 
                       self.stateModel[1,[ind]]                = velocity[0] 
                       self.stateModel[3,[ind]]                = velocity[1] 
           '''
            
                   
        if len(velocity) == 3 and  self.parameters['dimension']  == StateType.XYZ:
            self.xEst[1] = velocity[0]
            self.xEst[3] = velocity[1]
            self.xEst[5] = velocity[2]
            '''
            if self.parameters['algorithm'] == trackerType.IMM.name:
                for ind,model in enumerate(self.filter): 
                       self.stateModel[1,[ind]]                = velocity[0] 
                       self.stateModel[3,[ind]]                = velocity[1]
                       self.stateModel[5,[ind]]                = velocity[2]
            '''
    def estimation(self, plots = [],posCapteur=Position(), orientationCapteur=Orientation()):
        self.timeWithoutPlot    = 0
        self.isEstimated        = True
        self.likelihood         = 1 - self.PD
        if not isinstance(posCapteur, Position):
            print("\n[Error] posCapteur should be a Position instance.\n")
            return
        if not isinstance(orientationCapteur, Orientation):
            print("\n[Error] orientationCapteur should be a Orientation instance.\n")
            return
        if 'algorithm' not in self.parameters :
            print("\n[Error] estimation no type provided.\n")
            return

        if plots[0].type == PLOTType.ANGULAR and self.parameters['dimension']== StateType.XY:
               #==============================
               # UKF
               #==============================
            print('-----> ukf')
            return
        
      
        elif  self.parameters['algorithm'] == trackerType.EKF.name and plots[0].type == PLOTType.POLAR and self.parameters['dimension'] == StateType.XY:
            ekf.estimator(plots[0], self, posCapteur, orientationCapteur)
        elif self.parameters['algorithm'] ==  trackerType.CMKF.name  and (plots[0].type == PLOTType.POLAR or plots[0].type == PLOTType.SPHERICAL) and self.parameters['dimension']== StateType.XY:
            cmkf.estimator(plots[0], self, posCapteur, orientationCapteur)
        elif  self.parameters['algorithm'] == trackerType.IMM.name : 
              imm.estimator(plots[0], self, posCapteur, orientationCapteur,parameters=self.parameters)
        elif self.parameters['algorithm'] ==  trackerType.GNNSF.name  and (plots[0].type == PLOTType.POLAR or plots[0].type == PLOTType.SPHERICAL) and self.parameters['dimension']== StateType.XY:
            gnnsf.estimator(plots[0], self, posCapteur, orientationCapteur)
        elif self.parameters['algorithm'] ==  trackerType.SDA.name  and (plots[0].type == PLOTType.POLAR or plots[0].type == PLOTType.SPHERICAL) and self.parameters['dimension']== StateType.XY:
                sda.estimator(plots[0], self, posCapteur, orientationCapteur)
        else:
            print("\nThis type of estimation isn't available.\n")
        self.likelihood = self.PD * self.likelihood/self.lambdaFA 

    def getLocationWGS84(self):
        M = np.zeros((1, 2))
        WGS84  = np.zeros((1, 2))
        if self.parameters['dimension']  == StateType.XY:
            M = [self.xEst[0, 0], self.xEst[2, 0]]
        elif self.parameters['dimension']  == StateType.XY:
            M = [self.xEst[0, 0], self.xEst[2, 0], self.xEst[4, 0]]
        pt = Position()
        pt.setXYZ(float(M[0]), float(M[1]), 0.0)
        WGS84 = [pt.longitude, pt.latitude]
        return WGS84
        
    def getLocation(self):
        M = np.zeros((1, 2))
        if self.parameters['dimension']  == StateType.XY:
            M = [self.xEst[0, 0], self.xEst[2, 0]]
        elif self.parameters['dimension']  == StateType.XY:
            M = [self.xEst[0, 0], self.xEst[2, 0], self.xEst[4, 0]]
        return M
    
    def getVelocity(self):
        M = np.zeros((1, 2))
        if self.parameters['dimension']   == StateType.XY:
            M = [self.xEst[1, 0], self.xEst[3, 0]]
        elif self.parameters['dimension']   == StateType.XYZ:
            M = np.zeros((1, 3))
            M = [self.xEst[1, 0], self.xEst[3, 0], self.xEst[5, 0]]
        return np.linalg.norm(M) 

    def getHeading(self):
        M = np.zeros((1, 2))
        M = [self.xEst[1, 0], self.xEst[3, 0]]
        return 90 - np.arctan2(M[1], M[0]) * 180/np.pi

    def getDeltaTime(self):
        return self.startedTime.msecsTo(self.time)/1000

    '''
    def copyState(self,_State):
 
        self.idTrack             = _State.idTrack  
        self.idPere              = _State.idPere 
        self.startedTime         = _State.startedTime  
        self.time                = _State.time 
        self.idNode              = _State.idNode 
        self.parameters          = _State.parameters
        #informations pour l'estimation
        
 
        self.xEst                = _State.xEst 
        self.PEst                = _State.PEst
        self.xPred               = _State.xPred
        self.PPred               = _State.PPred 
        self.cost                = _State.cost  
        #informations pour la classification
                
        self.classe              = _State.classe 
        self.classeProbabilities = _State.classeProbabilities
        
        #informations pour affichage et sauvegarde
        self.location            = Position()
        self.covarianceWGS84     = None
        self.heading             = _State.heading 
        self.velocity            = _State.velocity  
        self.sigmaX              = _State.sigmaX  
        self.sigmaY              = _State.sigmaY 
        self.angle               = _State.angle  
        
        #informations pour la gestion des pistes
        
        self.timeWithoutPlot     = _State.timeWithoutPlot
        self.isEstimated         = False
        self.stateSavedInDb      = False
        self.idPlots             = []
        self.addtionnalInfo      = []
 
        print('copyState done')
     
    '''
    @staticmethod
    def copyState(previousState):
 
        startedTime = previousState.startedTime
        actualState = deepCopy(previousState)

        actualState.id = next(State.__cnt)
        actualState.idPere = previousState.id
        actualState.stateSavedInDb = False
        actualState.startedTime = startedTime
        return actualState
