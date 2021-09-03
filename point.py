# -*- coding: utf-8 -*-
"""
Created on Wed Jul  3 09:48:51 2019

@author: bpanneti
"""

from osgeo import osr, ogr,  gdal
import numpy as np
import math

class RefPosition:
     def __init__(self):
              self.latitude     = []
              self.longitude    = []
              self.altitude     = []
              self.defined      = False
     def setWGS84(self, longitude= 0, latitude = 0, altitude =0):

            self.latitude     = latitude
            self.longitude    = longitude
            self.altitude     = altitude
            self.defined      = True
            

REFERENCE_POINT = RefPosition()
a = 6378137
b = 6356752.3142
f = (a - b) / a
e_sq = f * (2-f)

def ecef_to_geodedic(_x,_y,_z):
    longi   = math.atan(_y/_x);

 
    e2  = (a*a - b*b)/(a*a);
    ep2 = (a*a - b*b)/(b*b);
    
    p       = math.sqrt(_x*_x+_y*_y);
    teta    = math.atan(_z*a/(p*b));

    sinTeta =  math.sin(teta);
    cosTeta =  math.cos(teta);
    lati=  math.atan((_z+(ep2*b*sinTeta*sinTeta*sinTeta))/(p-(e2*a*cosTeta*cosTeta*cosTeta)));

    sinLat =  math.sin(lati);
    n =  a/ math.sqrt(1-(e2*sinLat*sinLat))
    alti = (p/ math.cos(lati)) - n;

    longi=longi*180/math.pi;
    lati=lati*180/ math.pi
    
    return lati,longi, alti
def geodetic_to_ecef(lat, lon, h):
    # (lat, lon) in WSG-84 degrees
    # h in meters
    lamb = math.radians(lat)
    phi = math.radians(lon)
    s = math.sin(lamb)
    N = a / math.sqrt(1 - e_sq * s * s)

    sin_lambda = math.sin(lamb)
    cos_lambda = math.cos(lamb)
    sin_phi = math.sin(phi)
    cos_phi = math.cos(phi)

    x = (h + N) * cos_lambda * cos_phi
    y = (h + N) * cos_lambda * sin_phi
    z = (h + (1 - e_sq) * N) * sin_lambda

    return x, y, z

def ecef_to_enu3DVector(x, y, z, lat0, lon0, h0):
    lamb = math.radians(lat0)
    phi = math.radians(lon0)
    s = math.sin(lamb)
    N = a / math.sqrt(1 - e_sq * s * s)

    sin_lambda = math.sin(lamb)
    cos_lambda = math.cos(lamb)
    sin_phi = math.sin(phi)
    cos_phi = math.cos(phi)

    x0 = (h0 + N) * cos_lambda * cos_phi
    y0 = (h0 + N) * cos_lambda * sin_phi
    z0 = (h0 + (1 - e_sq) * N) * sin_lambda

    F = np.zeros([3,3])
    T = np.zeros([3,1])
    Xd = np.zeros([3,1])
    Xd[0]   = x
    Xd[1]   = y
    Xd[2]   = z
#    xd = x - x0
#    yd = y - y0
#    zd = z - z0

    T[0] = x0
    T[1] = y0
    T[2] = z0
    
    F[0,0] = -  sin_phi 
    F[0,1] =    cos_phi 
    F[1,0] = - sin_lambda * cos_phi  
    F[1,1] = - sin_lambda * sin_phi 
    F[1,2] =   cos_lambda 
    F[2,0] =   cos_lambda *  cos_phi
    F[2,1] =   cos_lambda * sin_phi   
    F[2,2] =   sin_lambda
    
    X = F@ (Xd-T)
    
#    xEast = -sin_phi * xd + cos_phi * yd
#    yNorth = -cos_phi * sin_lambda * xd - sin_lambda * sin_phi * yd + cos_lambda * zd
#    zUp = cos_lambda * cos_phi * xd + cos_lambda * sin_phi * yd + sin_lambda * zd

    return X
def ecef_to_enuMatrix(_M,lat0, lon0, h0):
    lamb = math.radians(lat0)
    phi = math.radians(lon0)
    #s = math.sin(lamb)
   
    sin_lambda = math.sin(lamb)
    cos_lambda = math.cos(lamb)
    sin_phi = math.sin(phi)
    cos_phi = math.cos(phi)
 

    F = np.zeros([6,6])
 
 

 
    
    F[0,0] = -  sin_phi
    F[1,1] = -  sin_phi
    F[0,2] =    cos_phi
    F[1,3] =    cos_phi 

    F[2,0] = - sin_lambda * cos_phi 
    F[3,1] = - sin_lambda * cos_phi 
    F[2,2] = - sin_lambda * sin_phi 
    F[3,3] = - sin_lambda * sin_phi
    F[2,4] =   cos_lambda 
    F[3,5] =   cos_lambda 
    
 
    
    F[4,0] =   cos_lambda * cos_phi
    F[4,2] =   cos_lambda * sin_phi
    F[4,4] =   sin_lambda
    F[5,1] =   cos_lambda * cos_phi
    F[5,3] =   cos_lambda * sin_phi
    F[5,5] =   sin_lambda
    
    return  F@ _M @ F.transpose()

def enu_to_ecefMatrix(_P, lat0, lon0, h0):
    
 
    lamb = math.radians(lat0)
    phi = math.radians(lon0)
    #s = math.sin(lamb)
   
    sin_lambda = math.sin(lamb)
    cos_lambda = math.cos(lamb)
    sin_phi = math.sin(phi)
    cos_phi = math.cos(phi)
 

    F = np.zeros([6,6])
 
 

 
    
    F[0,0] = -  sin_phi
    F[1,1] = -  sin_phi
    F[0,2] =    cos_phi
    F[1,3] =    cos_phi 

    F[2,0] = - sin_lambda * cos_phi 
    F[3,1] = - sin_lambda * cos_phi 
    F[2,2] = - sin_lambda * sin_phi 
    F[3,3] = - sin_lambda * sin_phi
    F[2,4] =   cos_lambda 
    F[3,5] =   cos_lambda 
    
 
    
    F[4,0] =   cos_lambda * cos_phi
    F[4,2] =   cos_lambda * sin_phi
    F[4,4] =   sin_lambda
    F[5,1] =   cos_lambda * cos_phi
    F[5,3] =   cos_lambda * sin_phi
    F[5,5] =   sin_lambda
    
    return  F.transpose()@ _P @ F
    
 
   
def enu_to_ecef(x, y, z, lat0, lon0, h0):
    
 
    lamb = math.radians(lat0)
    phi = math.radians(lon0)
    s = math.sin(lamb)
    N = a / math.sqrt(1 - e_sq * s * s)

    sin_lambda = math.sin(lamb)
    cos_lambda = math.cos(lamb)
    sin_phi = math.sin(phi)
    cos_phi = math.cos(phi)

    x0 = (h0 + N) * cos_lambda * cos_phi
    y0 = (h0 + N) * cos_lambda * sin_phi
    z0 = (h0 + (1 - e_sq) * N) * sin_lambda

    F = np.zeros([3,3])
    T = np.zeros([3,1])
    X = np.zeros([3,1])
    X[0]   = x
    X[1]   = y
    X[2]   = z
#    xd = x - x0
#    yd = y - y0
#    zd = z - z0

    T[0] = x0
    T[1] = y0
    T[2] = z0
    
    F[0,0] = -  sin_phi 
    F[0,1] =    cos_phi 
    F[1,0] = - sin_lambda * cos_phi  
    F[1,1] = - sin_lambda * sin_phi 
    F[1,2] =   cos_lambda 
    F[2,0] =   cos_lambda *  cos_phi
    F[2,1] =   cos_lambda * sin_phi   
    F[2,2] =   sin_lambda
    
    Xd = F.transpose()@ X +T
    
#    xEast = -sin_phi * xd + cos_phi * yd
#    yNorth = -cos_phi * sin_lambda * xd - sin_lambda * sin_phi * yd + cos_lambda * zd
#    zUp = cos_lambda * cos_phi * xd + cos_lambda * sin_phi * yd + sin_lambda * zd
 
    return float(Xd[0]),float(Xd[1]),float(Xd[2])
def ecef_to_enu(x, y, z, lat0, lon0, h0):
    lamb = math.radians(lat0)
    phi = math.radians(lon0)
    s = math.sin(lamb)
    N = a / math.sqrt(1 - e_sq * s * s)

    sin_lambda = math.sin(lamb)
    cos_lambda = math.cos(lamb)
    sin_phi = math.sin(phi)
    cos_phi = math.cos(phi)

    x0 = (h0 + N) * cos_lambda * cos_phi
    y0 = (h0 + N) * cos_lambda * sin_phi
    z0 = (h0 + (1 - e_sq) * N) * sin_lambda

    F = np.zeros([3,3])
    T = np.zeros([3,1])
    Xd = np.zeros([3,1])
    Xd[0]   = x
    Xd[1]   = y
    Xd[2]   = z
#    xd = x - x0
#    yd = y - y0
#    zd = z - z0

    T[0] = x0
    T[1] = y0
    T[2] = z0
    
    F[0,0] = -  sin_phi 
    F[0,1] =    cos_phi 
    F[1,0] = - sin_lambda * cos_phi  
    F[1,1] = - sin_lambda * sin_phi 
    F[1,2] =   cos_lambda 
    F[2,0] =   cos_lambda *  cos_phi
    F[2,1] =   cos_lambda * sin_phi   
    F[2,2] =   sin_lambda
    
    X = F@ (Xd-T)
    
#    xEast = -sin_phi * xd + cos_phi * yd
#    yNorth = -cos_phi * sin_lambda * xd - sin_lambda * sin_phi * yd + cos_lambda * zd
#    zUp = cos_lambda * cos_phi * xd + cos_lambda * sin_phi * yd + sin_lambda * zd
 
    return float(X[0]),float(X[1]),float(X[2])#xEast, yNorth, zUp

def utm_getZone(longitude):
    global utm_zone
    utm_zone =  (int(1+(longitude+180.0)/6.0))

def utm_isNorthern(latitude):
    global is_northern
    if (latitude < 0.0):
        is_northern = False;
    else:
        is_northern = True;

def utm_isDefined():
    try: 
        is_northern  
    except  NameError:
        return False
    
    try: 
        utm_zone  
    except  NameError:
        return False

    return True
class Velocity :
            def __init__(self, vx  = 0.0,  vy = 0.0, vz =0.0):
               self.Repere       = 'UTM' 
               self.x   = vx
               self.y   = vy
               self.z   = vz
            def distanceToVelocity(self,M  ):
                 distance = np.sqrt(np.power(M.y - self.y ,2.0) + np.power(M.x - self.x ,2.0) + np.power(M.z - self.z ,2.0) ) 
                 return distance
            def setXYZ(self, x= 0, y = 0, z =0,_format ='UTM'):
                self.Repere             = _format
                self.z                  = z
                self.x                  = x
                self.y                  = y
                    
                    
            def norm(self):
               velocity = np.sqrt(np.power( self.y ,2.0) + np.power(  self.x ,2.0) + np.power( self.z ,2.0) ) 
               return velocity
               
class Attitude :
            def __init__(self, yaw  = 0.0,  pitch = 0.0, roll =0.0):
              
               self.yaw   = yaw
               self.roll  = pitch
               self.pitch = roll
               
   
                
                
class Position :
        def __init__(self, latitude  = [],  longitude = [], altitude =[]):
              
              global R0
              R0 = 6371
              self.Repere       = 'WGS84'
              self.EPSG         = 4326
              self.latitude     = latitude
              self.longitude    = longitude
              self.altitude     = altitude
              self.x_UTM        = 0
              self.y_UTM        = 0
              self.x_ENU        = 0
              self.y_ENU        = 0
              self.z_ENU        = 0
              if latitude and longitude and utm_isDefined() == False:
                  utm_getZone(longitude)
                  utm_isNorthern(latitude)
                  
              self.WGS842UTM()
              self.WGS842ENU()
        
        def __add__(self, other):
            if not isinstance(other, self.__class__):
                print("[ERROR] you are summing a Position object with something different")
                return self
            
            if self.altitude == []:
                self.altitude = 0

            x_ENU = self.x_ENU + other.x_ENU
            y_ENU = self.y_ENU + other.y_ENU
            z_ENU = self.z_ENU + other.z_ENU
          
            newPosition = Position()
 
            newPosition.setXYZ(x_ENU, y_ENU, z_ENU, 'ENU')
 
            return newPosition


        def setWGS84(self, longitude= 0, latitude = 0, altitude =0):
            self.Repere       = 'WGS84'
            self.EPSG         = 4326
            self.latitude     = latitude
            self.longitude    = longitude
            self.altitude     = altitude
            self.x_UTM        = 0
            self.y_UTM        = 0
            self.WGS842UTM()
            self.WGS842ENU()
        def setXYZ(self, x= 0, y = 0, z =0,_format ='UTM'):
            self.Repere       = 'WGS84'
            self.EPSG         = 4326
            self.latitude     = 0
            self.longitude    = 0
            if _format == 'UTM':
                self.altitude     = z
                self.x_UTM        = x
                self.y_UTM        = y
                self.UTM2WGS84()
                self.WGS842ENU()
            if _format =='ENU':
 
                self.x_ENU        = x
                self.y_ENU        = y
                self.z_ENU        = z
                self.ENU2WGS84()
                self.WGS842UTM()
            
        def translate(self, t =np.ndarray):
            
            self.x_UTM += t[0]
            self.y_UTM += t[1]
        def distanceToPoint(self,M  ):
            
            distance = np.sqrt(np.power(M.y_ENU - self.y_ENU ,2.0) + np.power(M.x_ENU - self.x_ENU ,2.0))# + np.power(M.altitude - self.altitude ,2.0) ) 
           
            D = np.sqrt( np.power(0.9996*distance,2.0) +  np.power(M.altitude - self.altitude,2.0) ) * ((M.altitude - self.altitude)/2 + R0 )/ R0
        
            return distance
        def changeGeometry(self,outputEPSG):
            
 
            point = ogr.Geometry(ogr.wkbPoint)
            point.AddPoint(self.longitude, self.latitude)

            # create coordinate transformation
            inSpatialRef = osr.SpatialReference()
            if int(gdal.__version__[0])>=3:
                inSpatialRef.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
            inSpatialRef.ImportFromEPSG(self.EPSG)

            outSpatialRef = osr.SpatialReference()
            if int(gdal.__version__[0])>=3:
                outSpatialRef.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
            outSpatialRef.ImportFromEPSG(outputEPSG)

            coordTransform = osr.CoordinateTransformation(inSpatialRef, outSpatialRef)

            # transform point
            point.Transform(coordTransform)

 
        def WGS842ENU(self):
           
            if REFERENCE_POINT.defined and self.latitude and self.longitude :
                x,y,z=geodetic_to_ecef(self.latitude,self.longitude,self.altitude)
                self.x_ENU,self.y_ENU,self.z_ENU = ecef_to_enu(x,y,z,REFERENCE_POINT.latitude,REFERENCE_POINT.longitude,REFERENCE_POINT.altitude )
        def ENU2WGS84(self):
     
            if REFERENCE_POINT.defined:
                x,y,z                                       = enu_to_ecef(self.x_ENU,self.y_ENU,self.z_ENU,REFERENCE_POINT.latitude,REFERENCE_POINT.longitude,REFERENCE_POINT.altitude )
                self.latitude,self.longitude,self.altitude  = ecef_to_geodedic(x,y,z)
        def WGS842UTM(self):

            if self.Repere == 'WGS84' and  self.longitude and self.latitude:
                       
 
                epsg3857 = osr.SpatialReference()
                if int(gdal.__version__[0])>=3:
                    epsg3857.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
                #epsg3857.ImportFromEPSG(32631)
                epsg3857.SetWellKnownGeogCS('WGS84')
                epsg3857.SetUTM(utm_zone,is_northern);
                epsg4326 = osr.SpatialReference()
                if int(gdal.__version__[0])>=3:
                    epsg4326.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
                epsg4326.ImportFromEPSG(4326)
                
                coordTransform = osr.CoordinateTransformation(epsg4326, epsg3857)

                point = ogr.Geometry(ogr.wkbPoint)
                point.AddPoint(self.longitude, self.latitude)
                point.Transform(coordTransform)
                self.x_UTM            = point.GetX()
                self.y_UTM            = point.GetY()
                
            
        def getECEF(self):
         
            return geodetic_to_ecef(self.latitude,self.longitude,self.altitude)
                
        def UTM2WGS84(self):
             if self.Repere == 'WGS84' and self.x_UTM and  self.y_UTM:
                epsg3857 = osr.SpatialReference()
                if int(gdal.__version__[0])>=3:
                    epsg3857.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
                #epsg3857.ImportFromEPSG(32631)
      
                epsg3857.SetWellKnownGeogCS('WGS84')
                epsg3857.SetUTM(utm_zone,is_northern);
   
                epsg4326 = osr.SpatialReference()
                if int(gdal.__version__[0])>=3:
                    epsg4326.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
                epsg4326.ImportFromEPSG(4326)
                
                coordTransform = osr.CoordinateTransformation( epsg3857, epsg4326)

                point = ogr.Geometry(ogr.wkbPoint)
                point.AddPoint( self.x_UTM ,  self.y_UTM)
                point.Transform(coordTransform)
                self.longitude            = point.GetX()
                self.latitude             = point.GetY()
                

