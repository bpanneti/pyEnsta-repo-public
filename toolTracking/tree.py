# -*- coding: utf-8 -*-
"""
Created on Fri Mar 30 16:50:22 2018

@author: bpanneti
"""

from toolTracking.state import State
from PyQt5.QtCore import QDateTime
from copy import deepcopy as deepCopy

class Tree:
    def __init__(self,data= None,markToDelete=False):#,parent = None,childs=[],time = QDateTime(), plot = None, state = None,parameters=None,idTrack=-1): 
        #super().__init__(time,plot,idTrack,state,parameters)
        
 
    
        self.childs   = []
        self.parent   = None
        self.leafs    = []
        self.depth_d  = 0
        self.data     = data
        self.markToDelete = markToDelete      
    # @staticmethod
    # def copyTree(previousState):
 
    #     actualState = State.copyState(previousState)
    #     actualState.childs   = []
    #     actualState.leafs    = []
    #     actualState.parent   = None

    #     return actualState
        
    def getNode(self,time):
        _node = self
      
        while _node!=[]:
            if _node.date ==time:
                return _node
            
            _node = _node.child
        
        return []

    def removeChild(self,node):
        index = 0
        for i in range(0,len(self.childs)):
            if self.childs[i] == node:
                index = i;
        self.childs = self.childs[:index] + self.childs[index+1 :]
        
    def addChild(self, node):

        node.parent     =  self
        #node.leafs      = self.leafs
        node.depth_d    = self.depth_d +1
        self.childs.append(node)
      
        #self.addLeaf(node)

    def addLeaf(self, node):

        for count, leaf in enumerate(self.leafs):
            if node.parent == leaf:
                self.leafs[count] = node
                return

        self.leafs.append(node)
        
    def markBranch(self):
        
        self.markToDelete = True
        
        for _child in self.childs:
            if _child.markToDelete == False:
                self.markToDelete = False
                return
            
        
        if self.parent:
            self.parent.markBranch()
                           
    def getChilds(self,roots =[]):
 
        for i in self.childs:
 
            i.getChilds(roots)
            
        if  self.childs == []:
 
            roots.append(self)

        return
     
    def getData(self,condition):
        if self.data!=None and self.data.id == condition:
            return True,self
        for _child  in self.childs:
            
             flag,_val = _child.getData(condition)
             if flag == True:
                 return True,_val
             
        return False,None
        
    def depthParent(self):
        depth = 1
  
        if self.parent!=None:
            depth += self.parent.depthParent()
         
        return depth
    def depth(self):
        depth = 1
        
        depth_max = 0
 
   
        for _childs in self.childs:
            _localDepth = _childs.depth()
            if _localDepth >= depth_max:
                depth_max = _localDepth
        depth +=  depth_max
        return depth
    
    def displayTree(self):
        spaces = ' ' * (self.depthParent() - 1)
        cstr = spaces + str('|-> ') + str(self.data.id) + '_idtrack : '+str(self.data.idTrack ) +'_depth :'+str(self.depth_d)+'\n'
        for child in self.childs :
            print(cstr)
            child.displayTree()