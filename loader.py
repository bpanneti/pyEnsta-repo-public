# -*- coding: utf-8 -*-
"""
Created on Tue Jul  2 16:02:40 2019

@author: bpanneti
"""

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtOpenGL import *
from PyQt5.QtWidgets import *


import sqlite3
from sqlite3 import Error
import point
from point import REFERENCE_POINT,ecef_to_enu3DVector,ecef_to_enuMatrix,enu_to_ecef
import threading
import numpy as np
import io
from Managers.dataManager import DataManager as dataManager
from sensor import Node, Sensor,SensorCoverage, FOVType, SensorBias
from scan import Plot,PLOTType, Scan, State as plotState
from target  import Target,TARGET_TYPE, RECORDED_TYPE

from tool_tracking.tracker import Tracker

from tool_tracking.track import Track
from tool_tracking.estimator import TRACKER_TYPE
from tool_tracking.motionModel import StateType
from tool_tracking.state import State
import tool_tracking as tr
from tool_tracking.BiasProcessing.loader.biasCorrectorLoader import BiasCorrectorLoader

import matplotlib.pyplot as plt

def adapt_array(arr):
    out = io.BytesIO()
    np.save(out, arr)
    out.seek(0)
    return sqlite3.Binary(out.read())

def convert_array(text):
    out = io.BytesIO(text)
    out.seek(0)
    return np.load(out)

sqlite3.register_adapter(np.array, adapt_array)    
sqlite3.register_converter("ARRAY", convert_array)

def index_of(val, in_list):
    try:
        return in_list.index(val)
    except ValueError:
        return -1   
    
class selectData(QWidget):
    emitNodes       = pyqtSignal(list)
    emitSensors     = pyqtSignal(list)
    emitParameters  = pyqtSignal(list)
    emitDetections  = pyqtSignal(list)
    emitStates      = pyqtSignal(list)
    
    def __init__(self, parent=None):
        super(selectData, self).__init__()
        self.conn = None
        self.date = None
        self.previousDate = None
        

         
    def run(self):
        
        if self.conn!=None:
    
            #==================        
            # select nodes
            #==================
 
                self.conn.row_factory = sqlite3.Row
                cur = self.conn.cursor()
                c = cur.execute(("SELECT  * FROM node_t where date<='%s' and date>'%s';"%(self.date.toString("yyyy-MM-dd HH:mm:ss.zzz"),self.previousDate.toString("yyyy-MM-dd HH:mm:ss.zzz"))))
                data = c.fetchall()  
               
                nodes =[]
    
                for row in data :
               
                    _str =  str(row['color']) 
                    _str =_str.replace('{','');
                    _str =_str.replace('}','');
                    color = _str.split(',');
         
        
                    
                    node = Node(row['id_node'])
                    node.color = QColor(int(color[0]),int(color[1]),int(color[2]))
                    #node.color.setRgb(color[0],color[1],color[2])
        
                    node.typeNode   = row['type_node']
                    node.Position.setWGS84(float(row['longitude'] ),float(row['latitude'] ),float(row['altitude'] ))
                    node.Orientation.setOrientation(float(row['yaw'] ),float(row['pitch'] ),float(row['roll'] ))
                             
              
                    #on ajour le noeud à al liste des noeuds
                    nodes.append(node)
                
                if nodes!=[]:
             
                    self.emitNodes.emit(nodes)
                
                self.conn.row_factory = False;
             
            #==================#        
            # select sensors   #
            #==================#

                self.conn.row_factory = sqlite3.Row
                cur = self.conn.cursor()
                c = cur.execute(("SELECT  * FROM sensor_t where date<='%s' and date>'%s';"%(self.date.toString("yyyy-MM-dd HH:mm:ss.zzz"),self.previousDate.toString("yyyy-MM-dd HH:mm:ss.zzz"))))
                data = c.fetchall()  
          
                sensors =[]
    
                for row in data :
                
                    _str =  str(row['color']) 
                    _str =_str.replace('{','');
                    _str =_str.replace('}','');
                    color = _str.split(',');
         
        
                     
                    sensor = Sensor(row['id_sensor'])
                                   
                
 
                    sensor.color    = QColor(int(color[0]),int(color[1]),int(color[2]))
                    sensor.id_node  = row['id_node']
                    sensor.setSensorType(row['sensorType'])
                    sensor.name     = row['sensorName']
                    #on ajour le noeud à al liste des noeuds
                    sensors.append(sensor)
                 
                if sensors!=[]:
                    self.emitSensors.emit(sensors)
                self.conn.row_factory = False;
            
            #==================#        
            # select parameters#
            #==================#   

                self.conn.row_factory = sqlite3.Row
                cur = self.conn.cursor()
                c = cur.execute(("SELECT  * FROM parameters_t where date<='%s' and date>'%s';"%(self.date.toString("yyyy-MM-dd HH:mm:ss.zzz"),self.previousDate.toString("yyyy-MM-dd HH:mm:ss.zzz"))))
                data = c.fetchall()  
          
                parameters =[]
                for row in data :
                    coverage = SensorCoverage()
                    if row['coverageType']==3:
                        coverage.type           = FOVType.CONICAL
                    if row['coverageType']==2:
                        coverage.type           = FOVType.SPHERICAL
                    if row['coverageType']==1:
                        coverage.type           = FOVType.SECTOR
                        
                    
                    coverage.fov            = float(row['Component_3'])
                    coverage.distanceMin    = float(row['Component_1'])
                    coverage.distanceMax    = float(row['Component_2'])
                    coverage.fov_elevation  = float(row['Component_4'])  
                    coverage.id_Sensor      =  row['id_sensor']   
                    
                    for u in TARGET_TYPE:
                        if u.name == row['classType']:
                            coverage.name = u
                    coverage.parameters.pd  = float(row['DetectionProbability'])  
                    coverage.parameters.pfa = float(row['FaProbability'])
                    try:  
                        coverage.parameters.sigmaRho    = float(row['sigma_rho'])  
                        coverage.parameters.sigmaTheta  = float(row['sigma_theta']) 
                        coverage.parameters.sigmaPhi    = float(row['sigma_phi'])
                    except:
                        coverage.parameters.sigmaRho    = 1.0  
                        coverage.parameters.sigmaTheta  = 0.1
                        coverage.parameters.sigmaPhi    = 0.1
                        parameters.append(coverage)
      
                if parameters!=[]:    
                    self.emitParameters.emit(parameters)
                self.conn.row_factory = False

            #==================#        
            # select detection #
            #==================#
         
                self.conn.row_factory = sqlite3.Row
                cur = self.conn.cursor()
                #4print(("SELECT  * FROM plot_t where date<='%s' and date>'%s';"%(self.date.toString("yyyy-MM-dd HH:mm:ss.z"),self.previousDate.toString("yyyy-MM-dd HH:mm:ss.z"))))
                c = cur.execute(("SELECT  * FROM plot_t where date<='%s' and date>'%s';"%(self.date.toString("yyyy-MM-dd HH:mm:ss.zzz"),self.previousDate.toString("yyyy-MM-dd HH:mm:ss.zzz"))))
                data = c.fetchall()  
          
                detections = []
           
                for row in data :
                    if float(row['locComposant_1'])!=0.0:
     
                      _plot = Plot()
                      _plot.rho            = float(row['locComposant_1'])
                      _plot.theta          = float(row['locComposant_2'])
                      _plot.phi            = float(row['locComposant_3'])
                      _plot.sigma_rho      = float(row['locSTDType_1'])
                      _plot.sigma_theta    = float(row['locSTDType_2'])
                      _plot.sigma_phi      = float(row['locSTDType_2'])
                      _plot.idScan         = int(row['id_Scan'])
                      _plot.idSensor       = row['id_sensor']
                      _plot.dateTime       = QDateTime.fromString(row['date'],"yyyy-MM-dd HH:mm:ss.zzz")
                      _plot.doppler        = float(row['velocityComposant_1'])
                      _plot.sigma_doppler  = float(row['velocitySTDType_1'])
                      _plot.id             = int(row['id_Plot'])
     
                      if row['locationFormat']=='polar':
                            _plot.type           = PLOTType.POLAR
                      if row['locationFormat']=='spherical':
                            _plot.type           = PLOTType.SPHERICAL
                      _plot.Classification = "UNKNOWN"
                      _plot.ProbaClassification = 1.0
                      _plot.info_1         =  row['dataType_1']
                      _plot.value_info_1   =  float(row['data_1'])
                      _plot.info_2         =  row['dataType_2']
                      _plot.value_info_2   =  float(row['data_2'])
                      detections.append(_plot)
      
                #même vide on emet
                self.emitDetections.emit(detections)
    
            
            #==================#        
            # select states    #
            #==================#
         
                self.conn.row_factory = sqlite3.Row
                cur = self.conn.cursor()
                #4print(("SELECT  * FROM plot_t where date<='%s' and date>'%s';"%(self.date.toString("yyyy-MM-dd HH:mm:ss.z"),self.previousDate.toString("yyyy-MM-dd HH:mm:ss.z"))))
                c = cur.execute(("SELECT  * FROM state_t where date<='%s' and date>'%s';"%(self.date.toString("yyyy-MM-dd HH:mm:ss.zzz"),self.previousDate.toString("yyyy-MM-dd HH:mm:ss.zzz"))))
                data = c.fetchall()  
          
                states = []
                container = [] 
                for row in data :
 
                    if int(row['id_state']) in container :
                        continue
                 
                    container.append(int(row['id_state']))
                    _state          = State()
                    _state.id       = int(row['id_state']) 
                    _state.idPere   = int(row['id_parent']) 
                    _state.time     = QDateTime.fromString(row['date'],"yyyy-MM-dd HH:mm:ss.zzz")
                    _classe = TARGET_TYPE.UNKNOWN
                
                    for type_t in TARGET_TYPE:
                        if type_t.value.correspondance == row['classe'] :
                             _classe  = type_t
                             break
                          
                    _state.classe   = _classe
                    
                    _str            = str(row['estimated_state']) 
      
                    _str =_str.replace('{','');
                    _str =_str.replace('}','');
                    x = _str.split(',');
                    x = np.array(x)
                    x = x.astype(np.float)
            
                    ox,oy,oz           = enu_to_ecef(0.0,0.0,0.0,REFERENCE_POINT.latitude,REFERENCE_POINT.longitude,REFERENCE_POINT.altitude )
             
                    xLoc = ecef_to_enu3DVector(x[0],x[2],x[4],REFERENCE_POINT.latitude,REFERENCE_POINT.longitude,REFERENCE_POINT.altitude)
                    vLoc = ecef_to_enu3DVector(x[1]+ox,x[3]+oy,x[5]+oz,REFERENCE_POINT.latitude,REFERENCE_POINT.longitude,REFERENCE_POINT.altitude)
                    #le vecteur state doit être en ENU
                    
                    _state.state = np.array([xLoc[0],vLoc[0] ,xLoc[1],vLoc[1]  ,xLoc[2],vLoc[2] ])
              
                    _state.mode = StateType.XYZ
                    _str =  str(row['estimated_covariance']) 
                    _str2 = _str.split('},');
                    P = np.zeros([6,6])
                    for i,t in zip(range(0,6),_str2):
                        t =t.replace('{','');
                        t =t.replace('}','');  
                        x = t.split(',');
                        x= np.array(x)
                        x= x.astype(np.float)
                        P[i,:] = x
                    
                    _state.covariance = ecef_to_enuMatrix(P,REFERENCE_POINT.latitude,REFERENCE_POINT.longitude,REFERENCE_POINT.altitude)
                    _state.updateLocation() 
                    _state.updateCovariance()
                
                
           
                    _plots = [] 
                    _str =  str(row['id_plots']) 
                    _str =_str.replace('{','');
                    _str =_str.replace('}','');
                    _strPlots = _str.split(',');
                    for i,t in zip(range(0,len(_strPlots)),_strPlots):
                        _plots.append(_strPlots[i])
                  
                    states.append(_state)
                          
                #même vide on emet
                self.emitStates.emit(states)         
            
            
    def connection(self,conn):
      
        self.conn = conn
        

class data(QWidget):
    message         = pyqtSignal('QString')
    referencePoint  = pyqtSignal('QString')
    referenceTime   = pyqtSignal('QDateTime')
    endTime         = pyqtSignal('QDateTime')
    
    emitNodes               = pyqtSignal()
    emitSensors             = pyqtSignal(list)
    emitParameters          = pyqtSignal(list)
    emitDetections          = pyqtSignal(list)
    emitSelectedDetections  = pyqtSignal(list)
    emitTargets             = pyqtSignal()
    emitTrackers            = pyqtSignal(list)
    emitBiasCorrectors      = pyqtSignal()
    emitStates              = pyqtSignal(list)
    def __init__(self, parent=None):
    
        super(data, self).__init__()
        self.conn = None
 
        self.previousDate    = QDateTime.currentDateTime
        
        #self.readThread  = threading.Thread(target=self.readData) 
            #self.WrittenThread = threading.Thread(target=self.write) 
         
   
        self.previousDate   = None
        self.selectData     = selectData()
        #self.thread         = QThread()
        self.selectData.emitNodes.connect(self.receiveNodes)
        self.selectData.emitSensors.connect(self.receiveSensors)
        self.selectData.emitParameters.connect(self.receiveParameters)
        self.selectData.emitDetections.connect(self.receiveDetections)
        self.selectData.emitStates.connect(self.receiveStates)
        #self.selectData.moveToThread(self.thread)
        #self.thread.started.connect(self.selectData.run)
        self.Pause = False
        self.Polygon = QPolygon()
    def receiveStates(self,_states):
        
        self.emitStates.emit(_states)
    def receiveDetections(self, _detections):
        #print("---> receiveDetections ")
        flag = False
        
        if _detections ==[]:
             for _sensor in dataManager.instance().sensors():
                 _sensor.scan = None
        for det in _detections: 
            for _sensor in dataManager.instance().sensors():
                if det.idSensor == _sensor.id and _sensor.node!=None:
                
                     if flag==False:
                     
                         _sensor.realData = True;
                         _scan = Scan(det.dateTime,_sensor)
                         _scan.sensorPosition        = _sensor.node.Position 
                         _scan.sensorOrientation     = _sensor.node.Orientation
                         _sensor.setScanType(_scan)
                         _sensor.scan = _scan
                         flag = True
                 
                     det.updateLocation(_scan)

                     _scan.plots.append(det)
                   
 
         
        #test pour savoir si les détections sont dans le polygon
        #print(["len detection :", len(_detections)])
        _detSelected = []
        i = 0
        if self.Polygon.isEmpty() == False:
            for det in _detections:
                i = i+1
                
                _p = QPoint(det.Position.longitude*10000,det.Position.latitude*10000)
      
                
                if self.Polygon.containsPoint(_p,Qt.WindingFill)==True:
                    _detSelected.append(det)
        
        if _detections !=[]:
            self.emitDetections.emit(_detections)
            
        if _detSelected!=[]:
            #print('plots selected')
            self.emitSelectedDetections.emit(_detSelected)
            
        
    def receiveParameters(self,parameters):
        _sensrToUpdate = [];
        self.emitParameters.emit(parameters)
        '''
        for _param in parameters:
            for _node in dataManager.instance().nodes():
                for _sensor in _node.sensors:
                    if _param.id_Sensor == _sensor.id:
                        _sensrToUpdate.append(_sensor)
                        if _sensor.sensorCoverage == None:
                            _sensor.sensorCoverage = []
                        _sensor.sensorCoverage.append(_param)
                        
        if _sensrToUpdate!=[]:
            self.emitSensors.emit(_sensrToUpdate)                
        '''                
    def containsNode(self,node):
            
            for _node in dataManager.instance().nodes():
                if _node.id == node.id:
                    return True        
            return False
        
    def containsSensor(self,sensor):
            
            for _sensor in dataManager.instance().sensors():
                    if _sensor.id == sensor.id:                      
                        return True        
            return False
        
    def receiveNodes(self,nodes):
        for _node in  nodes:
            #print('in for or receive node')
            if dataManager.instance().searchNode(_node.id) == None:
                dataManager.instance().addNode(_node)
            else:
                
              
                for _cnode in dataManager.instance().nodes():
                    sensorList = []
                    if _cnode.id == _node.id : 
                        dataManager.instance().removeNode(_node.id)
                        sensorList = _node.sensors
                        break
                
                dataManager.instance().addNode(_node)
                _node.sensors = sensorList
                              
                 
                #mise à jour de l'objet node dans la classe sensor
                for _sensor in sensorList:           
               
                        _sensor.node = _node
            
        if nodes!=[]:
            print('emit nodes in loader')
            self.emitNodes.emit()

    def testSensorRealData(self,_sensor):
         cur = self.conn.cursor()
      
         c = cur.execute("SELECT COUNT(*) FROM plot_t;")
         data = c.fetchone()  
       
         if data:
          _sensor.realData = True;
             
         cur = self.conn.cursor()
      
         c = cur.execute("SELECT COUNT(*) FROM state_t;")
         data = c.fetchone()  
       
         if data:
          _sensor.realData = True;
    def receiveSensors(self,sensors):
        for _sensor in  sensors:  
 
            for _node in dataManager.instance().nodes():
                if _node.id == _sensor.id_node:
                     flag = False
                     for _sensorLoc in _node.sensors:
                         if _sensorLoc.id == _sensor.id :                             
                             flag = True
                     self.testSensorRealData(_sensor)        
                     if flag == False:     
                         _node.sensors.append(_sensor)
                         _sensor.node=_node

        if sensors!=[]:
           
            self.emitSensors.emit(sensors)
            
            
            
    def pause(self):
        self.Pause = True
        #self.readThread.do_run = False 
        #self.thread.wait()
    def stop(self):
        #print("stop loader")
        self.Pause = False
        self.selectData.previousDate  = None
       # self.readThread.do_run = False 
        #self.thread.wait()
    def start(self):
        self.Pause = False
        #self.thread.start()

    def receiveTime(self,_date = QDateTime()):
 
        if self.selectData.previousDate == None:
            self.selectData.previousDate = _date
        else :
            self.selectData.previousDate = self.selectData.date
            
        self.selectData.date = _date;
    
        self.selectData.run(); 
     
    def tableExists(self,table):
         cur = self.conn.cursor()
         cur.execute((''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='%s' ''')%(table))
         if cur.fetchone()[0]==1 : 
             return True
             
         return False
     
    def infoData(self):
        
        if self.conn!=None:
         
            cur = self.conn.cursor()
            #base structurée SEXTANT
            #nombre de plots
 
           
            #if the count is 1, then table exists

            if self.tableExists('plot_t'):            
                c = cur.execute("SELECT COUNT(*) FROM plot_t;")
                data = c.fetchone()  
                self.message.emit((" ==== dataBase contains %d plots")%(data))
            #nombre de noeuds
            if self.tableExists('node_t'): 
                c = cur.execute("SELECT  COUNT(DISTINCT id_node) FROM node_t;")
                data = c.fetchone()  
                self.message.emit((" ==== dataBase contains %d noeuds")%(data))
                
            if self.tableExists('track_t'): 
               try :
 
                    c = cur.execute("SELECT  COUNT(DISTINCT id_node) FROM track_t;")
                    data = c.fetchone()  
                    self.message.emit((" ==== dataBase contains %d tracker")%(data))
               except :
                    pass  
                
                
            #nombre de capteurs
            if self.tableExists('sensor_t'): 
                c = cur.execute("SELECT  COUNT(DISTINCT id_sensor) FROM sensor_t;")
                data = c.fetchone()  
                self.message.emit((" ==== dataBase contains %d capteurs")%(data))
            if self.tableExists('groundTrue_t'): 
                c = cur.execute("SELECT  COUNT(DISTINCT id_target) FROM groundTrue_t;")
                data = c.fetchone()  
                self.message.emit((" ==== dataBase contains %d targets")%(data))

                
            self.conn.row_factory = sqlite3.Row
            cur = self.conn.cursor()
            c = cur.execute("SELECT  *  FROM referencePoint_t;")
            data = c.fetchone()  
            self.message.emit((" ==== reference point %f %f %f")%(data['longitude'],data['latitude'],data['altitude']))
            self.message.emit((" ==== reference time %s")%(data['date']))
            self.conn.row_factory = False;
            
            
            
        
            
            
            self.message.emit((" ==== reference point %f %f %f")%(data['longitude'],data['latitude'],data['altitude']))
            self.message.emit((" ==== reference time %s")%(data['date']))
            self.conn.row_factory = False;
            
            
    def selectGIS(self,_gis):
        cur = self.conn.cursor()
        c = cur.execute("SELECT  *  FROM gis_t;")
        data = c.fetchall()  
        for row in data :
            if row['nature'] == 'roads':
                _gis.fileName = row['path']
                _gis.currentItem = _gis.layerRoad
                _gis.openFile('road')
            if row['nature'] == 'vegetation':
                _gis.fileName = row['path']
                _gis.currentItem = _gis.layerVegetation
                _gis.openFile('vegetation')
            if row['nature'] == 'buildings':
                _gis.fileName = row['path']
                _gis.currentItem = _gis.layerBuilding
                _gis.openFile('building')
            if row['nature'] == 'water':
                _gis.fileName = row['path']
                _gis.currentItem = _gis.layerWater
                _gis.openFile('water')
            if row['nature'] == 'waterArea':
                _gis.fileName = row['path']
                _gis.currentItem = _gis.layerWaterArea
                _gis.openFile('waterArea')
            if row['nature'] == 'image':
                  _str =  str(row['path']) 
                  _str =_str.replace('{','');
                  _str =_str.replace('}','');
                  _cartes = _str.split(',');
                  for _carte in _cartes:
                      _gis.fileName = _carte
                      _gis.currentItem = _gis.layerCarto
                      _gis.openFile('Maps')
            if row['nature'] == 'dted':
                  _str =  str(row['path']) 
                  _str =_str.replace('{','');
                  _str =_str.replace('}','');
                  _cartes = _str.split(',');
                  for _carte in _cartes:
                      _gis.fileName = _carte
                      _gis.currentItem = _gis.layerDTED
                      _gis.openFile('DTED')
            if row['nature'] == 'area':
                  _str =  str(row['path']) 
                  _str =_str.replace('{','');
                  _str =_str.replace('}','');
                  _coord = _str.split(',');
                  _gis.x0 = float(_coord[0])
                  _gis.y0 = float(_coord[1])
                  _gis.x1 = float(_coord[2])
                  _gis.y1 = float(_coord[3])
               
                  _gis.newAreaOfInterest()
                      
    def setFilter(self, _polygonWGS84):
        #initialise le filtre WGS84 de sélection de plots
        self.Polygon.clear()
        for point in _polygonWGS84:
            self.Polygon.append(QPoint(point[0]*10000,point[1]*10000))
        self.Polygon.append(self.Polygon.at(0))
        
        if self.Pause:
            
            #print('---> 1 ')
            #==================#        
            # select detection #
            #==================# 
            self.conn.row_factory = sqlite3.Row
            cur = self.conn.cursor()
            #print(("SELECT  * FROM plot_t where date<='%s' and date>'%s';"%(self.selectData.date.toString("yyyy-MM-dd HH:mm:ss.z"),self.selectData.previousDate.toString("yyyy-MM-dd HH:mm:ss.z"))))
            c = cur.execute(("SELECT  * FROM plot_t where date<='%s' and date>'%s';"%( self.selectData.date.toString("yyyy-MM-dd HH:mm:ss.zzz"),self.selectData.previousDate.toString("yyyy-MM-dd HH:mm:ss.zzz"))))
            data = c.fetchall()  
            #print('---> 2')
            detections = []
            
            for row in data :
              #print('yop pause in loader')
              _plot = Plot()
              _plot.rho            = float(row['locComposant_1'])
              _plot.theta          = float(row['locComposant_2'])
              _plot.phi            = float(row['locComposant_3'])
              _plot.sigma_rho      = float(row['locSTDType_1'])
              _plot.sigma_theta    = float(row['locSTDType_2'])
              _plot.sigma_phi      = float(row['locSTDType_2'])
              _plot.idScan         = int(row['id_Scan'])
              _plot.idSensor       = row['id_sensor']
              _plot.dateTime       = QDateTime.fromString(row['date'],"yyyy-MM-dd HH:mm:ss.zzz")
              _plot.doppler        = float(row['velocityComposant_1'])
              _plot.sigma_doppler  = float(row['velocitySTDType_1'])
              _plot.id             = int(row['id_Plot'])
              if row['locationFormat']=='polar':
                    _plot.type           = PLOTType.POLAR
              if row['locationFormat']=='spherical':
                    _plot.type           = PLOTType.SPHERICAL
              _plot.Classification = "UNKNOWN"
              _plot.ProbaClassification = 1.0
              _plot.info_1         =  row['dataType_1']
              _plot.value_info_1   =  float(row['data_1'])
              _plot.info_2         =  row['dataType_2']
              _plot.value_info_2   =  float(row['data_2'])
              detections.append(_plot)
            
            
            
            
        if self.Polygon.isEmpty() == False:
            
            _detSelected = []
            for det in detections:
                for _sensor in dataManager.instance().sensors():
                    if det.idSensor == _sensor.id and _sensor.node!=None:
                        det.updateLocation( _sensor)
                
                _p = QPoint(int(det.Position.longitude*10000),int(det.Position.latitude*10000))
      
                
                if self.Polygon.containsPoint(_p,Qt.WindingFill)==True:
                    _detSelected.append(det)
         
            
            if _detSelected!=[]:
                self.emitSelectedDetections.emit(_detSelected)  
                
    def updateComponents(self  ,date_begin = QDateTime(), date_end= QDateTime()):
      
        #==================#        
        # select nodes   #
        #==================# 

        self.conn.row_factory = sqlite3.Row
        cur = self.conn.cursor()
        c = cur.execute(("SELECT  * FROM node_t where date >='%s' and date<'%s';")%(date_begin.toString("yyyy-MM-dd HH:mm:ss.zzz"),date_end.toString("yyyy-MM-dd HH:mm:ss.zzz")))
        #print(("SELECT  * FROM node_t where date >='%s' and date<'%s';")%(date_begin.toString("yyyy-MM-dd HH:mm:ss.zzz"),date_end.toString("yyyy-MM-dd HH:mm:ss.zzz")))
        data = c.fetchall()  
        sensor = None
        node  = None


        for row in data : 
            print('in node')
            _str =  str(row['color']) 
            _str =_str.replace('{','');
            _str =_str.replace('}','');
            color = _str.split(',');
            node  = None
            for _node in dataManager.instance().nodes() :
     
                if _node.id == row['id_node'] :
                    node = _node
                    break
       
            if node ==None    :
                node = Node(row['id_node'])
                #on ajour le noeud à al liste des noeuds
                dataManager.instance().addNode(node) 
                print('adé')
            node.color = QColor(int(color[0]),int(color[1]),int(color[2]))
 
            node.typeNode   = row['type_node']
     
            node.Position.setWGS84(float(row['longitude'] ),float(row['latitude'] ),float(row['altitude'] ))
       
            node.Orientation.setOrientation(float(row['yaw'] ),float(row['pitch'] ),float(row['roll'] ))
                             
  
  
        
 
         
#        self.conn.row_factory = False;
 
        #==================#        
        # select sensors   #
        #==================#

#        self.conn.row_factory = sqlite3.Row
#        cur = self.conn.cursor()
        c = cur.execute(("SELECT  * FROM sensor_t where date >='%s' and date<'%s';")%(date_begin.toString("yyyy-MM-dd HH:mm:ss.zzz"),date_end.toString("yyyy-MM-dd HH:mm:ss.zzz")))
        data = c.fetchall()  
        sensors = []
  
       
        for row in data :
            sensor = None
            _str =  str(row['color']) 
            _str =_str.replace('{','');
            _str =_str.replace('}','');
            color = _str.split(',');
            flag = False
            for _node in dataManager.instance().nodes():
                for _sensor in _node.sensors:
                    if _sensor.id == row['id_sensor']:
                        sensor = _sensor
                        flag   = True 
                        break
            if flag==False:
 
                sensor = Sensor(row['id_sensor'],False)
                sensors.append(sensor) 
#                for _node in dataManager.instance().nodes() :
#                    if _node.id == row['id_node']:
#                        _node.sensors.append(sensor)
#                        sensor.node = _node
               
            sensor.color    = QColor(int(color[0]),int(color[1]),int(color[2]))
            sensor.id_node  = row['id_node']
            sensor.setSensorType(row['sensorType'])
            sensor.name     = row['sensorName']
            #dataManager.instance().addSensor(sensor)           
            
            
            try :
                
                sensor.timeOfSampling = float(row['timeOfSampling'])
            
            except:
                sensor.timeOfSampling = 1
                    #on ajour le noeud à al liste des noeuds
    
     
        dataManager.instance().addSensors(sensors) 
        self.conn.row_factory = False;

        #==================#        
        # select parameters#
        #==================#   
        
        #self.conn.row_factory = sqlite3.Row
        #cur = self.conn.cursor()
        c = cur.execute(("SELECT  * FROM parameters_t where date >='%s' and date<'%s';")%(date_begin.toString("yyyy-MM-dd HH:mm:ss.zzz"),date_end.toString("yyyy-MM-dd HH:mm:ss.zzz")))
        data = c.fetchall()  

        coverages  = []
        for row in data :

            coverage = SensorCoverage()
            if row['coverageType']==3:
                coverage.type           = FOVType.CONICAL
            if row['coverageType']==2:
                coverage.type           = FOVType.SPHERICAL
            if row['coverageType']==1:
                coverage.type           = FOVType.SECTOR
                
            coverage.fov            = float(row['Component_3'])
            coverage.distanceMin    = float(row['Component_1'])
            coverage.distanceMax    = float(row['Component_2'])
            coverage.fov_elevation  = float(row['Component_4'])  
            coverage.id_Sensor      = row['id_sensor']
            for u in TARGET_TYPE:
                if u.name == row['classType']:
                    coverage.name           = u
                    
            coverage.parameters.pd  = float(row['DetectionProbability'])  
            coverage.parameters.pfa = float(row['FaProbability'])  
            try :
                coverage.parameters.sigmaRho    = float(row['sigma_rho'])  
            except:
                coverage.parameters.sigmaRho    = 1
            try :    
                coverage.parameters.sigmaTheta  = float(row['sigma_theta']) 
            except:
                coverage.parameters.sigmaTheta  = 0.01
            try :
                coverage.parameters.sigmaPhi    = float(row['sigma_phi'])
            except :
                coverage.parameters.sigmaPhi    = 0.01
            coverages.append(coverage)
 
        if coverages!=[]:
          for _cover in coverages:
            for _sensor in dataManager.instance().sensors():  
             
                if _sensor.id == _cover.id_Sensor:
      
                    if _sensor.sensorCoverage == None:
                       _sensor.sensorCoverage = [_cover]
                    else:
                       _sensor.sensorCoverage.append(_cover)
          
                   
        sensor = None
        node   = None
 
        self.conn.row_factory = False;
      
    
        return
    def newComponents(self,date):
        
        if self.conn==None:
            return
        #==================#        
        # select nodes   #
        #==================# 
        
        self.conn.row_factory = sqlite3.Row
        cur = self.conn.cursor()
        c = cur.execute(("SELECT  * FROM node_t where date <='%s' ORDER BY date;")%(date.toString("yyyy-MM-dd HH:mm:ss.zzz")))
        data = c.fetchall()  
    
        nodes =[]
        
        for row in data :
               
            _str =  str(row['color']) 
            _str =_str.replace('{','');
            _str =_str.replace('}','');
            color = _str.split(',');
         
            node = Node(row['id_node'])
            node.color = QColor(int(color[0]),int(color[1]),int(color[2]))
 
            node.typeNode   = row['type_node']
     
            node.Position.setWGS84(float(row['longitude'] ),float(row['latitude'] ),float(row['altitude'] ))
           
            node.Orientation.setOrientation(float(row['yaw'] ),float(row['pitch'] ),float(row['roll'] ))
                             
              
            #on ajour le noeud à al liste des noeuds
            dataManager.instance().addNode(node)
            nodes.append(node)
            if nodes!=[]:
                self.emitNodes.emit()
         
        self.conn.row_factory = False;
              
        #==================#        
        # select sensors   #
        #==================#

        self.conn.row_factory = sqlite3.Row
        cur = self.conn.cursor()
        c = cur.execute(("SELECT  * FROM sensor_t where date <='%s' ORDER BY date;")%(date.toString("yyyy-MM-dd HH:mm:ss.zzz")))
        data = c.fetchall()  
          
        sensors =[]
 
        for row in data :
                
            _str =  str(row['color']) 
            _str =_str.replace('{','');
            _str =_str.replace('}','');
            color = _str.split(',');
                
            sensor = Sensor(row['id_sensor'])
 
            sensor.color    = QColor(int(color[0]),int(color[1]),int(color[2]))
            sensor.id_node  = row['id_node']
            sensor.setSensorType(row['sensorType'])
            sensor.name     = row['sensorName']
            
            
            try :
                
                sensor.timeOfSampling = float(row['timeOfSampling'])
            
            except:
                sensor.timeOfSampling = 1
                    #on ajour le noeud à al liste des noeuds
            sensors.append(sensor)
                 
    
            self.conn.row_factory = False;
   
        #==================#
        # real data or not #
        #==================#
        
        self.conn.row_factory = sqlite3.Row
        cur = self.conn.cursor()
        c = cur.execute("SELECT  * FROM plot_t ;") 
        data = c.fetchall()  
        if data:
            for _sensor in sensors:
                
                _sensor.realData = True;
        
        self.conn.row_factory = sqlite3.Row    
        cur = self.conn.cursor()
        c = cur.execute("SELECT  * FROM state_t ;") 
        data = c.fetchall()  
        if data:
            for _sensor in sensors:
                
                _sensor.realData = True;
          
        
        #==================#        
        # select parameters#
        #==================#   

        self.conn.row_factory = sqlite3.Row
        cur = self.conn.cursor()
        c = cur.execute(("SELECT  * FROM parameters_t where date <='%s' ORDER BY date;")%(date.toString("yyyy-MM-dd HH:mm:ss.zzz")))
        data = c.fetchall()  
          
  
        for row in data :
 
                coverage = SensorCoverage()
                if row['coverageType']==3:
                    coverage.type           = FOVType.CONICAL
                if row['coverageType']==2:
                    coverage.type           = FOVType.SPHERICAL
                if row['coverageType']==1:
                    coverage.type           = FOVType.SECTOR
                    
                coverage.fov            = float(row['Component_3'])
                coverage.distanceMin    = float(row['Component_1'])
                coverage.distanceMax    = float(row['Component_2'])
                coverage.fov_elevation  = float(row['Component_4'])  
                coverage.id_Sensor      = row['id_sensor']
                for u in TARGET_TYPE:
                    if u.name == row['classType']:
                        coverage.name           = u
                coverage.parameters.pd  = float(row['DetectionProbability'])  
                coverage.parameters.pfa = float(row['FaProbability'])
                try:  
                    coverage.parameters.sigmaRho    = float(row['sigma_rho'])  
                    coverage.parameters.sigmaTheta  = float(row['sigma_theta']) 
                    coverage.parameters.sigmaPhi    = float(row['sigma_phi'])
                except:
                    coverage.parameters.sigmaRho    = 1.0  
                    coverage.parameters.sigmaTheta  = 0.1
                    coverage.parameters.sigmaPhi    = 0.1

                for _sensor in sensors:
                    if _sensor.id == coverage.id_Sensor:
                        if _sensor.sensorCoverage == None:
                            _sensor.sensorCoverage = []
                        _sensor.sensorCoverage.append(coverage)
                        break
        
        #=============#        
        # select bias #
        #=============#   

        self.conn.row_factory = sqlite3.Row
        cur = self.conn.cursor()
        c = cur.execute(("SELECT name FROM sqlite_master where type='table' AND name='bias_t';"))
        result = c.fetchone()
        if result :
            c = cur.execute( "SELECT  * FROM bias_t ;") 
            data = c.fetchall()  

            for row in data :
                bias = SensorBias(int(row['id_sensor']), float(row['yaw']), float(row['x_ENU']), float(row['y_ENU']))

                for _sensor in sensors:
                    if int(_sensor.id) == bias.id:
                        _sensor.bias = bias
                        break
        else: 
             print('no table bias_t')

        if sensors!=[]:
            self.emitSensors.emit(sensors)
            dataManager.instance().addSensors(sensors) 
            
        self.conn.row_factory = False;

            #=======================#        
            # select bias corrector #
            #=======================#
        stmt = "SELECT name  FROM sqlite_master WHERE type='table'  AND name='roadCorrector_t' ; "
        c= cur.execute(stmt)
        result = c.fetchone()
        if result:
            BiasCorrectorLoader.load(self.conn, nodes, self.emitBiasCorrectors)

            #==================#        
            # select tracker#
            #==================# 
        self.conn.row_factory = sqlite3.Row
        cur = self.conn.cursor()
        stmt = "SELECT name  FROM sqlite_master WHERE type='table'  AND name='tracker_t' ; "
        c= cur.execute(stmt)
        result = c.fetchone()
        if result:    
        
            c = cur.execute( "SELECT  * FROM tracker_t ;") 
            data = c.fetchall()  
              
            trackers =[]
     
            for row in data :
          
      
                    
                tracker         = Tracker()
                tracker.id      = row['id_tracker']
                tracker.id_node = row['id_node']
                tracker.filter  = TRACKER_TYPE[row['type']]
                tracker.name    = row['name']
                if tracker.filter == TRACKER_TYPE.SIR:
                    tracker.trackerInfos = tr.sir.Infos(int(row['particlesNumber']), float(row['threshold']))
                
                _str =  str(row['targets']) 
                _str =_str.replace('{','');
                _str =_str.replace('}','');
                _targets = _str.split(',');
                
                _str =  str(row['sensors']) 
                _str =_str.replace('{','');
                _str =_str.replace('}','');
                _sensors = _str.split(',');
                
  
                if tracker.tracker!=None:
                    for i in _targets:
                        try:
                            tracker.tracker.targets.append(int(i))
                        except:
                            print("Empty targets list")
                 
                for _sensor in  dataManager.instance().sensors():
          
                    if index_of(str(_sensor.id),_sensors  )!=-1:
                        
                        tracker.sensors.append(_sensor)
                        if tracker.filter == TRACKER_TYPE.GMPHD:
                                tracker.trackerInfos = _sensor
                            
                tracker.loadTracker()        
                trackers.append(tracker)
                     
            self.emitTrackers.emit(trackers)
            self.conn.row_factory = False;
        else: 
             print('no table tracker_t')
    def loadPerformancesFromDataBase(self,field,database):
        self.conn.row_factory = sqlite3.Row
        cur = self.conn.cursor() 
        stmt = "SELECT name  FROM sqlite_master WHERE type='table'  AND name='performances_t' ; "
        c= cur.execute(stmt)
        result = c.fetchone()
        if result:    
            
            #==================        
            # select trackers
            #================== 
            nodes               = []
            conn                = sqlite3.connect(database)
            conn.row_factory    = sqlite3.Row
            cur                 =  conn.cursor()
            stmt = "SELECT *  FROM performances_t WHERE type='{0}' ; ".format(field)
       
            c= cur.execute(stmt)
            result = c.fetchall()
            
    
            perf =[]
            for row in result :
              perf.append((row['date'],float(row['value']))) 
 
                
            conn.row_factory = False;  
            
            return perf
        else: 
             print('no table performances_t')
             return []
    def loadTrackerFormDataBase(self,database):
            
            #==================        
            # select trackers
            #================== 
            nodes               = []
            conn                = sqlite3.connect(database)
            conn.row_factory    = sqlite3.Row
            cur                 =  conn.cursor()
            stmt = "SELECT name  FROM sqlite_master WHERE type='table'  AND name='tracker_t' ; "
            c= cur.execute(stmt)
            result = c.fetchone()
            
            if result:    
                      c                   = cur.execute("SELECT  DISTINCT id_node,name FROM tracker_t;")
                      data                = c.fetchall()  
                      for row in data :
                           nodes.append([row['id_node'],row['name']]) 
            else:
 
                       c                   = cur.execute("SELECT  DISTINCT id_node FROM track_t;")
                       data                = c.fetchall()  
                       for row in data :
                           nodes.append([row['id_node'],str('tracker_0')]) 
 
                
            conn.row_factory = False;  
            
            return nodes
    def loadTracksFormDataBase(self,database,idTracker = None,conditions=''):
         self.conn.close()
         self.conn = self.create_connection(database)
         print(conditions)
         return self.newTracks(idTracker,conditions)
    def newTracks(self,idTracker= None,condition=''):

        #==================#        
        # select targets   #
        #==================# 
        self.conn.row_factory = sqlite3.Row
        cur = self.conn.cursor()
   
 
        if idTracker!=None and condition!='':
           
            c = cur.execute("SELECT  *  FROM track_t where id_node == '%s' and %s"%(idTracker,condition)  )
        elif  condition!='':
            
            c = cur.execute("SELECT  *  FROM track_t where %s"%(condition))
        else: 
        
            c = cur.execute("SELECT  *  FROM track_t")
            
        data = c.fetchall()  
      
        tracks = []
 
        for row in data :
              _track               = Track() 
              tracks.append(_track)
              _track.id = int(row['id_track'])
    
        self.conn.row_factory = False;
            
        #==================#        
        # select states#
        #==================#   
    
      
        
        
        #latitude  = []
        #longitude = []
            
        for _track in tracks :
            self.conn.row_factory = sqlite3.Row
            cur = self.conn.cursor()
            c = cur.execute(("SELECT  * FROM state_t where id_track=='%s' ORDER BY date ASC;"%(_track.id)))
            data = c.fetchall()  
            flag = True
            container = []
            #print([REFERENCE_POINT.latitude,REFERENCE_POINT.longitude,REFERENCE_POINT.altitude])
            for row in data :
                if int(row['id_state']) in container :
                     continue
                 
                container.append(int(row['id_state']))
                _state          = State()
                _state.id       = int(row['id_state']) 
                _state.idPere   = int(row['id_parent']) 
                _state.time     = QDateTime.fromString(row['date'],"yyyy-MM-dd HH:mm:ss.zzz")
                _classe = TARGET_TYPE.UNKNOWN
                
                for type_t in TARGET_TYPE:
                    if type_t.value.correspondance == row['classe'] :
                         _classe  = type_t
                         break
                      
                _state.classe   = _classe
                
                _str            = str(row['estimated_state']) 
                
                
                #latitude.append(float(row['latitude']) )
                #longitude.append(float(row['longitude']))
                        
                        
                _str =_str.replace('{','');
                _str =_str.replace('}','');
                x = _str.split(',');
                x = np.array(x)
                x = x.astype(np.float)
                ox,oy,oz           = enu_to_ecef(0.0,0.0,0.0,REFERENCE_POINT.latitude,REFERENCE_POINT.longitude,REFERENCE_POINT.altitude )
         
                xLoc = ecef_to_enu3DVector(x[0],x[2],x[4],REFERENCE_POINT.latitude,REFERENCE_POINT.longitude,REFERENCE_POINT.altitude)
                vLoc = ecef_to_enu3DVector(x[1]+ox,x[3]+oy,x[5]+oz,REFERENCE_POINT.latitude,REFERENCE_POINT.longitude,REFERENCE_POINT.altitude)
                #le vecteur state doit être en ENU
      
                _state.state = np.array([xLoc[0],vLoc[0] ,xLoc[1],vLoc[1]  ,xLoc[2],vLoc[2] ])
                _state.mode = StateType.XYZ
                _str =  str(row['estimated_covariance']) 
                _str2 = _str.split('},');
                P = np.zeros([6,6])
                for i,t in zip(range(0,6),_str2):
                    t =t.replace('{','');
                    t =t.replace('}','');  
                    x = t.split(',');
                    x= np.array(x)
                    x= x.astype(np.float)
                    P[i,:] = x
                
                _state.covariance = ecef_to_enuMatrix(P,REFERENCE_POINT.latitude,REFERENCE_POINT.longitude,REFERENCE_POINT.altitude)
                _state.updateLocation() 
                _state.updateCovariance()
                
                #id plots
           
                _plots = [] 
                _str =  str(row['id_plots']) 
                _str =_str.replace('{','');
                _str =_str.replace('}','');
                _strPlots = _str.split(',');
                for i,t in zip(range(0,len(_strPlots)),_strPlots):
                    _plots.append(_strPlots[i])
              
              
                #_plots = _plots.astype(np.float)
                _state.idPlots = _plots
                
                
                #recherche du père
                
                
                
                
                
                
                pere = _track.getState(_state.idPere)
       

                if pere == None and (_state.idPere==-1 or flag):
                    _track.tree.data = _state
                    flag = False
#                    if _track.id == 1:
#                        print('---> 1')
                elif pere == None and _state.idPere!=-1:
                        pere = _track.getCurrentState()
                        _track.addState(_state,pere)
#                        if _track.id == 1:
#                            print('---> 2')
                else:
                 
                    _track.addState(_state,pere)
#                    if _track.id == 1:
#                              print('---> 3') 
#                if _track.id == 1:
#                         print(_state.idPere)
        self.conn.row_factory = False;
        #plt.plot(REFERENCE_POINT.longitude,REFERENCE_POINT.latitude, 'bo', linewidth= 2) 
        #plt.scatter(longitude,latitude,color = 'red',marker = '^') #             
        #==================
        # nettoyage des tracks 
        #==================

        for _track in tracks :
            _track.cutChilds()
        
        return tracks
    def newTargets(self):       
            #==================#        
            # select targets   #
            #==================# 
            self.conn.row_factory = sqlite3.Row
            cur = self.conn.cursor()
            #4print(("SELECT  * FROM plot_t where date<='%s' and date>'%s';"%(self.date.toString("yyyy-MM-dd HH:mm:ss.z"),self.previousDate.toString("yyyy-MM-dd HH:mm:ss.z"))))
            c = cur.execute("SELECT  * FROM groundTrue_t"  )
            data = c.fetchall()  
      
            targets = []

            for row in data :
              _target = None 

              for _tar in targets:
                  if _tar.id ==  int(row['id_target']):
                      _target = _tar              
                      break
              if _target == None:
                  _target               = Target() 
                  targets.append(_target)
                  _target.altitude      = float(row['altitude'])
                  _target.startVelocity      = float(row['velocity'])
                  _target.startTime     = QDateTime.fromString(row['date'],"yyyy-MM-dd HH:mm:ss.zzz")
                  _target.id            = int(row['id_target'])
                  _target.name          = row['name']
                  _target.recordedType = RECORDED_TYPE.BASE_ON_TIMETOWAYPOINTS

#                  try:
#                      _target.isRandomVelocity = int(row['isRandomVelocity'])
#                      if _target.isRandomVelocity== True:
#                          _target.recordedType = RECORDED_TYPE.BASED_ON_VELOCITY
#                  except:
#                      _target.isRandomVelocity = False
#                      _target.recordedType = RECORDED_TYPE.BASE_ON_TIMETOWAYPOINTS
                  try:
                      _target.isSplinTrajectory = int(row['isSplinTrajectory'])
                  except:
                      _target.isSplinTrajectory = False

                  for type_t in TARGET_TYPE:
                      if type_t.name==row['type']:
                          _target.type  = type_t
                          break

                      if row['type'] == 'DRONE_FIXWING' or row['type'] == 'DRONE_ROTARINGWING':
                          _target.type  = TARGET_TYPE.DRONE
                          break
                     
              _target.trajectoryWayPoints.append(point.Position(float(row['latitude']),float(row['longitude']),float(row['altitude'])))
              _target.timeToWayPoints.append(QDateTime.fromString(row['date'],"yyyy-MM-dd HH:mm:ss.zzz"))
              #_target.recordedType = RECORDED_TYPE.BASE_ON_TIMETOWAYPOINTS
           
              _target.velocityToWayPoints.append(float(row['velocity']))
              if _target.startVelocity <=0:
                  _target.recordedType = RECORDED_TYPE.BASE_ON_WAYPOINTS
            
              if _target.startVelocity <=0 and len(_target.trajectoryWayPoints)==2:
                      Point1 = _target.trajectoryWayPoints[0]
                      Point2 = _target.trajectoryWayPoints[1]
   
                      date1  = _target.timeToWayPoints[0]
                      date2  = _target.timeToWayPoints[1]
         
                      distance =  Point1.distanceToPoint(Point2)
                      delay    =  date1.secsTo(date2)
                      _target.startVelocity = distance/delay
                      _target.velocityToWayPoints[0] = _target.startVelocity
            
        
            
            if targets != []:
                dataManager.instance().addTargets(targets)
                for _tar in targets:
                    _tar.buildTrajectory()
                for _tar in targets:
                    _tar.buildTrajectory()
      
                self.emitTargets.emit()
                
    def create_connection(self, db_file):
 
        try:
            self.message.emit("try connection")
            conn = sqlite3.connect(db_file)
            self.message.emit("dataBase opened")
            self.selectData.connection(conn)
            return conn
        except Error as e:
            self.message.emit(e)
        return None

    def newReferences(self):
        
        #selectionne les nouvelles référence temporelle et position
        if self.conn!=None:
            self.conn.row_factory = sqlite3.Row
            cur = self.conn.cursor()
            c = cur.execute("SELECT  *  FROM referencePoint_t;")
            data = c.fetchone()  
 
            self.referencePoint.emit(('%f %f %f')%(data['longitude'],data['latitude'],data['altitude']) )
            date =QDateTime.fromString(data['date'],'yyyy-MM-dd HH:mm:ss.z')
            self.referenceTime.emit(date)
            self.conn.row_factory = False;

            self.conn.row_factory = sqlite3.Row
            cur = self.conn.cursor()
            c = cur.execute("SELECT  date  FROM state_t ORDER BY date DESC LIMIT 1;")
            data = c.fetchone()
            if data:
                dateEnd=QDateTime.fromString(data['date'],'yyyy-MM-dd HH:mm:ss.z')
          
            self.conn.row_factory = sqlite3.Row
            cur = self.conn.cursor()
            c = cur.execute("SELECT  date  FROM plot_t ORDER BY date DESC LIMIT 1;")
            data = c.fetchone()
            if data :
                dateEnd=QDateTime.fromString(data['date'],'yyyy-MM-dd HH:mm:ss.z')
            
            self.endTime.emit(dateEnd)
    def newArray(self,filename):

        self.conn = sqlite3.connect(filename, detect_types=sqlite3.PARSE_DECLTYPES)
        #selectionne les nouvelles référence temporelle et position
        if self.conn!=None:
            cur = self.conn.cursor()
            cur.execute("SELECT arr FROM array_t")
            return cur.fetchone()[0]
    def loadDetections(self,filename):        
        
            self.conn = sqlite3.connect(filename, detect_types=sqlite3.PARSE_DECLTYPES)
            self.conn.row_factory = sqlite3.Row
            cur = self.conn.cursor()
            c = cur.execute("SELECT  * FROM plot_t ;")
            data = c.fetchall() 
            #print('---> 2')
            detections = []
            
            for row in data :
              #print('yop pause in loader')
              _plot = Plot()
              _plot.rho            = float(row['locComposant_1'])
              _plot.theta          = float(row['locComposant_2'])
              _plot.phi            = float(row['locComposant_3'])
              _plot.sigma_rho      = float(row['locSTDType_1'])
              _plot.sigma_theta    = float(row['locSTDType_2'])
              _plot.sigma_phi      = float(row['locSTDType_2'])
              _plot.idScan         = int(row['id_Scan'])
              _plot.idSensor       = row['id_sensor']
              _plot.dateTime       = QDateTime.fromString(row['date'],"yyyy-MM-dd HH:mm:ss.zzz")
              _plot.doppler        = float(row['velocityComposant_1'])
              _plot.sigma_doppler  = float(row['velocitySTDType_1'])
              _plot.id             = int(row['id_Plot'])
              _plot.type           = PLOTType.NOTYPE
              if row['locationFormat']=='polar':
                    _plot.type           = PLOTType.POLAR
              if row['locationFormat']=='spherical':
                    _plot.type           = PLOTType.SPHERICAL
              _plot.Classification = "UNKNOWN"
              _plot.ProbaClassification = 1.0
              _plot.info_1         =  row['dataType_1']
              _plot.value_info_1   =  float(row['data_1'])
              _plot.info_2         =  row['dataType_2']
              _plot.value_info_2   =  float(row['data_2'])
              detections.append(_plot)
            return detections
    def loadData(self,filename):
        print('--> loadData')

        self.conn = self.create_connection(filename) 
        #print('infoData')
        self.infoData()
        #print('newReferences')
        self.newReferences()
        #print('loadTargets')
        self.newTargets()
        #print endtime
        
       
    #def receiveTime(self, time = QDateTime()):
        
        #selection des capteurs
        
        
