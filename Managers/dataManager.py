"""
Code from https://gist.github.com/werediver/4396488
"""
from threading import RLock

from sensor import Node,Sensor
from target import Target

class DataManager:
    _instance = None
    _rlock = RLock()

    
    @classmethod
    def instance(self):
        """Get *the* instance of the class, constructed when needed using (kw)args.

        Return the instance of the class. If it did not yet exist, create it
        by calling the "constructor" with whatever arguments and keyword arguments
        provided.

        This routine is thread-safe. It uses the *double-checked locking* design
        pattern ``https://en.wikipedia.org/wiki/Double-checked_locking``_ for this.

        :param args: Used for constructing the instance, when not performed yet.
        :param kwargs: Used for constructing the instance, when not perfored yet.
        :return: An instance of the class
        """
        if self._instance is not None:
            return self._instance
        with self._rlock:
            # re-check, perhaps it was created in the mean time...
            if self._instance is None:
                self._inside_instance = True
                try:
                    self._instance = self()
                finally:
                    self._inside_instance = False
        return self._instance

    def __new__(self):
        """Raise Exception when not called from the :func:``instance``_ class method.

        This method raises RuntimeError when not called from the instance class method.

        :param args: Arguments eventually passed to :func:``__init__``_.
        :param kwargs: Keyword arguments eventually passed to :func:``__init__``_
        :return: the created instance.
        """
        if not self._inside_instance:
            raise TypeError(f"Attempt to instantiate mixin class {self.__qualname__}")

        if self._instance is None:
            with self._rlock:
                if self._instance is None and self._inside_instance:
                    return super().__new__(self)

        raise RuntimeError(
             f"Attempt to create a {self.__qualname__} instance outside of instance()"
         )

    def __init__(self):
        self._nodes  = [] #list of nodes
        self.biaisCorrectors = dict() #dictionary of bias correctors
        self._targets = []
     
        

    def addNodes(self, nodes):
        if nodes == [] or nodes == None:
            return
        
        for node in nodes:
            self.addNode(node)
    def removeNodes(self):
        del self._nodes[:]
        self._nodes  = [] 
    def removeTargets(self):
        del self._targets[:]
        self._targets  = [] 
    
    def removeNode(self,idNode):
        for _node in self._nodes:
            if _node.id == idNode:
                self._nodes.remove(_node)
                del _node
                return
    def removeTarget(self,idTarget):
        for _target in self._targets:
            if _target.id == idTarget:
                self._targets.remove(_target)
                
                for _node in self._nodes:
                     for _sensor in _node.sensors:
                         if _target in _sensor.targets:
                            _sensor.targets.remove(_target)
                del _target
                return
    def addNode(self, node):
        if not isinstance(node, Node):
            print("[WARNING] It's not a node!")
        
        self._nodes.append(node)
    def addSensor(self, _sensor):
        if not isinstance(_sensor, Sensor):
            print("[WARNING] It's not a sensor!")
        
        
        for _node in self._nodes:
            if _node.id == _sensor.id_node:
                if self.searchSensor(_sensor.id)==None:
                    _node.sensors.append(_sensor)
                _sensor.node = _node
                break
       
        for target in self._targets:  
            if target not in _sensor.targets:
                _sensor.targets.append(target)
    def removeSensor(self,_sensor):
        if not isinstance(_sensor, Sensor):
            print("[WARNING] It's not a sensor!")
        for _node in self._nodes:
            if _node.id == _sensor.id_node:
                _node.sensors.remove(_sensor)
                del _sensor
                return            
    def addSensors(self, sensors):
       if sensors == [] or sensors == None:
            return
       for _sensor in sensors:
            self.addSensor(_sensor) 
    def addTargets(self, targets):
        if targets == [] or targets == None:
            return
        for target in targets:
            self.addTarget(target) 
            
    def addTarget(self, target):
        if not isinstance(target, Target):
            print("[WARNING] It's not a node!")
        self._targets.append(target)   
        for _node in self._nodes:
             for _sensor in _node.sensors:
                 if target not in _sensor.targets:
                     _sensor.targets.append(target)
        
    def sensors(self):
        _sensors =[]
        for _node in self._nodes:
             for _sensor in _node.sensors:
                 _sensors.append(_sensor)
        return _sensors
    def targets(self):
        return self._targets
    def nodes(self):
        return self._nodes
    
    def searchSensor(self,idSensor):
        for _node in self._nodes:
  
            for _sensor in _node.sensors:
                if _sensor.id== idSensor:
                    return _sensor
        return None
    def searchNode(self,idNode):
 
            for _node in self._nodes:
                if _node.id== idNode:
                    return _node
            return None