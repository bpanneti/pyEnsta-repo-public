# -*- coding: utf-8 -*-
"""
Created on Thu Jan 23 08:48:41 2020

@author: bpanneti
"""

# -*- coding: utf-8 -*-
"""
Created on Fri Jul 12 11:20:40 2019

@author: bpanneti
"""


from point import Position,Velocity
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtOpenGL import *
from PyQt5.QtWidgets import *
#from style import Style
 
import numpy as np   
from enum import Enum 
from scipy import interpolate
from collections import namedtuple

iconValide      =  "icones/valid.png"
iconNotValide   = "icones/notValid.png"
 
from point import Position,REFERENCE_POINT 
from orientation import Orientation         
import myTimer as _timer 

def compte():   
    global compteur
    compteur += 1
 
compteur = -1

TYPE  = namedtuple('MobileNodeType', ['value', 'gabarit','icone','velocity'])

class MOBILE_NODE_TYPE(Enum):
 
    #TYPE , Gabarit in m (lxLxH), icon path, velocity min max in m/s
    UNKNOWN     = TYPE(0,  [-1,-1,-1], 'icones/unknown.png', [0,30])
    UAV         = TYPE(1,  [0.5,0.8,1.8], 'icones/drone.png',     [0,18])
    UGV         = TYPE(2 , [1.8,4.2,2.0], 'icones/ugv.png',     [0,5])
    TANK        = TYPE(4,  [2.5,5.0,3.5], 'icones/tank.png',    [0,18])
    VEHICLE     = TYPE(5,  [2.3,12.0,3.5],'icones/car.png',   [0,20])
      
 
        
class MobileNode(QWidget):
 
        
    #Messagerie
            
    message = pyqtSignal('QString');
    
    def __init__(self):
        super(MobileNode, self).__init__()  
 
        self.name               = 'UNKNOWN'
        compte()
        self.id                 = str(compteur)
        self.sensors            = []                 # sensor object list                 
        self.typeNode           = MOBILE_NODE_TYPE.UNKNOWN
        self.trajectoryWayPoints= [] #WayPoints, list of Position 
        self.timeToWayPoints    = [] #List of arrival Time to waypoints  in QDateTime   
        self.trajectory         = [] #Position list of split trajectory
        self.velocityToWayPoints= [] #Velocity of split trajectory
        self.startVelocity      = 10 #Initiale velocity (in m/s) uniform
        self.altitude           = 0  #ALtitude (in m)  
        self.startTime          = _timer.getReferenceTime() #Start datetime of target 
        self.isRandomVelocity   = False #random velocity
        self.isSplinTrajectory  = False #splin the trajectory
        self.degreeOfTheSpline  = 3 #3 is the recommended degree for spline in scipy
        self.synchronized       = False #si données jouées en réseau
        
        self.tracker            = None
        #=====================
        # objets graphiques
        #=====================
        self.selectedNode           = False              # node selection  
     
        self.color                  = QColor('blue') #target color
        self.trajectoryObj          = None#target trajecory graphic object
        self.textObj                = None#target text graphic object
        self.locationObj            = None#target location graphic object
        self.marker                 = '+'#target marker graphic object
        self.width                  = 1 #target line width graphic object
        self.style                  ='-'#target line style graphic object

        
        self.locationIsVisible      = True #target visible on graphic 
    
        
        self.axes                   = None #axes object 
        self.canvas                 = None #canvas object 

      
        
        
        #---> Accès au tree widget 

        self.treeWidgetItem         = None #item widget object 
        #booleen de sélection de la cible
        
        self.selectedTarget         = False #selection of the target
    
    def toJson(self,dateTime = QDateTime(),ADRESS_IP = ''):
        
             flag, PositionAtTime,velocity = self.positionAtTime(dateTime)
             orientation = self.orientationAtTime(dateTime)
             if flag == False :
                 return ''
             adress = "135.125.1."+str(self.id)
            
             json = str('{  \
                         "attitude": { \
                                  "yaw": '+  str(orientation.yaw)+',\
                                  "pitch":'+ str(orientation.pitch)+',\
                                  "roll": '+ str(orientation.roll)+'\
                                  },\
                                  "code": 2,\
                                  "id": "'+adress+'",\
                                  "network": "'+ADRESS_IP+'",\
                                  "name": "super bawl",\
                                  "color": "#00000",\
                                  "ressource": ":_Myressource",\
                                  "nodeType": "'+self.typeNode.name+'",\
                                  "message": "running",\
                                  "date" : "'+ dateTime.toString("yyyy-MM-dd HH:mm:ss.z") +'",\
                                  "position": {\
                                          "altitude": ' +str(PositionAtTime.altitude)+',\
                                          "latitude": ' +str(PositionAtTime.latitude)+',\
                                          "longitude":' +str(PositionAtTime.longitude)+',\
                                          "format":"WGS84"\
                                          },\
                                "velocity": {\
                                        "velocity": '+str(velocity.norm())+',\
                                        "yaw": '+  str(orientation.yaw)+',\
                                        "pitch":'+ str(orientation.pitch)+',\
                                        "roll": '+ str(orientation.roll)+',\
                                        "format":"YPR"\
                                         },\
                                 "state": "running"\
                                 }')
     
             return json
    def containsSensor(self,_sensorId = 0):
         for u in self.sensors:
             if u.id == _sensorId:
                 return True
         return False      
    def removeSensor(self,_sensorId = 0):
        for u in self.sensors:
             if u.id == _sensorId:
                 self.sensors.remove(u)
                 return True
        return False  
    def set_visible(self,_checkstate):
    
        
        flag = True
        
        if _checkstate ==  Qt.Unchecked:
             flag = False
             
        self.locationIsVisible = flag
 
        if  self.trajectoryObj:
            self.trajectoryObj.set_visible(flag)
        if  self.textObj:
            self.textObj.set_visible(flag)  
        if  self.locationObj:
            self.locationObj.set_visible(flag) 
        
    def clear(self, axes, canvas):
        if self.locationObj !=None:
            axes.lines.remove(self.locationObj)
            self.locationObj = None
        if self.textObj !=None:
            self.textObj.remove()
            self.textObj =None   
        if   self.trajectoryObj !=None:
            axes.lines.remove(self.trajectoryObj)
            self.trajectoryObj = None
            
    def displayCurrentTime(self,_currentTime, axes,canvas):
        
        if self.axes == None:
            self.axes = axes
        if self.canvas == None:
            self.canvas = canvas
            
 
        if self.locationObj !=None:
            self.axes.lines.remove(self.locationObj)
            self.canvas.draw_idle()
            self.locationObj = None
 
       
       
        if self.textObj !=None:
            self.textObj.remove()
            self.canvas.draw_idle()
            self.textObj =None 
 
  

        
        flag, PositionAtTime,VelocityTime = self.positionAtTime(_currentTime)

        
        if  flag == True: 
            latitude    = PositionAtTime.latitude
            longitude   = PositionAtTime.longitude 
 
            self.locationObj,   = self.axes.plot(longitude,latitude,color = self.color.name() , linewidth= 2,marker = 'o',markerfacecolor = 'blue',markersize = 4,visible = self.locationIsVisible )
            self.textObj        = self.axes.text(longitude,latitude, 'mobile Node : '+ str(self.id)+' / '+ str(self.name),   bbox={'facecolor':'red', 'alpha':0.5, 'pad':10} ,visible= self.locationIsVisible  )

            for _sensor in self.sensors:
                _sensor.toDisplay(axes,canvas,_currentTime)
            self.axes.draw_artist(self.locationObj )
            self.axes.draw_artist(self.textObj )  
            self.canvas.draw_idle()
            #self.canvas.blit(self.axes.bbox)
            #self.canvas.update()
            #self.canvas.flush_events()
            #self.canvas.draw_idle()
   
    def toUndisplay(self):
         if self.locationObj !=None:
            self.axes.lines.remove(self.locationObj)
            self.locationObj = None
  
       
         if self.textObj !=None:
            self.textObj.remove()
            self.textObj =None 
         if   self.trajectoryObj !=None:
            self.axes.lines.remove(self.trajectoryObj)
            self.trajectoryObj = None
    def toDisplay(self, axes, canvas):
 
 
        if axes==None:
            return
        if self.trajectory==[]:
            return
        if self.axes == None or self.axes !=axes:
            self.axes = axes
        if self.canvas == None or self.canvas !=canvas:
            self.canvas = canvas
            
 
 
        
        latitude  = []
        longitude = []
        altitude  = []
 
        for i in range(len(self.trajectory)):
            latitude.append(self.trajectory[i].latitude)
            longitude.append(self.trajectory[i].longitude)
            altitude.append(self.trajectory[i].altitude)
      

  
        if self.locationObj !=None:
            axes.lines.remove(self.locationObj)
            self.locationObj = None
  
        self.locationObj, =  axes.plot(longitude[0],latitude[0],color = self.color.name(),marker = self.marker, linewidth= 2,visible =self.locationIsVisible) #
      
        if self.textObj !=None:
            self.textObj.remove()
            self.textObj =None 
       
       
        self.textObj = axes.text(longitude[0],latitude[0] , 'mobile node : '+ str(self.id) +' / '+ str(self.name),   bbox={'facecolor':'white', 'alpha':0.5, 'pad':10},visible =self.locationIsVisible )
  
        if   self.trajectoryObj !=None:
            axes.lines.remove(self.trajectoryObj)
            self.trajectoryObj = None
    
        self.trajectoryObj, =  axes.plot(longitude,latitude,color = self.color.name(),marker = self.marker, linewidth= 2,visible =self.locationIsVisible) #
#        self.canvas.blit(axes.bbox)
#        self.canvas.update()
#        self.canvas.flush_events()
        for _sensor in self.sensors:
          print ('in sensor display')
          _sensor.toDisplay(axes,canvas,self.startTime)
          
    def setWayPoints(self, wayPoints=[]):
        #WayPoinst in WGS84
        if len(wayPoints)>0:
            self.trajectoryWayPoints.clear()
        for pos in wayPoints:
            
            self.trajectoryWayPoints.append(Position(pos[1],pos[0],self.altitude))
        self.update()
        
    def setTreeWidget(self, treeWidget = QTreeWidgetItem()):
   
        self.treeWidgetItem = treeWidget
        self.isValid()
#        
#        _itm1 =  QTreeWidgetItem(treeWidget ,['','location',''])
#        _itm1.setCheckState(0, Qt.Checked)
#        _itm1.setFlags(_itm1.flags() | Qt.ItemIsUserCheckable)
#       
#        _itm2 =  QTreeWidgetItem(treeWidget ,['','trajectory',''])
#        _itm2.setCheckState(0, Qt.Checked)
#        _itm2.setFlags(_itm2.flags() | Qt.ItemIsUserCheckable)
#          
#        _itm3 =  QTreeWidgetItem(treeWidget ,['','label',''])
#        _itm3.setCheckState(0, Qt.Checked)
#        _itm3.setFlags(_itm3.flags() | Qt.ItemIsUserCheckable)
      
 #       self.update()
        
    def update(self):
        
       
             
            
        if self.treeWidgetItem:
            self.treeWidgetItem.setText(1,self.name)
            self.treeWidgetItem.setText(2,self.typeNode.name)
            self.treeWidgetItem.setForeground(0,QBrush(self.color))
            self.treeWidgetItem.setForeground(1,QBrush(self.color))
            self.treeWidgetItem.setForeground(2,QBrush(self.color))
      
            if self.isValid():
                self.treeWidgetItem.setIcon(0, QIcon(QPixmap(iconValide)))
            else:
                self.treeWidgetItem.setIcon(0,QIcon(QPixmap(iconNotValide)))  
                
    def editNode(self):
 
        self.d = QDialog()
        
        layout              = QVBoxLayout()
        targetName          = QLabel('Node name')
        targetType          = QLabel('Node type')
        targetLocation      = QLabel('Node''s location')
        targetColor         = QLabel('Node color')
        targetStartTime     = QLabel('Node start date time ')
        targetStartVelocity = QLabel('Node start velocity (in m/s)')
        targetAltitude      = QLabel('Node start altitude (in m)')
        
        self.targetNameEdit      = QLineEdit()
     
        if self.name!='':
            self.targetNameEdit.setText(self.name)
            
        self.targetTypeEdit      = QComboBox() 
        for type_t in MOBILE_NODE_TYPE:
            self.targetTypeEdit.addItem("%s"% type_t.name)
        
        if self.typeNode:
            self.targetTypeEdit.setCurrentText("%s"% self.typeNode.name)

        self.targetStartTimeEdit      = QDateTimeEdit()
        self.targetStartTimeEdit.setDisplayFormat("yyyy-MM-dd HH:mm:ss.zzz")
        self.targetStartTimeEdit.setDateTime(self.startTime)
  
        self.targetStartVelocityEdit      = QLineEdit()
        self.targetStartVelocityEdit.setText(str(self.startVelocity))
        
        self.targetAltitudeEdit = QLineEdit()
        self.targetAltitudeEdit.setText(str(self.altitude))

        #self.targetStartVelocityEdit.setEnabled(bool(not self.isRandomVelocity))
        self.randomVelocityBox               = QCheckBox()
        self.randomVelocityBox.setChecked(self.isRandomVelocity)
        #self.randomVelocityBox.stateChanged.connect(self.randomVelocity)
        self.randomVelocityBox.setText("random velocity")
        
        self.splinTrajectoryBox               = QCheckBox()
        self.splinTrajectoryBox.setChecked(self.isSplinTrajectory)
        #self.randomVelocityBox.stateChanged.connect(self.randomVelocity)
        tmp = "Splin trajectory\n(only if the number of locations\nis more than "+str(self.degreeOfTheSpline+1)+")"
        self.splinTrajectoryBox.setText(tmp)
        
        self.targetLocationEdit  = QTableWidget()
        self.targetLocationEdit.setColumnCount(4) 
        self.targetLocationEdit.setHorizontalHeaderLabels(["longitude", "latitude","altitude","dateTime"])
 
        for location_t in self.trajectoryWayPoints:
            rowPosition = self.targetLocationEdit.rowCount() ;
            self.targetLocationEdit.insertRow(rowPosition)
            self.targetLocationEdit.setItem(rowPosition , 0, QTableWidgetItem(str(location_t.longitude)) )
            self.targetLocationEdit.setItem(rowPosition , 1, QTableWidgetItem(str(location_t.latitude)) ) 
            self.targetLocationEdit.setItem(rowPosition , 2, QTableWidgetItem(str(location_t.altitude)) )
      
        for i in range(len(self.timeToWayPoints)):
             time =  self.timeToWayPoints[i]
             self.targetLocationEdit.setItem(i ,3, QTableWidgetItem(time.toString("yyyy-MM-dd HH:mm:ss.zzz")))
          
        self.targetLocationEdit.resizeColumnsToContents()
        self.targetLocationEdit.setContextMenuPolicy(Qt.CustomContextMenu)
        self.targetLocationEdit.customContextMenuRequested.connect(self.openMenu)
       
        
        self.targetColorEdit     = QPushButton()
        self.targetColorEdit.clicked.connect(self.changeColor)
        
        self.targetColorEdit.setToolTip("change color")
        self.targetColorEdit.setStyleSheet("background-color: %s" % self.color.name())
 
        grid = QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(targetName, 1, 0)
        grid.addWidget(self.targetNameEdit, 1, 1)

        grid.addWidget(targetType, 2, 0)
        grid.addWidget(self.targetTypeEdit, 2, 1)
        
        grid.addWidget(targetColor, 3, 0)
        grid.addWidget(self.targetColorEdit, 3, 1)
        
        grid.addWidget(targetStartTime, 4, 0)
        grid.addWidget(self.targetStartTimeEdit, 4, 1)
        
               
        grid.addWidget(targetStartVelocity, 5, 0)
        grid.addWidget(self.targetStartVelocityEdit, 5, 1)
        grid.addWidget(self.randomVelocityBox,6,0)
        grid.addWidget(self.splinTrajectoryBox,6,1)
        
        grid.addWidget(targetLocation, 7, 0)
        grid.addWidget(self.targetLocationEdit, 7, 1)
        

        grid.addWidget(targetAltitude, 8, 0)
        grid.addWidget(self.targetAltitudeEdit, 8, 1)
        layout.addLayout(grid)
        
        buttonLayout = QHBoxLayout();
        
        but_refresh = QPushButton("refresh")
        buttonLayout.addWidget(but_refresh )
        but_refresh.clicked.connect(self.OnRefresh)
        
        but_ok = QPushButton("OK")
        buttonLayout.addWidget(but_ok )
        but_ok.clicked.connect(self.OnOk)

        but_cancel = QPushButton("Cancel")
        buttonLayout.addWidget(but_cancel )
        but_cancel.clicked.connect(self.OnCancel)
        
        layout.addLayout(buttonLayout)
        
        
        
        self.d.setLayout(layout)
        self.d.setGeometry(300, 300, 350, 300)
        self.d.setWindowTitle("edit Node")
        self.d.setWindowIcon(QIcon('icones/mobileNode.png'))
        self.d.setWindowModality(Qt.ApplicationModal)
        
        
        
        
        return self.d.exec_() 
    
    def buildTrajectory(self):
        
     
        self.timeToWayPoints    = [] #Arrival Time to waypoints      
        self.velocityToWayPoints = [] #Arrival velocity to waypoints     
        if len(self.trajectoryWayPoints )  <2 or self.startVelocity <= 0:   
            return False    
       
        self.trajectory         = []
        if self.isSplinTrajectory == True   :
            latitude    =[]
            longitude   = []
            for i in range(len(self.trajectoryWayPoints)):
                longitude.append(self.trajectoryWayPoints[i].longitude)
                latitude.append(self.trajectoryWayPoints[i].latitude)

            if len(longitude)>self.degreeOfTheSpline: 
                tck,u=interpolate.splprep([longitude,latitude],k=self.degreeOfTheSpline,s=0.0)
                x_i,y_i= interpolate.splev(np.linspace(0,1,100),tck)
                latitude = y_i
                longitude = x_i
            
                for i in range(len( longitude)):
                    point = Position(latitude[i],longitude[i],self.altitude)
                    self.trajectory.append(point)
            else:
                self.isSplinTrajectory = False
        else :
            self.trajectory = self.trajectoryWayPoints
            for i in range(len(self.trajectory)):
                self.trajectory[i].altitude = self.altitude  
            
        self.timeToWayPoints.append(self.startTime) 
        self.velocityToWayPoints.append(self.startVelocity)
        for i in range(len(self.trajectory)-1):

            pointA      = self.trajectory[i]
            pointB      = self.trajectory[i+1]
            distance    = pointA.distanceToPoint(pointB)
            velocity    = self.startVelocity
 
            if self.isRandomVelocity:
       
                velocity = max([self.startVelocity,np.random.random_sample(1)*self.type.value.velocity[1]])
      
            duree       = (distance /  velocity)*1000
 
            _startDate  = self.timeToWayPoints[i]
            _arrivalDate = _startDate.addMSecs(duree)
 
            self.timeToWayPoints.append(_arrivalDate)
 
            self.velocityToWayPoints.append(velocity)
 
        if len(self.trajectory)==len(self.timeToWayPoints) and len(self.trajectory)==len(self.velocityToWayPoints):
            return True
        return False
    def setStartTime(self,currentTime = QDateTime()):
        
        if self.synchronized == True:
            return
        self.startTime = currentTime;
 
        self.buildTrajectory()
        self.synchronized = True
    def orientationAtTime(self,currentTime = QDateTime()):   
        orientation         = Orientation()
        orientation.yaw     = 0
        orientation.pitch   = 0
        orientation.roll    = 0
        if currentTime == None:
            return orientation
        if currentTime <self.startTime:
            return orientation
        for t in range(0,len(self.timeToWayPoints)-1):
  
            if currentTime>=self.timeToWayPoints[t] and currentTime < self.timeToWayPoints[t+1] :
                index = t
                break
        if index!=None:
      
    
            A = np.array([self.trajectory[index].x_UTM,self.trajectory[index].y_UTM])
            B =  np.array([self.trajectory[index+1].x_UTM,self.trajectory[index+1].y_UTM])
            u = B-A
            orientation.yaw = (np.pi/2 - np.arctan2(u[1],u[0])) * 180/np.pi
        return orientation

    def positionAtTime(self,currentTime = QDateTime()):
        
        positionAtTime = Position()
        velocityAtTime = Velocity()
        if currentTime == None:
            return False,positionAtTime,velocityAtTime
        if currentTime <self.startTime:
            return False,positionAtTime,velocityAtTime
        #sinon
    
        index =None    
  
   
        for t in range(0,len(self.timeToWayPoints)-1):
  
            if currentTime>=self.timeToWayPoints[t] and currentTime < self.timeToWayPoints[t+1] :
                index = t
                break
        
 
             
          

        if index!=None:
      
    
            A = np.array([self.trajectory[index].x_UTM,self.trajectory[index].y_UTM])
            diffTime =      self.timeToWayPoints[index].msecsTo(currentTime) /1000 
            B =  np.array([self.trajectory[index+1].x_UTM,self.trajectory[index+1].y_UTM])
            u = B-A
            durationBA = self.timeToWayPoints[index].msecsTo(self.timeToWayPoints[index+1]) /1000 
       
            velocity =  u/durationBA
            #vel = u/np.linalg.norm(u) *velocity
       
            
            #print(vel)
   
            
            Loc = A + diffTime* velocity  
     
            velocityAtTime.setXYZ(velocity[0],velocity[1],0.0,'UTM')
            positionAtTime.setXYZ(Loc[0],Loc[1],self.trajectory[index+1].altitude)
 
#            if self.gis != None:
 #               positionAtTime.altitude = self.Position[index+1].altitude + self.gis.altitude(positionAtT)
            
            self.Position = positionAtTime
            return True,positionAtTime,velocityAtTime
        
        return False,positionAtTime,velocityAtTime
    
    
            
    def isValid(self):
        
        if self.buildTrajectory():
            self.treeWidgetItem.setIcon(0,QIcon(QPixmap(iconValide)))
            return True
        self.treeWidgetItem.setIcon(0,QIcon(QPixmap(iconNotValide)))
        return False;
    def OnCancel(self):
        
        self.d.close()       
    def changeColor(self):
        
        col = QColorDialog.getColor()

        if col.isValid():
            self.targetColorEdit.setStyleSheet("  background-color: %s " % col.name())
    
    def OnRefresh(self):
        
        #permet de rafraichir la trajectoire en fonction des wayPoints et dates
        if self.splinTrajectoryBox.checkState()==Qt.Checked:
            self.isSplinTrajectory      =  True
        else:    
            self.isSplinTrajectory      =  False
            
        if self.randomVelocityBox.checkState()==Qt.Checked:
            self.isRandomVelocity      =  True
        else:    
            self.isRandomVelocity      =  False
        
        for type_t in MOBILE_NODE_TYPE:
            if type_t.name == self.targetTypeEdit.currentText():
                self.typeNode = type_t;
                
        self.startTime      =  self.targetStartTimeEdit.dateTime()
        self.startVelocity  = float(self.targetStartVelocityEdit.text())
        self.altitude       = float(self.targetAltitudeEdit.text()) 
 
        if self.buildTrajectory():
             for i in range(len(self.timeToWayPoints)):
              time =  self.timeToWayPoints[i]
              self.targetLocationEdit.setItem(i ,3, QTableWidgetItem(time.toString("yyyy-MM-dd HH:mm:ss.zzz")))
            
        
    def OnOk(self):
        if self.splinTrajectoryBox.checkState()==Qt.Checked:
            self.isSplinTrajectory      =  True
        else:    
            self.isSplinTrajectory      =  False
            
        if self.randomVelocityBox.checkState()==Qt.Checked:
            self.isRandomVelocity      =  True
        else:    
            self.isRandomVelocity      =  False
 
        if self.isValid()==False:
            self.d.close()    
   
        self.color                  = self.targetColorEdit.palette().button().color()
        self.name                   = self.targetNameEdit.text()
        self.type                   = MOBILE_NODE_TYPE[str(self.targetTypeEdit.currentText())] 
        self.startTime              =  self.targetStartTimeEdit.dateTime()
        self.startVelocity          = float(self.targetStartVelocityEdit.text())
        self.altitude               = float(self.targetAltitudeEdit.text()) 
        
        for type_t in MOBILE_NODE_TYPE:
            if type_t.name == self.targetTypeEdit.currentText():
                self.typeNode = type_t;
        
        self.treeWidgetItem.setText(2,self.typeNode.name)
        self.toDisplay(self.axes,self.canvas)
      
        self.d.accept() 
    def openMenu(self,position):
  
        menu = QMenu()
        deleteAction = menu.addAction("delete point")
        action = menu.exec_(self.targetLocationEdit.mapToGlobal(position))
        if action == deleteAction:
            index = self.targetLocationEdit.currentRow()  
            self.trajectoryWayPoints = self.trajectoryWayPoints[:index] + self.trajectoryWayPoints[index+1 :]
  
    
            for location_t in self.trajectoryWayPoints:
                rowPosition = self.targetLocationEdit.rowCount() ;
                self.targetLocationEdit.insertRow(rowPosition)
                self.targetLocationEdit.setItem(rowPosition , 0, QTableWidgetItem(str(location_t.longitude)) )
                self.targetLocationEdit.setItem(rowPosition , 1, QTableWidgetItem(str(location_t.latitude)) ) 
         
          
            self.targetLocationEdit.resizeColumnsToContents()
            
            self.OnRefresh()
            
 
 