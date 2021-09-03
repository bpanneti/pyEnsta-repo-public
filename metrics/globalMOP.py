# -*- coding: utf-8 -*-
"""
Created on Tue Jul  7 13:21:00 2020

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
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import array as arr
import numpy as np
import os
from point import Position,utm_getZone,utm_isNorthern,utm_isDefined,REFERENCE_POINT
linestyles = ['-', '--', '-.', ':']
class window_globalMOP:
    
    def __init__(self):
         
        #list of globalMops
        
        self.globalMOP                = []
        
        #widgets
        self.widgetNumberOfValidTrack = QWidget()
        self.widgetCompletness        = QWidget() 
        self.widgetFalseTrack         = QWidget()  
        self.widgetTrackContinuity    = QWidget() 
        self.widgetClassProbability   = QWidget()  
        self.widgetOSPA               = QWidget()  
        self.widgetPacketSize         = QWidget() 
        self.widgetExecutionTime      = QWidget() 
        
        self.widgetNumberOfValidTrack.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.widgetCompletness.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.widgetFalseTrack.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.widgetTrackContinuity.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.widgetClassProbability.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.widgetOSPA.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.widgetPacketSize.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.widgetExecutionTime.setWindowFlag(Qt.WindowCloseButtonHint, False)
        
        
        self.displayWidgetCompletness        = True
        self.displayWidgetNumberOfValidTrack = True
        self.displayWidgetTrackContinuity    = True
        self.displayWidgetClassProbability   = True
        self.displayWidgetOSPA               = True
        self.displayWidgetExecutionTime      = True
        self.displayWidgetPacketSize         = True
    def clear(self):
        del  self.globalMOP[:]
        self.globalMOP = []
    def save(self,_path):
        for u in range(0,len(self.globalMOP)):
            Mypath = _path+'/'+self.globalMOP[u].nom
            if not os.path.exists(Mypath):
                os.mkdir(Mypath)
                print("Directory " , Mypath ,  " Created ")
            else:    
                print("Directory " , Mypath ,  " already exists")
             
            self.globalMOP[u].save(Mypath) 
    def displayOSPA(self):
 
        widget = self.widgetOSPA
        fig = Figure((5.0, 4.0), dpi=100)
        axes =  fig.add_subplot(111)
   
        canvas = FigureCanvas( fig)
        canvas.setFocusPolicy(Qt.StrongFocus)
        canvas.setFocus()
        canvas.draw()
        canvas.show()
 
         
        navi_toolbar = NavigationToolbar(canvas, widget) #createa navigation toolbar for our plot canvas
        
        vbl = QVBoxLayout()
        vbl.addWidget(canvas )
        vbl.addWidget(navi_toolbar)
        widget.setLayout( vbl )
        
        if self.displayWidgetOSPA:
            widget.show()
            
        dates = []
        for _date in self.globalMOP[0].timeLine :
            dates.append(_date.toPyDateTime())
            
        for u in range(0,len(self.globalMOP)):
            axes.plot(dates, self.globalMOP[u].OSPA ,label=self.globalMOP[u].nom ,linewidth=1,linestyle=linestyles[u])
        
        widget.setWindowTitle( 'optimal sub-pattern assignment'  )
        axes.set_title('OSPA distance' )
        axes.set_ylabel('precision (in m)')
        axes.set_xlabel('time')
        #axes.set_xticks(y_pos, idTargets)
        axes.grid(axis='y', alpha=0.75)
        axes.legend(loc='upper right')
        fig.tight_layout()
    def displayClassificationProbability(self,_mopTargets =[]):
        widget = self.widgetClassProbability
        fig = Figure((5.0, 4.0), dpi=100)
        axes =  fig.add_subplot(111)
   
        canvas = FigureCanvas( fig)
        canvas.setFocusPolicy(Qt.StrongFocus)
        canvas.setFocus()
        canvas.draw()
        canvas.show()
 
         
        navi_toolbar = NavigationToolbar(canvas, widget) #createa navigation toolbar for our plot canvas
        
        vbl = QVBoxLayout()
        vbl.addWidget(canvas )
        vbl.addWidget(navi_toolbar)
        widget.setLayout( vbl )
        if self.displayWidgetClassProbability:

            widget.show()
            
        d           = []
        idTargets   = []
        for u in _mopTargets:
            d.append(u.classificationProbability)
            idTargets.append(('{%s/ %s/ %s}')%(u.target.id,u.target.name,u.target.type.name))
 
        y_pos = np.arange(len(idTargets))
        axes.bar(idTargets, d, align='center', alpha=0.5)
 
        widget.setWindowTitle( 'correct track classification'  )
        axes.set_title('correct track classification' )
        axes.set_ylabel('percentage of correct track classification')
        axes.set_xlabel('target id')
        #axes.set_xticks(y_pos, idTargets)
        axes.grid(axis='y', alpha=0.75)    
        fig.tight_layout()
    def displayTrackContinuity(self,_mopTargets =[]):
        widget = self.widgetTrackContinuity
        fig = Figure((5.0, 4.0), dpi=100)
        axes =  fig.add_subplot(111)
   
        canvas = FigureCanvas( fig)
        canvas.setFocusPolicy(Qt.StrongFocus)
        canvas.setFocus()
        canvas.draw()
        canvas.show()
 
         
        navi_toolbar = NavigationToolbar(canvas, widget) #createa navigation toolbar for our plot canvas
        
        vbl = QVBoxLayout()
        vbl.addWidget(canvas )
        vbl.addWidget(navi_toolbar)
        widget.setLayout( vbl )
        
        npTrackers = len(self.globalMOP)
        dimTargets = len(_mopTargets[0][1])
        
        width = 0.75 / npTrackers  # the width of the bars
        indice = np.arange(0,dimTargets*npTrackers,npTrackers)
        if self.displayWidgetTrackContinuity:

            widget.show()
            
         
        idTargets   = []
        flag = True
        for _tracker,numTracker in zip(_mopTargets,range(0,npTrackers)):
            d           = [] 
            for _target,u in zip(_tracker[1],indice):
                d.append(_target.trackContinuity)
                if flag:
                    idTargets.append(('{%s/ %s/ %s}')%(_target.target.id,_target.target.name,_target.target.type.name))
     
            axes.bar(indice + width*numTracker , d, width=width, alpha=0.5,label=self.globalMOP[numTracker].nom)#align='center'
            flag = False
        #y_pos = np.arange(len(idTargets))
        
        axes.set_xticks(indice)
        axes.set_xticklabels( idTargets )
        widget.setWindowTitle( 'track continuity'  )
        axes.set_title('track continuity' )
        axes.set_ylabel('rate')
        axes.set_xlabel('target id')
        #axes.set_xticks(y_pos, idTargets)
        axes.grid(axis='y', alpha=0.75)
        axes.legend(loc='upper right')
        fig.tight_layout()
    def  updateDisplay(self):
        if  self.displayWidgetCompletness:
            self.widgetCompletness.show()
        else:
            self.widgetCompletness.hide()
        if self.displayWidgetNumberOfValidTrack:
            self.widgetNumberOfValidTrack.show()
        else:
            self.widgetNumberOfValidTrack.hide()
        if self.displayWidgetTrackContinuity:
            self.widgetTrackContinuity.show()
        else:
            self.widgetTrackContinuity.hide()
        if self.displayWidgetClassProbability:
            self.widgetClassProbability.show()
        else:
            self.widgetClassProbability.hide()
            

        if self.displayWidgetOSPA:
            self.widgetOSPA.show()
        else:
            self.widgetOSPA.hide()
            
        if self.displayWidgetPacketSize:
            self.widgetPacketSize.show()
        else:
            self.widgetPacketSize.hide()
            
        if self.displayWidgetExecutionTime:
            self.widgetExecutionTime.show()
        else:
            self.widgetExecutionTime.hide()
            
    def displayFalseTrack(self):
        widget = self.widgetCompletness
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
        if self.displayWidgetCompletness:

            widget.show()
        widget.setWindowTitle( 'number of false track'  )
        axes.set_title('false track' )
        axes.set_xlabel('number of false track')
        axes.set_ylabel('date')
        dates = []
        for _date in self.timeLine :
            dates.append(_date.toPyDateTime())
        for u in range(0,len(self.globalMOP)):
            axes.plot(dates, self.globalMOP[u].NFT ,label=self.globalMOP[u].nom,linewidth=1,linestyle = linestyles[u])
        
        
        axes.legend(loc='upper right') 
        fig.tight_layout()
    def displayCompletness(self):
        widget = self.widgetCompletness
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
        widget.show()
        widget.setWindowTitle( 'Measure of Completness'  )
        axes.set_title('Measure of Completness'  )
        axes.set_xlabel('date')
        axes.set_ylabel('rate')
        dates = []
        for _date in self.globalMOP[0].timeLine :
            dates.append(_date.toPyDateTime())

        for u in range(0,len(self.globalMOP)):    
            axes.plot(dates, self.globalMOP[u].MOC ,label=self.globalMOP[u].nom,linewidth=1,linestyle=linestyles[u])
        
        
        axes.legend(loc='upper right') 
        fig.tight_layout()
        
    def displayExecutionTime(self):    
        widget = self.widgetExecutionTime
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
        widget.show()
        widget.setWindowTitle( 'Execution time'  )
        axes.set_title('Measure of  execution time')
        axes.set_xlabel('date')
        axes.set_ylabel('elapsed time (in msec)')
        dates = []
        for _date in self.globalMOP[0].timeLine :
            dates.append(_date.toPyDateTime())
            
        for u in range(0,len(self.globalMOP)):
            a_dates =[]
            a_packet_Receides = []
            for _date,i in zip(dates,range(0,len(self.globalMOP[u].ToE))):
                if self.globalMOP[u].ToE[i]!=0:
                    a_dates.append(_date)
                    a_packet_Receides.append(self.globalMOP[u].ToE[i])
         
            axes.plot(a_dates, a_packet_Receides ,label=self.globalMOP[u].nom ,linewidth=1,linestyle=linestyles[u])
        axes.legend(loc='upper right')  
        fig.tight_layout()
    def displayPacketSize(self):    
        widget = self.widgetPacketSize
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
        widget.show()
        widget.setWindowTitle( 'Packet size'  )
        axes.set_title('Measure of  packet size'  )
        axes.set_xlabel('date')
        axes.set_ylabel('ko')
        dates = []
        for _date in self.globalMOP[0].timeLine :
            dates.append(_date.toPyDateTime())
            
       
        for u in range(0,len(self.globalMOP)):
            a_dates = []
            a_packet_Track = []
            a_packet_Receides = []
            for _date,i in zip(dates,range(0,len(self.globalMOP[u].Packet_Track))):
                if self.globalMOP[u].Packet_Track[i]!=0:
                    a_dates.append(_date)
                    a_packet_Track.append(self.globalMOP[u].Packet_Track[i])
            axes.plot(a_dates, a_packet_Track ,   label=self.globalMOP[u].nom+'_Packet_Track'  ,linewidth=1,linestyle=linestyles[u])
            a_dates = []
            for _date,i in zip(dates,range(0,len(self.globalMOP[u].Packet_Received))):
                if self.globalMOP[u].Packet_Received[i]!=0:
                    a_dates.append(_date)
                    a_packet_Receides.append(self.globalMOP[u].Packet_Received[i])                   
            axes.plot(a_dates, a_packet_Receides,label=self.globalMOP[u].nom+'_Packet_Detection'  ,linewidth=1,linestyle=linestyles[u])
        axes.legend(loc='upper right')
        fig.tight_layout()
    def displayNumberOfValidTrack(self):
    
        widget = self.widgetNumberOfValidTrack
        fig = Figure((5.0, 4.0), dpi=100)
        if self.displayWidgetNumberOfValidTrack:
                widget.show()
        for u in range(0,len(self.globalMOP)):
            axes =  fig.add_subplot(len(self.globalMOP),1,u+1)
       
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
      
            widget.setWindowTitle( 'Track Cardinality Measures : '+str(self.globalMOP[u].nom)  )
            
            axes.set_title('Track Cardinality Measures :'+str(self.globalMOP[u].nom) )
            axes.set_xlabel('date')
            axes.set_ylabel('number')
            dates = []
            for _date in self.globalMOP[u].timeLine :
                dates.append(_date.toPyDateTime())
            
            axes.plot(dates, self.globalMOP[u].NVT ,label='number of valid tracks' ,linewidth=1,linestyle=linestyles[0])
            axes.plot(dates, self.globalMOP[u].NMT ,label='number of missed tracks' ,linewidth=1,linestyle=linestyles[1])
            axes.plot(dates, self.globalMOP[u].NFT ,label='number of false tracks' ,linewidth=1,linestyle=linestyles[2])
      
            axes.legend(loc='upper right') 
            fig.tight_layout()
class MCMC_Mop :
    #cardinality metrics
    def __init__(self,idTracker = -1):
        
        self.NVT                = []        # nombre de pistes valides
        self.NMT                = []        # nombre de cibles non trackées
        self.NFT                = []        # nombre de fausses pistes
        self.MOC                = []        # mesure de complétude
        self.OSPA               = []        # distanc OSPAP
        self.ANST               = 0         # average number od swap in tack 
        self.timeLine           = []
        self.NB_MCMC            = 0         # nombre de run de Monte-Carlo
        self.ToE                = []        # axecutionTime
        self.Packet_Track       = []        # packet Size
        self.Packet_Received    = []        # packet Size
        self.nom                = 'None'    # nom de l'agorithme'
        self.idTracker          = idTracker
       
    def save(self,path):
        np.save(path+str("/")+'nvt',self.NVT)
        np.save(path+str("/")+'nmt',self.NMT)
        np.save(path+str("/")+'nft',self.NFT)
        np.save(path+str("/")+'moc',self.MOC)
        np.save(path+str("/")+'ANST',self.ANST)
        np.save(path+str("/")+'timeLine',self.timeLine)
        np.save(path+str("/")+'NB_MCMC',self.NB_MCMC)
        np.save(path+str("/")+'OSPA',self.OSPA)
        np.save(path+str("/")+'ToE',self.ToE)
        np.save(path+str("/")+'Packet_Track',self.Packet_Track)
        np.save(path+str("/")+'Packet_Received',self.Packet_Received)
      
    def computeNumberOfMissedTargets(self,_mopTargets =[]):
        
        for _t,u in zip(self.timeLine,range(0,len(self.timeLine))):
            l = 0 #nombre de cibles non associées
            for _mop in    _mopTargets:            
                if _mop.targetIsAssociated(_t)== False and _mop.targetIsDetected(_t):
                    l = l+1
            self.NMT[u] += l/self.NB_MCMC  
 
    def computeOSPA(self,date = QDateTime(),error = 0):
        for _t,u in zip(self.timeLine,range(0,len(self.timeLine))):
            if _t == date:
                self.OSPA[u] += error /  self.NB_MCMC
                
    def computeExecutionTime(self,_perfs):
      for _perf in _perfs:
              
            for _t,u in zip(self.timeLine,range(0,len(self.timeLine))):
                   _date = QDateTime.fromString(_perf[0],"yyyy-MM-dd HH:mm:ss.zzz")
                   if u < len(self.timeLine)-1 and _date >= _t  and _date <self.timeLine[u+1]:
                       self.ToE[u]   += float(_perf[1])/  self.NB_MCMC
    def computePacketSize(self,_file,_perfs):
        for _perf in _perfs:
            for _t,u in zip(self.timeLine,range(0,len(self.timeLine))):
                _date = QDateTime.fromString(_perf[0],"yyyy-MM-dd HH:mm:ss.zzz")
                if u < len(self.timeLine)-1 and _date >= _t  and _date <self.timeLine[u+1]:
                         if _file == "trackPacket": 
                            self.Packet_Track[u]+= float(_perf[1]) /  self.NB_MCMC  #Packet Size
                         if _file == "detectionPacket": 
                            self.Packet_Received[u]+= float(_perf[1])  /  self.NB_MCMC
    def computeCompletude(self,date = QDateTime(),numberOfValidTrack = 0,numberOfTrack = 0 ):     
        
        for _t,u in zip(self.timeLine,range(0,len(self.timeLine))):
            if _t == date:
                self.MOC[u] += (numberOfValidTrack / numberOfTrack) /  self.NB_MCMC    
                self.NFT[u] += (numberOfTrack - numberOfValidTrack) /  self.NB_MCMC  
    def computeNumberOfValidTrack(self,_mopTargets =[]):
        
        for _t,u in zip(self.timeLine,range(0,len(self.timeLine))):
            l = 0 #nombre de pistes valides
            for _mop in    _mopTargets:            
                if _mop.targetIsAssociated(_t):
                    l = l+1
            self.NVT[u] += l/self.NB_MCMC  
            
    def averageExecutionTime(self):
        c = 0
        for u in self.ToE  :
            if u != 0:
                c+=1
        if c==0:
            return 0
        
        return self.ToE.sum()/c
    def averagePacketTrackSize(self):
        c = 0
        for u in self.Packet_Track  :
            if u != 0:
                c+=1
        if c==0:
            return 0
        
        return self.Packet_Track.sum()/c
    def averagePacketReceivedSize(self):
 
        c = 0
        for u in self.Packet_Received  :
            if u != 0:
                c+=1
        if c==0:
            return 0
        
        return self.Packet_Received.sum()/c
    
    def setTimeLine(self,_time):
        self.timeLine   = _time
        self.MOC        = np.zeros((len(self.timeLine),1))
        self.NFT        = np.zeros((len(self.timeLine),1))
        self.NVT        = np.zeros((len(self.timeLine),1))
        self.NMT        = np.zeros((len(self.timeLine),1))
        self.OSPA       = np.zeros((len(self.timeLine),1))
        self.Packet_Track             = np.zeros((len(self.timeLine),1))
        self.Packet_Received          = np.zeros((len(self.timeLine),1))
        self.ToE        = np.zeros((len(self.timeLine),1))
        
