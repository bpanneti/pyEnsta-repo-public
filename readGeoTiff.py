from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
"""
Created on Mon Aug 29 09:06:45 2016

@author: t0174034
"""
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import matplotlib.image as img
import matplotlib.mlab as ml
from osgeo import osr, gdal,ogr
from enum import Enum
#import cv2
import numpy as np

class TYPE_CARTO(Enum):
        DTED             = 0
        CARTO            = 1
 
class cartographie(QWidget):
    def __init__(self):
 
        super(cartographie, self).__init__()
        #print('init GIS')
 
        self.nom = 'data/carto/dnb_land_ocean_ice.2012.3600x1800_geo.tif'
        self.read(self.nom ,TYPE_CARTO.CARTO )
        '''
        #self.nom = 'land_shallow_topo_2048.tif'
        dem = gdal.Open(self.nom,gdal.GA_ReadOnly)
        band = dem.GetRasterBand(1)
        self.data = band.ReadAsArray()
        self.type =  TYPE_CARTO.DTED 
        
        nrows, ncols = self.data.shape

        #import matplotlib.pyplot as plt
        x0, dx, dxdy, y0, dydx, dy = dem.GetGeoTransform()

        x1 = x0 + dx * ncols
        y1 = y0 + dy * nrows
        self.ncols = ncols
        self.nrows = nrows
        self.x1 = x1
        self.x0 = x0
        self.y1 = y1
        self.y0 = y0
        
        self.read(self.nom ,self.type)
        '''
 
    def map2pixel(self,mx,my):
        #print('lol')

        px = int((mx - self.x0) /(self.x1 - self.x0) *(self.ncols )) #x pixel
        py = int((my - self.y0) /(self.y1 - self.y0) * (self.nrows )) #y pixel
        #print(['lol :',str(px), str(py)])
        return px,py    
    def height(self,mx,my):
        #print('in heig', str(mx),' : ', str(my))
        x, y = self.map2pixel(mx,my)
 
        if x < 0 or y < 0 or y > self.nrows  or x > self.ncols:
            return -1
        
        val  = self.data[y][x]
 
        return val
    
    def read(self,nom,_type):
        
        #print('in read')
        self.nom = nom
 
        
        self.type = _type
        dem = gdal.Open(self.nom)
        #print(self.nom)
        old_cs= osr.SpatialReference()
 
        if dem.GetProjectionRef() :
            old_cs.ImportFromWkt(dem.GetProjectionRef())
        else:
 
            old_cs.ImportFromEPSG(2154)
            
        
        #print(old_cs.GetAttrValue('AUTHORITY',1))
        new_cs = osr.SpatialReference()
        new_cs.ImportFromEPSG(4326)
        # create a transform object to convert between coordinate systems
        transform = osr.CoordinateTransformation(old_cs,new_cs)
        band1 = dem.GetRasterBand(1) # Red channel
        self.data_1 = band1.ReadAsArray()
        nrows, ncols = self.data_1.shape
 
        if dem.RasterCount==3 :
            
             band2 = dem.GetRasterBand(2) # Green channel
             band3 = dem.GetRasterBand(3) # Blue channel
             self.data_2 = band2.ReadAsArray()
             self.data_3 = band3.ReadAsArray()
             
        x0, dx, dxdy, y0, dydx, dy = dem.GetGeoTransform()
        #print(y0, dy, dydx, x0, dxdy, dx)
        x1 = x0 + dx * ncols
        y1 = y0 + dy * nrows
        #print(x1,y1)
        lat0long0 = transform.TransformPoint(x0,y0) 
        lat1long1 = transform.TransformPoint(x1,y1) 
        self.ncols = ncols
        self.nrows  = nrows
        self.x1 = lat1long1[0]
        self.x0 = lat0long0[0]
        self.y1 = lat1long1[1]
        self.y0 = lat0long0[1]
        '''    
        else:
            x0, dx, dxdy, y0, dydx, dy = dem.GetGeoTransform()
            x1 = x0 + dx * (1 + ncols)
            y1 = y0 + dy * (   nrows)
            
            lat0long0 = transform.TransformPoint(x0,y0) 
            lat1long1 = transform.TransformPoint(x1,y1) 
 
        #print([x0, y0])
            self.ncols = ncols
            self.nrows  = nrows
            self.x1 = lat1long1[0]
            self.x0 = lat0long0[0]
            self.y1 = lat1long1[1]
            self.y0 = lat0long0[1]
        '''
        #print(self.x0)
        #print(self.x1)
        #print(self.y0)
        #print(self.y1)
    def set_visible(self,_bool):
        #print('set carto visible',_bool)
        self.layer.set_visible(_bool)
    def display(self,axes):

        if self.type == TYPE_CARTO.CARTO:
            # img = cv2.imread(self.nom)
            # cv2.imshow('test',img)
            
            if hasattr(self,'data_2') and len(self.data_1)==len(self.data_2):
 
                geotiff_shifted = np.dstack((self.data_1, self.data_2, self.data_3))
                self.layer = axes.imshow(geotiff_shifted, extent=[self.x0, self.x1, self.y1, self.y0])  

            else:
                dem = img.imread(self.nom) 
                self.layer = axes.imshow(dem, extent=[self.y0, self.y1, self.x1, self.x0])  

            #geotiff_shifted = np.rollaxis(self.data_1,0,3)
                        #self.layer = axes.imshow( (geotiff_shifted/np.amax(geotiff_shifted) * 255).astype(np.uint8) , extent=[self.x0, self.x1, self.y1, self.y0])#,cmap='gist_earth', extent=[self.x0, self.x1, self.y1, self.y0]) 
            #self.layer = axes.imshow(self.data_1,cmap='gist_earth', interpolation='nearest', extent=[self.x0, self.x1, self.y1, self.y0]) 
     
        
        else:
            dem = img.imread(self.nom) 
            self.layer = axes.imshow(dem, extent=[self.x0, self.x1, self.y1, self.y0])  

            #self.layer = axes.imshow(self.data_1,cmap='gist_earth', interpolation='nearest', extent=[self.x0, self.x1, self.y1, self.y0]) 
   
       # axes.set_aspect('equal', 'datalim')
'''      
def main(argv=None):
     file='data/sample.tif'
      
     #file = 'data/carto/dnb_land_ocean_ice.2012.3600x1800_geo.tif'
     print(file)
     lat = 1.70
     long = 47.34
   
     a = cartographie()
     a.read(file)
 
     [px,py]= a.map2pixel(lat,long)
     print(px,py)
     print(a.height(lat,long))
     print("done")
     fig, ax = plt.subplots()
     a.displayMap(ax)
     plt.plot(lat,long,'ro')
   
if __name__ == "__main__":
    main() 
'''
