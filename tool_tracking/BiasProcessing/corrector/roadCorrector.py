from abc import ABCMeta, abstractmethod
from tool_tracking.BiasProcessing.corrector.biasCorrector import BiasCorrector, BIAS_CORRECTORS_TYPE
from point import Position
from matplotlib import pyplot as plt
import numpy as np
import math as mt

class RoadCorrector(BiasCorrector):
    __metaclass__ = ABCMeta

    def __init__(self, parent, name = BIAS_CORRECTORS_TYPE.NONE.name, integration = 15, threshold = 10):
        super(RoadCorrector, self).__init__(parent, name)
        self.type = BIAS_CORRECTORS_TYPE.NONE
        self.roads = []
        self.threshold = threshold
        self.roadsSelected = []
        self.associatedRoad = []
        self.allTrajectories = []
        self.trajectory = np.zeros((1,2))
        self.integration = integration
        self.canUpdate = True
        self.canDisplay = False
        self.fixed = None

    def onInitialize(self):
        self.canUpdate = True
        self.associatedRoad = []
        self.allTrajectories = []
        self.roadsSelected = []
        self.trajectory = np.zeros((1,2))
        self.fixed = None
        self.canDisplay = False


    @abstractmethod
    def onUpdate(self):
        pass

    def onLateUpdate(self):
        pass

    def integrationCheck(self, time):
        return time > self.integration

    def loadTrajectory(self):
        for track in self.parent.tracker.tracker.tracks:
            # check in the integration time is done
            for leaf in track.tree.leafs:
                print("Bias corrector time : {}".format(leaf.data.getDeltaTime()))
                if self.integrationCheck(leaf.data.getDeltaTime()):
                    self.addPositionChilds(leaf)

    def addPositionChilds(self, parent):
        if parent == None:
            return

        if parent.data.isEstimated:
            position = [parent.data.location.x_ENU, parent.data.location.y_ENU]
            self.addPosition(position)
        
        self.addPositionChilds(parent.parent)
        
    def addPosition(self, position):
        if self.allTrajectories == []:
            self.allTrajectories = np.array(position, ndmin = 2)
        else:
            self.allTrajectories = np.append(self.allTrajectories, [position], axis = 0)

    def loadRoad(self, roads):
        self.roads = np.zeros((len(roads), 2, 2))
        minPoint = None
        maxPoint = None

        for count, road in enumerate(roads):
            minPoint = Position(road.symin, road.sxmin, 0.0)
            maxPoint = Position(road.symax, road.sxmax, 0.0)
            self.roads[count] = [[minPoint.x_ENU, minPoint.y_ENU], [maxPoint.x_ENU, maxPoint.y_ENU]]

    def trajectoryInterpolation(self):
        if not self.allTrajectories:
            pass
        
    def findClosestRoad(self, trajectory):
        projMin = np.zeros((1,2))
        allDistMin = np.zeros((len(trajectory)), dtype=np.int32) 
        cntMin = np.zeros((len(trajectory)), dtype=np.int32) - 1
        projVector = np.zeros((trajectory.size // len(trajectory),))

        for count, position in enumerate(trajectory):
            distMin = 0
            distCurrent = 0
            cnt = 0
            firstEntry = True
            for road in self.roads:
                vector = position - road[0]
                roadVector = road[1] - road[0]
                projVector = np.vdot(vector, roadVector) / np.square(np.linalg.norm(roadVector)) * roadVector
                orthoVector = vector - projVector
                distCurrent = np.linalg.norm(orthoVector)

                if distCurrent <= self.threshold :
                    if firstEntry and self.isInSegment(roadVector, projVector) :
                        self.trajectory = np.append(self.trajectory, [position], axis = 0)
                        projMin = np.append(projMin, [road[0] + projVector], axis = 0)
                        distMin = distCurrent
                        cntMin[count] = cnt
                        firstEntry = False
                    elif self.isInSegment(roadVector, projVector):
                        if distCurrent < distMin:
                            self.trajectory[-1,:] = position
                            projMin[-1,:] = road[0] + projVector
                            cntMin[count] = cnt
                            distMin = distCurrent
    
                cnt += 1
            
            allDistMin[count] = distMin
        
        if self.trajectory.shape != (1,2) :
            self.trajectory = self.trajectory[1:,:]
            projMin = projMin[1:,:]

        self.setRoadsSelected(cntMin)
        self.associatedRoad = projMin
        print(projMin.shape)
        print(self.trajectory.shape)
        return allDistMin

    def setRoadsSelected(self, indexes):
        newInd = []
        for ind in indexes:
            if ind not in newInd and ind != -1:
                newInd.append(ind)
        self.roadsSelected = self.roads[newInd]

    def isInSegment(self, refVector, vectorToCheck):
        return np.linalg.norm(refVector) > np.linalg.norm(vectorToCheck) and np.linalg.norm(refVector) > np.linalg.norm(refVector-vectorToCheck)

    def lms(self, src, dest):
        associatedRoadCentered = dest - dest.mean(axis = 0)
        trajectoryCentered = src - src.mean(axis = 0)

        crossCovCentered = np.dot(associatedRoadCentered.T, trajectoryCentered)

        covCentre = np.dot(trajectoryCentered.T, trajectoryCentered)
        rotLeft, singularValue, rotRight = np.linalg.svd(crossCovCentered)
        
        rot = np.dot(rotRight.T, rotLeft.T)
        scale = np.sum(singularValue)/np.trace(covCentre)
        translation = (np.dot(np.array([dest.mean(axis = 0)]).T, np.ones((1, len(trajectoryCentered)))) - np.dot(np.array([np.dot(src.mean(axis = 0), rot)]).T, np.ones((1,len(trajectoryCentered))))).T

        return rot, translation, scale

    def onDisplay(self):
        if self.canDisplay:
            plt.figure()
            plt.title("Trajectoire corrigée par correcteur de biais", fontsize=20)
            plt.plot(self.fixed[:,0], self.fixed[:,1], 'ro', label = "Trajectoire estimé corrigé")
            plt.plot(self.trajectory[:,0], self.trajectory[:,1], 'bo', label = "Trajectoire estimé")
            plt.plot(self.associatedRoad[:,0], self.associatedRoad[:,1], 'go', label = "Trajectoire estimé projeté sur les routes")

            for road in self.roadsSelected:
                plt.plot([road[0,0], road[1,0]], [road[0,1], road[1,1]], 'k-')
            plt.plot([],[], 'k-', label = "Routes")
            plt.plot([],[], ' ', label = 'Biais en x(m) : {}\nBiais en y(m) : {}\nBiais en angle(°) : {}\nEchelle : {}\nRepère indirect : {}'.format(self.xBiais, self.yBiais, self.yaw, self.scale, self.swap))
            plt.legend()
            plt.xlabel("Position suivant X (en m)", fontsize=18)
            plt.ylabel("Position suivant Y (en m)", fontsize=18)
            plt.show()
            self.canDisplay = False

    def save(self, executeRequest, conn):
        super(RoadCorrector,self).save(executeRequest, conn)
        command = []
        command.append("insert into roadCorrector_t values ")
        command.append("({}, {}, {})".format(self.parentId, self.integration, self.threshold))
        command = ''.join(command)

        executeRequest(conn, command)
        print('Road corrector saved')