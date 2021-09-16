# -*- coding: utf-8 -*-
"""
Created on Thu Sep  9 13:31:27 2021

@author: benja
outil de conversion d'une base ART en une base pysim
"""
import sqlite3
from sqlite3 import Error

import point
from point import REFERENCE_POINT,ecef_to_enu3DVector,ecef_to_enuMatrix,enu_to_ecef
import threading
import numpy as np
import io
from Managers.dataManager import DataManager as dataManager
from sensor import Node, Sensor,SensorCoverage, FOVType, SensorBias
from scan import Plot,PLOTType, Scan
import sqlite3

from target  import Target,TARGET_TYPE, RECORDED_TYPE
from saver   import saveData

from tool_tracking.track import Track
from tool_tracking.state import State
from tool_tracking.motionModel import StateType

import datetime

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtOpenGL import *
from PyQt5.QtWidgets import *

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


 


    
    
class reader(QWidget):
    message = pyqtSignal('QString');
    conn = None
    date = None
    longitude = -1
    latitude  = -1
    altitude  = -1
    nodes     = []
    sensors    = []
    parameters = []
    tracks     = []
 
    def openFile(self, file):
        if self.create_connection(file)==None:
            return False
        return True
    
    #=================
    #reference point 
    #=================
    def create_connection(self, db_file):
 
        try:
            print("try connection")
            self.conn = sqlite3.connect(db_file)
            print("dataBase opened")
           
            return self.conn
        except Error as e:
            print(e)
        return None
    
    #===================
    # select reference point
    #===================
    def selectReferencePoint(self):
        self.conn.row_factory = sqlite3.Row
        cur = self.conn.cursor()
        c = cur.execute("SELECT  *  FROM DeviceContext WHERE ContextId=1 ORDER BY TimeStampBegin ASC LIMIT 1;")
        data= c.fetchone()  
  
        self.longitude = float(data['Coordinate1'])
        self.latitude  = float(data['Coordinate2'])
        self.altitude  = float(data['Coordinate3'])
        stamp = int(data['TimeStampBegin'])
     
     
        self.date = QDateTime.fromMSecsSinceEpoch(stamp)#.toString("yyyy-MM-dd HH:mm:ss.zzzz")
     
       
   
       
        self.conn.row_factory = False;
        
        return True
    
    #====================
    # Track
    #====================
    
    def selectTrack(self):
        self.conn.row_factory = sqlite3.Row
        cur = self.conn.cursor()
        c = cur.execute("SELECT  DISTINCT DeviceTrackID, ScenarioTrackID FROM Track where ActiveTime > 100  ;")
        data = c.fetchall() 
       
        for row in data :
            
              _track               = Track() 
              self.tracks.append(_track)
              idTrack   = int(row['ScenarioTrackID'])
              idDevice  = int(row['DeviceTrackID'])
              _track.id = int(str(row['ScenarioTrackID'])+str(row['DeviceTrackID']))
              _track.id_node = '1'
              _track.addtionnalInfo.append(('idART',int(row['ScenarioTrackID'])))
        self.message.emit(('nombre de piste %s')%(len(self.tracks)))     
        progress = QProgressDialog("converting tracks...", "Abort conversion", 0, len(self.tracks), self)
        progress.setWindowModality(Qt.WindowModal)   
   
        i = 0
        for _track in self.tracks:
            self.conn.row_factory = sqlite3.Row
            cur = self.conn.cursor()
            c = cur.execute(("SELECT  * FROM Track where ScenarioTrackID =%s and DeviceTrackID=%s  ORDER BY  ScenarioTimeStamp;")%(idTrack,idDevice))
            data = c.fetchall() 
            idPere = -1
            i+=1
            progress.setValue(i)
            if progress.wasCanceled():
                 break
            for row in data :
                
                if progress.wasCanceled():
                 break
    
                progress.setValue(i) 
                _state          = State()
                _state.id       = int(row['ID']) 
                _state.idPere   = idPere
                idPere          = _state.id 
                _state.time     = QDateTime.fromMSecsSinceEpoch(int(row['ScenarioTimeStamp']))
                _classe = TARGET_TYPE.UNKNOWN
 
                      
                _state.classe   = _classe
                
        
                
                x = - float(row['DeviceCoordinate1'])
                y =   float(row['DeviceCoordinate2'])
                z =   float(row['DeviceCoordinate3'])
                
                vx = - float(row['ScenarioVelocity1'])
                vy =   float(row['ScenarioVelocity2'])
                vz =   float(row['ScenarioVelocity3'])
                #latitude.append(float(row['latitude']) )
                #longitude.append(float(row['longitude']))
                        
                        
        
           
             
                ox,oy,oz           = enu_to_ecef(0.0,0.0,0.0,REFERENCE_POINT.latitude,REFERENCE_POINT.longitude,REFERENCE_POINT.altitude )
         
                xLoc = ecef_to_enu3DVector(x,y,z,REFERENCE_POINT.latitude,REFERENCE_POINT.longitude,REFERENCE_POINT.altitude)
                vLoc = ecef_to_enu3DVector(vx+ox,vy+oy,vz+oz,REFERENCE_POINT.latitude,REFERENCE_POINT.longitude,REFERENCE_POINT.altitude)
                #le vecteur state doit être en ENU
      
                _state.state = np.array([xLoc[0],vLoc[0] ,xLoc[1],vLoc[1]  ,xLoc[2],vLoc[2] ])
                _state.mode = StateType.XYZ
      
                P = np.eye(6)
   
                _state.covariance = ecef_to_enuMatrix(P,REFERENCE_POINT.latitude,REFERENCE_POINT.longitude,REFERENCE_POINT.altitude)
                _state.updateLocation() 
                _state.updateCovariance()
                
                
                _state.addtionnalInfo.append(('Power',float(row['Power'])))
                _state.addtionnalInfo.append(('Clutter',float(row['Clutter'])))
                _state.addtionnalInfo.append(('Doppler',float(row['Doppler'])))
                if _state.idPere==-1  :
                    _track.tree.data = _state
                     
                elif   _state.idPere!=-1:
           
                        pere = _track.getCurrentState()
                        _track.addState(_state,pere)
        progress.setValue(len(self.tracks))
 
    #====================
    # node radar
    #====================
    def selectRadarNode(self):
        self.conn.row_factory = sqlite3.Row
        cur = self.conn.cursor()
        c = cur.execute("SELECT  *  FROM DeviceContext WHERE ContextId=1  ;")
        data = c.fetchall() 
        
        for row in data :
            node = Node('1')
            node.color = QColor(Qt.gray)
            node.name  = 'ART'
            node.typeNode   =  'SENSOR_NODE'
            node.Position.setWGS84(float(row['Coordinate2'] ),float(row['Coordinate1'] ),float(row['Coordinate3'] ))
            stamp = int(row['TimeStampBegin'])
            node.date = QDateTime.fromMSecsSinceEpoch(stamp)#.toString("yyyy-MM-dd HH:mm:ss.zzzz")
            node.Orientation.setOrientation(0.0,0.0,0.0)
            self.nodes.append(node)
            
        self.conn.row_factory = sqlite3.Row
        cur = self.conn.cursor()
        c = cur.execute("SELECT  * FROM ParameterValue where ParameterInfoID=14;")
        data = c.fetchall()       
 
        count = 0  
        for row in data :    
          stamp = int(row['TimeUpdated'])
          dt    =  QDateTime.fromMSecsSinceEpoch(stamp)
 
          angle =  row['Double']
  
          if count == 0:
              for _node in self.nodes:
                  #init
                  _node.Orientation.setOrientation(angle,0.0,0.0)
 
              
   
          
          while count < len(self.nodes) and dt> self.nodes[count].date:
              count = count+1
          
           
          self.nodes[count-1].Orientation.setOrientation(angle,0.0,0.0)
          
          for _node in self.nodes[count:-1]:
                  #init
                  _node.Orientation.setOrientation(angle,0.0,0.0)
                  
      
              
            
        #==================       
        #sensor radar
        #==================
    
        sensor = Sensor(1,False)
 
        sensor.color    = QColor(Qt.yellow)
        sensor.id_node  = '1'
        sensor.setSensorType('radar3D')
        sensor.name     = 'ART radar'
       
        self.sensors.append(sensor)
    
        for _node in self.nodes:
             _node.sensors.append(sensor)
        #==================
        #parameter radar
        #==================
      
        coverage = SensorCoverage()
    
        coverage.type           = FOVType.CONICAL
     
            
        coverage.fov            = 90
        coverage.distanceMin    = 0
        coverage.distanceMax    = 4
        coverage.fov_elevation  = 30 
        coverage.id_Sensor      = sensor.id
    
        coverage.name           = TARGET_TYPE.UNKNOWN
                
        coverage.parameters.pd  = 0.9
        coverage.parameters.pfa = 0.0001 
      
        coverage.parameters.sigmaRho    = 1
       
        coverage.parameters.sigmaTheta  = 0.01
     
        coverage.parameters.sigmaPhi    = 0.01
     
                
        sensor.sensorCoverage=[]
        sensor.sensorCoverage.append(coverage)  
          
class convertART(QWidget):
    message = pyqtSignal('QString');
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
    
    
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent) 
       
        self.path_i = QLineEdit() #chemin vers le répertoire contenant les bases de données
        self.path_o = QLineEdit() #chemin vers le répertoire contenant les bases de données
        btn_i       = QPushButton('...', self)
        btn_o       = QPushButton('...', self)
        btn_i.clicked.connect(self.showDialog)
        btn_o.clicked.connect(self.showDialog_2)
        self.setWindowTitle('Database conversion')  
        self.setWindowIcon(QIcon(QPixmap("icones/art.png")))
   
        layout                          = QVBoxLayout()
        layoutPath_i                    = QHBoxLayout()
        layoutPath_o                    = QHBoxLayout()
        
        layoutPath_i.addWidget(self.path_i)
        layoutPath_i.addWidget(btn_i)
        layoutPath_o.addWidget(self.path_o)
        layoutPath_o.addWidget(btn_o)      
        
        layout.addLayout(layoutPath_i)
        layout.addLayout(layoutPath_o)
        
        buttonLayout = QHBoxLayout();
        but_ok = QPushButton("Compute")
        buttonLayout.addWidget(but_ok )
        but_ok.clicked.connect(self.OnOk)
        but_cancel = QPushButton("Cancel")
        buttonLayout.addWidget(but_cancel )
        but_cancel.clicked.connect(self.OnCancel)
       
        layout.addLayout(buttonLayout)
         
        self.setLayout(layout)
        
        self.base = reader()
        self.base.message.connect(self.message)
        
        #saver
        
        self.saver= saveData()
    def OnCancel(self):
        self.hide()
    def OnOk(self):
        
        self.base.openFile(self.path_i.text())
        
        self.newReferences()
        self.base.selectRadarNode()
        self.base.selectTrack()
        
        if self.path_o.text()!='':
            self.saver.saveData(self.path_o.text())
            self.saver.saveReference(self.base.latitude,self.base.longitude,self.base.altitude,self.base.date)
            self.saver.saveAllNodes(self.base.nodes)
            self.saver.saveAllTracks(self.base.tracks)
        #=====> Fin
        self.hide()
    def showDialog(self):
        text = QFileDialog.getOpenFileName(self, 'input database', '.','*.db')
        if text!='':
            self.path_i.setText(str(text[0]))
    def showDialog_2(self):
        text = QFileDialog.getSaveFileName(self, 'output database', '.','*.db')
        if text!='':
            self.path_o.setText(str(text[0]))

    
    def newReferences(self):
        if self.base.selectReferencePoint():
            self.message.emit(('%f %f %f')%(self.base.longitude,self.base.latitude,self.base.altitude) )
            self.message.emit(self.base.date.toString("yyyy-MM-dd HH:mm:ss.zzzz"))
            self.referencePoint.emit(('%f %f %f')%(self.base.longitude,self.base.latitude,self.base.altitude) )
            self.referenceTime.emit(self.base.date)
        else:
            
            self.receiveMessage('unable to load reference point and time')
    def receiveMessage(self,_message=''):
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText(_message)
            msg.setWindowTitle("Warning")
            msg.setStandardButtons(QMessageBox.Ok )
            msg.exec_() 
    

def main(arg1, **kwargs):
    
    convert(arg1,kwargs)
     

if __name__ == "__main__":
    main()
    
    