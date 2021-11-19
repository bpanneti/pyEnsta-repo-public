# -*- coding: utf-8 -*-
"""
Created on Mon Oct 28 10:21:43 2019

@author: bpanneti
"""
import sqlite3
import sys
from sqlite3 import Error
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtOpenGL import *
from PyQt5.QtWidgets import *
from enum import Enum 
from collections import namedtuple
import pynmea2
from datetime import datetime
import sys
import os
from distutils.dir_util import copy_tree

#=================
# kml tool
#=================
 
import simplekml


TYPE  = namedtuple('TargetType', ['value', 'gabarit','icone','velocity'])
class TARGET_TYPE(Enum):
 
    #TYPE , Gabarit in m (lxLxH), icon path, velocity min max in m/s
    UNKNOWN = TYPE(0,  [-1,-1,-1], 'icones_target/unknown.png', [0,30])
    PAX     = TYPE(1,  [0.5,0.8,1.8], 'icones_target/pax.png',     [0,8])
    CAR     = TYPE(2 , [1.8,4.2,2.0], 'icones_target/car.png',     [0,20])
    DRONE_FIXWING        = TYPE(3,  [0.3,0.3,0.2], 'icones_target/droneFIX.png',   [0,17])
    DRONE_ROTARINGWING   = TYPE(4,  [0.3,0.3,0.2], 'icones_target/drone.png',   [0,17])
    TANK    = TYPE(5,  [2.5,5.0,3.5], 'icones_target/tank.png',    [0,18])
    TRUCK   = TYPE(6,  [2.3,12.0,3.5], 'icones_target/truck.png',   [0,20]) 
def readSaveKMLFile(_file,output, Targetid, Targetname,TargetType ,deltaTime=0):
    file1 = open(_file, 'r') 
    Lines = file1.readlines()
    offset = -1
    dateTimeOld = QDateTime()
    
    
    kml =  simplekml.Kml()         
    folderTargets = kml.newfolder(name='target')
    fol = folderTargets.newfolder(name=Targetname)
    folLoc = fol.newfolder(name='locations')
    count = 0;
    Cumul =[]
    MyType = TARGET_TYPE.UNKNOWN
    
    
  
    for _type in TARGET_TYPE:
        if _type.name == TargetType:
            MyType = _type
    for _line in Lines:
        
 
            
        A = []
        flagOk = False
        MyDate = QDate
        if _file.endswith('.NMEA'):
            if _line.startswith("$GNRMC"):
                A = str.split(_line,',')
                _date = A[9]
        
                year = 2000+int(_date[4:6])
                month = int(_date[2:4])
                day = int(_date[0:2]) 
   
            if _line.startswith("$GNGGA"):
             msg = pynmea2.parse(_line)
             time = QTime(msg.timestamp.hour,msg.timestamp.minute,msg.timestamp.second,msg.timestamp.microsecond)
          
             hyu = datetime(year,month,day,msg.timestamp.hour,msg.timestamp.minute,msg.timestamp.second,msg.timestamp.microsecond)
      
             longitude       = msg.longitude
             latitude        = msg.latitude 
             altitude        = msg.altitude 
             vitesse         = -1
             string_date = hyu.strftime("%Y/%m/%dT%H:%M:%S")+'.'+str(int(int(msg.timestamp.microsecond)/10000))
             dateTime = QDateTime.fromString(string_date,"yyyy/MM/ddThh:mm:ss.z")
             #dateTime.setTimeSpec(Qt.UTC);
             #dateTime = dateTime.toLocalTime();
             flagOk = True
        if _file.endswith('.csv'):
             msg = _line;#[::5]
             
             A = str.split(msg,';')
             if A[0] =='drone':
                 continue
             #return 
         
            
      
             dateT           = A[1]
             longitude       = float(A[3])
             latitude        = float(A[2])  
             altitude        = float(A[4])
             
                 
             vitesse         = -1
             
             dateTime= QDateTime.fromString(dateT,"yyyyMMddhhmmss")
             if dateTimeOld==dateTime:
                 continue
             dateTimeOld = dateTime;
             dateTime = dateTime.addSecs(deltaTime)
             #dateTime.setTimeSpec(Qt.UTC)
             #dateTime = dateTime.toLocalTime();
             flagOk = True
             Cumul.append(( longitude, latitude, altitude))
                    
             pnt = folLoc.newpoint(name= Targetname, coords=[( longitude, latitude, altitude)])
             pnt.timestamp.when     = dateTime.toString('yyyy-MM-ddTHH:mm:ss.z')
             pnt.timestamp.begin    = dateTime.toString('yyyy-MM-ddTHH:mm:ss.z')
             pnt.altitudemode       =  simplekml.AltitudeMode.relativetoground
             pnt.style.iconstyle.scale = 3  # Icon thrice as big
             pnt.style.iconstyle.icon.href =   MyType.value.icone
             
         
        if _file.endswith('.LLH'):
         #print(_line)
         msg = _line;#[::5]
         A = str.split(msg)
         
         #return 
         
         if float(A[3])==0 and float(A[4])== 0 and float(A[2]) == 0:
             continue
        
         if float(A[7])+float(A[8])+float(A[9])>400:
        
             continue
         if count <5:
             count = count+1
             continue
         
         count = 0
         
         if offset == -1:
             offset = float(A[4])
             
         date            = A[0]
         time            = A[1]
         longitude       = A[3]
         latitude        = A[2]  
         altitude        = float(A[4]) - offset

             
         vitesse         = -1
         
         dateTime= QDateTime.fromString(date+'T'+time,"yyyy/MM/ddThh:mm:ss.z")
         #dateTime.setTimeSpec(Qt.UTC)
         #dateTime = dateTime.toLocalTime();
         flagOk = True
         
         Cumul.append(( longitude, latitude, altitude))
                    
         pnt = folLoc.newpoint(name= Targetname, coords=[( longitude, latitude, altitude)])
         pnt.timestamp.when     = dateTime.toString('yyyy-MM-ddTHH:mm:ss.z')
         pnt.timestamp.begin    = dateTime.toString('yyyy-MM-ddTHH:mm:ss.z')
         pnt.altitudemode       =  simplekml.AltitudeMode.relativetoground
         pnt.style.iconstyle.scale = 3  # Icon thrice as big
         
       
         pnt.style.iconstyle.icon.href =   MyType.value.icone
             
    lin = fol.newlinestring(name="target trajectory", description="trajectory of the target",coords=Cumul)
    lin.altitudemode = simplekml.AltitudeMode.relativetoground
    lin.extrude = 1
    lin.style.linestyle.color = simplekml.Color.rgb(10,240,125,150)# = 'cafc03ff'  # Red
    lin.style.linestyle.width= 10  # 10 pixels
    lin.style.polystyle.color = simplekml.Color.rgb(10,240,125,50)                                 
    
    kml.save(output) 
    
    #copie du repertoire icone dan sle répertoire kml 
 
    copy_tree("../icones_target", os.path.dirname(os.path.abspath(output))+"/icones_target")
    
         
def readSaveLLHFile(_file,_dataBase, Targetid, Targetname,TargetType,destroyGroundTrue,deltaTime=0):
    conn =   sqlite3.connect(_dataBase)
    count = 0;
    if destroyGroundTrue:
        
        Command ='DROP TABLE groundTrue_t'
        
        try:
             c = conn.cursor()
             c.execute(Command)
             conn.commit()
        except Error as e:
             print(e)
       
        Command = []
        Command.append("CREATE TABLE groundTrue_t ");
        Command.append("(id INTEGER PRIMARY KEY AUTOINCREMENT,");
        Command.append(" id_target VARCHAR,");
        Command.append(" name VARCHAR, ");
        Command.append(" type VARCHAR,");
        Command.append(" date  DATETIME,");
        Command.append(" isRandomVelocity INTEGER,");
        Command.append(" isSplinTrajectory INTEGER,");
        Command.append(" velocity  REAL,");
        Command.append(" latitude REAL,");
        Command.append(" longitude REAL,");
        Command.append(" altitude REAL");
        Command.append(");");
        Command = ''.join(Command) 

        try:
             c = conn.cursor()
             c.execute(Command)
             conn.commit()
        except Error as e:
             print(e)
        
    file1 = open(_file, 'r') 
    Lines = file1.readlines()
    offset = -1
    dateTimeOld = QDateTime()
    
 
    
    for _line in Lines:
        A = []
        flagOk = False
        MyDate = QDate
        
 
           
               

        if _file.endswith('.NMEA'):
            if _line.startswith("$GNRMC"):
                A = str.split(_line,',')
                _date = A[9]
        
                year = 2000+int(_date[4:6])
                month = int(_date[2:4])
                day = int(_date[0:2]) 
   
            if _line.startswith("$GNGGA"):
             msg = pynmea2.parse(_line)
             time = QTime(msg.timestamp.hour,msg.timestamp.minute,msg.timestamp.second,msg.timestamp.microsecond)
          
             hyu = datetime(year,month,day,msg.timestamp.hour,msg.timestamp.minute,msg.timestamp.second,msg.timestamp.microsecond)
      
             longitude       = msg.longitude
             latitude        = msg.latitude 
             altitude        = msg.altitude 
             vitesse         = -1
             string_date = hyu.strftime("%Y/%m/%dT%H:%M:%S")+'.'+str(int(int(msg.timestamp.microsecond)/10000))
             dateTime = QDateTime.fromString(string_date,"yyyy/MM/ddThh:mm:ss.z")
             dateTime = dateTime.addSecs(deltaTime)
           
             #dateTime.setTimeSpec(Qt.UTC);
             #dateTime = dateTime.toLocalTime();
             flagOk = True
        if _file.endswith('.csv'):
         msg = _line;#[::5]
         
         A = str.split(msg,';')
         if A[0] =='drone':
             continue
         #return 
     
         
         
         
  
         dateT           = A[1]
         longitude       = float(A[3])
         latitude        = float(A[2])  
         altitude        = float(A[4])
         
             
         vitesse         = -1
         
         dateTime= QDateTime.fromString(dateT,"yyyyMMddhhmmss")
         if dateTimeOld==dateTime:
             continue
         dateTimeOld = dateTime;
         dateTime = dateTime.addSecs(deltaTime)
         #dateTime.setTimeSpec(Qt.UTC)
         #dateTime = dateTime.toLocalTime();
         flagOk = True
         
            
        if _file.endswith('.LLH'):
         #print(_line)
         msg = _line;#[::5]
         A = str.split(msg)
         
         #return 
         
         if float(A[3])==0 and float(A[4])== 0 and float(A[2]) == 0:
             continue
         if float(A[7])+float(A[8])+float(A[9])>150:
        
             continue  
         if count <5:
             count = count+1
             continue
         
         count = 0
         
         if offset == -1:
             offset = float(A[4])
  
         date            = A[0]
         time            = A[1]
         longitude       = A[3]
         latitude        = A[2]  
         altitude        = float(A[4]) - offset

             
         vitesse         = -1
         
         dateTime= QDateTime.fromString(date+'T'+time,"yyyy/MM/ddThh:mm:ss.z")
         dateTime = dateTime.addSecs(deltaTime)
         dateTime.setTimeSpec(Qt.UTC)
         dateTime = dateTime.toLocalTime();
         flagOk = True
        if flagOk :

    
   
         
      
            Command = []
            Command.append("insert into groundTrue_t (");
            Command.append(" id_target, name, type,  date, latitude, longitude, altitude,velocity)");
            Command.append(" values (");
            Command.append(("'%s',")%(Targetid));
            Command.append(("'%s',")%(Targetname));
            Command.append(("'%s',")%(TargetType));
            Command.append(("'%s',")%(dateTime.toString("yyyy-MM-dd hh:mm:ss.zzz")));
            Command.append(("%s,")%(latitude));
            Command.append(("%s,")%(longitude));
            Command.append(("%f,")%(altitude));
            Command.append(("%s")%(vitesse));
            Command.append(")");
            Command = ''.join(Command)
          
            try:
                 c = conn.cursor()
                 c.execute(Command)
                 conn.commit()
            except Error as e:
                 print(e)
    return            
class Form(QWidget):
   def __init__(self, parent=None):
      super(Form, self).__init__(parent)
		
      layout = QVBoxLayout(self)
      self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok
                                      | QDialogButtonBox.Cancel)
      self.buttonBox.accepted.connect(self.accept)
      self.buttonBox.rejected.connect(self.reject)
      #Target Id
      layoutH11 = QHBoxLayout(self) 
      _id           = QLabel('target id')
      self.idTarget = QLineEdit() 
      layoutH11.addWidget(_id)
      layoutH11.addWidget(self.idTarget)
     
     
     
     
      #Target Name
      layoutH12 = QHBoxLayout(self)
      _name           = QLabel('target name')
      self.nameTarget = QLineEdit() 
      layoutH12.addWidget(_name)
      layoutH12.addWidget(self.nameTarget)
      
      #Target Type
      self.typeTarget = QComboBox() 

      for u in TARGET_TYPE:
            self.typeTarget.addItem("%s"% u.name)
      layoutH12.addWidget(self.typeTarget)
      #select database
	  #select LLH file
      layoutH1 = QHBoxLayout(self)
      self.LLHWidget = QLineEdit()
      self.LLHWidget.setReadOnly(True)
      pushButtonLLH =  QPushButton('...select location file') 
      pushButtonLLH.clicked.connect(self.getLLHFileName)
      layoutH1.addWidget(self.LLHWidget)
      layoutH1.addWidget(pushButtonLLH)
      self.destroyGroundTruth = QCheckBox()
      self.destroyGroundTruth .setText('clear data base')
      layoutH1.addWidget(self.destroyGroundTruth)
      TimeCorrectionLabel = QLabel("Time correction (in s):")
      self.TimeCorrectionWidget = QLineEdit()
      self.TimeCorrectionWidget.setText('0')
      layoutH4 = QHBoxLayout(self)
      layoutH4.addWidget(TimeCorrectionLabel)
      layoutH4.addWidget(self.TimeCorrectionWidget)
      layoutH2 = QHBoxLayout(self)
      self.DataBase = QLineEdit()
      self.DataBase.setReadOnly(True)
      pushButtonBase =  QPushButton('...select data base')
      pushButtonBase.clicked.connect(self.getDataBaseName)
      layoutH2.addWidget(self.DataBase)
      layoutH2.addWidget(pushButtonBase)
      
      layoutH3 = QHBoxLayout(self)
      self.KML = QLineEdit()
 
      pushButtonKML =  QPushButton('...save KML')
      pushButtonKML.clicked.connect(self.saveKML)
      layoutH3.addWidget(self.KML)
      layoutH3.addWidget(pushButtonKML)
      
      
      layout.addLayout(layoutH11)
      layout.addLayout(layoutH12)
      layout.addLayout(layoutH1)
      layout.addLayout(layoutH2)
      layout.addLayout(layoutH4)
      layout.addLayout(layoutH3)
      layout.addWidget(self.buttonBox)
      self.setWindowTitle("convert LLH file")
   def saveKML(self):
   
        output = QFileDialog.getSaveFileName(self, 'Save Kml File','*.kml')
        if output :
            _id         = self.idTarget.text()
            _name       = self.nameTarget.text()
            _type       = self.typeTarget.currentText()
           
            self.KML.setText(output[0])
        deltaTime = 0
        if not self.TimeCorrectionWidget.text()=='':
            deltaTime = float(self.TimeCorrectionWidget.text())
        readSaveKMLFile(self.LLHWidget.text(),output[0],_id,_name,_type,deltaTime)
   def getLLHFileName(self):
        fname = QFileDialog.getOpenFileName(self, 'select LLH or NMEA file', 
         '',"file (*.LLH *.NMEA *.csv)")
        if fname : 
            print(fname[0])
            self.LLHWidget.setText(fname[0])
   def getDataBaseName(self):
        fname = QFileDialog.getOpenFileName(self, 'select data base', 
         '',"data base (*.db)")
        if fname : 
            print(fname[0])
            self.DataBase.setText(fname[0])         
   def accept(self):

        _id         = self.idTarget.text()
        _name       = self.nameTarget.text()
        _type       = self.typeTarget.currentText()
        deltaTime = 0
        if not self.TimeCorrectionWidget.text()=='':
            deltaTime = float(self.TimeCorrectionWidget.text())
        readSaveLLHFile(self.LLHWidget.text(),self.DataBase.text(),_id,_name,_type,self.destroyGroundTruth.isChecked() ,deltaTime)
        
        self.close() 
        return
   def reject(self):
          print('reject')
          self.close()    
def main():
   app = QApplication(sys.argv)
   ex = Form()
   ex.show()
   sys.exit(app.exec_())
	
if __name__ == '__main__':
   main() 
 
readLLHFile('solution_202003051652.LLH')
     