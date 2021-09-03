# -*- coding: utf-8 -*-
"""
Created on Fri Mar 30 17:00:11 2018

@author: bpanneti

"""
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtOpenGL import *
from PyQt5.QtWidgets import *

from tool_tracking.state import State
#from tool_tracking.state_imm import State as _stateIMM
from tool_tracking.motionModel import StateType as _dim
from tool_tracking.tree import Tree as _tree
from tool_tracking.estimator import TRACKER_TYPE

from itertools import count

from tool_tracking.randomMatrice import group
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

def defined(_var):
    if _var is None:
        return False
    return True

def imscatter(x, y, imagePath, ax, zoom=0.1):
    im = OffsetImage(plt.imread(imagePath), zoom=zoom)

    ab = AnnotationBbox(im, (x, y), xycoords='data', frameon=False)
    return ax.add_artist(ab)

class Track:
    __cnt = count(0)
    def __init__(self, typeTracker=TRACKER_TYPE.UNKNOWN):
        self.id = next(self.__cnt)
        self.groundTruth = -1  # ☺id de la cible pistée
        self.tree = _tree()
        self.trackerType = typeTracker
        self.id_node     = -1
        # objets graphiques

        self.locObj = []
        self.textObj = None
        self.quiverObj = None
        self.iconeObj = None
        self.shapeObj = None
        self.ellipsesObj = []
        self.color = QColor(Qt.darkRed)
        self.trajectoryIsVisible = True
        self.textIsVisible = True
        self.axes = None
        self.canvas = None

    def __delete__(self, instance):
        print("deleted track object")
        self.undisplay()
        del self.tree

    def initialize(self, plots=[], time=QDateTime(), cov=0, state=0, ftype=0, Mu=[], M=[], filters=[], infos=[]):
        if len(plots) == 0:
            estate = State(time=time, cov=cov, state=state,extent=extent, ftype=ftype, dim=_dim.XY, estimatorInfos=infos)
            self.tree.data = estate
        elif len(plots) == 1 :
            plot = plots[0]
            estate = State(plot.dateTime, plot, _dim.XY,cov, state, 0, ftype, filters, self.trackerType, estimatorInfos=infos)
            self.tree.data = estate
            self.groundTruth = plot.idTarget
 
       
        elif len(plots) > 1:
            _group = group(plots[0].dateTime, plots, _dim.XY)
            self.tree.data = _group
            gT = []
            for u in plots:
                gT.append(u.idTarget)
            self.groundTruth = gT

    def addState(self, estate=State(), _parent=_tree()):
        _newTree = _tree()
        _newTree.data = estate
        estate.idPere = _parent.data.id
        _newTree.parent = _parent
        _parent.addChild(_newTree)

    def correction(self, currentState=_tree(), plot=Plot()):
        if plot.type == PLOTType.POLAR:
            #_previousState = currentState.parent.data
            estate = currentState.data
            duree = - plot.dateTime.msecsTo(estate.time)/1000.0
 
            vel_x = (plot.z_XY[0] - estate.state[0]) / duree
            vel_y = (plot.z_XY[1] - estate.state[2]) / duree
            print('correction')
            print([vel_x, vel_y])
            estate.setVelocity([vel_x, vel_y])
            estate.prediction(plot.dateTime)

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
            estate = State.copyState(cState.data)
            estate.prediction(time, True)

            self.addState(estate, cState)

        currentStates.clear()

    def taillePiste(self):
        return self.tree.depth()

    def getState(self, idState=-1):

        flag, val = self.tree.getData(idState)
        if flag:
            return val
        return None

    def update(self, plots=[], sensorPosition=Position(), sensorOrientation=Orientation()):
        # self.tree.displayTree()
        currentStates = []
 
        if len(plots) > 1:
            self.tree.getChilds(currentStates)
            dateTime = plots[0].dateTime
            for cState in currentStates:
                x, P, X, v = cState.data.prediction(dateTime)
                #print('after prediction')
       
                Gstate = group(dateTime, plots, _dim.XY)
                Gstate.estimation(x, P, X, v, plots, dateTime)
                #print('after estimation')
                #print(Gstate.X)
                self.addState(Gstate, cState)
            currentStates.clear()

        elif len(plots) == 1:
            plot = plots[0]
            print(['update ------> track id',self.id])
            print(self.taillePiste())
            
            if self.taillePiste() == 1 and plot.type == PLOTType.POLAR:
                
                print(['Initialisation ------> track id',self.id])
                estate = State.copyState(self.tree.data)
 
                self.addState(estate, self.tree)
 
                self.tree.getChilds(currentStates)
                
                estate.classification(plot) #ENSTA Todo
 
                self.correction(currentStates[0], plot)
                currentStates.clear()
             
     
            
            elif self.taillePiste() >= 2 and (plot.type == PLOTType.POLAR or plot.type == PLOTType.ANGULAR):
                self.tree.getChilds(currentStates)
                print(['usual cycle ------> track id',self.id])
        
                for cState in currentStates:
                    estate = State.copyState(cState.data)
         
                    estate.prediction(plot.dateTime)

                    estate.estimation(plot, self.trackerType, sensorPosition, sensorOrientation)
                    
                    estate.classification(plot) #ENSTA Todo 
                    

                    self.addState(estate, cState)
                currentStates.clear()
   
#        elif self.taillePiste() > 3 and plot.Type == PLOTType.POLAR:
#            print('update--> 222')
#            return
#        self.tree.getChilds(currentStates)
#
#        for cState in currentStates:
#            print('update--> 3')
#            estate = State()
#            estate.state   = _copy(cState.data.state)
#            estate.covariance   = _copy(cState.data.covariance)
#            estate.location = _copy(cState.data.location)
#            estate.time       = _copy(cState.data.time)
#            estate.mode       = _copy(cState.data.mode)
#
#
#            estate.estimation(plot,_scan)
#
#            self.addState(estate,cState)
#

    def validate(self,_plot,threshold = 14):
        currentStates = []
       
        self.tree.getChilds(currentStates)

        for cState in currentStates:
                [flag, structG] = cState.data.gating(_plot, threshold)
                if flag:
                    return True
        return False
    def gating(self,_plot,threshold = 14):
        currentStates = []
       
        self.tree.getChilds(currentStates)

        for cState in currentStates:
                [flag, structG] = cState.data.gating(_plot, threshold)
                if flag:

                    return True,structG
        return False, None
    
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
    def removeChilds(self,_currentNode,lastDate):
        
        if _currentNode.childs==[] and _currentNode.data.time < lastDate :
            return True
            
        for _child in _currentNode.childs:
             if self.removeChilds(_child,lastDate):
      
                 _currentNode.removeChild(_child)
        
        return False
    
      
        
        
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

            stdM = np.sqrt(win.data.covariance[0,0]  + win.data.covariance[2,2]  )
            stdV = np.sqrt(win.data.covariance[1,1]  + win.data.covariance[3,3]  )
  
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
            if self.locObj:
                for i in self.locObj:
                    if i in axes.lines:
                        axes.lines.remove(i)
            if self.ellipsesObj:
                self.ellipsesObj.clear()
                self.ellipsesObj = []
            if self.shapeObj != None:
                self.shapeObj.remove()
                self.shapeObj = None
            if self.textObj != None:
                self.textObj.remove()
                self.textObj = None

            if self.quiverObj != None:
                self.quiverObj.remove()
                self.quiverObj = None

            if self.iconeObj != None:
                self.iconeObj.remove()
                self.iconeObj = None
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
                coords.append((pos.longitude,pos.latitude))

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
            latitude.append(pos.latitude)
            longitude.append(pos.longitude)
            current = c.parent
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
            self.textObj = axes.text(pos.longitude, pos.latitude, 'track : ' + str(self.id),  color=self.color.name(), visible=self.textIsVisible)
            self.quiverObj = axes.quiver(pos.longitude, pos.latitude, dx, dy, color=self.color.name(), alpha=0.8)
           
            # =============================
            # display image
            # =============================
            if displayIcone:
                self.iconeObj = imscatter(
                    pos.longitude, pos.latitude, 'icones/unknown.png', axes)
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
            if defined(c.data.X):
                # attention en m alors qu'on affiche en WGS84
#                print(c.data.X)
#                print(c.data.x)
#                print(c.data.P)
                lmbda, u = np.linalg.eig(c.data.X)
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
            # =============================
            # display track
            # =============================
            while current != None:
                pos = current.data.location
                latitude.append(pos.latitude)
                longitude.append(pos.longitude)              
                #axes.text(pos.longitude, pos.latitude,  current.data.time.toString('hh:mm:ss.z'),  color=self.color.name() )
                current = current.parent
            # ,visible=self.trajectoryIsVisible)
            if  displayTack:
                self.locObj = axes.plot(longitude, latitude, '+-', color=self.color.name(), linewidth=2)

            #canvas.update()
            #canvas.flush_events()
            #canvas.draw()
        childs.clear()
