from enum import Enum
import numpy as np

class StateType(Enum):
    UNKNOWN = 0
    XY      = 1
    XYZ     = 2

class MotionModel(Enum):
    UNKNOWN = 0
    CV      = 1
    CA      = 2
    CT      = 3

def h(x, y):
    mat = np.zeros([2, 1])
    mat[0] = np.sqrt(x**2+y**2)
    mat[1] = np.arctan2(y, x)
    mat[1] = np.mod(mat[1]+np.pi, 2*np.pi)-np.pi
    return mat


# matrice représentant la cinétique du mouvement
def F(periode=0.0, dim=4, motionModelType=MotionModel.UNKNOWN):
    mat = np.identity(dim)

    if dim == 4 and motionModelType == MotionModel.CV:
        mat[0, 1] = periode
        mat[2, 3] = periode

    return mat

def Q(T=0.0, dim=4, motionModelType=MotionModel.UNKNOWN, noise=0.0):
    mat = np.identity(dim)

    if dim == 4 and motionModelType == MotionModel.CV:
        mat = np.array([[np.power(T, 3)/3, np.power(T, 2)/2, 0, 0], [np.power(T, 2)/2, T, 0, 0], [0, 0, np.power(T, 3)/3, np.power(T, 2)/2], [0, 0, np.power(T, 2)/2, T]])

    noisedMat = np.array(np.power(noise, 2.0)*mat)

    return noisedMat