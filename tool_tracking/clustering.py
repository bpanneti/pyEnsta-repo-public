# -*- coding: utf-8 -*-
"""
Created on Tue Oct 27 09:03:43 2020

@author: pannetier
"""

import numpy as np

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
