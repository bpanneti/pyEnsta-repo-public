# -*- coding: utf-8 -*-
"""
Created on Mon Apr 06 08:44:00 2020

@author: rgomescardoso
"""
from enum import Enum
from abc import ABCMeta, abstractmethod
from scipy.stats import chi2
#from estimator import TRACKER_TYPE
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from   matplotlib.path import Path  
import matplotlib as mpl
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)
from tool_tracking.estimator import TRACKER_TYPE
from itertools import count
import sys, math
from PyQt5.QtGui import  *
from PyQt5.QtWidgets import  *
from PyQt5.QtCore import  *
from math import atan2, sqrt
import numpy as np
from tool_tracking.motionModel import MotionModel, StateType, F, Q, h
from tool_tracking.track import Track
 
import re
class BIRTH_INIT(Enum):
    UNIFORM     = 0
    CONTOUR     = 1
 

class Gauss:
    __cnt = count(0)
    __id  = count(0)
    def __init__(self, loca, P,weight,label = -1,size=1,father = None):
        self.id             = next(self.__id)
        self.w              = weight
        self.m              = np.array(loca)
        self.P              = np.array(P, dtype=np.float64)
        self.detections     = []
        self.nbDetections   = 0
        self.meanDetections = 0
        self.lenght         = size
        self.m.resize((self.m.shape[0], 1))
        self.P.resize((self.m.shape[0], self.m.shape[0]))
        self.sigma_x  = 1.0
        self.sigma_y  = 1.0
        self.angle    = 0.0
        self.line     = np.matrix(self.m[[0,2]])
        self.father   = father   
        if label == -1:
            self.label   = next(self.__cnt)
        else:
            self.label   = label
    def distanceState(self,m):
          In    = m - self.m
          return np.linalg.norm(In[[0,2]])
        
    def distanceObs(self,z,H):
         In    = z - H@self.m
        
         return np.linalg.norm(In)
    def predict(self,deltaTime,model):
        _F = F(deltaTime, self.m.size, model[0])
        _Q = Q(deltaTime, self.m.size, model[0],model[1])
        self.m = _F@self.m
        self.P = _F@self.P@_F.T + _Q
    def computeMeanMesurement(self):
        current = self 
     
        while current!=None:
            
            self.meanDetections +=  current.nbDetections 
            current = current.father
        self.meanDetections = self.meanDetections /self.lenght    
    def attach(self,plots=[]):
        
        for lplot in plots:
            flag = True
            for _plot in self.detections:
                if _plot.id == lplot.id:
                    flag = False
                    break
            if flag:
                self.detections.append(lplot)
 
        self.nbDetections = len(self.detections)
    
        return
    
    
    def toPoint(self):
        return QPointF(self.m[0],self.m[2])
    def distStatGaussian(self,gm):
        
        In = gm.m - self.m 
        
        S  = gm.P + self.P
        
        mah_dist = np.float64( In.T @ np.linalg.inv(S)@In)
        return  mah_dist   
    def distStat(self,z,R,H):
    
         In    = z - H@self.m  
 
         S     = H@self.P@H.T + R
         mah_dist = np.float64( In.T @ np.linalg.inv(S)@In)
         return  mah_dist      
    def isValidated(self, z,R, H,seuil):
        
        if self.distStat(z,R,H) < seuil:
            return True
        return False
    def  updateCovariance(self,proba=0.95):
    
        lmbda, u = np.linalg.eigh(self.P[:3:2,:3:2])
        order = lmbda.argsort()[::-1]
        lmbda, u = lmbda[order],u[:,order]

        self.sigma_x = proba*sqrt(lmbda[0])
        self.sigma_y = proba*sqrt(lmbda[1])
        ux = u[:,0][0]
        uy = u[:,0][1]
        self.angle = atan2(uy, ux)
   
def take_weight(gm):
    return gm.w
        
class Gaussian(QObject):
    __metaclass__ = ABCMeta
    # Messagerie
    message = pyqtSignal('QString')
    birth_w = 0.001
    # list des pistes
    updatedTracks    = pyqtSignal(list)
    displayGaussian  = pyqtSignal(list)
    def __init__(self,infos):
        super(Gaussian, self).__init__()

        self.gm             = []
        self.gm_birth       = []
        self.polygons       = None
        self.survival       = 0
        self.detection      = 0  
        self.birth          = 0 
        self.model          = None
        self.minWeight      = 0
        self.dateTime       = QDateTime.currentDateTime()
        self.lambda_fa      = 0
        self.seuilMerging   = 0
        self.seuil_gating   = 0
        self.scan           = None
        self.tracks         = []
        self.infos          = infos
        
        #self.widget = GraphWidget2()
        self.display        = False
        
        
        
    def setTargets(self, targets):
        self.targets = targets
    def parameters(self,p_birth,p_survival, p_detection,min_weight,lambfa_fa,seuil_gating,seuil_merging,dist,polygons,model,J_Max):
        self.polygons       = polygons
        self.survival       = np.float64(p_survival)   
        self.detection      = np.float64(p_detection)   
        self.birth          = np.float64(p_birth) 
        self.model          = model
        self.minWeight      = min_weight
        self.dateTime       = QDateTime.currentDateTime()
        self.lambda_fa      = lambfa_fa
        self.dist           = dist
        self.seuilMerging   = chi2.ppf(seuil_merging, 4)
        self.seuil_gating   = chi2.ppf(seuil_gating, 2)
        self.scan           = None
        self.tracks         = []
        self.J_Max          = J_Max
    def receiveScan(self, scan):
        print('in GMPHD receiveScan')
        self.scan = scan
     
        self.run()
    @abstractmethod
    def run(self):
      
        pass
      
#        if self.mutex.tryLock()==False:
#            return 
       
 
    
    def birthTarget(self,    dist , geometry =  BIRTH_INIT.UNIFORM):
       
        #generationd des cibles naissantes
        #polygons: QtGui.QPolygonF()
        #dist entre les cibles naissantes
        #type de génération des cibles naissantes
        del self.gm_birth
        self.gm_birth = []
        for _pol in self.polygons:
             
             if geometry == BIRTH_INIT.CONTOUR:
                    for n in range(0,len(_pol)-1): 
                     pass
             elif geometry == BIRTH_INIT.UNIFORM:
                 rect = _pol.boundingRect()         
                 
                 for x in range(int(rect.topLeft().x()),int(rect.width()),dist):
                     for y in range(int(rect.topLeft().y()),int(rect.height()),dist):  
                         if _pol.containsPoint(QPointF(x,y), Qt.OddEvenFill):
                          
                             P = np.diag([dist*dist,100,dist*dist, 100])
                             self.gm_birth.append(Gauss([x,0,y,0],P,self.birth,-1))
 
        self.dateTime     = self.scan.dateTime
        
    def cycle(self):
        
        self.birthTarget(500,BIRTH_INIT.UNIFORM)
    
    def getTracks(self):
        return self.tracks
    
    def meanMeasurement(self):
        
        for   gm in self.gm:
            gm.computeMeanMesurement()
    def GIW(self,_date=QDateTime()):
        
        
        
        for gm in self.gm:
            if len(gm.detections) >6 and len(self.tracks)==0:
                self.tracks.append(Track(TRACKER_TYPE.RMKF)) 
                self.tracks[0].initialize(gm.detections,_date,StateType.XY )
            elif   len(gm.detections) >=3 and len(self.tracks)==1:
                print('in update')
                self.tracks[0].update(gm.detections)
        
        
    def update(self,plots):
        
         #Pour le moment
         H = np.zeros([2, 4])
         H[0, 0] = 1
         H[1, 2] = 1
         new_gm = []
         coeff  = 0

 
         #=========================
         #gaussiennes prédites 
         #=========================
         coeff  = 0
         for i,gm in enumerate(self.gm):
      
             for plotj in plots:
            
                 # and    
                 #if gm.distanceObs(plotj.z_XY,H)<self.dist and gm.isValidated(plotj.z_XY,plotj.R_XY,H,self.seuil_gating)==True:
                         
                        
                        innovation  = plotj.z_XY - np.dot(H, gm.m)

                        S           = plotj.R_XY + np.dot(H, np.dot(gm.P, H.T))

                        lambda_c    = innovation.T@np.linalg.inv(S)@innovation
                        
                        q           = np.sqrt(1/np.linalg.det(2*np.pi*S))* np.exp(-0.5 *lambda_c);
                        
                        K           = gm.P @ H.T  @np.linalg.inv(S)
                        
                        m           = gm.m + K@innovation
 
                        P           = (np.eye(gm.P.shape[0]) - K@H)@gm.P@(np.eye(gm.P.shape[0]) - K@H).T + K@plotj.R_XY@K.T
                        
                        w           = self.detection *q * gm.w 
                        
                        coeff      +=  w
                        newlgm      = Gauss(m,P,w,gm.label,gm.lenght,gm)
                        
                        newlgm.attach([plotj])
                        newlgm.line = np.concatenate((gm.line, np.matrix( m[[0,2]])),axis=1)      
                        newlgm.updateCovariance()
                        new_gm.append(newlgm)
                        #print(['-->',gm.label,' ',plotj.id ,'weigth: ',w, 'distance to plot:', gm.distanceObs(plotj.z_XY,H)])
         
                 
         for gm in new_gm:
            gm.w = gm.w/( self.lambda_fa + coeff) #
         
#         print('===========')
#         print([coeff,self.lambda_fa ])   
         #=========================
         #gaussiennes   naissantes
         #=========================
         if plots!=[]:
           
             for i,gm in enumerate(self.gm_birth):
          
                 for plotj in plots:
                
                     # and    
                     if  gm.isValidated(plotj.z_XY,plotj.R_XY,H,self.seuil_gating)==True:
                             
                       
                            innovation  = plotj.z_XY - np.dot(H, gm.m)
    
                            S           = plotj.R_XY + np.dot(H, np.dot(gm.P, H.T))
                    
                            lambda_c    = innovation.T@np.linalg.inv(S)@innovation
                            
                            q           = np.sqrt(1/np.linalg.det(2*np.pi*S))* np.exp(-0.5 *lambda_c);
                            
                            K           = gm.P @ H.T  @np.linalg.inv(S)
                            
                            m           = gm.m + K@innovation

                            P           =  (np.eye(gm.P.shape[0]) - K@H)@gm.P@(np.eye(gm.P.shape[0]) - K@H).T + K@plotj.R_XY@K.T
                            
                            w           =  gm.w 
               
                            newlgm      = Gauss(m,P,w,gm.label,gm.lenght,gm)
                     
                            newlgm.attach([plotj])
                            newlgm.line  = np.concatenate((gm.line, np.matrix( m[[0,2]])),axis = 1)      
                            newlgm.updateCovariance()
                            new_gm.append(newlgm)
                            
         #Concervation des gausiennes non détectée
 
         for i,gm in enumerate(self.gm):   
            gm.w =(1 - self.detection) * gm.w
            gm.line = np.concatenate((gm.line  ,np.matrix(gm.m[[0,2]])),axis=1)
         #concatenation
         
         self.gm += new_gm 
      
        #==============
        #Normalization
        #==============
#         coeff = 0
#         for  gm in self.gm:
#            coeff += gm.w
#         for  gm in self.gm:
#            gm.w = gm.w/coeff
#            
        
    
         self.gm= sorted(self.gm, key=take_weight,reverse = True)
         
    def destroyGausssian(self):

            del self.gm[0:]
    def gaussianInfos(self):
      print('in infos:')
      print('birth gaussian number : {}'.format(len(self.gm_birth)))
      print('gaussian number : {}'.format(len(self.gm)))
      
      print('label and weight vector:')
  
      L=[]
      for gm in self.gm:
           L.append((gm.label,gm.w))
 
      print(L)
    
        
    def prunning(self):
      #  print('in prunning:')
     #   print('gaussian number : {}'.format(len(self.gm)))
    #    print('weight vector:')
   #     L=[]
    #    for gm in self.gm:
     #       L.append(gm.w)
     #   print(L)
      #  print(['min weight:',  self.minWeight])
      
        coeff = 0
        for  gm in self.gm:
            coeff += gm.w
            
        loss_weight = 0

        for index,gm in enumerate(self.gm):
            if gm.w < self.minWeight: 
                del self.gm[index:]
                break
            
        if len(self.gm)>self.J_Max:
            del self.gm[self.J_Max+1:]
               
            
            
       # print('gaussian number after deleteing: {}'.format(len(self.gm)))
        #==============
        #Normalization
        #==============
#        loss_weight = 0
#        for  gm in self.gm:
#            loss_weight += gm.w
#            
#        if loss_weight !=0:    
#            for  gm in self.gm:
#                gm.w = gm.w*coeff/loss_weight
#                
 
        
    def merging(self):
        
        newGmList = []
       
        while self.gm !=[]:
            
            index_max   = -1
            cout_max    =  0
            listToDel   = []
            #selection de la gaussienne qui porte l epoids le plsus fort
            
            for index,gm in enumerate(self.gm):
                    if gm.w>=cout_max:
                       cout_max     = gm.w
                       index_max    = index
                       
            newGm   = Gauss(self.gm[index_max].m,self.gm[index_max].P,self.gm[index_max].w,self.gm[index_max].label,self.gm[index_max].lenght,self.gm[index_max])
            newGm.line = self.gm[index_max].line[:,:-1]
            newGm.m = self.gm[index_max].w * self.gm[index_max].m
            newGm.P = self.gm[index_max].w * self.gm[index_max].P
            newGm.attach(self.gm[index_max].detections)
            listToDel.append(index_max)
            
            
            for index,gm in enumerate(self.gm):
                
                if index!=index_max and self.gm[index_max].distStatGaussian(gm)<=self.seuilMerging and   self.gm[index_max].distanceState(gm.m)<self.dist:
                    newGm.m += gm.w * gm.m
                    newGm.P += gm.w * gm.P
                    newGm.w += gm.w 
                    newGm.attach(gm.detections)
                    listToDel.append(index)
                    
            #normalisation
            
            newGm.m = newGm.m/newGm.w
            
            
            
            for indexes  in listToDel:                  
                 newGm.P +=  self.gm[indexes].w *(newGm.m - self.gm[indexes].m)@(newGm.m - self.gm[indexes].m).T
                    
            newGm.P = newGm.P/newGm.w
            
#            if newGm.w>1:
#                newGm.w = 1
                
            newGmList.append(newGm)
         
             
            newGm.line = np.concatenate((newGm.line ,np.matrix(newGm.m[[0,2]])),axis=1)
            newGm.updateCovariance()
            
            self.gm = [i for j, i in enumerate(self.gm) if j not in listToDel]  
            
            #on retire de  la liste
#           
#            for u in listToDel:
#               # for index,gm in enumerate(self.gm):
#                for index in range(len(self.gm) - 1, -1, -1):
#                     if self.gm[index].id == u.id:
#                         del self.gm[index]
#                         
#            self.gm= list(self.gm, key=take_weight,reverse = True)
#            
#            filter(lambda num: num != 54 and num !=55,
#                         self.gm)
        self.gm = newGmList
        
        
    #def addScene(self,scene):
    #    self.scene = scene
    def unDisplaySituation(self):
        self.widget.close()
    def displaySituation(self):
        #display initial areas 
        if self.display == False:
            return
        
        
        self.widget.displayInitialareas(self.polygons)
        #self.widget.show() 
#        for _pol in self.polygons:
#            
#            self.scene.addPolygon(_pol)
#            
#            
#        #display gaussian
#        
#        pen = QPen(QColor(Qt.black))
#        brush = QBrush(QColor("#FFCCDD"))
#        for mg in self.gm:
#            self.scene.addEllipse(mg.m[0],mg.m[2],5,5,pen,brush)
            
    def prediction(self,_dateTime):
        deltaTime = self.dateTime.secsTo(_dateTime)  
        for gm in self.gm:
            
            gm.predict(deltaTime,self.model)
            gm.w                    = self.survival*  gm.w
            gm.lenght              += 1
            gm.detections           = []
#        # Prediction for existing targets
#        if len(self.gm) == 0:
#            return []
#  
##            gmm_mask = utils.inside_polygon(means, sss_path)
##            gmm_fov = list(itertools.compress(self.gm, gmm_mask))
#            predicted = []
#            for idx, comp in enumerate(self.gm):
##                if gmm_mask[idx]:
#                 comp.predict(F,Q) 
#                else:
#                    predicted.append(self.gm[idx])
        #return predicted
def corr2hex(n):
    ''' Maps a number in [0, 1] to a hex string '''
    if n >= 1.0: return '#ff0000'
    else: return '#' + hex(int(n * 16**6))[2:].zfill(6)
def rgb_to_hex(rgb_color):
   #rgb_color = re.search('\(.*\)', rgb_color).group(0).replace(' ', '').lstrip('(').rstrip(')')
    [r, g, b] = [int(x) for x in rgb_color]#.split(',')]
    # check if in range 0~255
    assert 0 <= r <= 255
    assert 0 <= g <= 255
    assert 0 <= b <= 255
 
    r = hex(r).lstrip('0x')
    g = hex(g).lstrip('0x')
    b = hex(b).lstrip('0x')
    # re-write '7' to '07'
    r = (2 - len(r)) * '0' + r
    g = (2 - len(g)) * '0' + g
    b = (2 - len(b)) * '0' + b
 
    hex_color = '#' + r + g + b
    return hex_color    

class GraphWidget2( ):
    def __init__(self):
        self.mainWidget               =   QWidget()
        self.timerId = 0

        self.figure     = Figure() 
        self.axes       = self.figure.add_subplot(111)
        self.axes.grid(True)
        self.axes.axis('equal')
        self.canvas     = FigureCanvas(self.figure)
        self.canvas.setFocusPolicy(Qt.StrongFocus)
        self.canvas.setFocus()
        self.navi_toolbar = NavigationToolbar(self.canvas, self.mainWidget ) #createa navigation toolbar for our plot canvas

        '''
        cdict = {
                'red'  :  ( (0.0, 0.25, .25), (0.02, .59, .59), (1., 1., 1.)),
                'green':  ( (0.0, 0.0, 0.0), (0.02, .45, .45), (1., .97, .97)),
                'blue' :  ( (0.0, 1.0, 1.0), (0.02, .75, .75), (1., 0.45, 0.45))
          }

        cm = mpl.colors.LinearSegmentedColormap('my_colormap', cdict, 1024)
        '''
        cmp   =  plt.get_cmap('jet')
        cNorm  = mpl.colors.Normalize(vmin=0.0, vmax=1.0)
        ax, _ =  mpl.colorbar.make_axes(self.figure.gca(), shrink=0.5)
        cbar  =  mpl.colorbar.ColorbarBase(ax, cmap=cmp, norm= cNorm)
        cbar.set_clim(-2.0, 2.0)
        self.scalarMap = mpl.cm.ScalarMappable(norm=cNorm, cmap=cmp)
        self.canvas.draw()
        self.canvas.show()
        Vlayout = QVBoxLayout()
        Vlayout.addWidget(self.navi_toolbar)     
        Vlayout.addWidget(self.canvas, Qt.AlignHCenter | Qt.AlignVCenter) 
        self.mainWidget.setLayout(Vlayout)
        #ellipses
        
        self.ellipses  = []
        self.ellipsesP = []
        self.tracks    = []
        self.areas     = []
        self.texts     = []
        self.mainWidget.show()
        #tools
        self.sensorAreaDisplay = False
        self.locationIsVisible = True
    def displayInitialareas(self,polygons):
        if self.areas!=[] or polygons == None:
            return
        self.sensorAreaDisplay = True
        for _pol in polygons:
             MyPoly = []
             for pts in _pol:
                MyPoly.append([pts.x() , pts.y()])
           
             polygon = Path(MyPoly)
             my_array = np.array(MyPoly)
       
             xmin = np.amin(my_array[:,0])
             xmax = np.amax(my_array[:,0])
             ymin = np.amin(my_array[:,1])
             ymax = np.amax(my_array[:,1])
         
             patch = patches.PathPatch(polygon,facecolor=(0,0.25,0.01),alpha =0.3,visible =self.locationIsVisible,edgecolor=(0.0, 0.0, 0.0),linestyle='--') 
         
             
             self.axes.add_patch(patch)
             
             
             self.axes.set_xlim([xmin,xmax])
             self.axes.set_ylim([ymin,ymax])
        self.canvas.blit(self.axes.bbox)
        self.canvas.update()
        self.canvas.draw_idle()
        #◘self.canvas.flush_events()
       #self.canvas.update()
    def close(self):
        self.mainWidget.close()
    def displayGaussians(self,gauss):
        if self.ellipses != []:
             for _e in self.ellipses:
                 _e.remove()
             self.ellipses = []
             
        if self.ellipsesP != []:
             for _e in self.ellipsesP:
                 _e.remove()
             self.ellipsesP = []
        if self.texts != []:
             for _text in self.texts:
                 _text.remove()
             self.texts = []
        if self.tracks  != []:   
            for _track in self.tracks:
                if _track in self.axes.lines:
                 self.axes.lines.remove(_track)
#            self.tracks = []
#                         if self.quiverObj != None:
#                self.quiverObj.remove()
#                self.quiverObj = None
        #remove gaussian
#        for item in self.ellipses:
#            self.scene().removeItem(item)
#        for item in self.texts:
#            self.scene().removeItem(item)
#        self.ellipses.clear()
#        self.texts.clear()
        #add gaussien
        for mg in gauss:
          
            weightColor = corr2hex(mg.w)
          #  print(weightColor)
          #  weightColor = rgb_to_hex(weightColor)
     
            ellipse = patches.Ellipse((mg.m[0],mg.m[2]), 5, 5, 0.0)
            ellipse.set_facecolor(weightColor)
            self.axes.add_patch(ellipse)
            
            ellipseP = patches.Ellipse((mg.m[0],mg.m[2]), 2*mg.sigma_x, 2*mg.sigma_y, angle=mg.angle*180/np.pi)
            ellipseP.set_alpha(0.3)
            ellipseP.set_facecolor(weightColor)
            self.axes.add_patch(ellipseP)
              
            #text = self.axes.text(mg.m[0],mg.m[2],str(mg.label), color = weightColor)
            text = self.axes.text(mg.m[0],mg.m[2],str(mg.label)+"\n"+"size : "+str(mg.lenght)+"\n"+'mean meas. : {0:.2}'.format(mg.meanDetections), color = weightColor)
             
            X = []
            Y = []
            for u in range(1,mg.line.shape[1]):
                X.append(mg.line[0,u])
                Y.append(mg.line[1,u])
            #if len(mg.line)>2:
            #print('-------------------->')
            #print(X)
                ##print(len(mg.line))
            ##print(mg.line)
                #u =  np.matrix(mg.line)
            #print(mg.line[0:1,:])
            #print(mg.line[1:2,:])
                #print(u)
                #print(u[:,0:1])
                #print( u[:,1:2])
                #print(mg.line[:,0:1])
            if len(X)>2:
                _line = self.axes.plot(X, Y,'-', color=weightColor, linewidth=1, antialiased=False)
                self.tracks.append(_line)
            #self.axes.plot([0,80,500], [0,30,500],'+-', color=weightColor, linewidth=4)     
            self.ellipses.append(ellipse)
            self.ellipsesP.append(ellipseP)
            self.texts.append(text)
             
        self.canvas.blit(self.axes.bbox)
        self.canvas.draw()
        self.canvas.flush_events()
 
      
#    def wheelEvent(self, event):
#            self.scaleView(math.pow(2.0, -event.angleDelta().y() / 240.0))
#
#    def scaleView(self, scaleFactor):
#            self.scale(scaleFactor, scaleFactor)    
#class GraphWidget(QGraphicsView):
#    def __init__(self):
#        super(GraphWidget, self).__init__()
#
#        self.timerId = 0
#
#        scene = QGraphicsScene(self)
#        scene.setItemIndexMethod(QGraphicsScene.NoIndex)
#        self.setScene(scene)
#        self.setCacheMode(QGraphicsView.CacheBackground)
#        self.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)
#        self.setRenderHint(QPainter.Antialiasing)
#        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
#        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
#    
#        #ellipses
#        
#        self.ellipses  = []
#        self.ellipsesP = []
#        self.areas     = []
#        self.texts     = []
#    def displayInitialareas(self,polygons):
#        if self.areas!=[]:
#            return
#        for _pol in polygons:
#             poly = QGraphicsPolygonItem()
#             MyPoly = QPolygonF()
#             for pts in _pol:
#                MyPoly.append(QPointF(pts.x() ,-pts.y()))
#             poly.setPolygon(MyPoly)
#             poly.setBrush(QColor(0,125,12,52))
#             self.scene().addItem(poly)
#             
#             self.areas.append(poly)
#    def displayGaussians(self,gauss):
#        
#        #remove gaussian
#        for item in self.ellipses:
#            self.scene().removeItem(item)
#        for item in self.texts:
#            self.scene().removeItem(item)
#        self.ellipses.clear()
#        self.texts.clear()
#        #add gaussien
#        for mg in gauss:
#            
#            pen = QPen(QColor(Qt.black))
#            brush = QBrush(QColor("#FFCCDD"))
#            ellipse = QGraphicsEllipseItem()    
#            size = 20
#            ellipse.setRect(mg.m[0] -size/2,-mg.m[2]-size/2, size,size)
#            ellipse.setPen(pen)
#            ellipse.setBrush(brush)
#            
#            color = QColor()
#            color.getCo
#            
##            ellipseP = QGraphicsEllipseItem()
##            ellipseP.setRect(mg.m[0] -size/2,-mg.m[2]-size/2, size,size)
##            brush = QBrush( QColor.gnum).red(), cMap.getColor(num).green(),
##              cMap.getColor(num).blue(), cMap.getColor(num).alpha());)
##            ellipseP.setPen(pen)
##            ellipseP.setBrush(brush)
#            
#            text                = QGraphicsTextItem()
#            text.setPlainText(str(mg.label)+"\n"+"size : "+str(mg.lenght)+"\n"+"mean meas. : "+str(mg.meanDetections))  
#            text.setPos(mg.m[0],-mg.m[2])
#
#            self.scene().addItem(ellipse)
#            self.scene().addItem(text)
#            self.ellipses.append(ellipse)
#            self.ellipsesP.append(ellipseP)
#            self.texts.append(text)
#        
#        self.scene().update()
#    
#    def wheelEvent(self, event):
#            self.scaleView(math.pow(2.0, -event.angleDelta().y() / 240.0))
#
#    def scaleView(self, scaleFactor):
#            self.scale(scaleFactor, scaleFactor)     
#            
            
            
if __name__ == '__main__':
    polygons = []
   
    P =  QPolygonF()
 
    P.append(QPointF(100,250))
    P.append(QPointF(-50,550))
    P.append(QPointF(-600,950))
    P.append(QPointF(-400,1250))
    P.append(QPointF(500,100))
    
    polygons.append(P)
    
    GMPHD = Gaussian(  0.00001,0.001, 0.9, [], [], [], [], polygons)
    GMPHD.cycle()
    import sys
    app = QApplication(sys.argv)
    widget = GraphWidget()
    GMPHD.addScene(widget.scene())
    
    GMPHD.display()
    widget.show()
    sys.exit(app.exec_())