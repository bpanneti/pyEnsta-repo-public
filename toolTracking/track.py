# -*- coding: utf-8 -*-
"""
Created on Fri Mar 30 17:00:11 2018

@author: bpanneti

"""
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtOpenGL import *
from PyQt5.QtWidgets import *

from toolTracking.tree import Tree
from toolTracking.utils import trackerType, StateType,TrackState
from toolTracking.state import State 

from target import TARGET_TYPE

from itertools import count

#from toolTracking.randomMatrice import group
import numpy as np
from numpy import linalg as LA
from scan import Plot, Scan
from point import Position, Velocity
from orientation import Orientation
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from sensor import PLOTType
import math

from treelib import Tree as _trTree
from treelib import Node as _trNode


def defined(_var):
    if _var is None:
        return False
    return True

def imscatter(x, y, imagePath, ax, zoom=0.1):
    im = OffsetImage(plt.imread(imagePath), zoom=zoom)

    ab = AnnotationBbox(im, (x, y), xycoords='data', frameon=False)
    return ax.add_artist(ab)

def LLROnBranch(cstate,SD):
    if cstate==None or SD==0:
        return 0
    
    a = LLROnBranch(cstate.parent,SD-1);

    return a + math.log(cstate.data.likelihood)


def cleanBranch(cState):
    
    if cState.parent!=None and cState.markToDelete == True:
        cState.parent.childs.remove(cState)
        if     cState.parent.childs==[]:
            cState.parent.markToDelete = True
            cleanBranch(cState.parent)
            
        del cState
        

        
    
        
        
 
def cleanTree(cState):
 

    if cState!=None:
    
        for _child in cState.childs :
            cleanTree(_child)
        #if root.markToDelete==True:
        #print('cleanTree del {}'.format(cState.markToDelete))
        if cState.markToDelete==True:
            #print('--> clean '+cState.id +' del {}'.format(cState.markToDelete))
            if cState.parent!=None:
                cState.parent.childs.remove(cState)
                if cState.parent.childs == []:
                    cState.parent.markToDelete = True
            #print('--> clean '+str(cState.id) +' del '+str(int(cState.markToDelete)))
   
            del cState
 
    
def markToDeleteChilds(cState,_mark = True):
    
    cState.markToDelete = _mark
    for _child in cState.childs:
        markToDeleteChilds(_child,_mark)
        
    return
     
def selectBranch(cState  ,_plots ):
    
    # if len(_plots)==0:
    #     #On a tout trouvé
    #     print("trouvé" ,cState.id)

    #     return cState
    flag = False
    if cState.data.plot!=None and cState.data.plot.id==_plots[-1] :
        #print("plots :",_plots[-1]," cstate id :",cState.id)
        flag = True
    
    if cState.data.plot==None and _plots[-1]== -1:
       # print("plots :",_plots[-1]," cstate id :",cState.id)
        flag = True
        
        
    if flag==True and  len(_plots)>1:
        return selectBranch(cState.parent,_plots[0:-1])
    elif flag==True and  len(_plots)==1:
        return cState
    return None
    
def getSDTuple(cState,SD,vectorPos):
        
        if cState==None or SD==0:
            return vectorPos
        if cState.data.plot!=None:
            vectorPos[0,SD-1] = cState.data.plot.id
        else:
            vectorPos[0,SD-1] = -1
 
 
        
        return  getSDTuple(cState.parent,SD-1,vectorPos)
def findCandidate(cState,vectorPos) :
        # if cState!=None:
            
        #     print('--->',cState.id)
        # else:
        #         print('---> nothong')
        # print(vectorPos)
        if len(vectorPos)==0:
            return True
         
 
 
        if cState!=None and cState.data.plot!=None and cState.data.plot.id == vectorPos[-1]:
           
            return      findCandidate(cState.parent,vectorPos[0:-1])  
        
        elif cState!=None and cState.data.plot==None and vectorPos[-1] == -1:
       
            return      findCandidate(cState.parent,vectorPos[0:-1])
        elif vectorPos[-1] == -1 and cState==None:
            #cas des pistes initialisées
            return True            
        
        return False
class Track(object):
    __cnt = count(0)
    def __init__(self,_parameters=None,_plot=None, _time=QDateTime(), _state=None):
        self.id = next(self.__cnt)
        self.groundTruth = -1   # id de la cible pistée
        self.tree        = None # accès à l'arbre
        self.id_node     = -1   # id nu noeud du tracker
        self.parameters  = _parameters
        self.trackState  = TrackState.Tentative
        #===================================
        # initialisation si possible
        #===================================
        
        #self.initialize(_plot,_time,_state)
        
        #===================================
        # objets graphiques
        #===================================
        self.addtionnalInfo = []
        self.locObj         = []
        self.textObj        = []
        self.quiverObj      = []
        self.iconeObj       = []
        self.shapeObj       = []
        self.ellipsesObj    = []
        self.color = QColor(Qt.darkRed)
        self.trajectoryIsVisible = True
        self.textIsVisible = True
        self.axes = None
        self.canvas = None

    def __del__(self):
        #print("deleted track object")
        self.undisplay()
        del self.tree
        
    def trackClassification(self,time):
        
        currentStates = []
        flag = False
        self.tree.getChilds(currentStates)
        for cState in currentStates:
            if self.tree.data.time.msecsTo(cState.data.time)/1000 > time :
                self.trackState = TrackState.Confirmed
                return
        currentStates.clear()   
    def initialize(self, _plot=None, _time=QDateTime(), _state=None):
        
        if _plot == None and _state!=None :
            print('ici pas possible')
            self.tree  = Tree(idTrack = self.id,time=_time , state=_state,parameters=  self.parameters)
      
        elif _plot != None and _state==None :
            
            _state      = State(idTrack = self.id,time= _plot.dateTime, plot = _plot,parameters=  self.parameters)
            self.tree  = Tree(data=_state)
            self.groundTruth = _plot.idTarget
            
    def computeLLR(self,side = 0):
        if side == 0:
            return
        

        currentStates = []
        self.tree.getChilds(currentStates)
        
        for cState in currentStates:
            cState.data.LLR = LLROnBranch(cState,side)
        currentStates.clear()
        return
    def correction(self, estate=State(), plot=Plot()):
        if plot.type == PLOTType.POLAR:
            #_previousState = currentState.parent.data
            #estate = currentState
            duree = - plot.dateTime.msecsTo(estate.time)/1000.0
 
            vel_x = (plot.z_XY[0] - estate.xEst[0]) / duree
            vel_y = (plot.z_XY[1] - estate.xEst[2]) / duree
       
            estate.setVelocity([vel_x, vel_y])
            estate.prediction(plot.dateTime)
    
    def maintainHypothesis(self,_plots = []):
        
        if self.tree.depth() <=len(_plots):
            markToDeleteChilds(self.tree,False)
            return
        
        currentStates = []
        self.tree.getChilds(currentStates)
        
        for cState in currentStates:
            
            _ancetre = selectBranch(cState,_plots)
            
            if _ancetre !=None  :
                markToDeleteChilds(_ancetre,False)            
    def getSDMeasurements(self,SD,matrixPoss):
         
         
         currentStates = []
         flag = False
         self.tree.getChilds(currentStates)
         for cState in currentStates:
             vectorPos = np.array(-1*np.ones((1,SD)))
  
             vectorPos = getSDTuple(cState,SD,vectorPos)
  
             if vectorPos[0,:].tolist() not in matrixPoss.tolist():
                matrixPoss = np.vstack((matrixPoss,vectorPos))
         currentStates.clear()
         return   matrixPoss      
         
         

    def findHypothesis(self,vectorPos):
         
         currentStates = []
  
         self.tree.getChilds(currentStates)
         for cState in currentStates:
             
             if findCandidate(cState,vectorPos)==True:
                 return cState
         
         return None
                    
 
    def trackValidity(self, time=QDateTime()):
        currentStates = []
        flag = False
        self.tree.getChilds(currentStates)
        for cState in currentStates:
             
            if cState.data.validity(time):
                flag = True

        currentStates.clear()
        return flag
 
    def prediction(self, time=QDateTime()):
        currentStates = []

        self.tree.getChilds(currentStates)
        for cState in currentStates:
            #estate = State.copyState(cState.data)
            #cState.addChild(Tree(data=estate))
            #estate.prediction(time, True)
            cState.data.prediction(time, True)
        currentStates.clear()
    def merging(self,_track):
        
        #on teste si les états d'une piste sont mergable avec une autre
        pass
    def cleanTrack(self):
        
        
        # cState = self.tree
        # cleanTree(cState)
        currentStates = []
        flag = False
        self.tree.getChilds(currentStates)
        for cState in currentStates:
            cleanBranch(cState)
           
        currentStates.clear()          
        
    def taillePiste(self):
        return self.tree.depth()

    def getState(self, idState=-1):

        if self.tree==None:
           return None    
        flag, val = self.tree.getData(idState)
        if flag:
            return val
        return None

    def update(self, plot=[], sensorPosition=Position(), sensorOrientation=Orientation()):
        # self.tree.displayTree()
        currentStates = []
        
        if len(plot) == 1:
            


            
            if self.taillePiste() == 1 and plot[0].type == PLOTType.POLAR:
                
                #print(['-> Initialisation ------> track id',self.tree.data.idTrack])
                estate = State.copyState(self.tree.data)
                self.correction(estate,plot[0])
                
                self.tree.addChild(Tree(data=estate))

            elif self.taillePiste() >= 2 and (plot[0].type == PLOTType.POLAR or plot[0].type == PLOTType.ANGULAR):
                self.tree.getChilds(currentStates)
     
                #print(self.tree,self.tree.childs)
                for cState in currentStates:
                    #print(['usual cycle ------> estate idTrack',cState.data.idTrack])
               
                    estate = State.copyState(cState.data)
                    cState.addChild(Tree(data=estate))
               
                    estate.prediction(plot[0].dateTime)
                    estate.estimation(plot, sensorPosition, sensorOrientation)
                    estate.classification(plot[0]) #ENSTA Todo 

                    #cState.addChild(estate)
                    return
                currentStates.clear()
   


    def validate(self,_plot,threshold = 14,sensorPosition=None,sensorOrientation=None):
        currentStates = []
       
        self.tree.getChilds(currentStates)

        for cState in currentStates:
                [flag, structG] = cState.data.gating(_plot, threshold,sensorPosition,sensorOrientation)
                if flag:
                    return True
        return False
    def gating(self,_plot,threshold = 14,sensorPosition=None,sensorOrientation=None):
        currentStates = []
       
        self.tree.getChilds(currentStates)

        for cState in currentStates:
                [flag, structG] = cState.data.gating(_plot, threshold,sensorPosition,sensorOrientation)
                if flag:

                    return True,structG
        return False, None
    def follow(self, _childs=[],tree = None):
        
        for _child in _childs:
            
            if _child.data.plot==None:
                _txt = "node {}  markToDelete: {} plot : {} LLR :{} likelihood {}".format(_child.data.id,_child.markToDelete,-1,_child.data.LLR,_child.data.likelihood)
            else:
                _txt = "node {}  markToDelete: {} plot : {} LLR :{} likelihood {}".format(_child.data.id,_child.markToDelete,_child.data.plot.id,_child.data.LLR,_child.data.likelihood)

 
            tree.create_node(_txt,_child.data.id,parent = _child.parent.data.id)
            self.follow(_child.childs,tree)
    def showTree(self,side):


        tree = _trTree()
        currentStates = []
        self.tree.getChilds(currentStates)
        
        cState = currentStates[0]
        while cState.parent != None and side>=0:             
            cState = cState.parent
            side = side-1
            
        
        if cState.data.plot==None:
            _txt = "Track : {}, node {} markToDelete: {}  plot : {} LLR :{} likelihood:{}".format(self.id,cState.data.id,cState.markToDelete,-1,cState.data.LLR,cState.data.likelihood)
        else:
            _txt = "Track : {}, node {} markToDelete: {}  plot : {} LLR :{} likelihood:{}".format(self.id,cState.data.id,cState.markToDelete,cState.data.plot.id,cState.data.LLR,cState.data.likelihood)
 
        tree.create_node(_txt,cState.data.id)
        self.follow(cState.childs,tree)
       
        currentStates.clear()   
        tree.show()
        
        
    def cutChilds(self):
        
        currentStates = []
        self.tree.getChilds(currentStates)
        winner   = None
        lastDate = None
        for _state in currentStates:
            if winner==None or _state.data.time>=winner.data.time:
                lastDate = _state.data.time
                winner   = _state
        if lastDate!=None:
     
            self.removeChilds(self.tree,lastDate)
    def removeChilds(self,_currentNode,lastDate):
        
        if _currentNode.childs==[] and _currentNode.data.time < lastDate :
            return True
            
        for _child in _currentNode.childs:
             if self.removeChilds(_child,lastDate):
      
                 _currentNode.removeChild(_child)
        
        return False
   
    def gatings(self, plots=[],threshold = 14):
        currentStates = []
        gatingPlots = []

        self.tree.getChilds(currentStates)
        for plot in plots:
            for cState in currentStates:
                [flag, structG] = cState.data.gating(plot, threshold)

                if flag:
                    gatingPlots.append(structG)
        return gatingPlots

    def getCurrentState(self):
        # retourne le state le plsu probable
        currentStates = []
        self.tree.getChilds(currentStates)
        cost = -1
        winner = None
        for cState in currentStates:
            if cState.depth_d > cost:
                cost = cState.depth_d
                winner = cState
        return winner

    def classesAtTime(self, currentTime=QDateTime()):

        classes = []
        noeuds = [self.tree]
        winners = []

        while noeuds != []:
            futurNoeuds = []

            for state in noeuds:
                parent = state.parent

#               if parent:
#                    print(parent.data.time)
#                    print(state.data.time)
#                    print(currentTime)
                if parent and parent.data.time <= currentTime and state.data.time > currentTime and parent not in winners:
                    # stop_branche

                    winners.append(parent)

                elif state.childs != []:
                    futurNoeuds += state.childs
            noeuds = futurNoeuds

        for win in winners:
            classes.append(win.data.classe)
        if classes != []:
            return True, classes
        return False, classes
    
    
      
        
        

    def positionAtTime(self, currentTime=QDateTime()):

        # recherche des états >= currentTime
        positions       = []
        velocities      = []
        stdPositions    = []
        stdVelocities   = []
        nbplots         = []
        noeuds          = [self.tree]
        winners         = []

        while noeuds != []:
            futurNoeuds = []

            for state in noeuds:
                parent = state.parent

              #  if parent:
#                    print(parent.data.time)
#                    print(state.data.time)
#                    print(currentTime)
                if parent and parent.data.time <= currentTime and state.data.time > currentTime and parent not in winners:
                    # stop_branche

                    winners.append(state)

                if state.childs != []:
                    futurNoeuds += state.childs
            noeuds = futurNoeuds

        for win in winners:
  
            pere = win.parent
            A = np.array([pere.data.location.x_UTM, pere.data.location.y_UTM])
            B = np.array([win.data.location.x_UTM, win.data.location.y_UTM])
            diffTime = pere.data.time.msecsTo(currentTime) / 1000
            delay = pere.data.time.msecsTo(win.data.time)/1000 
            Vel =  B-A
            Vel = Vel /delay
            Loc = A + diffTime * Vel
          
            M = Position()
            V = Velocity()
            V.setXYZ(Vel[0], Vel[1], 0.0, 'UTM')

            stdM = np.sqrt(win.data.PEst[0,0]  + win.data.PEst[2,2]  )
            stdV = np.sqrt(win.data.PEst[1,1]  + win.data.PEst[3,3]  )
  
            M.setXYZ(Loc[0], Loc[1], win.data.location.altitude)
            positions.append(M)
            velocities.append(V)
            stdPositions.append(stdM)
            stdVelocities.append(stdV)
            nbplots.append(len(win.data.idPlots))
        if positions != []:
            return True, positions, velocities, stdPositions,stdVelocities, nbplots
        return False, [], [],[],[],[]

    def undisplay(self):
        if self.axes != None:
            axes = self.axes
            if self.locObj!=[]:
                for line in self.locObj:# ax.lines:
                    _l = line.pop(0)
                    _l.remove()
 
                    # if i in axes.lines:
                self.locObj=[]     
            if self.ellipsesObj!=[]:
                for _e in self.ellipsesObj:
                    _e.remove()
                self.ellipsesObj = []
            if self.shapeObj != []:
                self.shapeObj.remove()
                self.shapeObj = []
            if self.textObj != []:
                for txt in self.textObj:
                    txt.remove()
                self.textObj = []

            if self.quiverObj != []:
                for _quiver in self.quiverObj:
                    _quiver.remove()
                self.quiverObj = []

            if self.iconeObj != []:
                for _icone in self.iconeObj:
                    _icone.remove()
                self.iconeObj = []
 
    
    def getTrajectory(self):
        
        childs = []
        self.tree.getChilds(childs)

        c = childs[0]
 
        coords = []
        pos = c.data.location
        coords.append((pos.longitude,pos.latitude))
 
        current = c.parent 
        while current != None:
                pos = current.data.location
                coords.append((pos.longitude,pos.latitude,pos.altitude))

                current = current.parent 
     
        return coords

    def getStates(self):
        childs = []
        self.tree.getChilds(childs)
        coords = []
        c = childs[0]
        for p in childs:
            if p.data.id>c.data.id:
                c = p
      
        coords.append(c.data)
        current = c.parent 
        while current != None:
                state = current.data
                coords.append(state)

                current = current.parent 
     
        return coords
  
    def displayTrack(self, axes, canvas,displayTack = True, displayCovariance = True,displayIcone = True):
     
        self.axes = axes
        self.canvas = canvas

        self.undisplay()

        childs = []
        self.tree.getChilds(childs)
   
        for c in childs:

            latitude = []
            longitude = []

            pos = c.data.location
            #latitude.append(pos.latitude)
            #longitude.append(pos.longitude)
            #current = c.parent
            # ============================
            # display heading
            # ============================
            vit = Position()
            velocity = 0

            if c.data.velocity == 0:
                velocity = 0.1
            else:
                velocity = c.data.velocity

            ux = velocity * np.cos((90 - c.data.heading)*np.pi/180)+pos.x_ENU
            uy = velocity * np.sin((90 - c.data.heading)*np.pi/180)+pos.y_ENU

            vit.setXYZ(ux, uy, 0.0, 'ENU')

            dx = vit.longitude - pos.longitude
            dy = vit.latitude - pos.latitude

            # =============================
            # display text
            # =============================
            self.textObj.append(axes.text(pos.longitude, pos.latitude, 'track : ' + str(self.id),  color=self.color.name(), visible=self.textIsVisible))
            self.quiverObj.append(axes.quiver(pos.longitude, pos.latitude, dx, dy, color=self.color.name(), alpha=0.8))
           
            # =============================
            # display image
            # =============================
            if displayIcone:
   
 
               
                icone = c.data.classe.value.icone
                    
     
                self.iconeObj.append(imscatter(pos.longitude, pos.latitude, icone, axes))
            # =============================
            # display covariances
            # =============================

            e1 = patches.Ellipse((pos.longitude, pos.latitude), c.data.sigmaX, c.data.sigmaY, angle=c.data.angle*180/np.pi)

            e1.set_alpha(0.3)
            e1.set_facecolor(self.color.name())
            if displayCovariance:
         
                axes.add_patch(e1)
                self.ellipsesObj.append(e1)
            
            # =============================
            # display shape
            # =============================
            '''
            if defined(c.X):
                # attention en m alors qu'on affiche en WGS84
#                print(c.data.X)
#                print(c.data.x)
#                print(c.data.P)
                lmbda, u = np.linalg.eig(c.X)
#                idx = lmbda.argsort()[::-1]   
#                lmbda = lmbda[idx]
#                u = u[:,idx]
#        
                #print(lmbda)
                Point3 = Position()
                Point3.setXYZ(pos.x_ENU + np.sqrt(lmbda[0]),  pos.y_ENU + np.sqrt(lmbda[1]), 0.0,'ENU')

                sigmaX = abs(pos.longitude - Point3.longitude)
                sigmaY = abs(pos.latitude - Point3.latitude)
                if sigmaX > sigmaY:
                    _angle = math.atan2(u[1, 0], u[0, 0])
                else:
                    _angle = math.atan2(u[1, 1], u[0, 1])
                e2 = patches.Ellipse((pos.longitude, pos.latitude), sigmaX, sigmaY, angle=_angle*180/np.pi)

                e2.set_alpha(0.3)
                col = QColor(Qt.darkGreen)
                e2.set_facecolor(col.name())
                e2.set_edgecolor(col.name())
                axes.add_patch(e2)
                self.shapeObj = e2
            '''
            # =============================
            # display track
            # =============================
            current = c
            while current != None:
            
                pos = current.data.location
                latitude.append(pos.latitude)
                longitude.append(pos.longitude)              
                #axes.text(pos.longitude, pos.latitude,  current.data.time.toString('hh:mm:ss.z'),  color=self.color.name() )
                current = current.parent
            # ,visible=self.trajectoryIsVisible)
            if  displayTack:
                self.locObj.append(axes.plot(longitude, latitude, '+-', color=self.color.name(), linewidth=2))

            #canvas.update()
            #canvas.flush_events()
            #canvas.draw()
        childs.clear()
