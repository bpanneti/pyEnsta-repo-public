# -*- coding: utf-8 -*-
"""
Created on Thu Aug 29 08:52:47 2019

@author: bpanneti
"""

# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'SAFIRsettings.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!
 
from PyQt5.QtCore    import *
from PyQt5.QtGui     import *
from PyQt5.QtOpenGL  import *
from PyQt5.QtWidgets import *
import os
import sys
 
#sys.path.append("C:/Users/benja/OneDrive/Documents/pysim/shieldlib/lib/python3.6/site-packages/shield")
sys.path.insert(1,"./shieldlib/lib/python3.6/site-packages/shield") 
import ShieldJsonSocket
import ShieldMessages 
import threading
import time

from shieldViewer import Ui_Dialog as Ui_Shield


from sensor import SensorMode
from scan import PLOTType
from tool_tracking.track import Track
from tool_tracking.motionModel import StateType
 
ADRESS_IP = '127.0.0.1'
TCP_PORT = 4567
BUFFER_SIZE = 1024 
from Managers.dataManager import DataManager as dataManager
from packages.ntplib import ntplib
from time import ctime


#class MessageSender(threading.Thread):
#    
#    def __init__(self, loop_timeout_msec):
#        threading.Thread.__init__(self)
#        self.__client               = None
#        self.__stop_received        = False
#        self.__loop_timeout_msec    = loop_timeout_msec
#        self.__lock                 = threading.Lock()
#        self.__message              = None
#    def set_client(self, client):
#        with self.__lock:
#            self.__client = client
#    
#    def stop(self):
#        with self.__lock:
#            self.__client           = None
#            self.__stop_received    = False
#
#    def run(self):
#        #messages_builder = TestMessagesBuilder()
#        exitLoop = False
#        while not exitLoop:
#            with self.__lock:
#                if self.__stop_received:
#                    exitLoop = True
#                elif self.__client is not None and self.__message!=None:
#                    #message = messages_builder.build_MessageDetection()
#                    self.__client.Send(self.__message)
#                    self.__message = None
#            time.sleep(self.__loop_timeout_msec / 1000.0)

class ClientShield(QWidget,threading.Thread):
    message         = pyqtSignal('QString');
    connected       = pyqtSignal()
    disconnected    = pyqtSignal() 
    messageChat     = pyqtSignal(list)
    referencePoint  = pyqtSignal('QString')
    synchronization = pyqtSignal(QDateTime)
    command         = pyqtSignal('QString')
    def __init__(self, client_name, server_address = '127.0.0.1', server_port = 4567):
        #super(ClientShield, self).__init__()
        threading.Thread.__init__(self)
        QWidget.__init__(self)
        
        self.client = Client(client_name,server_address, 4567)
     
        self.client.message.connect(self.receiveMessage)
        self.client.connected.connect(self.connectToServer)
        self.client.disconnected.connect(self.disconnectToServer)
        self.client.messageChat.connect(self.receiveMessageChat)
        self.client.referencePoint.connect(self.receiveReferencePoint)
        self.client.command.connect(self.receiveCommand)
        self.lastTime =     QDateTime.currentDateTime()
        
        
        self.__stop_received = False
        #self.__lock = threading.Lock()
        
    def receiveCommand(self,strCommand):
        #print('strCommand :'+strCommand)
        self.command.emit(strCommand)
    def receiveTime(self,time = QDateTime()):
         
        if  abs(self.lastTime.secsTo(time)) > 10 :
            self.lastTime =     time
            self.getNTPTime()
    def receiveReferencePoint(self,msg):
        self.referencePoint.emit(msg)
#    def start(self):    
#        self.getNTPTime()
    def getNTPTime(self):
        pass
        '''
        server_address= '127.0.0.1'
        c = ntplib.NTPClient()
        response = c.request(server_address)
        #print(ctime(response.tx_time))
  
        ms = int(round( response.tx_time  * 1000))
    
        dateT  = QDateTime.fromMSecsSinceEpoch(ms)
  
        self.synchronization.emit(dateT)
        '''
#    def getNTPTime(self,server_address,server_port ):
#
#        port = 123
#
#        buf = 1024
#
#        address = (server_address,server_port)
#
#        msg = '\x1b' + 47 * '\0'
#
#        # reference time (in seconds since 1900-01-01 00:00:00)
#
#        TIME1970 = 2208988800L # 1970-01-01 00:00:00
#
#        # connect to server
#
#        client = socket.socket( AF_INET, SOCK_DGRAM)
#
#        client.sendto(msg, address)
#
#        msg, address = client.recvfrom( buf )
#
# 
#
#        t = struct.unpack( "!12I", msg )[10]
#
#        t -= TIME1970
#
#        return time.ctime(t).replace("  "," ")

 

 
       
    def stop(self):
 
        
            
        del self.client
        print('stop')
    def sendSemanticInfo(self,sensor,fname):
        self.semanticInformation(sensor,fname);
    def receiveMessageChat(self,msg):
        self.messageChat.emit(msg)
    def disconnectToServer(self):
        self.disconnected.emit()
    def connectToServer(self):
     
        self.connected.emit()
    def receiveMessage(self,msg):
        self.message.emit(msg)
    def sendChatMessage(self,msgstr):
     
        chat_msg = ShieldMessages.MessageChat()
        print(msgstr)
        chat_msg.mName     = msgstr[0]
        chat_msg.mMessage  = msgstr[1]
        
        self.client.Send(chat_msg)
        
    def receiveScans(self,_scans =[]):
        print('receive scans in SHIELD')
        for _scan in _scans:
            msg = ShieldMessages.MessageDetection()
            msg.mSensorId   = _scan.sensor.id
            msg.mScanId     = str(_scan.id)
            print('-----> 2')
            msg.mScanDate     = ShieldMessages.DateTime(_scan.dateTime.toUTC().toString('yyyy-MM-ddThh:mm:ss'))
            msg.mMessageDate  = ShieldMessages.DateTime(_scan.dateTime.toUTC().toString('yyyy-MM-ddThh:mm:ss'))
            
            
            if _scan.plotType == PLOTType.EVENT:
                msg.mAddInfoType1 = ShieldMessages.Plot.SNR
                msg.mAddInfoUnit1 = ShieldMessages.Plot.DB
                msg.mAddInfoType2 = ShieldMessages.Plot.HRRR
                msg.mAddInfoUnit2 = ShieldMessages.Plot.M2    
            else:
                msg.mAddInfoType1 = ShieldMessages.Plot.NO_VALUE
                msg.mAddInfoUnit1 = ShieldMessages.Plot.OTHER_UNIT
                msg.mAddInfoType2 = ShieldMessages.Plot.NO_VALUE
                msg.mAddInfoUnit2 = ShieldMessages.Plot.OTHER_UNIT
            plot_list = ShieldMessages.vector_shared_ptr_Plot()
         
            for _plot in _scan.plots:
                 plot = ShieldMessages.Plot()
                 plot.mId = str(_plot.id)
                 plot.mAcqDate = ShieldMessages.DateTime(_plot.dateTime.toUTC().toString('yyyy-MM-ddThh:mm:ss'))
 
                 if _scan.plotType == PLOTType.EVENT:
                        localisation = ShieldMessages.PlotLocalisationAlarm()
                        plot.mLocalisation = localisation
                 if _scan.plotType == PLOTType.SPHERICAL:
                        localisation = ShieldMessages.PlotLocalisationSpherical()
                        localisation.mPosition.SetAzimuth(_plot.theta)
                        localisation.mPosition.SetElevation(_plot.phi)
                        localisation.mPosition.SetDistance(_plot.rho)
                        localisation.mPrecision.SetAzimuth(_plot.sigma_theta)
                        localisation.mPrecision.SetElevation(_plot.sigma_phi)
                        localisation.mPrecision.SetDistance(_plot.sigma_rho)
                        plot.mLocalisation = localisation
                 if _scan.plotType == PLOTType.POLAR:
                        localisation = ShieldMessages.PlotLocalisationPolar()
                        localisation.mPosition.SetAzimuth(_plot.theta)
                        localisation.mPosition.SetDistance(_plot.rho)
                        localisation.mPrecision.SetAzimuth(_plot.sigma_theta)
                        localisation.mPrecision.SetDistance(_plot.sigma_rho)
                        plot.mLocalisation = localisation
                 if _scan.plotType == PLOTType.ANGULAR2D:
          
                        localisation = ShieldMessages.PlotLocalisationAngular2D()
                        localisation.mPosition.SetAzimuth(_plot.theta)
                        localisation.mPosition.SetElevation(_plot.sigma_phi)
                        localisation.mPrecision.SetAzimuth(_plot.sigma_theta)
                        localisation.mPrecision.SetElevation(_plot.sigma_phi)
                        plot.mLocalisation = localisation
                 if _scan.plotType == PLOTType.ANGULAR:
          
                        localisation = ShieldMessages.PlotLocalisationAngular1D()
                        localisation.mAzimuth = _plot.theta
                        localisation.mPrecision = _plot.sigma_theta
                        plot.mLocalisation = localisation
                     
                 velocity = ShieldMessages.PlotVelocityNone()
                 plot.mVelocity = velocity
        
                 plot.mPd   = _plot.pfa
                 plot.mPfa  = _plot.pd
            
            
                 plot.mClassification = ShieldMessages.UNKNOWN_CLASSIFICATION
                 if  _plot.Classification=="UNKNOWN":
                         plot.mClassification = ShieldMessages.UNKNOWN_CLASSIFICATION
                 elif  _plot.Classification=="PAX":
                         plot.mClassification = ShieldMessages.PAX    
                 elif  _plot.Classification=="CAR":
                         plot.mClassification = ShieldMessages.VEHICLE_LIGHT
                 elif  _plot.Classification=="DRONE":
                         plot.mClassification = ShieldMessages.DRONE
                 elif  _plot.Classification=="TANK":
                         plot.mClassification = ShieldMessages.VEHICLE_HEAVY
                 elif  _plot.Classification=="TRUCK":
                         plot.mClassification = ShieldMessages.VEHICLE_HEAVY
                         
             
                
                 plot.mEvidences =   _plot.url.replace('\\','\\\\')
         
                 if _scan.plotType == PLOTType.EVENT:
                     plot.mAddInfoValue1 = 723.12
                     plot.mAddInfoValue2 =  -53.28
                 else:
                     plot.mAddInfoValue1 = ShieldMessages.Plot.NO_VALUE
                     plot.mAddInfoValue2 = ShieldMessages.Plot.NO_VALUE
                 plot_list.push_back(plot)
             
            msg.mPlotList = plot_list
            print('-----> 4')
            self.client.Send(msg)
    def sendFOV(self,_sensor,angle_north):
    
            msg = ShieldMessages.CommandFieldOfView()
            msg.mSensorId = _sensor.id
            print('-------------> send FOV')
            print(_sensor.node.Orientation.yaw)
            msg.mOrientation.SetTheta(_sensor.node.Orientation.yaw-angle_north)
            msg.mOrientation.SetPhi(_sensor.node.Orientation.pitch)
            msg.mOrientation.SetPsi(_sensor.node.Orientation.roll)
 
       
            #print('direction sended')
            if _sensor.sensorCoverage != None:
                for _coverage in _sensor.sensorCoverage:
                        msg.mAzimuthSweep = _coverage.fov
                        msg.mElevationSweep = _coverage.fov_elevation
                        
                        self.client.Send(msg)
                        return
    def sendTracks(self, tracks):
        print('send tracks')
        msg = ShieldMessages.MessageTracks()
        msg.mEmitterId = 'MyTracker'
        for _track in tracks:
            
          
             _state      = _track.getCurrentState()
             _state     = _state.data
             track      = ShieldMessages.Track()
             track.mId  = str(_track.id)
             track.mDate = ShieldMessages.DateTime(_state.time.toString('yyyy-MM-ddThh:mm:ss.z'))
             track.mStatus = ShieldMessages.Track.CONFIRMED
             track.mClassification = ShieldMessages.UNKNOWN_CLASSIFICATION
#             for i in range(0, 2):
#                track.mEvidences.push_back('Evidence #%r' % (i))
#             for i in range(0, 5):
#                track.mPlotIdList.push_back('Plot #%r' % (i))
             if _state.mode == StateType.XY:
                 kinematic = ShieldMessages.Kinematic2D()
                 kinematic.mFrame = ShieldMessages.WGS84
                 position = ShieldMessages.Position2DWGS84()
                 position.SetLat(_state.location.latitude)
                 position.SetLon(_state.location.longitude)
                 kinematic.mPosition = position

                 kinematic.mVelocity.mX = _state.state[1,0]
                 kinematic.mVelocity.mY = _state.state[3,0]
                 kinematic.mVelocity.mZ = 0.0
                 
                 kinematic.mCovariance.mX11 = _state.covarianceWGS84[0,0]
                 kinematic.mCovariance.mX12 = _state.covarianceWGS84[0,1]
                 kinematic.mCovariance.mX13 = _state.covarianceWGS84[0,2]
                 kinematic.mCovariance.mX14 = _state.covarianceWGS84[0,3]
                 kinematic.mCovariance.mX21 = _state.covarianceWGS84[1,0]
                 kinematic.mCovariance.mX22 = _state.covarianceWGS84[1,1]
                 kinematic.mCovariance.mX23 = _state.covarianceWGS84[1,2]
                 kinematic.mCovariance.mX24 = _state.covarianceWGS84[1,3]
                 kinematic.mCovariance.mX31 = _state.covarianceWGS84[2,0]
                 kinematic.mCovariance.mX32 = _state.covarianceWGS84[2,1]
                 kinematic.mCovariance.mX33 = _state.covarianceWGS84[2,2]
                 kinematic.mCovariance.mX34 = _state.covarianceWGS84[2,3]
                 kinematic.mCovariance.mX41 = _state.covarianceWGS84[3,0]
                 kinematic.mCovariance.mX42 = _state.covarianceWGS84[3,1]
                 kinematic.mCovariance.mX43 = _state.covarianceWGS84[3,2]
                 kinematic.mCovariance.mX44 = _state.covarianceWGS84[3,3]
                 track.mKinematic = kinematic
                 
#             if _state.mode == StateType.XYZ:
#                 kinematic = ShieldMessages.Kinematic3D()
#                 kinematic.mFrame = ShieldMessages.WGS84
#                 position = ShieldMessages.Position3DWGS84()
#                 position.SetLat(_state.location.latitude)
#                 position.SetLon(_state.location.longitude)
#                 position.SetAlt(_state.location.altitude)
#                 kinematic.mPosition = position
#                 kinematic.mCovariance.mX11 = 1.11
#                 kinematic.mCovariance.mX22 = 2.22
#                 kinematic.mCovariance.mX33 = 3.33
#                 kinematic.mVelocity.mX = 0.0001
#                 kinematic.mVelocity.mY = 0.0002
#                 kinematic.mVelocity.mZ = 0.0003
#                 track.mKinematic = kinematic
#                 shape = ShieldMessages.Shape2D()
#                 shape.mFrame = ShieldMessages.WGS84
#                 shape.mNbTargets = 77
#                 shape.mShape.mX11 = 11
#                 shape.mShape.mX12 = 12
#                 shape.mShape.mX21 = 21
#                 shape.mShape.mX22 = 22
#                 track.mShape = shape
#                 track.mFreeField = "Que j\'aime à faire apprendre un nombre utile aux sages, Immortel Archimède, artiste, ingénieur ..."
                 msg.mTrackList.push_back(track) 
        self.client.Send(msg)
        return    
    def sendStatus(self,_sensor):
          msg           = ShieldMessages.MessageSensorStatus()
          msg.mSensorId = _sensor.id
          msg.mStatus   = ShieldMessages.SENSOR_ALIVE
          print('send status message')
          self.client.Send(msg)
        
    def semanticInformation(self,_sensor,_url):
        msg = ShieldMessages.MessageImagingResult()
        msg.mSensorId   = _sensor.id
        print(_url)
        msg.mURL        = str(_url)
        print('send semantic message')
        self.client.Send(msg)
        print('sended')
    def sendConfiguration(self,nodes = []):
        for _node in dataManager.instance().nodes():
            print('build node message')
            msg = ShieldMessages.MessageRegisterNode()
            
            msg.mNetworkId = ADRESS_IP
            msg.mNodeId    = _node.id
            msg.mNodeName  = _node.name
            if _node.typeNode == 'UNKNOWN':
                msg.mNodeType  = ShieldMessages.UNKNOWN_NODE
            elif _node.typeNode == 'MASTER_NODE':
                msg.mNodeType  = ShieldMessages.FUSION_MASTER_NODE
            elif _node.typeNode == 'SENSOR_NODE':
                msg.mNodeType  = ShieldMessages.SENSOR_NODE
            elif _node.typeNode == 'FUSION_NODE':
                msg.mNodeType  = ShieldMessages.FUSION_SLAVE_NODE
         
           
            orientation     = ShieldMessages.Orientation3D()
            orientation.SetTheta(_node.Orientation.pitch)
            orientation.SetPhi(_node.Orientation.roll)
            orientation.SetPsi(_node.Orientation.yaw)
            msg.mOrientation=orientation

            position        = ShieldMessages.Position3DWGS84()
            position.SetLat(_node.Position.latitude)
            position.SetLon(_node.Position.longitude)
            position.SetAlt(_node.Position.altitude)
            msg.mPosition   = position 
            print('send node message')
            self.client.Send(msg)
            
            for _sensor in _node.sensors:
                msg = ShieldMessages.MessageRegisterSensor()
                
                if  _sensor.mode == SensorMode.nomode :
                    msg.mSensorType = ShieldMessages.UNKNOWN_SENSOR
                if  _sensor.mode == SensorMode.radar :
                    msg.mSensorType = ShieldMessages.ACTIVE_RADAR
                if  _sensor.mode == SensorMode.optroIR :
                    msg.mSensorType = ShieldMessages.PASSIVE_OPTRONIC
                if  _sensor.mode == SensorMode.optroVIS :
                    msg.mSensorType = ShieldMessages.PASSIVE_OPTRONIC
                if  _sensor.mode == SensorMode.accoustic :
                    msg.mSensorType = ShieldMessages.ACOUSTIC   
                if  _sensor.mode == SensorMode.radar3D :
                    msg.mSensorType = ShieldMessages.ACTIVE_RADAR
                if  _sensor.mode == SensorMode.optroIR2D :
                    msg.mSensorType = ShieldMessages.PASSIVE_OPTRONIC
                if  _sensor.mode == SensorMode.gonio:
                    msg.mSensorType = ShieldMessages.RADIOFREQUENCY   
                if  _sensor.mode == SensorMode.alarm:
                    msg.mSensorType = ShieldMessages.RADIOFREQUENCY 
                msg.mNodeId     = _node.id
                msg.mSensorId   = _sensor.id
                msg.mSensorName = _sensor.name
                print('send sensor declaration')
                self.client.Send(msg)
                print('message sended 2')
        
        
                msg = ShieldMessages.MessageSensorPosition()
                msg.mSensorId = _sensor.id
                position  = ShieldMessages.Position3DXYZ()
                position.mX = 0.0
                position.mY = 0.0
                position.mZ = 0.0
                msg.mPosition = position
                msg.mPrecision.mX = 1
                msg.mPrecision.mY = 2
                msg.mPrecision.mZ = 1
                self.client.Send(msg)
                print('message sended 3')
                msg = ShieldMessages.MessageSensorOrientation()
                msg.mSensorId = _sensor.id
                msg.mOrientation.SetPsi(0.0)
                msg.mOrientation.SetTheta(0.0)
                msg.mOrientation.SetPhi(0.0)
                self.client.Send(msg)
                print('message sended 4')
                if _sensor.sensorCoverage != None:
                    for _coverage in _sensor.sensorCoverage:
                        msg = ShieldMessages.MessageSensorFieldOfView()
                        msg.mSensorId = _sensor.id
                        msg.mFieldOfView.SetAzimuthSweep(_coverage.fov)
                        msg.mFieldOfView.SetElevationSweep(_coverage.fov_elevation )
                        msg.mFieldOfView.SetMinRange(_coverage.distanceMin)
                        msg.mFieldOfView.SetMaxRange(_coverage.distanceMax )
                        self.client.Send(msg)
                        print('message sended 5')
                
                
    def run(self):
        print('in run')
        self.client.Run(1)
        
        
class Client(ShieldJsonSocket.JsonClient,QWidget):
    
    #Messagerie
    message         = pyqtSignal('QString') 
    connected       = pyqtSignal()
    disconnected    = pyqtSignal() 
    messageChat     = pyqtSignal(list)
    referencePoint  = pyqtSignal('QString')
    command         = pyqtSignal('QString')
    def __init__(self, client_name, server_address = '127.0.0.1', server_port = 4567):
        ShieldJsonSocket.JsonClient.__init__(self, client_name, server_address, server_port)
        QWidget.__init__(self)

    def OnReceiveCommandFieldOfView(self, msg):

        command =('sensor %r -commandOrientation %r %r')%(msg.mSensorId,msg.mOrientation.GetTheta(),msg.mAzimuthSweep)
        command = command.replace('\'', '')
        print(command)
        self.command.emit(command)
        
    def OnReceiveMessageReferencePoint(self,msg):

        self.referencePoint.emit(('%f %f %f')%(msg.mPosition.mY,msg.mPosition.mX,msg.mPosition.mZ) )
    def OnReceiveCommandStatus(self,msg):
        print('Received CommandStatus (sent at %r) sensor = %s, order = %r' % (msg.GetSendDate().ToString(), msg.mSensorId, msg.mOrder))
                
#    def OnReceiveCommandStatus(self, msg):            
#        print('Received CommandStatus (sent at %r) sensor = %r, order = %r' % (msg.GetSendDate().ToString(), msg.mSensorId, msg.mOrder))
##        print('receive command')
#        print(msg.mOrder)
  
        command =('sensor %s -commandStatus %r')%(str(msg.mSensorId),msg.mOrder)
        print (command)
        self.command.emit(command)  
#        
    def OnReceiveMessageChat(self,msg):
#        print('receive chat message')
#        print(msg.mName)
#        print(msg.mMessage)
#        print(msg.GetSendDate().ToString())
    
        msgList = []
        msgList.append(msg.mName)
        msgList.append(msg.mMessage)
        self.messageChat.emit(msgList)
        
    def OnServerConnection(self):
        # self.GetRecorder().Start('TestJsonClient.html', ShieldJsonSocket.HTML, True)
     
        self.message.emit('connected to shield server')
        self.connected.emit()
 
 
        
    def OnServerDisconnection(self):
        # self.GetRecorder().Stop()
        #self.__message_sender.stop()

        self.message.emit('shield server deconnected')
        self.disconnected.emit()
  
    def OnReceiveMessageTracks(self, msg):
        print('Received MessageTracks (sent at %r) from %r, trackList size = %r' % (msg.GetSendDate().ToString(), msg.mEmitterId, len(msg.mTrackList)))
        for i in range(0, len(msg.mTrackList)):
            track = msg.mTrackList[i]
            print ('- Track %r : %r plots' % (track.mId, len(track.mPlotIdList))) 

 


            
def main(argv=None):
    app = QApplication(sys.argv)
    window = QDialog()
    ui = Ui_Shield()
    ui.setupUi(window)
    ui.pushButton_connect.clicked.connect(self.tryShieldConnection)
    ui.pushButton.clicked.connect(self.tryShieldDisConnection)
    ui.pushButton_sendMessage.clicked.connect(self.shieldChatMessage)
    ui.pushButton_SendConfiguation.clicked.connect(self.sendConfiguration)
    ui.pushButton_NTP.clicked.connect(self.shieldNTP)
    window.show()
    if window.exec_() == QDialog.Accepted  :
        print('debut')
        myclient = Client( 'Client', ui.lineEditIP.text())
        myclient.Run(1)
        print('end')
    sys.exit(app.exec_())
    
if __name__ == "__main__":
    main() 