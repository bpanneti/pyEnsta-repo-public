# -*- coding: utf-8 -*-
"""
Created on Sun Aug  4 08:09:35 2019

@author: bpanneti
"""

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtOpenGL import *
from PyQt5.QtWidgets import *
#from scan import Scan


# from toolTracking.GNNSF_cmkf import GNNSF_cmkf
# from toolTracking.GNNSF_imm import GNNSF_imm
# from toolTracking.GMPHD import GMPHD
# from toolTracking.PDAF_cmkf import PDAF_cmkf

#from tool_tracking.rmkf import rmkf
#from tool_tracking.sir import Sir, Infos
# from tool_tracking.PMBM import PMBM
#from toolTracking.imm import imm
#from tool_tracking.pf import pf
# from tool_tracking.PMBM_RM import PMBM_RM
from toolTracking.utils import  StateType
from itertools import count
from utils import isInteger, isNumber
 

from collections import namedtuple
from enum import Enum

from toolTracking.cmkf import cmkf
# from toolTracking.ekf  import ekf
# from toolTracking.imm  import imm
# from toolTracking.gnnsf  import gnnsf
# from toolTracking.sda  import sda

TYPE  = namedtuple('trackerType', ['id', 'name','function'])
class TRACKER_TYPE(Enum):
    UNKNOWN     = TYPE(0,'UNKNOWN','')
    CMKF        = TYPE(1,'CMKF',cmkf)
    # EKF         = TYPE(2,'EKF',ekf)
    # IMM         = TYPE(3,'IMM',imm)
    # GNNSF       = TYPE(4,'GNNSF',gnnsf)
    # SDA         = TYPE(5,'SDA',sda)
 
  
def has_method(o, name):
    return callable(getattr(o, name, None)) 
def index_of(val, in_list):
    try:
        return in_list.index(val)
    except ValueError:
        return -1


class Tracker(QObject):
    message = pyqtSignal('QString')
    tracks_updated = pyqtSignal(list)
    tracks_display = pyqtSignal(list)
    gauss_display  = pyqtSignal()
    emitTracks     = pyqtSignal(list) 
    __cnt = count(0)

    def __init__(self):
        super(Tracker, self).__init__()
    
        self.id = next(self.__cnt)  # id du tracker
        self.tracks = []  # liste des pistes
        self.filter = TRACKER_TYPE.UNKNOWN  # type du tracker
        self.sensors = []  # liste des capteurs associés au tracker
        self.node = None
        self.id_node = None
        self.name = 'no name'

        # Objet Tracker
        self.tracker      = None
        self.trackerInfos = None
        self.currentScan  =  None
        # tracker sur cibles sélectionnées
        # ne fonctionne que si les plots sint associés à l'identifiant des cibles

        self.targets = []

        # capteurs associés au tracker
        # liste des capteurs pour lesquels le tracker traite les plots

 
        # éléments graphiques
        self.axes = None
        self.canvas = None
        self.treeWidgetItem = None
        self.trajObj = None
        self.textObj = None
        self.displayTrackFig       = True
        self.displayCovariancekFig = True
        self.displayIconeFig       = True
        
        self.color = QColor(Qt.darkGreen)

        self.mutex = QMutex()

        self.sec = 0 #c'est l'arnaque
    
        self.thread = QThread()

        self.thread.started.connect(self.run)  
    
    def editTracker(self, _targets=[], _sensors=[]):
        self.d = QDialog()

        layout = QVBoxLayout()

        trackerName = QLabel('tracker name')
        filerName = QLabel('filter name')
        selectedTargets = QLabel('selected targets')
        selectedSensors = QLabel('selected sensors')
        filtrageParticulaire = QLabel('Particle filter')
        numberSamples = QLabel('Number of samples (int)')
        threshold = QLabel('Threshold (float, int)')

        

        self.trakerNameEdit = QLineEdit()

        if self.name != '':
            self.trakerNameEdit.setText(self.name)

        self.trakerFilterEdit = QComboBox()

        for type_t in TRACKER_TYPE:
            self.trakerFilterEdit.addItem("%s" % type_t.name)

        if self.filter:
            self.trakerFilterEdit.setCurrentText("%s" % self.filter.name)

        # liste des capteurs associés

        self.ComboBoxCapteurs = CheckableComboBox()
        self.ComboBoxCapteurs.setEditable(True)
        self.tmp_sensors = _sensors
        #self.ComboBoxCapteurs.addItem('sensors') 
        for i in range(0, len(_sensors)):
            _sensor = _sensors[i]
            self.ComboBoxCapteurs.addItem(
                "sensor : " + str(_sensor.id)+" "+str(_sensor.name))
            item = self.ComboBoxCapteurs.model().item(i, 0)
            if self.sensors != [] and index_of(_sensor, self.sensors) != -1:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
                # liste des capteurs associés

        self.ComboBoxTargets = CheckableComboBox()
        self.ComboBoxTargets.setEditable(True)
        self.tmp_targets = _targets
        #self.ComboBoxTargets.addItem('targets') 
        for i in range(0, len(_targets)):
            _target = _targets[i]
            self.ComboBoxTargets.addItem(
                "target : " + str(_target.id)+" "+str(_target.name))
            item = self.ComboBoxTargets.model().item(i, 0)

            if self.tracker != None and index_of(_target.id, self.tracker.targets) != -1:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)

        self.numberSamplesEdit = QLineEdit()
        self.thresholdEdit = QLineEdit()
        self.numberSamplesEdit.setReadOnly(True)
        self.thresholdEdit.setReadOnly(True)

        # if self.filter == TRACKER_TYPE.SIR:
        #     self.numberSamplesEdit.setReadOnly(False)
        #     self.thresholdEdit.setReadOnly(False)

#        if isinstance(self.trackerInfos, Infos):
#            self.numberSamplesEdit.setText("{}".format(self.trackerInfos.samplesNumber))
#            self.thresholdEdit.setText("{}".format(self.trackerInfos.threshold))


        #====Outils graphiques
        
        self.checkBox_cov   =QCheckBox()
 
        self.checkBox_cov.clicked.connect(self.displayCovariance) 
        
        if self.displayCovariancekFig:
            self.checkBox_cov.setCheckState(Qt.Checked)
        else:
            self.checkBox_cov.setCheckState(Qt.Unchecked )
            
        self.checkBox_track =QCheckBox()
        
        self.checkBox_track.clicked.connect(self.displayTrack) 
        if self.displayTrackFig:
            self.checkBox_track.setCheckState(Qt.Checked)
        else:
            self.checkBox_track.setCheckState(Qt.Unchecked)

        self.checkBox_icone   =QCheckBox()

        if self.displayIconeFig:
            self.checkBox_icone.setCheckState(Qt.Checked)
        else:
            self.checkBox_icone.setCheckState(Qt.Unchecked)
            
        self.checkBox_icone.clicked.connect(self.displayIcone) 












        self.trakerFilterEdit.currentIndexChanged.connect(self.onParticleFilter)

        grid = QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(trackerName, 1, 0)
        grid.addWidget(self.trakerNameEdit, 1, 1)
        grid.addWidget(filerName, 2, 0)
        grid.addWidget(self.trakerFilterEdit, 2, 1)
        grid.addWidget(selectedSensors, 3, 0)
        grid.addWidget(self.ComboBoxCapteurs, 3, 1)
        grid.addWidget(selectedTargets, 4, 0)
        grid.addWidget(self.ComboBoxTargets, 4, 1)
        grid.addWidget(filtrageParticulaire, 5, 0, 1, 2, Qt.AlignHCenter)
        grid.addWidget(numberSamples,6,0)
        grid.addWidget(self.numberSamplesEdit,6,1)
        grid.addWidget(threshold,7,0)
        grid.addWidget(self.thresholdEdit,7,1)
        
        
        grid.addWidget(QLabel('display covariance'), 8, 0)
        grid.addWidget(self.checkBox_cov, 8, 1)
        grid.addWidget(QLabel('display track'), 9, 0)
        grid.addWidget(self.checkBox_track, 9, 1)
        grid.addWidget(QLabel('display covariance'), 8, 0)
        grid.addWidget(self.checkBox_cov, 8, 1)
        grid.addWidget(QLabel('display icone'), 10, 0)
        grid.addWidget(self.checkBox_icone, 10, 1)
        
        layout.addLayout(grid)

        buttonLayout = QHBoxLayout()
        but_ok = QPushButton("OK")
        buttonLayout.addWidget(but_ok)
        but_ok.clicked.connect(self.onOk)

        but_cancel = QPushButton("Cancel")
        buttonLayout.addWidget(but_cancel)
        but_cancel.clicked.connect(self.onCancel)

        layout.addLayout(buttonLayout)

        self.d.setLayout(layout)
        self.d.setGeometry(300, 300, 350, 300)
        self.d.setWindowTitle("edit tracker")
        self.d.setWindowIcon(QIcon('icones/tracker.png'))
        self.d.setWindowModality(Qt.ApplicationModal)

        return self.d.exec_()

    def onParticleFilter(self):
        self.filter = TRACKER_TYPE[self.trakerFilterEdit.currentText()]

        # if TRACKER_TYPE.SIR == self.filter:
        #     self.numberSamplesEdit.setReadOnly(False)  
        #     self.thresholdEdit.setReadOnly(False) 
        # else:
        self.numberSamplesEdit.setReadOnly(True)  
        self.thresholdEdit.setReadOnly(True) 
        
    def onCancel(self):
        self.d.close()
 
    def displayCovariance(self):
         if self.checkBox_cov.isChecked():
           self.displayCovariancekFig = True
         else : 
             self.displayCovariancekFig = False
    def  displayIcone(self):
         if self.checkBox_icone.isChecked():
           self.displayIconeFig = True
         else : 
             self.displayIconeFig = False
             
    def  displayTrack(self):
         if self.checkBox_track.isChecked():
           self.displayTrackFig = True
         else : 
             self.displayTrackFig = False
    def receiveSensors(self,sensors):

        if self.filter == TRACKER_TYPE.GMPHD and  self.trackerInfos ==None :
            for _sensor in self.sensors:            
                    self.trackerInfos     = _sensor
                    self.tracker.polygons = _sensor.toPolygon()
                    break 
    def onOk(self):
 
        self.sensors.clear()
        self.targets.clear()
        self.name = self.trakerNameEdit.text()

        if self.numberSamplesEdit.text() == '' or not isInteger(self.numberSamplesEdit.text()):
            self.numberSamplesEdit.setText('1')
        if self.thresholdEdit.text() == '' or not isNumber(self.thresholdEdit.text()):
            self.thresholdEdit.setText('0')

     
        # if self.filter == TRACKER_TYPE.SIR:
        #     self.trackerInfos = Infos(int(self.numberSamplesEdit.text()),float(self.thresholdEdit.text()))
        

            
        for index in range(self.ComboBoxCapteurs.model().rowCount()):
            item = self.ComboBoxCapteurs.model().item(index)
            if item.checkState() == Qt.Checked:
                self.sensors.append(self.tmp_sensors[index])
     
        
        # if self.filter == TRACKER_TYPE.GMPHD:
        #     for _sensor in self.sensors:            
        #             self.trackerInfos = _sensor
                    
        for index in range(self.ComboBoxTargets.model().rowCount()):
            item = self.ComboBoxTargets.model().item(index)
            if item.checkState() == Qt.Checked:
                self.targets.append(self.tmp_targets[index].id)

        self.loadTracker()

        self.update()
        self.d.close()

    def loadTracker(self):
        idTargets = []
        
    

        if self.filter == TRACKER_TYPE.UNKNOWN:
            print("\nNo tracker is selected\n")
            return
    
        # if self.filter == TRACKER_TYPE.GMPHD:
        #     for _sensor in self.sensors:            
        #             self.trackerInfos = _sensor
       
        self.tracker =  self.filter.value.function()

     
        # self.tracker.moveToThread(self.thread)
        # self.thread.started.connect(self.tracker.run)
        
#        my_thread.start.connect(self.tracker.run)
        for target in self.targets:
            idTargets.append(target)

        self.tracker.setTargets(idTargets)

        if self.tracker != None:
            self.tracker.message.connect(self.receiveMessage)
   
    def update(self):
     
        if self.treeWidgetItem==None:
            return
        
        self.treeWidgetItem.setText(1,self.name)
        self.treeWidgetItem.setText(2,self.filter.name)
 
    def isScanFromSelectedSensor(self,idSensor):
        for _sensor in self.sensors:
            if str(_sensor.id) == str(idSensor):
                return True
        return False
    def run(self):
 
            _tracks = []
            _gauss  = []
            if self.currentScan!=None:
                #print('---------------------->')
                if self.mutex.tryLock() :
                    if self.tracker !=None and self.isScanFromSelectedSensor(self.currentScan.sensor.id):
                            self.tracker.receiveScan(self.currentScan)
                    if self.tracker !=None:
                        _tracks = self.tracker.getTracks()
                        
                        if has_method(self.tracker,'getGauss'):  
                            _gauss = self.tracker.getGauss() 
                        
                    for _t in _tracks : 
                        #A modifier c'est moche utilisé ici pour la fonction saveTracks dans saver.py
                        _t.id_node = self.node.id
                  
                    self.mutex.unlock()
                
            if _tracks :
                #self.tracks_updated.emit(self)
            
                self.tracks_display.emit(_tracks)
                self.emitTracks.emit(_tracks)     
            if _gauss :
                
                self.gauss_display.emit()
                
            self.currentScan = None
    def receiveScan(self,_scan): 
        
        if self.mutex.lock():
             return
        self.currentScan = _scan
            
        self.mutex.unlock()
        
        self.run()
    def receiveOmwnTracks(self,_tracks = []):
        pass
    def receiveTracks(self,idNode,_tracks = []):
        
        print(['--> receive', len(_tracks),' from node',idNode])
        pass
    def receiveScans(self,scans = []):
     
        for _scan in scans:

            if self.tracker !=None and self.isScanFromSelectedSensor(_scan.sensor.id):
                self.tracker.receiveScan(_scan)
               
    def start(self):
        self.thread.start()
        if self.tracker!=None:
            self.tracker.updatedTracks.connect(self.receiveOmwnTracks)
            
    def pause(self):   
        self.thread.terminate()
        while not self.thread.isFinished():
            pass          
    def stop(self):   
        self.thread.terminate()
        while not self.thread.isFinished():
            pass
        if self.tracker != None:
            self.tracker.clear()
     
    def displayTracks(self,axes=None,canvas=None):
        self.axes      = axes
        self.canvas    = canvas
        if self.node == None:
            return
        # print('in display track 1')
#        if self.mutex.tryLock()==False:
#            return
        # recupération des tracks
        if self.tracker!=None:
            # print('in display track')
            tracks =  self.tracker.getTracks()
            for _track in tracks:
 
                _track.displayTrack(axes,canvas,self.displayTrackFig,self.displayCovariancekFig,self.displayIconeFig)
        #self.mutex.unlock()
    
    def toDisplay(self,axes=None,canvas=None):
        self.axes      = axes
        self.canvas    = canvas
        if self.node == None:
            return
      
        if self.node.Position.latitude ==[] or  self.node.Position.longitude == []:
            return
        latitude  = self.node.Position.latitude  + 0.001
        longitude = self.node.Position.longitude - 0.001
        altitude  = self.node.Position.altitude
        
  
        # ==================
        # objet position
        # ==================
 
        if self.trajObj !=None:
            axes.lines.remove(self.trajObj)
            self.trajObj = None  
            
        self.trajObj, = axes.plot(longitude, latitude, color = self.color.name(), linewidth= 2) 

        # ==================
        # objet text
        # ==================

        if self.textObj !=None:
            self.textObj.remove()
            self.textObj = None  

        self.textObj  = axes.text(longitude,latitude , 'tracker : '+ str(self.id), bbox={'facecolor':'white', 'alpha':0.5, 'pad':10})

    def receiveMessage(self,_message):
        self.message.emit(_message)
 
         

         
class CheckableComboBox(QComboBox):
    def __init__(self):
        super(CheckableComboBox, self).__init__()
        self.view().pressed.connect(self.handleItemPressed)
        self.setModel(QStandardItemModel(self))

    def handleItemPressed(self, index):
        item = self.model().itemFromIndex(index)
        if item.checkState() == Qt.Checked:
            item.setCheckState(Qt.Unchecked)
        else:
            item.setCheckState(Qt.Checked)
