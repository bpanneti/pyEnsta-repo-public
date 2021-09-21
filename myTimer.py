# -*- coding: utf-8 -*-
"""
Created on Tue Aug 30 14:26:40 2016

@author: t0174034
"""
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtOpenGL import *
from PyQt5.QtWidgets import *
 
 
REFERENCE_TIME = QDateTime.currentDateTime()
def getReferenceTime():
    global REFERENCE_TIME
    return REFERENCE_TIME
 
class Timer(QTimer):
    sendTime = pyqtSignal()
    def __init__(self):

        QTimer.__init__(self)
        self.startTime = QDateTime.currentDateTime()
        self.timeout.connect(self.toc)
 
    def run(self):
        self.start(500)
    def terminate(self):
        self.stop()
    def pause(self):
        self.stop()
    def toc(self):
        self.sendTime.emit()
        
class Sequenceur(QWidget):
    receiveTime   = pyqtSignal('QDateTime')
    startTime     = pyqtSignal('QDateTime')
    stopTime      = pyqtSignal('QDateTime')
    pauseTime     = pyqtSignal()
    runCycle      = pyqtSignal()
    runMonteCarlo = pyqtSignal('QString')

    def __init__(self):
        super(Sequenceur, self).__init__()

        self.initUI()
        

    def builPalyerBar(self):
        
        """
        
        Builds the audio bar controls
        
        """
        self.depthTime = 600 
        sidepanel = QFrame()
        layout_panel = QGridLayout(sidepanel)

#        self.prevbutton = QPushButton()
#        pixmap = QPixmap("icones/prev.png")
#        self.prevbutton.setIcon(QIcon(pixmap))
#        layout_panel.addWidget(self.prevbutton, 0, 1)
#        self.prevbutton.clicked.connect(self.prev)
   
        self.playbutton = QPushButton()
        pixmap = QPixmap("icones/play.png")
        self.playbutton.setIcon(QIcon(pixmap))
        layout_panel.addWidget(self.playbutton, 0, 2)
        self.playbutton.clicked.connect( self.start)
        
        self.pausebutton = QPushButton()
        pixmap = QPixmap("icones/pause.png")
        self.pausebutton.setIcon(QIcon(pixmap))
        layout_panel.addWidget(self.pausebutton, 0, 3)
        self.pausebutton.clicked.connect( self.pause)
   
#        self.nextbutton = QPushButton()
#        pixmap = QPixmap("icones/next.png")
#        self.nextbutton.setIcon(QIcon(pixmap))
#        layout_panel.addWidget(self.nextbutton, 0, 4)
#        self.nextbutton.clicked.connect(  self.next)
#        
        self.stopbutton = QPushButton()
        pixmap = QPixmap("icones/stop.png")
        self.stopbutton.setIcon(QIcon(pixmap))
        layout_panel.addWidget(self.stopbutton, 0, 5)
        self.stopbutton.clicked.connect(  self.stop)
        
        
        self.runCycleButton = QPushButton()
        pixmap = QPixmap("icones/cycle.png")
        self.runCycleButton.setIcon(QIcon(pixmap))
        layout_panel.addWidget(self.runCycleButton, 0, 6)
        self.runCycleButton.clicked.connect(  self.cycle)
      
        p = QLabel("start time : ");
        self.lcd = QDateTimeEdit()
        self.lcd.setDisplayFormat("yyyy-MM-dd hh:mm:ss.zzz")
        layout_panel.addWidget(p, 0, 7)
        layout_panel.addWidget(self.lcd, 0, 8)
        self.lcd.setDateTime(REFERENCE_TIME)
        self.lcd.timeChanged.connect(self.timeModification)
        
        p = QLabel("end time : ");
        self.timeEnd = QDateTimeEdit()
        self.timeEnd.setDisplayFormat("yyyy-MM-dd hh:mm:ss.zzz")
        layout_panel.addWidget(p, 0, 9)
        layout_panel.addWidget(self.timeEnd, 0, 10)
        self.timeEnd.setDateTime(REFERENCE_TIME.addSecs(self.depthTime))
       # self.timeEnd.timeChanged.connect(self.timeEndModification)
        
        
        self.cb = QComboBox()
        self.cb.addItem("1")
        self.cb.addItem("10")
        self.cb.addItem("30")
        self.cb.addItem("60")
        self.cb.addItem("120")
        self.cb.currentIndexChanged.connect(self.accelerateur)
        layout_panel.addWidget(self.cb, 0, 11)
     
        self.progressBar =  QProgressBar()
        layout_panel.addWidget(self.progressBar, 0, 1,11,11)
        
        return sidepanel
    def duration(self):

        return  - self.timeEnd.dateTime().secsTo(REFERENCE_TIME) 
    def timeModification(self):
  
   
        self.localtime = self.lcd.dateTime()
        
    def displaySituation(self):
        if self.localtime <= self.timeEnd.dateTime() :
            self.receiveTime.emit(self.localtime)
        else:
            self.stop()
    def __del__(self):
        self.timer.stop()
        self.thread.wait()
        
    def accelerateur(self,i):
        self.msecs = 1000 *    int(self.cb.currentText())
            
    def next(self):  
        self.timer.stop()  
        self.previousTime = -self.localtime.msecsTo(REFERENCE_TIME);
        self.localtime = self.localtime.addMSecs(self.msecs);
        self.currentTime  = -self.localtime.msecsTo(REFERENCE_TIME);
        self.lcd.setTime(self.localtime)
        self.displaySituation()
        
    def prev(self):    
        self.timer.stop()
        self.previousTime = -self.localtime.msecsTo(REFERENCE_TIME);
        self.localtime = self.localtime.addMSecs(-self.msecs);
        self.currentTime  = -self.localtime.msecsTo(REFERENCE_TIME);
        self.lcd.setTime(self.localtime)
        self.displaySituation()
 
    def pause(self):
 
        self.thread.terminate()
        while  self.thread.isFinished()==False :
            {
            }
#        self.nextbutton.setEnabled(True);
#        self.prevbutton.setEnabled(True); 
        self.playbutton.setEnabled(True);
        self.lcd.timeChanged.connect(self.timeModification)
        self.pauseTime.emit()
    
    def setRunTime(self,currentTime =QDateTime()):
       
        t_value = REFERENCE_TIME.msecsTo(currentTime)
 
        self.lcd.setDateTime(currentTime)
        self.progressBar.setValue(t_value)
      
    def cycle(self):
        
        #self.stop()
        
        value, ok = QInputDialog().getInt(self, "Monte Carlo runs",
                                     "number of MCMC runs:", 100,
                                     1,100,1)
     
 
        if ok:
            self.stopbutton.setEnabled(False)
            self.playbutton.setEnabled(False)
#            self.nextbutton.setEnabled(False)
            #self.prevbutton.setEnabled(False)
            self.pausebutton.setEnabled(False)
            self.runMonteCarlo.emit("{}".format(value))

    def reEnable(self):
        self.stopbutton.setEnabled(True)
        self.playbutton.setEnabled(True)
#        self.nextbutton.setEnabled(True)
#        self.prevbutton.setEnabled(True)
        self.pausebutton.setEnabled(True)

    def stop(self):
        self.timer.terminate()
        self.thread.terminate()
       
        while  self.thread.isFinished()==False :
            {
     
            }
 
        self.OFFSET         = 0
        self.localtime = REFERENCE_TIME  
        self.playbutton.setEnabled(True)
#        self.nextbutton.setEnabled(True);
#        self.prevbutton.setEnabled(True); 
        self.lcd.timeChanged.connect(self.timeModification)
        self.stopTime.emit(self.lcd.dateTime())
 
        self.lcd.setDateTime(self.localtime)
 
        self.previousTime = 0 
        self.currentTime  = 0 
        self.displaySituation()
        
    def synchronization(self,_sTime = QDateTime() ):
        
        #synchronization depuis le server
#        
#        self.nextbutton.setEnabled(False)
#        self.prevbutton.setEnabled(False)
#        self.playbutton.setEnabled(False)
#        self.stopbutton.setEnabled(False)
#        self.runCycleButton.setEnabled(False)
        
        #self.lcd.timeChanged.disconnect(self.timeModification)
        #print(_sTime.toString('hh:mm:ss.z'))
       
        self.lcd.setDateTime(_sTime)
        self.BEGIN_TIME     =  _sTime
        self.timer.startTime=  _sTime
        self.timeEnd.setDateTime(_sTime.addSecs(self.depthTime))
    def startThread(self ):    
#        self.nextbutton.setEnabled(False)
 #       self.prevbutton.setEnabled(False)
        self.playbutton.setEnabled(False)
   
        self.lcd.timeChanged.disconnect(self.timeModification)
 
        self.timer.startTime      = QDateTime.currentDateTime()
   
        self.OFFSET         = 0
        self.BEGIN_TIME     =    self.lcd.dateTime()  
 
        if not self.thread.isRunning():
            self.thread.start()
    def start(self ):

       
     
        self.startTime.emit(self.localtime)
#-------- Slots ------------------------------------------
 
    def Time(self):
 
        self.previousTime   = self.localtime 
        self.OFFSET         = self.timer.startTime.msecsTo(QDateTime.currentDateTime()) 
 
        self.localtime      = self.BEGIN_TIME.addMSecs(self.OFFSET)
        self.currentTime    = self.localtime
        self.lcd.setDateTime(self.localtime)
 
        self.displaySituation()
    
    def newEndTime(self,date = QDateTime()):
        
        self.timeEnd.setDateTime(date)
        
    def newReferenceTime(self,ref = QDateTime()):
        global REFERENCE_TIME
        REFERENCE_TIME      = ref 
        self.localtime      = ref 
        self.OFFSET         = QDateTime.currentDateTime().msecsTo(REFERENCE_TIME)
        self.lcd.setDateTime(self.localtime)
        self.timeEnd.setDateTime(REFERENCE_TIME.addSecs(self.depthTime))
        
    def initUI(self):
 
        self.timer = Timer()
    
 
        self.OFFSET         = QDateTime.currentDateTime().msecsTo(REFERENCE_TIME)
 
        self.thread         = QThread()
 
        self.timer.sendTime.connect(self.Time)
        self.timer.moveToThread(self.thread)
    
        self.thread.started.connect(self.timer.run)
        
        self.timer.startTime      = QDateTime.currentDateTime()
        #self.thread.finished.connect(self.timer.terminate)
       
      
        #self.timer.timeout.connect(self.Time)
        self.msecs = 10


        self.localtime      = REFERENCE_TIME 
        self.previousTime   = 0 #Temps precedent en s
        self.currentTime    = 0#Temps courant en s
        sidepanel           = self.builPalyerBar()
        
             
        #---------Window settings --------------------------------
        
             

        layout = QHBoxLayout()
        layout.addWidget(sidepanel, Qt.AlignHCenter | Qt.AlignVCenter)
        #layout.addWidget(self.lcd, Qt.AlignHCenter | Qt.AlignVCenter)
        self.setLayout(layout)
        self.show
      
        