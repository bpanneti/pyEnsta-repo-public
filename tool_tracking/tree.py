# -*- coding: utf-8 -*-
"""
Created on Fri Mar 30 16:50:22 2018

@author: bpanneti
"""


class Tree:
    def __init__(self): 

        self.data     = None
        self.childs   = []
        self.parent   = None
        self.leafs    = []
        self.depth_d    = 0
        
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
        node.leafs      = self.leafs
        node.depth_d    = self.depth_d +1
        self.childs.append(node)
      
        self.addLeaf(node)

    def addLeaf(self, node):

        for count, leaf in enumerate(self.leafs):
            if node.parent == leaf:
                self.leafs[count] = node
                return

        self.leafs.append(node)
        
        
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
        cstr = spaces + str('|-> ') + str(self.data) + '\n'
        for child in self.childs :
            print(cstr)
            child.displayTree()