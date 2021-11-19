# -*- coding: utf-8 -*-
"""
Created on Sun Dec 22 23:00:29 2019

@author: benja
"""
 
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtOpenGL import *
from PyQt5.QtWidgets import *
#import os, sys
#sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from loader import data as dataBase
from scan import PLOTType
from point import Position,utm_getZone,utm_isNorthern,utm_isDefined,REFERENCE_POINT 

from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)
from matplotlib.patches import Rectangle
from matplotlib.collections import PatchCollection
from matplotlib.figure import Figure
from matplotlib.backend_bases import key_press_handler

from metrics.gospa_ospa import gospa_ospa_distances
import matplotlib.dates as mdates
import array as arr
 
import numpy as np
import os

from distutils.dir_util import copy_tree
from xml.dom import minidom

from scipy.optimize import linear_sum_assignment

from metrics.targetMOP import classTaxonomie
from metrics.targetMOP import windows_Mop
from metrics.targetMOP import target_Mop
from metrics.globalMOP import window_globalMOP, MCMC_Mop
 
from Managers.dataManager import DataManager as dataManager

class ProgressBar(QWidget):
    def __init__(self, parent=None, total=20):
        super(ProgressBar, self).__init__(parent)
        self.name_line = QLineEdit()

        self.progressbar = QProgressBar()
        self.progressbar.setMinimum(1)
        self.progressbar.setMaximum(total)

        main_layout = QGridLayout()
        main_layout.addWidget(self.progressbar, 0, 0)

        self.setLayout(main_layout)
        self.setWindowTitle("data reading...")

    def update_progressbar(self, val):
        self.progressbar.setValue(val)
        QApplication.processEvents()

def lines_that_contain(string, fp):
    return [line for line in fp if string in line]

#=================
# kml tool
#=================
 
import simplekml



   
class MOPComparison(QWidget):
     message = pyqtSignal('QString');
    
     def __init__(self, parent=None):
         QWidget.__init__(self, parent=parent) 
         
         self.windowMop                      = [] #classe qui gère l'affichage es Mop
         self.mopTargets                     = [] #MOP de chaque target
         self.window_globalMOP               = window_globalMOP() #MCMC_Mop() 
         
         self.currentDataBase                = dataBase()
         self.currentDataBase.referencePoint.connect(self.receiveReferencePoint)
 
         
         
         self.path_1 = QLineEdit() #chemin vers le répertoire contenant les bases de données
         self.path_2 = QLineEdit() #chemin vers le répertoire contenant les bases de données
         self.path_3 = QLineEdit() #chemin vers le répertoire contenant les bases de données
         self.path_4 = QLineEdit() #chemin vers le répertoire contenant les bases de données
         self.path_5 = QLineEdit() #chemin vers le répertoire contenant les bases de données
          
          
         layout                             = QVBoxLayout()
         layoutPath_1                       = QHBoxLayout()
         path_1                             = QLabel('MOP file s path 1')
         buttonPath_1                       = QPushButton()
         buttonPath_1.setIcon(QIcon('icones/folder.png'))
         buttonPath_1.clicked.connect(self.EditPath_1)
         layoutPath_1.addWidget(path_1)
         layoutPath_1.addWidget(self.path_1)
         layoutPath_1.addWidget(buttonPath_1)
         layout.addLayout(layoutPath_1)
         
         layoutPath_2                       = QHBoxLayout()
         path_2                             = QLabel('MOP file s path 2')
         buttonPath_2                       = QPushButton()
         buttonPath_2.setIcon(QIcon('icones/folder.png'))
         buttonPath_2.clicked.connect(self.EditPath_2)
         layoutPath_2.addWidget(path_2)
         layoutPath_2.addWidget(self.path_2)
         layoutPath_2.addWidget(buttonPath_2)
         layout.addLayout(layoutPath_2)
         
         
         
         layoutPath_3                       = QHBoxLayout()
         path_3                             = QLabel('MOP file s path3')
         buttonPath_3                       = QPushButton()
         buttonPath_3.setIcon(QIcon('icones/folder.png'))
         buttonPath_3.clicked.connect(self.EditPath_3)
         layoutPath_3.addWidget(path_3)
         layoutPath_3.addWidget(self.path_3)
         layoutPath_3.addWidget(buttonPath_3)
         layout.addLayout(layoutPath_3)
       
         layoutPath_4                       = QHBoxLayout()
         path_4                             = QLabel('MOP file s path4')
         buttonPath_4                       = QPushButton()
         buttonPath_4.setIcon(QIcon('icones/folder.png'))
         buttonPath_4.clicked.connect(self.EditPath_4)
         layoutPath_4.addWidget(path_4)
         layoutPath_4.addWidget(self.path_4)
         layoutPath_4.addWidget(buttonPath_4)
         layout.addLayout(layoutPath_4)
         
         
         layoutPath_5                       = QHBoxLayout()
         path_5                             = QLabel('MOP file s path5')
         buttonPath_5                       = QPushButton()
         buttonPath_5.setIcon(QIcon('icones/folder.png'))
         buttonPath_5.clicked.connect(self.EditPath_5)
         layoutPath_5.addWidget(path_5)
         layoutPath_5.addWidget(self.path_5)
         layoutPath_5.addWidget(buttonPath_5)
         layout.addLayout(layoutPath_5)
         
         self.setLayout(layout)
         self.setGeometry(300, 300, 350, 300)
         self.setWindowTitle("MOPs comparison")
         self.setWindowIcon(QIcon('icones/diagram.png'))
        
         buttonLayout = QHBoxLayout();  
         but_ok = QPushButton("Compute")
         buttonLayout.addWidget(but_ok )
         but_ok.clicked.connect(self.OnOk)
         but_cancel = QPushButton("Cancel")
         buttonLayout.addWidget(but_cancel )
         but_cancel.clicked.connect(self.OnCancel)
          
         layout.addLayout(buttonLayout)
     def receiveReferencePoint(self, pt   ) :
        
            strlist = pt.split(" ") 
            REFERENCE_POINT.setWGS84(float(strlist[0]),float(strlist[1]),float(strlist[2]))

            utm_getZone(float(strlist[0]))
            utm_isNorthern(float(strlist[1]))
     def receiveMessage(self,_message=''):
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText(_message)
            msg.setWindowTitle("Warning")
            msg.setStandardButtons(QMessageBox.Ok )
            msg.exec_()
        
     def OnOk(self):
         print('in reload MOP')
         # save np.load
         np_load_old = np.load

         # modify the default parameters of np.load
         np.load = lambda *a,**k: np_load_old(*a, allow_pickle=True, **k)

         mainPaths = []
         mainPaths.append(self.path_1.text())
         mainPaths.append(self.path_2.text())
         mainPaths.append(self.path_3.text())
         mainPaths.append(self.path_4.text())
         mainPaths.append(self.path_5.text())
                
         #==================
         # load target
         #==================
         if self.path_1.text()=='':
             self.receiveMessage ("Cannot open empty directory")
             return;
             
         _dir = QDir(self.path_1.text())
    
         if not _dir.exists():
             self.receiveMessage ("Cannot find the example directory")
             return;
 
         _filter =[]
         _filter.append("*.db")
#         self.receiveMessage("number of files: %s"%len(_dir.entryInfoList(_filter)));
   
         if len(_dir.entryInfoList(_filter))>= 1:
            self.currentDataBase.loadData(_dir.entryInfoList(_filter)[0].absoluteFilePath())
            
         for _target in dataManager.instance().targets():       
            self.windowMop.append(windows_Mop())
        
         #==================
         # display globalMop
         #==================
         
         for mainPath in mainPaths:
             if mainPath == '':
                 continue 
             
             _dir = os.listdir(mainPath)
             
             u = 0
             
             for _rep in  _dir :
                 path = mainPath+str("/")+_rep
         
         
                 if os.path.isdir(path):
                     
                     print(path)
                     mcmc = MCMC_Mop(_rep)
                    
                     _timeLine = np.load(path+str("/")+'timeLine.npy') 
             
                     mcmc.setTimeLine(_timeLine) 
                     mcmc.NVT               = np.load(path+str("/")+'nvt.npy') 
                     mcmc.NMT               = np.load(path+str("/")+'nmt.npy') 
                     mcmc.NFT               = np.load(path+str("/")+'nft.npy')
                     mcmc.MOC               = np.load(path+str("/")+'moc.npy')
                     mcmc.ANST              = np.load(path+str("/")+'ANST.npy')
                     mcmc.NB_MCMC           = np.load(path+str("/")+'NB_MCMC.npy')
                     mcmc.NMT               = np.load(path+str("/")+'nmt.npy')
                     mcmc.ToE               = np.load(path+str("/")+'ToE.npy')
                     mcmc.Packet_Track      = np.load(path+str("/")+'Packet_Track.npy')
                     mcmc.Packet_Received   = np.load(path+str("/")+'Packet_Received.npy')
                     mcmc.OSPA = np.load(path+str("/")+'OSPA.npy')
                     self.window_globalMOP.globalMOP.append(mcmc)
                     self.mopTargets.append([_rep,[]])
                     for _target,i in zip(dataManager.instance().targets(),range(0,len(dataManager.instance().targets()))):
                         _localMop           = target_Mop(_target)
                         _localMop.setTimeLine(_timeLine) 
                         #_localMop.setRun(self.mopGlobal.NB_MCMC)
                         _localMop.targetDetection       =      np.load(path+str("/")+'target_%s_targetDetection.npy'%_target.id)
                         _localMop.locationError         =      np.load(path+str("/")+'target_%s_locationError.npy'%_target.id)
                         _localMop.velocityError         =      np.load(path+str("/")+'target_%s_velocityError.npy'%_target.id)
                         _localMop.correctClassificationProbability      = np.load(path+str("/")+'target_%s_correctClassificationProbability.npy'%_target.id)
                         _localMop.classificationProbability             = np.load(path+str("/")+'target_%s_classificationProbability.npy'%_target.id)
                         _localMop.associatedTrack                       = np.load(path+str("/")+'target_%s_associatedTrack.npy'%_target.id)
                         _localMop.nbAssociatedTarget                    = np.load(path+str("/")+'target_%s_nbAssociatedTarget.npy'%_target.id)
                         _localMop.detectionProbability                  = np.load(path+str("/")+'target_%s_detectionProbability.npy'%_target.id)
                         _localMop.trackContinuity                       = np.load(path+str("/")+'target_%s_trackContinuity.npy'%_target.id)
                         self.windowMop[i].target_mops.append(_localMop) 
                         self.mopTargets[u][1].append(_localMop)
                     u +=1
               
           
         #======================
         # display global mops
         #======================
         self.window_globalMOP.displayNumberOfValidTrack()   
         self.window_globalMOP.displayCompletness()
         self.window_globalMOP.displayOSPA()
         #self.window_globalMOP.displayTrackContinuity(self.mopTargets)
         #self.window_globalMOP.displayClassificationProbability(self.mopTargets[indiceTracker][1])
         self.window_globalMOP.displayPacketSize()
         self.window_globalMOP.displayExecutionTime()
         
         for _mop in self.windowMop:
                _mop.displayLocationError()
                _mop.displayVelocityError()
    


  
 
         # restore np.load for future normal usage
         np.load = np_load_old
         
         
         #=====================#
         # nettoyage
         #=====================#
     def nettoyage(self):
        dataManager.instance().removeNodes()
        dataManager.instance().removeTargets()
 
        
         
     def OnCancel(self):
         self.close()
         self.nettoyage
     def EditPath_1(self):
            #self.clearAll()
            folder = QFileDialog.getExistingDirectory(None, "Select computed MOPs folder 1", '.')
            if not folder :
                 folder =  folder  + "/"   
         
            self.path_1.setText(folder)
 
     def EditPath_2(self):
            #self.clearAll()
            folder = QFileDialog.getExistingDirectory(None, "Select computed MOPs folder 2", '.')
            if not folder :
                 folder =  folder  + "/"   
         
            self.path_2.setText(folder)      
     def EditPath_3(self):
            #self.clearAll()
            folder = QFileDialog.getExistingDirectory(None, "Select computed MOPs folder 3", '.')
            if not folder :
                 folder =  folder  + "/"   
         
            self.path_3.setText(folder)   
     def EditPath_4(self):
            #self.clearAll()
            folder = QFileDialog.getExistingDirectory(None, "Select computed MOPs folder 4", '.')
            if not folder :
                 folder =  folder  + "/"   
         
            self.path_4.setText(folder)        
     def EditPath_5(self):
            #self.clearAll()
            folder = QFileDialog.getExistingDirectory(None, "Select computed MOPs folder 5", '.')
            if not folder :
                 folder =  folder  + "/"   
         
            self.path_5.setText(folder)     


class MOP(QWidget):
     message = pyqtSignal('QString');
    
     def __init__(self, parent=None):
         QWidget.__init__(self, parent=parent) 
         self.path = QLineEdit() #chemin vers le répertoire contenant les bases de données
         self.taonomieFile = QLineEdit() #chemin vers le fichier contenant la taxonomie
#         self.performanceSizeFile   = QLineEdit() #chemin vers le fichier contenant la taxonomie
#         self.performanceTimeFile   = QLineEdit() #chemin vers le fichier contenant la taxonomie
         self.checkBox_LocationError         = QCheckBox("error in location")
         self.checkBox_LocationError.setChecked(True) 
         self.checkBox_VelocityError         = QCheckBox("error in velocity")
         self.checkBox_VelocityError.setChecked(True) 
         self.checkBox_Velocity         = QCheckBox("mean velocity")
         self.checkBox_Velocity.setChecked(True) 
         
   
         
         self.checkBox_RLP                   = QCheckBox("cardinality metrics")
         self.checkBox_RLP.setChecked(True) 
         self.checkBox_TauxCouvertureSene    = QCheckBox("track continuity")
         self.checkBox_TauxCouvertureSene.setChecked(True) 
         self.checkBox_TauxCompletude        = QCheckBox("measure of completness")
         self.checkBox_TauxCompletude.setChecked(True) 
         self.checkBox_TrackClassification   = QCheckBox("track classification")
         self.checkBox_TrackClassification.setChecked(True) 
         self.checkBox_Ospa                  = QCheckBox("OSPA metric")
         self.checkBox_Ospa.setChecked(True) 
         
         self.checkBox_TimeProcessing        = QCheckBox("time processing")
         self.checkBox_TimeProcessing.setChecked(True) 
         self.checkBox_PacketSize            = QCheckBox("packet size")
         self.checkBox_PacketSize.setChecked(True)
         
         #connect 
         
         self.checkBox_LocationError.clicked.connect(self.displayLocationError)
         self.checkBox_VelocityError.clicked.connect(self.displayVelocityError)
         self.checkBox_Velocity.clicked.connect(self.displayVelocity)
         self.checkBox_RLP.clicked.connect(self.displayCardinality)
         self.checkBox_TauxCompletude.clicked.connect(self.displayCompletness)
         self.checkBox_TauxCouvertureSene.clicked.connect(self.displayTrackContinuity)
         self.checkBox_TrackClassification.clicked.connect(self.displayTrackClassification)
         self.checkBox_Ospa.clicked.connect(self.displayOSPA)
         self.checkBox_PacketSize.clicked.connect(self.displayPacketSize)
         self.checkBox_TimeProcessing.clicked.connect(self.displayExecutionTime)
 
         
         self.startDateTime                  = QDateTimeEdit()
         self.endDateTime                    = QDateTimeEdit()
         self.textEdit                       = QTextEdit()
         self.comboBox                       = QComboBox()
         self.buttonGEARTH                   =  QPushButton('Export Kml')
         requestLabel                        = QLabel('track request (condition)') 
         self.requestEdit                    = QLineEdit()
          
         #current dataBase
         
         self.currentDataBase                = dataBase()
         self.threadLoader = QThread()
         self.currentDataBase.moveToThread(self.threadLoader)
         self.threadLoader.start()
        
         self.currentDataBase.message.connect(self.receiveMessage)
         self.currentDataBase.referenceTime.connect(self.receiveReferenceTime)
         self.currentDataBase.endTime.connect(self.receiveEndTime)
         self.currentDataBase.referencePoint.connect(self.receiveReferencePoint)
         self.currentDataBase.emitTargets.connect(self.receiveTargets)
  
 
         #tracks
         
         self.currentTracks                  = []
         
  
         
         #MOP par cibles et globales 
         
         #Pour chaque tracker une mop 
         #[id_tracker, MopGlobal]
         #[id_tracker, mopTargets]
         
         self.windowMop                      = [] #classe qui gère l'affichage es Mop
         self.mopTargets                     = [] #MOP de chaque target
         self.window_globalMOP               = window_globalMOP() #MCMC_Mop() 
                  
         #map per base
         
         #self.newMap()
        
        #class taxnomie
        
         self.classTaxonomie                 = classTaxonomie()
         
         #file time perforamcnes
         
         self.TimeFilePerformances           = None
         
         #file packet size performances
         
         self.PacketSizeFilePerformances     = None
         #visu rapide de la base
         self.mapWidget = QWidget()
         self.mapWidget.hide()
         
         
         #===================
         # nex w figure
         #===================
         self.axes                           = None
         
     #def editMOP(self): 
    
          
        
         layout                         = QVBoxLayout()
         layoutPath                     = QHBoxLayout()
         path                           = QLabel('database path')
         buttonPath                     = QPushButton()
         buttonPath.setIcon(QIcon('icones/folder.png'))
         buttonPath.clicked.connect(self.EditPath)
         
         layoutPath.addWidget(path)
         layoutPath.addWidget(self.path)
         layoutPath.addWidget(buttonPath)
         layout.addLayout(layoutPath)
         #informations
         
         
         
         font = QFont()
         font.setFamily('Lucida')
         font.setFixedPitch(True)
         font.setPointSize(10)
         font.setBold(True)
         self.textEdit.setFont(font)
         self.textEdit.setReadOnly(True)
         layoutTexEdit = QHBoxLayout() 
         layoutTexEdit.addWidget(self.textEdit)
         layout.addLayout(layoutTexEdit)
         #plage de temps
          
         layoutTime                     = QHBoxLayout()
         startTime                           = QLabel('start time:')
         endTime                             = QLabel('end time:')
         layoutTime.addWidget(startTime)
         layoutTime.addWidget(self.startDateTime)
         layoutTime.addWidget(endTime)
         layoutTime.addWidget(self.endDateTime)
         layout.addLayout(layoutTime)
         
         self.startDateTime.setEnabled(False)
         self.endDateTime.setEnabled(False)

         layoutRequest              = QHBoxLayout()
         layoutRequest.addWidget(requestLabel)
         layoutRequest.addWidget(self.requestEdit)
         layout.addLayout(layoutRequest)
         #♦display selected base
         layoutDisplay                     = QHBoxLayout()
         self.comboBox.addItem("no table")
         self.comboBox.setEnabled(False)
         layoutDisplay.addWidget(QLabel("diaplay table :"))
         layoutDisplay.addWidget(self.comboBox)
 
         self.buttonGEARTH.setEnabled(False)
         layoutDisplay.addWidget(self.buttonGEARTH)
         layout.addLayout(layoutDisplay)
         #liste des MOPS
         
         layout.addWidget(self.checkBox_LocationError)
         layout.addWidget(self.checkBox_VelocityError)
         layout.addWidget(self.checkBox_Velocity)
         layout.addWidget(self.checkBox_RLP)
         layout.addWidget(self.checkBox_TauxCouvertureSene)
         #layout.addWidget(self.checkBox_TauxFaussesPistes)
         layout.addWidget(self.checkBox_TauxCompletude)
         layout.addWidget(self.checkBox_Ospa)
         layout.addWidget(self.checkBox_TrackClassification)
         layout.addWidget(self.checkBox_TimeProcessing)
         layout.addWidget(self.checkBox_PacketSize)
         self.setLayout(layout)
         self.setGeometry(300, 300, 350, 300)
         self.setWindowTitle("MOP")
         self.setWindowIcon(QIcon('icones/diagram.png'))
         #self.dialog.setWindowModality(Qt.ApplicationModal)
         
         
         #----------------------------------
         # Class Taxonomie file
        
         layoutPath2                     = QHBoxLayout()
         path2                           = QLabel('taxonomie file')
         buttonPath2                     = QPushButton()
         buttonPath2.setIcon(QIcon('icones/folder.png'))
         buttonPath2.clicked.connect(self.EditTaxonomie)
         
         layoutPath2.addWidget(path2)
         layoutPath2.addWidget(self.taonomieFile )
         layoutPath2.addWidget(buttonPath2)
         layout.addLayout(layoutPath2)
         #------------------------------------------
         # performances files
         #----------------------------------
#         layoutPath3                     = QHBoxLayout()
#         path3                           = QLabel('exchange packet size file')
#         buttonPath3                     = QPushButton()
#         buttonPath3.setIcon(QIcon('icones/folder.png'))
#         buttonPath3.clicked.connect(self.EditSizePerformances)
#         
#         layoutPath3.addWidget(path3)
#         layoutPath3.addWidget(self.performanceSizeFile )
#         layoutPath3.addWidget(buttonPath3)
#         layout.addLayout(layoutPath3)
#         
#         layoutPath4                     = QHBoxLayout()
#         path4                           = QLabel('computation time file')
#         buttonPath4                     = QPushButton()
#         buttonPath4.setIcon(QIcon('icones/folder.png'))
#         buttonPath4.clicked.connect(self.EditTimePerformances)
#         
#         layoutPath4.addWidget(path4)
#         layoutPath4.addWidget(self.performanceTimeFile)
#         layoutPath4.addWidget(buttonPath4)
#         layout.addLayout(layoutPath4)
         #------------------------------------------
         
         buttonLayout = QHBoxLayout();
         but_ok = QPushButton("Compute")
         buttonLayout.addWidget(but_ok )
         but_ok.clicked.connect(self.OnOk)
         but_cancel = QPushButton("Cancel")
         buttonLayout.addWidget(but_cancel )
         but_cancel.clicked.connect(self.OnCancel)
        
         layout.addLayout(buttonLayout)
         
         self.existingMopFile = False; 
     def closeEvent(self,event):
    
        reply =  QMessageBox.question(self, 'Message',
            "Are you sure to quit?", QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
            
            for _mop in self.windowMop:
                    _mop.locationErrorWidget.close()
                    _mop.velocityErrorWidget.close()
             
            if self.window_globalMOP:
                self.window_globalMOP.widgetCompletness.close()
                self.window_globalMOP.widgetTrackContinuity.close()
                self.window_globalMOP.widgetFalseTrack.close()
                self.window_globalMOP.widgetNumberOfValidTrack.close()
                self.window_globalMOP.widgetClassProbability.close()
                self.window_globalMOP.widgetOSPA.close()
                self.window_globalMOP.widgetPacketSize.close()
                self.window_globalMOP.widgetExecutionTime.close()
        else:
            event.ignore()
         
    
        self.clearData()
        self.startDateTime.clear()
        self.endDateTime.clear()
        self.path.clear()
        self.textEdit.clear()
        self.comboBox.clear()
        
        
     def newMap(self):         
     
         if self.axes!= None:
             return
         fig = Figure((5.0, 4.0), dpi=100)
         self.axes =  fig.add_subplot(111)
         self.canvas = FigureCanvas( fig)
         self.canvas.setFocusPolicy(Qt.StrongFocus)
         self.canvas.setFocus()
         self.canvas.draw()
         self.canvas.show()
         self.axes.grid(True)
         navi_toolbar = NavigationToolbar(self.canvas, self.mapWidget) #createa navigation toolbar for our plot canvas
         vbl = QVBoxLayout()
         vbl.addWidget(self.canvas )
         vbl.addWidget(navi_toolbar)
         self.mapWidget.setLayout( vbl )
         
     def displayLocationError(self):
         if self.checkBox_LocationError.isChecked():
             for _mop in self.windowMop:
                 _mop.displayLocationErrorWidget = True
                 _mop.updateDisplay()
         else : 
             for _mop in self.windowMop:
                 _mop.displayLocationErrorWidget = False
                 _mop.updateDisplay()
     def displayVelocity(self):
         if self.checkBox_Velocity.isChecked():
             for _mop in self.windowMop:
                 _mop.displayVelocityWidget = True
                 _mop.updateDisplay()
         else : 
             for _mop in self.windowMop:
                 _mop.displayVelocityWidget = False
                 _mop.updateDisplay()
     def displayVelocityError(self):
         if self.checkBox_VelocityError.isChecked():
             for _mop in self.windowMop:
                 _mop.displayVelocityErrorWidget = True
                 _mop.updateDisplay()
         else : 
             for _mop in self.windowMop:
                 _mop.displayVelocityErrorWidget = False
                 _mop.updateDisplay() 
     def displayTrackContinuity(self):
        if self.checkBox_TauxCouvertureSene.isChecked():
            self.window_globalMOP.displayWidgetTrackContinuity = True
        else:
            self.window_globalMOP.displayWidgetTrackContinuity = False
        self.window_globalMOP.updateDisplay()  
     def displayTrackClassification(self):
    
         if self.checkBox_TrackClassification.isChecked():
             self.window_globalMOP.displayWidgetClassProbability = True
         else : 
             self.window_globalMOP.displayWidgetClassProbability = False
             
         self.window_globalMOP.updateDisplay()    
     def displayOSPA (self):
 
        if self.checkBox_Ospa.isChecked():
            self.window_globalMOP.displayWidgetOSPA = True
        else:
            self.window_globalMOP.displayWidgetOSPA = False
        self.window_globalMOP.updateDisplay()
     def displayPacketSize (self):
        
        if self.checkBox_PacketSize.isChecked():
            self.window_globalMOP.displayWidgetPacketSize = True
        else:
            self.window_globalMOP.displayWidgetPacketSize = False
        self.window_globalMOP.updateDisplay()      
        
 
         
     def displayExecutionTime (self):
        
        if self.checkBox_TimeProcessing.isChecked():
            self.window_globalMOP.displayWidgetExecutionTime = True
        else:
            self.window_globalMOP.displayWidgetExecutionTime = False
        self.window_globalMOP.updateDisplay()        
     def displayCardinality(self):
        
        if self.checkBox_RLP.isChecked():
            self.window_globalMOP.displayWidgetNumberOfValidTrack = True
        else:
            self.window_globalMOP.displayWidgetNumberOfValidTrack = False
        self.window_globalMOP.updateDisplay()
     def displayCompletness(self)    :
  
        if self.checkBox_TauxCompletude.isChecked():
            self.window_globalMOP.displayWidgetCompletness = True
        else:
            self.window_globalMOP.displayWidgetCompletness = False
        self.window_globalMOP.updateDisplay()
     def clearData(self):
         
         #destruction des cibles
         self.clearAll()
         dataManager.instance().removeNodes()
         dataManager.instance().removeTargets()
 
     def dataBaseInfos(self):
         _dir = QDir(self.path.text())
   
         if not _dir.exists():
             self.receiveMessage ("Cannot find the example directory")
         
         self.clearData()
 
         _filter =[]
         _filter.append("*.db")
         self.receiveMessage("number of files: %s"%len(_dir.entryInfoList(_filter)));
         text =['']
         if len(_dir.entryInfoList(_filter))>= 1:
            self.currentDataBase.loadData(_dir.entryInfoList(_filter)[0].absoluteFilePath()) 
         for _fileInfo in _dir.entryInfoList(_filter):
           text.append(_fileInfo.fileName())
         self.comboBox.clear()
         self.comboBox.addItems(text)
         self.comboBox.setEnabled(True)
         self.comboBox.currentIndexChanged.connect(self.displayDataBase)
         self.buttonGEARTH.setEnabled(True)
         self.buttonGEARTH.clicked.connect(self.generateKML)
         #existance des mops
         # recherche des répertoires
         _list = os.listdir(self.path.text())
         nbDirs = 0
         for _rep in  _list :
             path = self.path.text()+str("/")+_rep
             if os.path.isdir(path):
                 nbDirs +=1
                 
         self.receiveMessage("number of mop directories: %s"%nbDirs);
#         self.receiveMessage("number of mop files: %s"%len(_dir.entryInfoList(['*.npy'])));
#         if len(_dir.entryInfoList(['*.npy']))>= 1:
#             self.existingMopFile = True;
         if nbDirs>=1 : 
             self.existingMopFile = True;
     def receiveMessage(self,_message=''):
         
         self.textEdit.append(_message)
#     def EditTimePerformances(self):
#        f_path, filters = QFileDialog.getOpenFileName(None, "Select log file", '*.MTT')  
#        if f_path:
#            self.TimeFilePerformances = f_path
#            self.performanceTimeFile.setText(f_path)
        
#     def EditSizePerformances(self):
#        f_path, filters = QFileDialog.getOpenFileName(None, "Select packet file", '*.txt')
#        if f_path:
#            self.PacketSizeFilePerformances = f_path
#            self.performanceSizeFile.setText(f_path)
#     
#        
     def clearAll(self):
         
               
  
         self.currentTracks                  = []
 
         self.windowMop                      = []
         self.mopTargets                     = []
         self.textEdit.setPlainText('')
         for _mop in self.windowMop:
             _mop.locationErrorWidget.close()
             _mop.velocityErrorWidget.close()
             
             if self.window_globalMOP:
                self.window_globalMOP.widgetCompletness.close()
                self.window_globalMOP.widgetTrackContinuity.close()
                self.window_globalMOP.widgetFalseTrack.close()
                self.window_globalMOP.widgetNumberOfValidTrack.close()
                self.window_globalMOP.widgetClassProbability.close()
                self.window_globalMOP.widgetOSPA.close()
                self.window_globalMOP.widgetPacketSize.close()
                self.window_globalMOP.widgetExecutionTime.close()
         
         self.window_globalMOP.clear()
     def EditTaxonomie(self):
     
        f_path, filters = QFileDialog.getOpenFileName(None, "Select taxonomie file", '*.xml')
        
     
        self.taonomieFile.setText(f_path)
      
     def EditPath(self):
        self.clearAll()
        folder = QFileDialog.getExistingDirectory(None, "Select Folder to compute MOP", '.')
        if not folder :
             folder =  folder  + "/"   
     
        self.path.setText(folder)
        self.dataBaseInfos() 
     
     def question(self,message='no message',title='no title'):
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Question)
            msg.setText( message)
            msg.setWindowTitle(title)
 
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
 
            return msg.exec_()        
     def OnOk(self):
     
         if self.existingMopFile == True:
             if self.question("MOP files already exists. Do you want reload them?","MonteCarlo run") == QMessageBox.Yes:
                 self.reload();
                 return
         self.run()
    
     def OnCancel(self):
         
         self.close()
   
     def displayMops(self):
         
         #display timeLine
         print('displayMops')
     def reload(self):
         print('in reload MOP')
         # save np.load
         np_load_old = np.load

         # modify the default parameters of np.load
         np.load = lambda *a,**k: np_load_old(*a, allow_pickle=True, **k)


         mainPath = self.path.text()
         
         #==================
         # display textfile
         #==================
         
         
         text=open(mainPath+'/log.txt').read()
         self.textEdit.setPlainText(text)
         for _target in dataManager.instance().targets():       
            self.windowMop.append(windows_Mop())
         #==================
         # display globalMop
         #==================
         _dir = os.listdir(mainPath)
         u = 0
         for _rep in  _dir :
             path = mainPath+str("/")+_rep
     
     
             if os.path.isdir(path):
 
                 mcmc = MCMC_Mop(_rep)
                
                 _timeLine = np.load(path+str("/")+'timeLine.npy') 
         
                 mcmc.setTimeLine(_timeLine) 
                 mcmc.NVT               = np.load(path+str("/")+'nvt.npy') 
                 mcmc.NMT               = np.load(path+str("/")+'nmt.npy') 
                 mcmc.NFT               = np.load(path+str("/")+'nft.npy')
                 mcmc.MOC               = np.load(path+str("/")+'moc.npy')
                 mcmc.ANST              = np.load(path+str("/")+'ANST.npy')
                 mcmc.NB_MCMC           = np.load(path+str("/")+'NB_MCMC.npy')
                 mcmc.NMT               = np.load(path+str("/")+'nmt.npy')
                 mcmc.ToE               = np.load(path+str("/")+'ToE.npy')
                 mcmc.Packet_Track      = np.load(path+str("/")+'Packet_Track.npy')
                 mcmc.Packet_Received   = np.load(path+str("/")+'Packet_Received.npy')
                 mcmc.OSPA = np.load(path+str("/")+'OSPA.npy')
                 self.window_globalMOP.globalMOP.append(mcmc)
                 self.mopTargets.append([_rep,[]])
                 for _target,i in zip(dataManager.instance().targets(),range(0,len(dataManager.instance().targets()))):
                     _localMop           = target_Mop(_target)
                     _localMop.setTimeLine(_timeLine) 
                     #_localMop.setRun(self.mopGlobal.NB_MCMC)
                     _localMop.targetDetection       =      np.load(path+str("/")+'target_%s_targetDetection.npy'%_target.id)
                     _localMop.locationError         =      np.load(path+str("/")+'target_%s_locationError.npy'%_target.id)
                     _localMop.velocityError         =      np.load(path+str("/")+'target_%s_velocityError.npy'%_target.id)
                     _localMop.velocity              =      np.load(path+str("/")+'target_%s_velocity.npy'%_target.id)
                     _localMop.correctClassificationProbability      = np.load(path+str("/")+'target_%s_correctClassificationProbability.npy'%_target.id)
                     _localMop.classificationProbability             = np.load(path+str("/")+'target_%s_classificationProbability.npy'%_target.id)
                     _localMop.associatedTrack                       = np.load(path+str("/")+'target_%s_associatedTrack.npy'%_target.id)
                     _localMop.nbAssociatedTarget                    = np.load(path+str("/")+'target_%s_nbAssociatedTarget.npy'%_target.id)
                     _localMop.detectionProbability                  = np.load(path+str("/")+'target_%s_detectionProbability.npy'%_target.id)
                     _localMop.trackContinuity                       = np.load(path+str("/")+'target_%s_trackContinuity.npy'%_target.id)
                     self.windowMop[i].target_mops.append(_localMop) 
                     self.mopTargets[u][1].append(_localMop)
                 u +=1
               
           
         #======================
         # display global mops
         #======================
         self.window_globalMOP.displayNumberOfValidTrack()   
         self.window_globalMOP.displayCompletness()
         self.window_globalMOP.displayOSPA()
         self.window_globalMOP.displayTrackContinuity(self.mopTargets)
         #self.window_globalMOP.displayClassificationProbability(self.mopTargets[indiceTracker][1])
         self.window_globalMOP.displayPacketSize()
         self.window_globalMOP.displayExecutionTime()
         
         for _mop in self.windowMop:
                _mop.displayLocationError()
                _mop.displayVelocityError()
                _mop.displayVelocity()


  
 
         # restore np.load for future normal usage
         np.load = np_load_old
         
     def readTree(self,_attrib,_classTaxonomie = classTaxonomie()):
         if  _attrib.nodeName == 'Category' or _attrib.nodeName =='Type' or _attrib.nodeName =='Half-type' or _attrib.nodeName =='Target' :
             _classTaxonomie.name = str(_attrib.getAttribute("name"))
            
         for elem in _attrib.childNodes:
             if  elem.nodeName == 'Category' or elem.nodeName =='Type' or elem.nodeName =='Half-type' or elem.nodeName =='Target':
                  if _classTaxonomie.name == 'NOTHING':
                      _chilClass = _classTaxonomie
                  else:
                      _chilClass = classTaxonomie()                  
                  _classTaxonomie.fils.append(_chilClass)
                  _chilClass.pere  = _classTaxonomie
                  self.readTree(elem,_chilClass)
             else :
                 self.readTree(elem,_classTaxonomie)
         return
     def convertTaxonomie(self):
        #print(['convert :',self.taonomieFile.text()])
        doc = minidom.parse(self.taonomieFile.text())
        root = doc.documentElement
        
        self.readTree(root,self.classTaxonomie)
       

     def run(self):
        
         #gestion de la taxonomie
         
         
        if self.taonomieFile.text():             
             self.convertTaxonomie();
         
        
      
        #================================
        # fichiers à traiter
        #================================
        
        AllItems = [self.comboBox.itemText(i) for i in range(1,self.comboBox.count())] 
        _file  = self.path.text()+str("/")+ AllItems[0]

        #===============================
        # construction de la timeLine
        #===============================
        _timeLine = []
        
        t = self.startDateTime.dateTime()
        
        while t < self.endDateTime.dateTime():           
            _timeLine.append(t)
            t = t.addSecs(1)
    
        #===========================================%
        # récupération de l'adresse des trackers    %
        #===========================================%
        
        _trackers = self.currentDataBase.loadTrackerFormDataBase(_file)
        self.currentDataBase.updateComponents(QDateTime(),self.endDateTime.dateTime())
    
        for _tracker in _trackers:
            idTrackers = _tracker[0]
            self.mopTargets.append([idTrackers,[]])
            mcmc = MCMC_Mop(idTrackers)
            mcmc.setTimeLine(_timeLine)
            mcmc.NB_MCMC =   len(AllItems)
            mcmc.nom     =   _tracker[1]  
            self.window_globalMOP.globalMOP.append(mcmc)
            print(['---->',idTrackers])

        
        #===========================================%       
        # lancement du prograssBar                  %    
        #===========================================%
            
        progress_Bar = ProgressBar(None,len(AllItems)*len(_trackers))
        progress_Bar.show()
            
        #===========================================%
        # construction de la vérité terrain         %
        #===========================================%     

        for _target in dataManager.instance().targets():       
            self.windowMop.append(windows_Mop())
 
        for _tracker,u in zip(_trackers,range(0,len(_trackers))):
       
           for _target,i in zip(dataManager.instance().targets(),range(0,len(dataManager.instance().targets()))):
            _localMop           = target_Mop(_target)
            _localMop.setTimeLine(_timeLine) 
            _localMop.setRun(len(AllItems) )
            _localMop.setTaxonomieClassification(self.classTaxonomie)
            _localMop.setTrackerName(_tracker[1])
            self.windowMop[i].target_mops.append(_localMop)
            self.mopTargets[u][1].append(_localMop)

            
        for t in range(0,len(_timeLine)-1):                
            
            currentTime = _timeLine[t]
            
            for i in range(0,len(self.mopTargets[0][1])):
                _mopTarget = self.mopTargets[0][1][i] 
                
                flag,position,velocity = _mopTarget.target.positionAtTime(currentTime)
                #('----> 1')
                for _node in dataManager.instance().nodes():
                    #print('----> 2')
                    for _sensor in _node.sensors:
                        #print('----> 3')
                        #print(flag)
                        if flag  and _sensor.isInFOV(position,_mopTarget.target.type):
                         
                            for u in range(0,np.shape(self.mopTargets)[0])   : 
                                
                                self.mopTargets[u][1][i].detected(currentTime)
                         
        #=================================================
        # Acces aux tracks
        #=================================================
        num = 0
        for indiceTracker  in range(0,np.shape(self.mopTargets)[0]):
            idTracker  = self.mopTargets[indiceTracker][0]
            for indexTable in range(0,len(AllItems)):  
                
                _file  = self.path.text()+str("/")+ AllItems[indexTable]
       
                progress_Bar.update_progressbar(num)
                num = num+1
                tracks = self.currentDataBase.loadTracksFormDataBase(_file,idTracker,self.requestEdit.text())
               
                self.receiveMessage(('---> compute mop from base %s')%(str(_file)) )             
          
                for _t in _timeLine:
                    
                    #=========================================
                    #construction de la matrice d'association
                    #=========================================
                    
                    _currentTargets = []
                    _currentTracks  = []
                    X               = []
                    Y               = []
                    for _mopTarget in self.mopTargets[indiceTracker][1]:
   
                        flag,_point,velovity    = _mopTarget.target.positionAtTime(_t)
           
                        if flag :
                         
                            X.append([_point.x_UTM,_point.y_UTM])
                            _currentTargets.append( (_mopTarget,_point,velovity))
                    for track in tracks:
                        flag,_point,velovity,stdLocation, stdVelocity,_nbplots = track.positionAtTime(_t)
                        flag2,_classes       = track.classesAtTime(_t)
                        
                        
                        
                        if flag :
                 
                            Y.append([_point[0].x_UTM,_point[0].y_UTM])
                            _currentTracks.append( (track,_point,velovity,_classes,stdLocation, stdVelocity,_nbplots)) 
#                    print('----------')
#                    print(len(_currentTargets))
#                    print(len(_currentTracks))
                    if len(_currentTargets)==0 or len(_currentTracks)==0:
                        continue
                    #===================
                    # Compute OSPA
                    #===================
                    X_os = np.zeros((2,len(X)))
                    for i,u in zip(range(0,len(X)),X) :
                        X_os[:,i] = u
                    Y_os = np.zeros((2,len(Y)))
                    for i,u in zip(range(0,len(Y)),Y) :
                        Y_os[:,i] = u                     
      
                    gospa_err,ospa_err,cardinals,mse = gospa_ospa_distances(np.asarray(X,dtype='float'),np.asarray(Y,dtype='float')) 
                    
                    #========================================%
                    MAX_VALUE                   = 100
                    costMatrix                  = MAX_VALUE * np.ones([len(_currentTargets),len(_currentTracks)])
                    costMatrixVelocity          = MAX_VALUE * np.ones([len(_currentTargets),len(_currentTracks)])
                    costMatrixStdVelocity       = MAX_VALUE * np.ones([len(_currentTargets),len(_currentTracks)])
                    costMatrixStLocation        = MAX_VALUE * np.ones([len(_currentTargets),len(_currentTracks)])
                    c = 0
                    
                    
                   
                    for target,positionTarget,velocityTarget in _currentTargets:                
                        t = 0
                        for track,positionTrack,velocityTrack,_classes,stdLocation, stdVelocity, nbPlots  in _currentTracks:
                            minDistance     = MAX_VALUE
                            minVelocity     = 100 
                            minStdVelocity  = 100
                            minStdLocation  = 100
                            for p,v,std_p,std_v in zip(positionTrack,velocityTrack,stdLocation, stdVelocity):
                               distance         =  positionTarget.distanceToPoint(p)
                               velocityError    =  velocityTarget.distanceToVelocity(v)
                           
                               if distance < minDistance:
                                   minDistance = distance
                                   minVelocity = velocityError
                                   minStdLocation  = std_p
                                   minStdVelocity  = std_v
                            costMatrix[c,t]         =  minDistance
                            costMatrixVelocity[c,t] =  minVelocity
                            costMatrixStdVelocity[c,t] =  minStdVelocity
                            costMatrixStLocation[c,t]  =  minStdLocation
                 
                            t =  t+1
                        c = c+1
                                   
                    row_ind, col_ind = linear_sum_assignment(costMatrix)
#                    print(costMatrix)
#                    False Track
                    
                    self.window_globalMOP.globalMOP[indiceTracker].computeCompletude(_t,len(col_ind),np.shape(_currentTracks)[0])
                    self.window_globalMOP.globalMOP[indiceTracker].computeOSPA(_t,ospa_err)
                    for r in range(0,len(row_ind)):
                               row      = row_ind[r]
                               column   = col_ind[r]
      
                               if costMatrix[row][column]!=MAX_VALUE:   
    
                                   _mopTarget,_point,vel = _currentTargets[row]
                                   state,_point2,vels,classes,_stdLoc,_stdVel,_nbplots = _currentTracks[column]
                                   #print('Track : {0}  associated to target {1} error {2}'.format(state.id ,_mopTarget.target.id,costMatrix[row][column]))
                                   
                                   _mopTarget.addLocationError(costMatrix[row][column],_t)
                                   _mopTarget.addVelocityError(costMatrixVelocity[row][column],_t)
                                   _mopTarget.addVelocity(vels[0],_t)
                                   _mopTarget.addStdLocationError( costMatrixStLocation[row][column],_t)
                                   _mopTarget.addStdVelocityError(costMatrixStdVelocity[row][column],_t)
                                   _mopTarget.addLocations(_point,_point2[0],_t)
                                   _mopTarget.addCurrentTarget(state.id,_t)
                                   _mopTarget.addTrackClass(classes[0],_t)
                                   _mopTarget.addPlots(_nbplots[0],_t)
                
                self.window_globalMOP.globalMOP[indiceTracker].computeNumberOfValidTrack(self.mopTargets[indiceTracker][1])
                self.window_globalMOP.globalMOP[indiceTracker].computeNumberOfMissedTargets(self.mopTargets[indiceTracker][1])
                
                perf_tracker    = self.currentDataBase.loadPerformancesFromDataBase("tracker",_file)
                perf_trackMsg   = self.currentDataBase.loadPerformancesFromDataBase("trackPacket",_file)
                perf_nodeMsg    = self.currentDataBase.loadPerformancesFromDataBase("nodePacket",_file)
                perf_sensorMsg  = self.currentDataBase.loadPerformancesFromDataBase("sensorPacket",_file)
                perf_detMsg     = self.currentDataBase.loadPerformancesFromDataBase("detectionPacket",_file)
      
                self.window_globalMOP.globalMOP[indiceTracker].computeExecutionTime(perf_tracker)
                self.window_globalMOP.globalMOP[indiceTracker].computePacketSize("nodePacket",      perf_nodeMsg)
                self.window_globalMOP.globalMOP[indiceTracker].computePacketSize("trackPacket",     perf_trackMsg)
                self.window_globalMOP.globalMOP[indiceTracker].computePacketSize("sensorPacket",    perf_sensorMsg)
                self.window_globalMOP.globalMOP[indiceTracker].computePacketSize("detectionPacket", perf_detMsg)
        
               
                for _mopTarget in self.mopTargets[indiceTracker][1]:
                    _mopTarget.computeTrackContinuity()
                    _mopTarget.computetrackProbabilityDetection()
                    _mopTarget.computeClassificationProbability()
                    _mopTarget.computeAverageMeasure()
                    _mopTarget.reset(_timeLine)
                    
       
        #fin du parcours des tables
        
        for _mop in self.windowMop:
                #_mop.displayLocations()
                _mop.displayLocationError()
                _mop.displayVelocityError()
                _mop.displayVelocity()
         
        self.window_globalMOP.displayNumberOfValidTrack()   
        self.window_globalMOP.displayCompletness()
        self.window_globalMOP.displayOSPA()
        self.window_globalMOP.displayTrackContinuity(self.mopTargets)
        self.window_globalMOP.displayClassificationProbability(self.mopTargets[indiceTracker][1])
        self.window_globalMOP.displayPacketSize()
        self.window_globalMOP.displayExecutionTime()
        #====================
        #mesures synthétiques 
        #====================
        for indiceTracker  in range(0,np.shape(self.mopTargets)[0]):
            self.receiveMessage(("tracker %d : temsp d'éxécution moyen du tracker (en ms) %f")%(indiceTracker,self.window_globalMOP.globalMOP[indiceTracker].averageExecutionTime()))
            self.receiveMessage(("tracker %d : taille moyen des packets émis par le tracker %f")%(indiceTracker,self.window_globalMOP.globalMOP[indiceTracker].averagePacketTrackSize()))
            self.receiveMessage(("tracker %d : taille moyen des packets des détections reçues par le tracker %f")%(indiceTracker,self.window_globalMOP.globalMOP[indiceTracker].averagePacketReceivedSize()))
        
        for indiceTracker  in range(0,np.shape(self.mopTargets)[0]):
            for _mopTarget in self.mopTargets[indiceTracker][1]:
                self.receiveMessage("============================")
                self.receiveMessage(("MOP target %s")%(_mopTarget.target.id))
                self.receiveMessage(("tracker %d : average error in location %f")%(indiceTracker,_mopTarget.ARMSE_Location))
                self.receiveMessage(("tracker %d : average error in velocity %f")%(indiceTracker,_mopTarget.ARMSE_Velocity))
                self.receiveMessage(("tracker %d : detection probability %f")%(indiceTracker,_mopTarget.detectionProbability))
                self.receiveMessage(("tracker %d : mean track continuity %f")%(indiceTracker,_mopTarget.trackContinuity ))
                self.receiveMessage(("tracker %d : classification probability %f")%(indiceTracker,_mopTarget.classificationProbability))
                 
        
        #====================
        #automatic save 
        #====================
        self.window_globalMOP.save(self.path.text())
        
        file = open(self.path.text()+'/log.txt','w')
        text = self.textEdit.toPlainText()
        file.write(text)
        file.close()
       
            
        for indiceTracker  in range(0,np.shape(self.mopTargets)[0]):
            for _mopTarget in self.mopTargets[indiceTracker][1]: 
 
                    path = self.path.text()+'/'+_trackers[indiceTracker][1]
                    _mopTarget.save(path)
                    
                    
                    
     def receiveTargets(self):
       
         for _targ in dataManager.instance().targets():
             _targ.buildTrajectory()
         #liste des fichiers *.db
     def receiveReferenceTime(self, date = QDateTime()):
         self.startDateTime.setDateTime(date)
         self.startDateTime.setEnabled(True)
         
         self.endDateTime.setDateTime(date.addSecs(3600))
         self.endDateTime.setEnabled(True)
         
     def receiveEndTime(self, date = QDateTime()):
         self.endDateTime.setDateTime(date)
         self.endDateTime.setEnabled(True)
     def generateKML(self):
         indexTable = self.comboBox.currentIndex()
      
         indexTable = indexTable-1
         if indexTable <0:
             return
         else : 
         
             #display ground true
             kml =  simplekml.Kml()
             
             folderSensor = kml.newfolder(name='sensors location')
             
             _file = self.path.text()+str("/")+ self.comboBox.itemText(1)
               
            
             self.currentDataBase.updateComponents(QDateTime(),self.endDateTime.dateTime())
             tracks =self.currentDataBase.loadTracksFormDataBase(_file,None,self.requestEdit.text()) 
             maxData = len(dataManager.instance().nodes())+len(dataManager.instance().targets())+len(tracks)
             progress = QProgressDialog("converting sitac in kml...", "Abort conversion", 0, maxData, self)
             progress.setWindowModality(Qt.WindowModal)   
        
             i = 0
             center = []
             for _node in  dataManager.instance().nodes():
                 fol = folderSensor.newfolder(name=_node.name)
                 folLoc = fol.newfolder(name='locations')
                 pnt = folLoc.newpoint(name= _node.name, coords=[(_node.Position.longitude,_node.Position.latitude,_node.Position.altitude)])
                 pnt.altitudemode       =  simplekml.AltitudeMode.relativetoground
                 pnt.style.iconstyle.scale = 3  # Icon thrice as big
                 pnt.style.iconstyle.icon.href =  './icones_target/radar.png'
                 center=[_node.Position.longitude,_node.Position.latitude,_node.Position.altitude]                         
                 i+=1
                 
                 
                 
                 for _sensor in  _node.sensors:
                     print('--->')
                     if _sensor.sensorCoverage!=None  and  REFERENCE_POINT.longitude !=[]  and  REFERENCE_POINT.latitude!=[]:
                        print('--->')
                        folAreas = fol.newfolder(name='fields of view')
                        for _cover in _sensor.sensorCoverage: 
                                print('---> 2')
                                pol = folAreas.newpolygon(name='field of View '+str(_cover.name))
                                dmax = _cover.distanceMax
                                
                                pts =  Position()
                                pts.setXYZ(_node.Position.x_UTM + dmax,_node.Position.y_UTM,0.0)
                              
                                _angle = np.mod(np.pi/2 - _node.Orientation.yaw * np.pi/180  -  _cover.fov/2.0 * np.pi/180 + np.pi, 2*np.pi) - np.pi
                                _angle = _angle -np.pi/2
                                verts = np.array([_cover.distanceMin*np.cos(_angle), _cover.distanceMin*np.sin(_angle)])        
                               
                                while _angle  < np.pi/2  - _node.Orientation.yaw*np.pi/180  + _cover.fov/2*np.pi/180:
                                    _angle = _angle + 2*np.pi/180
                                    Pt = np.array([_cover.distanceMin*np.cos(_angle), _cover.distanceMin*np.sin(_angle)])
                                    verts = np.vstack([verts, Pt] )
                         
                                while _angle  > np.pi/2  - _node.Orientation.yaw*np.pi/180  - _cover.fov/2*np.pi/180:
                                    _angle = _angle - 2*np.pi/180
                                    Pt = np.array([_cover.distanceMax*np.cos(_angle), _cover.distanceMax*np.sin(_angle)])
                                    verts = np.vstack([verts, Pt] )
                        
                                Pt = np.array([_cover.distanceMin*np.cos(_angle), _cover.distanceMin*np.sin(_angle)])       
                                verts = np.vstack([verts, Pt] )    +[_node.Position.x_UTM,_node.Position.y_UTM]
                            
                                tot=[]
                                for u in verts:
                                    pts =  Position()
                                    pts.setXYZ(u[0],u[1],0.0)
                                    tot.append((pts.longitude ,pts.latitude))
                                
                                pol.outerboundaryis = tot
                                pol.style.linestyle.color = simplekml.Color.green
                                pol.style.linestyle.width = 5
                                pol.style.polystyle.color = simplekml.Color.changealphaint(50, simplekml.Color.green)
                     
                                break
                 progress.setValue(i)
                 if progress.wasCanceled():
                     break
                 
                    
             #=================================
             # grid
             #==================================     
             if center !=():
                 multilin = kml.newmultigeometry(name="Grid") # SA (Hartebeeshoek94) Grid 
         
                 for x in np.arange(-0.1,0.1,0.005):
                     linecoords = []
                     for y in np.arange(-0.1, 0.1,0.005):
                         linecoords.append((center[0] + x,center[1] + y))
                        
                         multilin.newlinestring(coords=linecoords)
                 for y in np.arange(-0.1,0.1,0.005):
                     linecoords = []
                     for x in np.arange(-0.1, 0.1,0.005):
                         linecoords.append((center[0] + x,center[1] + y))
                        
                         multilin.newlinestring(coords=linecoords)      
             folderTargets = kml.newfolder(name='targets')
             
             for _target in  dataManager.instance().targets():
                 fol = folderTargets.newfolder(name=_target.name)
                 folLoc = fol.newfolder(name='locations')
                 i+=1
                 progress.setValue(i)
                 if progress.wasCanceled():
                     break
                 
                 Cumul =[]
                 for i in range(len(_target.trajectoryWayPoints)):
                     if self.startDateTime.dateTime() <= _target.timeToWayPoints[i] and _target.timeToWayPoints[i] <= self.endDateTime.dateTime() :
                     
                         pnt = folLoc.newpoint(name= _target.name, coords=[(_target.trajectoryWayPoints[i].longitude,_target.trajectoryWayPoints[i].latitude,_target.trajectoryWayPoints[i].altitude)])
                         Cumul.append((_target.trajectoryWayPoints[i].longitude,_target.trajectoryWayPoints[i].latitude,_target.trajectoryWayPoints[i].altitude))
                         pnt.timestamp.when     = _target.timeToWayPoints[i].toString('yyyy-MM-ddTHH:mm:ss.z')
                         pnt.timestamp.begin    = _target.timeToWayPoints[i].toString('yyyy-MM-ddTHH:mm:ss.z')
                         pnt.altitudemode       =  simplekml.AltitudeMode.relativetoground
    
        
                         pnt.style.iconstyle.scale = 3  # Icon thrice as big
                         pnt.style.iconstyle.icon.href =  _target.type.value.icone
             
                 lin = fol.newlinestring(name="target trajectory", description="trajectory of the target",
                        coords=Cumul)
                 lin.altitudemode = simplekml.AltitudeMode.relativetoground
                 lin.extrude = 1
                 lin.style.linestyle.color = simplekml.Color.rgb(10,240,125,150)# = 'cafc03ff'  # Red
                 lin.style.linestyle.width= 10  # 10 pixels
                 lin.style.polystyle.color = simplekml.Color.rgb(10,240,125,150)
                    
             folderTracks = kml.newfolder(name='tracks')

            
            #=================================
            # verrif
            #==================================
             _timeLine = []
             
             t = self.startDateTime.dateTime()
             
     
            
             while t < self.endDateTime.dateTime():
             
                _timeLine.append(t)
                t = t.addSecs(1) 
 
             #tracks = self.currentDataBase.newTracks()
             
             for _track in tracks:
                 i+=1
                 progress.setValue(i)
                 if progress.wasCanceled():
                     break
                 
                 if _track.taillePiste()>5    and _track.tree.data.time <= _timeLine[-1]  and _track.getCurrentState().data.time >=  _timeLine[0]: 
                    fol = folderTracks.newfolder(name=str(_track.id))
                    coordonnes = _track.getTrajectory()
                    lin = fol.newlinestring(name="track", description="trajectory of the track",
                        coords=coordonnes)
                    lin.altitudemode = simplekml.AltitudeMode.relativetoground
                    lin.style.linestyle.color = simplekml.Color.rgb(230,40,125,150)#
                    lin.style.linestyle.width= 5  # 10 pixels
                    lin.style.polystyle.color = "7f00ff00"
                    lin.extrude = 1
                    folState = fol.newfolder(name=str('estimated states'))
     
      
                    for _state in  _track.getStates() :
                            #if self.startDateTime.dateTime() <= _state.time and _state.time <= self.endDateTime.dateTime() :
                            
                                #print([(_state.location.longitude,_state.location.latitude)])
                                pnt = folState.newpoint(name= str(_state.id), coords=[(_state.location.longitude,_state.location.latitude,_state.location.altitude)])
                                pnt.timestamp.when     = _state.time.toString('yyyy-MM-ddTHH:mm:ss.z')
                                pnt.style.iconstyle.scale = 3  # Icon thrice as big
                                pnt.altitudemode       =  simplekml.AltitudeMode.relativetoground
                                pnt.style.iconstyle.icon.href =  './icones_target/location.png'
                     
                    
                    
             kml.save(self.path.text()+'/battleplaces.kml') 
                 #copie du repertoire icone dan sle répertoire kml 
             progress.setValue(maxData)
             s = os.path.join(os.getcwd(), 'icones_target')
             d = os.path.join(self.path.text(), 'icones_target')
             copy_tree(s,d)
     def displayDataBase(self,indexTable):
 
        indexTable = indexTable-1
  
        if indexTable <0:
             return
        AllItems = [self.comboBox.itemText(i) for i in range(1,self.comboBox.count())] 
  
        _file = self.path.text()+str("/")+ AllItems[indexTable]
  
                
#        if self.mapWidget.isVisible()==False:
        for _target in dataManager.instance().targets():
                 _target.textObj        = None 
                 _target.locationObj    = None
                 _target.trajectoryObj  = None
        self.newMap()
        self.mapWidget.show()
        self.axes.cla()
        #display reference point

        self.axes.plot(REFERENCE_POINT.longitude,REFERENCE_POINT.latitude, 'bo', linewidth= 2) 
        #display targets
        for _target in dataManager.instance().targets():
            _target.toDisplay(self.axes)
             

        #display tracks
        tracks =self.currentDataBase.loadTracksFormDataBase(_file,None,self.requestEdit.text()) 
        #=================================
        # verrif
        #==================================
        _timeLine = []
 
        t = self.startDateTime.dateTime()
 
        longitude =[]
        latitude  =[]
        
        while t < self.endDateTime.dateTime():
 
            _timeLine.append(t)
            t = t.addSecs(1) 
        #tracks = self.currentDataBase.newTracks()
        for _track in tracks:
           
            if _track.taillePiste()>5:
                if _track.tree.data.time <= _timeLine[-1]  and _track.getCurrentState().data.time >=  _timeLine[0]:
                    _track.displayTrack(self.axes,self.canvas) 
    

 
        #==================================
        # display plot
        #==================================

 
        for t in range(0,len(_timeLine)-1):
            self.currentDataBase.updateComponents(_timeLine[t],_timeLine[t+1])
 
  
        
        plots = self.currentDataBase.loadDetections(_file) 
        sensors = []
      
        for _node in dataManager.instance().nodes():
            for _sensor in _node.sensors:
                sensors.append(_sensor)
      
        latitude = []
        longitude = []
        for _plot in plots:
            if _plot.Type == PLOTType.POLAR or _plot.Type == PLOTType.SPHERICAL:
                for _sensor in  sensors:
                    if _sensor.id == _plot.idSensor:
                        
                        pos =Position()
                       
                        pos.setXYZ(_plot.rho*np.cos((-_plot.theta + 90 - _sensor.node.Orientation.yaw)*np.pi/180 ) + _sensor.node.Position.x_ENU,_plot.rho*np.sin(( -_plot.theta+90 - _sensor.node.Orientation.yaw)*np.pi/180 )+ _sensor.node.Position.y_ENU,0.0,'ENU')
                        latitude.append(pos.latitude)
                        longitude.append(pos.longitude)
                        #self.axes.text(pos.longitude,pos.latitude, _plot.dateTime.toString('hh:mm:ss.z'),  color='cyan')
        self.axes.scatter(longitude,latitude,color = 'cyan',marker = '^')
        '''
        for _target in self.targets:
            longitude =[]
            latitude  =[]
            for _t in _timeLine:
              flag,position,velocity = _target.positionAtTime(_t)
              if flag:
                  longitude.append(position.longitude)
                  latitude.append(position.latitude)
                  self.axes.text(position.longitude,position.latitude, _t.toString('hh:mm:ss.z'),  color='green')
            self.axes.plot(longitude,latitude,color = 'green',marker = 'o') # 
              
         
            
        for track in tracks:
            longitude =[]
            latitude  =[]
            for _t in _timeLine:
              flag,_point,velovity = track.positionAtTime(_t)
              if flag:
                  for u in range(0,len(_point)):
                      longitude.append(_point[u].longitude)
                      latitude.append(_point[u].latitude)
                      self.axes.text(_point[u].longitude,_point[u].latitude, _t.toString('hh:mm:ss.z'),  color='blue')
            self.axes.plot(longitude,latitude,color = 'blue',marker = 'o')
         '''
     def receiveReferencePoint(self, pt   ) :
        
            strlist = pt.split(" ") 
            REFERENCE_POINT.setWGS84(float(strlist[0]),float(strlist[1]),float(strlist[2]))

            utm_getZone(float(strlist[0]))
            utm_isNorthern(float(strlist[1]))
            self.receiveMessage(("new referencePoint %f %f %f")%(REFERENCE_POINT.longitude, REFERENCE_POINT.latitude, REFERENCE_POINT.altitude))
            
             
         
def main(argv=None):
    app = QApplication(sys.argv)
    window = MOP()
    window.show()
    sys.exit(app.exec_())
    
if __name__ == "__main__":
    main() 