# -*- coding: utf-8 -*-
"""
Created on Sat Jul 27 12:02:35 2019

@author: bpanneti
"""

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtOpenGL import *
from PyQt5.QtWidgets import *

import numpy as np

import sqlite3
import io
from sqlite3 import Error
import myTimer as _timer 

from point import REFERENCE_POINT
from Managers.dataManager import DataManager as dataManager
#from tool_tracking.track import Track
from tool_tracking.state import State
from target import TARGET_TYPE, RECORDED_TYPE
from mobileNode import MobileNode
from sensor     import Node
from tool_tracking.BiasProcessing.saver import icpTable as It, roadLmsTable as Rlt
import tool_tracking as tr

def adapt_array(arr):
    out = io.BytesIO()
    np.save(out, arr)
    out.seek(0)
    return sqlite3.Binary(out.read())

def convert_array(text):
    out = io.BytesIO(text)
    out.seek(0)
    return np.load(out)

sqlite3.register_adapter(np.ndarray, adapt_array)
sqlite3.register_converter("array", convert_array)

class saveData(QWidget):
     message         = pyqtSignal('QString')
     def __init__(self, parent=None):
        super(saveData, self).__init__()
        self.conn   = None
        self.connp  = None
 
        
     def saveData(self,_filename = None):
         
         if _filename==None:
             self.message.emit('no data base created!')
             return
         
         self.conn = self.create_connection(_filename)
         
         if self.conn ==None:
             return
            
         self.createTables()
 
     @staticmethod
     def executeRequest(conn, create_table_sql):
         """ create a table from the create_table_sql statement
         :param conn: Connection object
         :param create_table_sql: a CREATE TABLE statement
         :return:
             """
         try:
            c = conn.cursor()
            c.execute(create_table_sql)
            conn.commit()
         except Error as e:
            print(e)
             
     @staticmethod
     def executeManyRequests(conn, query_table_sql, value_rows):
         """ create a table from the create_table_sql statement
         :param conn: Connection object
         :param create_table_sql: a CREATE TABLE statement
         :param requests: a list of rows to put in the table
         :return:
             """
         #try:
         c = conn.cursor()
         #c.execute(create_table_sql)
         c.executemany(query_table_sql, value_rows)
         conn.commit()

         #except Error as e:
         #    print(e)

     def createNumpyTable(self, _filename):

         self.connp = sqlite3.connect(_filename, detect_types=sqlite3.PARSE_DECLTYPES)

         if self.connp ==None:
             return

         self.executeRequest(self.connp,'DROP TABLE array_t')
         Command = []
         Command.append('CREATE TABLE array_t (')
         Command.append('arr ARRAY')
         Command.append(')')
         Command = ''.join(Command)
         self.executeRequest(self.connp,Command)

     def saveNumpyTable(self, x):
        Command = "insert into array_t "
        Command += "(arr) values (?)"
        try:
            c = self.connp.cursor()
            c.execute(Command,(x,))
            self.connp.commit()
        except Error as e: 
            print(e)

     def closeNumpyTable(self):
         self.connp.close()
         self.connp = None

     def createTables(self):
         #------------------
         #table référence
         #------------------

         self.executeRequest(self.conn,'DROP TABLE referencePoint_t')
         
         Command = []
         Command.append('CREATE TABLE referencePoint_t (');
         Command.append('date STRING,');
         Command.append('  longitude REAL,');
         Command.append('  latitude  REAL,');
         Command.append(' altitude   REAL,');
         Command.append(' type VARCHAR');
         Command.append(');');
         Command = ''.join(Command)
    
         self.executeRequest(self.conn,Command)
         
         #------------------
         #table node
         #------------------
         self.executeRequest(self.conn,'DROP TABLE node_t')
         Command = []
         Command.append("CREATE TABLE node_t ");
         Command.append("(id INTEGER PRIMARY KEY AUTOINCREMENT,");
         Command.append(" id_node VARCHAR,");
         Command.append(" id_network VARCHAR,");
         Command.append(" m_nom  VARCHAR,");
         Command.append(" type_node  VARCHAR,");
         Command.append(" ressource  VARCHAR,");
         Command.append(" color INTEGER INTEGER[],");
         Command.append(" date  DATETIME,");
         Command.append(" id_sensors INTEGER INTEGER[],");
         Command.append(" latitude REAL,");
         Command.append(" longitude REAL,");
         Command.append(" altitude REAL,");
         Command.append(" yaw REAL,");
         Command.append(" pitch REAL,");
         Command.append(" roll REAL,");
         Command.append(" std_lat   REAL,");
         Command.append(" std_long   REAL,");
         Command.append(" cross_latlong REAL,");
         Command.append(" std_alt   REAL,");
         Command.append(" std_yaw   REAL,");
         Command.append(" std_pitch   REAL,");
         Command.append(" std_roll   REAL,");
         Command.append(" links VARCHAR VARCHAR[],");
         Command.append(" state VARCHAR");
         Command.append(")");
         Command = ''.join(Command)
    
         self.executeRequest(self.conn,Command)
         #------------------
         #table tracker
         #------------------
         self.executeRequest(self.conn,'DROP TABLE tracker_t')
         Command = []
         Command.append("CREATE TABLE tracker_t ");
         Command.append("(id INTEGER PRIMARY KEY AUTOINCREMENT,");
         Command.append(" id_tracker VARCHAR,");
         Command.append(" id_node VARCHAR, ");
         Command.append(" type VARCHAR,");
         Command.append(" name VARCHAR,");
         Command.append(" targets   VARCHAR VARCHAR[],");
         Command.append(" sensors VARCHAR VARCHAR[],");
         Command.append(" particlesNumber VARCHAR,");
         Command.append(" threshold VARCHAR");
         Command.append(")");
         Command = ''.join(Command)
         self.executeRequest(self.conn,Command)
         
         #------------------
         #table sensor
         #------------------
         self.executeRequest(self.conn,'DROP TABLE sensor_t')
         Command = []
         Command.append("CREATE TABLE sensor_t ");
         Command.append("(id INTEGER PRIMARY KEY AUTOINCREMENT,");
         Command.append(" id_sensor VARCHAR,");
         Command.append(" id_node VARCHAR, ");
         Command.append(" sensorType INTEGER,");
         Command.append(" timeOfSampling REAL,");
         Command.append(" sensorName VARCHAR,");
         Command.append(" date  DATETIME,");
         Command.append(" color   INTEGER INTEGER[],");
         Command.append(" ressource   VARCHAR,");
         Command.append(" state VARCHAR");
         Command.append(")");
         Command = ''.join(Command)
         self.executeRequest(self.conn,Command)
         #------------------
         #table parameter
         #------------------
         self.executeRequest(self.conn,'DROP TABLE parameters_t')
         Command = []
         Command.append("CREATE TABLE parameters_t ");
         Command.append("(id INTEGER PRIMARY KEY AUTOINCREMENT,");
         Command.append(" id_sensor varchar,");
         Command.append(" date  DATETIME,");
         Command.append(" coverageType  INTEGER,");
         Command.append(" classType    varchar,");
         Command.append(" Component_1  REAL,");
         Command.append(" Component_2   REAL,");
         Command.append(" Component_3   REAL,");
         Command.append(" Component_4   REAL,");
         Command.append(" FaProbability  REAL,");
         Command.append(" DetectionProbability REAL,");
         Command.append(" sigma_rho     REAL,");
         Command.append(" sigma_theta   REAL,");
         Command.append(" sigma_phi     REAL ");
         Command.append(");");
         Command = ''.join(Command)
         self.executeRequest(self.conn,Command)

         #---------------------
         #table bias corrector
         #---------------------

         It.IcpTable.createTable(self.conn)
         Rlt.RoadLmsTable.createTables(self.conn)

         #------------------
         #table bias
         #------------------
         self.executeRequest(self.conn,'DROP TABLE bias_t')
         Command = []
         Command.append("CREATE TABLE bias_t ");
         Command.append("(id INTEGER PRIMARY KEY AUTOINCREMENT,");
         Command.append(" id_sensor     VARCHAR,");
         Command.append(" yaw         REAL,");
         Command.append(" x_ENU       REAL,");
         Command.append(" y_ENU       REAL ");
         Command.append(");");
         Command = ''.join(Command)
         self.executeRequest(self.conn,Command)
         #------------------
         #table ground true
         #------------------         
         self.executeRequest(self.conn,'DROP TABLE groundTrue_t')
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

         self.executeRequest(self.conn,Command)
         #------------------
         #table class
         #----------------
         self.executeRequest(self.conn,'DROP TABLE class_t')
         Command = []
         Command.append("CREATE TABLE class_t ");
         Command.append("( id       INTEGER PRIMARY KEY AUTOINCREMENT ,");
         Command.append("class VARCHAR)");
         Command = ''.join(Command)

         self.executeRequest(self.conn,Command)
         
         #------------------
         #table plots
         #-----------------
         self.executeRequest(self.conn,'DROP TABLE plot_t')
         Command = []
         Command.append("CREATE TABLE plot_t ");
         Command.append("( id       INTEGER PRIMARY KEY AUTOINCREMENT ,");
         Command.append("id_Plot    LONG LONG,");
         Command.append("id_Sensor  VARCHAR,");
         Command.append("id_Scan       LONG LONG,");
         Command.append("date       STRING,");
         Command.append("receptionDate      STRING,");
         Command.append("locationFormat     ENUM,");
         Command.append("locComposant_1  REAL,     ");
         Command.append("LocComposant_2 REAL,");
         Command.append("locComposant_3 REAL,");
         Command.append("locSTDType_1  REAL,");
         Command.append("locSTDType_2 REAL,");
         Command.append("locSTDType_3 REAL,");
         Command.append("velocityFormat     ENUM,");
         Command.append("velocityComposant_1  REAL,");
         Command.append("velocityComposant_2 REAL,");
         Command.append("velocityComposant_3 REAL,");
         Command.append("velocitySTDType_1  REAL,");
         Command.append("velocitySTDType_2 REAL,");
         Command.append("velocitySTDType_3 REAL,");
         Command.append("Pfa  REAL,     ");
         Command.append("Pd  REAL,     ");
         Command.append("classe STRING,");
         Command.append("likelyhood_classe   STRING,");
         Command.append("url STRING,");
         Command.append("dataType_1 STRING,");
         Command.append("data_1 STRING,");
         Command.append("dataType_2 STRING,");
         Command.append("data_2 STRING)");
         Command = ''.join(Command)

         self.executeRequest(self.conn,Command)
         #------------------
         #table track
         #------------------
         self.executeRequest(self.conn,'DROP TABLE track_t')
         Command  = []
         Command.append("CREATE TABLE track_t ");
         Command.append("(id INTEGER PRIMARY KEY AUTOINCREMENT,");
         Command.append(" id_node VARCHAR,");
         Command.append(" id_track INTEGER,");
         Command.append(" date_creation DATETIME,");
         Command.append(" date_end   DATETIME,");
         Command.append(" last_states INTEGER  INTEGER[],");
         Command.append(" statut     VARCHAR, ");
         Command.append(" classe     VARCHAR,");
         Command.append(" probability_classe VARCHAR,");
         Command.append(" additionalInfo_1 VARCHAR,");
         Command.append(" additionalValue_1 REAL");
         Command.append(");");
         Command = ''.join(Command)
         self.executeRequest(self.conn,Command)
         #------------------
         #table state
         #------------------
         self.executeRequest(self.conn,'DROP TABLE state_t')
         Command  = []
         Command.append("CREATE TABLE state_t ");
         Command.append("(id INTEGER PRIMARY KEY AUTOINCREMENT,");
         Command.append(" id_state INTEGER,");
         Command.append(" id_track INTEGER,");
         Command.append(" id_parent INTEGER,");
         Command.append(" id_node VARCHAR,");
         Command.append(" date DATETIME,");
         Command.append(" format VARCHAR,");
         Command.append(" estimated_state   REAL[4],");
         Command.append(" estimated_covariance  REAL[4][4],");
         Command.append(" longitude   REAL,");
         Command.append(" latitude   REAL,");
         Command.append(" altitude   REAL,");
         Command.append(" statut     VARCHAR, ");
         Command.append(" id_plots   VARCHAR,");
         Command.append(" classe     VARCHAR,");
         Command.append(" probabilite_classe VARCHAR,");
         Command.append(" additionalInfo_1 VARCHAR,");
         Command.append(" additionalValue_1 REAL,");
         Command.append(" additionalInfo_2 VARCHAR,");
         Command.append(" additionalValue_2 REAL,");
         Command.append(" additionalInfo_3 VARCHAR,");
         Command.append(" additionalValue_3 REAL");
         Command.append(");");
         Command = ''.join(Command)
         self.executeRequest(self.conn,Command)
         
         #------------------
         #GIS datae
         #------------------
         self.executeRequest(self.conn,'DROP TABLE gis_t')
         Command  = []
         Command.append("CREATE TABLE gis_t ");
         Command.append(" (nature VARCHAR,");
         Command.append(" path VARCHAR);");
         Command = ''.join(Command)
         self.executeRequest(self.conn,Command)
    
     def create_connection(self, db_file):

        try:
            self.message.emit("try connection")
            conn = sqlite3.connect(db_file)
            self.message.emit("dataBase opened")
            return conn
        except Error as e:
            self.message.emit(e)
        return None    
     def saveReference(self,latitide,longitude,altitude,_time):
         
        Command = []
        Command.append("insert into referencePoint_t ");
        Command.append(" (date,longitude, latitude, altitude, type) values(");
        Command.append(("'%s',")%( _time.toString("yyyy-MM-dd hh:mm:ss.zzz")));
        Command.append(("%s,")%(longitude));
        Command.append(("%s,")%(latitide ));
        Command.append(("%s,")%(altitude ));
        Command.append(("'WGS84'"));
        Command.append(");");
        Command = ''.join(Command)
 
        self.executeRequest(self.conn,Command)

        print('reference point saved')    
         
     def saveReferencePoint(self):
        REFERENCE_TIME =_timer.getReferenceTime()  

        if REFERENCE_POINT.longitude ==[]  or REFERENCE_POINT.latitude==[] or REFERENCE_TIME == None:
            return

        Command = []
        Command.append("insert into referencePoint_t ");
        Command.append(" (date,longitude, latitude, altitude, type) values(");
        Command.append(("'%s',")%( REFERENCE_TIME.toString("yyyy-MM-dd hh:mm:ss.zzz")));
        Command.append(("%s,")%(REFERENCE_POINT.longitude ));
        Command.append(("%s,")%(REFERENCE_POINT.latitude ));
        Command.append(("%s,")%(REFERENCE_POINT.altitude ));
        Command.append(("'WGS84'"));
        Command.append(");");
        Command = ''.join(Command)
 
        self.executeRequest(self.conn,Command)

        print('reference point saved')
     def saveGIS(self,_gis):
        #routes
        if _gis.road:
            Command = []
            Command.append("insert into gis_t ");
            Command.append(" (nature,path) values(");
            Command.append("'roads',");
            Command.append(("'%s');")%(_gis.road.file));
            Command = ''.join(Command)
            self.executeRequest(self.conn,Command)
            print('road saved')
        #buildings
        if _gis.building:
            Command = []
            Command.append("insert into gis_t ");
            Command.append(" (nature,path) values(");
            Command.append("'buildings',");
            Command.append(("'%s');")%(_gis.building.file));
            Command = ''.join(Command)
            self.executeRequest(self.conn,Command)
            print('building saved')
        #vegetation
        if _gis.vegetation:
            Command = []
            Command.append("insert into gis_t ");
            Command.append(" (nature,path) values(");
            Command.append("'vegetation'',");
            Command.append(("'%s');")%(_gis.vegetation.file));
            Command = ''.join(Command)
            self.executeRequest(self.conn,Command)
            print('vegetation saved')
        #water
        if _gis.water:
            Command = []
            Command.append("insert into gis_t ");
            Command.append(" (nature,path) values(");
            Command.append("'water',");
            Command.append(("'%s');")%(_gis.water.file));
            Command = ''.join(Command)
            self.executeRequest(self.conn,Command)
            print('water saved')
        #waterArea
        if _gis.waterArea:
            Command = []
            Command.append("insert into gis_t ");
            Command.append(" (nature,path) values(");
            Command.append("'waterArea',");
            Command.append(("'%s');")%(_gis.waterArea.file));
            Command = ''.join(Command)
            self.executeRequest(self.conn,Command)
            print('waterArea saved')
        #images
        if _gis.maps:
            Command = []
            Command.append("insert into gis_t ");
            Command.append(" (nature,path) values(");
            Command.append("'image',");
            Command.append("'{");
            for _im in _gis.maps:
                Command.append(("%s,")%(_im.nom))
            if  len(_gis.maps)>=1:
                     Command = Command[:-2]
                     Command.append(("%s")%(_im.nom))
            Command.append("}');");
            Command = ''.join(Command)
            self.executeRequest(self.conn,Command)
            print('images saved')
        #dted
        if _gis.dtedList:
            Command = []
            Command.append("insert into gis_t ");
            Command.append(" (nature,path) values(");
            Command.append("'dted',");
            Command.append("'{");
            for _dted in _gis.dtedList:
                Command.append(("%s,")%(_dted.nom))
            if  len(_gis.dtedList)>=1:
                     Command = Command[:-2]
                     Command.append(("%s")%(_dted.nom))
            Command.append("}');");
            Command = ''.join(Command)
            self.executeRequest(self.conn,Command)
            print('dted saved')
        if _gis.x0!=None and _gis.y0!=None and _gis.y1!=None and _gis.x1!=None:
            Command = []
            Command.append("insert into gis_t ");
            Command.append(" (nature,path) values(");
            Command.append("'area',");
            Command.append("'{");
            Command.append(("%s,")%( _gis.x0))
            Command.append(("%s,")%( _gis.y0))
            Command.append(("%s,")%( _gis.x1))
            Command.append(("%s")%( _gis.y1))
            Command.append("}');");
            Command = ''.join(Command)
            self.executeRequest(self.conn,Command)
            print('area saved')
        print('gis saved')
     def saveClass(self):
        for type_t in TARGET_TYPE: 
            Command = []
            Command.append("insert into class_t (class) values (");
            Command.append(("'%s'")%(type_t.name))
            Command.append(");");
            Command = ''.join(Command)
            self.executeRequest(self.conn,Command)
        
     def saveParameters(self,_parameters =[]):
         if _parameters==None:
             return
         if len(_parameters)<=0 :
             return
         
         REFERENCE_TIME = _timer.getReferenceTime() 

         Command = ["insert into  parameters_t (id_sensor, date,coverageType,classType, Component_1,Component_2,Component_3,Component_4,FaProbability,DetectionProbability,sigma_rho,sigma_theta,sigma_phi)"]
         Command.append(" values (?,?,?,?,?,?,?,?,?,?,?,?,?);")
         Command = "".join(Command)
         
         Rows = []
         for _parameter in _parameters:
                row = []
                row.append(("%s")%(_parameter.id_Sensor));
                row.append(("%s")%(REFERENCE_TIME.toString("yyyy-MM-dd hh:mm:ss.zzz")));
                row.append(("%d")%(_parameter.type.value ));
                row.append(("%s")%(_parameter.name.name));
                row.append(("%s")%(_parameter.distanceMin));
                row.append(("%s")%(_parameter.distanceMax));
                row.append(("%s")%(_parameter.fov));
                row.append(("%s")%(_parameter.fov_elevation));
                row.append(("%s")%(_parameter.parameters.pfa));
                row.append(("%s")%(_parameter.parameters.pd));
                row.append(("%s")%(_parameter.parameters.sigmaRho));
                row.append(("%s")%(_parameter.parameters.sigmaTheta));
                row.append(("%s")%(_parameter.parameters.sigmaPhi));
                Rows.append(row)
   
         self.executeManyRequests(self.conn,Command,Rows)
         print('parameter saved')

     def saveBias(self, bias):
         if bias == None :
             return
         
         Command = []
         Command.append("insert into bias_t (id_sensor, yaw, x_ENU, y_ENU)")
         Command.append(" values (" )
         Command.append(("'%s',")%(bias.id))
         Command.append(("'%s',")%(bias.orientation.yaw))
         Command.append(("'%s',")%(bias.position.x_ENU))
         Command.append(("'%s'")%(bias.position.y_ENU))
         Command.append(");")
         Command = ''.join(Command)

         self.executeRequest(self.conn,Command)
         print('Bias saved')

     def saveTrackers(self,_tracker  ):
 
         if _tracker==None :
             return
 
         REFERENCE_TIME = _timer.getReferenceTime() 
         Command = []
         Command.append("insert into  tracker_t (id_tracker, id_node, type, name, targets, sensors, particlesNumber, threshold)");
         Command.append(" values (" );
         Command.append(("'%s',")%(_tracker.id));
         Command.append(("'%s',")%(_tracker.id_node));
         Command.append(("'%s',")%(_tracker.filter.name));
         Command.append(("'%s',")%(_tracker.name));
         Command.append("'{");
         
 
                
                
         if _tracker.tracker!=None:
             for _target in _tracker.tracker.targets :
                 Command.append(("%s,")%(str(_target)))
   
             if  len(_tracker.tracker.targets)>=1:
                 Command = Command[:-1]
                 Command.append(("%s")%(str(_target)))
                 
         Command.append("}',"); 
         Command.append("'{");
    
         if _tracker.sensors!=[]:
             for _sensor in _tracker.sensors  :
     
                 Command.append(("%s,")%(str(_sensor.id)))
             if  len(_tracker.sensors)>0:
                 Command = Command[:-1]
                 Command.append(("%s")%(str(_sensor.id)))
         Command.append("}' ");
#
#         if isinstance(_tracker.trackerInfos, tr.sir.Infos):
#            Command.append(",'{}',".format(_tracker.trackerInfos.samplesNumber))
#            Command.append("'{}'".format(_tracker.trackerInfos.threshold))
#         else :
         Command.append(",-1,")
         Command.append("-1") 
            
         Command.append(");");   
         Command = ''.join(Command)
 
         self.executeRequest(self.conn,Command)
 
             
     def saveSensors(self, _sensors = []):
         
         if len(_sensors)<=0 :
             return
         
         REFERENCE_TIME = _timer.getReferenceTime() 
         for _sensor in _sensors:
             Command = []
             Command.append("insert into  sensor_t (id_sensor, id_node, sensorType, timeOfSampling, sensorName, date, color, ressource, state)");
             Command.append(" values (" );
             Command.append(("'%s',")%(_sensor.id));
             Command.append(("'%s',")%(_sensor.id_node));
             Command.append(("'%s',")%(_sensor.mode.name));
             Command.append(("'%s',")%(_sensor.timeOfSampling));
             Command.append(("'%s',")%(_sensor.name));
             Command.append(("'%s',")%(REFERENCE_TIME.toString("yyyy-MM-dd hh:mm:ss.zzz")));
             Command.append(("'{%d,%d,%d}',")%(_sensor.color.red(),_sensor.color.green(),_sensor.color.blue()));
             Command.append(("'none',"));
             Command.append(("'ALIVE'"));
             Command.append(");");   
             Command = ''.join(Command)
             self.executeRequest(self.conn,Command)

             self.saveParameters(_sensor.sensorCoverage)
             self.saveBias(_sensor.bias)
             
     def saveStates(self, _state,_idTrack,_idNode ): 
  
             _state.stateSavedInDb = True
             Command = []
             Command.append("insert into state_t ");
             Command.append(" (id_state, id_track, id_parent, id_node, date, format, estimated_state, estimated_covariance,longitude,latitude,altitude , statut, id_plots, classe, probabilite_classe,additionalInfo_1,additionalValue_1,additionalInfo_2,additionalValue_2,additionalInfo_3,additionalValue_3) values(");
             Command.append(("%s,")%(_state.id))
             Command.append(("%s,")%(_idTrack)) 
             Command.append(("%s,")%(_state.idPere)) 
             Command.append(("'%s',")%(_idNode)) 
             Command.append(("'%s',")%(_state.time.toString("yyyy-MM-dd hh:mm:ss.zzz")));
             Command.append("'ECEF',")
             Command.append("'{");
             x = _state.getStateECEF()
             for  i in range(6):
                  Command.append(("%s,")%(x[i][0]));
             Command = Command[:-1]
             Command.append(("%s")%(x[i][0]))
             Command.append( "}',");
             Command.append( "'{");
             P = _state.getCovarianceECEF()
             for  i in range(6):
                 Command.append( "{");
                 for j in range(6):
                        Command.append(("%s,")%(P[i,j]));
                 Command = Command[:-1]
                 Command.append(("%s")%(P[i,j]));
                 Command.append( "},");
             Command = Command[:-1]
             Command.append( "}");
             Command.append( "}',");
             pos = _state.location
             Command.append(("%s,")%(pos.longitude));
             Command.append(("%s,")%(pos.latitude));
             Command.append(("%s,")%(pos.altitude));
             Command.append("'");
             Command.append("CONFIRMED");
             Command.append("',");
             Command.append("'{");
             Command.append("}',");
             Command.append(("'%s',")%_state.classe.name);
             Command.append( ("'{"));
             _values = _state.getClassProbabilities()
             for  i in range(len(_values)):
                    Command.append( ("%s,")%(_values[i]));
             Command = Command[:-1]
             Command.append( "}',");
             if len(_state.addtionnalInfo)  >=1:
                  Command.append( ("'%s',%s,")%(_state.addtionnalInfo[0][0],_state.addtionnalInfo[0][1]));
             else:
                 Command.append( "' ', ,");
             if len(_state.addtionnalInfo)  >=2:
                  Command.append( ("'%s',%s,")%(_state.addtionnalInfo[1][0],_state.addtionnalInfo[1][1]));
             else:
                 Command.append( "' ', ,");
             if len(_state.addtionnalInfo)  >=3:
                  Command.append( ("'%s',%s")%(_state.addtionnalInfo[2][0],_state.addtionnalInfo[2][1]));
             else:
                 Command.append( "' ', ");
                 
             Command.append(");");
             Command = ''.join(Command)

             
             self.executeRequest(self.conn,Command)
        
     def saveAllTracks(self,_tracks = []): 
   
          
             progress = QProgressDialog("save tracks...", "Abort save", 0, len(_tracks), self)
             progress.setWindowModality(Qt.WindowModal) 
             i = 0

             for _track  in _tracks:
                 progress.setValue(i)
                 if progress.wasCanceled():
                     break
                 i+=1
 
                  
                 currentStates  = []
                 _track.tree.getChilds(currentStates)
                 _cState = currentStates[0]
                 first = True
                 while _cState != None:
                     Command  = []
                     self.saveStates(_cState.data,_track.id,_track.id_node)
                     if first==True:
                         Command.append("insert into track_t");
                         Command.append(" (id_node,id_track, date_creation, date_end, last_states,  statut, classe, probability_classe,additionalInfo_1,additionalValue_1) values(");
                         Command.append(("'%s',")%(_track.id_node));
                         Command.append( ("%s,")%(_track.id));
                         Command.append( ("'%s',")%(_track.tree.data.time.toString("yyyy-MM-dd hh:mm:ss.zzz")));
                         Command.append( ("'%s',")%(_cState.data.time.toString("yyyy-MM-dd hh:mm:ss.zzz")));
                         Command.append( " '{");
                         Command.append(("%s}',")%( _cState.data.id ));
                         Command.append("'CONFIRMED',");
                         Command.append("'UNKNOWN',");
                         Command.append("1.0,");
                         if len(_track.addtionnalInfo)  ==1:
                             Command.append( ("'%s',%s")%(_track.addtionnalInfo[0][0],_track.addtionnalInfo[0][1]));
                         else:
                            Command.append( "' ', ");
                            
                         
                         Command.append(");");
                         first = False
          
                     else:
                         Command.append("UPDATE track_t ");
                         Command.append("SET  last_states=");
                         Command.append( " '{");
                         Command.append(("%s")%( _cState.data.id ))
                         Command.append("}',");
                         Command.append("date_end=");
                         Command.append( ("'%s' ")%(_cState.data.time.toString("yyyy-MM-dd hh:mm:ss.zzz")))
                         Command.append((" WHERE id_track = %s;")%(_track.id));
                         
                     _cState = _track.getState(_cState.data.idPere)
                     
                     Command = ''.join(Command)
             
                     self.executeRequest(self.conn,Command)
                   
             progress.setValue(len(_tracks))
             self.conn.commit()              
     def saveTracks(self,_tracks = []): 
   
         _tracker = None
            
         if _tracks == []:
                return
         
         for _node in dataManager.instance().nodes():
                if _node.id == _tracks[0].id_node:
                   _tracker = _node.tracker    
     
         if _tracker and _tracker.mutex.tryLock() :  
      

             for _track  in _tracker.tracker.getTracks():
  
                 self.conn.row_factory = sqlite3.Row
                 cur = self.conn.cursor()
                 c = cur.execute(("SELECT id_track FROM track_t where id_track = %s;")%(_track.id))
                 data = c.fetchall()
                
              
                 currentStates  = []
                 _track.tree.getChilds(currentStates)
                 Command = []
                 if len(data)==0:
                     Command.append("insert into track_t");
                     Command.append(" (id_node,id_track, date_creation, date_end, last_states,  statut, classe, probability_classe) values(");
                     Command.append(("'%s',")%(_track.id_node));
                     Command.append( ("%s,")%(_track.id));
                     Command.append( ("'%s',")%(_track.tree.data.time.toString("yyyy-MM-dd hh:mm:ss.zzz")));
                     Command.append( ("'%s',")%(currentStates[0].data.time.toString("yyyy-MM-dd hh:mm:ss.zzz")));
                     Command.append( " '{");
                     for _cState in currentStates: 
                         
                         Command.append(("%s,")%( _cState.data.id ));
                         if _cState.data.stateSavedInDb == False: 
                             self.saveStates(_cState.data,_track.id,_track.id_node)
                     if  len(currentStates)>0:
                         Command = Command[:-1]
                         Command.append(("%s")%( _cState.data.id ));
            
                     Command.append("}',");
                     Command.append("'CONFIRMED',");
                     Command.append("'UNKNOWN',");
                     Command.append("1.0");
                     Command.append(");");
      
                 else:
                     Command.append("UPDATE track_t ");
                     Command.append("SET  last_states=");
                     Command.append( " '{");
                     for _cState in currentStates: 
                         Command.append( '{0}'.format(_cState.data.id));
                         if _cState.data.stateSavedInDb == False: 
                             self.saveStates(_cState.data,_track.id,_track.id_node)
                     if  len(currentStates)>0:
                         Command = Command[:-1]
                         Command.append(("%s")%( _cState.data.id ))
                     Command.append("}',");
                     Command.append("date_end=");
                     Command.append( ("'%s' ")%(currentStates[0].data.time.toString("yyyy-MM-dd hh:mm:ss.zzz")))
                     Command.append((" WHERE id_track = %s;")%(_track.id));
                     
                     
                 Command = ''.join(Command)
   
                 self.executeRequest(self.conn,Command)
             _tracker.mutex.unlock()
         self.conn.commit()
         
       
     def saveTargets(self ):
         for _target in dataManager.instance().targets():
             if _target.isValid()==False:
                 continue
 
             Command = []
             Command.append("insert into groundTrue_t (");
             Command.append(" id_target, name, type,  date, isRandomVelocity, isSplinTrajectory, latitude, longitude, altitude,velocity)");
             Command.append(" values (?,?,?,?,?,?,?,?,?,?);");
             Command = ''.join(Command)
             
             ValueRows = []

             for i in range(0,len(_target.trajectoryWayPoints)):
                 
                 row = []
                 row.append(('%s')%(_target.id));
                 row.append(('%s')%(_target.name));
                 row.append(('%s')%(_target.type.name));
                 row.append(('%s')%(_target.timeToWayPoints[i].toString("yyyy-MM-dd hh:mm:ss.zzz")));
                 row.append(('%s')%(int(_target.isRandomVelocity)));
                 row.append(('%s')%(int(_target.isSplinTrajectory)));
                 row.append(('%s')%(_target.trajectoryWayPoints[i].latitude));
                 row.append(('%s')%(_target.trajectoryWayPoints[i].longitude));
                 row.append(('%s')%(_target.altitude));
                 
                  
                 if _target.velocityToWayPoints and _target.recordedType  != RECORDED_TYPE.BASE_ON_WAYPOINTS:
                     row.append(("%s")%(float(_target.velocityToWayPoints[i])));
                 else:
                     row.append(("%s")%("-1"));#float(_target.velocityToWayPoints[i])));
                 #row.append("");
                 #row = ''.join(row)
    
                 ValueRows.append(row)
     
             self.executeManyRequests(self.conn,Command,ValueRows)

             print('target saved')

     def saveBiasCorretors(self, biasCorrector):
         if biasCorrector == None:
             return

         biasCorrector.save(self.executeRequest, self.conn)
     def saveAllNodes(self,_nodes=[]):
         for _node in _nodes:
            Command = []
            Command.append("insert into  node_t "
                      "(id_node,"
                      "id_network, "
                      "m_nom,"
                      "type_node,"
                      "ressource,"
                      "color,"
                      "date, "
                      "id_sensors, "
                      "latitude, "
                      "longitude, "
                      "altitude, "
                      "yaw, "
                      "pitch, "
                      "roll, "
                      "std_lat, "
                      "std_long, "
                      "cross_latlong, "
                      "std_alt, "
                      "std_yaw,"
                      "std_pitch , "
                      "std_roll, "
                      " links,"
                      "state)");

  
            Command.append(" values (" );
            Command.append("'"+_node.id+"',");
            Command.append("'none',");
            Command.append("'"+_node.name+"',");
            if type(_node) == MobileNode:
                Command.append("'"+_node.typeNode.name+"',");
            else:
                Command.append("'"+_node.typeNode+"',");
   
            Command.append("'none',");
            Command.append(("'{%d,%d,%d}',")%(_node.color.red(),_node.color.green(),_node.color.blue()));
            Command.append(("'%s',")%(_node.date.toString("yyyy-MM-dd hh:mm:ss.zzz")));
            Command.append("'{");
  
            for _sensor in _node.sensors:
                Command.append(("%s,")%(_sensor.id ));
            if len(_node.sensors)>=1:
        
                Command = Command[:-1]
            
            if type(_node) == MobileNode :
                flag, position,VelocityTime = _node.positionAtTime(_currentTime)
                orientation     = _node.orientationAtTime(_currentTime)
            
            elif type(_node) == Node:
                position        = _node.Position 
                orientation     = _node.Orientation
            
            Command.append("}',");
            Command.append(("{0},").format(position.latitude));
            Command.append(("{0},").format(position.longitude));
            Command.append(("{0},").format(position.altitude));

            Command.append(("{0},").format(orientation.yaw));
            Command.append(("{0},").format(orientation.pitch));
            Command.append(("{0},").format(orientation.roll));

            Command.append(("0,"))
            Command.append(("0,"))
            Command.append(("0,"))
            Command.append(("0,"))

            Command.append(("0,"))
            Command.append(("0,"))
            Command.append(("0,"))


            Command.append("'{");
            Command.append("}',");
            Command.append(("'ALIVE'"));
            Command.append(");");
            Command = ''.join(Command)
            self.executeRequest(self.conn,Command)
         
 
      
                    
            self.saveSensors(_node.sensors)
 
            self.saveTrackers(_node.tracker)

          

            self.saveBiasCorretors(_node.biasCorrector)
         
     def saveNodes(self,_currentTime = QDateTime()):
         REFERENCE_TIME = _timer.getReferenceTime()
         for _node in dataManager.instance().nodes():
            Command = []
            Command.append("insert into  node_t "
                      "(id_node,"
                      "id_network, "
                      "m_nom,"
                      "type_node,"
                      "ressource,"
                      "color,"
                      "date, "
                      "id_sensors, "
                      "latitude, "
                      "longitude, "
                      "altitude, "
                      "yaw, "
                      "pitch, "
                      "roll, "
                      "std_lat, "
                      "std_long, "
                      "cross_latlong, "
                      "std_alt, "
                      "std_yaw,"
                      "std_pitch , "
                      "std_roll, "
                      " links,"
                      "state)");

  
            Command.append(" values (" );
            Command.append("'"+_node.id+"',");
            Command.append("'none',");
            Command.append("'"+_node.name+"',");
            if type(_node) == MobileNode:
                Command.append("'"+_node.typeNode.name+"',");
            else:
                Command.append("'"+_node.typeNode+"',");
   
            Command.append("'none',");
            Command.append(("'{%d,%d,%d}',")%(_node.color.red(),_node.color.green(),_node.color.blue()));
            Command.append(("'%s',")%(REFERENCE_TIME.toString("yyyy-MM-dd hh:mm:ss.zzz")));
            Command.append("'{");
  
            for _sensor in _node.sensors:
                Command.append(("%s,")%(_sensor.id ));
            if len(_node.sensors)>=1:
        
                Command = Command[:-1]
            
            if type(_node) == MobileNode :
                flag, position,VelocityTime = _node.positionAtTime(_currentTime)
                orientation     = _node.orientationAtTime(_currentTime)
            
            elif type(_node) == Node:
                position        = _node.Position 
                orientation     = _node.Orientation
            
            Command.append("}',");
            Command.append(("{0},").format(position.latitude));
            Command.append(("{0},").format(position.longitude));
            Command.append(("{0},").format(position.altitude));

            Command.append(("{0},").format(orientation.yaw));
            Command.append(("{0},").format(orientation.pitch));
            Command.append(("{0},").format(orientation.roll));

            Command.append(("0,"))
            Command.append(("0,"))
            Command.append(("0,"))
            Command.append(("0,"))

            Command.append(("0,"))
            Command.append(("0,"))
            Command.append(("0,"))


            Command.append("'{");
            Command.append("}',");
            Command.append(("'ALIVE'"));
            Command.append(");");
            Command = ''.join(Command)
            self.executeRequest(self.conn,Command)
         
 
      
                    
            self.saveSensors(_node.sensors)
 
            self.saveTrackers(_node.tracker)

          

            self.saveBiasCorretors(_node.biasCorrector)