# -*- coding: utf-8 -*-
"""
Created on Thu Jul  4 13:56:02 2019

@author: bpanneti
"""

class Orientation:
    def __init__(self, yaw  = 0.0,  pitch = 0.0, roll =0.0):
        self.Repere       = 'ENU';#ENU/SENSOR
        self.yaw      = yaw
        self.pitch    = pitch
        self.roll     = roll

    def __add__(self, other):
        if not isinstance(other, self.__class__):
            print("[ERROR] you are summing an Orientation object with something different")
            return self
        
        return Orientation(self.yaw + other.yaw, self.pitch + other.pitch, self.roll + other.roll)
       
    def setOrientation(self,yaw =0.0, pitch = 0.0, roll = 0.0):
        self.yaw      = yaw
        self.pitch    = pitch
        self.roll     = roll