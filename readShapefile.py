# -*- coding: utf-8 -*-
"""
Created on Mon Aug 29 09:05:02 2016

@author: t0174034
"""

import gdal
import matplotlib.pyplot as plt
import numpy as np
import shapefile as shp

 
from matplotlib.patches import Polygon
from matplotlib import colors 
import matplotlib.cm as cmx 
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtOpenGL import *
from PyQt5.QtWidgets import QWidget, QMessageBox, QApplication,QProgressBar, QLineEdit,QGridLayout 
import sys 
from osgeo import osr, ogr,  gdal


from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)


color_norm  = colors.Normalize(vmin=5100, vmax=5200)
scalar_map = cmx.ScalarMappable(norm=color_norm, cmap='hsv') 
    

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

from collections import namedtuple
MyStruct = namedtuple('MyStruct', 'type code trafic velocity_max')
typeRoad = []
typeRoad.append(MyStruct('unknown',     5199,-1,-1))
typeRoad.append(MyStruct('bridleway',   5151,1,-1))
typeRoad.append(MyStruct('cycleway',    5152,2,8))
typeRoad.append(MyStruct('Piste cyclable',5152,0,8))
typeRoad.append(MyStruct('footway',     5153,0,1))
typeRoad.append(MyStruct('Sentier',     5153,0,1))
typeRoad.append( MyStruct('path',       5154,2,-1))
typeRoad.append(MyStruct('steps',       5155,1,-1))
typeRoad.append(MyStruct('Chemin'       ,5155,1,8))
typeRoad.append(MyStruct('service',     5141,1,-1))
typeRoad.append(MyStruct('track',5142,1,-1))
typeRoad.append(MyStruct('track_grade1',5143,1,-1))
typeRoad.append(MyStruct('Route à 1 chaussée',5143,2,50))
typeRoad.append(MyStruct('track_grade2',5144,1,90))
typeRoad.append(MyStruct('Route à 2 chaussées',5144,3,90))
typeRoad.append(MyStruct('track_grade3',5145,1,110))
typeRoad.append(MyStruct('track_grade4',5146,1,130))
typeRoad.append(MyStruct('Autoroute',5146,4,130))
typeRoad.append(MyStruct('Quasi-autoroute',5146,4,130))
typeRoad.append(MyStruct('track_grade5',5147,1,130))
typeRoad.append(MyStruct('motorway_link',5131,4,-1)  )
typeRoad.append(MyStruct('trunk_link',5132,3,-1)   )
typeRoad.append(MyStruct('primary_link',5133,3,-1)  ) 
typeRoad.append(MyStruct('secondary_link',5134,3,-1)  ) 
typeRoad.append(MyStruct('unclassified',5121,-1,-1)  )
typeRoad.append(MyStruct('residential',5122,1,-1) )
typeRoad.append(MyStruct('living_street',5123,1,-1) )
typeRoad.append(MyStruct('pedestrian',5124,1,-1)) 
typeRoad.append(MyStruct('motorway',5111,5,-1) )
typeRoad.append(MyStruct('trunk',5112,4,-1) )
typeRoad.append(MyStruct('primary',5113,3,-1)  )
typeRoad.append(MyStruct('secondary',5114,2,-1) )
typeRoad.append(MyStruct('tertiary',5115,1,-1)  )
typeRoad.append(MyStruct('river',8101,2,-1) )
typeRoad.append(MyStruct('stream',8102,1,-1)  )
typeRoad.append(MyStruct('canal',8103,1,-1) )
typeRoad.append(MyStruct('drain',8104,1,-1)  )
typeRoad.append(MyStruct('dock',8100,2,-1) )
typeRoad.append(MyStruct('ditch',8100,1,-1)  )
typeRoad.append(MyStruct('pond',8100,1,-1) )
typeRoad.append(MyStruct('weir',8100,1,-1)  )
typeRoad.append(MyStruct('brook',8100,1,-1)  )

  


class layerVegetation :
    def __init__(self):
        self.code    = -1
        self.fclass = ''
        self.maxSpeed = -1
        self.shape = np.zeros((1,2))
        self.layer =''
        self.traficability = -1 
        self.layerObj =[]
        self.color = 'white'
        self.sxmin = 0.0
        self.symin = 0.0 
        self.sxmax = 0.0  
        self.symax = 0.0 
        self.hauteur = 0.0
        self.parts = []
        #for layer vegetation traficability is possible True or not False
        #traficabikity == True color = white
        #Traficability = false color = green
    def update(self,layer):
        self.layer = layer
        '''
        if self.code >=7201 and self.code < 7220:
            self.layer ='vegetation'
            self.traficability = True
        elif self.code == 1500:
            self.layer  ='building'
            self.fclass = 'unknown'
            self.traficability = False
            return
        elif self.code >=8200 and self.code < 8221:
            self.layer  ='waterArea'
            self.fclass = 'unknown'
            self.traficability = False
         
        if self.code == 7201:
            self.fclass = 'forest'
            self.traficability = False 
        elif self.code == 7202:
            self.fclass =  'park'
            self.traficability = False  
        elif self.code == 7206:
            self.fclass =  'cemetery'
            self.traficability = False   
        elif self.code == 7208:
            self.fclass =  'meadow'
            self.traficability = False     
        elif self.code == 7210:
            self.fclass =  'nature_reserve'
            self.traficability = False  
        elif self.code == 7217:
            self.fclass =  'scrub'
            self.traficability = False
        elif self.code == 7218:
            self.fclass =  'grass'
            self.traficability = False
        elif self.code == 8200:
            self.fclass =  'water'
            self.traficability = False 
        elif self.code == 8201:
            self.fclass =  'reservoir'
            self.traficability = False  
        elif self.code == 8202:
            self.fclass =  'river'
            self.traficability = False     
        elif self.code == 8211:
            self.fclass =  'glacier'
            self.traficability = False  
        elif self.code == 8221:
            self.fclass =  'wetland'
            self.traficability = False 
        else:       
            self.fclass =  'unknown'
            self.traficability = True 
        '''
 
        if  self.layer =='vegetation':
            self.traficability == False             
            self.color = 'green'
 
        elif self.layer =='building':
            self.traficability == False
            self.color = 'gray'        
        elif self.layer =='waterArea':    
            self.color = 'blue'
            self.traficability == False
          
class layerRoad :
    #road type for openstreetmap
   
    def __init__(self):
         self.code    = -1
         self.fclass = ''
         self.name = ''
         self.maxSpeed = -1
         self.shape = np.zeros((1,2))
         self.layer =''
         self.traficability = -1
         self.velocity      = -1
         self.layerObj =[]
         self.color = 'white'
         self.bridge = 0
         self.tunnel = 0
         self.linestyle   = '-'
         self.sxmin = 0.0
         self.symin = 0.0 
         self.sxmax = 0.0  
    def set_visible(self,_bool): 
 
        if self.layerObj !=[]:
            self.layerObj.set_visible(_bool)
    def update(self,type):
        
        
        self.layer =type
        flagTrouve=False
     
        for lst in typeRoad:
            if self.fclass == lst[0]:
             flagTrouve=True
             self.code = lst[1]
             self.traficability = lst[2]
             self.velocity      = lst[3]
             self.color  = scalar_map.to_rgba(self.code)
             break



        if flagTrouve==False:
            self.code = typeRoad[0][1]
            self.traficability = typeRoad[0][2]
            self.traficability = typeRoad[0][3]
            self.color  = scalar_map.to_rgba(self.code) 
            
        if self.tunnel==1:
           self.linestyle   = '-.'
        if self.bridge==1:
           self.linestyle   = '--'
       
 
        if self.layer =='water':
            self.color  = 'blue'
            self.linestyle   = '-'   
  
    
    

class shapefile:
    
    def findColumn(self,name):
            column = -1
            fields = self.shp.fields
         
            for fieldno in range(len(fields)):
                
           
                if fields[fieldno][0]==name:
                    column  =  fieldno-1
                    break
            return column 
 
    
    def __init__(self,file='',layer=''):
 
        self.file = file
        self.containers = [];
        self.fields =''
        self.layer = layer
        self.containerType =[]
        
    def __del__(self):
        for i in range(len(self.containers)):
            for u in self.containers[i].layerObj:
                u.remove()
                del u
    
    def ChangeColor(self,name):
        for i in range(len(self.containers)):
            if self.containers[i].fclass == name :
                color =  self.containers[i].color
                break
        
        color = QColorDialog.getColor()
       
        for i in range(len(self.containers)):
            if self.containers[i].fclass == name :
                self.containers[i].color = color
                for p in self.containers[i].layerObj:
                    p.set_color(color.name())
                
    def update(self): 
 
     
        
        self.shp = shp.Reader(self.file,encoding='ISO-8859-1')#'utf-8')
        self.fields = self.shp.fields           
        recs        =   self.shp.records()


        driver = ogr.GetDriverByName('ESRI Shapefile')
        dataset = driver.Open(self.file)

        # from Layer
        layer = dataset.GetLayer()
        spatialRef = layer.GetSpatialRef()
        
        #Transformation
        
        epsg2154 = osr.SpatialReference()
        epsg2154.ImportFromEPSG(2154) 
        epsg4326 = osr.SpatialReference()
        epsg4326.ImportFromEPSG(4326)
        coordTransform = osr.CoordinateTransformation( epsg4326, epsg4326)
        #print(spatialRef.GetAttrValue("PROJECTION"))
        #print(epsg2154.GetAttrValue("PROJECTION"))
        #if spatialRef.GetAttrValue("PROJECTION") == epsg2154.GetAttrValue("PROJECTION"):        
        coordTransform = osr.CoordinateTransformation( epsg2154, epsg4326)

        NAME        =   self.findColumn('name') 
        if NAME==-1:
            NAME        =   self.findColumn('NAME') 
         
        MAxSpeed    =   self.findColumn('maxspeed')
        LAYER       =   self.findColumn('layer') 
        if LAYER==-1:
            LAYER        =   self.findColumn('LAYER') 
    
        REF         =   self.findColumn('ref') 
        FCLASS      =   self.findColumn('fclass') 
    
        if FCLASS==-1:
            FCLASS  =   self.findColumn('NATURE') 
        
        HAUTEUR     =   self.findColumn('HAUTEUR') 
        CODE        =   self.findColumn('code')     
        TypeZ       =   self.findColumn('type')
        BRIDGE      =   self.findColumn('bridge')     
        TUNNEL      =   self.findColumn('tunnel')
        
 
        
        shapes = self.shp.shapes()

        bar = ProgressBar(total=len(shapes))
        bar.show()
    
        for shapeno in range(len(shapes)):
            
            bar.update_progressbar(shapeno)            
            
            if self.layer=='road':
                container   = layerRoad()
            elif self.layer == 'vegetation':
                container   = layerVegetation() 
            elif self.layer == 'building':
                container   = layerVegetation()
            elif self.layer == 'water':
                container   = layerRoad() 
            elif self.layer == 'waterArea':
                container   = layerVegetation() 
         
         
            fclass = -1
            code = -1
            shapename   = recs[shapeno][NAME]
            maxspeed    = recs[shapeno][MAxSpeed]
            layer       = recs[shapeno][LAYER]
            ref         = recs[shapeno][REF]
            bridge      = recs[shapeno][BRIDGE]
            tunnel      = recs[shapeno][TUNNEL] 
            hauteur     = recs[shapeno][HAUTEUR]
        
            if FCLASS != -1:
                b = recs[shapeno][FCLASS]
                fclass = b
                if type(b)==bytes:
                    fclass      = b.decode("ISO-8859-1")
                  
                
                
            else :
                fclass      = recs[shapeno][TypeZ]
                
            if CODE != -1:
                code        = recs[shapeno][CODE] 

            container.code      = code
            container.fclass    = fclass
            if hauteur:
                container.hauteur    = hauteur
                if type(hauteur)==bytes and hauteur>bytes([255]):
                    container.hauteur    = 0
                elif type(hauteur)==int and hauteur>255:#bytes([255]):
                    container.hauteur    = 0
            container.maxSpeed  = maxspeed
            container.name      = shapename
            container.parts     = shapes[shapeno].parts #pour les polygones
     
            for i in range(len(shapes[shapeno].points)):
                point = ogr.Geometry(ogr.wkbPoint)
                point.AddPoint( shapes[shapeno].points[i][0] ,  shapes[shapeno].points[i][1])
                point.Transform(coordTransform)
                try: 
                    point.SwapXY() #The gdal3 has inverted X and Y coordinate
                except:
                    print('bad version GDAL')
                container.shape = np.vstack((container.shape,[point.GetX(),point.GetY()]))
                
       
            container.shape = container.shape[1:i+2,:]
            
        
            a = container.shape.min(axis=0)
            container.sxmin = a[0]
            container.symin = a[1]
            a = container.shape.max(axis=0)
            container.sxmax = a[0]
            container.symax = a[1]
         
            container.area      =  abs(container.sxmax - container.sxmin) * abs(container.symax - container.symin)
 
            container.tunnel = tunnel
            container.bridge = bridge
            container.update(self.layer)
         
            
            if container.fclass not in self.containerType:
                self.containerType.append(container.fclass) 

                
            self.containers.append(container)
             
        bar.close()
 
    def accrosAShape(self,_line=QLineF(),hauteur = 0):
        #return vraie si la ligne délimitée par deux points intersecte un segment
        linrd = []
        for i in range(len(self.containers)):
           # if not(self.containers[i].layerObj):
                    shape = self.containers[i].shape
                    x = shape[:,0]
                    y = shape[:,1]
                    hauteurLine = self.containers[i].hauteur
                    for u in range(len(x)-1):
                        line = QLineF(QPointF(x[u],y[u]) , QPointF(x[u+1],y[u+1]))
                        P = QPointF()
                        if _line.intersect(line,P) == QLineF.BoundedIntersection: 
                            #print (hauteurLine)
                            if hauteur <= hauteurLine:
                                return True,P
        return False,None 
                            
    
    def isInShape(self,point):
        #point [x,y] 
        for i in range(len(self.containers)):
                if not(self.containers[i].layerObj):
                    shape = self.containers[i].shape
                    x = [i[0] for i in shape.points[:]]
                    y = [i[1] for i in shape.points[:]]
                    vec =[]
                    for u in len(x):
                        vec.append(QPointF(x[u],y[u]))
                    poly = QPolygonF(vec)
                    
                    if poly.containsPoint(QPointF(point[0],point[1]), Qt.OddEvenFill):
                        return True, self.containers[i]
        return False, None
                    
    def display(self,axes = None,bbox=[],canvas=[]):


        xmin = -180
        xmax = 180
        ymin = -90 
        ymax = 90
         
        if bbox:
           xmin = bbox[0]
           xmax = bbox[1]
           ymin = bbox[2]
           ymax = bbox[3]
        
   
        if axes is None:
            fig             = plt.figure()
            axes            = fig.add_subplot(111)
            canvas          = FigureCanvas(fig)
        
            background = []
        else:
            background =  canvas.copy_from_bbox(axes.bbox) 
   
            
        if self.layer =="road":
            for i in range(len(self.containers)):
                if not(self.containers[i].layerObj):
                    shape = self.containers[i].shape
                
                    sxmin, symin, sxmax, symax = self.containers[i].sxmin,self.containers[i].symin,self.containers[i].sxmax,self.containers[i].symax
               
                    if sxmin <  xmin: continue
                    elif sxmax > xmax: continue
                    elif symin < ymin: continue
                    elif symax > ymax: continue                
                    x = shape[:,0]
                    y = shape[:,1]
  
                    size =  self.containers[i].traficability               
                    if size == -1:
                        size = 1
              
                    self.containers[i].layerObj, = axes.plot(x,y,color = self.containers[i].color , linewidth=  size+1,linestyle=self.containers[i].linestyle)
                    #axes.draw_artist(self.containers[i].layerObj[0] )
                    
            #canvas.blit(axes.bbox)
            canvas.update()
            canvas.flush_events()
                        
        elif self.layer =="water":
            for i in range(len(self.containers)):
                if not(self.containers[i].layerObj):
                    shape = self.containers[i].shape
                    sxmin, symin, sxmax, symax = self.containers[i].sxmin,self.containers[i].symin,self.containers[i].sxmax,self.containers[i].symax
                    if sxmin <  xmin: continue
                    elif sxmax > xmax: continue
                    elif symin < ymin: continue
                    elif symax > ymax: continue                
                    x = [i[0] for i in shape.points[:]]
                    y = [i[1] for i in shape.points[:]]
                    size =  self.containers[i].traficability               
                    if size == -1:
                        size = 1
                    self.containers[i].layerObj, = axes.plot(x,y,color = self.containers[i].color , linewidth=  size+1,linestyle=self.containers[i].linestyle)
                    axes.draw_artist(self.containers[i].layerObj )
                        
            canvas.blit(axes.bbox)
            canvas.update()
            canvas.flush_events()
                
        elif self.layer =="building" or self.layer =="vegetation":
        #draw shape
 
            for i in range(len(self.containers)):
                if not self.containers[i].layerObj:
                    shape = self.containers[i].shape
                    ptchs   = []
                    #pts     = np.array(shape.points)
                    #prt     = shape.parts
                    #par     = list(prt) + [pts.shape[0]]
 
                    sxmin, symin, sxmax, symax = self.containers[i].sxmin,self.containers[i].symin,self.containers[i].sxmax,self.containers[i].symax
                    if sxmin <  xmin: continue
                    elif sxmax > xmax: continue
                    elif symin < ymin: continue
                    elif symax > ymax: continue                
                    
                    x = shape[:,0]
                    y = shape[:,1]
                    lim = [self.containers[i].parts, len(shape)-1]
                    
                    for pij in range(len(lim)-1):
                        if pij == 0 :
                            ptchs=Polygon(shape[0:lim[pij+1],:],facecolor=self.containers[i].color,linewidth=1);#Polygon(pts[par[pij]:par[pij+1]],facecolor='white',linewidth=0);
                        else:
                            ptchs=Polygon(shape[lim[pij]:lim[pij+1],:],facecolor=self.containers[i].color,linewidth=1);#Polygon(pts[par[pij]:par[pij+1]],facecolor=self.containers[i].color,linewidth=1);
  
                        self.containers[i].layerObj.append(axes.add_patch(ptchs))
                    #canvas.blit(axes.bbox)
                    canvas.update()
                    canvas.flush_events()
#                    
#        elif self.layer =="vegetation":
#            for i in range(len(self.containers)):
#                if not self.containers[i]:
#                    shape = self.containers[i].shape
#                    ptchs   = []
#                    pts     = np.array(shape.points)
#                    prt     = shape.parts
#                    par     = list(prt) + [pts.shape[0]]
#               
#                
#                    sxmin, symin, sxmax, symax = shape.bbox
#                    if sxmin <  xmin: continue
#                    elif sxmax > xmax: continue
#                    elif symin < ymin: continue
#                    elif symax > ymax: continue
#            
#                
#                    for pij in range(len(prt)):
#                        if pij >= 1 :
#                            ptchs=Polygon(pts[par[pij]:par[pij+1]],facecolor='white',linewidth=0);
#                        else:
#                            ptchs=Polygon(pts[par[pij]:par[pij+1]],facecolor=self.containers[i].color,linewidth=1);                                
#                        self.containers[i].layerObj.append(axes.add_patch(ptchs))
#                    
#                    canvas.blit(axes.bbox)
#                    canvas.update()
#                    canvas.flush_events()
                    
        if self.layer =="waterArea":
        #draw shape
       
        
            for i in range(len(self.containers)):
                 if not self.containers[i]:
                    shape = self.containers[i].shape
                    ptchs   = []
                    pts     = np.array(shape.points)
                    prt     = shape.parts
                    par     = list(prt) + [pts.shape[0]]
               
               
                    sxmin, symin, sxmax, symax = shape.bbox
                    if sxmin <  xmin: continue
                    elif sxmax > xmax: continue
                    elif symin < ymin: continue
                    elif symax > ymax: continue
            
                
                    for pij in range(len(prt)):
                        if pij >= 1 :
                            ptchs=Polygon(pts[par[pij]:par[pij+1]],facecolor='white',linewidth=0);
                        else:
                            ptchs=Polygon(pts[par[pij]:par[pij+1]],facecolor=self.containers[i].color,linewidth=1);
                        self.containers[i].layerObj.append(axes.add_patch(ptchs))
        
        

        
def main(argv=None):
    
    app = QApplication(sys.argv)
 
 

    #Map = shapefile("data/palaiseau/Route.shp","road")#data/dresden/gis.osm_roads_v06.shp","road")
   # Map.update()
    #Map.display()
    Map =shapefile("data/palaiseau/Batiment.shp","building")#"data/dresden/gis.osm_buildings_v06.shp","building")
    Map.update()
    Map.display()
    
    
    Map =shapefile("data/palaiseau/Vegetation.shp","vegetation")#"data/dresden/gis.osm_buildings_v06.shp","building")
    Map.update()
    Map.display()
    
    #Map =shapefile("gis.osm_water_v06.shp","waterArea")
    #Map.update()
    #Map.display()
    
    #Map =shapefile("gis.osm_waterways_v06.shp","waterWay")
    #Map.update()
   # Map.display()
    
   # Map =shapefile("gis.osm_natural_a_v06.shp","vegetation")
   # Map.update()
   # Map.display()
    
   # Map =shapefile("dresden/gis.osm_landuse_v06.shp","vegetation")
   # Map.update()
   # Map.display()
    plt.axis('equal')
    plt.title("Dresden") 
    plt.show() 
    
    sys.exit(app.exec_())
if __name__ == "__main__":
    main() 