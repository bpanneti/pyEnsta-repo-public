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
from random import randint
import numpy as np   
from enum import Enum 
from scipy import interpolate
from collections import namedtuple
 
 
 

def interpolate_polyline(polyline, num_points):
    duplicates = []
    for i in range(1, len(polyline)):
        if np.allclose(polyline[i], polyline[i-1]):
            duplicates.append(i)
    if duplicates:
        polyline = np.delete(polyline, duplicates, axis=0)
    tck, u = interpolate.splprep(polyline.T, s=0,)
    u = np.linspace(0.0, 1.0, num_points)
    return np.column_stack(interpolate.splev(u, tck))

iconValide      =  "icones/valid.png"
iconNotValide   = "icones/notValid.png"
 
        
import myTimer as _timer

def compte():   
    global compteur
    compteur += 1
 
compteur = -1

TYPE  = namedtuple('TargetType', ['value', 'gabarit','icone','velocity','correspondance'])

class RECORDED_TYPE(Enum):
    NOT_DEFINED                             = 0
    BASE_ON_TIMETOWAYPOINTS                 = 1
    BASED_ON_VELOCITY                       = 2
    BASE_ON_WAYPOINTS                       = 3
    
class TARGET_TYPE(Enum):
 
    #TYPE , Gabarit in m (lxLxH), icon path, velocity min max in m/s
    UNKNOWN = TYPE(0,  [-1,-1,-1]    , 'icones/unknown.png',    [0,30],     'UNKNOWN')
    PAX     = TYPE(1,  [0.5,0.8,1.8] , 'icones/pax.png'    ,    [0,8 ],     'PAX')
    CAR     = TYPE(2,  [1.8,4.2,2.0] , 'icones/car.png'    ,    [0,30],     'VEHICLE_LIGHT')
    DRONE   = TYPE(3,  [0.3,0.3,0.2] , 'icones/drone.png'  ,    [0,17],     'SUAV')
    TANK    = TYPE(4,  [2.5,5.0,3.5] , 'icones/tank.png'   ,    [0,18],     'ARMORED_VEHICLE')
    TRUCK   = TYPE(5,  [2.3,12.0,3.5], 'icones/truck.png'  ,    [0,20],     'truck')
    BIRD    = TYPE(6,  [0.7,0.7,0.4] , 'icones/bird.png'   ,    [0,8 ],     'UNKNOWN')

 
        
class Target(QWidget):
 
        
    #Messagerie
            
    message = pyqtSignal('QString');
    
    def __init__(self):
        super(Target, self).__init__()  
 
        self.name               = 'UNKNOWN'
        compte()
        self.id                 = compteur
        
        self.type               = TARGET_TYPE.UNKNOWN
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
        
        # acces au gis s'il existe
        self.gis                = None
        #=====================
        # objets graphiques
        #=====================
        
        self.color                  = QColor('black') #target color
        self.trajectoryObj          = None#target trajecory graphic object
        self.textObj                = None#target text graphic object
        self.locationObj            = None#target location graphic object
        self.marker                 = ''#target marker graphic object
        self.width                  = 1 #target line width graphic object
        self.style                  ='-'#target line style graphic object

        
        self.locationIsVisible      = True #target visible on graphic 
    
        
        self.axes                   = None #axes object 
 

      
        
        
        #---> Accès au tree widget 

        self.treeWidgetItem         = None #item widget object 
        
        #booleen de sélection de la cible
        
        self.selectedTarget         = False #selection of the target
        
        #=============================
        # target trajectory
        #=============================
        
        self.recordedType           =       RECORDED_TYPE.BASED_ON_VELOCITY
        
    def duration(self):
        
        return self.timeToWayPoints[0].secsTo(self.timeToWayPoints[-1])
        
    def toJson(self,dateTime = QDateTime):
        
          flag, PositionAtTime,velocity = self.positionAtTime(dateTime)
          
          if flag == False:
              return ''
          #print('target time : '+str(dateTime.toString('hh:mm:ss.z')) +' position : {0}, {1}'.format(PositionAtTime.longitude,PositionAtTime.latitude) )
   
          json  = '{'+\
            '"code": 6,'+\
            '"message":"",'+\
	         '"id": "'+str(self.id)+'",'+\
            '"nom": "'+str(self.name)+'",'+\
            '"classType": "'+str(self.type.value.correspondance)+'",'+\
			'"date": "'+dateTime.toUTC().toString("yyyy-MM-dd HH:mm:ss.z") +'",'+\
            '"position":{'+\
            '"format":"WGS84",'+ \
            '"latitude":'+ str(PositionAtTime.latitude)+','+\
            '"longitude":'+ str(PositionAtTime.longitude)+','+\
            '"altitude":'+ str(PositionAtTime.altitude)+'}'+\
            '}'
          
          return json
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
        
    def clear(self, axes):
        if self.locationObj !=None:
            axes.lines.remove(self.locationObj)
            self.locationObj = None
        if self.textObj !=None:
            self.textObj.remove()
            self.textObj =None   
        if   self.trajectoryObj !=None:
            axes.lines.remove(self.trajectoryObj)
            self.trajectoryObj = None
            
    def displayCurrentTime(self,_currentTime, axes):
        
        if self.axes == None:
            self.axes = axes
            
 
        if self.locationObj !=None:
            self.axes.lines.remove(self.locationObj)
         
            self.locationObj = None
 
       
       
        if self.textObj !=None:
            self.textObj.remove()

            self.textObj =None 
 
  

        
        flag, PositionAtTime,VelocityTime = self.positionAtTime(_currentTime)

 
        if  flag == True: 
            latitude    = PositionAtTime.latitude
            longitude   = PositionAtTime.longitude 
 
            self.locationObj,   = self.axes.plot(longitude,latitude,color = self.color.name() , linewidth= 2,marker = 'o',markerfacecolor = 'blue',markersize = 4,visible = self.locationIsVisible )
            self.textObj        = self.axes.text(longitude,latitude, 'target : '+ str(self.id)+' / '+ str(self.name),   bbox={'facecolor':'red', 'alpha':0.5, 'pad':10} ,visible= self.locationIsVisible  )


#            self.axes.draw_artist(self.locationObj )
#            self.axes.draw_artist(self.textObj )  

   
    def smoothReealTrajectorty(self):
       return
        
       latitude    = []
       longitude   = []
       altitude    = []
       points      = None      
       for i in range(0,len(self.trajectory)):
          longitude = self.trajectory[i].longitude
          latitude = self.trajectory[i].latitude
          altitude.append(self.trajectory[i].altitude)
          if i == 0:
              points      = [latitude,longitude]  
          else:
             
              
              points      = np.vstack((points,[latitude,longitude]) )
       self.trajectory = []    
       #tck,u=interpolate.splprep(points.T,s=0.0)
      
       #B = np.column_stack(interpolate.splev(np.linspace(0,1,len(points)),tck))
       #B = interpolate_polyline( points ,len(points))
       tck,u=interpolate.splprep(points.T,k=3,s=0.0)
       x_i,y_i= interpolate.splev(np.linspace(0,1,5*len(points)),tck)
       B = np.column_stack((x_i,y_i))
       print(len(B))
       for u,i in zip(B,range(0,len(B))):
 
          point = Position(u[0],u[1], altitude[i])
          self.trajectory.append(point)
 
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
    def toDisplay(self, axes):
 
 
        if axes==None:
            return
        if self.trajectory==[]:
            return
        if self.axes == None or self.axes !=axes:
            self.axes = axes

 
 
        
        latitude  = []
        longitude = []
        altitude  = []
        
 

        for i in range(len(self.trajectory)):
             latitude.append(self.trajectory[i].latitude)
             longitude.append(self.trajectory[i].longitude)
             altitude.append(self.trajectory[i].altitude)
#        for i in range(len(self.trajectoryWayPoints)):
#            latitude.append(self.trajectoryWayPoints[i].latitude)
#            longitude.append(self.trajectoryWayPoints[i].longitude)
#            altitude.append(self.trajectoryWayPoints[i].altitude)
             #if i%10==0: 
              #axes.text(self.trajectory[i].longitude,self.trajectory[i].latitude , self.timeToWayPoints[i].toString('hh:mm:ss.z') )

  
        if self.locationObj !=None:
            axes.lines.remove(self.locationObj)
            self.locationObj = None
  
        self.locationObj, =  axes.plot(longitude[0],latitude[0],color = self.color.name(),marker = self.marker, linewidth= 2,visible =self.locationIsVisible) #
      
        if self.textObj !=None:
            self.textObj.remove()
            self.textObj =None 
       
       
        self.textObj = axes.text(longitude[0],latitude[0] , 'target : '+ str(self.id) +' / '+ str(self.name),   bbox={'facecolor':'white', 'alpha':0.5, 'pad':10},visible =self.locationIsVisible )
  
        if   self.trajectoryObj !=None:
            axes.lines.remove(self.trajectoryObj)
            self.trajectoryObj = None
    
        self.trajectoryObj, =  axes.plot(longitude,latitude,color = self.color.name(),marker = self.marker, linewidth= 2,visible =self.locationIsVisible) #
#        self.canvas.blit(axes.bbox)
#        self.canvas.update()
#        self.canvas.flush_events()
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
            self.treeWidgetItem.setText(2,self.type.name)
            self.treeWidgetItem.setForeground(0,QBrush(self.color))
            self.treeWidgetItem.setForeground(1,QBrush(self.color))
            self.treeWidgetItem.setForeground(2,QBrush(self.color))
      
            if self.isValid():
                self.treeWidgetItem.setIcon(0, QIcon(QPixmap(iconValide)))
            else:
                self.treeWidgetItem.setIcon(0,QIcon(QPixmap(iconNotValide)))  
                
    def editTarget(self):
 
        self.d = QDialog()
        
        layout              = QVBoxLayout()
        targetName          = QLabel('Target name')
        targetType          = QLabel('Target type')
        targetLocation      = QLabel('Target''s location')
        targetColor         = QLabel('Target color')
        targetStartTime     = QLabel('Target start date time ')
        targetStartVelocity = QLabel('Target start velocity (in m/s)')
        targetAltitude      = QLabel('Target start altitude (in m)')
        
        self.targetNameEdit      = QLineEdit()
     
        if self.name!='':
            self.targetNameEdit.setText(self.name)
            
        self.targetTypeEdit      = QComboBox() 
        for type_t in TARGET_TYPE:
            self.targetTypeEdit.addItem("%s"% type_t.name)
        
        if self.type:
            self.targetTypeEdit.setCurrentText("%s"% self.type.name)

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
        self.d.setWindowTitle("edit Target")
        self.d.setWindowIcon(QIcon('icones/newTarget.png'))
        self.d.setWindowModality(Qt.ApplicationModal)
        
        
        
        
        return self.d.exec_() 
    
    def buildTrajectory(self):
#        self.trajectory = self.trajectoryWayPoints
#        return True;
        print(f'target id {self.id} in {self.recordedType.name}')  
        
        if self.recordedType == RECORDED_TYPE.BASE_ON_WAYPOINTS:
            
            self.trajectory = self.trajectoryWayPoints
            self.smoothReealTrajectorty()
            return True
        
        if self.recordedType == RECORDED_TYPE.BASE_ON_TIMETOWAYPOINTS:
            #print(f'target id {self.id} in BASE_ON_TIMETOWAYPOINTS')
       
            if self.velocityToWayPoints!=[]   :
                self.timeToWayPoints = []
             
                if self.isSplinTrajectory == True   :
                    latitude    =[]
                    longitude   = []
          
                    for i in range(len(self.trajectoryWayPoints)):
                        longitude.append(self.trajectoryWayPoints[i].longitude)
                        latitude.append(self.trajectoryWayPoints[i].latitude)
      
                    if len(longitude)>self.degreeOfTheSpline: 
                  
                        tck,u=interpolate.splprep([longitude,latitude],k=self.degreeOfTheSpline,s=0.0)
                        x_i,y_i= interpolate.splev(np.linspace(0,1,5*len(self.trajectoryWayPoints)),tck)
                        latitude = y_i
                        longitude = x_i
                        self.trajectory =[]
                        for i in range(len( longitude)):
                            altitude = self.altitude
                            if self.gis:
                                altitude += self.gis.elevation(latitude[i],longitude[i]) 
                            point = Position(latitude[i],longitude[i], altitude)
                            self.trajectory.append(point)
          
                        self.timeToWayPoints.append(self.startTime)
                        for i in range(len(self.trajectory)-1):
                
                            pointA      = self.trajectory[i]
                            pointB      = self.trajectory[i+1]
                            distance    = pointA.distanceToPoint(pointB)
                   
                            velocity    = self.velocityToWayPoints[0] 
                            
                            
                            duree       = (distance /  velocity)*1000
             
                            _startDate  = self.timeToWayPoints[i]
                            
                            _arrivalDate = _startDate.addMSecs(duree)
             
                            self.timeToWayPoints.append(_arrivalDate)
                    else:
                        self.isSplinTrajectory = False
                else:        
                    self.trajectory = self.trajectoryWayPoints
       
                    self.timeToWayPoints.append(self.startTime)
                    for i in range(len(self.trajectory)-1):
        
                        pointA      = self.trajectory[i]
                        pointB      = self.trajectory[i+1]
                        distance    = pointA.distanceToPoint(pointB)
               
                        velocity    = self.velocityToWayPoints[i] 
             
                        if type(velocity)==np.ndarray:
                     
                            velocity= velocity[0]
                        duree       = (distance /  velocity)*1000
         
                        _startDate  = self.timeToWayPoints[i]
      
                        _arrivalDate = _startDate.addMSecs(duree)
         
                        self.timeToWayPoints.append(_arrivalDate)
                
                #print(len(self.velocityToWayPoints))
                #print(len(self.trajectory))
                #print(len(self.timeToWayPoints))
                return True
            
        
        if self.recordedType == RECORDED_TYPE.BASED_ON_VELOCITY:
       
    
            print(f'target id {self.id} in BASED_ON_VELOCITY')
            self.timeToWayPoints     = [] #Arrival Time to waypoints
            self.velocityToWayPoints = [] #Arrival velocity to waypoints    
                
            if len(self.trajectoryWayPoints )  <2 or self.startVelocity ==-1:   
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
                    x_i,y_i= interpolate.splev(np.linspace(0,1,5*len(self.trajectoryWayPoints)),tck)
                    latitude = y_i
                    longitude = x_i
                
                    for i in range(len( longitude)):
                        altitude = self.altitude
                        if self.gis:
                            altitude += self.gis.elevation(latitude[i],longitude[i]) 
                        point = Position(latitude[i],longitude[i], altitude)
                        self.trajectory.append(point)
                  
                else:
                    self.isSplinTrajectory = False
#                print('in isSplinTrajectory')
#                print(f'self.timeToWayPoints {len(self.timeToWayPoints)}')
#                print(f'self.velocityToWayPoints {len(self.velocityToWayPoints)}')
#                print(f'self.trajectory {len(self.trajectory)}')
#                print(f'self.trajectoryWayPoints {len(self.trajectoryWayPoints)}')
#                print('-------------------> fin') 
            else :
 
                self.trajectory = self.trajectoryWayPoints
                for i in range(len(self.trajectory)):
                    P = self.trajectory[i]
                    altitude = self.altitude
                    if self.gis:
                            altitude += self.gis.elevation(P.latitude,P.longitude) 
                    self.trajectory[i].altitude = altitude  
            
            self.timeToWayPoints.append(self.startTime) 
            self.velocityToWayPoints.append(self.startVelocity)
            for i in range(len(self.trajectory)-1):
    
                pointA      = self.trajectory[i]
                pointB      = self.trajectory[i+1]
                distance    = pointA.distanceToPoint(pointB)
                velocity    = self.startVelocity
     
                if self.isRandomVelocity:
           
                    velocity = max([self.startVelocity,np.random.random_sample(1)*self.type.value.velocity[1]])
                    if type(velocity)==np.ndarray:
                     
                            velocity= velocity[0]
                duree       = (distance /  velocity)*1000
     
                _startDate  = self.timeToWayPoints[i]
                _arrivalDate = _startDate.addMSecs(duree)
     
                self.timeToWayPoints.append(_arrivalDate)
     
                self.velocityToWayPoints.append(velocity)
            #devient une cible basée sur le timeOnWaypoints
            self.recordedType == RECORDED_TYPE.BASE_ON_TIMETOWAYPOINTS
#            print(f'self.timeToWayPoints {len(self.timeToWayPoints)}')
#            print(f'self.velocityToWayPoints {len(self.velocityToWayPoints)}')
#            print(f'self.trajectory {len(self.trajectory)}')
#            print(f'self.trajectoryWayPoints {len(self.trajectoryWayPoints)}')
#            print('-------------------> fin') 
            if len(self.trajectory)==len(self.timeToWayPoints) and len(self.trajectory)==len(self.velocityToWayPoints):
                return True
            return False
    def setStartTime(self,currentTime = QDateTime()):
        
        if self.synchronized == True:
            return
        self.startTime = currentTime;
 
        self.buildTrajectory()
        self.synchronized = True
        
    def positionAtTime(self,currentTime = QDateTime()):
  
        positionAtTime = Position()
        velocityAtTime = Velocity()
     
    
        if currentTime <self.startTime:
            return False,positionAtTime,velocityAtTime
        #sinon
       
        index =None    
       
     
         
        for t in range(0,len(self.timeToWayPoints)-1):
  
            if currentTime>=self.timeToWayPoints[t] and currentTime < self.timeToWayPoints[t+1] :
                index = t
                break
   
        if index!=None:
#            print('------------>')
#            print(f'target : {self.id}')
#            print(len(self.timeToWayPoints))
#            print(len(self.trajectory))
#            print(index)
#            
            A = np.array([self.trajectory[index].x_UTM,self.trajectory[index].y_UTM])
            diffTime =      self.timeToWayPoints[index].msecsTo(currentTime) /1000 
            B =  np.array([self.trajectory[index+1].x_UTM,self.trajectory[index+1].y_UTM])
            u = B-A
            durationBA = self.timeToWayPoints[index].msecsTo(self.timeToWayPoints[index+1]) /1000 
       
            velocity =  u/durationBA
            #vel = u/np.linalg.norm(u) *velocity
       
            
    
            
            Loc = A + diffTime* velocity  
     
            velocityAtTime.setXYZ(velocity[0],velocity[1],0.0,'UTM')
            positionAtTime.setXYZ(Loc[0],Loc[1],self.trajectory[index+1].altitude)
 
#            if self.gis != None:
 #               positionAtTime.altitude = self.Position[index+1].altitude + self.gis.altitude(positionAtT)
   
            return True,positionAtTime,velocityAtTime
        
        return False,positionAtTime,velocityAtTime
    
    
            
    def isValid(self):
        
        if self.buildTrajectory():
            if self.treeWidgetItem :
                self.treeWidgetItem.setIcon(0,QIcon(QPixmap(iconValide)))
            return True
        if self.treeWidgetItem:
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
            self.recordedType           =       RECORDED_TYPE.BASED_ON_VELOCITY
            
        else:    
            self.isRandomVelocity      =  False
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
            self.recordedType          =  RECORDED_TYPE.BASED_ON_VELOCITY
        else:    
            self.isRandomVelocity      =  False
 
        if self.isValid()==False:
            self.d.close()    
   
        self.color                  = self.targetColorEdit.palette().button().color()
        self.name                   = self.targetNameEdit.text()
        self.type                   = TARGET_TYPE[str(self.targetTypeEdit.currentText())] 
        self.startTime              =  self.targetStartTimeEdit.dateTime()
        self.startVelocity          = float(self.targetStartVelocityEdit.text())
        self.altitude               = float(self.targetAltitudeEdit.text()) 
        

        

        self.toDisplay(self.axes)
      
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

class RandomTargets(QWidget):
 
        
    #Messagerie
            
    message = pyqtSignal('QString');
    
    def __init__(self,GIS  ):
        super(RandomTargets, self).__init__() 
        self.GIS                = GIS
        self.targets            = []
    def activateRndType(self):
        if self.randomTypeBox.checkState()==Qt.Checked:
            self.targetTypeEdit.setDisabled(True) 
        else:
            self.targetTypeEdit.setDisabled(False) 
    def editRandomTarget(self):
        self.d = QDialog()
        
        layout              = QVBoxLayout()
        targetNumber        = QLabel('Number of target')
        targetType          = QLabel('Random class')
        targetLocation      = QLabel('Random trajectories')
        targetStartTime     = QLabel('Random start time ')
        PlageTime           = QLabel('Plage de temps (en s)')
        targetStartVelocity = QLabel('Random velocity (in m/s)')
        targetAltitude      = QLabel('Random start altitude (in m)')
        
        self.targetTypeEdit      = QComboBox() 
        for type_t in TARGET_TYPE:
            self.targetTypeEdit.addItem("%s"% type_t.name) 
        self.targetNumber                    = QLineEdit()        
        self.randomTypeBox                   = QCheckBox()
        self.randomTypeBox.stateChanged.connect(self.activateRndType)
        self.randomVelocityBox               = QCheckBox()
        self.randomLocationBox               = QCheckBox()
        self.randomStartTimeBox              = QCheckBox() 
        self.randomAltitude                  = QCheckBox()
        self.selectPlageTime                 = QLineEdit()  
        self.selectPlageTime.setEnabled(False)
        self.selectPlageTime.setText('0')
        self.randomStartTimeBox.toggled.connect(self.activeTime)
        grid = QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(targetNumber, 1, 0)
        grid.addWidget(self.targetNumber, 1, 1)
        grid.addWidget(targetType, 2, 0)
        grid.addWidget(self.randomTypeBox, 2, 1)  
        grid.addWidget(self.targetTypeEdit, 2, 2)
        grid.addWidget(targetLocation, 3, 0)
        grid.addWidget(self.randomLocationBox, 3, 1)
        grid.addWidget(targetStartTime, 4, 0)
        grid.addWidget(self.randomStartTimeBox, 4, 1) 
        grid.addWidget(PlageTime, 5, 0)
        grid.addWidget(self.selectPlageTime, 5, 1) 
        grid.addWidget(targetStartVelocity, 6, 0)
        grid.addWidget(self.randomVelocityBox, 6, 1)
        grid.addWidget(targetAltitude,7,0)
        grid.addWidget(self.randomAltitude,7,1)
   
        layout.addLayout(grid)
        
        
   
  
        
        
        buttonLayout = QHBoxLayout();
#        
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
        self.d.setWindowTitle("random Targets")
        self.d.setWindowIcon(QIcon('icones/randomTarget.png'))
        self.d.setWindowModality(Qt.ApplicationModal)

        return self.d.exec_()
    def activeTime(self):
        if self.randomStartTimeBox.isChecked() == True:
            self.selectPlageTime.setEnabled(True)
        else:
            self.selectPlageTime.setEnabled(False)
    def OnCancel(self)    :
        self.d.reject()
        
    def OnOk(self):

        N = int(self.targetNumber.text())
        M =  np.random.rand(N,2)
        widthArea  = np.abs(self.GIS.x1 - self.GIS.x0) ;
        heightArea = np.abs(self.GIS.y1 - self.GIS.y0) ;
  
        self.timeToWayPoints     = [] #Arrival Time to waypoints      
        self.velocityToWayPoints = [] #Arrival velocity to waypoints 
        
        for u in  range(0,N) :
            _target = Target()
            _target.gis = self.GIS
            
            self.targets.append(_target)
            
            targetType      = TARGET_TYPE.UNKNOWN
            if self.randomTypeBox.checkState()==Qt.Checked:
                rnd           = 1+np.random.randint(len(TARGET_TYPE)-1)
                
                for _type in TARGET_TYPE:
                    if _type.value.value==rnd:
                        targetType  = _type
            else :
            
                targetType = TARGET_TYPE[str(self.targetTypeEdit.currentText())]
                
            name            = str('random target')+str(u)
            color           = QColor()
            bb = "%06x" % np.random.randint(0, 0xFFFFFF)
            bb = ["#"+bb]
            color.setNamedColor(bb[0])
            
            _target.color = color
            _target.name  = name
            _target.type  = targetType                  
            velocity      = 10.0
            
        
            noRoad = False
            
            if self.randomLocationBox.checkState()==Qt.Checked  and \
             (_target.type == TARGET_TYPE.CAR or _target.type == TARGET_TYPE.TRUCK ) :
                 
                _target.recordedType  = RECORDED_TYPE.BASE_ON_TIMETOWAYPOINTS
                _target.startVelocity = _target.type.value.velocity[1]/2 + np.random.randint(_target.type.value.velocity[1]/2)
                
                flagStop  = False
                direction = True
                longueur  = 0
                
                conts = []
           
                
#                longitude       = self.GIS.x0 ;+ widthArea  * x    
#                latitude        = self.GIS.y0 ;- heightArea * y  
           #     print([self.GIS.x0 , ' ',self.GIS.y0,' ',self.GIS.x1 , ' ',self.GIS.y1])
                if self.GIS.road:
                    for r in self.GIS.road.containers : 
                        x = r.shape[0,0]
                        y = r.shape[0,1]
                        if self.GIS.x0<= x and self.GIS.y0>= y and x <= self.GIS.x1  and self.GIS.y1 <= y \
                            and r.traficability>=2 :
                            conts.append(r)
                 
           
#                    elif self.GIS.x0<= r.sxmax and self.GIS.y0>= r.symax and r.sxmax <= self.GIS.x1  and self.GIS.y1 <= r.symax:
#                        conts.append(r)  
#                        print([r.sxmin  , ' ',r.symin,' ',r.sxmax , ' ',r.symax])
                        
                if len(conts)==0:                    
                    noRoad = True
                else : 
                        
                       
                    indexRoad = np.random.randint(len(conts))
                    road      = conts[indexRoad]
                    indexRoads = []
                    while road !=None and flagStop == False:
                        
                        shape = road.shape

                        x = shape[:,0]
                        y = shape[:,1]
                        _traj= []
                        _vel = []
          
                        if direction==True : 
                            for u in range(0,len(x)):
                                
                                P_p = Position(y[u],x[u],0.0)
                                velo = velocity
                        
                                
                                if len(_traj) >=2:
                                   longueur+= P_p.distanceToPoint(_traj[-1])
                                _traj.append(P_p)
                                _vel.append(velo)
                        if direction==False :
                            
                            for u in range(len(x),0,-1):
        
                                P_p = Position(y[u-1],x[u-1],0.0)
                                velo = velocity
                          
                                    
                                if len(_traj) >=2:
                                   longueur+= P_p.distanceToPoint(_traj[-1])
                                _traj.append(P_p)
                                _vel.append(velo)
            
                        if longueur > 3000:
                            flagStop = True
                        indexRoads.append(indexRoad)
     
                        
                        road,indexRoad,direction,velocity = self.GIS.getOneRoad(_traj[-1],indexRoads)
                        
                        
                            
                        if self.randomVelocityBox.checkState()==Qt.Checked :
                          
                            _randvel = ( velocity-5 + 10*np.random.randn(1)) /3.6
                          
                            velocity  = min([abs(_randvel),_target.type.value.velocity[1]] )   
                    
                       
                        _target.trajectoryWayPoints +=_traj
                        _target.velocityToWayPoints +=_vel
 
                    _target.isSplinTrajectory   = False
                
                
            if self.randomLocationBox.checkState()==Qt.Checked and \
             (_target.type == TARGET_TYPE.TANK \
              or _target.type == TARGET_TYPE.DRONE \
              or _target.type == TARGET_TYPE.PAX
              or noRoad) :
                x = M[u,0]
                y = M[u,1]
                longitude       = self.GIS.x0 + widthArea  * x    
                latitude        = self.GIS.y0 - heightArea * y   
                
                P = Position(latitude,longitude,0.0)        
                
                if self.randomLocationBox.checkState()==Qt.Checked:
                    v = _target.type.value.velocity[1]/2
                    direction = 2*np.pi*np.random.rand() 
                    
                    _traj = [P]
      
                    for m in range(0,20):
                    
                        lasP        = _traj[-1]
                        vel         = 5 *(v + np.random.randn())
                        direction   = direction + 0.1*np.random.randn()
           
                        pos         = np.array([lasP.x_UTM,lasP.y_UTM]) + np.array([vel*np.cos(direction),vel*np.sin(direction)])
              
                        P_p = Position()
              
                        P_p.setXYZ(pos[0],pos[1],0.0,'UTM')
              
                        _traj.append(P_p)
                    
                    
                
                    _target.trajectoryWayPoints =_traj
                    _target.isSplinTrajectory   = True
                
            
            if self.randomStartTimeBox.checkState()==Qt.Checked:
                 #entre 0 et 1 minutes
                  
                
                 _target.startTime = _target.startTime.addSecs(np.random.randint(int( self.selectPlageTime.text())))
              
            if self.randomAltitude.checkState()==Qt.Checked and _target.type == TARGET_TYPE.DRONE: 
                 _target.altitude   = np.random.randint(20, 70)
            
            
            
  
            
            _target.update()
            
        self.d.accept()
def addTarget():
    
    target = Target()
    
    target.editTarget()
    
def main():
  
    app = QApplication(sys.argv)
    main = QWidget()
    layout = QVBoxLayout()
    button = QPushButton('add target')
    button.clicked.connect( addTarget()) 
    layout.addWidget(button)
    main.setLayout(layout)
    main.show()
    return sys.exit(app.exec_())
      
 
if __name__ == "__main__":
    main()
