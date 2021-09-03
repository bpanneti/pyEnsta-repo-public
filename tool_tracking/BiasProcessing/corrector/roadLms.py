from tool_tracking.BiasProcessing.corrector.biasCorrector import BIAS_CORRECTORS_TYPE
from tool_tracking.BiasProcessing.corrector.roadCorrector import RoadCorrector
from point import Position
from matplotlib import pyplot as plt
import numpy as np
import math as mt

class RoadLms(RoadCorrector):
    def __init__(self, parent, name = BIAS_CORRECTORS_TYPE.ROAD_LMS.name, integration = 20, threshold = 10):
        super(RoadLms, self).__init__(parent, name, integration, threshold)
        self.type = BIAS_CORRECTORS_TYPE.ROAD_LMS
        self.fixed = None

    def onUpdate(self):
        if not self.canUpdate:
            return
        
        if self.roads == []:
            return

        self.loadTrajectory()

        if self.allTrajectories == []:
            return

        self.canUpdate = False

        self.findClosestRoad(self.allTrajectories)

        rotation, translation, scale = self.lms(self.trajectory, self.associatedRoad)

        self.fixed = np.dot(self.trajectory,rotation) + translation

        self.xBiais = translation[0,0]
        self.yBiais = translation[0,1]
        print("biais x : {}\nbiais y : {}".format(self.xBiais, self.yBiais))
        self.yaw = mt.copysign(mt.acos(rotation[0,0])*180/mt.pi,mt.asin(rotation[1,0]))
        print("angle : {}".format(self.yaw))
        self.swap = not (mt.copysign(1, rotation[0,0]) == mt.copysign(1, rotation[1,1]))
        print("Repère indirecte : ".format(self.swap))
        print("scale : {}".format(scale))
        self.scale = scale
        self.fixedBias()
        self.canDisplay = True

    def save(self, executeRequest, conn):
        super(RoadLms,self).save(executeRequest, conn)
        command = []
        command.append("insert into roadLms_t values ")
        command.append("({})".format(self.parentId))
        command = ''.join(command)

        executeRequest(conn, command)
        print('Road Lms saved')