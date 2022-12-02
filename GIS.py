from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtOpenGL import *
from PyQt5.QtWidgets import *
from readShapefile import shapefile as shpFile
from readGeoTiff import cartographie as cartoFile
from readGeoTiff import TYPE_CARTO
from readDTED import dted
from enum import Enum
from matplotlib.figure import Figure
from matplotlib.backend_bases import key_press_handler
from matplotlib.patches import Rectangle
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)    
import numpy as np
from target  import Target
from scan import  PLOTType

from Managers.dataManager import DataManager

#from toolTracking.Gaussian import GraphWidget2

class GISMode(Enum):
    nomode          = 0
    openfile        = 1
    update          = 2
    updateCarto     = 3
    updateTarget    = 4
    updateSensor    = 5
    updateTrack     = 6
    updatePlatform  = 7
    updateNode      = 8
    updatePlot      = 9
    updateState     = 10


 
        
class GIS(QWidget):
 

        message             = pyqtSignal('QString');
        emitRemoveTarget    = pyqtSignal('QString');
        emitRemoveNode      = pyqtSignal('QString');
        emitRemoveSensor    = pyqtSignal('QString');
        emitTrajectory      = pyqtSignal('QString');
        emitEditTarget      = pyqtSignal('QString');
        emitEditNode        = pyqtSignal('QString');
        emitAddSensor       = pyqtSignal('QString');
        emitNodeLocation    = pyqtSignal('QString');
        emitEditSensor      = pyqtSignal('QString');
        emitAddTracker      = pyqtSignal('QString');
        emitEditTracker     = pyqtSignal('QString');
        def __init__(self):
            super(GIS, self).__init__()
            self.tree   = QTreeWidget()
            
            self.mode   = GISMode.updateCarto
            header=QTreeWidgetItem(["name","type","value"])
            self.tree.setHeaderItem(header)
            self.root = QTreeWidgetItem(self.tree)
            self.tree.topLevelItem(0).setText(0, "Geographic layers")
            self.tree.customContextMenuRequested.connect(self.menuContextTree)
            self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
            self.layerRoad          = QTreeWidgetItem(self.root,['road','trafficability','polyline'])
            self.layerVegetation    = QTreeWidgetItem(self.root,['vegetation','trafficability','area'])
            self.layerBuilding      = QTreeWidgetItem(self.root,['building','trafficability','area'])
            self.layerWater         = QTreeWidgetItem(self.root,['water','trafficability','polyline & area'])
            self.layerWaterArea     = QTreeWidgetItem(self.root,['waterArea','trafficability','polyline & area'])
            self.layerCarto         = QTreeWidgetItem(self.root,['Maps','','area'])
            self.layerDTED          = QTreeWidgetItem(self.root,['DTED','','area'])
            #TODO - Refactoring
            """
            Make some objects to avoid layerRoad, layerVegetation... and all those test on it.
            #You will be able to clean this item, its subItem and those methods :
            openFile, display, changeColor, changeStyle
            """
            self.road = None
            self.roadlayer()
            self.vegetationlayer()
            self.buildinglayer()
            self.waterlayer()
            self.cartolayer()            
            self.DTEDlayer()
            #self.mutex    = QMutex()
        
            self.plotsObj = []
            
            self.statesObj =[]
            
            self.rect = None #(Area of interest)
    
            self.tree.itemClicked.connect(self.onClickItem)
            #self.tree.setUpdatesEnabled(False);
        
            
            self.bbox = [-180,180,-90,90]#[5.35, 5.38, 43.28, 43.30]#[13.7,13.8,50.90,51.05]#
           
            #bbox
            self.bbox_itm  = QTreeWidgetItem(self.root,['bbox','value','unit'])
            self.bbox_itm.setCheckState(0, Qt.Checked)
            QTreeWidgetItem(self.bbox_itm  ,['x_min','-180','(in °)'])#13.7
            QTreeWidgetItem(self.bbox_itm  ,['x_max','180','(in °)'])#13.8
            QTreeWidgetItem(self.bbox_itm  ,['y_min','-90','(in °)'])#N50.90
            QTreeWidgetItem(self.bbox_itm  ,['y_max','90','(in °)'])#;51.05

                     
        
        
            
            self.dtedList = [] 
            
            
            self.Itemdted = [] 
            #zoom leve
            
            self.zoomLevel = 0
           
            #area of interest
            
            self.x0 = None
            self.y0 = None
            self.x1 = None
            self.y1 = None
            
 
 
            self.manager = DataManager.instance()
            
 
            
            #List des détections
            
            self.detections = []
            
            #List des states
            
            self.states = []
            
            #gaussian widget
            
            self.GaussianWidget = None
            
            #Dictionary of biasControler


        def  removeStates(self):
             if self.statesObj!=[]:
                self.axes.lines.remove(self.statesObj)
             self.statesObj = []           
        def removeDetections(self):
            if self.plotsObj!=[]:
                self.axes.lines.remove(self.plotsObj)
            self.plotsObj = []
        def receiveStates(self,_states):
            self.states =  self.states + _states
            self.mode = GISMode.updateState
            self.run()
            
        def receiveDetections(self,_detections):
            #self.mutex.lock()
            self.detections =  self.detections + _detections
            #self.mutex.unlock()
       
            self.mode = GISMode.updatePlot
            self.run()
        def drawStates(self):
            self.removeStates()
      
            x = []
            y = []
   
            for _det in self.states:
   
                   x.append(_det.location.longitude)
                   y.append(_det.location.latitude)
               #box_coords = list(zip(x, y))

            couleur = QColor(Qt.darkBlue)
            #plotsObj, = self.axes.scatter(box_coords, marker='o', c='r', edgecolor='b')
            #plotsObj,  = self.axes.plot(self.Position[0].longitude + distance *np.cos(an),self.Position[0].latitude + distance *np.sin(an) ,color=couleur.name()) 
            #self.axes.plot(box_coords,color=couleur.name())
            if x!=[] and y !=[]:

                self.statesObj,  =  self.axes.plot(x,y, marker='o', color=couleur.name(), ls='')
                self.axes.draw_artist(self.statesObj )
                
                self.canvas.blit(self.axes.bbox)
                self.canvas.update()
                self.canvas.flush_events()
                #self.plotsObj = plotsObj
            self.states.clear()   
        def drawDetections(self):
      
            self.removeDetections()
      
            x = []
            y = []
   
            for _det in self.detections:
         
               if _det.type  == PLOTType.POLAR:
               # for _det in self._detections:
                   x.append(_det.Position.longitude) 
                   y.append(_det.Position.latitude)
               #box_coords = list(zip(x, y))

            couleur = QColor(Qt.gray)
            #plotsObj, = self.axes.scatter(box_coords, marker='o', c='r', edgecolor='b')
            #plotsObj,  = self.axes.plot(self.Position[0].longitude + distance *np.cos(an),self.Position[0].latitude + distance *np.sin(an) ,color=couleur.name()) 
            #self.axes.plot(box_coords,color=couleur.name())
            if x!=[] and y !=[]:

                self.plotsObj,  =  self.axes.plot(x,y, marker='o', color=couleur.name(), ls='')
                self.axes.draw_artist(self.plotsObj )
                
                self.canvas.blit(self.axes.bbox)
                self.canvas.update()
                self.canvas.flush_events()
                #self.plotsObj = plotsObj
            self.detections.clear()

          
        def setParameters(self,  axes, canvas):
            self.axes = axes
            self.canvas =canvas
            
         
            
        def newAreaOfInterest(self):
            self.bbox_itm.child(0).setText(1, str(self.x0))
            self.bbox_itm.child(1).setText(1, str(self.x1))
            self.bbox_itm.child(2).setText(1, str(self.y0))
            self.bbox_itm.child(3).setText(1, str(self.y1))

            if self.rect == None : 
                self.rect = Rectangle((self.x0,self.y0), self.x1-self.x0, self.y1 - self.y0, facecolor='yellow', edgecolor='violet',alpha = 0.5)
                self.axes.add_patch(self.rect)
            else:
                self.rect.set_width(float(self.x1 - self.x0))
                self.rect.set_height(float(self.y1 - self.y0))
                self.rect.set_xy((self.x0, self.y0))
                
      
            
        def refreshbbox(self):
            self.bbox = self.axes.axis()
            child_count = self.bbox_itm.childCount()
            for i in range(child_count):
                item = self.bbox_itm.child(i)
                item.setText(1,str(self.bbox[i]))
            #self.emit(SIGNAL("message"),"new bbox = " + str(self.bbox[0]) +' '+ str(self.bbox[1]) + ' '+ str(self.bbox[2])+ ' '+ str(self.bbox[3]))
            self.message.emit("new bbox = " + str(self.bbox[0]) +' '+ str(self.bbox[1]) + ' '+ str(self.bbox[2])+ ' '+ str(self.bbox[3]))
        def readbbox(self):
            self.bbox = []
            
            child_count = self.bbox_itm.childCount()
            for i in range(child_count):
                item = self.bbox_itm.child(i)
                self.bbox.append(float(item.text(1)))
     
            self.mode = GISMode.updateCarto            
            self.run()
         
        def cartolayer(self):
            
          #   QTreeWidgetItem(self.layerCarto,['file','no file','image'])
             self.maps = []
             
        def DTEDlayer(self):
         #    QTreeWidgetItem(self.layerDTED,['file','no file','image'])
             self.dted = []
             
        def roadlayer(self):
            
            # QTreeWidgetItem(self.layerRoad,['file','no file','polyline'])
             self.road = []
             #self.layerRoad.itemClicked.connect(self.onClickItem)
        def waterlayer(self):
           #  QTreeWidgetItem(self.layerWater,['file','no file','polyline'])
             self.water = []    
            # QTreeWidgetItem(self.layerWaterArea,['file','no file','polyline'])
             self.waterArea = []                 
             
        def vegetationlayer(self):
            
          #   QTreeWidgetItem(self.layerVegetation,['file','no file','shapearea'])
             self.vegetation = []
             
        def buildinglayer(self):
            
          #   QTreeWidgetItem(self.layerBuilding,['file','no file','shapearea'])
             self.building = []
    
        def init(self):
     
            self.fileName =  'data/carto/dnb_land_ocean_ice.2012.3600x1800_geo.tif'#'MOS_EU_LAEA_2000.tif'
            
            self.currentItem = self.layerCarto
            self.openFile('Maps') 
          
        def handleItemChanged(self,item,column):
            itemPere = item.parent()
            if column!=0:
                return
            if itemPere and itemPere.text(0) == 'Nodes' :
                    for _var in self.manager.nodes():
                        if item.text(0) == str(_var.id):
                            _var.set_visible(item.checkState(column) )
                            break
                        
            if itemPere and itemPere.text(0) == 'Sensors' :
                    for _var in self.manager.sensors():
                        if item.text(0) == str(_var.id):
                            _var.set_visible(item.checkState(column) )
                            break 
            if itemPere and itemPere.text(0) == 'Targets' :
                    for _var in self.manager.targets():
                        if item.text(0) == str(_var.id):
                            _var.set_visible(item.checkState(column) )
                            break
            
            if itemPere and  itemPere.text(0) == 'Maps':
                u = 0
                for layer in self.maps:
                    if int(item.text(0))==u:

                        layer.set_visible(item.checkState(column))
                        break
                    u = u+1
                    
            if itemPere and   itemPere.text(0) == 'DTED':  
                    u = 0
                    for layer in self.dtedList:
         
                        if int(item.text(0))==u:
                            #print("extinction des feux")    
                            layer.set_visible(item.checkState(column))
                            break
                        u = u+1
            if itemPere and (itemPere.text(0) == 'road' or itemPere.text(0) == 'vegetation' or itemPere.text(0) == 'building' or itemPere.text(0) == 'water' or itemPere.text(0) == 'waterArea'):
                       for layer in self.road.containers:
                            if layer.fclass == item.text(0)  :
                                     layer.set_visible(item.checkState(column))
 
            if item.text(0) == 'bbox' and self.rect!=None :     
                self.rect.set_visible(item.checkState(column))                                      
#            for i in range(item.childCount()):
#                self.handleItemChanged(item.child(i),column)
            self.canvas.draw_idle()
            self.canvas.blit(self.axes.bbox)  
              
                                    
     
            
                 
               # if   self.mode != GISMode.nomode:
                #    return 
#                if item.checkState(column) == Qt.Checked:
#                    if self.road:
#                        for layer in self.road.containers:
#                            if layer.fclass == item.text(0) and itemPere.text(0) == 'road':
#                                for u in layer.layerObj:
#                                    u.set_visible(True)
#                                
#                    if self.vegetation:
#                        for layer in self.vegetation.containers:
#                            if layer.fclass == item.text(0) and itemPere.text(0) == 'vegetation':
#                                for u in layer.layerObj:
#                                    u.set_visible(True)
#                    if self.building:
#                        for layer in self.building.containers:
#                            if layer.fclass == item.text(0) and itemPere.text(0) == 'building':
#                                for u in layer.layerObj:
#                                    u.set_visible(True)
#                    if self.water:
#                        for layer in self.water.containers:
#                            if layer.fclass == item.text(0) and itemPere.text(0) == 'water':
#                                for u in layer.layerObj:
#                                    u.set_visible(True)
#                    if self.waterArea:
#                        for layer in self.waterArea.containers:
#                            if layer.fclass == item.text(0) and itemPere.text(0) == 'waterArea':
#                                for u in layer.layerObj:
#                                    u.set_visible(True) 
#    
#                    if self.dted:
#                        if itemPere:
#                            u = 0
#                            for layer in self.dted:
#                                u = u+1
#                                if itemPere.text(0) == 'DTED' and int(item.text(0))==u:
#             
#                                    layer.set_visible(True)
#                                    break
                    
         
                                    
#                elif item.checkState(column) == Qt.Unchecked:
#                    if self.road:
#                        for layer in self.road.containers:
#                            if layer.fclass == item.text(0) and itemPere.text(0) == 'road':
#                                for u in layer.layerObj:
#                                    u.set_visible(False)
#                    if self.vegetation:
#                        print(self.vegetation)
#                        for layer in self.vegetation.containers:
#                            if layer.fclass == item.text(0)  and itemPere.text(0) == 'vegetation':
#                                for u in layer.layerObj:
#                                    u.set_visible(False)
#                    if self.building:
#                        for layer in self.building.containers :
#                            if layer.fclass == item.text(0) and itemPere.text(0) == 'building':
#                                for u in layer.layerObj:
#                                    u.set_visible(False)
#                            
#                    if self.water:
#                        for layer in self.water.containers:
#                            if layer.fclass == item.text(0) and itemPere.text(0) == 'water':
#                                for u in layer.layerObj:
#                                    u.set_visible(False)
#                    if self.waterArea:
#                        for layer in self.waterArea.containers:
#                            if layer.fclass == item.text(0) and itemPere.text(0) == 'waterArea':
#                                for u in layer.layerObj:
#                                    u.set_visible(False)
#                 
#                    if self.maps:
#                        u = 0
#                        if itemPere:
#                            for layer in self.maps:
#                                u = u+1
#                                if itemPere.text(0) == 'Maps' and int(item.text(0))==u:
#                                    layer.set_visible(False)
#                                    break
#                                
#                         
#                    if self.dted:
#                        if itemPere:
#                            u = 0
#                            for layer in self.dted:
#                                u = u+1
#                                if itemPere.text(0) == 'DTED' and int(item.text(0))==u:
#                                    layer.set_visible(False)
#                                    break
#                    if self.Nodes:          
#                
#     
#                        if itemPere and itemPere.text(0) == 'Nodes':
#                            for _tar in self.Nodes:
#                                if item.text(0) == str(_tar.id):
#                                        print('False visibe')
#                                        _tar.set_visible(False,'location')
#                                        _tar.set_visible(False,'label')
#                                        break 
#                        if itemPere and itemPere.text(0) == 'Node':
#                            for _tar in self.Nodes:
#                                if itemPere.text(0) == str(_tar.id):
#                                        print('False visibe')
#                                        _tar.set_visible(False,item.text(0))
#                                        break           
              
                
           
   
      
                
        def onClickItem (self, item, column):  
            
            self.handleItemChanged(item, column)
            '''
            itmPere = item.parent();
            if item.text(0) == 'file':
               
                if itmPere.text(0)  == 'vegetation' or itmPere.text(0)  == 'road' or itmPere.text(0) =='building' or itmPere.text(0) =='water' or itmPere.text(0) =='waterArea':
                    self.fileName,filter = QFileDialog.getOpenFileName(self.tree, 'open ' + itmPere.text(0) + ' file', '.','*.shp')
                elif itmPere.text(0)  == 'Maps':
                    self.fileName,filter  = QFileDialog.getOpenFileName(self.tree, 'open ' + itmPere.text(0) + ' file', '.','*.tif')
                elif itmPere.text(0)  == 'DTED':
                    self.fileName = QFileDialog.getOpenFileName(self.tree, 'open ' + itmPere.text(0) + ' file', '.','*.dt2;*.tif')
                
                self.currentItem = item
                self.openFile()
            
            '''    
 
        def actionOpenFile(self):
            
                 
                layer = self.currentItem.text(0)
         
                if layer  == 'vegetation' or layer  == 'road' or layer =='building' or layer =='water' or layer =='waterArea':
                    self.fileName,filter = QFileDialog.getOpenFileName(self.tree, 'open ' + layer + ' file', '.','*.shp')
                elif layer  == 'Maps':
                    self.fileName,filter  = QFileDialog.getOpenFileName(self.tree, 'open ' + layer + ' file', '.','*.tif')
                elif layer  == 'DTED':
                    self.fileName,filter  = QFileDialog.getOpenFileName(self.tree, 'open ' + layer + ' file', '.',str("file (*.dt2 *.tif)"))
                self.openFile(layer)    
        def openFile(self,layer):        
                
                itmPere = self.currentItem
                if self.fileName and layer  == 'road':
                     self.road = shpFile(self.fileName, layer)
                     self.road.update()
          
                     self.currentItem.setText(1,self.fileName)
                     self.road.display(self.axes,self.bbox,self.canvas)
                     #creation des sous layer                      
                     for i in range(len(self.road.containerType)):
                         _itm =  QTreeWidgetItem(itmPere,[str(self.road.containerType[i]),'',''])
                         _itm.setCheckState(0, Qt.Checked)
                     #self.newLayer.emit(self.road)     
                elif self.fileName and layer  == 'vegetation':
                     self.vegetation = shpFile(self.fileName, layer)
                     self.vegetation.update()
                     self.vegetation.display(self.axes,self.bbox,self.canvas)
                     self.currentItem.setText(1,self.fileName)
                     #creation des sous layer                      
                     for i in range(len(self.vegetation.containerType)):
                         _itm =  QTreeWidgetItem(itmPere,[str(self.vegetation.containerType[i]),'',''])
                         _itm.setCheckState(0, Qt.Checked)
                     #self.newLayer.emit(self.vegetation)
                elif self.fileName and layer =='building':
                     self.building = shpFile(self.fileName, layer)
                     self.building.update()
                     self.building.display(self.axes,self.bbox,self.canvas)
                     self.currentItem.setText(1,self.fileName)
                     #creation des sous layer                      
                     for i in range(len(self.building.containerType)):
                         _itm =  QTreeWidgetItem(itmPere,[str(self.building.containerType[i]),'',''])
                         _itm.setCheckState(0, Qt.Checked)  
                     #self.newLayer.emit(self.building)
                elif self.fileName and itmPere.text(0) =='water':
                     self.water = shpFile(self.fileName, itmPere.text(0))
                     self.water.update()
                     self.water.display(self.axes,self.bbox,self.canvas)
                     self.currentItem.setText(1,self.fileName)
                     #creation des sous layer                      
                     for i in range(len(self.water.containerType)):
                         _itm =  QTreeWidgetItem(itmPere,[str(self.water.containerType[i]),'',''])
                         _itm.setCheckState(0, Qt.Checked)        
                    # self.newLayer.emit(self.water)
                elif self.fileName and layer =='waterArea':
                     self.waterArea = shpFile(self.fileName, layer)
                     self.waterArea.update()
                     self.waterArea.display(self.axes,self.bbox,self.canvas)
                     self.currentItem.setText(1,self.fileName)
                     #creation des sous layer                      
                     for i in range(len(self.waterArea.containerType)):
                         _itm =  QTreeWidgetItem(itmPere,[str(self.waterArea.containerType[i]),'',''])
                         _itm.setCheckState(0, Qt.Checked)     
                    # self.newLayer.emit()    
                elif self.fileName and layer =='Maps':
                        carte = cartoFile()
                        carte.read(self.fileName,TYPE_CARTO.CARTO)
                        carte.display(self.axes) 
                        self.maps.append(carte)
                        _itm =  QTreeWidgetItem(itmPere,[str(itmPere.childCount()) ,self.fileName,''])
                        _itm.setCheckState(0, Qt.Checked)
                        #print("Carto has been read and bbox = " + str(carte.x0)+' '+ str(carte.x1) + ' '+ str(carte.y1)+ ' '+ str(carte.y0))
                        self.message.emit("Carto has been read and bbox = " + str(carte.x0)+' '+ str(carte.x1) + ' '+ str(carte.y1)+ ' '+ str(carte.y0))
                        #pyqtSignal("Carto has been read and bbox = " + str(carte.x0)+' '+ str(carte.x1) + ' '+ str(carte.y1)+ ' '+ str(carte.y0),"message")
                elif self.fileName and layer =='DTED':
                    
                        carte = None
                        if '.tif' in self.fileName:
                            carte = dted()#cartoFile()
                            carte.read(self.fileName)#,TYPE_CARTO.DTED)
                     
                        if '.dt2' in self.fileName:
                       
                            carte = dted()
                            carte.read(self.fileName)
                        if self.fileName and carte != None:
                            
                            self.dtedList.append(carte)
                            _itm =  QTreeWidgetItem(itmPere,[str(itmPere.childCount()) ,self.fileName,''])
                            _itm.setCheckState(0, Qt.Checked)
                        
                            
                            #print("DTED  has been read and bbox = " + str(carte.x0)+' '+ str(carte.x1) + ' '+ str(carte.y1)+ ' '+ str(carte.y0))
                        #self.emit(SIGNAL("message"),"DTED has been read and bbox = " + str(carte.x0)+' '+ str(carte.x1) + ' '+ str(carte.y1)+ ' '+ str(carte.y0))
                     
                self.mode = GISMode.updateCarto
                self.run()
                 
        def run(self):
            
            #self.mutex.lock() 

            #print(["nb detections" ,len(self.detections)])
            #print('in run',self.mode.name)
            if self.mode == GISMode.updateCarto :
                '''
                if self.road:
                    self.road.display(self.axes,self.bbox,self.canvas)  
                if self.vegetation:
                    self.vegetation.display(self.axes,self.bbox,self.canvas)     
                if self.building:
                    self.building.display(self.axes,self.bbox,self.canvas)  
                if self.water:
                    self.water.display(self.axes,self.bbox,self.canvas)  
                if self.waterArea:
                    self.waterArea.display(self.axes,self.bbox,self.canvas)  
                '''
                # if self.maps:
                #     for carto in self.maps:
                #         carto.display(self.axes) 
                if self.dtedList:
                    for carto in self.dtedList:
            
                        carto.display(self.axes)
            if self.mode == GISMode.updateNode:
                    for _node in self.manager.nodes():
                        #print('---> in GISMode display nodes')
                        _node.toDisplay(self.axes,self.canvas)
            if self.mode == GISMode.updatePlot:
                    self.drawDetections();
            if self.mode == GISMode.updateState:
                    self.drawStates();
            if self.mode == GISMode.updateSensor:
             
                    for _sensor in self.manager.sensors():
                        _sensor.toDisplay(self.axes,self.canvas)
            if self.mode == GISMode.updateTarget:
  
                    for _target in self.manager.targets():
                        _target.toDisplay(self.axes)            
                        
                        
            self.mode = GISMode.nomode
            #self.canvas.draw()
            #self.canvas.draw_idle()
            self.canvas.blit(self.axes.bbox)
            self.canvas.draw()
            #self.mutex.unlock()
#            self.canvas.blit(self.axes.bbox)
#            self.canvas.update()
#            self.canvas.flush_events()
            
        def changeColor(self):
     
            item = self.tree.currentItem()
 
            if not item.parent():
              return
           
            name = item.text(0)
            layer = item.parent().text(0)

            if layer  == 'road':
                self.road.ChangeColor(name)
            elif layer  == 'vegetation':
                self.vegetation.ChangeColor(name)
            elif layer  == 'building':
                self.biilding.ChangeColor(name) 
            elif layer  == 'water':
                self.water.ChangeColor(name) 
            elif layer  == 'waterArea':
                self.waterArea.ChangeColor(name)
            elif layer == 'Targets':
                for _tar in self.Targets:
                    if name == _tar.id:
                        _tar.ChangeColor()
                        _tar.update()
                        break
             
            self.run()    
            
        def changeStyle(self):
     
            item = self.tree.currentItem()
 
            if not item.parent():
              return
           
            name = item.text(0)
            layer = item.parent().text(0)
            
     
            if layer  == 'road':
                self.road.changeStyle(name)
            elif layer  == 'vegetation':
                self.vegetation.changeStyle(name)
            elif layer  == 'building':
                self.biilding.changeStyle(name) 
            elif layer  == 'water':
                self.water.v(name) 
            elif layer  == 'waterArea':
                self.waterArea.changeStyle(name)
            
            self.run()    
           
        def menuContextTree(self, point):
           index = self.tree.indexAt(point)
           if not index.isValid():
              return
           
           item = self.tree.itemAt(point)
           itemParent = item.parent()
           self.currentItem = item
           if not itemParent:
              return
           
           name = item.text(0)
           layer = itemParent.text(0)
           
           if layer=='Geographic layers' : 
               menu=QMenu()
               action=menu.addAction("Souris au-dessus de %s"%name)
   
               menu.addSeparator()
               colorAction = QAction("Change layer color",self.tree)
               action_1=menu.addAction(colorAction)
               colorAction.setStatusTip('select new layer color')
               colorAction.triggered.connect( self.changeColor)
               fontAction = QAction("Change layer style",self.tree)
               action_2=menu.addAction(fontAction)
               fontAction.setStatusTip('select new layer style')
               fontAction.triggered.connect( self.changeStyle)
               action_3=menu.addAction("Add file")
               action_3.triggered.connect( self.actionOpenFile)
               menu.exec_(QCursor.pos())
            
           elif layer=='Tracker':
               menu=QMenu()
               imageEdit= QPixmap("icones/edit.png")
               icon  = QIcon(imageEdit)
               action=menu.addAction("edit tracker %s"%name)
               action.setStatusTip('edit tracker')
               action.setIcon(icon)
               action.triggered.connect( self.editTracker)
               menu.exec_(QCursor.pos())
               
               
               
           elif layer=='Sensors' :
               menu=QMenu()
               imageEdit= QPixmap("icones/edit.png")
               icon  = QIcon(imageEdit)
               action=menu.addAction("edit sensor %s"%name)
               action.setStatusTip('edit sensor')
               action.setIcon(icon)
               action.triggered.connect( self.editSensor)
               
               imageDeleted= QPixmap("icones/delete.png")
               icon  = QIcon(imageDeleted)
               deleteTarget = QAction("remove sensor",self.tree)
               menu.addAction(deleteTarget)
               deleteTarget.setStatusTip('delete selected sensor')
               deleteTarget.setIcon(icon)
               deleteTarget.triggered.connect( self.removeSensor)
          
            
               menu.exec_(QCursor.pos())

 

           elif layer=='Nodes' :
               menu=QMenu()
               menu.setLayoutDirection(Qt.LeftToRight)
               imageEdit= QPixmap("icones/edit.png")
               icon  = QIcon(imageEdit)
               action=menu.addAction("edit node %s"%name)
               action.setStatusTip('edit node')
               action.setIcon(icon)
               action.triggered.connect( self.editNode)
               menu.addSeparator()
               
               imageTrajectory= QPixmap("icones/trajectory.png")
               icon  = QIcon(imageTrajectory)
               trajectoryAction = QAction("new location",self.tree)
               menu.addAction(trajectoryAction)
               trajectoryAction.setStatusTip('select new location')
               trajectoryAction.setIcon(icon)
               trajectoryAction.triggered.connect( self.locationNode)
               menu.addSeparator()
               
               imageDeleted= QPixmap("icones/delete.png")
               icon  = QIcon(imageDeleted)
               
               deleteNode = QAction("destruction du noeud",self.tree)
               menu.addAction(deleteNode)
               deleteNode.setStatusTip('delete selected node')
               deleteNode.setIcon(icon)
               deleteNode.triggered.connect( self.removeNode)
               
               icon  = QIcon("icones/addSensor.png")
               addSensor = QAction("Add sensor",self.tree)
               menu.addAction(addSensor)
               addSensor.setStatusTip('add sensor to node')
               addSensor.setIcon(icon)
               addSensor.triggered.connect(self.addSensor)
               
               icon         = QIcon("icones/tracker.png")
               addTracker   = QAction("Add tracker",self.tree)
               menu.addAction(addTracker)
               addTracker.setStatusTip('add tracker to node')
               addTracker.setIcon(icon)
               addTracker.triggered.connect( self.addTracker)

        
               
               #colorAction.triggered.connect( self.changeColor)
               #fontAction = QAction("Change layer style",self.tree)
               #action_2=menu.addAction(fontAction)
               #fontAction.setStatusTip('select new layer style')
               #fontAction.triggered.connect( self.changeStyle)
               #action_3=menu.addAction("Choix 3")
               #menu.exec_(QCursor.pos())  
               
               menu.exec_(QCursor.pos())
           elif layer=='Targets' :
               menu=QMenu()
               imageEdit= QPixmap("icones/edit.png")
               icon  = QIcon(imageEdit)
               action=menu.addAction("edit target %s"%name)
               action.setStatusTip('edit target')
               action.setIcon(icon)
               action.triggered.connect( self.editTarget)
               menu.addSeparator()
               
               imageTrajectory= QPixmap("icones/trajectory.png")
               icon  = QIcon(imageTrajectory)
               trajectoryAction = QAction("creation d'une nouvelle trajectoire",self.tree)
               menu.addAction(trajectoryAction)
               trajectoryAction.setStatusTip('select new trajectory')
               trajectoryAction.setIcon(icon)
               trajectoryAction.triggered.connect( self.trajectoryTarget)
               menu.addSeparator()
               
               imageDeleted= QPixmap("icones/delete.png")
               icon  = QIcon(imageDeleted)
               
               deleteTarget = QAction("destruction de la cible",self.tree)
               menu.addAction(deleteTarget)
               deleteTarget.setStatusTip('delete selected target')
               deleteTarget.setIcon(icon)
               deleteTarget.triggered.connect( self.removeTarget)
               #colorAction.triggered.connect( self.changeColor)
               #fontAction = QAction("Change layer style",self.tree)
               #action_2=menu.addAction(fontAction)
               #fontAction.setStatusTip('select new layer style')
               #fontAction.triggered.connect( self.changeStyle)
               #menu.exec_(QCursor.pos())  
               
               menu.exec_(QCursor.pos())
               
        def locationNode(self):
            item = self.tree.currentItem()
            if item :
                id_node = item.text(0)
                self.emitNodeLocation.emit(("%s")%(id_node))
                
        def editSensor(self):
            item = self.tree.currentItem()
            if item :
                id_sensor = item.text(0)
                self.emitEditSensor.emit(("%s")%(id_sensor))
        def editTracker(self):
            item = self.tree.currentItem()
            if item :
                id_tracker = int(item.text(0))
                self.emitEditTracker.emit(("%s")%(id_tracker))    
        def editNode(self):
            item = self.tree.currentItem()
            if item :
                id_node = item.text(0)
                self.emitEditNode.emit(("%s")%(id_node))
          
        def removeSensor(self):
            item = self.tree.currentItem()
            
            if item :
                id_sensor = item.text(0)
                 
                for _sensor in self.manager.sensors():      
                    _treeItem = _sensor.treeWidgetItem
                    if _treeItem and _sensor.id == id_sensor:
       
                       _treeItem.parent().removeChild(_treeItem) 
                       self.message.emit(("request to remove sensor %s")%(id_sensor)) 
               
                       _sensor.clearGrpahicalData(self.canvas,self.axes) 
                       self.manager.removeSensor(_sensor)
                       self.emitRemoveSensor.emit(("%s")%(id_sensor))
                       self.run()
                       return
        def removeNode(self):
            item = self.tree.currentItem()
            
            if item :
                id_node = item.text(0)
                 
                for _node in self.manager.nodes():      
                    _treeItem = _node.treeWidgetItem
                    if _treeItem and _node.id == id_node:
       
                       _treeItem.parent().removeChild(_treeItem) 
                       self.message.emit(("request to remove node %s")%(id_node)) 
                       
                       _node.clear(self.canvas,self.axes) 
                       
                       while _node.sensors!=[] :
                             _sensor  =  _node.sensors[0]
                             _sensor.clearGrpahicalData(self.canvas,self.axes) 
                             self.manager.removeSensor(_sensor)
                           
                       self.manager.removeNode(_node.id)
                       self.emitRemoveNode.emit(("%s")%(id_node))
                       self.mode == GISMode.updateNode
                       self.run()
                       return
        def addTracker(self):

            item = self.tree.currentItem()
            if item :
                id_node = item.text(0)
                self.emitAddTracker.emit(("%s")%(id_node))
                
        def addSensor(self):
            item = self.tree.currentItem()
            if item :
                id_node = item.text(0)
                self.emitAddSensor.emit(("%s")%(id_node))
        def removeTarget(self):      
             item = self.tree.currentItem()
             if item :
 
                id_target = item.text(0)                
                for _target in self.manager.targets():                   
                    _treeItem = _target.treeWidgetItem                     
                    if _treeItem and _target.id == int(id_target):
                       _treeItem.parent().removeChild(_treeItem) 
                       self.message.emit(("request to remove target %s")%(id_target)) 
                       
                       _target.clear(self.axes);
                       self.manager.removeTarget(id_target)
                       self.emitRemoveTarget.emit(id_target)
                       self.run()
                       return
            
        def trajectoryTarget(self):
            item = self.tree.currentItem()
            if item :
                id_target = item.text(0) 
                self.message.emit(("request to build trajectory of target %s")%(id_target)) 
                self.emitTrajectory.emit(id_target)
            
        def editTarget(self):
            item = self.tree.currentItem()
            if item :
                id_target = item.text(0) 
                self.message.emit(("request to edit trajectory of target %s")%(id_target)) 
                self.emitEditTarget.emit(id_target)
                    
                        
        def searchTarget(self, target):
            
            for _target in self.manager.targets():
       
                if _target.id == target.id and _target.treeWidgetItem != None :
                    return True
            return False
        
        def searchSensor(self,idSensor):
 
            for _sensor in self.manager.sensors():
              
                if str(_sensor.id)== str(idSensor) and _sensor.treeWidgetItem != None :
                    return True
            return False
        
        def receiveTrackers(self,trackers):
            for _tracker in trackers:
                listitemsNode = self.tree.findItems(_tracker.id_node, Qt.MatchExactly | Qt.MatchRecursive, 0)
                
                _itm = None
        
                for item in listitemsNode :
                    if item.parent().text(0) == "Nodes":
                        _itm = item
                        break
    
                _itmTracker = None
                
                for x in range(0,_itm.childCount()):
                     if _itm.child(x).text(0) ==    "Tracker":
                         _itmTracker = _itm.child(x)
                         break;

                if _itmTracker == None :

                        _itmTracker  = QTreeWidgetItem(_itm,['id','name','type'])
                        _itmTracker.setText(0, "Tracker")
                        s_itm =  QTreeWidgetItem(_itmTracker ,[str(_tracker.id),str(_tracker.name),str(_tracker.filter.name)])
                        s_itm.setCheckState(0, Qt.Checked)
                        s_itm.setFlags(s_itm.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
                        _tracker.treeWidgetItem = s_itm

              
        def receiveSensors(self): 
         
            #Dprint('receive sensor in GIS')
            for _sensor in self.manager.sensors():
                
                listitemsNode = self.tree.findItems(_sensor.id_node, Qt.MatchExactly | Qt.MatchRecursive, 0)
                
                _itm = None
        
                for item in listitemsNode :
                    if item.parent().text(0) == "Nodes":
                        _itm = item
                        break
         
                
                _itmSensor = None
                if _itm==None:
                    print('error sensor without node')
                    return
                for x in range(0,_itm.childCount()):
                         if _itm.child(x).text(0) ==    "Sensors":
                             _itmSensor = _itm.child(x)
                             break;
 
                if _itmSensor == None :
     
                        _itmSensor  = QTreeWidgetItem()
                        
                 
                        _itmSensor.setText(1,'name')
                        _itmSensor.setText(2,'type')
                        #_itm,['id','name','type'])
                        _itm.addChild(_itmSensor)   
                        _itmSensor.setText(0, "Sensors")
                        _itm.setFlags(_itm.flags()| Qt.ItemIsTristate| Qt.ItemIsUserCheckable)
                       # _itmSensor.setFlags(_itmSensor.flags() | Qt.ItemIsTristate| Qt.ItemIsUserCheckable )
                         
                if self.searchSensor(_sensor.id)==False:
                            s_itm =  QTreeWidgetItem()
                            _itmSensor.addChild(s_itm) 
                            s_itm.setText(1,str(_sensor.name))
                            s_itm.setText(2,str(_sensor.mode.name))
                            s_itm.setText(0,str(_sensor.id))
                            #_itmSensor ,[str(_sensor.id),str(_sensor.name),str(_sensor.mode.name)])

                            
                            s_itm.setFlags(s_itm.flags()| Qt.ItemIsUserCheckable)
                            _sensor.setTreeWidget(s_itm)
                            s_itm.setCheckState(0, Qt.Checked)
                            _sensor.update()
                            
        
            self.mode = GISMode.updateSensor
            self.run()
            
  
        def receiveTarget(self, _target ):
           
            #self.tree.setUpdatesEnabled(False);
 
            listitems = self.tree.findItems('Targets', Qt.MatchExactly | Qt.MatchRecursive, 0)
            #print(['listitems:',len(listitems)])
            if len(listitems) == 0:
                 itemTargets  = QTreeWidgetItem(self.tree,['id','name','type'])
                 itemTargets.setText(0, 'Targets')
            else:
                itemTargets = listitems[0]
              
            
              
            if self.searchTarget(_target)==False:
      
             
                _itm =  QTreeWidgetItem(itemTargets,[str(_target.id),str(_target.name),str(_target.type.name)])
                _itm.setCheckState(0, Qt.Checked)
                _itm.setFlags(_itm.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)   
                _itm.setForeground(0,QBrush(_target.color))
                _itm.setForeground(1,QBrush(_target.color))
                _itm.setForeground(2,QBrush(_target.color))
                _target.setTreeWidget(_itm)
                 
            #self.tree.setUpdatesEnabled(True);
            self.mode = GISMode.updateTarget
          
            self.run()
        def getOneRoad(self,P,indexContainers):
            
            listCandidats=[]
            directions = []
            for r in range(0,len(self.road.containers)):
                shape = self.road.containers[r].shape
                x_deb = shape[0,0]
                y_deb = shape[0,1]
                x_fin = shape[-1,0]
                y_fin = shape[-1,1]
#                print('---->')
#                print([x_deb,' ',y_deb])
#                print([P.latitude,' ',P.longitude])
#                print(x_deb-P.longitude)
#                print(y_deb-P.latitude)
                if  np.abs(x_deb-P.longitude)<0.00001  and np.abs( y_deb-P.latitude)<0.00001 and r not in indexContainers:
                    listCandidats.append(r)
                    directions.append(True)
                if  np.abs(x_fin-P.longitude)<0.00001  and  np.abs(y_fin-P.latitude)<0.00001 and r not in indexContainers:
                    listCandidats.append(r)
                    directions.append(False)
            Mmax = -1;
            WinnerCont = None
            WinnerFlag = False
            WinnerVelocity = -1
            for _candidat,flag in zip(listCandidats,directions):
                tr          = self.road.containers[_candidat].traficability
                velocity    = self.road.containers[_candidat].velocity
                if tr >=Mmax:
                    Mmax                =     tr
                    WinnerCont          =     _candidat 
                    WinnerFlag          =     flag
                    WinnerVelocity      =     velocity
            if WinnerCont:
                return self.road.containers[WinnerCont], WinnerCont,WinnerFlag, WinnerVelocity
            
            return None,-1,True,-1
        def elevation(self,latitude,longitude):
            for dted in self.dtedList:
                elevation = dted.height( longitude, latitude)
                if elevation !=-1:
                    return elevation
            return 0
        
        def receiveGauss(self,_tracker =None):
            print('receiveGauss in GIS')
            if _tracker and _tracker.mutex.tryLock() :
            
                if self.GaussianWidget==None:
                    
                    self.GaussianWidget  = GraphWidget2()
                if self.GaussianWidget.sensorAreaDisplay == False:
                    self.GaussianWidget.displayInitialareas(_tracker.tracker.polygons)
                    
                self.GaussianWidget.displayGaussians(_tracker.tracker.getGauss())
         
                _tracker.mutex.unlock()  
            
        def receiveTracks(self, tracks = None):
            
            _tracker = None
            
            if tracks == None:
                return
            
            for _node in  self.manager.nodes():
                if _node.id == tracks[0].id_node:
                   _tracker = _node.tracker 
                    
            if _tracker and _tracker.mutex.tryLock() :
            
                for _track in tracks:
                    _track.displayTrack(self.axes,self.canvas,_tracker.displayTrackFig,_tracker.displayCovariancekFig,_tracker.displayIconeFig)
                _tracker.mutex.unlock()    
        def receiveScan(self, scan = None):

            #scan.sensor.clear()
            #print('in GIS receive Scan')
            scan.sensor.displayScan(self.axes,self.canvas)
           # self.canvas.blit(self.axes.bbox)
            self.canvas.draw_idle()
            #self.canvas.flush_events()
            #self.canvas.draw()
            
        def isDetectable(self,line= QLineF(),hauteurObjet = 0):
            if self.building == []:
                return True
            flag, point= self.building.accrosAShape(line,hauteurObjet)
            #self.axes.plot([line.x1(),line.x2()],[line.y1(),line.y2()] ,color='green')
            if flag :
                #self.axes.plot(point.x(),point.y(), marker='o',color='red') 
                return False
            return True
        def searchNode(self,idNode):
            
            for _i in range(0,self.itemNodes.childCount()) :
                if self.itemNodes.child(_i).text(0) == str(idNode):
                    return True
                
            return False
        def receiveNodes(self):
           
            #print('in receiveNodes')
            #self.tree.setUpdatesEnabled(False);
            listitems = self.tree.findItems('Nodes', Qt.MatchExactly | Qt.MatchRecursive, 0)
            #♂print(['listitems:',len(listitems)])
            if len(listitems) == 0:
                self.itemNodes  = QTreeWidgetItem(self.tree,['id','name','type'])
                self.itemNodes.setText(0, 'Nodes')
             
            for _node in self.manager.nodes():
         
                   if self.searchNode(_node.id) == False:
        
                       #_itm =  QTreeWidgetItem(self.itemNodes ,[str(_node.id),str(_node.name),str(_node.typeNode)])
                       _itm =  QTreeWidgetItem()
                       
                       _itm.setText(0,str(_node.id))
                       _itm.setText(1,str(_node.name))
                       _itm.setText(2,str(_node.typeNode))
                       _itm.setCheckState(0, Qt.Checked)
                       _itm.setFlags(_itm.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
                       
                       _node.setTreeWidget( _itm)
                       _node.setGis(self)
                       self.itemNodes.addChild(_itm)
   
                       self.receiveSensors()
 
             
            
            self.mode = GISMode.updateNode
            self.run()
               
