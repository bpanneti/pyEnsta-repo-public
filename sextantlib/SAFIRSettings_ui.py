# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'SAFIRsettings.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!
import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtOpenGL import *
from PyQt5.QtWidgets import *
import json as readJson
from tool_tracking.state import State as localState
#import ntplib Package installé.
import socket   
import threading
from Managers.dataManager import DataManager as dataManager
#from sensor import  Sensor, SensorMode, Scan
import time
#from sensor import Sensor, Node,SensorMode
ADRESS_IP ='192.168.100.24' #
TCP_IP    = ADRESS_IP #'192.168.1.1'#ADRESS_IP.encode('utf-8')#'10.10.11.220'.encode('utf-8')#'localhost' 
#'127.0.0.1'.encode('utf-8')
TCP_PORT = 16810
BUFFER_SIZE = 1024 
'''
class Ui_Connection(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(400, 300)
        icon = QIcon()
        icon.addPixmap(QPixmap("icones/settings.png"), QIcon.Normal, QIcon.Off)
        Dialog.setWindowIcon(icon)
        self.verticalLayout = QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QLabel(Dialog)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.lineEditIP = QLineEdit(Dialog)
        self.lineEditIP.setObjectName("lineEditIP")
        self.horizontalLayout.addWidget(self.lineEditIP)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_2 = QLabel(Dialog)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_2.addWidget(self.label_2)
        self.lineEditPort = QLineEdit(Dialog)
        self.lineEditPort.setObjectName("lineEditPort")
        self.horizontalLayout_2.addWidget(self.lineEditPort)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)
        self.lineEditIP.setText(str(ADRESS_IP))
        self.lineEditPort.setText(str(TCP_PORT))
        self.retranslateUi(Dialog)

        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)
        QMetaObject.connectSlotsByName(Dialog)
        print('yo')
  
    def retranslateUi(self, Dialog):
        _translate = QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "server settings"))
        self.label.setText(_translate("Dialog", "server addres"))
        self.label_2.setText(_translate("Dialog", "port"))

'''
       
class server(QObject):
              
    #Messagerie
    message = pyqtSignal('QString');
    finished = pyqtSignal()
    chatMessage = pyqtSignal('QString');
    def __init__(self):
        super(server, self).__init__()
        #self.ui                 = Ui_Connection()
        self.socket             = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  
        self.platforms          = []
        self.commande           = str("")
        self.connected          = False
        self.clients            = []
        self.buffer             = ""
        self.onlyJson           = False
        self.mutex              = QMutex()
    def receiveNodes(self ):
        body = str("")
        if self.onlyJson == True:
            for _node in dataManager.instance().nodes():
      
                body = '<HTTP_JSON>'
                body = body + _node.toJson( ADRESS_IP)
                body+='</HTTP_JSON>'
                body+='\n'
                self.message.emit("send node parameters")
                self.send(body);
                time.sleep(0.5)
          
            body = str("")
          
            for _sensor in dataManager.instance().sensors():
                body = '<HTTP_JSON>'
                body += _sensor.toJson()
                body+='</HTTP_JSON>'
                body+='\n'
          
                self.message.emit("send sensor parameters")
                self.send(body);
         
                time.sleep(0.5)
            body = str("")
    def receiveScan(self,_scan  = None):
        #print('in receive Scan from SEXTANT')
        json = _scan.toJson()
       
        return
        if json!='':
            self.sendJsonMessage(json)
    def receiveStates(self,_stats=[]):
        if _stats ==[]:
            return
        c=0
        body = str("")
        body = '<HTTP_JSON>'
        body  += '{'+\
            '"code": 11,'+\
            '"tracks": ['
        for states in _stats:
            c=c+1
            body += states.toJson(c,len(_stats))+','
            
        body = body[:-1]
        body +='],'+\
        '"scanTime": "'+_stats[0].time.toUTC().toString("yyyy-MM-dd HH:mm:ss.z") +'"'+\
        '}'
        body+='</HTTP_JSON>'
        print(body)
        self.send(body);
    def receiveSensors(self):
        body = str("")
        if self.onlyJson == True:
            for _csensor in dataManager.instance().sensors():
 
                    body = '<HTTP_JSON>'
                    body += _csensor.toJson()
                    body+='</HTTP_JSON>'
                    body+='\n'
          
                    self.message.emit("send sensor parameters")
                    self.send(body);
         
                    time.sleep(0.5)
                    body = str("")
    def receiveSensor(self,_sensor):
        body = str("")
        if self.onlyJson == True:
 
            for _csensor in dataManager.sensors():
                if _sensor.id == _csensor.id:
                    body = '<HTTP_JSON>'
                    body += _sensor.toJson()
                    body+='</HTTP_JSON>'
                    body+='\n'
          
                    self.message.emit("send sensor parameters")
                    self.send(body);
         
                    time.sleep(0.5)
                    return
           
    def receivePlatform(self,_plateform):
    
        self.platforms.append(_plateform)
        
    def close(self):
        #print("close")
        self.connected = False
        
        #if self.connected:
       #     self.client.close()
  
 
        self.finished.emit()
        self.socket.close()
     
    def parameters(self):
 
         window = QDialog()
         self.ui.setupUi(window)
  
         if window.exec():
             ADRESS_IP = self.ui.lineEditIP.text()
             TCP_IP    = ADRESS_IP.encode('utf-8')
             TCP_PORT  = int(self.ui.lineEditPort.text())
 
    def connect(self):
  
        if not self.connected:
            self.message.emit("try connection")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            #self.socket = socket.socket()
            self.socket.bind((TCP_IP, TCP_PORT)) 
            self.socket.listen(5)
            self.connected = True
            while   self.connected:
 
                self.message.emit("waiting for connection...")
                client,  adress = self.socket.accept()
                listen = threading.Thread(target=self.listen,args=( client,  adress))
                #threading.Thread(target=self.write,args=( client,  adress))
#                print('yu')
#                print('self.adress')
#                print(self.adress)
#                buf = self.client.recv(BUFFER_SIZE)
#                print(len(buf))
#                if len(buf) > 0:
                self.message.emit("\n>>"+ "["+str(adress)+"]")# + str(buf))
                self.connected = True
                listen.start()
                self.clients.append((client,listen,'UNKNOWN'))
              
                
            self.socket.close()
    
        
#            self.ListenThread  = threading.Thread(target=self.listen) 
#            #self.WrittenThread = threading.Thread(target=self.write) 
#         
#            self.ListenThread.start()
            #self.WrittenThread.start()
    
    def sendConfiguration(self):
  
        body = str("")
        if self.onlyJson == True:
            for _node in dataManager.instance().nodes():
      
                body = '<HTTP_JSON>'
                body = body + _node.toJson( ADRESS_IP)
                body+='</HTTP_JSON>'
                body+='\n'
                self.message.emit("send node parameters")
                self.send(body);
                time.sleep(0.5)
          
            body = str("")
          
            for _sensor in dataManager.instance().sensors():
                body = '<HTTP_JSON>'
                body += _sensor.toJson()
                body+='</HTTP_JSON>'
                body+='\n'
          
                self.message.emit("send sensor parameters")
                self.send(body);
         
                time.sleep(0.5)
            body = str("")
            return
                
        
        for _platform in self.platforms:
            #create Node
                #print("2 - send _platform") 
                body = str(" <HTTP_JSON> ")
                adress = "135.128.1."+str(_platform.id)
                body+='<Node address="'+adress+'"   name="'+_platform.name+'" color="#ff00ff" TypeNode="5" date="'+_platform.times[0].toString("yyyy-MM-dd HH:mm:ss.z")+'">'+\
                  '<Comments></Comments>'+\
                  '<Position latitude="'+str(_platform.locations[0].latitude)+'" altitude="'+str(_platform.altitude)+'" longitude="'+str(_platform.locations[0].longitude)+'"/>'+\
                  '<sensors number="0">'+\
                  '</sensors>'+\
                  '</Node>'
                  
                self.message.emit("platform parameter send")
                body = str(" </HTTP_JSON> ")
                self.send(body);
                time.sleep(0.5)
           
                body=''
               
                for _sensor in _platform.sensors:          
                    
                    sensorType = 'UNKNOWN'
                    if _sensor.mode == SensorMode.radar:
                         sensorType='RADAR_ELTA'
                         adressSen = "165.111.1."+str(_sensor.id)
                         body='<sensor id="'+adressSen+'" nodeAddress="'+adress+'" sensorType="'+str(sensorType)+'">'+'<command>create</command >'+\
                        '<volumes>'+\
                        '<volume type="2">'+\
                        '<class>UNKNOWN</class>'+\
                        '<distance_min unit="meter">'+str(_sensor.sensorCoverage.distanceMin)+'</distance_min>'+\
                        '<distance_max unit="meter"> '+str(_sensor.sensorCoverage.distanceMax)+'</distance_max>'+\
                        '<field_of_view unit="degree">'+str(_sensor.sensorCoverage.fov)+'</field_of_view>'+\
                        '</volume>'+\
                        '</volumes>'+\
                        '</sensor>'
                    if _sensor.mode == SensorMode.radar3D:
                         sensorType='RADAR'
                         adressSen = "165.111.1."+str(_sensor.id)
                         body='<sensor id="'+adressSen+'" nodeAddress="'+adress+'" sensorType="'+str(sensorType)+'">'+'<command>create</command >'+\
                        '<volumes>'+\
                        '<volume type="3">'+\
                        '<class>UNKNOWN</class>'+\
                        '<distance_min unit="meter">'+str(_sensor.sensorCoverage.distanceMin)+'</distance_min>'+\
                        '<distance_max unit="meter"> '+str(_sensor.sensorCoverage.distanceMax)+'</distance_max>'+\
                        '<field_of_view unit="degree">'+str(_sensor.sensorCoverage.fov)+'</field_of_view>'+\
                        '<field_of_view_site>'+str(_sensor.sensorCoverage.fov_elevation)+'</field_of_view_site>'+\
                        '</volume>'+\
                        '</volumes>'+\
                        '</sensor>'
                    if _sensor.mode == SensorMode.optroIR2D:
                         sensorType='VIDEO_IR'
                         adressSen = "165.111.1."+str(_sensor.id)
                         body='<sensor id="'+adressSen+'" nodeAddress="'+adress+'" sensorType="'+str(sensorType)+'">'+'<command>create</command >'+\
                        '<volumes>'+\
                        '<volume type="3">'+\
                        '<class>UNKNOWN</class>'+\
                        '<distance_min unit="meter">'+str(_sensor.sensorCoverage.distanceMin)+'</distance_min>'+\
                        '<distance_max unit="meter"> '+str(_sensor.sensorCoverage.distanceMax)+'</distance_max>'+\
                        '<field_of_view unit="degree">'+str(_sensor.sensorCoverage.fov)+'</field_of_view>'+\
                        '<field_of_view_site>'+str(_sensor.sensorCoverage.fov_elevation)+'</field_of_view_site>'+\
                        '</volume>'+\
                         '<volume type="3">'+\
                        '<class>GROUND_VEHICLE</class>'+\
                        '<distance_min unit="meter">'+str(_sensor.sensorCoverage.distanceMin)+'</distance_min>'+\
                        '<distance_max unit="meter"> '+str(_sensor.sensorCoverage.distanceMax)+'</distance_max>'+\
                        '<field_of_view unit="degree">'+str(_sensor.sensorCoverage.fov)+'</field_of_view>'+\
                        '<field_of_view_site>'+str(_sensor.sensorCoverage.fov_elevation)+'</field_of_view_site>'+\
                        '</volume>'+\
                         '<volume type="3">'+\
                        '<class>PAX</class>'+\
                        '<distance_min unit="meter">'+str(_sensor.sensorCoverage.distanceMin)+'</distance_min>'+\
                        '<distance_max unit="meter"> '+str(_sensor.sensorCoverage.distanceMax)+'</distance_max>'+\
                        '<field_of_view unit="degree">'+str(_sensor.sensorCoverage.fov)+'</field_of_view>'+\
                        '<field_of_view_site>'+str(_sensor.sensorCoverage.fov_elevation)+'</field_of_view_site>'+\
                        '</volume>'+\
                        '<volume type="3">'+\
                        '<distance_min unit="meter">'+str(_sensor.sensorCoverage.distanceMin)+'</distance_min>'+\
                        '<distance_max unit="meter"> '+str(_sensor.sensorCoverage.distanceMax)+'</distance_max>'+\
                        '<field_of_view unit="degree">'+str(_sensor.sensorCoverage.fov)+'</field_of_view>'+\
                        '<field_of_view_site>'+str(_sensor.sensorCoverage.fov_elevation)+'</field_of_view_site>'+\
                        '</volume>'+\
                        '</volumes>'+\
                        '</sensor>'
                    elif _sensor.mode == SensorMode.optroVIS:
                         sensorType='VIDEO_VISIBLE'
                         adressSen = "165.111.1."+str(_sensor.id)
                         body='<sensor id="'+adressSen+'" nodeAddress="'+adress+'" sensorType="'+str(sensorType)+'">'+'<command>create</command >'+\
                        '<volumes>'+\
                        '<volume type="2">'+\
                        '<class>UNKNOWN</class>'+\
                        '<distance_min unit="meter">'+str(_sensor.sensorCoverage.distanceMin)+'</distance_min>'+\
                        '<distance_max unit="meter"> '+str(_sensor.sensorCoverage.distanceMax)+'</distance_max>'+\
                        '<field_of_view unit="degree">'+str(_sensor.sensorCoverage.fov)+'</field_of_view>'+\
                        '</volume>'+\
                        '<volume type="2">'+\
                        '<class>GROUND_VEHICLE</class>'+\
                        '<distance_min unit="meter">'+str(_sensor.sensorCoverage.distanceMin)+'</distance_min>'+\
                        '<distance_max unit="meter"> '+str(_sensor.sensorCoverage.distanceMax)+'</distance_max>'+\
                        '<field_of_view unit="degree">'+str(_sensor.sensorCoverage.fov)+'</field_of_view>'+\
                        '</volume>'+\
                        '<volume type="2">'+\
                        '<class>AERIAL</class>'+\
                        '<distance_min unit="meter">'+str(_sensor.sensorCoverage.distanceMin)+'</distance_min>'+\
                        '<distance_max unit="meter"> '+str(_sensor.sensorCoverage.distanceMax)+'</distance_max>'+\
                        '<field_of_view unit="degree">'+str(_sensor.sensorCoverage.fov)+'</field_of_view>'+\
                        '</volume>'+\
                        '<volume type="2">'+\
                        '<class>PAX</class>'+\
                        '<distance_min unit="meter">'+str(_sensor.sensorCoverage.distanceMin)+'</distance_min>'+\
                        '<distance_max unit="meter"> '+str(_sensor.sensorCoverage.distanceMax)+'</distance_max>'+\
                        '<field_of_view unit="degree">'+str(_sensor.sensorCoverage.fov)+'</field_of_view>'+\
                        '</volume>'+\
                        '</volumes>'+\
                        '</sensor>'
                    elif _sensor.mode == SensorMode.sismo:
                         sensorType='SEISMIC'
                         adressSen = "165.111.1."+str(_sensor.id)
                         body='<sensor id="'+adressSen+'" nodeAddress="'+adress+'" sensorType="'+str(sensorType)+'">'+'<command>create</command >'+\
                        '<volumes>'+\
                        '<volume type="1">'+\
                        '<class>UNKNOWN</class>'+\
                        '<distance_min unit="meter">'+str(_sensor.sensorCoverage.distanceMin)+'</distance_min>'+\
                        '<distance_max unit="meter"> '+str(_sensor.sensorCoverage.distanceMax)+'</distance_max>'+\
                        '</volume>'+\
                        '</volumes>'+\
                        '</sensor>'
                   
                       
                    #print(body)
                    self.send(body);
                    time.sleep(1)
                    self.message.emit("sensor parameter send")
            
        
 
                body = str("")

        for _node in dataManager.instance().nodes():           
            adress = "135.125.1."+str(_node.id)
            body='<Node address="'+adress+'"   name="'+_node.name+'" color="#ff00ff" TypeNode="1">'+\
                  '<Comments></Comments>'+\
                  '<Position latitude="'+str(_node.Position.latitude)+'" altitude="1.0" longitude="'+str(_node.Position.longitude)+'"/>'+\
                  '<Attitude pitch="'+str(_node.Orientation.pitch)+'" yaw="'+str(_node.Orientation.roll)+'" roll="'+str(0)+'"/>'+\
                  '<sensors number="0">'+\
                  '</sensors>'+\
                  '</Node>'
     
            self.send(body);
            time.sleep(1)
            body =[];
            
        for _sensor in dataManager.instance().sensors():              
                sensorType = 'UNKNOWN'
                adress = "135.125.1."+str(_sensor.node.id)
                if _sensor.mode == SensorMode.radar:
                     sensorType='RADAR_ELTA'
                     adressSen = "165.111.1."+str(_sensor.id)
                     body='<sensor id="'+adressSen+'" nodeAddress="'+adress+'" sensorType="'+str(sensorType)+'">'+'<command>create</command >'+\
                    '<volumes>'+\
                    '<volume type="2">'+\
                    '<class>UNKNOWN</class>'+\
                    '<distance_min unit="meter">'+str(_sensor.sensorCoverage.distanceMin)+'</distance_min>'+\
                    '<distance_max unit="meter"> '+str(_sensor.sensorCoverage.distanceMax)+'</distance_max>'+\
                    '<field_of_view unit="degree">'+str(_sensor.sensorCoverage.fov)+'</field_of_view>'+\
                    '</volume>'+\
                    '</volumes>'+\
                    '</sensor>'
                if _sensor.mode == SensorMode.radar3D:
                     sensorType='RADAR'
                     adressSen = "165.111.1."+str(_sensor.id)
                     body='<sensor id="'+adressSen+'" nodeAddress="'+adress+'" sensorType="'+str(sensorType)+'">'+'<command>create</command >'+\
                    '<volumes>'+\
                    '<volume type="3">'+\
                    '<class>UNKNOWN</class>'+\
                    '<distance_min unit="meter">'+str(_sensor.sensorCoverage.distanceMin)+'</distance_min>'+\
                    '<distance_max unit="meter"> '+str(_sensor.sensorCoverage.distanceMax)+'</distance_max>'+\
                    '<field_of_view unit="degree">'+str(_sensor.sensorCoverage.fov)+'</field_of_view>'+\
                    '<field_of_view_site>'+str(_sensor.sensorCoverage.fov_elevation)+'</field_of_view_site>'+\
                    '</volume>'+\
                    '</volumes>'+\
                    '</sensor>'
                if _sensor.mode == SensorMode.optroIR2D:
            
                     sensorType='VIDEO_IR'
                     adressSen = "165.111.1."+str(_sensor.id)
                     body='<sensor id="'+adressSen+'" nodeAddress="'+adress+'" sensorType="'+str(sensorType)+'">'+'<command>create</command >'+\
                    '<volumes>'+\
                    '<volume type="3">'+\
                    '<class>UNKNOWN</class>'+\
                    '<distance_min unit="meter">'+str(_sensor.sensorCoverage.distanceMin)+'</distance_min>'+\
                    '<distance_max unit="meter"> '+str(_sensor.sensorCoverage.distanceMax)+'</distance_max>'+\
                    '<field_of_view unit="degree">'+str(_sensor.sensorCoverage.fov)+'</field_of_view>'+\
                    '<field_of_view_site>'+str(_sensor.sensorCoverage.fov_elevation)+'</field_of_view_site>'+\
                    '</volume>'+\
                     '<volume type="3">'+\
                    '<class>GROUND_VEHICLE</class>'+\
                    '<distance_min unit="meter">'+str(_sensor.sensorCoverage.distanceMin)+'</distance_min>'+\
                    '<distance_max unit="meter"> '+str(_sensor.sensorCoverage.distanceMax)+'</distance_max>'+\
                    '<field_of_view unit="degree">'+str(_sensor.sensorCoverage.fov)+'</field_of_view>'+\
                    '<field_of_view_site>'+str(_sensor.sensorCoverage.fov_elevation)+'</field_of_view_site>'+\
                    '</volume>'+\
                     '<volume type="3">'+\
                    '<class>PAX</class>'+\
                    '<distance_min unit="meter">'+str(_sensor.sensorCoverage.distanceMin)+'</distance_min>'+\
                    '<distance_max unit="meter"> '+str(_sensor.sensorCoverage.distanceMax)+'</distance_max>'+\
                    '<field_of_view unit="degree">'+str(_sensor.sensorCoverage.fov)+'</field_of_view>'+\
                    '<field_of_view_site>'+str(_sensor.sensorCoverage.fov_elevation)+'</field_of_view_site>'+\
                    '</volume>'+\
                    '<volume type="3">'+\
                    '<distance_min unit="meter">'+str(_sensor.sensorCoverage.distanceMin)+'</distance_min>'+\
                    '<distance_max unit="meter"> '+str(_sensor.sensorCoverage.distanceMax)+'</distance_max>'+\
                    '<field_of_view unit="degree">'+str(_sensor.sensorCoverage.fov)+'</field_of_view>'+\
                    '<field_of_view_site>'+str(_sensor.sensorCoverage.fov_elevation)+'</field_of_view_site>'+\
                    '</volume>'+\
                    '</volumes>'+\
                    '</sensor>'
                if _sensor.mode == SensorMode.optroVIS:
                     sensorType='VIDEO_VISIBLE'
                     adressSen = "165.111.1."+str(_sensor.id)
                     body='<sensor id="'+adressSen+'" nodeAddress="'+adress+'" sensorType="'+str(sensorType)+'">'+'<command>create</command >'+\
                    '<volumes>'+\
                    '<volume type="2">'+\
                    '<class>UNKNOWN</class>'+\
                    '<distance_min unit="meter">'+str(_sensor.sensorCoverage.distanceMin)+'</distance_min>'+\
                    '<distance_max unit="meter"> '+str(_sensor.sensorCoverage.distanceMax)+'</distance_max>'+\
                    '<field_of_view unit="degree">'+str(_sensor.sensorCoverage.fov)+'</field_of_view>'+\
                    '</volume>'+\
                    '<volume type="2">'+\
                    '<class>GROUND_VEHICLE</class>'+\
                    '<distance_min unit="meter">'+str(_sensor.sensorCoverage.distanceMin)+'</distance_min>'+\
                    '<distance_max unit="meter"> '+str(_sensor.sensorCoverage.distanceMax)+'</distance_max>'+\
                    '<field_of_view unit="degree">'+str(_sensor.sensorCoverage.fov)+'</field_of_view>'+\
                    '</volume>'+\
                    '<volume type="2">'+\
                    '<class>AERIAL</class>'+\
                    '<distance_min unit="meter">'+str(_sensor.sensorCoverage.distanceMin)+'</distance_min>'+\
                    '<distance_max unit="meter"> '+str(_sensor.sensorCoverage.distanceMax)+'</distance_max>'+\
                    '<field_of_view unit="degree">'+str(_sensor.sensorCoverage.fov)+'</field_of_view>'+\
                    '</volume>'+\
                    '<volume type="2">'+\
                    '<class>PAX</class>'+\
                    '<distance_min unit="meter">'+str(_sensor.sensorCoverage.distanceMin)+'</distance_min>'+\
                    '<distance_max unit="meter"> '+str(_sensor.sensorCoverage.distanceMax)+'</distance_max>'+\
                    '<field_of_view unit="degree">'+str(_sensor.sensorCoverage.fov)+'</field_of_view>'+\
                    '</volume>'+\
                    '</volumes>'+\
                    '</sensor>'
                if  _sensor.mode == SensorMode.PIR:
                     sensorType='PIR'
                     adressSen = "165.111.1."+str(_sensor.id)
                     body='<sensor id="'+adressSen+'" nodeAddress="'+adress+'" sensorType="'+str(sensorType)+'">'+'<command>create</command >'+\
                    '<volumes>'+\
                    '<volume type="2">'+\
                    '<class>UNKNOWN</class>'+\
                    '<distance_min unit="meter">'+str(_sensor.sensorCoverage.distanceMin)+'</distance_min>'+\
                    '<distance_max unit="meter"> '+str(_sensor.sensorCoverage.distanceMax)+'</distance_max>'+\
                    '<field_of_view unit="degree">'+str(_sensor.sensorCoverage.fov)+'</field_of_view>'+\
                    '</volume>'+\
                    '</volumes>'+\
                    '</sensor>  '   
                elif _sensor.mode == SensorMode.sismo:
                     sensorType='SEISMIC'
                     adressSen = "165.111.1."+str(_sensor.id)
                     body='<sensor id="'+adressSen+'" nodeAddress="'+adress+'" sensorType="'+str(sensorType)+'">'+'<command>create</command >'+\
                    '<volumes>'+\
                    '<volume type="1">'+\
                    '<class>UNKNOWN</class>'+\
                    '<distance_min unit="meter">'+str(_sensor.sensorCoverage.distanceMin)+'</distance_min>'+\
                    '<distance_max unit="meter"> '+str(_sensor.sensorCoverage.distanceMax)+'</distance_max>'+\
                    '</volume>'+\
                    '</volumes>'+\
                    '</sensor>'
             
                if body:
               
                    self.send(body);
                
                time.sleep(1)
                self.message.emit("sensor parameter send")
                self.sendLink(_sensor)
                body = str("")
       
    def sendLink(self,sensor ):
        
                adress = "135.125.1."+str(sensor.id)
                
                body='<Links nodeAddress="'+adress+'">'
                
                for _link in sensor.connections:
                     adress = "135.125.1."+str(_link)
                     body+='<Link connectedTo="'+str(adress)+'" RSSI="-52.0"/>'
                
                body+='</Links>'
                #print(body)
                  
               
                self.send(body);
                time.sleep(0.1)
        
#                self.commande = body
#                flag = True
#                while flag == True:
#                    time.sleep(0.5)
#                    if self.commande == str(""):
#                        flag = False
    def sendJsonMessage(self,json,_node = None):
            body = '<HTTP_JSON>'
            body += json 
            body +='</HTTP_JSON>'
            body+='\n'
 
            self.send(str(body),_node)
            body = str("")
    def sendJsonCommand(self,json,_node = None):
            if json =='':
                return
            body = '<HTTP_JSON>'
            body += json 
            body +='</HTTP_JSON>'
            body+='\n'
            
            self.send(str(body),_node)
            body = str("")
    def sendScans(self,_scans ):
        
        for _scan in _scans :
            self.sendScan(_scan)
    def sendScan(self,_scan ):
        
        
        if self.onlyJson == True:
            body = '<HTTP_JSON>'
            body += _scan.toJson() 
            body +='</HTTP_JSON>'
            body+='\n'
        else:
            body = '<HTTP_JSON>'
            body += _scan.toJson()
            body +='</HTTP_JSON>'
        selected_clients = []
        
        for _node in self.clients:
           
            if len(_node)==4:
                if int(_scan.sensor.id) in _node[3]:
                    selected_clients.append(_node)
#        if selected_clients == [] :
#            print("no client selected")
#        else: 
#            print('client selected')
        for _node in selected_clients:
            if _node[2]!='FUSION_MASTER_NODE':
                self.send(str(body),_node[0])
        body = str("")
    def sendTarget(self,jsonTarget):
        if self.onlyJson == True:
            self.send(str(jsonTarget))
        else:
            body = '<HTTP_JSON>'
            body += str(jsonTarget)
            body +='</HTTP_JSON>'
            self.send(body)
    def sendPlatform(self,json ):        
        self.send(str(json ))
    def newRun(self,val):
        time.sleep(0.2)
        body = '<HTTP_JSON>'
        body += str('{\
                    "message":"",\
                    "code":5,\
                    "command":"tracker destroy  tracks"\
                    }')
        body +='</HTTP_JSON>'
        #body ="<command>tracker destroy  tracks</command>"
        self.send(body)
        
        time.sleep(0.2)
        body = '<HTTP_JSON>'
        body += str('{\
                    "message":"",\
                    "code":5,\
                    "command":"dataBase new ')  + str("run_"+str(val)+".db\"")+str('}')
        body +='</HTTP_JSON>'
     
        #body ="<command>dataBase new "+ "run_"+str(val)+".db"+" </command>"
        self.send(body)
        
        time.sleep(0.2)
        body = '<HTTP_JSON>'
        body += str('{\
                    "message":"",\
                    "code":5,\
                    "command":"target -delete all"\
                    }')
        body +='</HTTP_JSON>'
        #body ="<command>target -delete all</command>"
        self.send(body)
        time.sleep(0.2)
        body = '<HTTP_JSON>'
        body += str('{\
                    "message":"",\
                    "code":5,\
                    "command":"SIG remove detections"\
                    }')
        body +='</HTTP_JSON>'
        #body ="<command>SIG remove detections</command>"
        self.send(body)
    def tic(self,time ):
    
        #body = "<command>time -emit "+ str(QDateTime.currentDateTimeUtc)  +"</command>"
        #self.send(body)
        body = "<command>time -tic "+ str(time.toTime_t())  +"</command>"
        #print(body)
        self.send(body)
    def synchronize(self,time ):
        #print('----> synchro')
        #body = "<command>time -emit "+ str(QDateTime.currentDateTimeUtc)  +"</command>"
        #self.send(body)
         body = '<HTTP_JSON>'
         body += str('{\
                    "message":"",\
                    "code":5,\
                    "command":"time -synchronize ')+ str(time.toTime_t())+"\""+str('}')
         body +='</HTTP_JSON>'
        #body = "<command>time -synchronize "+ str(time.toTime_t())  +"</command>"
   
         self.send(body)
#            
            
#    def write(self,clientsock, addr):
#        while True:
#            if self.commande != str(""):
#                print(self.commande)
#                clientsock.send(self.commande.encode(encoding='utf_8'))
#                self.commande =str("")
    
    def run(self):
        
        #print("thread started")
        self.connect()  
  

    def flush(self):
        self.buffer+=(BUFFER_SIZE-len(self.buffer)%BUFFER_SIZE)*"\x00"
        self.send("")
        
    def send(self,body,_client = None):
        if  self.mutex.tryLock() :
     
        
            if self.connected and body!='':
  
                data = body.encode(encoding='utf_8')
                if _client == None:
          
                    for _client in self.clients :
                            totalsent = 0
                
                            while totalsent < len(data):

                                sent = _client[0].send(data[totalsent:])
                   
                                if sent == 0:
                                
                                    raise RuntimeError("socket connection broken")
                                totalsent = totalsent + sent
                  
                else:
                    totalsent = 0
                    while totalsent < len(data):
#                            print("--------->")
#                            print(body)
#                            print("--------->")
                            sent = _client.send(data[totalsent:])
                            if sent == 0:
                                raise RuntimeError("socket connection broken")
                            totalsent = totalsent + sent 
            self.mutex.unlock()
            
    def listen(self,clientsocket,addr):
        dataStr =''
       
        while True:
    
            data = clientsocket.recv(BUFFER_SIZE)
#            print(data)
#            t = clientsocket.recv(1024, socket.MSG_PEEK) 
#            print('y')
            if len(data)==0:
                print("Client disconnected.") 
                for _client in self.clients:
                    if _client[0] == clientsocket :
                        self.clients.remove(_client)
                        print('thread is killed')
                        return
            if data:
                data = data.decode("utf-8")
              
#                if dataStr !='':
#                print('============================================')
#                print(data)
                dataStr += data
                
#                if data[0:11] =='<HTTP_JSON>':
#                    dataStr = data
          
                
                
                            
                #Pprint('*****************************************************')
                if  dataStr.find('<HTTP_JSON>')!=-1 and dataStr.find('</HTTP_JSON>')!=-1:
          
                    Datalist = dataStr.split('<HTTP_JSON>')
                    dataStr2 = ''
                    for u in Datalist:
#                                print('----------------->')
#                                print(u)
#                                print('----------------->')
                                dataStr2 = u
                                #dataStr2 = dataStr.replace('<HTTP_JSON>', '')
                                if dataStr2.find('</HTTP_JSON>')!=-1 and dataStr2 !='':
                                    dataStr2 = dataStr2.replace('</HTTP_JSON>', '')
                                    self.message.emit(dataStr2) 
                                    try : 
                                        jsonD = readJson.loads(dataStr2)
                                    except:
                                        print('json Error')
                                        
                                    if jsonD['code'] ==10 :
                                         for _client in self.clients:
                                            if _client[0] != clientsocket:
                                              self.sendJsonMessage(dataStr2,_client[0])
                                         self.chatMessage.emit(jsonD['chat']['emitter']+str(': ')+jsonD['chat']['message'])
                                    if jsonD['code'] ==2 :
                                                #print("in jsonD[code]==2")
                                                for _client in self.clients:
                                                 #   print([jsonD['nodeType'],clientsocket,_client[0]])
                                                    if _client[0] == clientsocket and _client[2]!='FUSION_MASTER_NODE' and (jsonD['nodeType'] == 'FUSION_SLAVE_NODE' or jsonD['nodeType'] == 'FUSION_MASTER_NODE' ) :
                                                
                                                        JsonArray =[]
                                                        sensorsResp = []
                                                        try :
                                                            JsonArray = jsonD['sensorResponsabilities']
                                                        except:
                                                            print('no sensor Responsabilities')
                                                     
                                                        for up in range (0,len(JsonArray)):
                                                            sensorsResp.append(int(JsonArray[up]['sensor']));
                                                  
                                                        _client2  = (_client[0],_client[1],str(jsonD['nodeType']),sensorsResp)
                                                        #print('---2')    
                                                        self.clients.remove(_client)
                                                        self.clients.append(_client2)
                                                        #print(_client[0])
                                                         #print(self.clients)
#                                                        print(self.clients)
#                                                        print(_client2[0].gethostname())
#                                                        print(clientsocket.gethostname())
#                                                        print('---3')
                                                        break
                                                #print('receive node')
                                  
                                                for _client in self.clients:
                                                 #   print(_client[2])
                                                    if _client[2]== 'FUSION_MASTER_NODE' :
                                                        
                                                        print("====> send node to master node listen")
                                                        self.sendJsonMessage(dataStr2,_client[0])
                         
                                                
                                    if jsonD['code'] ==1 :
                                                for _client in self.clients:
                                                    if _client[2]== 'FUSION_MASTER_NODE' :
                                                         print("====> send track")
                                                         self.sendJsonMessage(dataStr2,_client[0])
                                                         
                 
                    dataStr = '<HTTP_JSON>'+dataStr2

                    

#                        myState = localState()
#                        print(dataStr2)
                        #myState
                        #self.sendTrackState.emit(myState)
            
                    #dataStr = ''
                    
#        if not self.connected:
#            self.connect()
#            print("not connected")
#
#        while self.connected:
#       
#            data = self.client.recv(BUFFER_SIZE)
#            if data:
#               self.message.emit(str(data)) 
            #if not  data: break
            #else:
            #  self.message.emit(str(data))
        #print("listen close")
        clientsocket.close()
   
    
def main(argv=None):
    app = QApplication(sys.argv)
    window = QDialog()
    ui = Ui_Dialog()
    ui.setupUi(window)

    window.show()
    sys.exit(app.exec_())
    
if __name__ == "__main__":
    main() 