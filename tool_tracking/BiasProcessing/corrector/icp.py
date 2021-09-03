
from tool_tracking.BiasProcessing.corrector.biasCorrector import BIAS_CORRECTORS_TYPE
from tool_tracking.BiasProcessing.corrector.roadCorrector import RoadCorrector
from matplotlib import pyplot as plt
from tool_tracking.BiasProcessing.data.icp import nearestNeighbor, bestFitTransform, icp
import numpy as np
import math as mt

class Icp(RoadCorrector):
    def __init__(self, parent, name=BIAS_CORRECTORS_TYPE.ICP.name, integration=20, maxIteration = 20, tolerance = 0.001, threshold = 10):
        super(Icp, self).__init__(parent, name, integration, threshold)
        self.type = BIAS_CORRECTORS_TYPE.ICP
        self.maxIteration = maxIteration
        self.tolerance = tolerance
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
        # rotation, translation, scale, distances, i = self.icp()
        self.findClosestRoad(self.allTrajectories)

        rotation, translation, scale, distances, i = self.icp()
        self.fixed = np.dot(self.trajectory,rotation) + translation
        # C = np.ones((np.shape(self.trajectory)[0], np.shape(self.trajectory)[1]+1))
        # C[:,:np.shape(self.trajectory)[1]] = np.copy(self.trajectory)

        # # Transform C
        # C = np.dot(T, C.T).T
        
        # self.fixed = C[:,:np.shape(self.trajectory)[1]]
        
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

    def icp(self, init_pose=None):
        '''
        Code made by : ClayFlannigan with some modifications
        https://github.com/ClayFlannigan/icp/blob/master/icp.py
        The Iterative Closest Point method: finds best-fit transform that maps points A on to points B
        Input:
            init_pose: (m+1)x(m+1) homogeneous transformation
        Output:
            Rotation: final Rotation that maps A on to B
            Translation: final translation that maps A on to B
            Scale: final scale that maps A on to B
            distances: Euclidean distances (errors) of the nearest neighbor
            i: number of iterations to converge
        '''

        # make points homogeneous, copy them to maintain the originals

        src = np.copy(self.trajectory)
        dst = np.ones(self.trajectory.shape)

        # apply the initial pose estimation
        if init_pose is not None:
            src = np.dot(init_pose, src)

        prev_error = 0
        # minError = 0

        for i in range(self.maxIteration):

            # find the nearest neighbors between the current source and destination points
            distances, indices = nearestNeighbor(src, self.associatedRoad)

            # compute the transformation between the current source and nearest destination points
            rotation, translation, scale = self.lms(src, self.associatedRoad[indices,:])
            # print("T: {}\nsrc: {}".format(T, src))

            # update the current source
            src = np.dot(src,rotation) + translation
            # src = np.dot(T, src.T)

            # check error
            mean_error = np.mean(distances)
            # if i == 0 or minError>mean_error:
            #     minError = mean_error
            
            print("iteration : {}\ntolérance : {}\n diffError : {}".format(i, self.tolerance, np.abs(prev_error - mean_error)))
            if np.abs(prev_error - mean_error) < self.tolerance: #and minError == mean_error:
                break
            prev_error = mean_error

        # calculate final transformation
        rotation, translation, scale = self.lms(self.trajectory, src)

        return rotation, translation, scale, distances, i

    def save(self, executeRequest, conn):
        super(Icp,self).save(executeRequest, conn)
        command = []
        command.append("insert into icp_t values ")
        command.append("({}, {}, {})".format(self.parentId, self.maxIteration, self.tolerance))
        command = ''.join(command)

        executeRequest(conn, command)
        print('Icp saved')