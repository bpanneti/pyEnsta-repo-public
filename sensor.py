# -*- coding: utf-8 -*-
"""
Created on Thu Jun  9 11:34:41 2016

@author: t0174034
"""
import numpy as np
import math
from enum import Enum, unique
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from   matplotlib.path import Path   
 
from point import Position,REFERENCE_POINT 
from orientation import Orientation 
from mobileNode import MobileNode
from matplotlib.patches import Circle
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtOpenGL import *
from PyQt5.QtWidgets import *
from target  import iconNotValide, iconValide,TARGET_TYPE
from scan import Scan,PLOTType
import myTimer as _timer
from copy import deepcopy as deepCopy
import random


from os import path, listdir

numberScan = 0
nmberPlot  = 0
numberSensor = 0

def imscatter(x, y, imagePath, ax, zoom=0.1):
    im = OffsetImage(plt.imread(imagePath), zoom=zoom)

    ab = AnnotationBbox(im, (x, y), xycoords='data', frameon=False)
    return ax.add_artist(ab)

def is_integer_num(n):
 
    try:
          isinstance(int(n), int)
          return True
    except ValueError:
         return False
     
#    if isinstance(int(n), int):
#        return True
#    if isinstance(float(n), float):
#        return n.is_integer()
#    return False


compteur_node = -1
def compte_node(val = None):   
    global compteur_node
    if val==None:
        compteur_node += 1
    else:
        compteur_node = np.amax([compteur_node,val]) +1
    return compteur_node
 

compteur_sensor = -1
def compte_sensor(val = None):   
    global compteur_sensor
    if val==None:
        compteur_sensor += 1
    else:
        compteur_sensor = np.amax([compteur_sensor,val]) +1
    return compteur_sensor
 


 
def SER(_target):
    
    if _target == TARGET_TYPE.PAX :
        mean = 0
        std  = 2 
    elif  _target == TARGET_TYPE.UNKNOWN :
        mean = 0
        std  = 40
        
    elif  _target == TARGET_TYPE.CAR :
        mean = 20
        std  = 5
    elif  _target == TARGET_TYPE.DRONE :
        mean = -10
        std  = 8        
    elif  _target == TARGET_TYPE.TANK :
         mean = 33
         std  = 4       
    elif  _target == TARGET_TYPE.TRUCK :
        mean = 23
        std  = 2       
    elif  _target == TARGET_TYPE.BIRD :
        mean = -20
        std  = 7   
    elif  _target == TARGET_TYPE.VOILIER :
        mean = 15
        std  = 2  
    elif  _target == TARGET_TYPE.TANKER :
        mean = 30
        std  = 2  
    elif  _target == TARGET_TYPE.GOFAST :
          mean = 7
          std  = 5        
    return np.random.normal(mean,std)    
        
class SensorMode(Enum):
    nomode          = 0
    radar           = 1
    optroIR         = 2
    optroVIS        = 3
    sismo           = 4
    radar3D         = 5
    optroIR2D       = 6
    PIR             = 7
    accoustic       = 8
    gonio           = 9
    alarm           = 10
    COM             = 11
 
class AsservissementMode(Enum):
         NOMODE          = 0
         FIX_POINT       = 1 
         FIX_DIRECTION   = 2 
  
class FOVType(Enum):
    UNKNOWN     = 0
    SECTOR      = 1
    SPHERICAL   = 2
    CONICAL     = 3
    CIRCULAR    = 4
    



def is_float(value):
  try:
    float(value)
    return True
  except:
    return False
    
class   resolutionCell(object):
    def __init__(self,  rho=0.0, theta = 0.0, phi = 0.0 ):
        self.rho     = rho
        self.phi     = phi  
        self.theta   = theta
        
class Parameters(object):
    def __init__(self,sigmaRho = None, sigmaTheta = None, pfa = None, pd = None, sigmaPhi = None):
        self.pfa           = pfa
        self.pd            = pd
        self.sigmaRho      = sigmaRho
        self.sigmaTheta    = sigmaTheta
        self.sigmaPhi      = sigmaPhi
        
class SensorCoverage(object):
    def __init__(self,type = FOVType(0), ouverture=None, distanceMin = None, distanceMax = None, fov_elevation = None):
        self.type           = type
        self.fov            = ouverture
        self.distanceMin    = distanceMin
        self.distanceMax    = distanceMax
        self.fov_elevation  = fov_elevation
        self.parameters     = Parameters()
        self.name           = TARGET_TYPE.UNKNOWN
        self.id_Sensor      = -1
    
# class SensorBias(object):
#     def __init__(self, sensorId = -1, yaw = 0, x_ENU = 0, y_ENU = 0):
#         self.id = sensorId
#         self.position = Position()
#         self.orientation = Orientation()
    
#         self.position.setXYZ(x_ENU, y_ENU, 0, 'ENU')
#         self.position.ENU2WGS84();
#         self.orientation.setOrientation(yaw, 0, 0)

class Node(object):
     message = pyqtSignal('QString');
    
     def __init__(self,_id = None):
 
        if  _id == None:# or  is_integer_num(_id)==False:
             
             self.id    = str(compte_node())
    
        elif is_integer_num(_id)== True:  
             compte_node(int(_id))
 
             self.id            = str(_id) # node id as string caracters
        else:      
 
             self.id            = str(_id) # node id as string caracters
             
        self.Position           = Position()         # node location
        self.Orientation        = Orientation()      # node attitude
        self.date               = QDateTime()        # node date
        
        self.locObj             = None               # graphical node location object   
        self.textObj            = None               # graphical node text  object
        self.quiverObj          = None               # graphical node quiver  object
        
        self.locationIsVisible  = True
      
        self.color              = QColor(Qt.black)   # node color 
        self.typeNode           = 'UNKNOWN'          # node type 
        self.name               = "NoName"           # node name
        self.sensors            = []                 # sensor object list                 
        self.tracker            = None               # object tracker  
         
        
        self.axes               = None               # axes object
        self.canvas             = None               # canvas object
        self.selectedNode       = False              # node selection  
        self.treeWidgetItem     = None               #tree widget item reference  
        
        self.gis                = None
     
     def toJson(self ,ADRESS_IP = ''):
         adress = "192.168.1."+str(self.id)
        
         body = str('{  \
                     "attitude": { \
                              "yaw": '+  str(self.Orientation.yaw)+',\
                              "pitch":'+ str(self.Orientation.pitch)+',\
                              "roll": '+ str(self.Orientation.roll)+'\
                              },\
                              "code": 2,\
                              "idNode": "'+adress+'",\
                              "network": "'+ADRESS_IP+'",\
                              "name": "toto",\
                              "color": "#00000",\
                              "ressource": ":_Myressource",\
                              "nodeType": "'+self.typeNode+'",\
                              "message": "running",\
                              "position": {\
                                      "altitude": '+str(self.Position.altitude)+',\
                                      "latitude": '+str(self.Position.latitude)+',\
                                      "longitude": '+str(self.Position.longitude)+',\
                                      "format":"WGS84"\
                                      },\
                            "velocity": {\
                                    "vx": 0,\
                                    "vy": 0,\
                                    "vz": 0,\
                                    "format":"ENU"\
                                     },\
                             "state": "running"\
                             }')
 
         return body
     def set_visible(self, _checkstate):
 
        flag = True
        
        if _checkstate ==  Qt.Unchecked:
             flag = False
             
        self.locationIsVisible = flag
 
        if  self.locObj:
            self.locObj.set_visible(flag)
             
                
        if  self.textObj:
                self.textObj.set_visible(flag)     
        if  self.quiverObj:
            self.quiverObj.set_visible(flag)
            
     def removeSensor(self,_sensorId = 0):
        for u in self.sensors:
             if u.id == _sensorId:
                 self.sensors.remove(u)
                 return True
        return False
     def containsSensor(self,_sensorId = 0):
         for u in self.sensors:
             if u.id == _sensorId:
                 return True
         return False
             
     def setLocation(self,wayPoints):
            self.Position.setWGS84(wayPoints[0],wayPoints[1],0.0)
         
     def editNode(self):
 
        self.d = QDialog()
        
        layout              = QVBoxLayout()
        
        nodeName          = QLabel('Node name')
        nodeType          = QLabel('Node type')
        nodeLocation      = QLabel('Node''s location')
        nodeOrientation   = QLabel('Node''s orientation')
        nodeColor         = QLabel('Node color')

        self.nodeNameEdit      = QLineEdit()
     
        if self.name!='':
            self.nodeNameEdit.setText(self.name)
            
        self.nodeTypeNameEdit      = QLineEdit()

        if self.typeNode:
            self.nodeTypeNameEdit.setText(("%s")% (self.typeNode))
  
        self.nodeLocationEdit  = QTableWidget()
        self.nodeLocationEdit.setColumnCount(3) 
        self.nodeLocationEdit.setHorizontalHeaderLabels(["longitude", "latitude","hauteur"])


        hauteur = 0
        
        if self.gis!=None:
            altitude_g = self.gis.elevation(self.Position.latitude,self.Position.longitude) 
            hauteur    = self.Position.altitude - altitude_g
            
        rowPosition = self.nodeLocationEdit.rowCount() ;
        self.nodeLocationEdit.insertRow(rowPosition)
        self.nodeLocationEdit.setItem(rowPosition , 0, QTableWidgetItem(str(self.Position.longitude)) )
        self.nodeLocationEdit.setItem(rowPosition , 1, QTableWidgetItem(str(self.Position.latitude)) ) 
        self.nodeLocationEdit.setItem(rowPosition , 2, QTableWidgetItem(str(hauteur)) )
        self.nodeLocationEdit.resizeColumnsToContents()
#             
#        for i in range(len(self.timeToWayPoints)):
#             time =  self.timeToWayPoints[i]
#             self.targetLocationEdit.setItem(i ,3, QTableWidgetItem(time.toString("yyyy-MM-dd HH:mm:ss.zzz")))
   
        self.nodeLocationEdit.resizeColumnsToContents()
#        self.nodeLocationEdit.setContextMenuPolicy(Qt.CustomContextMenu)
#        self.nodeLocationEdit.customContextMenuRequested.connect(self.openMenu)
       
        self.nodeOrientationEdit  = QTableWidget()
        self.nodeOrientationEdit.setColumnCount(3) 
        self.nodeOrientationEdit.setHorizontalHeaderLabels(["Yaw", "Pitch","Roll"])
        
        rowPosition = self.nodeOrientationEdit.rowCount() ;
        self.nodeOrientationEdit.insertRow(rowPosition)
        self.nodeOrientationEdit.setItem(rowPosition , 0, QTableWidgetItem(str(self.Orientation.yaw)) )
        self.nodeOrientationEdit.setItem(rowPosition , 1, QTableWidgetItem(str(self.Orientation.pitch)) ) 
        self.nodeOrientationEdit.setItem(rowPosition , 2, QTableWidgetItem(str(self.Orientation.roll)) )
        
        self.nodeOrientationEdit.resizeColumnsToContents()

        self.nodeColorEdit     = QPushButton()
        self.nodeColorEdit.clicked.connect(self.changeColor)
        
        self.nodeColorEdit.setToolTip("change color")
        self.nodeColorEdit.setStyleSheet("background-color: %s" % self.color.name())
 
        grid = QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(nodeName, 1, 0)
        grid.addWidget(self.nodeNameEdit, 1, 1)
 
        grid.addWidget(nodeType, 2, 0)
        grid.addWidget(self.nodeTypeNameEdit, 2, 1)
 
        grid.addWidget(nodeColor, 3, 0)
        grid.addWidget(self.nodeColorEdit, 3, 1)
 
        grid.addWidget(nodeLocation, 4, 0)
        grid.addWidget(self.nodeLocationEdit, 4, 1)
        grid.addWidget(nodeOrientation, 5, 0)
        grid.addWidget(self.nodeOrientationEdit, 5, 1)  
        layout.addLayout(grid)

        buttonLayout = QHBoxLayout();
        
#        but_refresh = QPushButton("refresh")
#        buttonLayout.addWidget(but_refresh )
#        but_refresh.clicked.connect(self.OnRefresh)
        
        but_ok = QPushButton("OK")
        buttonLayout.addWidget(but_ok )
        but_ok.clicked.connect(self.OnOk)

        but_cancel = QPushButton("Cancel")
        buttonLayout.addWidget(but_cancel )
        but_cancel.clicked.connect(self.OnCancel)
        
        layout.addLayout(buttonLayout)
        
        
        self.d.setLayout(layout)
        self.d.setGeometry(300, 300, 350, 300)
        self.d.setWindowTitle("edit node")
        self.d.setWindowIcon(QIcon('icones/node.png'))
        self.d.setWindowModality(Qt.ApplicationModal)

        
        return self.d.exec_()
    
     def treeWidgetItem(self):
         return self.treeWidgetItem
     
     def setGis(self,_gis=None):
         self.gis=_gis
     def setTreeWidget(self,item):
         self.treeWidgetItem = item
         self.update()
         
     def update(self):
            if self.treeWidgetItem:
                self.treeWidgetItem.setText(1,self.name)
                self.treeWidgetItem.setText(2,self.typeNode)
                self.treeWidgetItem.setForeground(0,QBrush(self.color))
                self.treeWidgetItem.setForeground(1,QBrush(self.color))
                self.treeWidgetItem.setForeground(2,QBrush(self.color))
 
            if self.isValid():
                self.treeWidgetItem.setIcon(0, QIcon(QPixmap(iconValide)))
                self.toDisplay(self.axes,self.canvas)
                
            else:
                self.treeWidgetItem.setIcon(0,QIcon(QPixmap(iconNotValide)))  
     def isValid(self):
 
        if self.Position.latitude == [] or self.Position.longitude == []:
                  return False
        if self.Orientation.yaw == [] or    self.Orientation.pitch ==[] or self.Orientation.roll ==[]:
                return False
 
        return True;
    
     def OnCancel(self):
         self.d.close()

     def OnOk(self):
         
        self.name          = self.nodeNameEdit.text()
        self.typeNode      = self.nodeTypeNameEdit.text()

        if  self.nodeLocationEdit.item(0,0) != None and \
            self.nodeLocationEdit.item(0,1) != None and \
            self.nodeLocationEdit.item(0,2) != None and \
            is_float(self.nodeLocationEdit.item(0,0).text()) or \
            is_float(self.nodeLocationEdit.item(0,1).text()) or \
            is_float(self.nodeLocationEdit.item(0,2).text()):

            longitude = self.Position.longitude
            latitude  = self.Position.latitude
            altitude  = self.Position.altitude

            if is_float(self.nodeLocationEdit.item(0,0).text()):
                longitude   = float(self.nodeLocationEdit.item(0,0).text())
            if is_float(self.nodeLocationEdit.item(0,1).text()):
                latitude    = float(self.nodeLocationEdit.item(0,1).text())
            if is_float(self.nodeLocationEdit.item(0,2).text()):
                
                hauteur = float(self.nodeLocationEdit.item(0,2).text())
                
                if self.gis!=None:
                    altitude_g = self.gis.elevation(self.Position.latitude,self.Position.longitude) 
                    hauteur    = float(self.nodeLocationEdit.item(0,2).text()) + altitude_g
                    
                altitude    = hauteur
            
            self.Position.setWGS84(longitude,latitude,altitude)
                
        if  self.nodeOrientationEdit.item(0,0) != None and \
            self.nodeOrientationEdit.item(0,1) != None and \
            self.nodeOrientationEdit.item(0,2) != None and \
            is_float(self.nodeOrientationEdit.item(0,0).text()) or \
            is_float(self.nodeOrientationEdit.item(0,1).text()) or \
            is_float(self.nodeOrientationEdit.item(0,2).text()):

            yaw       = self.Orientation.yaw
            pitch     = self.Orientation.pitch
            roll      = self.Orientation.roll
            
            if is_float(self.nodeOrientationEdit.item(0,0).text()):
                yaw          = float(self.nodeOrientationEdit.item(0,0).text())
            if is_float(self.nodeOrientationEdit.item(0,1).text()):
                pitch           = float(self.nodeOrientationEdit.item(0,1).text())
            if is_float(self.nodeOrientationEdit.item(0,2).text()):
                roll           = float(self.nodeOrientationEdit.item(0,2).text())

            #print([yaw,pitch,roll])
            self.Orientation.setOrientation(yaw,pitch,roll)
        
        self.update()
        self.d.close()

        self.toDisplay(self.axes,self.canvas)
     def clear(self,canvas,axes):
 
    
       if self.locObj !=None:
            axes.lines.remove(self.locObj)
            self.locObj = None  

       if self.textObj !=None:
            self.textObj.remove()
            self.textObj =None 

       if self.quiverObj !=None:
            self.quiverObj.remove()
            self.quiverObj =None 
          
       canvas.blit(self.axes.bbox)
       #canvas.flush_events()   
     def changeColor(self):
        col = QColorDialog.getColor()

        if col.isValid():
            self.nodeColorEdit.setStyleSheet("  background-color: %s " % col.name()) 
            self.color = col
     def toDisplay(self,axes,canvas):
         
       if axes==None or canvas==None:
           return
       
       self.axes    = axes
       self.canvas  = canvas

       if   self.isValid() ==False  :
           return
        
       latitude     = self.Position.latitude
       longitude    = self.Position.longitude
       altitude     = self.Position.altitude

            
    #==================
    #objet position
    #==================
    
       if self.locObj !=None:
            self.locObj.remove()
            self.locObj = None  
            
       self.locObj, =  axes.plot(longitude,latitude,color = self.color.name(), linewidth= 2, visible =self.locationIsVisible ) #
       
         
    #==================
    #objet text
    #==================
       if self.textObj !=None:
            self.textObj.remove()
            self.textObj =None 

       self.textObj = axes.text(longitude,latitude , 'node : '+ str(self.id)+'\n'+self.name,color = self.color.name(),  bbox={'facecolor':'cyan' ,'alpha':0.5, 'pad':10}, visible =self.locationIsVisible )
  
    #==================
    #objet quiver 
    #==================
       if self.quiverObj !=None:
            self.quiverObj.remove()
            self.quiverObj =None 

        
       dx = 10*np.cos( (90-self.Orientation.yaw)*np.pi/180)
       dy = 10*np.sin( (90-self.Orientation.yaw)*np.pi/180) 

    
       self.quiverObj = axes.quiver(longitude,latitude,dx,dy,color = self.color.name(),alpha=0.8,visible =self.locationIsVisible ) 
  
    
    
       axes.draw_artist(self.locObj )
       axes.draw_artist(self.textObj )
       axes.draw_artist(self.quiverObj )           
       canvas.blit(self.axes.bbox)
       canvas.flush_events()

       #affichage des capteurs
       
       for _sensor in self.sensors:
          _sensor.toDisplay(axes,canvas)
       
       if self.tracker !=None:
           self.tracker.toDisplay(axes,canvas)
 
       
class Sensor(QWidget):
 
        
    newScan = pyqtSignal(Scan)
        
    #Messagerie
            
    message = pyqtSignal('QString');
 

    def __init__(self,_id = None,thread = True):
        super(Sensor, self).__init__()
        if  _id == None    : 
             self.id            = str(compte_sensor())           #id sensor as  a string 
             
        elif is_integer_num(_id)== True:   
             compte_sensor(int(_id))
             self.id            = str(_id)
        else:
             self.id            = str(_id) # sensor id as string caracter
      
        self.name               = 'UNKNOWN'             #sensor name
        self.id_node            = None                  #id_node
        self.node               = None                  #node object 
        self.sensorCoverage     = None                  #sensor coverage liste
        self.mode               = SensorMode.nomode     #sensor mode
        self.timeOfSampling     = 1                     #time of sampling in second
        self.trajObj            = None                  #sensor lcoation graphic object
        self.textObj            = None                  #sensor text graphic object
        self.plotsObj           = []                    #sensor detections graphic object
        self.coverAreaObj       = []                    #area of surveillance graphic object
        self.ellipsesObj        = []                    #detections covariance in location
        self.iconeObj           = []                    #detections type icone
        self.textPlotsObj       = []
        self.locationIsVisible  = True                  #visible or not
        self.color              = QColor(Qt.blue)       # sensor color
        self.connections        = []                    # communication connections
        self.treeWidgetItem     = None                  # tree widget reference
        self.scan               = None                  #current scan
        self.lastScanTime       = QDateTime()           #last scan dateTime
        #self.bias               = SensorBias()     # bias of the sensor
        self.position           = Position()            # unbiased position of the sensor
        self.orientation        = Orientation()         # unbiased orientation of the sensor
        #self.positionBiased     = Position()            # biased position of the sensor
        #self.orientationBiased  = Orientation()         # biased orientation of the sensor
        self.randomSeeded       = np.random.RandomState(np.random.randint(100000))  # random use for this sensor scan
        self.realData           = False
        self.displayCumulated   = False
        self.displayCovariance  = False
        self.displayIcone       = False
        self.GIS                = None
        
        
        self.targetTable        = []
        #==============================
        # intenralTracker
        #==============================
        
        self.internalTracker = False
        self.numTrack = 1

        #===============================
        # Asservissement
        #===============================
        
        self.AsservSensor           =  AsservissementMode.NOMODE
        self.AsservFixPoint         =  Position()
        self.AsservFixOrientation   =  Orientation()
        
        self.targets                = [] 
        
        #==============================
        # thread
        #==============================
        if thread:
            self.mutex                  = QMutex()
            self.thread                 = QThread()
            self.thread.started.connect(self.run)
 
        self.currentTime            = None
    def toJson(self):
        if self.id_node==None:
            return
        adressNode = "192.168.1."+str(self.id_node)
        sensorType= 'UNKNOWN'
        if self.mode == SensorMode.radar:
            sensorType = 'RADAR'
        elif self.mode == SensorMode.radar3D:
            sensorType = 'RADAR'
        elif self.mode == SensorMode.alarm:
            sensorType = 'RADIOFREQUENCE'
        elif self.mode == SensorMode.gonio:
            sensorType = 'RADIOFREQUENCE'
        elif self.mode == SensorMode.optroVIS:
            sensorType = 'VIDEO_VISIBLE'
        elif self.mode == SensorMode.optroIR:
            sensorType = 'VIDEO_IR'
        json ='{\
              "associatedArea": ['
        if self.sensorCoverage:
                    for _cover in self.sensorCoverage:
                        json+='{'
                        if _cover.type == FOVType.SPHERICAL:
                            json+='"VolumeType": 4,'
                        elif _cover.type == FOVType.CONICAL:
                            json+='"VolumeType": 3,'
                        elif _cover.type == FOVType.CIRCULAR:
                            json+='"VolumeType": 1,'
                        elif _cover.type == FOVType.SECTOR:
                            json+='"VolumeType": 2,'
                            
                        
                        json+='"classType": "'+str(_cover.name.name)+'", \
                                "distanceMin":'+str(_cover.distanceMin)+',\
                                "distanceMax":'+ str(_cover.distanceMax)+',\
                                "fov_AZ": '+str(_cover.fov)+',\
                                "fov_Site":'+str(_cover.fov_elevation)
                                
                        json+='},'
                    json =json[:-1]    
        json+='], \
                "code": 3,\
                "message": "sensor parameters",\
                "idNode": "'+adressNode+'",\
                "sensorId": "'+str(self.id )+'",\
                "sensorType": "'+sensorType+'",\
                "state": "KO"\
                }'

     
        return json
    
    # def setupBiasEdit(self):
    #     self.sensorBiasEdit = QTableWidget()
    #     self.sensorBiasEdit.setColumnCount(3)
    #     self.sensorBiasEdit.setHorizontalHeaderLabels(["Yaw (en °)", "Position x (en m)", "Position y (en m)"])
       
    #     rowPosition = self.sensorBiasEdit.rowCount() 
    #     self.sensorBiasEdit.insertRow(rowPosition)
    #     self.sensorBiasEdit.setItem(rowPosition, 0, QTableWidgetItem(str(self.bias.orientation.yaw)))
    #     self.sensorBiasEdit.setItem(rowPosition, 1, QTableWidgetItem(str(self.bias.position.x_ENU)))
    #     self.sensorBiasEdit.setItem(rowPosition, 2, QTableWidgetItem(str(self.bias.position.y_ENU)))
    #     self.sensorBiasEdit.resizeColumnsToContents()
       
    def editSensor(self):
 
        self.d = QDialog()
        layout              = QVBoxLayout()
        
        sensorName          = QLabel('Sensor name')
        sensorType          = QLabel('Sensor mode')
        sensorColor         = QLabel('Sensor color')
        sensorCoverage      = QLabel('Sensor coverage')
        sensorDisplayCum    = QLabel('Display cumulated reports')
        sensorIntTracker    = QLabel('Internal Tracker')
        #sensorBias          = QLabel('Sensor bias')
        sensorTimeEdit      = QLabel('Time of sampling')
        sensorAsservMode    = QLabel('Sensor management mode')
        sensorAsservLoc     = QLabel('Sensor management location')
        sensorAsservOri     = QLabel('Sensor management orientation')
        
        
        self.sensorNameEdit      = QLineEdit()
     
        if self.name!='':
            self.sensorNameEdit.setText(self.name)
  
        self.sensorModeEdit      = QComboBox()

        for type_t in SensorMode:
            self.sensorModeEdit.addItem("%s"% type_t.name)
        
        if self.mode:
            self.sensorModeEdit.setCurrentText("%s"% self.mode.name)
     
      
  
        self.sensorColorEdit     = QPushButton()
        self.sensorColorEdit.clicked.connect(self.changeColor)
        
        self.sensorColorEdit.setToolTip("change color")
        self.sensorColorEdit.setStyleSheet("background-color: %s" % self.color.name())


        #time of sampling
        self.sensorTimeofSamplingEdit = QLineEdit()
        self.sensorTimeofSamplingEdit.setText(str(self.timeOfSampling))
        #sensor area coverage

        self.sensorAreaCoverageEdit  = QTableWidget()
        self.sensorAreaCoverageEdit.setColumnCount(10) 
        self.sensorAreaCoverageEdit.setHorizontalHeaderLabels(["name","d_min (en m)","d_max (en m)","ouverture azimuth (en °)","ouverture site (en °)", "pfa","pd", "sigma rho (en m)", "sigma theta (en °)","sigma phi (en °)"])

        
        if self.sensorCoverage:
         for _cover in self.sensorCoverage:
            rowPosition = self.sensorAreaCoverageEdit.rowCount() ;
            self.sensorAreaCoverageEdit.insertRow(rowPosition)
            
            comboBox = QComboBox()
            for type_t in TARGET_TYPE:
                comboBox.addItem("%s"% type_t.name)

            comboBox.setCurrentText(str(_cover.name.name)) 
            
            self.sensorAreaCoverageEdit.setCellWidget(rowPosition, 0, comboBox)
            
    
            #self.sensorAreaCoverageEdit.setItem(rowPosition , 0, QTableWidgetItem(str(_cover.name)) )
            self.sensorAreaCoverageEdit.setItem(rowPosition , 1, QTableWidgetItem(str(_cover.distanceMin)) ) 
            self.sensorAreaCoverageEdit.setItem(rowPosition , 2, QTableWidgetItem(str(_cover.distanceMax)) )
            self.sensorAreaCoverageEdit.setItem(rowPosition , 3, QTableWidgetItem(str(_cover.fov)) )
            self.sensorAreaCoverageEdit.setItem(rowPosition , 4, QTableWidgetItem(str(_cover.fov_elevation)) ) 
            self.sensorAreaCoverageEdit.setItem(rowPosition , 5, QTableWidgetItem(str(_cover.parameters.pfa)) )
            self.sensorAreaCoverageEdit.setItem(rowPosition , 6, QTableWidgetItem(str(_cover.parameters.pd)) )
            self.sensorAreaCoverageEdit.setItem(rowPosition , 7, QTableWidgetItem(str(_cover.parameters.sigmaRho)) )
            self.sensorAreaCoverageEdit.setItem(rowPosition , 8, QTableWidgetItem(str(_cover.parameters.sigmaTheta)) )
            self.sensorAreaCoverageEdit.setItem(rowPosition , 9, QTableWidgetItem(str(_cover.parameters.sigmaPhi)))
            self.sensorAreaCoverageEdit.resizeColumnsToContents()

        self.sensorAreaCoverageEdit.setContextMenuPolicy(Qt.CustomContextMenu)
        self.sensorAreaCoverageEdit.customContextMenuRequested.connect(self.openMenu)
        #cumulated reports
        self.checkBoxInternalTracker    = QCheckBox("Internal Tracker")
        self.checkBoxInternalTracker.clicked.connect(self.internatTracker)
        if self.internalTracker:
            self.checkBoxInternalTracker.setCheckState(Qt.Checked)
        else:
            self.checkBoxInternalTracker.setCheckState(Qt.Unchecked)
            
        self.checkBox    = QCheckBox('cumulated data')
        self.checkBox.clicked.connect(self.displayCumulatedReports)
        
        if self.displayCumulated:
            self.checkBox.setCheckState(Qt.Checked)
        else:
            self.checkBox.setCheckState(Qt.Unchecked)
            
        self.checkBox_cov    = QCheckBox('display covariance')
        self.checkBox_cov.clicked.connect(self.displayCovarianceCheck)
        if self.displayCovariance:
            self.checkBox_cov.setCheckState(Qt.Checked)
        else:
            self.checkBox_cov.setCheckState(Qt.Unchecked) 
            
        self.checkBox_icone    = QCheckBox('display icone')
        self.checkBox_icone.clicked.connect(self.displayIconeCheck)
        if self.displayIcone:
            self.checkBox_icone.setCheckState(Qt.Checked)
        else:
            self.checkBox_icone.setCheckState(Qt.Unchecked)      

        #Add bias
        #self.setupBiasEdit()
        
        self.sensorAsserMode = QComboBox()
        for type_t in AsservissementMode :
            self.sensorAsserMode.addItem("%s"% type_t.name)
        for type_t in AsservissementMode :
            if type_t == self.AsservSensor:
                self.sensorAsserMode.setCurrentText("%s"% type_t.name)
        
        self.sensorAsserLocation = QTableWidget()
        self.sensorAsserLocation.setColumnCount(3) 
        self.sensorAsserLocation.setHorizontalHeaderLabels(["longitude (en °)","latitude (en °)","altitude (en m)"])
        self.sensorAsserLocation.insertRow(0)
        self.sensorAsserLocation.setItem(0 , 0, QTableWidgetItem(str(self.AsservFixPoint.longitude)) ) 
        self.sensorAsserLocation.setItem(0 , 1, QTableWidgetItem(str(self.AsservFixPoint.latitude )) ) 
        self.sensorAsserLocation.setItem(0 , 2, QTableWidgetItem(str(self.AsservFixPoint.altitude )) ) 
        
        self.sensorAsserOrientation = QTableWidget()
        self.sensorAsserOrientation.setColumnCount(3) 
        self.sensorAsserOrientation.setHorizontalHeaderLabels(["yaw (en °)","pitch (en °)","roll (en m)"])
        self.sensorAsserOrientation.insertRow(0)
        self.sensorAsserOrientation.setItem(0 , 0, QTableWidgetItem(str(self.AsservFixOrientation.yaw)) ) 
        self.sensorAsserOrientation.setItem(0 , 1, QTableWidgetItem(str(self.AsservFixOrientation.pitch )) ) 
        self.sensorAsserOrientation.setItem(0 , 2, QTableWidgetItem(str(self.AsservFixOrientation.roll )) )  
        
        self.sensorAsserLocation.setEnabled(False)  
        self.sensorAsserOrientation.setEnabled(False)  
        
        if self.AsservSensor == AsservissementMode.FIX_POINT:
            self.sensorAsserLocation.setEnabled(True)  
        if self.AsservSensor == AsservissementMode.FIX_DIRECTION:
            self.sensorAsserOrientation.setEnabled(True)
        self.sensorAsserMode.currentIndexChanged.connect(self.changeAsservMode)
        
        but_addSensorArea = QPushButton("add")
        but_addSensorArea.clicked.connect(self.addSensorArea)
        
        grid = QGridLayout()
        grid.setSpacing(13)

        grid.addWidget(sensorName, 1, 0)
        grid.addWidget(self.sensorNameEdit, 1, 1)
 
        grid.addWidget(sensorType, 2, 0)
        grid.addWidget(self.sensorModeEdit, 2, 1)
 
        grid.addWidget(sensorColor, 3, 0)
        grid.addWidget(self.sensorColorEdit, 3, 1)
        
        grid.addWidget(sensorTimeEdit, 4, 0)
        grid.addWidget(self.sensorTimeofSamplingEdit, 4, 1)
        
        grid.addWidget(sensorCoverage, 5, 0)
        grid.addWidget(self.sensorAreaCoverageEdit, 5, 1)
        grid.addWidget(but_addSensorArea,6,1 )
        layout.addLayout(grid)
      
        grid.addWidget(sensorIntTracker, 7, 0)
        grid.addWidget(self.checkBoxInternalTracker, 7, 1)
        grid.addWidget(sensorDisplayCum, 8, 0)
        grid.addWidget(self.checkBox, 8, 1)
        
   
        grid.addWidget(QLabel('display covariance'),9, 0)
        grid.addWidget(self.checkBox_cov,9, 1)
     
        grid.addWidget(QLabel('display icone'),10, 0)
        grid.addWidget(self.checkBox_icone,10, 1)
        

        
        # grid.addWidget(sensorBias, 10, 0)
        # grid.addWidget(self.sensorBiasEdit, 10, 1)
        
        grid.addWidget(sensorAsservMode, 11, 0)
        grid.addWidget(self.sensorAsserMode, 11, 1)
        grid.addWidget(sensorAsservLoc, 12, 0)
        grid.addWidget(self.sensorAsserLocation, 12, 1)
        grid.addWidget(sensorAsservOri, 13, 0)
        grid.addWidget(self.sensorAsserOrientation, 13, 1)
        
        buttonLayout = QHBoxLayout();

#        but_refresh = QPushButton("refresh")
#        buttonLayout.addWidget(but_refresh )
#        but_refresh.clicked.connect(self.OnRefresh)
        
        but_ok = QPushButton("OK")
        buttonLayout.addWidget(but_ok )
        but_ok.clicked.connect(self.OnOk)

        but_cancel = QPushButton("Cancel")
        buttonLayout.addWidget(but_cancel )
        but_cancel.clicked.connect(self.OnCancel)
        
        layout.addLayout(buttonLayout)
 
        
        self.d.setLayout(layout)
        self.d.setGeometry(300, 300, 350, 300)
        self.d.setWindowTitle("edit sensor")
        self.d.setWindowIcon(QIcon('icones/porteur.png'))
        self.d.setWindowModality(Qt.ApplicationModal)

        return self.d.exec_()
    
    def displayCovarianceCheck(self):
        
         if self.checkBox_cov.isChecked():
           self.displayCovariance = True
         else : 
             self.displayCovariance = False
    def displayIconeCheck(self):
            
             if self.checkBox_icone.isChecked():
               self.displayIcone = True
             else : 
                 self.displayIcone = False
                 
    def internatTracker(self):
         if self.checkBoxInternalTracker.isChecked():
           self.internalTracker = True
         else : 
             self.internalTracker = False
    def displayCumulatedReports(self):
         if self.checkBox.isChecked():
           self.displayCumulated = True
         else : 
             self.displayCumulated = False
    def changeAsservMode(self):
        
        for _mode in AsservissementMode:
 
            if _mode.name == self.sensorAsserMode.currentText():
 
                break;
      
        self.sensorAsserLocation.setEnabled(False)  
        self.sensorAsserOrientation.setEnabled(False)  
        
        if _mode == AsservissementMode.FIX_POINT:
            self.sensorAsserLocation.setEnabled(True)  
        if _mode == AsservissementMode.FIX_DIRECTION:
            self.sensorAsserOrientation.setEnabled(True)
            
    def openMenu(self,position):
        menu = QMenu()
        imageSelection = QPixmap("icones/delete.png")
        actionSelection= QAction(QIcon(imageSelection), 'delete point', self)
        deleteAction = menu.addAction(actionSelection)
 
        action = menu.exec_(self.sensorAreaCoverageEdit.mapToGlobal(position))
 
        if action == deleteAction:
 
            index = self.sensorAreaCoverageEdit.currentRow() 
            self.sensorCoverage = self.sensorCoverage[:index]+ self.sensorCoverage[index+1 :]
 
            if len(self.sensorCoverage)==0:
                self.sensorCoverage = []
 
            if self.sensorCoverage:
                for _cover in self.sensorCoverage:
                    rowPosition = self.sensorAreaCoverageEdit.rowCount()
                    self.sensorAreaCoverageEdit.insertRow(rowPosition)
                    self.sensorAreaCoverageEdit.setItem(rowPosition , 0, QTableWidgetItem(str(_cover.name)) )
                    self.sensorAreaCoverageEdit.setItem(rowPosition , 1, QTableWidgetItem(str(_cover.distanceMin)) ) 
                    self.sensorAreaCoverageEdit.setItem(rowPosition , 2, QTableWidgetItem(str(_cover.distanceMax)) )
                    self.sensorAreaCoverageEdit.setItem(rowPosition , 3, QTableWidgetItem(str(_cover.fov)) )
                    self.sensorAreaCoverageEdit.setItem(rowPosition , 4, QTableWidgetItem(str(_cover.fov_elevation)) ) 
                    self.sensorAreaCoverageEdit.setItem(rowPosition , 5, QTableWidgetItem(str(_cover.parameters.pfa)) )
                    self.sensorAreaCoverageEdit.setItem(rowPosition , 6, QTableWidgetItem(str(_cover.parameters.pd)) )
                    self.sensorAreaCoverageEdit.setItem(rowPosition , 7, QTableWidgetItem(str(_cover.parameters.sigmaRho)) )
                    self.sensorAreaCoverageEdit.setItem(rowPosition , 8, QTableWidgetItem(str(_cover.parameters.sigmaTheta)) )
                    self.sensorAreaCoverageEdit.setItem(rowPosition , 9, QTableWidgetItem(str(_cover.parameters.sigmaPhi)))
                    self.sensorAreaCoverageEdit.resizeColumnsToContents()
    def OnCancel(self):
         self.d.close()
    def OnOk(self):
        self.name          = self.sensorNameEdit.text()
        self.timeOfSampling = float(self.sensorTimeofSamplingEdit.text())

        fovType  = FOVType.UNKNOWN
        
        for type_t in SensorMode:
            if type_t.name == self.sensorModeEdit.currentText():
                self.mode       = type_t
                
            if self.mode == SensorMode.radar or \
               self.mode == SensorMode.optroIR or \
               self.mode == SensorMode.optroIR2D or \
               self.mode == SensorMode.optroVIS or \
               self.mode == SensorMode.gonio or \
               self.mode == SensorMode.alarm or \
               self.mode == SensorMode.PIR:
                    fovType = FOVType.SECTOR
            elif self.mode == SensorMode.radar3D:
                    fovType = FOVType.CONICAL
            elif self.mode == SensorMode.accoustic:
                    fovType = FOVType.SPHERICAL

        rowCount = self.sensorAreaCoverageEdit.rowCount() ;
        sensorAreaCoverages = []
        for i in range (0,rowCount):
            sensorAreaCoverage                  = SensorCoverage()
            
            for type_t in TARGET_TYPE:
                if type_t.name == self.sensorAreaCoverageEdit.cellWidget(i,0).currentText():
                    sensorAreaCoverage.name             = type_t
                    break
                
            sensorAreaCoverage.type             = fovType
            sensorAreaCoverage.id_Sensor        = self.id
            if  self.sensorAreaCoverageEdit.item(i,1) != None and is_float(self.sensorAreaCoverageEdit.item(i,1).text()):
                sensorAreaCoverage.distanceMin      =  float(self.sensorAreaCoverageEdit.item(i,1).text())
            else:
                continue
            if  self.sensorAreaCoverageEdit.item(i,2) != None and is_float(self.sensorAreaCoverageEdit.item(i,2).text()):
                sensorAreaCoverage.distanceMax      =  float(self.sensorAreaCoverageEdit.item(i,2).text())
            else:
                continue
            if  self.sensorAreaCoverageEdit.item(i,3) != None and is_float(self.sensorAreaCoverageEdit.item(i,3).text()):
                sensorAreaCoverage.fov     =  float(self.sensorAreaCoverageEdit.item(i,3).text())
            else:
                continue
            if  self.sensorAreaCoverageEdit.item(i,4) != None and is_float(self.sensorAreaCoverageEdit.item(i,4).text()):
                sensorAreaCoverage.fov_elevation     =  float(self.sensorAreaCoverageEdit.item(i,4).text())
            else:
                continue
            if  self.sensorAreaCoverageEdit.item(i,5) != None and is_float(self.sensorAreaCoverageEdit.item(i,5).text()):
                sensorAreaCoverage.parameters.pfa     =  float(self.sensorAreaCoverageEdit.item(i,5).text())
            else:
                continue
            if  self.sensorAreaCoverageEdit.item(i,6) != None and is_float(self.sensorAreaCoverageEdit.item(i,6).text()):
                sensorAreaCoverage.parameters.pd     =  float(self.sensorAreaCoverageEdit.item(i,6).text())
            else:
                continue
            if  self.sensorAreaCoverageEdit.item(i,7) != None and is_float(self.sensorAreaCoverageEdit.item(i,7).text()):
                sensorAreaCoverage.parameters.sigmaRho     =  float(self.sensorAreaCoverageEdit.item(i,7).text())
            else:
                continue
            if  self.sensorAreaCoverageEdit.item(i,8) != None and is_float(self.sensorAreaCoverageEdit.item(i,8).text()):
                sensorAreaCoverage.parameters.sigmaTheta     =  float(self.sensorAreaCoverageEdit.item(i,8).text())
            else:
                continue
            if  self.sensorAreaCoverageEdit.item(i,9) != None and is_float(self.sensorAreaCoverageEdit.item(i,9).text()):
                sensorAreaCoverage.parameters.sigmaPhi     =  float(self.sensorAreaCoverageEdit.item(i,9).text())
            else:
                continue
            sensorAreaCoverages.append(sensorAreaCoverage)

        if len(sensorAreaCoverages)>0:
            self.sensorCoverage = sensorAreaCoverages
        
        # bias
        yaw = 0
        x_ENU = 0
        y_ENU = 0
        '''
        if self.sensorBiasEdit.item(0, 0) != None and is_float(self.sensorBiasEdit.item(0, 0).text()):
            yaw = float(self.sensorBiasEdit.item(0, 0).text())
        if self.sensorBiasEdit.item(0, 1) != None and is_float(self.sensorBiasEdit.item(0, 1).text()):
            x_ENU = float(self.sensorBiasEdit.item(0, 1).text())
        if self.sensorBiasEdit.item(0, 2) != None and is_float(self.sensorBiasEdit.item(0, 2).text()):
            y_ENU = float(self.sensorBiasEdit.item(0, 2).text())
        '''    
        #self.bias = SensorBias(self.id, yaw, x_ENU, y_ENU)

        self.updateLocationOrientation()

        for _mode in AsservissementMode: 
            if _mode.name == self.sensorAsserMode.currentText():
                self.AsservSensor = _mode
                
                break;
                
        if  self.sensorAsserLocation.item(0,0) != None and \
            self.sensorAsserLocation.item(0,1) != None and \
            self.sensorAsserLocation.item(0,2) != None and \
            is_float(self.sensorAsserLocation.item(0,0).text()) and \
            is_float(self.sensorAsserLocation.item(0,1).text()) and \
            is_float(self.sensorAsserLocation.item(0,2).text()) and \
            self.AsservSensor == AsservissementMode.FIX_POINT:
                 
            longitude = float(self.sensorAsserLocation.item(0,0).text())
            latitude  = float(self.sensorAsserLocation.item(0,1).text())
            altitude  = float(self.sensorAsserLocation.item(0,2).text())
            
            self.AsservFixPoint.setWGS84(longitude,latitude,altitude)
    
        if  self.sensorAsserOrientation.item(0,0) != None and \
            self.sensorAsserOrientation.item(0,1) != None and \
            self.sensorAsserOrientation.item(0,2) != None and \
            is_float(self.sensorAsserOrientation.item(0,0).text()) and \
            is_float(self.sensorAsserOrientation.item(0,1).text()) and \
            is_float(self.sensorAsserOrientation.item(0,2).text()) and \
            self.AsservSensor == AsservissementMode.FIX_DIRECTION:
                 
             yaw     = float(self.sensorAsserOrientation.item(0,0).text())
             pitch   = float(self.sensorAsserOrientation.item(0,1).text())
             roll    = float(self.sensorAsserOrientation.item(0,2).text())   
             self.AsservFixOrientation.setOrientation(yaw,pitch,roll)
             
        self.update()
         
        
        self.d.accept()
    def isValid(self):
        if self.sensorCoverage == None  or self.sensorCoverage ==[] :
            return False
        if self.AsservSensor== AsservissementMode.FIX_POINT and  (self.AsservFixPoint.latitude == [] or self.AsservFixPoint.longitude == [] or self.AsservFixPoint.altitude == [] ):
                  return False
        if self.AsservSensor== AsservissementMode.FIX_DIRECTION and (self.AsservFixOrientation.yaw == [] or    self.AsservFixOrientation.pitch ==[] or self.AsservFixOrientation.roll ==[]):
                return False
 
        return True;
    def addSensorArea(self):
        rowPosition = self.sensorAreaCoverageEdit.rowCount() ;
        self.sensorAreaCoverageEdit.insertRow(rowPosition)
        comboBox = QComboBox()
        for type_t in TARGET_TYPE:
                comboBox.addItem("%s"% type_t.name)
        #comboBox.setItemText(str(_cover.name))     
        self.sensorAreaCoverageEdit.setCellWidget(rowPosition, 0, comboBox)
    def update(self):
        if self.treeWidgetItem==None:
            return 
        
        if self.isValid()==True:
            self.treeWidgetItem.setIcon(0, QIcon(QPixmap(iconValide)))
        else:
            self.treeWidgetItem.setIcon(0,QIcon(QPixmap(iconNotValide)))
            
        if self.treeWidgetItem:
                self.treeWidgetItem.setText(1,self.name)
                self.treeWidgetItem.setText(2,self.mode.name)
                self.treeWidgetItem.setForeground(0,QBrush(self.color))
                self.treeWidgetItem.setForeground(1,QBrush(self.color))
                self.treeWidgetItem.setForeground(2,QBrush(self.color))
      
                
    def changeColor(self):
        col = QColorDialog.getColor()

        if col.isValid():
            self.sensorColorEdit.setStyleSheet("  background-color: %s " % col.name()) 
            self.color = col
    def setTreeWidget(self,item):

         self.treeWidgetItem = item
         self.update()
         
    def updateLocationOrientation(self):
      
        flag = True
        position = Position()
        orientation = Orientation()

        if type(self.node) == MobileNode :
            flag, position,VelocityTime = self.node.positionAtTime(currentTime)
            orientation       = self.node.orientationAtTime(currentTime)
        elif type(self.node) == Node:
            position        = self.node.Position
            orientation     = self.node.Orientation
        
        if flag :
            self.position = deepCopy(position)
            #self.positionBiased = self.position + self.bias.position


        self.orientation = deepCopy(orientation)
        #self.orientationBiased = self.orientation + self.bias.orientation

    def setSensorType(self,_typeStr):
        
        for _typet in SensorMode:
            if _typeStr == _typet.name:
                self.mode = _typet
                return
        
        self.mode = SensorMode.nomode
    def displayLinks(self,sensors,axes):
        latitude    = []
        longitude   = []
        for sensor in sensors:
            for _id in self.connections:   
                if _id == sensor.id:
                    latitude  = [self.Position[0].latitude,sensor.Position[0].latitude]
                    longitude = [self.Position[0].longitude,sensor.Position[0].longitude]
                    obj,  =  axes.plot(longitude,latitude,'r--' , linewidth= 2  )
                    axes.draw_artist(obj) 
        
        
    def toDisplay(self,axes = None,canvas= None,_currentTime= None): 

        if self.node == None:
            return
            
        self.updateLocationOrientation()
  
        if self.position.latitude ==[] or self.position.longitude == []:
           return
        
        self.axes   = axes 
        self.canvas = canvas           
 
        #==================
        #objet position
        #==================
 
        if self.trajObj !=None:
            axes.lines.remove(self.trajObj)
            self.trajObj = None  
            
        self.trajObj, = axes.plot(self.position.longitude,self.position.latitude,color = self.color.name() , linewidth= 2,visible =self.locationIsVisible ) 
        
        
        #==================
        #objet text
        #==================
 
        if self.textObj !=None:
            self.textObj.remove()
            self.textObj = None  
        
        self.textObj  = axes.text(self.position.longitude,self.position.latitude , 'sensor : '+ str(self.id),   bbox={'facecolor':'white', 'alpha':0.5, 'pad':10},visible =self.locationIsVisible )
      
        if self.coverAreaObj != []:
            for u in self.coverAreaObj:
                u.remove()
            self.coverAreaObj = []
 
        if self.sensorCoverage!=None  and  REFERENCE_POINT.longitude !=[]  and  REFERENCE_POINT.latitude!=[]:

            for _cover in self.sensorCoverage: 
                if _cover.type == FOVType.SPHERICAL:
                    dmax = _cover.distanceMax
                    
                    pts =  Position()
                    pts.setXYZ(self.position.x_UTM + dmax,self.position.y_UTM,0.0)
                  
                    ddegree = np.sqrt(np.power(pts.longitude-self.position.longitude,2.0)+np.power(pts.latitude-self.position.latitude ,2.0))
                    _circle = Circle( [self.position.longitude,self.position.latitude], ddegree, ec="none")
                
               
                    self.coverAreaObj.append(_circle)
                    axes.add_patch(_circle)
             
                    canvas.blit(axes.bbox)
                    canvas.update()
                    canvas.flush_events()
                    
                if    _cover.type== FOVType.SECTOR  or _cover.type== FOVType.CONICAL :        
                    if self.orientation.yaw == None:
                        self.message.emit(("Error the %s node's yaw is not defined")%self.node.name)
                        return
                    if _cover.fov == None:
                        self.message.emit(("Error the %s sensor's fov is not defined")%_cover.name)
                        return
                    if _cover.distanceMax == None:
                        self.message.emit(("Error the %s sensor's dMax is not defined")%_cover.name)
                        return
                    if _cover.distanceMin == None:
                        self.message.emit(("Error the %s sensor's dMin is not defined")%_cover.name)
                        return
 
#                    u = (_cover.distanceMin )*np.cos(np.pi/2-self.orientationBiased.yaw*np.pi/180) 
#                    v = (_cover.distanceMin )*np.sin(np.pi/2-self.orientationBiased.yaw*np.pi/180) 
#
#                    Att =  Position(latitude,longitude,altitude)
#                    Att.x = Att.x + u
#                    Att.y = Att.y + v
#                    Att.UTM2WGS84()
                    #print(['node location:',Att.x,Att.y])
        
                   # _angle =  np.pi/2 - self.orientationBiased.yaw *np.pi/180 - _cover.fov/2.0*np.pi/180;# np.pi/2  - 
                    _angle = np.mod(np.pi/2 - self.orientation.yaw * np.pi/180  -  _cover.fov/2.0 * np.pi/180 + np.pi, 2*np.pi) - np.pi
                    verts = np.array([_cover.distanceMin*np.cos(_angle), _cover.distanceMin*np.sin(_angle)])        
                  
                    while _angle  < np.pi/2  - self.orientation.yaw*np.pi/180  + _cover.fov/2*np.pi/180:
                        _angle = _angle + 2*np.pi/180
                        Pt = np.array([_cover.distanceMin*np.cos(_angle), _cover.distanceMin*np.sin(_angle)])
                        verts = np.vstack([verts, Pt] )
             
                    while _angle  > np.pi/2  - self.orientation.yaw*np.pi/180  - _cover.fov/2*np.pi/180:
                        _angle = _angle - 2*np.pi/180
                        Pt = np.array([_cover.distanceMax*np.cos(_angle), _cover.distanceMax*np.sin(_angle)])
                        verts = np.vstack([verts, Pt] )
            
                    Pt = np.array([_cover.distanceMin*np.cos(_angle), _cover.distanceMin*np.sin(_angle)])       
                    verts = np.vstack([verts, Pt] )    +[self.position.x_UTM,self.position.y_UTM]
                
                    pathWGS84 = []
                    for u in verts:
                        pts =  Position()
                        pts.setXYZ(u[0],u[1],0.0)
                        pathWGS84.append([pts.longitude ,pts.latitude])
          
                    path = Path(pathWGS84)
            
                    patch = patches.PathPatch(path,facecolor=self.color.name(),alpha =0.5,visible =self.locationIsVisible,edgecolor=(0.0, 0.0, 0.0),linestyle='--') 
                    self.coverAreaObj.append(patch)
                    axes.add_patch(patch)
             
        canvas.blit(axes.bbox)
        canvas.update()
        canvas.flush_events()
        canvas.draw()
            #axes.plot(pathWGS84,verts[:,1]+latitude[0],'k',linewidth=2)
    def  sensorURL(self,_targetType ):
        _url ='';
 
 
        if (self.mode== SensorMode.optroVIS or self.mode== SensorMode.optroIR) and path.exists('./images/'+_targetType.name):
 
            arr = listdir('./images/'+_targetType.name)
           
            index = random.randint(0,len(arr)+2)
          
            if index >=0 and index < len(arr):
                _url = path.dirname(path.abspath(__file__))+'\\images\\'+_targetType.name+'\\'+arr[index]
            #print(_url)    
        return _url;
    def sensorClassification(self,targetType = TARGET_TYPE.UNKNOWN, truePosition = Position()):
        #cible est considéreé dans le volume de surveillance du capteur
        
        #on va définir un critère de classification fonction de la distance
        #approche bof mais bon 
        probaClassif    = 0.95
        if self.mode == SensorMode.radar or self.mode == SensorMode.radar3D :
            probaClassif    = 0.7
        probaClass      = np.zeros((len(TARGET_TYPE),1))
        distance        = self.node.Position.distanceToPoint(truePosition)
        classif         = targetType
        
        Emprise = None
        for _cover in self.sensorCoverage:
            if _cover.name == targetType or \
            (Emprise==None and _cover.name==TARGET_TYPE.UNKNOWN) :
                Emprise = _cover
                break
        if distance> 0.75 * Emprise.distanceMax:
            proba = max(0.6, 1-distance/Emprise.distanceMax)
        else:
            proba = probaClassif
            
            
        tir = np.random.uniform(0,1);
        
        if proba < tir:
            proba   = tir
            p = np.random.randint(0,len(TARGET_TYPE)-1)
            for _type in TARGET_TYPE:
                   if _type.value.value == p: 
                      classif = _type
            
        if self.mode == SensorMode.radar or self.mode == SensorMode.radar3D :
            c = np.random.uniform(0,1,size=(len(TARGET_TYPE),1))
        
            c[classif.value.value] = proba
            probaClass = c/np.sum(c)
            _string = classif.name

        
        elif self.mode == SensorMode.optroIR2D or self.mode == SensorMode.optroVIS or self.mode == SensorMode.optroIR :
            c = np.random.uniform(0,1,size=(len(TARGET_TYPE),1))
            c[classif.value.value] = proba
            probaClass = c/np.sum(c)
            _string = classif.name
        elif self.mode == SensorMode.gonio or self.mode == SensorMode.accoustic  :
            c = np.random.uniform(0,1,size=(len(TARGET_TYPE),1))
            c[classif.value.value] = proba
            probaClass = c/np.sum(c)
            _string = classif.name
            
           # if targetType ==  TARGET_TYPE.TANK:
           #    _string = 'vehicle'
           # elif targetType ==  TARGET_TYPE.TRUCK  :
           #     _string = 'vehicle'
           # elif targetType ==  TARGET_TYPE.CAR  :
           #       _string ='light vehicle'
           # elif targetType ==  TARGET_TYPE.PAX  :
           #       _string ='personn'
           # elif targetType ==  TARGET_TYPE.DRONE  :
           #       _string ='drone'
           # else : 
           #       _string ='unknown'
                 
                 
        else:
             _string = targetType.value.correspondance
            
            


       
        
    

        return _string, probaClass
        
        # else:
        #     classif = np.random.randint(0,len(TARGET_TYPE)-1)
        #     for _type in TARGET_TYPE:
        #         if _type.value.value == classif: 
        #             _string = 
        #             return _string,  proba
        
            
        
    def isDetectable(self,pos = Position(),altitude = 0):

        if self.GIS:
            A = QPointF(pos.longitude,pos.latitude)
            B = QPointF(self.position.longitude,self.position.latitude)
            line  = QLineF(A,B)
            flag = self.GIS.isDetectable(line,altitude)
            return flag
        
        return True
    def toVolume(self):
        
        Emprise = None
      
        for _cover in self.sensorCoverage:
 
            if _cover.name==TARGET_TYPE.UNKNOWN:
                Emprise = _cover
        if Emprise == None:
            
            return  1        
    
 
        volume = Emprise.distanceMax / np.abs(np.tan(Emprise.fov*np.pi/180))     * Emprise.distanceMax
        volume = volume/2.0
        return volume
    def toPolygon(self):
        #retourne sous liste de points le polygon de la FOV
        Emprise = None
        Polygon = QPolygonF()
        for _cover in self.sensorCoverage:
 
            if _cover.name==TARGET_TYPE.UNKNOWN:
                Emprise = _cover
          
                break
      
        if Emprise == None:
            print('in function toPolygon no FOV selected')
            return  Polygon
        
        
                            
 
        _angle =  np.pi/2 - self.orientation.yaw *np.pi/180 - Emprise.fov/2.0*np.pi/180;# np.pi/2  - 
        verts = np.array([Emprise.distanceMin*np.cos(_angle), Emprise.distanceMin*np.sin(_angle)])        
                
        while _angle  < np.pi/2  - self.orientation.yaw*np.pi/180  + Emprise.fov/2*np.pi/180:
            _angle = _angle + 2*np.pi/180
            Pt = np.array([Emprise.distanceMin*np.cos(_angle), Emprise.distanceMin*np.sin(_angle)])
            verts = np.vstack([verts, Pt] )
 
        while _angle  > np.pi/2  - self.orientation.yaw*np.pi/180  - Emprise.fov/2*np.pi/180:
            _angle = _angle - 2*np.pi/180
            Pt = np.array([Emprise.distanceMax*np.cos(_angle), Emprise.distanceMax*np.sin(_angle)])
            verts = np.vstack([verts, Pt] )

        Pt = np.array([Emprise.distanceMin*np.cos(_angle), Emprise.distanceMin*np.sin(_angle)])       
        verts = np.vstack([verts, Pt] )    +[self.position.x_UTM,self.position.y_UTM]
                
 
        for u in verts:
                        pts =  Position()
                        pts.setXYZ(u[0],u[1],0.0)
                        Polygon.append(QPointF(pts.x_ENU ,pts.y_ENU))
        return  Polygon 
        
    def isInFOV(self, pos = Position(), targetType = TARGET_TYPE.UNKNOWN,currentTime=QDateTime()): 
        #Test si le point est dans l'emprise du capteur
     
    
        if self.node == None:
            return False
        if self.sensorCoverage == None:
            return False
        if type(self.node)==Node and (self.node.Position.longitude==[] or self.node.Position.latitude==[]):
            return False

        self.updateLocationOrientation()
         
        sensorLoc   = np.array([self.position.x_ENU , self.position.y_ENU , self.position.altitude])
        pt          = np.array([pos.x_ENU , pos.y_ENU,pos.altitude])
        distance    = np.sqrt(np.power(pt[0]-sensorLoc[0],2.0)+np.power(pt[1]-sensorLoc[1],2.0)+np.power(pt[2]-sensorLoc[2],2.0))#np.linalg.norm( sensorLoc - pt) 
        angle       = np.arctan2(pt[1] - sensorLoc[1] ,pt[0] - sensorLoc[0])*180/np.pi    
        
   
        if angle >=  0 or angle >= -90:
           angle = 90 - angle  
           
        elif angle <=-90 :
            angle = -90 - (180 + angle)  
 
        Emprise = None
   
        for _cover in self.sensorCoverage:
 
            if _cover.name == targetType or \
            (Emprise==None and _cover.name==TARGET_TYPE.UNKNOWN):
                Emprise = _cover
          
                break
      
        if Emprise == None:
            return False
    
        ecart = angle-self.orientation.yaw
 
        if ecart > 180 :
            ecart = 360 - ecart;
        elif ecart < -180 :
            ecart = 360+ecart; 
 
       
        if Emprise.type == FOVType.SPHERICAL and distance <= Emprise.distanceMax:
            return True
        if Emprise.type == FOVType.SECTOR and np.abs(ecart) <=  Emprise.fov/2 and distance >= Emprise.distanceMin and distance <= Emprise.distanceMax:
            return True
        if Emprise.type == FOVType.CONICAL and np.abs(ecart) <=  Emprise.fov/2 and distance >= Emprise.distanceMin and distance <= Emprise.distanceMax:
            return True
        else:
            return False
    def clearScanData(self,canvas,axes):
       if self.plotsObj and self.displayCumulated ==False:
      
          for u in self.plotsObj:
               u.remove()
               #axes.lines.remove(u)
          self.plotsObj=[]
        
       for _e in self.ellipsesObj:
             _e.remove()
       self.ellipsesObj = [] 
       
       for _e in self.iconeObj:
             _e.remove()
       self.iconeObj = [] 
       
       for _e in self.textPlotsObj:
           _e.remove()
       self.textPlotsObj = [] 
                
    def clearGrpahicalData(self,canvas,axes):
     
       if self.plotsObj:
          for u in self.plotsObj:
               u.remove()
          self.plotsObj=[]
       
       if self.trajObj !=None:
            axes.lines.remove(self.trajObj)
            self.trajObj = None
            
       if self.textObj !=None:
            self.textObj.remove()
            self.textObj = None 
            
       if self.coverAreaObj != []:
            for u in self.coverAreaObj:
                u.remove()
            self.coverAreaObj = []
            
       canvas.blit(axes.bbox)
       canvas.flush_events()   
       
    def displayCurrentTime(self,currenTime, previousTime):
        indexs = []
        latitude = []
        longitude =[]
       
        if not        previousTime:
            previousTime = 0
    
        
        if previousTime < 0 :
            previousTime = 0        
        if currenTime < 0 :
            currenTime = 0   
 
        if previousTime <= currenTime:
            t_prec      = _timer.getReferenceTime().addMSecs(previousTime)
            t_curent    = _timer.getReferenceTime().addMSecs(currenTime)
        
        elif previousTime > currenTime:
              t_prec      = _timer.getReferenceTime().addMSecs(currenTime)
              t_curent    = _timer.getReferenceTime().addMSecs(previousTime)
              
 
        for t in range(len(self.scan)):
            if self.scan[t].dateTime.time().toPyTime() >   t_prec.toPyTime() and self.scan[t].dateTime.time().toPyTime() <= t_curent.toPyTime():
                 indexs.append(t)
        
        #display
        
        for i in indexs:
       
            if self.scan[i].Type == PLOTType.POLAR or self.scan[i].Type == PLOTType.SPHERICAL:
 
                for plot in  self.scan[i].plots:     
                    pos =position.Position()
                    pos.setXYZ(plot.z_XY[0,0],plot.z_XY[1,0],0.0,'ENU')

                    
                    latitude.append(pos.latitude)
                    longitude.append(pos.longitude)
 
                    e1 = patches.Ellipse((longitude[-1], latitude[-1]), plot.width, plot.height,
                    angle=plot.angle*180/np.pi)

                    e1.set_alpha(0.5)
                    e1.set_facecolor(self.color.name())
        
                    
                    #self.axes.add_patch(e1)
           
                if longitude and latitude:
                    if self.plotsObj:
                        for u in self.plotsObj:
                            self.axes.lines.remove(u)
                        self.plotsObj=[]
              
                    obj,  = self.axes.plot(longitude,latitude,color = 'k' , linewidth= 0,marker = 's',markerfacecolor =  self.color.name() ,markersize = 3)
                    self.plotsObj.append(obj)
                    self.axes.draw_artist(obj )
                        
#                    self.canvas.blit(self.axes.bbox)
#                    self.canvas.update()
#                    self.canvas.flush_events()
                    
            if self.scan[i].Type == PLOTType.DISTANCE:  
                
                an = np.linspace(0, 2*np.pi, 100)
                if self.plotsObj:
                    for yu in self.plotsObj:
                        yu.remove()
                        #self.plotsObj.pop(yu).remove()
                    #self.axes.lines.remove(self.plotsObj)
                    self.plotsObj=[]
                        
                for plot in  self.scan[i].plots:  
                    pos  =position.Position()
                    pos.setXYZ(self.scan[i].location.x,self.scan[i].location.y)
                    pos.x+= plot.rho
                    pos.UTM2WGS84()
                    distance =  np.sqrt(np.power(pos.latitude -     self.scan[i].location.latitude,2.0)+np.power(pos.longitude -     self.scan[i].location.longitude,2.0))
                    couleur = QColor(Qt.black)
                    plotsObj,  = self.axes.plot(self.Position[0].longitude + distance *np.cos(an),self.Position[0].latitude + distance *np.sin(an) ,color=couleur.name()) 

   
                    self.plotsObj.append(plotsObj)
                
#                self.canvas.blit(self.axes.bbox)
#                self.canvas.update()
#                self.canvas.flush_events()
           
           

                
                
            if self.scan[i].Type == PLOTType.ANGULAR or self.scan[i].Type == PLOTType.ANGULAR2D :
        
                if self.plotsObj:
                    for u in self.plotsObj:
                        self.axes.lines.remove(u)
                    self.plotsObj=[]
                    
                for plot in  self.scan[i].plots:     
                    pos1 =position.Position()
                    pos1.setXYZ(self.scan[i].location.x + self.sensorCoverage.distanceMin * np.cos( np.pi/2 - (self.direction*np.pi/180 + plot.theta)), self.scan[i].location.y +self.sensorCoverage.distanceMin* np.sin( np.pi/2 - (self.direction*np.pi/180 + plot.theta)) ,0.0)
                    pos2 =position.Position()
                    pos2.setXYZ(self.scan[i].location.x +  self.sensorCoverage.distanceMax* np.cos( np.pi/2 - (self.direction*np.pi/180 + plot.theta)), self.scan[i].location.y +self.sensorCoverage.distanceMax* np.sin( np.pi/2 - (self.direction*np.pi/180 + plot.theta)) ,0.0)
                   
#                    if len(self.scan[i].plots)==1:
                    
                    latitude  = [pos1.latitude,pos2.latitude]
                    longitude = [pos1.longitude,pos2.longitude]
                    
#                    else:
#                    
#                        latitude.append( [pos1.latitude,pos2.latitude])
#                        longitude.append( [pos1.longitude,pos2.longitude])
        
                    #if longitude and latitude:
              
              
                    

                    obj,  = self.axes.plot(longitude,latitude,'k--' , linewidth= 1  )
                    self.plotsObj.append(obj)
                    self.axes.draw_artist(obj) 
                    
                    
    
                    
    def clear(self):  
 
 
        if self.plotsObj != []:
            for u in self.plotsObj:
                 self.axes.lines.remove(u)
 
        self.plotsObj= []

        self.scan = None
 
        
        if self.ellipsesObj != []:
             for _e in self.ellipsesObj:
                 _e.remove()
             self.ellipsesObj = []
        
        if self.iconeObj != []:
                 for _e in self.iconeObj:
                     _e.remove()
                 self.iconeObj = []         
             
    def displayScan(self,axes = None, canvas = None):
        
         x = []
         y = []
         
         
        #  if self.plotsObj != []:
        #     for u in self.plotsObj:
        #          self.axes.lines.remove(u)
        #     canvas.draw_idle()
        #     self.plotsObj= []
        #  if self.ellipsesObj != []:
        #      for _e in self.ellipsesObj:
        #          _e.remove()
        #      self.ellipsesObj = []
         couleur = QColor(Qt.darkGreen)  
         red = QColor(Qt.red)
         _linestyle='' 
         if self.scan==None:
             return
         
         self.clearScanData(canvas,axes)
         #================================
         # display tracks internat track 
         #================================
         for _track in self.scan.tracks:

               if _track.type  == PLOTType.POLAR_TRACK or _track.type  == PLOTType.SPHERICAL_TRACK:
                   #display location
                   

                   x.append(_track.Position.longitude) 
                   y.append(_track.Position.latitude)
        
               self.textPlotsObj.append(axes.text(_track.Position.longitude, _track.Position.latitude, 'track : ' + str(_track.id),  color=couleur.name() ))
         if x!=[] and y !=[]:
             
 
            obj,  = axes.plot(x,y , marker='+', color=couleur.name(), ls=_linestyle )
            self.plotsObj.append(obj) 
            
         #================================
         # display tracks internat plot 
         #================================               
         x = []
         y = []
     
         for _det in self.scan.plots:
             
#               print('------------------')
#               print(_det.Classification)
#               print(_det.ProbaClassification)
#               print(_det.info_1)
#               print(_det.value_info_1)
#               print(_det.info_2)
#               print(_det.value_info_2)
                    
               if _det.type  == PLOTType.POLAR or _det.type  == PLOTType.SPHERICAL:
                   #display location
                   x.append(_det.Position.longitude) 
                   y.append(_det.Position.latitude)
   
                   #display covariances
                   #attention with et height en m à conevertir en wgs84
            
                   if self.displayCovariance:
            
                       pos = Position()
                       pos.setXYZ(_det.Position.x_ENU + _det.width, _det.Position.y_ENU + _det.height,0,'ENU')
      
                    
                       e1 = patches.Ellipse((x[-1], y[-1]), np.abs(x[-1] - pos.longitude), np.abs(y[-1] - pos.latitude), angle=_det.angle  )
                       
                       e1.set_alpha(0.5)
                       e1.set_facecolor( couleur.name())
                       self.axes.add_patch(e1) 
                       
                       self.ellipsesObj.append(e1)
                   _linestyle=''
                   
                   
                   # =============================
                   # display image
                   # =============================
                   if self.displayIcone:
                       icone = 'icones_target/unknown.png'
                       for _t in TARGET_TYPE:

                           if _t.name == _det.Classification:
                               icone = _t.value.icone
                               print(icone)
                               break
                           
                       self.iconeObj.append(imscatter(_det.Position.longitude, _det.Position.latitude, icone, self.axes))
                       
                       
              
               if self.node!=None and (_det.type  == PLOTType.ANGULAR or _det.type  == PLOTType.ANGULAR2D) :
          
                    Emprise = None
                    Pos = self.node.Position
                    dmin = -1
                    dmax = 10
                    for _cover in self.sensorCoverage:
                        if (dmin ==-1 and _cover.name == TARGET_TYPE.UNKNOWN) or _cover.name.name == _det.Classification:
                            dmin = _cover.distanceMin
                            dmax = _cover.distanceMax
                            
                    pos1 = Position()
                    pos1.setXYZ(Pos.x_UTM + dmin * np.cos( np.pi/2 - (self.node.Orientation.yaw*np.pi/180 + _det.theta*np.pi/180 )), Pos.y_UTM  +dmin* np.sin( np.pi/2 - (self.node.Orientation.yaw*np.pi/180 + _det.theta*np.pi/180 )) ,0.0)
                    pos2 = Position()
                    pos2.setXYZ(Pos.x_UTM  + dmax* np.cos( np.pi/2 - (self.node.Orientation.yaw*np.pi/180 + _det.theta*np.pi/180 )), Pos.y_UTM  +dmax* np.sin( np.pi/2 - (self.node.Orientation.yaw*np.pi/180 + _det.theta*np.pi/180 )) ,0.0)
                   
            
                    
                    latitude  = [pos1.latitude,pos2.latitude]
                    longitude = [pos1.longitude,pos2.longitude]
   
                    _linestyle='dashed' 
                    obj,  = self.axes.plot(longitude,latitude,'k--' , linewidth= 1  )
                    self.plotsObj.append(obj)
                    #axes.draw_artist(obj) 

         
         
            #plotsObj, = self.axes.scatter(box_coords, marker='o', c='r', edgecolor='b')
            #plotsObj,  = self.axes.plot(self.Position[0].longitude + distance *np.cos(an),self.Position[0].latitude + distance *np.sin(an) ,color=couleur.name()) 
            #self.axes.plot(box_coords,color=couleur.name())
            
         if x!=[] and y !=[]:
         
   
            #axes.scatter(x,y)
            obj,  = axes.plot(x,y, marker='o', color=couleur.name(), ls=_linestyle )
            self.plotsObj.append(obj)

            axes.draw_artist(obj )
           # 
            canvas.blit( axes.bbox)
            #canvas.draw_idle()
#         canvas.update()
#         canvas.flush_events()  
    
    def start(self):
        self.lastScanTime = _timer.getReferenceTime()
    
    def getGroundTruth(self, currentTime,   targets):

        flagCycle = False

        if self.lastScanTime.msecsTo(currentTime)*0.001 >=self.timeOfSampling:
                self.lastScanTime = currentTime            
                flagCycle = True
 
        if flagCycle == False:
            return []

        volumeMax   = 0
        pfa         = 0
        pd          = 0
        _coverMax   = None
        if self.sensorCoverage:
         for _cover in self.sensorCoverage:
             _volume = _cover.fov_elevation*np.pi/180.0 * _cover.fov * np.pi/180.0*np.abs(_cover.distanceMax - _cover.distanceMin)
             if _volume >   volumeMax:
                 volumeMax = _volume
                 _coverMax = _cover
                 pfa       = _cover.parameters.pfa
                 pd        = _cover.parameters.pd

        #=============================
        #détections issues des cibles
        #=============================

        ground_truth = np.zeros((len(targets),3))

        got_one = False

        for k,_target in enumerate(targets):

            flag, PositionAtTime,velocity = _target.positionAtTime( currentTime)

            if flag and self.isInFOV(PositionAtTime,_target.type) and self.isDetectable(PositionAtTime,_target.altitude):
                ground_truth[k,0] = PositionAtTime.x
                ground_truth[k,1] = PositionAtTime.y
                ground_truth[k,2] = 1
                got_one = True
        # In case no target can be observed, the gospa still needs to be computed
        if not(got_one == True):
            ground_truth[:,2]=2

        return ground_truth
 
    def run(self):
  
           if self.currentTime!=None:
                 #if self.mutex.tryLock() :
                     self.detection(self.currentTime)
                     self.currentTime = None
                     #self.mutex.unlock()
            
    def receiveTime(self,currentTime):
    
    
        self.currentTime = currentTime
        self.run()
   
       
      
             
  
    
   
    def detection(self,currentTime):
     
        if self.realData:
            if self.scan !=None:
                self.newScan.emit(self.scan)
            return

        self.updateLocationOrientation()

#        _scan.sensorPosition    = self.position
#        _scan.sensorOrientation = self.orientation
        
        
        flagCycle = False

        if self.scan !=None:
            self.lastScanTime = self.scan.dateTime
            del self.scan
            self.scan=None
        # print(currentTime.toString("hh:mm:ss.z"))
        # print(self.lastScanTime.toString("hh:mm:ss.z"))   
        # print(self.lastScanTime.msecsTo(currentTime)*0.001 ) 
        if self.lastScanTime.msecsTo(currentTime)*0.001 >=self.timeOfSampling:
                #print(self.lastScanTime.msecsTo(currentTime)*0.001 ) 
                #print(['sensor id: ', str(self.id),' ',str(self.lastScanTime.msecsTo(currentTime)*0.001) , ' : time of sammp : ' , str(self.timeOfSampling)])
                flagCycle = True
    
  
        if flagCycle == False:
            return
       
        _scan = Scan(currentTime,self)
        if self.internalTracker==False:
            self.setScanType(_scan)
        if self.internalTracker==True:   
            self.setScanTrackType(_scan)
        
        self.updateLocationOrientation()
        _scan.sensor = self
        _scan.sensorPosition = self.position
        _scan.sensorOrientation = self.orientation
   
        volumeMax   = 0
        pfa         = 0
        pd          = 0
        _coverMax   = None
        if self.sensorCoverage:
         for _cover in self.sensorCoverage:
             _volume = _cover.fov_elevation*np.pi/180.0 * _cover.fov * np.pi/180.0*np.abs(_cover.distanceMax - _cover.distanceMin)
             if _volume >=   volumeMax:
                 volumeMax = _volume
                 _coverMax = _cover
                 pfa       = _cover.parameters.pfa
                 pd        = _cover.parameters.pd
     
        #=============================
        #détections issues des cibles
        #=============================
       
        for k,_target in enumerate(self.targets):

            flag, PositionAtTime,velocity = _target.positionAtTime( currentTime)
            #if flag :
                
            #print('in sensor detection : '+str(currentTime.toString('hh:mm:ss.z')) +' position : {0}, {1}'.format(PositionAtTime.and self.isDetectable(PositionAtTime,_target.altitude) x_ENU,PositionAtTime.y_ENU) )
   
            if flag and self.isInFOV(PositionAtTime,_target.type,currentTime)   and random.uniform(0, 1) <pd: #and self.isDetectable(PositionAtTime,_target.altitude) 
             
                _class, _ProbaClass = self.sensorClassification(_target.type,PositionAtTime)
                _url                = self.sensorURL(_target.type )
                gabarit             =   _target.type.value.gabarit
                surface_target      = gabarit[0]*gabarit[1]*gabarit[2]  + np.random.randn(1)[0]
                _ser                = SER(_target.type)
                if self.mode == SensorMode.radar or  self.mode == SensorMode.radar3D:
                    infos               = np.array([['target size',surface_target],['SER',_ser]])
                else : 
                    infos               = np.array(['target size',surface_target] )
                
                if self.internalTracker==False:
                    _scan.addPlot(PositionAtTime,_target.id,_target.type.name,currentTime,_class, _ProbaClass,infos,_url)
                else:
                    _idTrack = -1;
                    for _li in self.targetTable :
                        if str(_target.id) in _li:
                            _idTrack = _li[1]
                    if _idTrack==-1:
                        self.numTrack +=1
                        self.targetTable.append([str(_target.id), self.numTrack]) 
                        _idTrack = self.numTrack
                        
                    _scan.addTrack(PositionAtTime,velocity, _idTrack,_target.type.name,currentTime,_class, _ProbaClass,np.array(['target size',surface_target]),_url)
#            else  :
#                  if self.internalTracker:
#                   self.numTrack +=1
#                   self.targetTable.append([str(_target.id), self.numTrack]) 
        #=============================
        # génération des fausses alarmes
        #=============================   

#        if self.mode == SensorMode.radar3D:
#                    nb_cellules = self.sensorCoverage.distanceMax/self.resolution.rho* self.sensorCoverage.fov/self.resolution.theta*self.sensorCoverage.fov_elevation/ self.resolution.phi;
#        if self.mode == SensorMode.radar:
#                    nb_cellules = self.sensorCoverage.distanceMax/self.resolution.rho* self.sensorCoverage.fov/self.resolution.theta ;
#        if self.mode == SensorMode.optroIR or self.mode == SensorMode.optroVIS:
#                    nb_cellules =   self.sensorCoverage.fov/self.resolution.theta*self.sensorCoverage.fov_elevation/ self.resolution.phi ;
#        if  self.mode == SensorMode.optroIR2D:
#                    nb_cellules =  self.sensorCoverage.fov/self.resolution.theta  ;
#        if  self.mode == SensorMode.PIR:
#                    nb_cellules =  self.sensorCoverage.fov/self.resolution.theta  ;
#        if  self.mode == SensorMode.sismo:
#                    nb_cellules =  self.sensorCoverage.distanceMax/self.resolution.rho;
        lamda_fa = pfa;#*nb_cellules# 

        m_fa   = np.random.poisson(lamda_fa*volumeMax);

        if _coverMax!=None and m_fa> 0 and m_fa <=50:
          [rho_fa,theta_fa,phi_fa]      = [np.random.uniform(_coverMax.distanceMax,_coverMax.distanceMin,m_fa),np.random.uniform(-_coverMax.fov/2*np.pi/180,_coverMax.fov/2*np.pi/180,m_fa), np.random.uniform(-_coverMax.fov_elevation/2*np.pi/180,_coverMax.fov_elevation/2*np.pi/180,m_fa)]  
          _intclasses                   = np.random.randint(0,len(TARGET_TYPE)-1,m_fa)
          _probas                       = np.random.uniform(0,1,size=(len(TARGET_TYPE),m_fa))
          
          infos                         = []
          infosSER                      = []
          _classes                      = []
     
          for u in range(0,m_fa):
              for ku,_type in enumerate(TARGET_TYPE):
                  if ku == _intclasses[u]:
                      TT        = _type
               
                      break
                  
              _classes.append(TT.name)
              
              gabarit             =   TT.value.gabarit
              
         
              if self.mode == SensorMode.radar or  self.mode == SensorMode.radar3D:
                  infos.append([['target size', gabarit[0]*gabarit[1]*gabarit[2] + np.random.randn(1)[0]],['SER',SER(TT)]])
              else:
                  infos.append(['target size', gabarit[0]*gabarit[1]*gabarit[2] + np.random.randn(1)[0]])
      
          if self.internalTracker==False:
              _scan.addFa([rho_fa,theta_fa,phi_fa],currentTime,_classes,_probas,infos);        
          else :
              _scan.addFalseTrack([rho_fa,theta_fa,phi_fa],currentTime,_classes,_probas,infos);
              
        self.scan = _scan
        
        if self.scan.tracks!=[] or self.scan.plots!=[]:
            self.newScan.emit(_scan)
        
    def drawAllDetections(self):
         sensorLoc   = np.array([self.location]) 
         for scan in self.scan:
             for _plot in scan.plots:
                 x = _plot.rho * np.cos(np.pi/2 - _plot.theta)
                 y = _plot.rho * np.sin(np.pi/2 - _plot.theta)
                 plt.plot(x+sensorLoc[0,0],y+sensorLoc[0,1],'m+')
    
    def set_visible(self, _checkstate):
    
        flag = True
        
        if _checkstate ==  Qt.Unchecked:
             flag = False
             
        self.locationIsVisible = flag
 
        if  self.trajObj:
            self.trajObj.set_visible(flag)
        if  self.textObj:
            self.textObj.set_visible(flag)  
        if  self.coverAreaObj!=[]:
            for u in self.coverAreaObj:
                u.set_visible(flag) 
 
            
            
    def addConnection(self,id):
        self.connections.append(id)
    def addResolutionCell(self,rho,theta,phi):

        self.resolution.rho     = rho
        self.resolution.phi     = phi  
        self.resolution.theta   = theta  
    def setScanTrackType(self,_scan =Scan()): 
        if self.mode == SensorMode.radar:
            _scan.plotType = PLOTType.POLAR_TRACK
        if self.mode == SensorMode.optroVIS:     
            _scan.plotType = PLOTType.ANGULAR2D_TRACK
        if self.mode == SensorMode.optroIR:     
            _scan.plotType = PLOTType.ANGULAR2D_TRACK
        if self.mode == SensorMode.radar3D:     
            _scan.plotType = PLOTType.SPHERICAL_TRACK
        if self.mode == SensorMode.gonio:     
            _scan.plotType = PLOTType.ANGULAR2D_TRACK
        if self.mode == SensorMode.optroIR2D:     
            _scan.plotType = PLOTType.ANGULAR2D_TRACK
        if self.mode == SensorMode.accoustic:
            _scan.plotType = PLOTType.ANGULAR2D_TRACK
            
    

    def setScanType(self,_scan =Scan()):
    
       
        if self.mode == SensorMode.radar:
            _scan.plotType = PLOTType.POLAR
        if self.mode == SensorMode.optroVIS:     
            _scan.plotType = PLOTType.ANGULAR
        if self.mode == SensorMode.optroIR:     
            _scan.plotType = PLOTType.ANGULAR
        if self.mode == SensorMode.sismo:
            _scan.plotType= PLOTType.DISTANCE
        if self.mode == SensorMode.radar3D:     
            _scan.plotType = PLOTType.SPHERICAL
        if self.mode == SensorMode.gonio:     
            _scan.plotType = PLOTType.ANGULAR2D
        if self.mode == SensorMode.optroIR2D:     
            _scan.plotType = PLOTType.ANGULAR2D
        if self.mode == SensorMode.alarm:
            _scan.plotType = PLOTType.EVENT
        if self.mode == SensorMode.PIR:
            _scan.plotType = PLOTType.PIR_EVENT
        if self.mode == SensorMode.accoustic:
            _scan.plotType = PLOTType.ANGULAR2D