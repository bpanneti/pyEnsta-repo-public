# -*- coding: utf-8 -*-
"""
Created on Sat Jul 27 11:56:09 2019

@author: bpanneti
"""
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtOpenGL import *
from PyQt5.QtWidgets import *
from enum import Enum, unique
from target import TARGET_TYPE
import numpy as np


from point import Position
numberScan = -1
nmberPlot  = -1
global numberTrack        
numberTrack  = -1 
        
class PLOTType(Enum):
    NOTYPE          = 0
    POLAR           = 1
    ANGULAR         = 2
    DISTANCE        = 3
    SPHERICAL       = 4
    ANGULAR2D       = 5
    POLAR_SQUIRE    = 6
    EVENT           = 7
    PIR_EVENT       = 8
    ANGULAR_TRACK   = 9
    ANGULAR2D_TRACK = 10
    SPHERICAL_TRACK = 11
    POLAR_TRACK     = 12

class State(object):
    def __init__(self,idScan = 0, rho = 0.0, theta = 0.0,phi = 0.0,  sigma_rho = 0.0, sigma_theta = 0.0, sigma_phi=0.0):
        global    numberTrack
        numberTrack+=1
        self.rho            = rho
        self.theta          = theta
        self.phi            = phi
        self.sigma_rho      = sigma_rho
        self.sigma_theta    = sigma_theta
        self.sigma_phi      = sigma_phi
        self.idScan         = idScan
        self.idSensor       = ''
        self.dateTime       = QDateTime()
        self.doppler        = 0
        self.sigma_doppler  = 0
        self.id             = numberTrack
        self.type           = PLOTType.NOTYPE
        self.idTarget       = -1
        self.Classification = "UNKNOWN"
        self.ProbaClassification = 1.0
        self.Position       = Position()
        self.R              = np.zeros((2,2))
        self.z              = np.zeros((2,1))
        self.R_XY           = np.zeros((2,2))
        self.z_XY           = np.zeros((2,1))
        self.width          = 0 #largeur de l'ellipse d'incertitude
        self.height         = 0 #hauteur de l'ellipse d'incertitude
        self.angle          = 0 #orientation de l'ellipse d'incertitude dans le sens anti horaire en degré
     
        
    def updateLocation(self,  _scan ):

            if self.type == PLOTType.SPHERICAL and _scan.sensorOrientation!=None:
                self.R              = np.zeros((3,3))
                self.z              = np.zeros((3,1))
                self.R_XY           = np.zeros((3,3))
                self.z_XY           = np.zeros((3,1))
                self.z[0]       = self.rho
                self.z[1]       = self.theta
                self.z[2]       = self.phi
                self.R[0,0]     = self.sigma_rho   *self.sigma_rho
                self.R[1,1]     = self.sigma_theta *self.sigma_theta
                self.R[2,2]     = self.sigma_phi   *self.sigma_phi
                
                #converted measurement
                azimut              = np.pi/2 -  (_scan.sensorOrientation.yaw  + self.theta)   *np.pi/180
                site                = self.phi #* np.pi/180
                
                sensorLoc           =    np.array([_scan.sensorPosition.x_ENU, _scan.sensorPosition.y_ENU]) 
                m_ec_azimut         =    self.sigma_theta * np.pi/180
                m_ec_site           =    self.sigma_phi * np.pi/180
                
                self.z_XY[0] = self.rho*np.cos(azimut)*np.cos(site) - self.rho*np.cos(azimut)*np.cos(site)*(np.exp(-pow(m_ec_azimut,2.0))*np.exp(-pow(m_ec_site,2.0)) - np.exp(1/2*(-pow(m_ec_azimut,2.0)))*np.exp(1/2*(-pow(m_ec_site,2.0)))) + sensorLoc[0];
                self.z_XY[1] = self.rho*np.sin(azimut)*np.cos(site) - self.rho*np.sin(azimut)*np.cos(site)*(np.exp(-pow(m_ec_azimut,2.0))*np.exp(-pow(m_ec_site,2.0)) - np.exp(1/2*(-pow(m_ec_azimut,2.0)))*np.exp(1/2*(-pow(m_ec_site,2.0)))) + sensorLoc[1];
                self.z_XY[2] = self.rho*np.sin(site) - self.rho*np.sin(site)*(1 -  np.exp(1/2*(-pow(m_ec_site,2.0))))  ;
    
             
                Alpha_x = pow(np.sin(azimut),2.0)*np.sinh( pow(m_ec_azimut,2.0)) + pow(np.cos(azimut),2.0)*np.cosh(pow(m_ec_azimut,2.0));
                Alpha_y = pow(np.sin(azimut),2.0)*np.cosh( pow(m_ec_azimut,2.0)) + pow(np.cos(azimut),2.0)*np.sinh(pow(m_ec_azimut,2.0));
                Alpha_z = pow(np.sin(site),2.0)*np.cosh(pow(m_ec_site,2.0))  + pow(np.cos(site),2.0)*np.sinh(pow(m_ec_site,2.0));
                Alpha_xy = pow(np.sin(site),2.0)*np.sinh(pow(m_ec_site,2.0))  + pow(np.cos(site),2.0)*np.cosh(pow(m_ec_site,2.0));
    
                Beta_x =  pow(np.sin(azimut),2.0)*np.sinh(2*pow(m_ec_azimut,2.0))  + pow(np.cos(azimut),2.0)*np.cosh(2*pow(m_ec_azimut,2.0)) ;
                Beta_y =  pow(np.sin(azimut),2.0)*np.cosh(2*pow(m_ec_azimut,2.0))  + pow(np.cos(azimut),2.0)*np.sinh(2*pow(m_ec_azimut,2.0)) ;
                Beta_z =  pow(np.sin(site),2.0)*np.cosh(2*pow(m_ec_site,2.0))  + pow(np.cos(site),2.0)*np.sinh(2*pow(m_ec_site,2.0)) ;
                Beta_xy = pow(np.sin(site),2.0)*np.sinh(2*pow(m_ec_site,2.0))  + pow(np.cos(site),2.0)*np.cosh(2*pow(m_ec_site,2.0)) ;
    
                self.R_XY[0,0]= ( pow(self.rho,2.0) *(Beta_x*Beta_xy - Alpha_x*Alpha_xy) + pow(self.sigma_rho,2.0) * (2*Beta_x*Beta_xy - Alpha_x*Alpha_xy))*np.exp(-2*pow(m_ec_azimut,2.0))*np.exp(-2*pow(m_ec_site,2.0)) 
                self.R_XY[1,1]= ( pow(self.rho,2.0) *(Beta_y*Beta_xy - Alpha_y*Alpha_xy) + pow(self.sigma_rho,2.0) * (2*Beta_y*Beta_xy - Alpha_y*Alpha_xy))*np.exp(-2*pow(m_ec_azimut,2.0))*np.exp(-2*pow(m_ec_site,2.0)) 
                self.R_XY[0,1]= ( pow(self.rho,2.0) *( Beta_xy -  Alpha_xy * np.exp(pow(m_ec_azimut,2.0))) +pow(self.sigma_rho,2.0) * (2*Beta_xy -  Alpha_xy * np.exp(pow(m_ec_azimut,2.0)) ))*np.exp(-2*pow(m_ec_azimut,2.0))*\
                np.sin(azimut)*np.cos(azimut)*np.exp(-4*pow(m_ec_azimut,2.0))*np.exp(-2*pow(m_ec_site,2.0)) 
    
                self.R_XY[0,2]= ( pow(self.rho,2.0) *(1-np.exp(pow(m_ec_site,2.0))) + pow(self.sigma_rho,2.0) *(2-np.exp(pow(m_ec_site,2.0))) ) * np.cos(azimut)*np.cos(site)*np.sin(site)*np.exp(-pow(m_ec_azimut,2.0))*np.exp(-4*pow(m_ec_site,2.0));
                self.R_XY[1,2]= ( pow(self.rho,2.0) *(1-np.exp(pow(m_ec_site,2.0))) + pow(self.sigma_rho,2.0) *(2-np.exp(pow(m_ec_site,2.0))) ) * np.sin(azimut)*np.cos(site)*np.sin(site)*np.exp(-pow(m_ec_azimut,2.0))*np.exp(-4*pow(m_ec_site,2.0));
                self.R_XY[2,2]= ( pow(self.rho,2.0) * (Beta_z-Alpha_z)+ pow(self.sigma_rho,2.0)*(2*Beta_z-Alpha_z))*np.exp(-2*pow(m_ec_site,2.0));
                self.R_XY[1,0]=self.R_XY[0,1];
                self.R_XY[2,0]=self.R_XY[0,2];
                self.R_XY[2,1]=self.R_XY[1,2];
                
                
                self.Position.setXYZ( float(self.z_XY[0]),float(self.z_XY[1]),float(self.z_XY[2]),'ENU')
                  
                V,D = np.linalg.eig(self.R_XY)
                self.width  =  np.sqrt(V[0])
                self.height =  np.sqrt(V[1])
                self.angle  =  np.arccos(D[0,0])*180/np.pi
                
            if self.type == PLOTType.POLAR and _scan.sensorOrientation!=None: 
       
                self.z[0]       = self.rho
                self.z[1]       = self.theta
                self.R[0,0]     = self.sigma_rho*self.sigma_rho
                self.R[1,1]     = self.sigma_theta*self.sigma_theta

 
            angleTrigo          =    np.pi/2 -  (_scan.sensor.orientationBiased.yaw  + self.theta)   *np.pi/180 
            sensorLoc           =    np.array([_scan.sensor.positionBiased.x_ENU, _scan.sensor.positionBiased.y_ENU]) 
            sigma_thetaTrigo    =    self.sigma_theta * np.pi/180   
            
            self.z_XY[0]        = sensorLoc[0] + self.rho*np.cos(angleTrigo)*(1+( 1-np.exp(-0.5* sigma_thetaTrigo*sigma_thetaTrigo))) # -   self.rho*np.cos(angleTrigo) - np.exp(- 0.5* sigma_thetaTrigo*sigma_thetaTrigo)) 
            self.z_XY[1]        = sensorLoc[1] + self.rho*np.sin(angleTrigo)*(1+( 1-np.exp(-0.5* sigma_thetaTrigo*sigma_thetaTrigo))) # -   self.rho*np.sin(angleTrigo) *( np.exp(- sigma_thetaTrigo*sigma_thetaTrigo))# - np.exp(- 0.5* sigma_thetaTrigo*sigma_thetaTrigo)) 
           
            
            self.R_XY[0,0]  =  - pow(self.rho,2.0) *np.exp(-pow(sigma_thetaTrigo,2.0)) * pow(np.cos(angleTrigo),2.0) +0.5*(pow(self.rho,2.0) + pow(self.sigma_rho,2.0)) \
            *                   (1 + np.cos(2*angleTrigo)*np.exp(-2*pow(sigma_thetaTrigo,2.0) ));
    
    
            self.R_XY[1,1]  = - pow(self.rho,2.0) *np.exp(-pow(sigma_thetaTrigo,2.0)) * pow(np.sin(angleTrigo),2.0)+0.5*(pow(self.rho,2.0) + pow(self.sigma_rho,2.0))\
            *                   (1 - np.cos(2*angleTrigo)*np.exp(-2*pow(sigma_thetaTrigo,2.0) ));


            self.R_XY[1,0]  =- pow(self.rho,2.0) *np.exp(-pow(sigma_thetaTrigo,2.0)) * np.cos(angleTrigo)* np.sin(angleTrigo) + 0.5*(pow(self.rho,2.0) + pow(self.sigma_rho,2.0))\
            *                  (np.sin(2*angleTrigo)*np.exp(-2*pow(sigma_thetaTrigo,2.0) ));
            
             
      
    
            self.R_XY[0,1]      = self.R_XY[1,0]           
            
            self.Position.setXYZ( float(self.z_XY[0]),float(self.z_XY[1]),0.0,'ENU')
             
            V,D = np.linalg.eig(self.R_XY)
            a = 0
            if V[0]<V[1]:
                a = 1
            self.width  =  2*np.sqrt(np.abs(5.991*V[0]))
            self.height =  2*np.sqrt(np.abs(5.991*V[1]))       
            self.angle  =  np.arctan2(D[1,a],D[0,a])*180/np.pi
            
            
class Plot(object):
    def __init__(self,idScan = 0, rho = 0.0, theta = 0.0,phi = 0.0,  sigma_rho = 0.0, sigma_theta = 0.0, sigma_phi=0.0):
        global nmberPlot        
        nmberPlot +=1        
        self.rho            = rho
        self.theta          = theta
        self.phi            = phi
        self.sigma_rho      = sigma_rho
        self.sigma_theta    = sigma_theta
        self.sigma_phi      = sigma_phi
        self.idScan         = idScan
        self.idSensor       = ''
        self.dateTime       = QDateTime()
        self.doppler        = 0
        self.sigma_doppler  = 0
        self.id             = nmberPlot
        self.R              = np.zeros((2,2))
        self.z              = np.zeros((2,1))
        self.R_XY           = np.zeros((2,2))
        self.z_XY           = np.zeros((2,1))
        self.width          = 0 #largeur de l'ellipse d'incertitude
        self.height         = 0 #hauteur de l'ellipse d'incertitude
        self.angle          = 0 #orientation de l'ellipse d'incertitude dans le sens anti horaire en degré
        self.pfa            = 0
        self.pd             = 0
        self.Position       = Position()
        self.type           = PLOTType.NOTYPE
        self.idTarget       = -1
#        self.width          = -1
#        self.height         = -1
#        self.angle          = -1
        self.Classification = "UNKNOWN"
        self.ProbaClassification = 1.0
        self.info_1         =  []
        self.value_info_1   =  []
        self.info_2         =  []
        self.value_info_2   =  []
        self.url            =  str('')

    def addImageInfo(self,_url):
        self.url = _url;
        
        
    def updateLocation(self,  _scan ):

        if self.type == PLOTType.SPHERICAL and _scan.sensorOrientation!=None:
            self.R              = np.zeros((3,3))
            self.z              = np.zeros((3,1))
            self.R_XY           = np.zeros((3,3))
            self.z_XY           = np.zeros((3,1))
            self.z[0]       = self.rho
            self.z[1]       = self.theta
            self.z[2]       = self.phi
            self.R[0,0]     = self.sigma_rho   *self.sigma_rho
            self.R[1,1]     = self.sigma_theta *self.sigma_theta
            self.R[2,2]     = self.sigma_phi   *self.sigma_phi
            
            #converted measurement
            azimut              = np.pi/2 -  (_scan.sensorOrientation.yaw  + self.theta)   *np.pi/180
            site                = self.phi #* np.pi/180
            
            sensorLoc           =    np.array([_scan.sensorPosition.x_ENU, _scan.sensorPosition.y_ENU]) 
            m_ec_azimut         =    self.sigma_theta * np.pi/180
            m_ec_site           =    self.sigma_phi * np.pi/180
            
            self.z_XY[0] = self.rho*np.cos(azimut)*np.cos(site) - self.rho*np.cos(azimut)*np.cos(site)*(np.exp(-pow(m_ec_azimut,2.0))*np.exp(-pow(m_ec_site,2.0)) - np.exp(1/2*(-pow(m_ec_azimut,2.0)))*np.exp(1/2*(-pow(m_ec_site,2.0)))) + sensorLoc[0];
            self.z_XY[1] = self.rho*np.sin(azimut)*np.cos(site) - self.rho*np.sin(azimut)*np.cos(site)*(np.exp(-pow(m_ec_azimut,2.0))*np.exp(-pow(m_ec_site,2.0)) - np.exp(1/2*(-pow(m_ec_azimut,2.0)))*np.exp(1/2*(-pow(m_ec_site,2.0)))) + sensorLoc[1];
            self.z_XY[2] = self.rho*np.sin(site) - self.rho*np.sin(site)*(1 -  np.exp(1/2*(-pow(m_ec_site,2.0))))  ;

         
            Alpha_x = pow(np.sin(azimut),2.0)*np.sinh( pow(m_ec_azimut,2.0)) + pow(np.cos(azimut),2.0)*np.cosh(pow(m_ec_azimut,2.0));
            Alpha_y = pow(np.sin(azimut),2.0)*np.cosh( pow(m_ec_azimut,2.0)) + pow(np.cos(azimut),2.0)*np.sinh(pow(m_ec_azimut,2.0));
            Alpha_z = pow(np.sin(site),2.0)*np.cosh(pow(m_ec_site,2.0))  + pow(np.cos(site),2.0)*np.sinh(pow(m_ec_site,2.0));
            Alpha_xy = pow(np.sin(site),2.0)*np.sinh(pow(m_ec_site,2.0))  + pow(np.cos(site),2.0)*np.cosh(pow(m_ec_site,2.0));

            Beta_x =  pow(np.sin(azimut),2.0)*np.sinh(2*pow(m_ec_azimut,2.0))  + pow(np.cos(azimut),2.0)*np.cosh(2*pow(m_ec_azimut,2.0)) ;
            Beta_y =  pow(np.sin(azimut),2.0)*np.cosh(2*pow(m_ec_azimut,2.0))  + pow(np.cos(azimut),2.0)*np.sinh(2*pow(m_ec_azimut,2.0)) ;
            Beta_z =  pow(np.sin(site),2.0)*np.cosh(2*pow(m_ec_site,2.0))  + pow(np.cos(site),2.0)*np.sinh(2*pow(m_ec_site,2.0)) ;
            Beta_xy = pow(np.sin(site),2.0)*np.sinh(2*pow(m_ec_site,2.0))  + pow(np.cos(site),2.0)*np.cosh(2*pow(m_ec_site,2.0)) ;

            self.R_XY[0,0]= ( pow(self.rho,2.0) *(Beta_x*Beta_xy - Alpha_x*Alpha_xy) + pow(self.sigma_rho,2.0) * (2*Beta_x*Beta_xy - Alpha_x*Alpha_xy))*np.exp(-2*pow(m_ec_azimut,2.0))*np.exp(-2*pow(m_ec_site,2.0)) 
            self.R_XY[1,1]= ( pow(self.rho,2.0) *(Beta_y*Beta_xy - Alpha_y*Alpha_xy) + pow(self.sigma_rho,2.0) * (2*Beta_y*Beta_xy - Alpha_y*Alpha_xy))*np.exp(-2*pow(m_ec_azimut,2.0))*np.exp(-2*pow(m_ec_site,2.0)) 
            self.R_XY[0,1]= ( pow(self.rho,2.0) *( Beta_xy -  Alpha_xy * np.exp(pow(m_ec_azimut,2.0))) +pow(self.sigma_rho,2.0) * (2*Beta_xy -  Alpha_xy * np.exp(pow(m_ec_azimut,2.0)) ))*np.exp(-2*pow(m_ec_azimut,2.0))*\
            np.sin(azimut)*np.cos(azimut)*np.exp(-4*pow(m_ec_azimut,2.0))*np.exp(-2*pow(m_ec_site,2.0)) 

            self.R_XY[0,2]= ( pow(self.rho,2.0) *(1-np.exp(pow(m_ec_site,2.0))) + pow(self.sigma_rho,2.0) *(2-np.exp(pow(m_ec_site,2.0))) ) * np.cos(azimut)*np.cos(site)*np.sin(site)*np.exp(-pow(m_ec_azimut,2.0))*np.exp(-4*pow(m_ec_site,2.0));
            self.R_XY[1,2]= ( pow(self.rho,2.0) *(1-np.exp(pow(m_ec_site,2.0))) + pow(self.sigma_rho,2.0) *(2-np.exp(pow(m_ec_site,2.0))) ) * np.sin(azimut)*np.cos(site)*np.sin(site)*np.exp(-pow(m_ec_azimut,2.0))*np.exp(-4*pow(m_ec_site,2.0));
            self.R_XY[2,2]= ( pow(self.rho,2.0) * (Beta_z-Alpha_z)+ pow(self.sigma_rho,2.0)*(2*Beta_z-Alpha_z))*np.exp(-2*pow(m_ec_site,2.0));
            self.R_XY[1,0]=self.R_XY[0,1];
            self.R_XY[2,0]=self.R_XY[0,2];
            self.R_XY[2,1]=self.R_XY[1,2];
            
            
            self.Position.setXYZ( float(self.z_XY[0]),float(self.z_XY[1]),float(self.z_XY[2]),'ENU')
              
            V,D = np.linalg.eig(self.R_XY)
            self.width  =  np.sqrt(V[0])
            self.height =  np.sqrt(V[1])
            self.angle  =  np.arccos(D[0,0])*180/np.pi
            
        if self.type == PLOTType.POLAR and _scan.sensorOrientation!=None: 
   
            self.z[0]       = self.rho
            self.z[1]       = self.theta
            self.R[0,0]     = self.sigma_rho*self.sigma_rho
            self.R[1,1]     = self.sigma_theta*self.sigma_theta

            #converted measurement
       
            
#            print(_scan.sensor.positionBiased.x_ENU)
#            print(_scan.sensor.position.x_ENU)
#            print(_scan.sensor.positionBiased.y_ENU)
#            print(_scan.sensor.position.y_ENU)
#            print(_scan.sensor.orientationBiased.yaw )
#            print(_scan.sensor.orientation.yaw )
            angleTrigo          =    np.pi/2 -  (_scan.sensor.orientationBiased.yaw  + self.theta)   *np.pi/180 
            sensorLoc           =    np.array([_scan.sensor.positionBiased.x_ENU, _scan.sensor.positionBiased.y_ENU]) 
            sigma_thetaTrigo    =    self.sigma_theta * np.pi/180   
            
            self.z_XY[0]        = sensorLoc[0] + self.rho*np.cos(angleTrigo)*(1+( 1-np.exp(-0.5* sigma_thetaTrigo*sigma_thetaTrigo))) # -   self.rho*np.cos(angleTrigo) - np.exp(- 0.5* sigma_thetaTrigo*sigma_thetaTrigo)) 
            self.z_XY[1]        = sensorLoc[1] + self.rho*np.sin(angleTrigo)*(1+( 1-np.exp(-0.5* sigma_thetaTrigo*sigma_thetaTrigo))) # -   self.rho*np.sin(angleTrigo) *( np.exp(- sigma_thetaTrigo*sigma_thetaTrigo))# - np.exp(- 0.5* sigma_thetaTrigo*sigma_thetaTrigo)) 
           
            
            self.R_XY[0,0]  =  - pow(self.rho,2.0) *np.exp(-pow(sigma_thetaTrigo,2.0)) * pow(np.cos(angleTrigo),2.0) +0.5*(pow(self.rho,2.0) + pow(self.sigma_rho,2.0)) \
            *                   (1 + np.cos(2*angleTrigo)*np.exp(-2*pow(sigma_thetaTrigo,2.0) ));
    
    
            self.R_XY[1,1]  = - pow(self.rho,2.0) *np.exp(-pow(sigma_thetaTrigo,2.0)) * pow(np.sin(angleTrigo),2.0)+0.5*(pow(self.rho,2.0) + pow(self.sigma_rho,2.0))\
            *                   (1 - np.cos(2*angleTrigo)*np.exp(-2*pow(sigma_thetaTrigo,2.0) ));


            self.R_XY[1,0]  =- pow(self.rho,2.0) *np.exp(-pow(sigma_thetaTrigo,2.0)) * np.cos(angleTrigo)* np.sin(angleTrigo) + 0.5*(pow(self.rho,2.0) + pow(self.sigma_rho,2.0))\
            *                  (np.sin(2*angleTrigo)*np.exp(-2*pow(sigma_thetaTrigo,2.0) ));
            
             
      
    
            self.R_XY[0,1]      = self.R_XY[1,0]           
            
            self.Position.setXYZ( float(self.z_XY[0]),float(self.z_XY[1]),0.0,'ENU')
             
            V,D = np.linalg.eig(self.R_XY)
            a = 0
            if V[0]<V[1]:
                a = 1
            self.width  =  2*np.sqrt(np.abs(5.991*V[0]))
            self.height =  2*np.sqrt(np.abs(5.991*V[1]))
            
            self.angle  =  np.arctan2(D[1,a],D[0,a])*180/np.pi

        
class Scan(object):

      def __init__(self,datetTime = QDateTime(),sensor = None):

        global numberScan  
        numberScan += 1
        self.id             = numberScan
        self.sensor         = sensor
        self.plots          = []
        self.tracks          = []
        self.dateTime       = datetTime
        self.plotType       = PLOTType.NOTYPE
        self.sensorPosition = None
        self.sensorOrientation = None

        #graphic data
        
        self.plotsObj       = None
        self.ellipsesObj    = None

      def printInfo(self):
          print("---> Scan :")
          print(self.id)
          if self.sensor != None:
              print(self.sensor.id)
          print(self.plotType.name)
          print(self.plots)
          print(self.tracks)
          print(self.dateTime.toString("HH:mm:ss.z"))
          print("---> Fin")
                         

      def addFa(self,FA,time = QDateTime(),FAClasses=[],PAClasses=[]  ,FAInfos =[] ):
          if self.sensor == None : 
              return  
          if self.sensor.node == None :
             return
          if self.sensorPosition==None or self.sensorOrientation == None:
              return
      
          FalseAlarms = np.array(FA)
          
          if FalseAlarms.shape[1] > 50:
              print('trop de fa')
              return
  
          sigma_rho   = None
          sigma_theta = None
          sigma_phi   = None
          distanceMin = None
          distanceMax = None
          pd          = None
          pfa         = None
         
       

  
                 
#          if flag == False:
#             print(("no cover founded for the target %s")%(str(FAClass)))
#             return 
             
          for j in range(0,FalseAlarms.shape[1]):
             flag = False
             _plot = Plot() 
             _plot.idScan = self.id
             _plot.type  = self.plotType
             
             infos      = FAInfos[j]
             
             FAClass     = FAClasses[j] 
             if self.sensor.sensorCoverage:
                 for _cover in self.sensor.sensorCoverage:
                     if _cover.name  == FAClass or  flag==False :
                         distanceMin    =  _cover.distanceMin
                         distanceMax    =  _cover.distanceMax
                         pfa            =  _cover.parameters.pfa
                         pd             =  _cover.parameters.pd
                         sigma_rho      =  _cover.parameters.sigmaRho
                         sigma_theta    =  _cover.parameters.sigmaTheta
                         sigma_phi      =  _cover.parameters.sigmaPhi
                         flag = True
 
             _plot.pfa   = pfa
             _plot.pd    = pd    
             if self.plotType == PLOTType.POLAR or self.plotType == PLOTType.DISTANCE:
                 _plot.rho            = FalseAlarms[0,j]
                 _plot.sigma_rho      = sigma_rho
             # angle par rapport au nord géographique   
             if self.plotType == PLOTType.POLAR or self.plotType == PLOTType.ANGULAR:
                 _plot.theta  = FalseAlarms[1,j]  * 180/np.pi 
                 _plot.sigma_theta    = sigma_theta #* 180/np.pi
             
             
             if self.plotType == PLOTType.SPHERICAL:
                 _plot.theta          = FalseAlarms[1,j] * 180/np.pi  
                 _plot.sigma_theta    = sigma_theta #* 180/np.pi
                 _plot.rho            = FalseAlarms[0,j]
                 _plot.sigma_rho      = sigma_rho
                 _plot.phi            = FalseAlarms[2,j]* 180/np.pi 
                 _plot.sigma_phi      = sigma_phi #* 180/np.pi
             
             if self.plotType == PLOTType.ANGULAR2D:
                _plot.phi             = FalseAlarms[2,j]* 180/np.pi  #+ float(2*self.params[2] *np.pi/180 *(self.sensor.randomSeeded.rand(1)-0.5))
                _plot.sigma_phi      = sigma_phi  #* 180/np.pi
                _plot.theta          = FalseAlarms[1,j] * 180/np.pi  
                _plot.sigma_theta    = sigma_theta    #* 180/np.pi
                for _type in TARGET_TYPE:
                    if _type.value.value == FAClasses[j]: 
                        _plot.Classification      = _type.name
                        
             _plot.ProbaClassification = PAClasses[j]
             _plot.updateLocation(self)
             _plot.dateTime         = time
     
             if infos.size == 2:
                 _plot.info_1         =  infos[0]
                 _plot.value_info_1   =  infos[1]
                        
                 
             if infos.size == 4:    
                 _plot.info_1          =  infos[0,0]
                 _plot.value_info_1    =  infos[0,1]
                 _plot.info_2          =  infos[1,0]
                 _plot.value_info_2    =  infos[1,1]
                 
  
             
             self.plots.append(_plot) 
      def addFalseTrack(self,FA,time = QDateTime(),FAClasses=[],PAClasses=[]  ,FAInfos =[] ):
      
          if self.sensor == None : 
              return  
          if self.sensor.node == None :
             return
          if self.sensorPosition==None or self.sensorOrientation == None:
              return
      
          FalseAlarms = np.array(FA)
          
          if FalseAlarms.shape[1] > 50:
              print('trop de fa')
              return
  
          sigma_rho   = 1
          sigma_theta = 0.1
          sigma_phi   = 0.1 
          distanceMin = None
          distanceMax = None
          pd          = None
          pfa         = None
         
       

  
                 
#          if flag == False:
#             print(("no cover founded for the target %s")%(str(FAClass)))
#             return 
             
          for j in range(0,FalseAlarms.shape[1]):
             flag = False
             _state = State()
             _state.idScan = self.id
             _state.type  = self.plotType
             
   
 
   
             if self.plotType == PLOTType.POLAR_TRACK  :
                 _state.rho            = FalseAlarms[0,j]
                 _state.sigma_rho      = sigma_rho
             # angle par rapport au nord géographique   
             if self.plotType == PLOTType.POLAR_TRACK or self.plotType == PLOTType.ANGULAR_TRACK:
                 _state.theta  = FalseAlarms[1,j]  * 180/np.pi 
                 _state.sigma_theta    = sigma_theta #* 180/np.pi
             
             
             if self.plotType == PLOTType.SPHERICAL_TRACK:
                 _state.theta          = FalseAlarms[1,j] * 180/np.pi  
                 _state.sigma_theta    = sigma_theta #* 180/np.pi
                 _state.rho            = FalseAlarms[0,j]
                 _state.sigma_rho      = sigma_rho
                 _state.phi            = FalseAlarms[2,j]* 180/np.pi 
                 _state.sigma_phi      = sigma_phi #* 180/np.pi
             
             if self.plotType == PLOTType.ANGULAR2D_TRACK:
                _state.phi            = FalseAlarms[2,j]* 180/np.pi  #+ float(2*self.params[2] *np.pi/180 *(self.sensor.randomSeeded.rand(1)-0.5))
                _state.sigma_phi      = sigma_phi  #* 180/np.pi
                _state.theta          = FalseAlarms[1,j] * 180/np.pi  
                _state.sigma_theta    = sigma_theta    #* 180/np.pi
                for _type in TARGET_TYPE:
                    if _type.value.value == FAClasses[j]: 
                        _state.Classification      = _type.name
                        
             _state.ProbaClassification = PAClasses[j]
             _state.updateLocation(self)
             _state.dateTime         = time
     
 
                 
  
             
             self.tracks.append(_state) 
      def addTrack(self,truePosition = Position(),idtarget = -1,targetClass= TARGET_TYPE.UNKNOWN,time = QDateTime(),_class= 'unknown',_probaClass = 1.0 ,infos =[],_url=''):
         if self.sensor == None : 
              return  
         if self.sensor.node == None :
             return
         
         if self.sensorPosition==None or self.sensorOrientation == None:
              return
          
         _state = State()
         
         distance_3D = self.sensorPosition.distanceToPoint(truePosition)
         _state.id   = idtarget
     
         sensorLoc   = np.array([self.sensorPosition.x_ENU, self.sensorPosition.y_ENU,self.sensorPosition.altitude]) 
         M           = np.array([truePosition.x_ENU, truePosition.y_ENU, truePosition.altitude]) 
                
         angle       = np.arctan2(M[1] - sensorLoc[1] ,M[0] - sensorLoc[0]) #sens trigonométrique
         phi         = np.arctan2(M[2] - sensorLoc[2] ,np.sqrt(np.power(M[1] - sensorLoc[1],2.0) + np.power(M[0] - sensorLoc[0],2.0)))
         theta= np.mod(np.pi/2  - self.sensorOrientation.yaw*np.pi/180 - angle  +np.pi,2*np.pi)-np.pi
         sigma_rho   = 1
         sigma_theta = 0.1
         sigma_phi   = 0.1 
         
 
    
         if self.plotType == PLOTType.SPHERICAL_TRACK:
             _state.theta          =  theta * 180/np.pi + float(sigma_theta  *0.5*(self.sensor.randomSeeded.randn(1)))
             _state.sigma_theta    =  sigma_theta #* 180/np.pi
             _state.rho            =  distance_3D  + float(sigma_rho    *0.5*(self.sensor.randomSeeded.randn(1)))
             _state.sigma_rho      =  sigma_rho
             _state.phi            =  phi* 180/np.pi    + float(sigma_phi  *0.5*(self.sensor.randomSeeded.randn(1)))
             _state.sigma_phi      =  sigma_phi #* 180/np.pi
         if self.plotType == PLOTType.ANGULAR2D_TRACK:
             _state.phi            = phi * 180/np.pi + float(sigma_theta  *(self.sensor.randomSeeded.randn(1)))
             _state.sigma_phi      = sigma_phi #* 180/np.pi
             _state.theta          = theta * 180/np.pi  + float(sigma_phi  *(self.sensor.randomSeeded.randn(1)))
             _state.sigma_theta    = sigma_theta #* 180/np.pi
         if self.plotType == PLOTType.ANGULAR_TRACK:
             _state.theta          = theta * 180/np.pi  + float(sigma_phi  *(self.sensor.randomSeeded.randn(1)))
             _state.sigma_theta    = sigma_theta #* 180/np.pi    
         if self.plotType == PLOTType.POLAR_TRACK:               
             _state.theta          =  theta * 180/np.pi + float(sigma_theta  *0.5*(self.sensor.randomSeeded.randn(1)))
             _state.sigma_theta    =  sigma_theta #* 180/np.pi
             _state.rho            =  distance_3D  + float(sigma_rho    *0.5*(self.sensor.randomSeeded.randn(1)))
             _state.sigma_rho      =  sigma_rho     
             
         _state.idScan               = self.id
         _state.type                 = self.plotType
         _state.updateLocation(self)
         _state.idTarget             = idtarget
         _state.dateTime             = time
         _state.Classification       = _class 
         _state.ProbaClassification  = _probaClass
         self.tracks.append(_state)   
         return            
      def addPlot(self,truePosition = Position(),idtarget = -1,targetClass= TARGET_TYPE.UNKNOWN,time = QDateTime(),_class= 'unknown',_probaClass = 1.0 ,infos =[],_url=''):
   

         _plot = Plot()
         
         distance_3D = self.sensorPosition.distanceToPoint(truePosition)
         
     
         sensorLoc   = np.array([self.sensorPosition.x_ENU, self.sensorPosition.y_ENU,self.sensorPosition.altitude]) 
         M           = np.array([truePosition.x_ENU, truePosition.y_ENU, truePosition.altitude]) 
                
         angle       = np.arctan2(M[1] - sensorLoc[1] ,M[0] - sensorLoc[0]) #sens trigonométrique
#         theta       = np.pi/2  - self.sensor.node.Orientation.yaw*np.pi/180 - angle 
         phi         = np.arctan2(M[2] - sensorLoc[2] ,np.sqrt(np.power(M[1] - sensorLoc[1],2.0) + np.power(M[0] - sensorLoc[0],2.0)))
       
#         if theta >= np.pi:
#            theta =  theta - 2*np.pi
#         elif theta <= - np.pi:
#            theta = 2*np.pi + theta   
 
         theta= np.mod(np.pi/2  - self.sensorOrientation.yaw*np.pi/180 - angle  +np.pi,2*np.pi)-np.pi
         sigma_rho   = None
         sigma_theta = None
         sigma_phi   = None
         distanceMin = None
         distanceMax = None
         pd          = None
         pfa         = None
         
         flag = False
 
         if self.sensor.sensorCoverage:
             for _cover in self.sensor.sensorCoverage:  
           
                 if (distanceMax == None and _cover.name == TARGET_TYPE.UNKNOWN  ) or _cover.name.name == targetClass:#"targetClass:
                     distanceMin    =  _cover.distanceMin
                     distanceMax    =  _cover.distanceMax
                     pfa            =  _cover.parameters.pfa
                     pd             =  _cover.parameters.pd
                     sigma_rho      =  _cover.parameters.sigmaRho
                     sigma_theta    =  _cover.parameters.sigmaTheta
                     sigma_phi      = _cover.parameters.sigmaPhi
                     flag = True
                     break
                 
         if flag == False:
             print(("no cover founded for the target %s")%(str(idtarget)))
             return
         _plot.pfa   = pfa
         _plot.pd    = pd
         if self.plotType == PLOTType.SPHERICAL:
             #print('# adddPlot 3 ')
             _plot.theta          =  theta * 180/np.pi + float(sigma_theta  *0.5*(self.sensor.randomSeeded.randn(1)))
             _plot.sigma_theta    =  sigma_theta #* 180/np.pi
             _plot.rho            =  distance_3D  + float(sigma_rho    *0.5*(self.sensor.randomSeeded.randn(1)))
             _plot.sigma_rho      =  sigma_rho
             _plot.phi            =  phi* 180/np.pi    + float(sigma_phi  *0.5*(self.sensor.randomSeeded.randn(1)))
             _plot.sigma_phi      =  sigma_phi #* 180/np.pi
         if self.plotType == PLOTType.POLAR or self.plotType == PLOTType.DISTANCE:  
             _plot.rho            = distance_3D  + float(sigma_rho    *0.5*(self.sensor.randomSeeded.randn(1)))
             _plot.sigma_rho      = sigma_rho
             #print(['self.params[0] :',self.params[0], ' distance: ',distance, 'bruit:', float(self.params[0]  *(self.sensor.randomSeeded.randn(1)))])
            # angle par rapport au nord géographique 
         if self.plotType == PLOTType.POLAR or self.plotType == PLOTType.ANGULAR: 
             #print(sigma_theta)
             _plot.theta          = theta * 180/np.pi + float(sigma_theta  *0.5*(self.sensor.randomSeeded.randn(1)))
             _plot.sigma_theta    = sigma_theta #* 180/np.pi
         if self.plotType == PLOTType.ANGULAR2D:
             _plot.phi            = phi * 180/np.pi + float(sigma_theta  *(self.sensor.randomSeeded.randn(1)))
             _plot.sigma_phi      = sigma_phi #* 180/np.pi
             _plot.theta          = theta * 180/np.pi  + float(sigma_phi  *(self.sensor.randomSeeded.randn(1)))
             _plot.sigma_theta    = sigma_theta #* 180/np.pi
   
         _plot.idScan               = self.id
         _plot.type                 = self.plotType
         _plot.updateLocation(self)
         _plot.idTarget             = idtarget
         _plot.dateTime             = time
         _plot.Classification       = _class 
         _plot.ProbaClassification  = _probaClass
         if infos.size == 2:
                 _plot.info_1         =  infos[0]
                 _plot.value_info_1   =  infos[1]
                        
                 
         if infos.size == 4:    
                 _plot.info_1          =  infos[0,0]
                 _plot.value_info_1    =  infos[0,1]
                 _plot.info_2          =  infos[1,0]
                 _plot.value_info_2    =  infos[1,1]
                 
                 
         _plot.addImageInfo(_url)
         self.plots.append(_plot) 
    
          
      def drawPlots(self):
    
          if self.Type == PLOTType.POLAR:
              for _plot in  self.plots:
                 x = _plot.z_XY[0] 
                 y = _plot.z_XY[1] 
                 plt.plot(x,y,'m+')
                 
             
      def toJson(self):
 
          json  = '{'+\
            '"scanId": '+str(self.id)+','+\
	         '"sensorId": "'+str(self.sensor.id)+'",'+\
            '"code": 7,'+\
            '"detection": ['
            
          for det in self.plots:
            json+= '{'+\
		           '"plotId":'+ str(det.id)+','+\
		           '"position_available": 0,'
            if self.plotType == PLOTType.ANGULAR:
                
                json+=  '"plotType": "BEARING_1D",'+\
		                  '"azimut": '+str( det.theta)+','+\
		                  '"stdAzimut": '+str(det.sigma_theta)+','+\
		                  '"VelocityType": "NOVELOCITY",'+\
		                  '"plotTime": "'+self.dateTime.toUTC().toString("yyyy-MM-dd HH:mm:ss.z") +'",'+\
		                   '"classification":"' +str(det.Classification)+'",'+\
		                  '"probaClassification": "'+str(det.ProbaClassification) +'"},'     
                
             
            elif self.plotType == PLOTType.DISTANCE:
                json+=  '"plotType": "RANGE",'+\
		                  '"range": '+str(det.rho)+','+\
		                  '"stdRange": '+str(det.sigma_rho)+','+\
		                  '"VelocityType": "NOVELOCITY",'+\
		                  '"plotTime": "'+self.dateTime.toUTC().toString("yyyy-MM-dd HH:mm:ss.z") +'",'+\
		                  '"classification": "UNKNOWN",'+\
		                  '"probaClassification": "1.0"},'
            elif self.plotType == PLOTType.SPHERICAL:
                json+=  '"plotType": "SPHERICAL",'+\
		                  '"range": '+str(det.rho)+','+\
		                  '"stdRange": '+str(det.sigma_rho)+','+\
                        '"azimut": '+str(det.theta)+','+\
		                  '"stdAzimut": '+str(det.sigma_theta)+','+\
                        '"site": '+str( det.phi)+','+\
                        '"stdSite": '+str(det.sigma_phi)+','+\
		                  '"VelocityType": "NOVELOCITY",'+\
		                  '"plotTime": "'+self.dateTime.toUTC().toString("yyyy-MM-dd HH:mm:ss.z") +'",'+\
		                  '"classification": "UNKNOWN",'+\
		                  '"probaClassification": "1.0"},'
                
                        
            elif self.plotType == PLOTType.ANGULAR2D:
                #print(-self.elevation + det.phi*180/np.pi)
                json+=  '"plotType": "BEARING_2D",'+\
                        '"azimut": '+str(det.theta )+','+\
		                  '"stdAzimut": '+str(det.sigma_theta )+','+\
                        '"site": '+str( det.phi)+','+\
                        '"stdSite": '+str(det.sigma_phi)+','+\
		                  '"VelocityType": "NOVELOCITY",'+\
		                  '"plotTime": "'+self.dateTime.toUTC().toString("yyyy-MM-dd HH:mm:ss.z") +'",'+\
		                  '"classification":"' +str(det.Classification)+'",'+\
		                  '"probaClassification": "'+str(det.ProbaClassification) +'"},'
    
            elif self.plotType == PLOTType.POLAR:
                json+=  '"plotType": "POLAR",'+\
		                  '"azimut": '+str(det.theta)+','+\
		                  '"stdAzimut": '+str(det.sigma_theta)+','+\
                        '"range": '+str(det.rho)+','+\
		                  '"stdRange": '+str(det.sigma_rho)+','+\
		                  '"VelocityType": "NOVELOCITY",'+\
		                  '"plotTime": "'+self.dateTime.toUTC().toString("yyyy-MM-dd HH:mm:ss.z") +'",'+\
		                  '"classification": "UNKNOWN",'+\
		                  '"probaClassification": "1.0"},'
                
            elif self.plotType == PLOTType.POLAR_SQUIRE:
                json+= '"plotType": "POLAR",'+\
                 '"azimut": '+str(  det.theta )+','+\
                 '"stdAzimut": '+str(det.sigma_theta)+','+\
                 '"range": '+str(det.rho)+','+\
                 '"stdRange": '+str(det.sigma_rho)+','+\
                 '"VelocityType": "NOVELOCITY",'+\
                 '"plotTime": "'+det.dateTime.toUTC().toString("yyyy-MM-dd HH:mm:ss.z") +'",'+\
                 '"dataType_1":  " '+det.info_1+'",'+\
                 '"data_1":   '+str(det.value_info_1)+','+\
                 '"dataType_2":  " '+det.info_2+'",'+\
                 '"data_2":   '+str(det.value_info_2)+','+\
                 '"classification": "UNKNOWN",'+\
                 '"probaClassification": "1.0"},'
            elif self.plotType == PLOTType.PIR_EVENT:
                        json+=  '"plotType": "BEARING_1D",'+\
		                  '"azimut": '+str(0.0)+','+\
		                  '"stdAzimut": '+str(0.01)+','+\
		                  '"VelocityType": "NOVELOCITY",'+\
		                  '"plotTime": "'+self.dateTime.toUTC().toString("yyyy-MM-dd HH:mm:ss.z") +'"},'   
                
                
          json = json[:-1]
          json +='],'+\
            '"scanTime": "'+self.dateTime.toUTC().toString("yyyy-MM-dd HH:mm:ss.z") +'"'+\
            '}'
   
       
    
          return json           
        
