# -*- coding: utf-8 -*-
"""
Created on Mon Oct  7 14:12:18 2019

@author: bpanneti
"""
import math
from PyQt5.QtCore import QDateTime
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

from point import Position, enu_to_ecef, enu_to_ecefMatrix, REFERENCE_POINT
from scan import Plot, PLOTType
from tool_tracking.motionModel import StateType as _dim
import tool_tracking as toolTracking
from target import TARGET_TYPE
from itertools import count
def imscatter(x, y, imagePath, ax, zoom=0.1):
    im = OffsetImage(plt.imread(imagePath), zoom=zoom)
    ab = AnnotationBbox(im, (x, y), xycoords='data', frameon=False)
    return ax.add_artist(ab)

from scipy.linalg import sqrtm
def F(periode, dim):
    mat = np.identity(dim)
    if dim == 4:
        mat[0, 1] = periode
        mat[2, 3] = periode
    return mat

def Q(T, dim, noise):
    M = np.identity(dim)
    if dim == 4:
        M = np.array([[np.power(T, 3)/3, np.power(T, 2)/2, 0, 0], [np.power(T, 2)/2, T, 0, 0], [0, 0, np.power(T, 3)/3, np.power(T, 2)/2], [0, 0, np.power(T, 2)/2,     T]])

    Q = np.matrix(np.power(noise, 2.0)*M)
    return Q


class group(object):
    "Classe group"
    __cnt = count(0)
    def __init__(self,  time=QDateTime(), _cluster=[],  dim=_dim(0)):
        self.time = time
        self.mode = dim
        self.id                  = next(self.__cnt)
        self.idPere              = -1
        self.periode = 0
        self.x = None
        self.X = None
        self.P = None
        self.v = None
        self.d = 2
        self.location = Position()
        self.covarianceWGS84 = None
        self.heading = 0  # direction dans le sens anti-horaire
        self.velocity = 0  # vitesse en m/s
        self.sigmaX = -1
        self.sigmaY = -1
        self.angle = -1
        self.cost = 0
        self.idPlots             = []
        self.isEstimated         = False
        self.stateSavedInDb      = False
        self.classe              = TARGET_TYPE.UNKNOWN
        self.classeProbabilities = np.zeros((1, 1))
        if dim == _dim(1):
            self.v = 2*len(_cluster)
            [z, Z] = self.detection(_cluster)
            self.x = np.zeros((4, 1))
            self.X = np.zeros((2, 2))
            self.P = 10*np.identity(4)

            self.x[0] = z[0]
            self.x[2] = z[1]
            self.P[0, 0] = Z[0, 0]
            self.P[2, 0] = Z[1, 0]
            self.P[0, 2] = Z[0, 1]
            self.P[2, 2] = Z[1, 1]
            
            #init
#            print('=======================> init')
#            print(Z)
#            print(self.P)
            
            self.X = np.copy(Z)

            self.location.setXYZ(float(self.x[0]), float(self.x[2]), 0.0,'ENU')
            self.updateCovariance()
        elif dim == _dim(2):
            self.state = np.zeros((6, 1))
            self.covariance = np.identity(6)

    def detection(self, _cluster):
        if self.mode == _dim(1):
            z = np.zeros((2, 1))
            Z = np.zeros((2, 2))

            for plot in _cluster:
                z += plot.z_XY
                self.idPlots.append(plot.id)
            z = z / len(_cluster)

            for plot in _cluster:
                Z += (z - plot.z_XY)@(z - plot.z_XY).T

            return z, Z
        return None

    def setTime(self,  _time=QDateTime):
        self.time = _time

    def updateLocation(self):
        self.location.setXYZ(float(self.x[0]), float(self.x[2]), 0.0,'ENU')

    def gating(self, plot=Plot(), threshold=0):
        [x, P] = self.prediction(plot.dateTime)
        cost = toolTracking.state.CostPlot()
        cost.plot = plot
        lambda_c = np.inf
        if plot.type == PLOTType.POLAR and self.mode == _dim(1):
            H = np.zeros([2, 4])
            H[0, 0] = 1
            H[1, 2] = 1

            innovation = plot.z_XY - np.dot(H, x)

            S = plot.R_XY + np.dot(H, np.dot(P, H.T))

            lambda_c = innovation.T@ np.linalg.inv(S)@innovation

        if lambda_c <= threshold:
            cost.cost = lambda_c
            cost.state = self
            return [True, cost]

        return [False, cost]
        return self.classeProbabilities
    def getCovarianceECEF(self):
        covariance = np.identity(6)
        for j in range(4):
            for i in range(4):
                covariance[i,j] = self.P[i,j]
    
        P = enu_to_ecefMatrix(covariance,REFERENCE_POINT.latitude,REFERENCE_POINT.longitude,REFERENCE_POINT.altitude )
        return P
    def getStateECEF(self):
        state = np.zeros((6,1))

        x, y, z    = enu_to_ecef(float(self.x[0]), float(self.x[2]), 0.0, REFERENCE_POINT.latitude, REFERENCE_POINT.longitude, REFERENCE_POINT.altitude)
        vx, vy, vz = enu_to_ecef(float(self.x[1]), float(self.x[3]), 0.0, REFERENCE_POINT.latitude, REFERENCE_POINT.longitude, REFERENCE_POINT.altitude)
        ox, oy, oz = enu_to_ecef(0.0, 0.0, 0.0, REFERENCE_POINT.latitude, REFERENCE_POINT.longitude, REFERENCE_POINT.altitude)

        state[0] = x
        state[1] = vx - ox
        state[2] = y
        state[3] = vy - oy
        state[4] = z
        state[5] = vz - oz
        return np.array(state)

    def getClassProbabilities(self):
        return self.classeProbabilities
    def prediction(self,  time=QDateTime):

        periode = self.time.msecsTo(time)/1000
        #tau = 10  # maneuvrability coefficient
        # np.matrix(np.dot(F(periode,self.state.shape[0]),self.state))
        n = 10#degré de liberté de l'extension
        A = np.identity(self.d)/np.sqrt(n)#transitio de l'extension //voir papier de Li
        x_pred = F(periode, self.x.shape[0])@self.x
        P_pred = np.dot(F(periode, self.x.shape[0]), np.dot(self.P, F(periode, self.x.shape[0]).T)) + Q(periode, self.x.shape[0],5)
        _lambda = self.v-2*self.d - 2
        
        v = 2*n*(_lambda+1)*(_lambda-1)*(_lambda-2)/(_lambda*_lambda*(_lambda+n))+2*self.d+4#self.v*np.exp(-periode/tau)
        
        #Attention! que se passe-t-il si 2*self.d-2>v?
        V_ = self.X #(self.v -2*self.d-2)*??
        V = n *(v-2*self.d-2)/_lambda*A@V_ @A.T
       
        
        
        X_pred =  V#♦(v-2*self.d - 2)/(self.v - 2*self.d - 2) * self.X

        # self.location.setXYZ(float(x[0]),float(x[2]),0.0)
        #self.time = time
        # self.updateCovariance()
        return x_pred, P_pred, X_pred, v

    def updateCovariance(self):

        # update heading et velocity en même temps

        # direction dans le sens anti-horaire
        self.heading = (np.pi/2-math.atan2(self.x[3], self.x[1]))*180/np.pi
        self.velocity = float(
            np.sqrt(np.power(self.x[1], 2.0) + np.power(self.x[3], 2.0)))

        lmbda, u = np.linalg.eig(self.P)

        Point = Position()
#        print('-----------------------------------------')
#        print(self.P)
#        print('valeur prores')
#        print(lmbda)
#        print('valeur prores')
# 
#        idx = np.argsort(lmbda)#lmbda.argsort()[::-1]   
#        lmbda = lmbda[idx]
#        u = u[:,idx]
#        print(idx)
#        print('valeur prores')
#        print(lmbda)
        Point.setXYZ(float(self.x[0]+math.sqrt(np.abs(lmbda[0]))),
                     float(self.x[2]+math.sqrt(np.abs(lmbda[2]))), 0.0,'ENU')
        Point2 = Position()
        Point2.setXYZ(float(self.x[0]), float(self.x[2]), 0.0,'ENU')

        self.sigmaX = Point.latitude - Point2.latitude
        self.sigmaY = Point.longitude - Point2.longitude

        if self.sigmaX > self.sigmaY:
            self.angle = math.atan2(u[2, 0], u[0, 0])
        else:
            self.angle = math.atan2(u[2, 2], u[0, 2])

        if self.mode == _dim(1):
            Point = Position()
            Point.setXYZ(float(self.x[1]+math.sqrt(np.abs(lmbda[1]))),
                         float(self.x[3]+math.sqrt(np.abs(lmbda[3]))), 0.0,'ENU')
            Point2 = Position()
            Point2.setXYZ(float(self.x[1]), float(self.x[3]), 0.0,'ENU')
            self.sigmaVX = Point.latitude - Point2.latitude
            self.sigmaVY = Point.longitude - Point2.longitude
            self.covarianceWGS84 = np.zeros((4, 4))
            self.covarianceWGS84[0, 0] = self.sigmaX**2
            self.covarianceWGS84[1, 1] = self.sigmaVX**2
            self.covarianceWGS84[2, 2] = self.sigmaY**2
            self.covarianceWGS84[3, 3] = self.sigmaVY**2
            self.covarianceWGS84 = u@np.diag(
                [self.sigmaX**2, self.sigmaVX**2, self.sigmaY**2, self.sigmaVY**2])@u.T

    def estimation(self, xPred, PPred, XPred, v, _cluster, _time):

        n = len(_cluster)

        z, Z = self.detection(_cluster)
        z_parameter = 1/4

        if self.mode == _dim(1):
            #Approche Rong-Li
            
            R = np.zeros((2, 2))

            for _dot in _cluster:
                R += _dot.R_XY
            R = R/n

            H = np.zeros([2, 4])
            H[0, 0] = 1
            H[1, 2] = 1
            
            X_ = XPred# / (v-self.d*2-2) ????
                   
#            print('======')
            B =   sqrtm((z_parameter*X_+R))*sqrtm (np.linalg.inv(X_))
#            print(sqrtm((z_parameter*X_+R)))
#            print(sqrtm (np.linalg.inv(X_)))
#            print(B)
            In = z - np.dot(H, xPred)
            
            Intilde = np.outer(In,In)
            
     
            
            S = np.dot(H, np.dot(PPred, H.T)) + np.linalg.det(B) / n #la puissance sur det(B) a été supprimée car d/2 == 1
            
            K = np.dot(PPred, np.dot(H.T, np.linalg.inv(S)))
            S_1 = np.linalg.inv(S)
            
            NPred =sqrtm(S_1)@Intilde@ sqrtm(S_1).T
            B_1 = np.linalg.inv(B)
            ZPred =B_1@Z@B_1.T
            
#            X = XPred / (v-self.d*2-2)
#
#            YPred = z_parameter*X + R
#
#            In = z - np.dot(H, xPred)
#
#            Intilde = In@In.T
#
#            S = YPred/n + np.dot(H, np.dot(PPred, H.T))
#
#            K = np.dot(PPred, np.dot(H.T, np.linalg.inv(S)))
#
#            NPred = np.sqrt(X)@np.linalg.inv(np.sqrt(S))@ Intilde @np.linalg.inv(np.sqrt(S)).T@np.sqrt(X).T
#
#            ZPred = np.sqrt(X)@np.linalg.inv(np.sqrt(YPred))@Z@np.linalg.inv(np.sqrt(YPred)).T@np.sqrt(X).T

            self.x = np.matrix(xPred + np.dot(K, In))
            self.P = PPred - K@S@K.T
            self.v = v + n
            self.X = (XPred + NPred + ZPred)#/(self.v -2*self.d-2)
            

            self.location.setXYZ(float(self.x[0]), float(self.x[2]), 0.0, 'ENU')

            print(["PPred", PPred])
            print(["self.P", self.P])
            print(["S", S])
            print(["R",R])
            print(['np.linalg.inv(S)',S_1])
            print(["X", self.X])
            print(["XPred", XPred])
            print(["ZPred", ZPred])
            print(["Intilde", Intilde])
            print(["NPred", NPred])
            print(["B", B])
#            print(["v-self.d*2-2", v-self.d*2-2])
#            print([" self.d ", self.d])
#            print(["v", v])
            self.updateCovariance()
            self.time = _time

    def getLocationWGS84(self):
        M = np.zeros((1, 2))
        WGS84 = np.zeros((1, 2))
        if self.mode == _dim(1):
            M = [self.state[0, 0], self.state[2, 0]]
        elif self.mode == _dim(1):
            M = [self.state[0, 0], self.state[2, 0], self.state[4, 0]]
        pt = Position()
        pt.setXYZ(float(M[0]), float(M[1]), 0.0)
        WGS84 = [pt.longitude, pt.latitude]
        return WGS84

    def getLocation(self):
        M = np.zeros((1, 2))
        if self.mode == _dim(1):
            M = [self.state[0, 0], self.state[2, 0]]
        elif self.mode == _dim(1):
            M = [self.state[0, 0], self.state[2, 0], self.state[4, 0]]
        return M

    def getVelocity(self):
        M = np.zeros((1, 2))
        if self.mode == _dim(1):
            M = [self.state[1, 0], self.state[3, 0]]
            # print('here!',M)
        elif self.mode == _dim(2):
            M = np.zeros((1, 3))
            M = [self.state[1, 0], self.state[3, 0], self.state[5, 0]]

        return np.linalg.norm(M)

    def getHeading(self):
        M = np.zeros((1, 2))
        M = [self.state[1, 0], self.state[3, 0]]

        return 90 - np.arctan2(M[1], M[0])*180/np.pi
