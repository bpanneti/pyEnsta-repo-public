from tool_tracking.BiasProcessing.corrector.biasCorrector import BiasCorrector, BIAS_CORRECTORS_TYPE
from point import Position
from matplotlib import pyplot as plt
from matplotlib import collections as mc
import cv2
import numpy as np
import math as mt

class LogPolar(BiasCorrector):
    def __init__(self, parent, name = BIAS_CORRECTORS_TYPE.ROAD_LMS.name, integration = 20):
        super(LogPolar, self).__init__(parent, name)
        self.type = BIAS_CORRECTORS_TYPE.ROAD_LMS
        self.roads = []
        self.trajectory = []
        self.binaryTrajectory = []
        self.fftBinaryTrajectory = []
        self.logPolarTrajectory = []
        self.associatedRoad = []
        self.binaryAssociatedRoad = []
        self.fftBinaryAssociatedRoad = []
        self.logPolarAssociatedRoad = []
        self.integration = integration
        self.canUpdate = True
        self.scalePrecision = 1
        self.xOffTrajectory = 0
        self.yOffTrajectory = 0
        self.xOffAssociatedRoad = 0
        self.yOffAssociatedRoad = 0

    def onInitialize(self):
        self.canUpdate = True
        pass

    def onUpdate(self):
        if self.isEmpty(self.trajectory):
            return

        if self.isEmpty(self.roads):
            return

        if not self.canUpdate:
            return

        self.findClosestRoad()
        self.setupBinaryImages()
        self.fftBinaryImages()
        self.createLogPolar()
        
        rotation, translation, scale = self.lms()
        # fig, axs = plt.subplots(2, 3, constrained_layout=True)
        # axs[0,0].set_title("binary Trajectory")
        # axs[0,0].imshow(self.binaryTrajectory, cmap = plt.get_cmap('gray'))
        # axs[1,0].set_title("binary Associated Road")
        # axs[1,0].imshow(self.binaryAssociatedRoad, cmap = plt.get_cmap('gray'))

        # axs[0,1].set_title("fft binary Trajectory")
        # axs[0,1].imshow(abs(self.fftBinaryTrajectory), cmap = plt.get_cmap('gray'))
        # axs[1,1].set_title("fft Associated Road")
        # axs[1,1].imshow(abs(self.fftBinaryAssociatedRoad), cmap = plt.get_cmap('gray'))

        # axs[0,2].set_title("log Polar Trajectory")
        # axs[0,2].imshow(self.logPolarTrajectory, cmap = plt.get_cmap('gray'))
        # axs[1,2].set_title("log Polar Associated Road")
        # axs[1,2].imshow(self.logPolarAssociatedRoad, cmap = plt.get_cmap('gray'))
        # plt.show()
        
        # fig, ax = plt.subplots(1, 1, constrained_layout=True)
        # ax.plot(self.trajectory[:,0], self.trajectory[:,1], 'bo')
        # ax.plot(self.associatedRoad[:,0], self.associatedRoad[:,1], 'go')

        fixed = np.dot(self.trajectory,rotation)*scale + translation

        plt.figure()
        plt.title("trajectory fixed")
        plt.plot(fixed[:,0], fixed[:,1], 'ro')
        plt.plot(self.trajectory[:,0], self.trajectory[:,1], 'bo')
        plt.plot(self.associatedRoad[:,0], self.associatedRoad[:,1], 'go')

        plt.show()

        print("translation :")
        print(translation)
        print("angle : {}".format(mt.acos(rotation[0,0])*180/mt.pi))
        print("scale : {}".format(scale))

        self.canUpdate = False

    def integrationCheck(self, time):
        return time > self.integration

    def isEmpty(self, matrice):
        return matrice == []

    def loadRoad(self, roads):
        self.roads = np.zeros((len(roads), 2, 2))
        minPoint = None
        maxPoint = None

        for count, road in enumerate(roads):
            minPoint = Position(road.symin, road.sxmin, 0.0)
            maxPoint = Position(road.symax, road.sxmax, 0.0)
            self.roads[count] = [[minPoint.x_ENU, minPoint.y_ENU], [maxPoint.x_ENU, maxPoint.y_ENU]]
        
    def addPositions(self, positions):
        for position in positions:
            self.addPosition(position)

    def addPosition(self, position):
        if self.isEmpty(self.trajectory):
            self.trajectory = np.array(position, ndmin = 2)
        else:
            self.trajectory = np.append(self.trajectory, [position], axis = 0)

    def trajectoryInterpolation(self):
        if not self.trajectory:
            pass
        
    def findClosestRoad(self):
        projMin = np.zeros((len(self.trajectory), self.trajectory.size // len(self.trajectory)))
        cntMin = np.zeros((len(self.trajectory), self.trajectory.size // len(self.trajectory)))
        projVector = np.zeros((self.trajectory.size // len(self.trajectory),))

        for count, position in enumerate(self.trajectory):
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

                if firstEntry and self.isInSegment(roadVector, projVector):
                    projMin[count] = road[0] + projVector
                    distMin = distCurrent
                    cntMin[count] = cnt
                    firstEntry = False
                elif self.isInSegment(roadVector, projVector):
                    if distCurrent < distMin:
                        projMin[count] = road[0] + projVector
                        cntMin[count] = cnt
                        distMin = distCurrent

                cnt += 1

        self.associatedRoad = projMin

    def isInSegment(self, refVector, vectorToCheck):
        return np.linalg.norm(refVector) > np.linalg.norm(vectorToCheck) and np.linalg.norm(refVector) > np.linalg.norm(refVector-vectorToCheck)

    def createImageContainer(self, vector):
        dim = mt.ceil(max(abs(vector[:,0].max() - vector[:,0].min()), abs(vector[:,1].max() - vector[:,1].min()))/self.scalePrecision)+1
        self.binaryTrajectory = np.zeros((dim, dim))
        self.binaryAssociatedRoad = np.zeros((dim, dim))

    def defineOffset(self):
        self.xOffTrajectory = mt.floor(self.trajectory[:,0].min())
        self.yOffTrajectory = mt.floor(self.trajectory[:,1].min())
        self.xOffAssociatedRoad = mt.floor(self.associatedRoad[:,0].min())
        self.yOffAssociatedRoad = mt.floor(self.associatedRoad[:,1].min())

    def addDotsImage(self, image, dots, xOffset, yOffset):
        for dot in dots:
            x = int(round(dot[0]/self.scalePrecision))-xOffset-1
            y = int(round(dot[1]/self.scalePrecision))-yOffset-1
            if x<0:
                x = 0
            if y<0:
                y = 0
            image[x, y] = 1

    def setupBinaryImages(self):
        self.createImageContainer((np.concatenate((self.trajectory, self.associatedRoad))))
        self.defineOffset()
        self.addDotsImage(self.binaryAssociatedRoad, self.associatedRoad, self.xOffAssociatedRoad, self.yOffAssociatedRoad)
        self.addDotsImage(self.binaryTrajectory, self.trajectory, self.xOffTrajectory, self.yOffTrajectory)

    def fftBinaryImages(self):
        self.fftBinaryAssociatedRoad = np.fft.fft2(self.binaryAssociatedRoad)
        self.fftBinaryTrajectory = np.fft.fft2(self.binaryTrajectory)
        
    def createLogPolar(self):
        self.logPolarAssociatedRoad = cv2.logPolar(abs(self.fftBinaryAssociatedRoad),(self.fftBinaryAssociatedRoad.shape[0]//2,self.fftBinaryAssociatedRoad.shape[0]//2),1,flags=cv2.WARP_FILL_OUTLIERS)
        self.logPolarTrajectory = cv2.logPolar(abs(self.fftBinaryTrajectory),(1,1),1,flags=cv2.WARP_FILL_OUTLIERS)

    def lms(self):
        associatedRoadCentered = self.associatedRoad - self.associatedRoad.mean(axis = 0)
        trajectoryCentered = self.trajectory - self.trajectory.mean(axis = 0)

        crossCovCentered = np.dot(np.dot(associatedRoadCentered.T, np.eye(len(self.associatedRoad))), trajectoryCentered)

        covCentre = np.dot(np.dot(trajectoryCentered.T, np.eye(len(trajectoryCentered))), trajectoryCentered)
        rotLeft, singularValue, rotRight = np.linalg.svd(crossCovCentered)
        
        rot = np.dot(rotLeft, rotRight)
        scale = np.sum(singularValue)/np.trace(covCentre)
        translation = (np.dot(np.array([self.associatedRoad.mean(axis = 0)]).T, np.ones((1, len(trajectoryCentered)))) - np.dot(np.array([scale*np.dot(self.trajectory.mean(axis = 0), rot)]).T, np.ones((1,len(trajectoryCentered))))).T

        return rot, translation, scale

    def save(self, executeRequest, conn):
        super(LogPolar,self).save(executeRequest, conn)
        command = []
        command.append("insert into roadLms_t values ")
        command.append("({}, {})".format(self.parentId, self.integration))
        command = ''.join(command)

        executeRequest(conn, command)
        print('Road Lms saved')