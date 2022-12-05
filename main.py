# -*- coding: utf-8 -*-
"""
Created on Wed May 22 13:43:07 2019

@author: bpanneti
"""

import sys
import os

#os.environ['QT_API']='pyqt5'
#print(os.environ)

import numpy as np

from PyQt5.QtCore    import *
from PyQt5.QtCore    import QThread
from PyQt5.QtGui     import *
#from PyQt5.QtOpenGL  import *
from PyQt5.QtWidgets import *

from GIS import GIS as gis
import matplotlib
matplotlib.use('Qt5Agg')


from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.backend_bases import key_press_handler
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)
from matplotlib.patches import Rectangle
from matplotlib.collections import PatchCollection

from matplotlib.patches import Circle, Wedge, Polygon
from myTimer import Sequenceur  as Sqc, getReferenceTime 
import timer as _timer 
import time

from Managers.dataManager import DataManager
from console import Console
from loader  import data

#from tablePlots import tablePlots
from metrics.tableMetrics import metricsWidget
from metrics.MOP import MOP 
from metrics.MOP import MOPComparison 

from point import Position,utm_getZone,utm_isNorthern,utm_isDefined,REFERENCE_POINT ,RefPosition

from enum import Enum, unique

from target  import Target, RandomTargets
from sensor   import Node, Sensor
from mobileNode import MobileNode
from toolTracking.tracker import Tracker
 
from saver   import saveData
from metrics.gospa_ospa import Metrics

#if os.name != "posix":
#    from shield import  ADRESS_IP,  TCP_PORT, ClientShield, Client
#    from shieldViewer import Ui_Dialog as Ui_Shield


from toolTracking.utils import trackerType 



from artlib.toolConvertDataBase import convertART

TCP_PORT = 8080
ADRESS_IP = '192.168.1.11'
from sextantlib.sextant import Ui_Dialog as UI_Sextant
from sextantlib.SAFIRSettings_ui import server as sextantServer
from sextantlib.SAFIRSettings_ui import ADRESS_IP 

sys.setrecursionlimit(10**6) 

class ACTION(Enum):
        NOACTION             = 0
        SELECTION            = 1
        TRAJECTROY_SELECT    = 2
        TARGET_TRAJECTORY    = 3
        PLATFORM_TRAJECTORY  = 4
        AREAOfINTEREST       = 5
        NODE_LOCATION        = 6
    
 

class mainwindow(QMainWindow):
    variableGlobale = 0
    def __init__(self):
        super(QMainWindow, self).__init__()
        #QMainWindow.__init__(self)
        self.initUI()
        #self.ui_SafirControls = UI_Window()
        self.show()
        self.u = 10 #qynchro toute les 10 secondes
 
        mainwindow.variableGlobale =  0
        
    def initUI(self):
        
        mainWidget               =   QWidget()
        self.tabs	             =   QTabWidget() 
        self.tabs.tabBar().setContextMenuPolicy(Qt.ActionsContextMenu)

        self.action = ACTION.NOACTION 
        self.GIS = gis()
        self.graphicalArea() 
        self.GIS.fig        = self.fig
        self.GIS.axes       = self.axes
        self.GIS.canvas     = self.canvas
        self.axes.grid(True)
        self.axes.axis('equal')
        self.GIS.init()
        self.GIS.setParameters(self.axes,self.canvas)
        self.GIS.emitRemoveTarget.connect(self.deleteTarget)
        self.GIS.emitTrajectory.connect(self.trajectoryTarget)
        self.GIS.emitEditTarget.connect(self.editTarget)
        self.GIS.emitEditNode.connect(self.editNode)
        self.GIS.emitRemoveNode.connect(self.deleteNode)
        self.GIS.emitNodeLocation.connect(self.locationNode)
        self.GIS.message.connect(self.receiveMessage)
        self.GIS.emitAddSensor.connect(self.newSensor)
        self.GIS.emitEditSensor.connect(self.editSensor)
        self.GIS.emitRemoveSensor.connect(self.deleteSensor)
        self.GIS.emitAddTracker.connect(self.newTracker)
        self.GIS.emitEditTracker.connect(self.editTracker)
        

#        self.threadGIS = QThread()
#        
#        self.GIS.moveToThread(self.threadGIS)
#        self.threadGIS.start() 
        
        self.setWindowTitle("Benjamin GIS")
 
        self.mpl_toolbar = NavigationToolbar(self.canvas, mainWidget)
        pixmap = QPixmap("icones/refresh.png")
        self.push_buttonRefreshBBOX = QPushButton()   
        self.push_buttonRefreshBBOX.setToolTip("refresh the bbox to reduce data")
        self.push_buttonRefreshBBOX.setIcon(QIcon(pixmap))
        self.mpl_toolbar.addWidget(self.push_buttonRefreshBBOX)
        self.push_buttonRefreshBBOX.clicked.connect(  self.GIS.refreshbbox)
        
        self.canvas.mpl_connect('scroll_event', self.onscroll)
        self.canvas.mpl_connect('button_press_event', self.pressEvent)
        #self.canvas.mpl_connect('key_press_event', self.keyPressEvent)
        self.canvas.mpl_connect('motion_notify_event', self.moveEvent)
        self.canvas.mpl_connect('button_release_event', self.releaseMouseEvent)
        
        self.tabs.setTabsClosable(True)

        Vlayout = QVBoxLayout()
        Vlayout.addWidget(self.mpl_toolbar)     
        Vlayout.addWidget(self.canvas ) 
        tab1 = QWidget()
        tab1.setLayout(Vlayout)
        self.tabs.addTab(tab1,"GIS")
        self.tabs.tabBar().tabButton(0,QTabBar.RightSide).hide()
        
        # objet graphique du polygon de selection    
        self.selection = None
        # variables
        self.currentSelectoption = []
        #----------- Table des détections
        '''
        self.tablePlots = tablePlots()
        Vlayout4 = QVBoxLayout()
        Vlayout4.addWidget(self.tablePlots)    
        tab3 = QWidget()
        tab3.setLayout(Vlayout4)
        self.tabs.addTab(tab3,"Table des plots")
        self.tabs.tabBar().tabButton(1,QTabBar.RightSide).hide()
        '''
        #----------- Console
        
        self.console        = Console()
        
        Vlayout3 = QVBoxLayout()
        Vlayout3.addWidget(self.console)    
        tab2 = QWidget()
        tab2.setLayout(Vlayout3)
        self.tabs.addTab(tab2,"Console")
        
        self.tabs.tabBar().tabButton(1,QTabBar.RightSide).hide()
        
        Vlayout2 = QVBoxLayout()
        Vlayout2.addWidget(self.tabs ) 
        mainWidget.setLayout(Vlayout2)
        
        self.tabs.tabCloseRequested.connect(self.closeTab)
        
        self.setCentralWidget(mainWidget)
       
        #---------Dock Widgets ----------------------------    
        
        self.DockWidget()

        #----------- Timer
        
        self.timer =  Sqc()
        self.timer.receiveTime.connect(self.receiveTime)
        self.timer.stopTime.connect(self.stopTime)
        self.timer.startTime.connect(self.startTime)
        self.timer.pauseTime.connect(self.pauseTime)
        self.timer.runMonteCarlo.connect(self.runMonteCarlo)
        self.isStarted = False
        Vlayout2.addWidget(self.timer)
        
        #----------- Menu Bar
        
        self.Menu()

        #----------- Saver
        self.threadSaver    = QThread()
        self.threadSaver.start()
        self.saver          = saveData()
        self.saver.moveToThread(self.threadSaver)
        self.saver.message.connect(self.receiveMessage)
  
        #DataManager
        
        self.manager = DataManager.instance()
                
        #------------ Loader
        
        self.loader = data()
        
        self.threadLoader = QThread()
        self.loader.moveToThread(self.threadLoader)
        self.threadLoader.start()
    
        self.loader.message.connect(self.receiveMessage)
        self.loader.referencePoint.connect(self.receiveReferencePoint)
        self.loader.referenceTime.connect(self.receiveReferenceTime)
        self.loader.endTime.connect(self.receiveEndTime)
        self.loader.emitNodes.connect(self.receiveNode)
 
        self.loader.emitSensors.connect(self.receiveSensors)
        self.loader.emitParameters.connect(self.receiveParameters)
        self.loader.emitDetections.connect(self.receiveDetections)
        self.loader.emitTargets.connect(self.receiveTargets)
        self.loader.emitTrackers.connect(self.receiveTrackers)
        #self.loader.emitSelectedDetections.connect(self.receiveSelectedDetections)
        #self.loader.emitStates.connect(self.receiveStates)
 
        #----------- MOP
        
        self.MOP = MOP()
        self.MOPCompare = MOPComparison()
        #----------- Client SHIELD
        # if os.name != "posix":
        #   self.clientUI = Ui_Shield() 
        self.clientShield   = None
        
        #----------- client SEXTANT
        self.ui_SafirControls       = UI_Sextant()
        self.sextantServer          = sextantServer() 
        self.sextantServer.message.connect(self.receiveMessage)
        self.sextantServer.chatMessage.connect(self.receiveChatMessage)
        self.workerThread           = QThread()
        self.sextantServer.moveToThread(self.workerThread)
        self.workerThread.started.connect(self.sextantServer.run)
        #-------------- CSV File
        
        self.csv_radar = None
        #===========
        # Variables
        #===========
  
        
        self.currentSelection = []
        
        #===============
        #  saveDatabase
        #===============
        fileName = './data/base/tmp.db' 
        self.saver.saveData(fileName)
        
        self.ART = convertART()
        self.ART.message.connect(self.receiveMessage)
        self.ART.referencePoint.connect(self.receiveReferencePoint)
        self.ART.referenceTime.connect(self.receiveReferenceTime)
            
        
    def closeTab(self,index):
        self.tabs.removeTab(index)

    def runCycle(self,value):
        self.console.write("run cycle %s"%(value))
        self.loader.start()
 
        timeref = getReferenceTime()
  
        self.sextantServer.newRun(value)
        self.sextantServer.synchronize(timeref.addSecs(-15))
        print('------------- sleep 10 seconds ------------')     
        time.sleep(1)
    #    self.timer.lcd.setDateTime(time)
        print('------------- restart ------------')  
        for _node in self.manager.nodes():
            for _sensor in _node.sensors:
#<<<<<<< HEAD:main.py
                _sensor.start()
        secs = self.timer.duration()  
      
        #self.timer.startThread()
        
        for t in range(0,1000*secs,100):
            
            # 1000 Msecs = 1 secs  
            
            time_c = timeref.addMSecs(t)
            self.timer.lcd.setDateTime(time_c)   
            if t == 0 : 
                self.sextantServer.tic(time_c)
                
            self.timer.progressBar.setValue(value*secs + 0.001*t +1)
            if t%1000 ==0:
                self.sextantServer.tic(time_c)
                for _target in self.manager.targets():
                     json = _target.toJson(time_c)
                     if json!='':
                       self.sextantServer.sendJsonMessage(json)
#      
            #chargement des données
            self.timer.receiveTime.emit(time_c)
            
#=======
#                _sensor.start(time)
#        secs = self.timer.duration()       
#        for t in range(0,secs ):
#            
#            print(['temps : t=',t,' secs=',secs])
#            time_c = time.addSecs(t)
# 
#            #chargement des données
#            self.timer.progressBar.setValue(value*secs + t +1)
#            self.timer.lcd.setDateTime(time_c)
#>>>>>>> 860fcd2d4cb0fa5d08cb3519c8192a80110f0b8a:setup.py
      
            self.timer.progressBar.update()
            QApplication.processEvents()
            '''
            for _node in self.manager.nodes():
                for _sensor in _node.sensors:
                    #print('----> detections')
                    _sensor.detection(time_c) 
            '''
#                    if _sensor.scan != None:
#       
#                        json = _sensor.scan.toJson()
#                        self.sextantServer.sendJsonMessage(json)
        
            time.sleep(0.05)
        #=====> fin du cycle
        print('fin du cycles --> 1')    
        for _node in self.manager.nodes():
            if _node.tracker!=None:
                _node.tracker.stop()
            for _sensor in _node.sensors:
                if _sensor.scan != None:
                    del _sensor.scan
                    _sensor.scan=None
                
        self.threadLoader.terminate()
        while  self.threadLoader.isFinished()==False : 
            {
                    }
        self.loader.stop()
        print('fin du cycles --> 2') 
    def runMonteCarlo(self,value):
        #print(value)
        value = int(value)
        #◙filename, _  = QFileDialog.getSaveFileName(self, 'Save Monte Carlo runs : 1 file per run', '.','*.db')
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to save Monte Carlo runs : 1 file per run", '.')
        if not folder :
             folder =  folder  + "/"
        if (not folder) or (len(self.manager.nodes())==0):
            self.timer.reEnable()
            return
        self.console.write("Creating a directory for Monte Carlo runs...")
      
        if not os.path.exists(folder):
            os.mkdir(folder)
#            self.console.write("Can't create an existing directory.")
#            self.timer.reEnable()
            return
        self.console.write("Directory %s created"%folder)

        self.console.write("Run %s cycles"%value)

        time = getReferenceTime()

 
        if self.question("Do you want compute MOP based on saved data base?","MonteCarlo run") == QMessageBox.Yes:
     
           self.timer.progressBar.setMinimum(1)
           self.timer.progressBar.setMaximum(self.timer.duration() *value)
         
           for nb in range(0,value):
               self.saver.saveData((folder+"/run_%s.db")%(nb))
               self.saver.saveReferencePoint()
               self.saver.saveNodes(time)
               self.saver.saveClass() 
               self.saver.saveTargets()
               self.runCycle(nb)
    
           self.timer.reEnable()
        else:
            
            ground_truth = np.zeros((len(self.manager.targets()),3,3600,len(self.manager.nodes()))) # 3 because 2 dimensions plus 1 mask
    
          
    
            for k in range(value):
    
                self.loader.start()
                self.timer.progressBar.setMinimum(0)
                self.timer.progressBar.setMaximum(360000)
    
                for _node in self.manager.nodes():
                    for _sensor in _node.sensors:
                        _sensor.start()
    
                for t in range(0,360000,value ):
                    time_c = time.addMSecs(t)
                    #chargement des données
                    self.loader.receiveTime(time_c)
    
                    self.timer.setRunTime(time_c)
    
                    for _node in self.manager.nodes():
                        for _sensor in _node.sensors:
                            _sensor.detection(time_c,self.manager.targets())
   

        self.timer.reEnable()


    def synchronization(self,_sTime = QDateTime()):
            for _target in self.manager.targets():
                _target.setStartTime(_sTime)
                
  
    
    def startTime(self,_sTime = QDateTime()):
        self.isStarted = True
        self.console.write("start timer")
 
        self.saver.cleanTableReferencePoint()
        self.saver.cleanTableNodes()
        self.saver.cleanTableSensors()
        self.saver.cleanTableParameters()
        self.saver.cleanTableClasses()
        self.saver.cleanTableTrackers()     
        self.saver.cleanTableTargets()    
        
        
        self.loader.start()
        self.saver.saveReferencePoint()
        self.saver.saveNodes(_sTime)
        self.saver.saveClass() 
        self.saver.saveTargets()
        for _target in self.manager.targets():
             _target.synchronized = False
        
        for _node in self.manager.nodes() :
            for _sensor in _node.sensors:
                _sensor.start()
            if _node.tracker !=None:
                _node.tracker.start()
 

        self.timer.startThread()
    def receiveGauss(self):
         for node in self.manager.nodes() :
    
            if node.tracker and  node.tracker.filter == trackerType.GMPHD:
             
                self.GIS.receiveGauss(node.tracker)
    def receiveTracks(self,tracks = []):
#        if self.clientShield!=None:
#            self.clientShield.sendTracks(tracks)
        if tracks == []:
            return
        for node in self.manager.nodes() :
    
            if node.tracker and node.id!=tracks[0].id_node :
                node.tracker.receiveTracks(tracks[0].id_node,tracks) 
          

    def receiveTrackers(self,trackers):
        self.GIS.receiveTrackers(trackers)
 
        for node in self.manager.nodes() :
            for _tracker in trackers:
                if _tracker.id_node == node.id:
                    
                   _tracker.node    = node
                   node.tracker     = _tracker
                   for _node in self.manager.nodes():
                       for _sensor in _node.sensors:
                           _sensor.newScan.connect(_tracker.receiveScan)
                           _sensor.newScan.connect(self.receiveScan)
                           
               
                   _tracker.tracks_display.connect(self.saver.saveTracks)
                   _tracker.tracks_display.connect(self.GIS.receiveTracks)
                   _tracker.emitTracks.connect(self.receiveTracks)
                   _tracker.gauss_display.connect(self.receiveGauss)
                   _tracker.toDisplay(self.axes,self.canvas)
     
    def receiveScan(self, scan = None):
            #scan.sensor.clear()
            #obligé car sextant server tourne sur un autre thread, les connect sont supprimés
            self.sextantServer.receiveScan(scan)
            self.saver.receiveScan(scan)
            if self.clientShield!=None:
                self.clientShield.receiveScans([scan])
  
    def receiveParameters(self,parameters):
        for _node in self.manager.nodes() :
            for _sensor in _node.sensors:
                for coverage in parameters:
                    if _sensor.id == coverage.id_Sensor:
                        if _sensor.sensorCoverage == None:
                            _sensor.sensorCoverage = []
                        _sensor.sensorCoverage.append(coverage)
                        
                        self.GIS.receiveSensors()
                        self.saver.saveParameters(parameters)
    def receiveSensors(self,sensors):

        for node in self.manager.nodes() :
            if node.tracker:
                node.tracker.receiveSensors(sensors)
            for _sensor in sensors:
 
                if _sensor.id_node == node.id:


                   #_sensor.newScan.connect(self.receiveScan)
                   _sensor.newScan.connect(self.GIS.receiveScan)
                   _sensor.newScan.connect(self.receiveScan)
                   
                   if node.tracker:
                       _sensor.newScan.connect(node.tracker.receiveScan)
                   #print('sensor recorded')
                   self.manager.addSensor(_sensor)
                   self.timer.receiveTime.connect(_sensor.receiveTime)
                                      
                   if node.containsSensor(_sensor.id) ==False:         
                       node.sensors.append(_sensor)
                   _sensor.node    = node 
                   _sensor.update()
                   _sensor.GIS     = self.GIS
                   if utm_isDefined() == False:
                      self.showWarningDialog('area of interest is not defined')
                   _sensor.toDisplay(self.axes,self.canvas) 
                   
            self.saver.saveSensors(sensors)
                   
        self.GIS.receiveSensors()
        self.sextantServer.receiveSensors()
    '''
    def receiveSelectedDetections(self,_detections):
        #print('receive selected dets in setup')
        self.tablePlots.receiveDetections(_detections)
    '''
    '''
    def receiveStates(self,_states):
        if _states!=[]:
 
           self.GIS.receiveStates(_states)
           self.sextantServer.receiveStates(_states)
    '''
    def receiveDetections(self,_detections):
        if _detections != []:
            self.GIS.receiveDetections(_detections)
            
    
        
    def receiveNode(self):
        
        self.console.write(" nodes received ")
        self.GIS.receiveNodes()
        self.sextantServer.receiveNodes()
        
        self.saver.saveNodes()
        
    def receiveTargets(self):
        self.console.write(" targets received ")
        for _target in self.manager.targets():
            self.GIS.receiveTarget(_target)
            _target.update()
       
    def receiveCommand(self,cmd):
        strlist = cmd.split(" ") 
  
 
        if strlist[0] == 'sensor':
            idSensor = strlist[1]
            mySensor = None
            for _node in self.manager.nodes() :
                for _sensor in _node.sensors:
    
                    if str(_sensor.id) == str(idSensor):
                            mySensor = _sensor
                            break
 
            if strlist[2] == '-commandStatus' and mySensor :
 
                if self.clientShield!=None and strlist[3]=='2':
                        self.clientShield.sendStatus(mySensor)
                
            if strlist[2] == '-commandOrientation' and mySensor:
      
                for _cover in mySensor.sensorCoverage:
                    _cover.fov = float(strlist[4])
                
                signe = 1.0
                if float(strlist[3]) < 0:
                    signe = -1.0
                borne =  abs(float(strlist[3])) #- mySensor.node.Orientation.yaw)
                angle = 0.0
                flag = True

                deb = mySensor.node.Orientation.yaw
         
                
                while angle < borne:
                    
                    print(['directon imposesd : ',mySensor.node.Orientation.yaw])
                    #mySensor.node.update()
 
                
                    
                    angle = angle + 5.0
                    print(angle)
                    if   angle>borne:
                          angle = borne
                    mySensor.node.Orientation.yaw =  deb + signe*angle      
                    mySensor.node.toDisplay(self.axes,self.canvas)
                    self.canvas.draw() 
  
                    if self.clientShield!=None:
                       self.clientShield.sendFOV(mySensor,deb)
                    time.sleep(1) 
                return    
       
    def receiveReferencePoint(self, pt   ) :
        
            strlist = pt.split(" ") 
         
            REFERENCE_POINT.setWGS84(float(strlist[0]),float(strlist[1]),float(strlist[2]))

            utm_getZone(float(strlist[0]))
            utm_isNorthern(float(strlist[1]))
            self.receiveMessage(("new referencePoint %f %f %f")%(REFERENCE_POINT.longitude, REFERENCE_POINT.latitude, REFERENCE_POINT.altitude))
            
            #Mise à jour des composants
            for _node in self.manager.nodes():
                if type(_node)==Node:
                    _node.Position.WGS842UTM()                    
                    _node.Position.WGS842ENU()
                elif type(_node)==MobileNode:
                    for u in _node.trajectoryWayPoints:
                        u.WGS842UTM()                    
                        u.Position.WGS842ENU()
            #Mise à jour des cibles
            for _target in self.manager.targets():
                for _point in _target.trajectory:
                    _point.WGS842UTM()
                    
                    _point.WGS842ENU()
    def receiveEndTime (self, date = QDateTime()):
            self.timer.newEndTime(date)     
            self.receiveMessage(("new endTime %s")%(date.toString("dd-MM-yyyy HH:mm:ss.z")))
    def receiveReferenceTime(self, date = QDateTime()):
            self.timer.newReferenceTime(date)
            self.receiveMessage(("new referenceTime %s")%(date.toString("dd-MM-yyyy HH:mm:ss.z")))
            #nouveau composent dans la base
            self.loader.newComponents(date)
            

            
    def Menu(self):
        
        #===========================
        # Files
        #===========================
        
        menuFichier = self.menuBar().addMenu("&File"); 
        imageLoadDb = QPixmap("icones/database.png")
        actionLoadDb= QAction(QIcon(imageLoadDb), 'load database', self)
        actionLoadDb.setToolTip('click to load dataBase!')
        actionLoadDb.setShortcut('Ctrl+O')
        icon  = QIcon(imageLoadDb)
        actionLoadDb.setIcon(icon)
        actionLoadDb.triggered.connect(self.loadDataBase);
        #actionQuitter.setIconSize(QSize(10, 10))
        menuFichier.addAction(actionLoadDb)
        
        imageSaveXml = QPixmap("icones/save.png")
        actionSave = QAction(QIcon(imageSaveXml), 'save data', self)
        actionSave.setToolTip('click to save data!')
        actionSave.setShortcut('Ctrl+s')
        icon  = QIcon(imageSaveXml)
        actionSave.setIcon(icon)
        actionSave.triggered.connect(self.saveData);
        menuFichier.addAction(actionSave)
        
        
        imageClose = QPixmap("icones/exit.png")
        actionQuit = QAction(QIcon(imageClose), 'exit', self)
        actionQuit.setToolTip('click to quit!')
        actionQuit.setShortcut('Ctrl+q')
        icon  = QIcon(imageClose)
        actionQuit.setIcon(icon)
        actionQuit.triggered.connect(self.close);
        #actionQuitter.setIconSize(QSize(10, 10))
        
        menuFichier.addAction(actionQuit)
       
        #===========================
        # Actions
        #===========================
        menuAction = self.menuBar().addMenu("&Actions"); 
        imageSelection = QPixmap("icones/selection.png")
        actionSelection= QAction(QIcon(imageSelection), 'select reports', self)
        actionSelection.setToolTip('click to select reports!')
        actionSelection.setShortcut('Ctrl+G')
        icon  = QIcon(imageSelection)
        actionSelection.setIcon(icon)
        actionSelection.triggered.connect(self.selectData);
        menuAction.addAction(actionSelection)
        
        imageSelection = QPixmap("icones/elevation.png")
        actionAreaSelection= QAction(QIcon(imageSelection), 'define area of interest', self)
        actionAreaSelection.setToolTip('click to define area of interest!')
        actionAreaSelection.setShortcut('Ctrl+I')
        icon  = QIcon(imageSelection)
        actionAreaSelection.setIcon(icon)
        actionAreaSelection.triggered.connect(self.newAreaOfInterest);
        
        #actionQuitter.setIconSize(QSize(10, 10))
        menuAction.addAction(actionAreaSelection)
        
        
        imageAddTarget= QPixmap("icones/newTarget.png")
        actionAddTarget = QAction(QIcon(imageAddTarget), 'add Target', self)
        actionAddTarget.setToolTip('click to add target!')
        actionAddTarget.setShortcut('Ctrl+A')
        icon  = QIcon(imageAddTarget)
        actionAddTarget.setIcon(icon)
        actionAddTarget.triggered.connect(self.addTarget);
        #actionQuitter.setIconSize(QSize(10, 10))
        menuAction.addAction(actionAddTarget)
        
        imageAddNode= QPixmap("icones/node.png")
        actionAddNode = QAction(QIcon(imageAddNode), 'add Node', self)
        actionAddNode.setToolTip('click to add Node!')
        actionAddNode.setShortcut('Ctrl+N')
        icon  = QIcon(imageAddNode)
        actionAddNode.setIcon(icon)
        actionAddNode.triggered.connect(self.addNode)
        #actionQuitter.setIconSize(QSize(10, 10))
        menuAction.addAction(actionAddNode)
    
        imageAddNode= QPixmap("icones/mobileNode.png")
        actionAddMNode = QAction(QIcon(imageAddNode), 'add mobile Node', self)
        actionAddMNode.setToolTip('click to add mobile Node!')
        actionAddMNode.setShortcut('Ctrl+M')
        icon  = QIcon(imageAddNode)
        actionAddMNode.setIcon(icon)
        actionAddMNode.triggered.connect(self.addMobileNode)
        #actionQuitter.setIconSize(QSize(10, 10))
        menuAction.addAction(actionAddMNode)
        
        
        imageAddRandTarget= QPixmap("icones/randomTarget.png")
        actionAddRandTarget = QAction(QIcon(imageAddRandTarget), 'random targets', self)
        actionAddRandTarget.setToolTip('click to add several targets!')
        actionAddRandTarget.setShortcut('Ctrl+A')
        icon  = QIcon(imageAddRandTarget)
        actionAddRandTarget.setIcon(icon)
        actionAddRandTarget.triggered.connect(self.addRandTarget);
        #actionQuitter.setIconSize(QSize(10, 10))
        menuAction.addAction(actionAddRandTarget)
        
        #===========================
        # Connections
        #===========================
        
        menuConnection = self.menuBar().addMenu("&Connection/output"); 
        imageConnect = QPixmap("icones/connection.png")
        actionConnect= QAction(QIcon(imageConnect), 'connect SHIELD server', self)
        actionConnect.setToolTip('click to connect on SHIELD server!')
        icon  = QIcon(imageConnect)
        actionConnect.setIcon(icon)
        actionConnect.triggered.connect(self.connection);
        menuConnection.addAction(actionConnect)
        
        actionConnectSextant= QAction(QIcon(imageConnect), 'connect LEXLUTOR server', self)
        actionConnectSextant.setToolTip('click to connect on LEXLUTOR server!')
        icon  = QIcon(imageConnect)
        actionConnectSextant.setIcon(icon)
        actionConnectSextant.triggered.connect(self.connectionSEXTANT);
        menuConnection.addAction(actionConnectSextant)

        imageCSV = QPixmap("icones/csv.png")
        actionCSV= QAction(QIcon(imageConnect), 'csv output', self)
        actionCSV.setToolTip('click to specify csv output!')
        icon  = QIcon(imageCSV)
        actionCSV.setIcon(icon)
        actionCSV.triggered.connect(self.csvOutput);
        menuConnection.addAction(actionCSV)
        
        #===========================
        # Metrics
        #===========================
        
        menuMetrics = self.menuBar().addMenu("&Metrics");
        imageMetrics = QPixmap("icones/diagram.png")
        actionComputeMOP= QAction(QIcon(imageMetrics), 'Compute MOPS', self)
        actionComputeMOP.setToolTip('Click to compute and display the performances of your algorithm!')
        icon  = QIcon(imageMetrics)
        actionComputeMOP.setIcon(icon)
        actionComputeMOP.triggered.connect(self.computeMOP);
        menuMetrics.addAction(actionComputeMOP)
        
        imageMetrics = QPixmap("icones/displayDiagram.png")
        actionComapreMOP= QAction(QIcon(imageMetrics), 'Compare MOPS', self)
        actionComapreMOP.setToolTip('Click to comapre and display the performances of several algorithms!')
        icon  = QIcon(imageMetrics)
        actionComapreMOP.setIcon(icon)
        actionComapreMOP.triggered.connect(self.compareMOP);
        menuMetrics.addAction(actionComapreMOP)
        #===========================
        # Tools
        #===========================
        
        menuMetrics = self.menuBar().addMenu("&Tools");
        imageART = QPixmap("icones/art.png")
        actionART= QAction(QIcon(imageMetrics), 'Convert ART database', self)
        actionART.setToolTip('Click to convert ART database to pysim database!')
        icon  = QIcon(imageART)
        actionART.setIcon(icon)
        actionART.triggered.connect(self.convertART_d);
        menuMetrics.addAction(actionART)
        
        #===========================
        # tracking tools
        #===========================
    
#        menuTracking = self.menuBar().addMenu("&Tracking tools"); 
#        imageT = QPixmap("icones/tracker.png")
#        actionT= QAction(QIcon(imageT), 'tracker', self)
#        actionT.setToolTip('click to load tracker!')
#        icon  = QIcon(imageT)
#        actionT.setIcon(icon)
#        actionT.triggered.connect(self.loadTracker);
#        #actionQuitter.setIconSize(QSize(10, 10))
#        menuTracking.addAction(actionT)

    def csvOutput(self):
            dockControls = QDockWidget("CSV parameters");
            dockControls.setWindowIcon(QIcon('icones\connection.png'))
            dockControls.setWindowTitle('CSV parameters')
            self.addDockWidget(Qt.LeftDockWidgetArea, dockControls) 
            myWidget = QWidget()
         
            _box = QVBoxLayout();
            self.csv_radar = QCheckBox('radar output')
            self.csv_radar.setCheckState(Qt.Unchecked)
            self.csv_radar.toggled.connect(self.csv_control)
            self.csv_fileRadar    = QLineEdit()
            self.csv_fileRadar.setEnabled(False)
            label            = QLabel('csv radar file');
            _boxH = QHBoxLayout()
            _boxH.addWidget(label)
            _boxH.addWidget(self.csv_fileRadar)
            
            _box.addWidget(self.csv_radar)
            _box.addLayout(_boxH)
            
            myWidget.setLayout(_box)
            
            
            
            dockControls.setWidget(myWidget)
    def csv_control(self): 
       
         if self.csv_radar!= None and self.csv_radar.checkState()==Qt.Checked:
             self.csv_fileRadar.setEnabled(True)
             self.csv_fileRadar.setText('radar.csv')
                
                
            
    def SextantChatMessage(self):

        json = self.ui_SafirControls.lineEdit_chatMessage.text()
        cmd = str(' { \
                     "code": 10,\
                     "chat": {"emitter":"server", "message":"')+str(json)+str('"}}')
        #print(cmd)
        self.sextantServer.sendJsonCommand(cmd);
        self.ui_SafirControls.textEdit_Chat.append("server"+str(": ")+str(json))
    def sendJsonMessage(self,json):
        json = self.ui_SafirControls.textEdit_Json.toPlainText()
        self.sextantServer.sendJsonCommand(json);
    def sendSextantQuitSafir(self):
        self.receiveMessage("LEXLUTOR try to quit SAFIR NG...")
        cmd = str(' { \
                              "code": 5,\
                              "command": "quit",\
                              "node": ""\
                     }')
                
        self.sextantServer.sendJsonCommand(cmd);
    def trySextantConnection(self):
        self.receiveMessage("LEXLUTOR try connection...")
        self.workerThread.start()
    def trySextantDisConnection(self):
        self.receiveMessage("LEXLUTOR disconnection...")
       
        self.sextantServer.close()
        self.workerThread.terminate()
 
    def convertART_d(self):
        
   
         self.ART.show()
 
    def connectionSEXTANT(self):
            dockControls = QDockWidget("Controls");
            dockControls.setWindowIcon(QIcon('icones\connection.png'))
            dockControls.setWindowTitle('LEXLUTOR protocol')
            self.addDockWidget(Qt.LeftDockWidgetArea, dockControls) 
            myWidget = QWidget()
            
            self.ui_SafirControls.setupUi(myWidget)
            self.ui_SafirControls.lineEdit_IPAdress.setText(str(ADRESS_IP))
            self.ui_SafirControls.lineEdit_Port.setText(str(TCP_PORT))
            self.ui_SafirControls.pushButton.setEnabled(True)
            #self.ui_SafirControls.groupBox.setEnabled(False)
            self.ui_SafirControls.pushButton_connect.clicked.connect(self.trySextantConnection)
            self.ui_SafirControls.pushButton.clicked.connect(self.trySextantDisConnection)
            self.ui_SafirControls.pushButton_sendMessage.clicked.connect(self.SextantChatMessage)
            self.ui_SafirControls.pushButton_SendConfiguation.clicked.connect(self.sendSextantConfiguration)
            self.ui_SafirControls.pushButton_QuitSafir.clicked.connect(self.sendSextantQuitSafir)
            self.ui_SafirControls.pushButton_SendJson.clicked.connect(self.sendJsonMessage)
            self.ui_SafirControls.checkBox_Java.stateChanged.connect(self.SextantJava)
            self.ui_SafirControls.lineEdit_IPAdress.editingFinished.connect(self.newIP)   
            self.ui_SafirControls.lineEdit_Port.editingFinished.connect(self.newPort)   
            
#            self.ui_SafirControls.pushButton_NTP.clicked.connect(self.SextantNTP)
     
 
            dockControls.setWidget(myWidget)
    def newIP(self):
        self.sextantServer.newIP(self.ui_SafirControls.lineEdit_IPAdress.text())
    def newPort(self):
        self.sextantServer.newPort(self.ui_SafirControls.lineEdit_Port.text())
        
    def SextantJava(self, int ):
        if self.ui_SafirControls.checkBox_Java.isChecked():
             self.sextantServer.onlyJson = True
        else:
             self.sextantServer.onlyJson = False
    def compareMOP(self):
        
        self.MOPCompare.show()
        pass
        
    def computeMOP(self):
        
        self.MOP.show() 
    def connection(self):
#        window = QDialog()
#        ui = Ui_Connection()
#        ui.setupUi(window)
#        if window.exec_() == QDialog.Accepted  :
#          
#             
#                    self.clientShield = ClientIHM( 'Client', ui.lineEditIP.text())
#                    self.clientShield.message.connect(self.receiveMessage)
        dockControls = QDockWidget("Connection/ouput");
        dockControls.setWindowIcon(QIcon('icones\connection.png'))
        dockControls.setWindowTitle('Shield protocol')
        self.addDockWidget(Qt.LeftDockWidgetArea, dockControls)
        myWidget = QDialog()
        self.clientUI.setupUi(myWidget)
        self.clientUI.lineEdit_IPAdress.setText(str(ADRESS_IP))
        self.clientUI.lineEdit_Port.setText(str(TCP_PORT))
        #self.clientUI.pushButton.setEnabled(False)
        self.clientUI.groupBox.setEnabled(False)
        self.clientUI.pushButton_connect.clicked.connect(self.tryShieldConnection)
        self.clientUI.pushButton.clicked.connect(self.tryShieldDisConnection)
        self.clientUI.pushButton_sendMessage.clicked.connect(self.shieldChatMessage)
        self.clientUI.pushButton_SendConfiguation.clicked.connect(self.sendConfiguration)
        self.clientUI.pushButton_SendSemanticInfo.clicked.connect(self.sendSemanticInfo)
        self.clientUI.pushButton_NTP.clicked.connect(self.shieldNTP)
        
         
        dockControls.setWidget(myWidget)  
    def shieldNTP(self):
        pass
        # if self.clientShield!=None:
        #    self.clientShield.getNTPTime()
    def sendSextantConfiguration(self):
            self.sextantServer.sendConfiguration()
    def sendSemanticInfo(self):
        print('in sendSemanticInfo' )
        #attention test toujours sensor 0
        if self.clientShield!=None:
            print('---->' )
            fname = QFileDialog.getOpenFileName(self, 'Open file',  'c:\\',"Image files (*.jpg *.gif *.png)")
            for _node in self.manager.nodes():
                for _sensor in _node.sensors:
                    print('in   sensor')
                    if str(_sensor.id) == str(2):
                            self.clientShield.sendSemanticInfo(_sensor,fname[0])
        
    def sendConfiguration(self):
        #envoie toute la configuration vers le C2
        print('in sendConfiguration' )
        if self.clientShield!=None:
 
            self.clientShield.sendConfiguration()
    def shieldConnected(self):
        self.clientUI.pushButton.setEnabled(True)
        self.clientUI.groupBox.setEnabled(True) 
        self.clientUI.pushButton_connect.setEnabled(False)
        self.clientUI.groupBox_Command.setEnabled(True)
    def shieldDisonnected(self):
        self.clientUI.pushButton.setEnabled(False)
        self.clientUI.groupBox.setEnabled(False) 
        self.clientUI.pushButton_connect.setEnabled(True)
        self.clientUI.groupBox_Command.setEnabled(False)
    def shieldChatMessage(self):
        
        msg = self.clientUI.lineEdit_chatMessage.text()
        if msg and self.clientShield!=None:
            self.clientUI.lineEdit_chatMessage.setText('')
            msgList = []
            msgList.append('me client')
            msgList.append(msg)
            self.shieldChat(msgList)
            self.clientShield.sendChatMessage(msgList)
    def shieldChat(self,msgList):
        #msgList structure name et contenu du msg
        new_message =  '['+msgList[0]+']'+'----> '+ msgList[1]

        if new_message  :
            self.clientUI.textEdit_Chat.append(new_message)
        
    def tryShieldDisConnection(self):
        if self.clientShield!=None:
            self.clientShield.stop()
            del self.clientShield
            self.clientShield = None
    def tryShieldConnection(self):
      pass

            
#        else:
#            self.clientShield.start() 
    def addMobileNode(self):
        _node = MobileNode()
        self.manager.addNode(_node)
        _nodelist = []
        _nodelist.append(_node)
        self.GIS.receiveNodes()
        self.sextantServer.receiveNodes()
    def addNode(self):
        
        _node = Node()
        self.manager.addNode(_node)
        self.GIS.receiveNodes()
        self.sextantServer.receiveNodes()
    def addRandTarget(self):
        if utm_isDefined() == False:
          self.showWarningDialog('area of interest is not defined')
          return
      
        _rand = RandomTargets(self.GIS)
        if _rand.editRandomTarget() == 1:
            self.receiveMessage("random targets added")
            
            for _tar in _rand.targets : 
                       self.manager.addTarget(_tar)
                       self.GIS.receiveTarget(_tar) 
            
    def addTarget(self):  
            
        _target = Target()
        _target.gis = self.GIS
        self.manager.addTarget(_target)
        self.GIS.receiveTarget(_target)
        
    def deleteSensor(self,idSensor):
        for _node in self.manager.nodes():
            for _sensor in _node.sensors :
                if _sensor.id == idSensor:
                    print('do delete sensor')
                    _node.removeSensor(idSensor)
                    return
    def deleteNode(self,idNode):
        print('todo delete nodes')
        self.manager.removeNode(idNode)
 
    def deleteTarget(self, idTarget):
        #attention idTarget est un string
        self.manager.removeTarget(idTarget)
  
    def newTracker(self,id_node):
        for _node in self.manager.nodes():
           _trackers = []
           if _node.id == id_node: 
               if _node.tracker!=None:
                   self.showWarningDialog('tracker exists already!')
                   return
               #print(['add Tracjer for node :', id_node])    
               MyTracker         = Tracker()
               MyTracker.node    = _node
               MyTracker.id_node = id_node
               _trackers.append(MyTracker)
               _node.tracker     = MyTracker
               self.receiveTrackers(_trackers)
               self.saver.saveTrackers(MyTracker)
               
    def newSensor(self,id_node):
        print(f"newsensor sur {id_node} node")
        for _node in self.manager.nodes():
           _sensor = []
           if _node.id == id_node:  
               MySensor         = Sensor()
               
               
               MySensor.id_node = id_node
               _sensor.append(MySensor)
               self.receiveSensors(_sensor)
          
    def editTracker(self,id_tracker):
        _sensors = []
        for _pnode in self.manager.nodes():
            _sensors+=_pnode.sensors
        for _node in self.manager.nodes():
      
            if _node.tracker!= None and int(_node.tracker.id) == int(id_tracker):
         
   
                if _node.tracker.editTracker(self.manager.targets(),_sensors) ==1 :
                   _node.tracker.update()
                   _node.tracker.toDisplay(self.axes,self.canvas)
    def editSensor(self,id_sensor):

        for _node in self.manager.nodes():
            for _sensor in _node.sensors:
                print('in edit sensor')
                if _sensor.id == id_sensor:
                    if _sensor.editSensor() ==1 :
                        _sensor.update()
                        if utm_isDefined() == False:
                                self.showWarningDialog('area of interest is not defined')
                        _sensor.toDisplay(self.axes,self.canvas,getReferenceTime())
    def editNode(self,id_node):
        print(len(self.manager.nodes()))
        for _node in self.manager.nodes():
            print('in for edit node')
            if _node.id == id_node:
                print('id node:', id_node) 
                if _node.editNode() ==1 :
                   
                    _node.update()
                    if utm_isDefined() == False:
                      self.showWarningDialog('area of interest is not defined')
                    _node.toDisplay(self.axes,self.canvas)
                    


                    
    def editTarget(self,idTarget) :         
         for _target in self.manager.targets():
            if _target.id == int(idTarget): 
                    if _target.editTarget() == 1:
                       _target.update()
    def question(self,message='no message',title='no title'):
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Question)
            msg.setText( message)
            msg.setWindowTitle(title)
 
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
 
            return msg.exec_()                  
    def showWarningDialog(self,_message):
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText(_message)
            msg.setWindowTitle("Warning")
            msg.setStandardButtons(QMessageBox.Ok )
            msg.exec_()
                   
    def locationNode(self,id_node):
        
        for _node in self.manager.nodes():
            if _node.id == id_node: 
                    _node.selectedNode = True
                    
                    if type(_node) == Node :
                        self.action = ACTION.NODE_LOCATION
                    if type(_node) == MobileNode :
                        self.action = ACTION.PLATFORM_TRAJECTORY
    def trajectoryTarget(self,idTarget) :
         #attention idTarget est un string
         
         for _target in self.manager.targets():
            if _target.id == int(idTarget): 
                    _target.selectedTarget = True
                    
         self.action = ACTION.TARGET_TRAJECTORY
         

    def receiveChatMessage(self,message):
        self.ui_SafirControls.textEdit_Chat.append(message)
    def receiveMessage(self,message):    
        
        self.console.write(message)
        

        
    def loadDataBase(self):
        self.console.write("load database")
        fileName, _  = QFileDialog.getOpenFileName(self, 'open dataBase', '.','*.db')        
        if fileName:
                self.loader.loadData(fileName,self.GIS)
                #self.loader.selectGIS(self.GIS)
#    def computeAndStoreOSPA(self,filename):
#        ground_truth = self.loader.newArray(filename+"gt.db")
#
#        n_nodes = ground_truth.shape[3]
#
#        n_times = ground_truth.shape[2]
#
#        gospa = np.zeros((n_times,n_nodes))
#        ospa = np.zeros((n_times,n_nodes))
#        mask = np.zeros((n_times,n_nodes))
#        cards = np.zeros((2,n_times,n_nodes))
#        mse = np.zeros((n_times,n_nodes))
#        
#        self.timer.progressBar.setMinimum(1)
#        self.timer.progressBar.setMaximum(100)
#        time = getReferenceTime()
#
#        for k in range(100):
#            time_c = time.addMSecs(k+1)
#            self.timer.setRunTime(time_c)
#            run = self.loader.newArray(filename+"run_%d.db"%k)
#            for j in range(n_nodes):
#                for t in range(n_times):
#                    if (ground_truth[:,2,t,j]>0).any():
#                        if (ground_truth[:,2,t,j]==2).any():
#                            Y = np.zeros((0,2))
#                        else:
#                            Y = ground_truth[ground_truth[:,2,t,j]>0,:2,t,j]
#                        if (run[:,2,t,j]>0).any():
#                            X = run[run[:,2,t,j]>0,:2,t,j]
#                        else:
#                            X = np.zeros((0,2))
#                        tmp1,tmp2,tmp3,tmp4 = gospa_ospa_distances(X,Y)
#                        gospa[t,j] += tmp1
#                        ospa[t,j] += tmp2
#                        cards[0,t,j] += tmp3[0]
#                        cards[1,t,j] += tmp3[1]
#                        mse[t,j] += tmp4
#                        mask[t,j] = 1
#
#        for j in range(n_nodes):
#            maskj = np.nonzero(mask[:,j])[0]
#            gospaj = gospa[maskj,j]/100
#            ospaj = ospa[maskj,j]/100
#            cardsj = cards[:,maskj,j]/100
#            msej = mse[maskj,j]/100
#            gospa_ospa = np.concatenate((gospaj,ospaj,cardsj[0,:],cardsj[1,:],msej)).reshape((5,len(maskj)))
#            self.saveNumpy(filename+"gospa_ospa_node_%d.db"%j,gospa_ospa)

    


    def receiveTime(self,_time ):
        
        if not self.isStarted :
            return
        #print(time.toString("hh:mm:ss.z"))
        self.console.write(("receiveTime time : %s")%(_time.toString("hh:mm:ss.z")))    
            
        #chargement des données

        self.loader.receiveTime(_time)
        
        #Usynchro
  
        if mainwindow.variableGlobale  == 0 :
            self.sextantServer.synchronize(_time )
            mainwindow.variableGlobale = self.u  
        mainwindow.variableGlobale -= 1
       
        #position des cibles
   
         

        for _target in self.manager.targets():
            if utm_isDefined() == False:
                self.showWarningDialog('area of interest is not defined')    
                return
            _target.displayCurrentTime(_time,self.axes,self.canvas)
      
            
            json = _target.toJson(_time)
            if json!='':
 
                self.sextantServer.sendJsonMessage(json)
       
         
         
        ''' 
        for _node in self.manager.nodes():
            
            if type(_node) == MobileNode:
                _node.displayCurrentTime(_time,self.axes,self.canvas)
                json = _node.toJson(_time,ADRESS_IP)
                if json!='':
    
                    self.sextantServer.sendJsonMessage(json)
                
       
        ''' 
        #self.canvas.draw_idle()
#        
 
        #self.canvas.blit(self.axes.bbox)
   
        '''
        xlim = self.axes.get_xlim()
        ylim = self.axes.get_ylim()
        self.axes.set_xlim(xlim)
        self.axes.set_ylim(ylim) 
        '''
        #self.canvas.draw()
        self.canvas.flush_events()
 
        
        #self.canvas.update()
        QApplication.processEvents()
 

    def pauseTime(self):
        self.loader.pause()
        for _node in self.manager.nodes():
                if _node.tracker!=None:
                   _node.tracker.pause()
        self.console.write("pause timer")    
    def stopTime(self):
        self.isStarted = False
        self.loader.stop()
        self.console.write("stop timer")
        #===============
        #  saveDatabase
        #===============
        fileName = './data/base/tmp.db' 
        self.saver.saveData(fileName)
        
        mainwindow.variableGlobale = 0
        for _tar in self.manager.targets():
            _tar.synchronized = False
        for _node in self.manager.nodes():
                if _node.tracker!=None:
                   _node.tracker.stop()
        # nettoyage des scan capteurs
        for _node in self.manager.nodes():
               
            for _sensor in _node.sensors:
                _sensor.clear()  
                # _sensor.displayScan(self.axes,self.canvas)
        self.canvas.draw()
        self.canvas.update()
        
    def onscroll(self, event):
        bbox = self.axes.axis()                
        bornx = bbox[1]-bbox[0]
        borny = bbox[3]-bbox[2]
        if event.button == 'up':
            self.ind =  5#
            self.GIS.zoomLevel = self.GIS.zoomLevel +1
            self.axes.set_xlim(event.xdata-bornx/self.ind,event.xdata+bornx/self.ind)
            self.axes.set_ylim(event.ydata-borny/self.ind,event.ydata+borny/self.ind)
        else:
            self.ind =  5#self.ind - 1
            self.GIS.zoomLevel = self.GIS.zoomLevel -1
            
            if(event.xdata-bornx*self.ind<-180) or (event.xdata+bornx*self.ind>180):
                self.axes.set_xlim(-180 ,180)
            else:
                self.axes.set_xlim(event.xdata-bornx*self.ind,event.xdata+bornx*self.ind)
            if(event.ydata-borny*self.ind<-90) or (event.ydata+borny*self.ind>90):
                self.axes.set_ylim(-90 ,90)
            else :               
                self.axes.set_ylim(event.ydata-borny*self.ind,event.ydata+borny*self.ind)
            
       
        self.axes.set_aspect('equal', 'datalim')
        self.canvas.draw() 
    def drawLine(self,_color): 
          
         if len(self.currentSelection)>=1:
              x = []
              y = []
              for pos in self.currentSelection:
                    x.append(pos[0]) 
                    y.append(pos[1])
          

              line, = self.axes.plot(x,y,  color=_color,marker="o",alpha = 0.5)
              self.selection =  line
              self.canvas.draw()
              
    def drawPolygon(self,_color): 
         if len(self.currentSelection)>=3:
              x = []
              y = []
              for pos in self.currentSelection:
                    x.append(pos[0]) 
                    y.append(pos[1])
              box_coords = list(zip(x, y))      

              polygon = Polygon(box_coords,  color=_color, edgecolor='violet',alpha = 0.5)
              self.selection = self.axes.add_patch(polygon)
              self.canvas.draw()
    def closeEvent(self, event):

        self.quitProgram()          
    
    def moveEvent(self, event):  
 
        if self.action == ACTION.AREAOfINTEREST:
 
            if self.x0 != None and event!= None  :
                self.x1 = event.xdata
                self.y1 = event.ydata
                self.rect.set_width(float(self.x1 - self.x0))
                self.rect.set_height(float(self.y1 - self.y0))
                self.rect.set_xy((self.x0, self.y0))
                self.rect.set_visible(True)
                self.canvas.draw()
    def releaseMouseEvent(self, QMouseEvent):
        
        if self.action == ACTION.AREAOfINTEREST and QMouseEvent!=None and self.x1!=None and self.y1!=None:
  
            self.action = ACTION.NOACTION
            self.GIS.x0 = self.x0
            self.GIS.y0 = self.y0
            self.GIS.x1 = self.x1
            self.GIS.y1 = self.y1
            mid_x = self.GIS.x0 + float((self.GIS.x1 - self.GIS.x0)/2) ;
            mid_y = self.GIS.y0 + float((self.GIS.y1 - self.GIS.y0)/2) ;
            self.x0 = None
            self.y0 = None
            self.x1 = None
            self.y1 = None
            utm_getZone(mid_x)    
            utm_isNorthern(mid_y)
            
            self.receiveReferencePoint(("%s %s 0.0")%(str(mid_x),str(mid_y)))
            self.rect.set_visible(False)
            self.GIS.newAreaOfInterest()
            
        cursor =QCursor()            
    def pressEvent(self, event):
        
         if event.button   == 3 and  self.action == ACTION.NOACTION :
             
             self.action = ACTION.NOACTION
             
         elif event.button   == 1 and self.action == ACTION.AREAOfINTEREST and event!=None:
            
            self.receiveMessage("AREAOfINTEREST action activated ")
            self.x0 = event.xdata
            self.y0 = event.ydata    
            self.rect.set_visible(True)
         elif event.button   == 1 and self.action ==ACTION.NODE_LOCATION:
             if len(self.currentSelection)==0:
                     for _node in self.manager.nodes():
             
                         if _node.selectedNode :
                             _node.selectedNode = False
                             pos =  [event.xdata  ,event.ydata]
                             _node.setLocation(pos)
                             if utm_isDefined() == False:
                                self.showWarningDialog('area of interest is not defined')
                             _node.toDisplay(self.axes,self.canvas)
                   
                     self.selection = None
                     self.currentSelection.clear() 
                     
             self.action = ACTION.NOACTION       
         elif event.button   == 3 and self.action == ACTION.PLATFORM_TRAJECTORY :
             
             if len(self.currentSelection)>=2:
                 for _node in self.manager.nodes():
                     if _node.selectedNode :
                        _node.setWayPoints(self.currentSelection)
                        _node.selectedTarget = False
                        _node.toDisplay(self.axes,self.canvas) 
                 self.axes.lines.remove(self.selection)
                 self.canvas.draw_idle()
                 self.selection = None
                 self.currentSelection.clear()
             self.action = ACTION.NOACTION              
         elif event.button   == 3 and self.action == ACTION.TARGET_TRAJECTORY:
             
             if len(self.currentSelection)>=2:
                 for _target in self.manager.targets():
                     if _target.selectedTarget :
                        _target.setWayPoints(self.currentSelection)
                        _target.selectedTarget = False
                        self.GIS.receiveTarget(_target)
                 self.axes.lines.remove(self.selection)
                 self.canvas.draw_idle()
                 self.selection = None
                 self.currentSelection.clear()
             self.action = ACTION.NOACTION                
                 
         elif event.button   == 3 and self.action == ACTION.SELECTION:
             
             if len(self.currentSelection)>=3:
                 self.loader.setFilter(self.currentSelection)
                 self.drawPolygon('cyan')
                 self.currentSelection.clear()
                 
             self.action = ACTION.NOACTION
         
         elif event.button   == 1 and self.action == ACTION.TARGET_TRAJECTORY:

             if self.selection!=None:
                 self.selection.remove()
                 self.selection = None
                 
             pos =  [event.xdata  ,event.ydata]
             self.currentSelection.append(pos)
             self.drawLine('red')
         elif event.button   == 1 and self.action == ACTION.PLATFORM_TRAJECTORY:

             if self.selection!=None:
                 self.selection.remove()
                 self.selection = None
                 
             pos =  [event.xdata  ,event.ydata]
             self.currentSelection.append(pos)
             self.drawLine('red')    
         elif event.button   == 1 and self.action == ACTION.SELECTION:

             if self.selection!=None:
                 self.selection.remove()
                 self.selection = None
                 
             pos =  [event.xdata  ,event.ydata]
             self.currentSelection.append(pos)
             self.drawPolygon('magenta')
    
    def saveData(self):
        self.console.write("save data")
        fileName, _  = QFileDialog.getSaveFileName(self, 'save data', '.','*.db')        
        if fileName:
                self.saver.saveData(fileName)
                self.saver.saveReferencePoint()
                self.saver.saveNodes( getReferenceTime() )
                self.saver.saveClass() 
                self.saver.saveTargets()
                self.saver.saveGIS(self.GIS)
                for _node in self.manager.nodes():
                    if _node.tracker!=None:
                        self.saver.saveTracks(_node.tracker.tracks)
    def saveNumpy(self,filename,array):
        self.console.write("Save numpy array")
        if filename:
                self.saver.createNumpyTable(filename)
                self.saver.saveNumpyTable(array)
                self.saver.closeNumpyTable()


    def selectData(self):
         self.action = ACTION.SELECTION
    def newAreaOfInterest(self):
        
       self.action = ACTION.AREAOfINTEREST     
    def graphicalArea(self):
        
        self.fig        =  Figure((5.0, 4.0), dpi=100)
        self.axes       = self.fig.add_subplot(111)
        self.canvas     = FigureCanvas(self.fig)
        self.canvas.setFocusPolicy(Qt.StrongFocus)
        self.canvas.setFocus()
     

        #canvas.mpl_connect('key_press_event', self.on_key_press)         

        self.canvas.draw()
        self.canvas.show()
 
        self.rect = Rectangle((0,0), 1, 1, facecolor='violet', edgecolor='violet',alpha = 0.5)
        self.rect.set_visible(False)
        self.axes.add_patch(self.rect)   
        self.x0 = None
        self.y0 = None
        self.x1 = None
        self.y1 = None
        
  

    def DockWidget(self):
        
        dock = QDockWidget("GIS");
        dock.setWindowIcon(QIcon('icones\layer.png'))
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)     
        dock.setWidget(self.GIS.tree)
        

        
    def quitProgram(self):
        del self.timer
   
        for _node in self.manager.nodes():
                if _node.tracker!=None:
                   _node.tracker.stop()
                   del _node.tracker
        
               
        self.sextantServer.close()
        self.workerThread.terminate()
#        while  self.workerThread.isFinished()==False : 
#            {
#                    }
            
            
        self.loader.stop()
        self.threadLoader.terminate()
#        while  self.threadLoader.isFinished()==False : 
#            {
#                    }
#        
        
        
        self.close()
        os._exit(1)
def main():
  
    app = QApplication(sys.argv)
    main = mainwindow()
    return sys.exit(app.exec_())
      
 
if __name__ == "__main__":
    main()
