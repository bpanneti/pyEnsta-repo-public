# -*- coding: utf-8 -*-
"""
Created on Mon Aug 29 09:06:12 2016

@author: t0174034
"""
from osgeo import osr, gdal
import numpy as np  
#from mpl_toolkits.basemap import Basemap
from numpy import linspace
from numpy import meshgrid
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import matplotlib.mlab as ml

class dted:
    def __init__(self):
        self.nom = []
        self.layer = []
        
    def map2pixel(self,mx,my):
        #print('lol')

        px = int((mx - self.gt[0]) / self.gt[1]) #x pixel
        py = int((my - self.gt[3]) / self.gt[5]) #y pixel
        #print(['lol :',str(px), str(py)])
        return px,py

    def read(self,nom):
        self.nom = nom
 
        dem = gdal.Open(self.nom)
        self.gt  = dem.GetGeoTransform()
        self.dem = dem.ReadAsArray()
  
   
        
        xres = self.gt[1]
        yres = self.gt[5]

        X = np.arange(self.gt[0], self.gt[0] + self.dem.shape[1]*xres, xres)
        Y = np.arange(self.gt[3], self.gt[3] + self.dem.shape[0]*yres, yres)
        
        X, Y = np.meshgrid(X, Y)
        
        self.X = X
        self.Y = Y
        
        x0, dx, dxdy, y0, dydx, dy = dem.GetGeoTransform()

        self.nrows, self.ncols = self.dem.shape
        
        x1 = x0 + dx * self.ncols
        y1 = y0 + dy * self.nrows
        
        self.x1 = x1
        self.x0 = x0
        self.y1 = y1
        self.y0 = y0
        self.dx = dx
        self.dy = dy
       
               
    def height(self,mx,my):
        #print('in heig', str(mx),' : ', str(my))
        x, y = self.map2pixel(mx,my)
 
        if x < 0 or y < 0 or x > self.nrows  or y > self.ncols:
            return -1
        
        val  = self.dem[y][x]
 
        return val
         
    def set_visible(self,_bool):
        
        self.layer.set_visible(_bool)
        
    def display(self,axes):
        A = self.dem
        A[A>255] = 255
        A[A<0] = 0
        
        self.layer = axes.imshow(self.dem, cmap='gist_earth', extent=[self.x0, self.x1, self.y1, self.y0])

def main(argv=None):
     print("file")
     file='D:\\bpanneti\\safir_ng\\tools\\SimulateurSextant\\data\\palaiseau\\ONERA_P_E2_N48.dt2'
     print(file)
     a = dted()
     a.read(file)
     print("done")
     fig, ax = plt.subplots()
     a.displayDTED(ax)
if __name__ == "__main__":
    main() 
       