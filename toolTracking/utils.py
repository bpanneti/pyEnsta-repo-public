from enum import Enum
import numpy as np

class trackerType(Enum):
    UNKNOWN         = 0
    CMKF            = 1
    #----> EKF             = 2
    #---->IMM             = 3
    #---->GNNSF           = 4
    #---->SDA             = 5 
    
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


class TrackState:
    Tentative = 1
    Confirmed = 2
    Deleted   = 3


# matrice représentant la cinétique du mouvement
def F(periode=0.0, dim=4, motionModelType=MotionModel.UNKNOWN):
    mat #--->  

    #if dim == 4 and motionModelType == MotionModel.CV:
            #--->  
    return mat

def Q(T=0.0, dim=4, motionModelType=MotionModel.UNKNOWN, noise=0.0):
    mat #--->  

    if dim == 4 and motionModelType == MotionModel.CV:
        mat #--->  
    noisedMat = np.array(np.power(noise, 2.0)*mat)

    return noisedMat

def Compress(Omega_Matrix):
    Omega_Compress      = []
    Track_indices       = []
    Measurement_Indices = []
    
    if  Omega_Matrix.size == 0:
        return Omega_Compress, Track_indices, Measurement_Indices
 
    Track_indices = np.where(np.sum(Omega_Matrix, axis=1)!=0)[0]
    Measurement_Indices = np.where(np.sum(Omega_Matrix, axis=0)!=0)[0]
    
    # Compression of initial validation matrix
    Omega_Compress = Omega_Matrix

    Omega_Compress = np.delete(Omega_Compress,np.where(np.sum(Omega_Compress,axis=1)==0)[0],0)
    Omega_Compress = np.delete(Omega_Compress,np.where(np.sum(Omega_Compress,axis=0)==0)[0],1)
                  
    return Omega_Compress, Track_indices, Measurement_Indices

def clustering(Omega_Compress =[]):
    
    Cluster   = []  
    Nz              = np.size(Omega_Compress,1);
    Ntarget         = np.size(Omega_Compress,0);
    Track_indices_by_cluster = []
    if  Omega_Compress.size == 0:
            return Cluster

    #Cluster separation
    Null_Row=np.zeros((1,np.size(Omega_Compress,1)))
    L =np.zeros((1,np.size(Omega_Compress,1)))
    Cluster=Omega_Compress;
 
    for j in range(0,Nz):
        M = np.vstack(([Cluster[np.where(Cluster[:,j]!=0)[0],:],Null_Row]))
    
        L = np.sum(M,axis = 0)
        Cluster =np.delete(Cluster,np.where(Cluster[:,j]!=0)[0],0)
        Cluster =np.vstack([Cluster,L])
    return Cluster  

def main():
    Omega = np.array([[0, 0 ,1 ,0, 1 ,0 ,0],
            [0 ,0 ,0 ,0, 0 ,0, 1],
            [1 ,0 ,0 ,0, 0 ,1, 0],
            [0 ,0 ,0 ,0 ,0 ,0, 0],
            [0 ,0 ,0 ,0 ,1 ,0, 0],
            [0 ,1 ,1 ,0 ,1 ,0, 0],
            [0 ,1 ,1 ,0 ,0 ,0, 0],
            [0 ,0 ,0 ,0 ,0 ,0, 0],
            [0 ,0 ,0 ,0 ,0 ,1, 0],
            [1 ,0 ,0 ,0 ,0 ,0, 0]])
    
    Omega_Compress, Track_indices, Measurement_Indices = Compress(Omega)
    
    print(Omega_Compress)
    print(Track_indices)
    print(Measurement_Indices)
    cluster = clustering(Omega_Compress)
    print(cluster)
if __name__ == "__main__":
    main()