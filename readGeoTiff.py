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
import cv2

class TYPE_CARTO(Enum):
        DTED             = 0
        CARTO            = 1
 
class cartographie(QWidget):
    def __init__(self):
 
        super(cartographie, self).__init__()
        self.nom = 'data/carto/dnb_land_ocean_ice.2012.3600x1800_geo.tif'
        dem = gdal.Open(self.nom)
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
        self.nom = nom
 
        
        self.type = _type
        dem = gdal.Open(self.nom)
        #print(self.nom)
        old_cs= osr.SpatialReference()
 
        if dem.GetProjectionRef() :
            old_cs.ImportFromWkt(dem.GetProjectionRef())
        else:
 
            old_cs.ImportFromEPSG(2154)
            
        
        
        new_cs = osr.SpatialReference()
        new_cs.ImportFromEPSG(4326)
        
        # create a transform object to convert between coordinate systems
        transform = osr.CoordinateTransformation(old_cs,new_cs)

        band = dem.GetRasterBand(1)
        
        self.data = band.ReadAsArray()

        nrows, ncols = self.data.shape

        #import matplotlib.pyplot as plt
        #print(dem)
        x0, dx, dxdy, y0, dydx, dy = dem.GetGeoTransform()

        x1 = x0 + dx * ncols
        y1 = y0 + dy * nrows
     

        lat0long0 = transform.TransformPoint(x0,y0) 
        lat1long1 = transform.TransformPoint(x1,y1) 
 
        #print([latlong0, latlong1])
        self.ncols = ncols
        self.nrows  = nrows
        self.x1 = lat1long1[0]
        self.x0 = lat0long0[0]
        self.y1 = lat1long1[1]
        self.y0 = lat0long0[1]
     
    def set_visible(self,_bool):
        #print('set carto visible',_bool)
        self.layer.set_visible(_bool)
    def display(self,axes):
        if self.type == TYPE_CARTO.CARTO:
            img = cv2.imread(self.nom)
            self.layer = axes.imshow(img,cmap='gist_earth', extent=[self.x0, self.x1, self.y1, self.y0]) 
        else:
    
            self.layer = axes.imshow(self.data,cmap='gist_earth', interpolation='nearest', extent=[self.x0, self.x1, self.y1, self.y0]) 
        
def main(argv=None):
     file='data/dted/selleSaintDenisLambert93.tif'
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