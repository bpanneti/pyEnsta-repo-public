# -*- coding: utf-8 -*-
"""
Created on Mon Jul  6 15:58:39 2020

@author: pannetier
"""
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtOpenGL import *
from PyQt5.QtWidgets import *
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)
from matplotlib.patches import Rectangle
from matplotlib.collections import PatchCollection
from matplotlib.figure import Figure
 
from matplotlib.backend_bases import key_press_handler
import matplotlib.dates as mdates
import array as arr
import numpy as np
import os
from point import Position,utm_getZone,utm_isNorthern,utm_isDefined,REFERENCE_POINT 


linestyles = ['-', '--', '-.', ':']

class classTaxonomie :
    
    def __init__(self):
        
      
            self.pere = None
            self.fils = []
            self.name = "NOTHING"
            self.cost = 0.0
    def copy(self,_node):
        newNode         =  classTaxonomie()

        newNode.name    =  _node.name
        newNode.cost    =  _node.cost
        
        for _fils in _node.fils:
            filius      = self.copy(_fils)
            newNode.fils.append(filius)
            filius.pere = newNode 
        return newNode
    def printRec(self,depth = 0):
        msg = ''
        for i in rane(0,depth):
          msg+='-'
        print([msg + '>name : ', self.name,' with value', self.cost] )
        c = depth +1
        for _fils in self.fils:
            _fils.printRec(c)
        return

class windows_Mop(QObject):
    def __init__(self):
        super(windows_Mop, self).__init__()
        #widgets
        self.locationWidget         = QWidget()
        self.locationErrorWidget    = QWidget()
        self.velocityErrorWidget    = QWidget()
        self.velocityWidget         = QWidget()
        
        self.locationWidget.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.locationErrorWidget.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.velocityErrorWidget.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.velocityWidget.setWindowFlag(Qt.WindowCloseButtonHint, False)
        
        self.displayLocationWidget      = True
        self.displayLocationErrorWidget = True
        self.displayVelocityErrorWidget = True
        self.displayVelocityWidget      = True
        
        self.target_mops = [] #liste de MOP target de plusieurs algorithmes
        
        
    def updateDisplay(self):
#        if self.displayLocationWidget == False:
#            self.locationWidget.hide()
#        else:
#            self.locationWidget.show()
        if self.displayLocationErrorWidget == False:
            self.locationErrorWidget.hide()
        else:
            self.locationErrorWidget.show()
        if self.displayVelocityErrorWidget == False:
            self.velocityErrorWidget.hide()
        else:
            self.velocityErrorWidget.show() 
        if self.displayVelocityWidget == False:
            self.velocityWidget.hide()
        else:
            self.velocityWidget.show() 
    def displayLocations(self):
        widget = self.locationWidget;
        fig = Figure((5.0, 4.0), dpi=100)
        axes =  fig.add_subplot(111)
   
        canvas = FigureCanvas( fig)
        canvas.setFocusPolicy(Qt.StrongFocus)
        canvas.setFocus()
        canvas.draw()
        canvas.show()
        axes.grid(True)
         
        navi_toolbar = NavigationToolbar(canvas, widget) #createa navigation toolbar for our plot canvas
        
        vbl = QVBoxLayout()
        vbl.addWidget(canvas)
        vbl.addWidget(navi_toolbar)
        widget.setLayout( vbl )
        target = self.target_mops[0].target
        widget.setWindowTitle(('location of target %s * %s ')%(str(target.id),str(target.name)))
        axes.set_title(('location  of target %s * %s ')%(str(target.id),str(target.name)))
        axes.set_xlabel('longitude (in degree)')
        axes.set_ylabel('latitude (in degree)')
        longitude = []
        latitude  = []
        for t,p in self.groundTruthLocations :
  
            longitude.append(p.longitude)
            latitude.append(p.latitude)
            
        axes.plot(longitude,latitude , linewidth= 2,label='ground truth')
 
        
        longitude = []
        latitude  = []
        if self.displayLocationWidget:
            widget.show()
        for t,p in self.stateLocations :
 
            longitude.append(p.longitude)
            latitude.append(p.latitude)
        axes.plot(longitude,latitude, 'mo',label='associated states', linewidth= 2)
        axes.legend(loc='upper right')
        
    def displayVelocity(self):
        widget = self.velocityWidget
        fig = Figure((5.0, 4.0), dpi=100)
        axes =  fig.add_subplot(111)
        canvas = FigureCanvas( fig)
        canvas.setFocusPolicy(Qt.StrongFocus)
        canvas.setFocus()
        canvas.draw()
        canvas.show()
        axes.grid(True)
         
        navi_toolbar = NavigationToolbar(canvas, widget) #createa navigation toolbar for our plot canvas
        
        vbl = QVBoxLayout()
        vbl.addWidget(canvas )
        vbl.addWidget(navi_toolbar)
        widget.setLayout( vbl )
        target = self.target_mops[0].target
        widget.setWindowTitle(('velocity  of target %s * %s ')%(str(target.id),str(target.name)))
        axes.set_title(('velocity  of target %s * %s ')%(str(target.id),str(target.name)))
        axes.set_xlabel('date')
        axes.set_ylabel('velocity (in m/s)')
        fig.tight_layout()
        #date
        
        dates = []
 
        for _date in self.target_mops[0].timeLine :
                dates.append(_date.toPyDateTime())
    
        _max = 0
        for _mop in self.target_mops: 
            c = np.max([_mop.velocity])
            if c> _max:
                _max = c
        
        y = _max*np.array(self.target_mops[0].targetDetection)
        y2 =[]
        for u in y:
            y2.append(float(u))
            
        axes.plot(dates, y,'--',label='time detection' , color='#ecbf16',linewidth=1)
        axes.fill_between(dates,0,y2,facecolor='#ecdf16',alpha=0.5)    
        #plot
        for _mop,u in zip(self.target_mops,range(0,len(self.target_mops))):
#            dates = []
#            for _date in _mop.timeLine :
#                dates.append(_date.toPyDateTime())
            
    
            
           # _max = np.max(_mop.velocityError) 


            axes.plot(dates, _mop.velocity,label=_mop.nom,linestyle=linestyles[u])
        
            for label in axes.get_xticklabels():
                label.set_rotation(40)
                label.set_horizontalalignment('right')
            axes.legend(loc='upper right')    
            fig.tight_layout()
        if self.displayVelocityWidget:
                widget.show()      
    def displayVelocityError(self):
        widget = self.velocityErrorWidget
        fig = Figure((5.0, 4.0), dpi=100)
        axes =  fig.add_subplot(111)
        canvas = FigureCanvas( fig)
        canvas.setFocusPolicy(Qt.StrongFocus)
        canvas.setFocus()
        canvas.draw()
        canvas.show()
        axes.grid(True)
         
        navi_toolbar = NavigationToolbar(canvas, widget) #createa navigation toolbar for our plot canvas
        
        vbl = QVBoxLayout()
        vbl.addWidget(canvas )
        vbl.addWidget(navi_toolbar)
        widget.setLayout( vbl )
        target = self.target_mops[0].target
        widget.setWindowTitle(('velocity error of target %s * %s ')%(str(target.id),str(target.name)))
        axes.set_title(('velocity error of target %s * %s ')%(str(target.id),str(target.name)))
        axes.set_xlabel('date')
        axes.set_ylabel('error (in m/s)')
        fig.tight_layout()
        #date
        
        dates = []
 
        for _date in self.target_mops[0].timeLine :
                dates.append(_date.toPyDateTime())
    
        _max = 0
        for _mop in self.target_mops: 
            c = np.max([_mop.velocityError])
            if c> _max:
                _max = c
        
        y = _max*np.array(self.target_mops[0].targetDetection)
        y2 =[]
        for u in y:
            y2.append(float(u))
            
        axes.plot(dates, y,'--',label='time detection' , color='#ecbf16',linewidth=1)
        axes.fill_between(dates,0,y2,facecolor='#ecdf16',alpha=0.5)    
        #plot
        for _mop,u in zip(self.target_mops,range(0,len(self.target_mops))):
#            dates = []
#            for _date in _mop.timeLine :
#                dates.append(_date.toPyDateTime())
            
    
            
           # _max = np.max(_mop.velocityError) 


            axes.plot(dates, _mop.velocityError,label=_mop.nom,linestyle=linestyles[u])
        
            for label in axes.get_xticklabels():
                label.set_rotation(40)
                label.set_horizontalalignment('right')
            axes.legend(loc='upper right')    
            fig.tight_layout()
        if self.displayVelocityErrorWidget:
                widget.show()
                
    def displayLocationError(self):
        widget = self.locationErrorWidget
        fig = Figure((5.0, 4.0), dpi=100)
        axes =  fig.add_subplot(111)
        canvas = FigureCanvas( fig)
        canvas.setFocusPolicy(Qt.StrongFocus)
        canvas.setFocus()
        canvas.draw()
        canvas.show()
        axes.grid(True)
         
        navi_toolbar = NavigationToolbar(canvas, widget) #createa navigation toolbar for our plot canvas
        
        vbl = QVBoxLayout()
        vbl.addWidget(canvas )
        vbl.addWidget(navi_toolbar)
        widget.setLayout( vbl )
        target = self.target_mops[0].target
        widget.setWindowTitle(('location error of target %s * %s ')%(str(target.id),str(target.name)))
        axes.set_title(('location error of target %s * %s ')%(str(target.id),str(target.name)))
        axes.set_xlabel('date')
        axes.set_ylabel('error (in m)')
        #date
        
        dates = []
 
        for _date in self.target_mops[0].timeLine :
                dates.append(_date.toPyDateTime())
    
        _max = 0

        for _mop in self.target_mops: 

            c = np.max([_mop.locationError+_mop.stdLocationError])
            if c> _max:
                _max = c
                
                
#        print(_max)
#        print(self.target_mops[0].targetDetection)
        y = _max*np.array(self.target_mops[0].targetDetection)
        y2 =[]
        for u in y:
            y2.append(float(u))
            
        axes.plot(dates, y,'--',label='time detection' , color='#ecbf16',linewidth=1)
        axes.fill_between(dates,0,y2,facecolor='#ecdf16',alpha=0.5)    
        #standard deviation    
            
 
  
        #plot
        for _mop,u in zip(self.target_mops,range(0,len(self.target_mops))):
        #plot
    
            axes.plot(dates, _mop.locationError,label=_mop.nom,linestyle=linestyles[u])
            #axes.plot(dates, _mop.locationError+_mop.stdLocationError, lable = 'std location','--','color blue')
            #§axes.fill_between(dates,A,B,facecolor='#ecdf16',alpha=0.5)     
            for label in axes.get_xticklabels():
                label.set_rotation(40)
                label.set_horizontalalignment('right')
        axes.legend(loc='upper right')
        fig.tight_layout()
        if self.displayLocationErrorWidget:
                    widget.show()
        
class target_Mop(QObject):
    
    def __init__(self,_target = None):
        super(target_Mop, self).__init__()
        
        self.nom             = 'none' #nom de l'agorithme
        
        self.nbRun           = -1 
        self.timeLine        = []
        self.targetDetection = []
        self.plots           = []
        self.target          = _target
        self.locationError   = []   
        self.stdLocationError= []                       
        self.velocityError   = [] 
        self.velocity        = [] 
        self.stdVelocityError= []                         
        self.correctClassificationProbability = []          
        self.classificationProbability = 0                  
        self.classificationTaxonomie   = None
        self.associatedTrack        = []
        
        self.stateLocations         = []
        self.groundTruthLocations   = []
        self.associated             = []
        self.nbAssociatedTarget     = 0
        self.trackContinuity        = 0
        self.detectionProbability   = 0
    
        self.ARMSE_Location         = 0
        self.ARMSE_Velocity         = 0
  
        
    def computeAverageMeasure(self):
        mean = 0
        c    = 0
        A=[]
        for u in self.locationError:
            if u !=0:
                A.append(u)
                mean+=u
                c=c+1
       
        if c == 0:
            self.ARMSE_Location = mean
        else:
            self.ARMSE_Location = mean/c
        mean = 0
        c    = 0
        for u in self.velocityError:
            if u !=0:
                mean+=u
                c=c+1
        if c == 0:
            self.ARMSE_Velocity = mean
        else:        
            self.ARMSE_Velocity = mean/c
        
    def setTrackerName(self,name='none'):
        self.nom = name
    def constructTree(self, _node = classTaxonomie()):
        
        if _node.name == self.target.type.name:
            _node.cost = 1
            return 1
        for _fils in  _node.fils:
            return self.constructTree(_fils)
        _node.cost =0
        return 0
    
    def setTaxonomieClassification(self,_class = classTaxonomie()):
        
        #---------------------------------------------
        #self.classificationTaxonomie = _class.copy()
        #self.constructTree(self.classificationTaxonomie)
        #-----------------------------------------------
        #display
        #-----------------------------------------------
        #self.classificationTaxonomie.printRec()
        #-----------------------------------------------
        print('end class') 
        
        
    def save(self, path):   

        if not os.path.exists(path):
            os.mkdir(path)
            print("Directory " , path ,  " Created ")
        else:    
            print("Directory " , path ,  " already exists")
                
        np.save(path+str("/")+'target_%s_targetDetection'%self.target.id,self.targetDetection)
        np.save(path+str("/")+'target_%s_locationError'%self.target.id,self.locationError)
        np.save(path+str("/")+'target_%s_velocityError'%self.target.id,self.velocityError)
        np.save(path+str("/")+'target_%s_velocity'%self.target.id,self.velocity)
        np.save(path+str("/")+'target_%s_stdLocationError'%self.target.id,self.stdLocationError)
        np.save(path+str("/")+'target_%s_stdVelocityError'%self.target.id,self.stdVelocityError)
        np.save(path+str("/")+'target_%s_correctClassificationProbability'%self.target.id,self.correctClassificationProbability)
        np.save(path+str("/")+'target_%s_classificationProbability'%self.target.id,self.classificationProbability)
        np.save(path+str("/")+'target_%s_associatedTrack'%self.target.id,self.associatedTrack)
        np.save(path+str("/")+'target_%s_nbAssociatedTarget'%self.target.id,self.nbAssociatedTarget)
        np.save(path+str("/")+'target_%s_trackContinuity'%self.target.id,self.trackContinuity)
        np.save(path+str("/")+'target_%s_detectionProbability'%self.target.id,self.detectionProbability)
    def setRun(self,nbRun=1):
        self.nbRun  = nbRun
    def setTimeLine(self,_time):
        self.timeLine  = _time
        self.targetDetection = np.zeros([len(_time),1])
        self.plots           = np.zeros([len(_time),1])
        self.locationError = np.zeros([len(_time),1])
        self.velocityError = np.zeros([len(_time),1])
        self.velocity      = np.zeros([len(_time),1])
        self.stdLocationError = np.zeros([len(_time),1])
        self.stdVelocityError = np.zeros([len(_time),1])
        self.correctClassificationProbability = np.zeros([len(_time),1]) 
        self.associated         = [False for i in range(len(_time))]
        self.associatedTrack    = [-1 for i in range(len(_time))]
    def detected(self,_time = QDateTime() ):
        for t,u in zip(self.timeLine,range(0,len(self.timeLine))):
                if t == _time :
                    
                    self.targetDetection[u] = 1
             
    def reset(self,_time):
        self.associated         = [False for i in range(len(_time))]
        self.associatedTrack    = [-1 for i in range(len(_time))]    

    def addLocations(self,grounTruth = Position(),state = Position(),date =QDateTime()):
           
           self.stateLocations.append((date,state))
           self.groundTruthLocations.append((date,grounTruth))
    def computeClassificationProbability(self):
        P = 0
        c = 0
        for u in range(0,len(self.associated)):
            if self.associated[u]:
                c = c+1
            if self.associated[u] and self.correctClassificationProbability[u]!=0 : 
                P = P+1
 
        if c!=0:        
            self.classificationProbability = P/c *100 
    
    def computeClassLevelProbability(self,_class):
            pass
    def addTrackClass(self,_class, _time = QDateTime(),_classTaxonomie= classTaxonomie()):
        for t,u in zip(self.timeLine,range(0,len(self.timeLine))):
            
            #    if t == _time and  self.associated[u]==True :
                    
                   # _classTaxonomie.
              #     self.computeClassLevelProbability(_class)
                    
                    
                    
                if t == _time and self.associated[u]==True and self.target.type == _class :
                    self.correctClassificationProbability[u] += 1 / self.nbRun 
                    
    def targetIsAssociated(self,_time = QDateTime() ):  
 
        for t,u in zip(self.timeLine,range(0,len(self.timeLine))):
            
                if t == _time and self.associated[u]==True:
                    return True
        return False
    def targetIsDetected   (self,_time = QDateTime() ):   
        for t,u in zip(self.timeLine,range(0,len(self.timeLine))):
                if t == _time and self.targetDetection[u]==1:
                    return True
        return False
    def addCurrentTarget (self,idTrack = -1,_time =QDateTime()):
        for t,u in zip(self.timeLine,range(0,len(self.timeLine))):
                if t == _time  :
        
                    self.associatedTrack[u] = idTrack
                    self.associated[u]      = True
                    if idTrack not in self.associatedTrack:
                      self.nbAssociatedTarget+=1
    def addVelocity(self,vel = [],_time =QDateTime()):
        for t,u in zip(self.timeLine,range(0,len(self.timeLine))):
                if t == _time :
              
                    value = np.linalg.norm([vel.x,vel.y,vel.z])
                    self.velocity[u] += value/self.nbRun                  
    def addVelocityError(self,value = 0,_time =QDateTime()):
        for t,u in zip(self.timeLine,range(0,len(self.timeLine))):
                if t == _time :
                    self.velocityError[u] += value/self.nbRun
    def addStdVelocityError(self,value = 0,_time =QDateTime()):
        for t,u in zip(self.timeLine,range(0,len(self.timeLine))):
                if t == _time :
                    self.stdVelocityError[u] += value/self.nbRun
    def addLocationError(self,value = 0,_time =QDateTime()):
     
        for t,u in zip(self.timeLine,range(0,len(self.timeLine))):
            
                if t == _time :
                    self.locationError[u] += value/self.nbRun
    def addStdLocationError(self,value = 0,_time =QDateTime()):
        for t,u in zip(self.timeLine,range(0,len(self.timeLine))):
                if t == _time :
                    self.stdLocationError[u] += value/self.nbRun      
    def addPlots(self,value = 0,_time =QDateTime()):
        for t,u in zip(self.timeLine,range(0,len(self.timeLine))):
                if t == _time :
                    self.plots[u]  += value/self.nbRun 
    def computetrackProbabilityDetection(self):
        
        targetDuration   = 0#-1
        detection        = 0#-1 
    
        for u in range(0,len(self.targetDetection)):
            if self.targetDetection[u]==1:
                targetDuration+=1

        for u in range(0,len(self.plots)):
            if self.plots[u]>=1:
                detection+=1
                
        if targetDuration == 0:
            self.detectionProbability =0
        else:
                self.detectionProbability +=  detection/(targetDuration*self.nbRun) 
        
        
          
    def computeTrackContinuity(self):
        
#        startTime  = QDateTime()
#        endTime    = QDateTime()
        targetDuration   = 0#-1
        trackContinuity  = 0
        for u in range(0,len(self.targetDetection)):
            if self.targetDetection[u]==1:
                targetDuration+=1
#                endTime   = self.timeLine[u]
#                
#                if trackDuration == -1:
#                    startTime = self.timeLine[u]
#                    
#                trackDuration  = startTime.secsTo(endTime)
        
        #_idTracks = []
        
        for i in range(0,len(self.associatedTrack)):
            if self.associatedTrack[i] != -1:
                #_idTracks.append(self.associatedTrack[i])
                trackContinuity+=1
    
        
        if targetDuration != 0:
            self.trackContinuity +=  trackContinuity /(targetDuration* self.nbRun)
        