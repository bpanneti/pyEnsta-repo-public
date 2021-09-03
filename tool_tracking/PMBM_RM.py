import numpy as np
import matplotlib.pyplot as plt
#from numba.decorators import njit
import math
from scipy.optimize import linear_sum_assignment
from scipy.special import multigammaln

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from tool_tracking.track import Track
from tool_tracking.state import State

from sklearn.cluster import DBSCAN as dbscan

import sys

MINI_FLOAT = sys.float_info.min

def cluster(scan, eps=50, min_samples=2):
    labels = dbscan(eps,min_samples,metric="euclidean").fit(scan[:2,:].T)
    return labels.labels_,labels.labels_.max()+1

def gaussian(x,mu,sig):
    numerat = np.exp(-0.5*(x-mu).dot(np.linalg.inv(sig)).dot(x-mu))
    denom = (np.sqrt(np.linalg.det(sig))*(2*np.pi))
    return numerat/denom

def multigamma(a,b):
    return np.exp(multigammaln(a,b))

def matSqrt(X):
    D_X, P_X = np.linalg.eig(X)
    D_X = np.diag(np.sqrt(D_X))
    return P_X.dot(D_X).dot(np.linalg.inv(P_X))

def frobNorm(X):
    return np.sqrt(np.trace(X.dot(X.T)))

def findWindow(gM,j,meas,trck):
    meas[j] = 1
    trck = trck | gM[:,j]
    new_trck = np.nonzero(gM[:,j])[0]
    for i in new_trck:
        if ((gM[i,:]>0) & (meas==0)).any():
            j2 = np.nonzero((gM[i,:]>0) & (meas==0))[0]
            for j3 in j2:
                meas, trck = findWindow(gM,j3,meas,trck)
    return meas,trck

def Q(T,dim,noise):
    
    M  = np.identity(3*dim)
        
    M =   np.array([[ np.power(T,4)/4, np.power(T,3)/2, np.power(T,2)/2, 0, 0, 0], \
                    [ np.power(T,3)/2, np.power(T,2)  ,        T       , 0, 0, 0], \
                    [ np.power(T,2)/2  ,        T       ,        1       , 0, 0, 0], \
                    [ 0, 0, 0, np.power(T,4)/4, np.power(T,3)/2, np.power(T,2)/2], \
                    [ 0, 0, 0, np.power(T,3)/2, np.power(T,2)  ,        T       ], \
                    [ 0, 0, 0, np.power(T,2)/2  ,        T       ,        1       ]] )
    
    Q  = np.matrix(np.power(noise,2.0)*M)/T
    
    return Q  

class Tgts():
    init_state_cov = np.kron(np.eye(2),np.array(((500,0,0),(0,500,0),(0,0,500))))
    d=2
    init_weight=0.8

    def __init__(self, pc=np.ndarray(()), cov=np.ndarray(()), ext=np.ndarray(()), card=np.ndarray(()), not_assigned=np.zeros(()), prev_pc=np.ndarray(()), prev_cov=np.ndarray(()), prev_ext=np.ndarray(()), prev_card=np.ndarray(()), prev_not_assigned=np.ndarray((0)),dt=0):
        if (prev_not_assigned>0).any():
            self.consec_init(pc, cov, ext, card, not_assigned, prev_pc, prev_cov, prev_ext, prev_card, prev_not_assigned,dt)
        else:
            self.regular_init()

    def regular_init(self):
        # The objectif here is to take each non assigned measurment from
        # previous detection and use them to create new targets
        # timestamp could be used in order to label
        # predict a new target in fov frontier
        self.state_v_p = np.ndarray((3*self.d,1))
        self.state_c_p = np.ndarray((3*self.d,3*self.d,1))
        self.lambda_p = np.ndarray((1))
        self.state_v_p[0::3,0] = np.array((500,0)) # 50m in front and 0m left or right
        self.state_v_p[1::3,0] = 0
        self.state_v_p[2::3,0] = 0
        self.state_c_p[:,:,0] = self.init_state_cov
        self.alpha_p = np.array((1,))
        self.beta_p = np.array((1,))
        self.nu_p = np.array((7,))
        self.Nu_p = np.zeros((self.d,self.d,1))
        self.Nu_p[0,0] = 1
        self.Nu_p[1,1] = 1
        self.lambda_p[0] = self.init_weight
        self.n_p = 1

        # Multi Bernoulli
        self.n_mb = 0
        self.r = np.ndarray((0))
        self.state_v_mb = np.ndarray(())
        self.state_c_mb = np.ndarray(())
        self.alpha_mb = np.ndarray(())
        self.beta_mb = np.ndarray(())
        self.nu_mb = np.ndarray(())
        self.Nu_mb = np.ndarray(())
        self.labels = np.ndarray(())
            
    # TODO: initialize new targets from consecutive measurments in order to get a plausible speed!
    # Maybe inspire myself of the way the init of new mbs is done with the former Poisson!
    def consec_init(self, pc, cov, ext, card, not_assigned, prev_pc, prev_cov, prev_ext, prev_card, prev_not_assigned, dt, speed=100):
        # try to assoc in a 2m radius: it means a relative speed of 128km/h
        state = []
        state_cov = []
        extent = []
        nu = []
        alpha = []
        beta = []
        
        init_cov=np.ndarray((self.d,self.d))
        na = np.nonzero(not_assigned>0)[0] # because an assigned marker can be 0 or -1!
        pna = np.nonzero(prev_not_assigned>0)[0]
        for i in na:
            delta = (pc[:,i]-prev_pc[:,pna].T).T
            idxs = np.sqrt(np.sum(delta**2,axis=0))
            # TODO: when the dt is big, the eps becomes huge: scores are negatives,
            # nan appears and a shitstorm falls 
            idxs = idxs<speed*dt
            idxs = np.nonzero(idxs)[0]
            #if len(idxs):
            for j in idxs:
                init_cov[:,:]=0
                tmp_c = np.eye((3*self.d))
                #scores = []
                #for k,j in enumerate(idxs):
                    #scores.append(np.exp(-(delta[:,j]).T.dot(np.linalg.inv(cov[:,:,i]+prev_cov[:,:,j])).dot(delta[:,j])))
                    #init_cov += scores[k]*prev_cov[:,:,j]     
                #init_cov = init_cov/(np.sum(scores)+10**-9)
                #scores = scores/(np.sum(scores)+10**-9)
                #init_cov = (pc[:,i]-prev_pc[:,j])
                #init_cov = np.outer(init_cov,init_cov)
                init_cov = 0.1*cov[:,:,i]+0.1*prev_cov[:,:,j]
                tmp =   [pc[0,i],\
                        (delta[0,j]/dt),0,\
                        pc[1,i],\
                        (delta[1,j]/dt),0]
                state.append(np.array(tmp))
                tmp_c[0,0] = init_cov[0,0]
                tmp_c[3,3] = init_cov[1,1]
                tmp_c[0,3] = init_cov[0,1]
                tmp_c[3,0] = init_cov[1,0]
                tmp_c = tmp_c+Q(dt,self.d,1)
                state_cov.append(tmp_c)
                extent.append(0.5*ext[:,:,i]+0.5*prev_ext[:,:,j]+np.eye(self.d))
                nu.append(card[i]+prev_card[j])
                alpha.append(card[i]+prev_card[j])
                beta.append(2)


        # Poisson
        if len(state)==0:
            self.regular_init()
        else:
            self.state_v_p = np.array(state).T
            self.state_c_p = np.moveaxis(np.array(state_cov),(-2,-1),(0,1))
            self.lambda_p = self.init_weight*np.ones(len(state))
            self.alpha_p = np.array(alpha).T
            self.beta_p = np.array(beta).T
            self.nu_p = np.array(nu).T
            self.Nu_p = np.moveaxis(np.array(extent),(-2,-1),(0,1))
            self.n_p = len(state)

        # Multi Bernoulli
        self.n_mb = 0
        self.r = np.ndarray(())
        self.state_v_mb = np.ndarray(())
        self.state_c_mb = np.ndarray(())
        self.alpha_mb = np.ndarray(())
        self.beta_mb = np.ndarray(())
        self.nu_mb = np.ndarray(())
        self.Nu_mb = np.ndarray(())
        self.labels = np.ndarray(())

    def prediction(self,p_s,F,eta,tau,T):
        eT=np.exp(-T/tau)
        if self.n_mb>0:
            self.r = p_s*self.r
            self.alpha_mb = self.alpha_mb/eta
            self.beta_mb = self.beta_mb/eta
            self.nu_mb = 2*self.d+3+eT*(self.nu_mb-2*self.d-2)
            self.nu_mb[self.nu_mb<7] = 7
            self.state_v_mb = F.dot(self.state_v_mb)
            for i in range(self.n_mb):
                self.state_c_mb[:,:,i] = F.dot(self.state_c_mb[:,:,i]).dot(F.T)+Q(T,self.d,0.5)
            self.Nu_mb = eT*self.Nu_mb

        if self.n_p>0:
            self.lambda_p = p_s*self.lambda_p 
            self.alpha_p = self.alpha_p/eta
            self.beta_p = self.beta_p/eta
            self.nu_p = 2*self.d+3+eT*(self.nu_p-2*self.d-2)
            self.nu_p[self.nu_p<7] = 7
            self.state_v_p = F.dot(self.state_v_p)
            for i in range(self.n_p):
                self.state_c_p[:,:,i] = F.dot(self.state_c_p[:,:,i]).dot(F.T)+Q(T,self.d,1)
            self.Nu_p = eT*self.Nu_p

    def correction_rm(self, scan, scan_ext, scan_cov, map_trcks, labels, n_labels, p_d, p_d_p, lambda_fa, F, H, R, t):

        # Regular Gaussian Part
        n_meas = scan.shape[1]
        n_mb = map_trcks.shape[0]
        w_tmp = np.zeros((n_mb+1,n_meas+1))
        r_tmp = np.zeros((n_mb+1,n_meas+1))
        state_v_tmp = np.ndarray((self.state_v_p.shape[0],n_mb+1,n_meas+1))
        state_c_tmp = np.ndarray((3*self.d,3*self.d,n_mb+1,n_meas+1))

        # Gamma Inverse Wishart Part
        alpha_tmp = np.ones((n_mb+1,n_meas+1)) #number of event expected
        beta_tmp = np.zeros((n_mb+1,n_meas+1)) #rate of events happening (Poisson)
        nu_tmp = np.zeros((n_mb+1,n_meas+1))
        Nu_tmp = np.ndarray((self.d,self.d,n_mb+1,n_meas+1))

        if n_mb>0:
            b=self.beta_mb[map_trcks]
            a=self.alpha_mb[map_trcks]

            q_d = (1-p_d)#+p_d*(b/(b+1))**(a) # beta is 0 if not extended and alpha is 1
            w_tmp[:-1,0] = (1-self.r[map_trcks]+self.r[map_trcks]*q_d)
            r_tmp[:-1,0] = (self.r[map_trcks]*q_d/w_tmp[:-1,0])
            state_v_tmp[:,:-1,0] = self.state_v_mb[:,map_trcks]
            state_c_tmp[:,:,:-1,0] = self.state_c_mb[:,:,map_trcks]
            nu_tmp[:-1,0] = self.nu_mb[map_trcks]
            Nu_tmp[:,:,:-1,0] = self.Nu_mb[:,:,map_trcks]
            alpha_tmp[:-1,0] = a
            w1 = (1-p_d)/q_d
            #w2 = p_d/q_d*((b)/(b+1))**a
            beta_tmp[:-1,0] = w1*b#+w2*b

            for i,I in enumerate(map_trcks):
                # Correction components
                # TODO: check if R can be replace by the cov returned by the sensor
#                S = self.H.dot(self.tgts.state_c_mb[:,:,i]).dot(self.H.T)+self.R
#                K = self.tgts.state_c_mb[:,:,i].dot(self.H.T).dot(np.linalg.inv(S))
#                P = self.tgts.state_c_mb[:,:,i]-K.dot(self.H).dot(self.tgts.state_c_mb[:,:,i])

                X = self.Nu_mb[:,:,I]/(self.nu_mb[I]-2*self.d-2)
                #confidence = (t-self.labels[0,I])
                for j in range(n_meas):
                    # Chaque mesures TODO: triple check
                    #print("state_c_mb",self.state_c_mb[:,:,i])
                    cardinal = np.sum(labels==j)
                    if cardinal==0: cardinal = 1
                    #if cardinal==0:
                    #    cardinal=1
                    #if (scan_cov[:,:,j]/confidence>R).all():
                    #    S = H.dot(self.state_c_mb[:,:,I]).dot(H.T)+scan_cov[:,:,j]/(confidence*cardinal)#+R
                    #else:
                    #    S = H.dot(self.state_c_mb[:,:,I]).dot(H.T)+R

                    nu = scan[:,j]-H.dot(self.state_v_mb[:,I])

                    #if cardinal > 1:
                    #    S =  H.dot(self.state_c_mb[:,:,I]).dot(H.T) + X/cardinal
                    #else:
                    S = H.dot(self.state_c_mb[:,:,I]).dot(H.T)+ X/cardinal + R #+scan_cov[:,:,j] #/confidence
                    
                    K = self.state_c_mb[:,:,I].dot(H.T).dot(np.linalg.inv(S))

                    N = matSqrt(X).dot(matSqrt(np.linalg.inv(S)))
                    N = N.dot(np.outer(nu,nu)).dot(N.T)

                    #if cardinal>1:
                    #    nu_tmp[i,j+1] = self.nu[I]+cardinal
                    #    Nu_tmp [:,:,i,j+1] = self.Nu[:,:,I] + scan_cov[:,:,j] + N
                    #else:
                    nu_tmp[i,j+1] = self.nu_mb[I]+cardinal
                    Nu_tmp[:,:,i,j+1] = self.Nu_mb[:,:,I] + scan_ext[:,:,j] + N

                    #print("K",K)
                    state_c_tmp[:,:,i,j+1] = self.state_c_mb[:,:,I]-K.dot(H).dot(self.state_c_mb[:,:,I])
                    
                   #print("error=",nu)

                   #print("w_tmp",w_tmp[i,j+1])
                   #print("r",self.r[i])
                    r_tmp[i,j+1] = 1
                    #print("state_v_mb", self.state_v_mb[:,i])
                    state_v_tmp[:,i,j+1] = self.state_v_mb[:,I]+K.dot(nu)
                    #print("state_v_tmp",state_v_tmp[:,i,j+1])
                    alpha_tmp[i,j+1] = self.alpha_mb[I] + cardinal
                    beta_tmp[i,j+1] = self.beta_mb[I]+1

                    likelihood = ((np.pi)**cardinal*cardinal)**-1

                    #print('Nu_tmp = ')
                    #print(Nu_tmp[:,:,i,j+1])
                    #print('nu_tmp = ')
                    #print(nu_tmp[i,j+1])
                    likelihood = likelihood*np.linalg.det(self.Nu_mb[:,:,I])**((self.nu_mb[I]-self.d-1)/2)

                    likelihood = likelihood/(np.linalg.det(Nu_tmp[:,:,i,j+1])**((nu_tmp[i,j+1]-self.d-1)/2))

                    likelihood = likelihood*np.linalg.det(X)**0.5

                    likelihood = likelihood/np.linalg.det(S)**0.5

                    likelihood = likelihood*multigamma((nu_tmp[i,j+1]-self.d-1)/2,self.d)

                    likelihood = likelihood/multigamma((self.nu_mb[I]-self.d-1)/2,self.d)

                    likelihood = likelihood*multigamma(alpha_tmp[i,j+1],1)*self.beta_mb[I]**self.alpha_mb[I]

                    likelihood = likelihood/(multigamma(self.alpha_mb[I],1)*beta_tmp[i,j+1]**alpha_tmp[i,j+1])

                    #likelihood = likelihood/np.trace(np.outer(nu,nu))
                    #w_tmp[i,j+1] = self.r[I]*p_d[i]*likelihood
                    w_tmp[i,j+1] = self.r[I]*p_d[i]*gaussian(nu,np.zeros(self.d),S)

                    ##if (np.abs(nu)<20).all():#when it is absorbed into the extended measurment, it disappear...
                       ##print("------------ label ------------", self.labels[:,I])
                       ##print("nu",nu)
                       ##print("likelihood", likelihood)
                       ##print("w_tmp ", w_tmp[i,j+1])
                       ##print("alpha_tmp ", alpha_tmp[i,j+1])
                       ##print("beta_tmp ", beta_tmp[i,j+1])
                       ##print("w_tmp ", w_tmp[i,j+1])
                       ##print("cov_tmp ",state_c_tmp[:,:,i,j+1])
                       ##print("alpha ", self.alpha_mb[I])
                       ##print("beta ", self.beta_mb[I])
                       ##print("cov ",self.state_c_mb[:,:,I])


                    #if likelihood>10**-20:
                    #    print("Likelihood before trick mb:",likelihood)
                    #    likelihood = likelihood*np.trace(scan_cov[:,:,j])/np.trace(np.outer(nu,nu))
                    #    print("likelihood after trick mb", likelihood)

                #print("w_tmp",w_tmp[i,:])
                #### this is the missed detection hypothesis normalization trick.
                #### we just need to set missed detection hypothesis a bit higher
                #### than detection hypothesis in order to correct it during LBP,
                #### then we get a correct marginal probability!
                expo = np.max(np.log10(w_tmp[i,1:]+MINI_FLOAT))
                if expo>-8 and expo<-1:
                    w_tmp[i,0] = w_tmp[i,0]*10**(expo+1)

        # if self.tgts.n_p>0: -> at least 1, we keep one or two secret poisson hyp in 
        # Correction components for undetected self.tgts
        P        = np.ndarray((3*self.d,3*self.d,self.n_p))
        Nu       = np.ndarray((self.d,self.d,self.n_p))
        nu       = np.ndarray((self.n_p))
        alpha    = np.ndarray((self.n_p))
        beta     = np.ndarray((self.n_p))
        poiss_id = np.zeros((n_meas),dtype=int)

        #for k in range(self.n_p):

            #print("trace poisson=",np.trace(self.state_c_p[:,:,k]))

        for j in range(n_meas):
            c = np.zeros((self.n_p))
            y = np.ndarray((self.state_v_p.shape[0],self.n_p))
            cardinal = np.sum(labels==j)
            if cardinal == 0 : cardinal = 1
            #if cardinal==0:
            #    cardinal=1

            alpha = self.alpha_p+cardinal
            beta = self.beta_p+1
            cmax = 0
            for k in range(self.n_p):
                X = self.Nu_p[:,:,k]/(self.nu_p[k]-2*self.d-2)
                epsilon = scan[:,j]-H.dot(self.state_v_p[:,k])
                #if cardinal>1:
                #    S[:,:,k] = H.dot(self.state_c_p[:,:,k]).dot(H.T) + X/cardinal
                #else:
                S = H.dot(self.state_c_p[:,:,k]).dot(H.T) + X/cardinal + R#+ scan_cov[:,:,j] # eye?
                K = self.state_c_p[:,:,k].dot(H.T).dot(np.linalg.inv(S))


                #if cardinal>1:
                nu[k] = self.nu_p[k]+cardinal
                N = matSqrt(X).dot(matSqrt(np.linalg.inv(S)))
                N = N.dot(np.outer(epsilon,epsilon).T).dot(N.T)
                Nu[:,:,k] = self.Nu_p[:,:,k] + scan_ext[:,:,j] + N
                #else:
                #    Nu[:,:,k] = self.Nu_p[:,:,k]

            
                likelihood = ((np.pi)**cardinal*cardinal)**-1
                likelihood = likelihood*np.linalg.det(self.Nu_p[:,:,k])**((self.nu_p[k]-self.d-1)/2)
                likelihood = likelihood/(np.linalg.det(Nu[:,:,k])**((nu[k]-self.d-1)/2))
                likelihood = likelihood*np.linalg.det(X)**0.5
                likelihood = likelihood/np.linalg.det(S)**0.5
                likelihood = likelihood*multigamma((nu[k]-self.d-1)/2,self.d)
                likelihood = likelihood/multigamma((self.nu_p[k]-self.d-1)/2,self.d)
                likelihood = likelihood*multigamma(alpha[k],1)*self.beta_p[k]**self.alpha_p[k]
                likelihood = likelihood/(multigamma(self.alpha_p[k],1)*beta[k]**alpha[k])
                P[:,:,k] = self.state_c_p[:,:,k]-K.dot(H).dot(self.state_c_p[:,:,k])
                #likelihood = likelihood/np.trace(np.outer(epsilon,epsilon))
                #c[k] = self.lambda_p[k]*p_d_p*likelihood
                c[k] = self.lambda_p[k]*p_d_p*gaussian(epsilon,np.zeros(self.d),S)
                #if likelihood>10**-20:
                #    print("likelihood before trick p", likelihood)
                #    likelihood = likelihood*np.trace(scan_cov[:,:,j])/np.trace(np.outer(epsilon,epsilon))
                #    print("likelihood after trick p", likelihood)
                y[:,k] = self.state_v_p[:,k]+K.dot(epsilon)
                if cmax<c[k]:
                    cmax = c[k]
                    poiss_id[j] = k
                ##if (np.abs(epsilon)<20).all():#when it is absorbed into the extended measurment, it disappear...
                   ##print("------------ Poisson small epsilon ------------")
                   ##print("epsilon",epsilon)
                   ##print("likelihood", likelihood)
                   ##print("cardinal", cardinal)
                ##elif likelihood>10**-20 and False:
                   ##print("------------ Poisson big likelihood ------------")
                   ##print("epsilon",epsilon)
                   ##print("likelihood", likelihood)
                   ##print("cardinal", cardinal)

            c=c+MINI_FLOAT
            #c = c[poiss_id[j]]+MINI_FLOAT
            C=np.sum(c)#Lc
            w_tmp[-1,j] = C+lambda_fa
            #if cardinal>3:
            #    r_tmp[-1,j] = 1
            #else:
            r_tmp[-1,j] = C/w_tmp[-1,j]
            # todo: trick
            nu_tmp[-1,j] = np.sum(c*nu)/C
            alpha_tmp[-1,j] = np.sum(c*alpha)/C
            beta_tmp[-1,j] = np.sum(c*beta)/C

            state_v_tmp[:,-1,j] = np.sum(np.outer(np.ones((3*self.d)),c)*y,axis=1)/C
            #state_v_tmp[:,-1,j] = (y[:,poiss_id[j]])
            tmp = np.zeros((state_c_tmp.shape[:2]))
            tmp2 = np.zeros((Nu_tmp.shape[:2]))

            for k in range(self.n_p):
                tmp += c[k]*(P[:,:,k]+np.outer(state_v_tmp[:,-1,j]-y[:,k],state_v_tmp[:,-1,j]-y[:,k]))
                tmp2+= c[k]*(Nu[:,:,k])
            state_c_tmp[:,:,-1,j] = tmp/C
            Nu_tmp[:,:,-1,j] = tmp2/C

        self.lambda_p = (1-p_d_p)*self.lambda_p

        return w_tmp, r_tmp, state_v_tmp, state_c_tmp, alpha_tmp, beta_tmp, nu_tmp, Nu_tmp, poiss_id



class PMBM_RM(QThread):

            
    #Messagerie     
    message         = pyqtSignal('QString')    
    #list des pistes 
    updatedTracks   = pyqtSignal(list) 

    # Type 0 is the ETGMPHD 
    def __init__(self, parent=None):
        self.d = 2 # Dimension de l'extension
        self.t = 0.05 # acquisition interval in second
        self.theta = 5 # coherence time of a vehicle maneuver in second
        self.acc_rms = 0.1 # scalar acceleration value in g
        self.p_d = 0.98 # detection probability
        self.p_s = 0.95 # survival probability
        self.sigma_p = np.array((0.9,1.1,1.1))*np.eye(3)
        self.sigma_c = 2
        self.lambda_fa = 0.05
        self.D = np.zeros([3,3])
        self.D[2,2] = self.acc_rms**2*(1-np.exp(-2*self.t/self.theta))
        self.H = np.zeros([1,3], dtype=float)
        self.H[0,0] = 1
        self.H = np.kron(np.identity(self.d),self.H)
        #self.Q = self.sigma_p**2*np.identity(3*self.d, dtype=float)
        self.Q = np.kron(np.eye(self.d),self.sigma_p**2)
        self.R = self.sigma_c**2*np.identity(2, dtype=float)
        self.F = np.ndarray((3*self.d,3*self.d))
        self.timestamp = 0

        self.tau = 3 # seconds
        self.eta = 10 # measurement rate: how many good meas for how many missed meas
    
        QThread.__init__(self, parent)    
        self.tracks  = []
        self.scan    = None
        self.time = QDateTime()

        
        self.prev_scan = np.ndarray(())
        self.prev_cov = np.ndarray(())
        self.prev_not_assigned = np.zeros((1),dtype=int)
        self.prev_ext = np.ndarray(())
        self.prev_card = np.ndarray(())
        self.targets = []
        self.tgts = Tgts()
        

    def prediction(self,ptgts):

        self.tgts.prediction(self.p_s,self.F, self.eta, self.tau, self.t)
        
        ptgts.prediction(self.p_s,self.F, self.eta, self.tau, self.t)

        if ptgts.n_p:
            self.tgts.lambda_p = np.concatenate([self.tgts.lambda_p, ptgts.lambda_p])
            self.tgts.state_v_p = np.concatenate([self.tgts.state_v_p, ptgts.state_v_p],axis=1)
            self.tgts.state_c_p = np.concatenate([self.tgts.state_c_p, ptgts.state_c_p],axis=2)
            self.tgts.alpha_p = np.concatenate([self.tgts.alpha_p, ptgts.alpha_p])
            self.tgts.beta_p = np.concatenate([self.tgts.beta_p, ptgts.beta_p])
            self.tgts.nu_p = np.concatenate([self.tgts.nu_p, ptgts.nu_p])
            self.tgts.Nu_p = np.concatenate([self.tgts.Nu_p, ptgts.Nu_p],axis=2)
            self.tgts.n_p += ptgts.n_p

    def correction(self, scan, scan_cov,ftype=1):
        # First we correct the identified tgts
        # Starting with the missed detection hypothesis
        n_meas = scan.shape[1]
        n_tracks = self.tgts.n_mb
        if n_tracks>0 and ftype==1:
            gatedMeas = self.gatingKirubarajan(scan)
        else:
            gatedMeas = np.ndarray(())

        if n_tracks>0 and ftype==1:
            all_meas = np.zeros(n_meas,dtype=int)
            Windows=[]
            while (all_meas==0).any():
                meas = np.zeros(n_meas,dtype=int)
                trck = np.zeros(n_tracks,dtype=int)
                j = np.where(all_meas==0)[0][0]
                #check find window
                meas,trck = findWindow(gatedMeas,j,meas,trck)
                all_meas = meas | all_meas
                Windows.append([trck,meas])
                # not TODO: Windows.append([np.unique(trck),np.unique(meas)])

            
            residual_bernoullis = np.ones(n_tracks,dtype=int)
            not_assigned = np.ndarray((0),dtype=int)
            poiss_id  = np.ndarray((0),dtype=int)
            scan2     = np.ndarray((self.d,0))
            scan_cov2 = np.ndarray((self.d,self.d,0))
            scan_ext2 = np.ndarray((self.d,self.d,0))
            card2     = np.ndarray((0),dtype=int)
            offset = 0
            for window in Windows:
                map_meas = np.nonzero(window[1])[0]
                map_trcks = np.nonzero(window[0])[0]
                residual_bernoullis[map_trcks] = 0
                nt=map_trcks.shape[0]

                #TODO: DBSCAN?
                labels, n_labels = cluster(scan[:,map_meas])
                nm = n_labels+np.sum(labels==-1)
                meas = np.ndarray((self.d,nm))
                ext_meas = np.zeros((self.d,self.d,nm))
                cov_meas = np.zeros((self.d,self.d,nm))
                card = np.ones(nm)
                for j in range(n_labels):
                    meas[:,j] = np.mean(scan[:,map_meas[labels==j]], axis = 1)
                    card[j] = np.sum(labels==j)
                    for j1 in map_meas[labels==j]:
                        ext_meas[:,:,j] = ext_meas[:,:,j] + np.outer(scan[:,j1]-meas[:,j],scan[:,j1]-meas[:,j])
                        cov_meas[:,:,j] = cov_meas[:,:,j] + scan_cov[:,:,j1]
                    cov_meas = cov_meas/card[j]
                solo_meas = np.where(labels==-1)[0]
                for j,j1 in enumerate(map_meas[solo_meas]):
                    meas[:,j+n_labels] = scan[:,j1]
                    cov_meas[:,:,j+n_labels] = scan_cov[:,:,j1]
                    ext_meas[:,:,j+n_labels] = np.eye(self.d)
                
                #ind_ext = np.nonzero(self.tgts.nu_mb[map_trcks]>7)[0]
                #ind_ext = map_trcks[ind_ext]
                #if ind_ext.shape[0]:
                #p_d = (1-self.p_d)*np.ones(nt)
                    # Watch out
                #    p_d[ind_ext] = (self.p_d)/ind_ext.shape[0]
                #else:
                
                p_d = (self.p_d)*np.ones(nt)
                if nt:
                    norm = np.ndarray(nt)
                    for i,I in enumerate(map_trcks):
                        norm[i] = frobNorm(self.tgts.Nu_mb[:,:,I])
                    normax=np.max(norm)
                    p_d = p_d*(1-(normax-norm)/normax)
                
                w, r, state_v, state_c, alpha, beta, nu, Nu, poiss_tmp = self.tgts.correction_rm(meas, ext_meas, cov_meas, map_trcks, labels, n_labels, p_d, self.p_d, self.lambda_fa, self.F, self.H, self.R, self.timestamp)

                poiss_id  = np.concatenate((poiss_id,poiss_tmp))
                scan2     = np.concatenate((scan2,meas),axis=1)
                scan_cov2 = np.concatenate((scan_cov2,cov_meas),axis=2)
                scan_ext2 = np.concatenate((scan_ext2,ext_meas),axis=2)
                card2     = np.concatenate((card2,card))

                marg_prob = self.LBP2(w,nm)

                na = self.small_munk_assignement(marg_prob, r, state_v, state_c, alpha, beta, nu, Nu, map_trcks, nm)

                offset += self.concatenateMultiBern( na, offset, r, state_v, state_c, alpha, beta, nu, Nu)

                not_assigned = np.concatenate((not_assigned,na))


            for i in np.nonzero(residual_bernoullis)[0]:
                #print("label non gated meas", self.tgts.labels[:,map_trcks[i]])
                self.tgts.r[i] = self.tgts.r[i]*(1-self.p_d)/(1-self.tgts.r[i]+self.tgts.r[i]*(1-self.p_d))
            
            n_old_tracks = self.tgts.n_mb
            self.tgts.n_mb = len(self.tgts.r)

            if self.tgts.n_mb:
                for i in range(self.tgts.n_mb):
                    self.Target2Track(i,n_old_tracks)

        else:

            labels, n_labels = cluster(scan)
            nm = n_labels+np.sum(labels==-1)
            nt = self.tgts.n_mb
            scan2     = np.ndarray((self.d,nm))
            scan_cov2 = np.zeros((self.d,self.d,nm))
            scan_ext2 = np.zeros((self.d,self.d,nm))
            card2 = np.ones(nm)
            for j in range(n_labels):
                scan2[:,j] = np.mean(scan[:,labels==j], axis = 1)
                card2[j] = np.sum(labels==j)
                for j1 in np.where(labels==j)[0]:
                    scan_ext2[:,:,j] = scan_ext2[:,:,j] + np.outer(scan[:,j1]-scan2[:,j],scan[:,j1]-scan2[:,j])
                    scan_cov2[:,:,j] = scan_cov2[:,:,j] + scan_cov[:,:,j1]
                scan_cov2 = scan_cov2/np.sum(labels==j)
            solo_meas = np.where(labels==-1)[0]
            for j,j1 in enumerate(solo_meas):
                scan2[:,j+n_labels] = scan[:,j1]
                scan_cov2[:,:,j+n_labels] = scan_cov[:,:,j1]
                scan_ext2[:,:,j+n_labels] = np.eye(self.d)

            map_trcks = np.arange(nt,dtype=int)
            p_d = (self.p_d)*np.ones(nt)

            w, r, state_v, state_c, alpha, beta, nu, Nu, poiss_id = self.tgts.correction_rm(scan2, scan_ext2, scan_cov2, map_trcks , labels, n_labels, p_d, self.p_d, self.lambda_fa, self.F, self.H, self.R, self.timestamp)

            marg_prob2 = self.LBP2(w, nm)

            not_assigned = self.small_munk_assignement(marg_prob2, r, state_v, state_c, alpha, beta, nu, Nu, map_trcks, nm)

            self.tgts.n_mb += self.concatenateMultiBern( not_assigned, 0, r, state_v, state_c, alpha, beta, nu, Nu)
            

            if self.tgts.n_mb:
                for i in range(self.tgts.n_mb):
                    self.Target2Track(i,nt)

        #self.TOMBP(self.tgts, marg_prob, r_tmp, state_v_tmp, state_c_tmp,n_meas)

        return not_assigned, poiss_id, scan2, scan_cov2, scan_ext2, card2

# Using Munkres assignment algorithm, we match measurment with self.tgts. 
# Hence if needed, a new Bernoulli is created.
# Finally, the not assined clusters are marked so we can get reed of used Poisson
# hypothesis while creating new ones where clusters were undetected!

    def small_munk_assignement(self, marg_prob, r, state_v, state_c, alpha_tmp, beta_tmp, nu_tmp, Nu_tmp, map_trcks, n_meas):
#        if map_meas.shape[0]==0:
#            map_meas = np.arange(n_meas)
#            map_trcks = np.arange(n_tracks)
        n_tracks = map_trcks.shape[0]

        not_assigned = np.ones(n_meas)

        tmp = np.copy(marg_prob[:,1:])
        tmp[:n_tracks,:] = tmp[:n_tracks,:]/np.outer(marg_prob[:n_tracks,0]+MINI_FLOAT,np.ones(n_meas))
        tmp = tmp+MINI_FLOAT
        ind_lines, ind_cols = linear_sum_assignment(-np.log(tmp))

        nd_mb = np.ones((n_tracks),dtype=int)

        for k in range(len(ind_lines)):
            i=ind_lines[k]
            j=ind_cols[k]
            if i<n_tracks:
                print('marj_prob non detection:',marg_prob[i,0])
                print("marj_prob detection : ", marg_prob[i,j+1])
                print("label", self.tgts.labels[:,map_trcks[i]])
                if marg_prob[i,0]<marg_prob[i,j+1]:
                    nd_mb[i]=0
                    not_assigned[j] = 0 # here the jth meas is assigned
                    self.tgts.r[map_trcks[i]] = marg_prob[i,j+1]*r[i,j+1]
                    self.tgts.state_v_mb[:,map_trcks[i]] = state_v[:,i,j+1]
                    self.tgts.state_c_mb[:,:,map_trcks[i]] = state_c[:,:,i,j+1]
                    self.tgts.alpha_mb[map_trcks[i]] = alpha_tmp[i,j+1]
                    self.tgts.beta_mb[map_trcks[i]] = beta_tmp[i,j+1]
                    self.tgts.nu_mb[map_trcks[i]] = nu_tmp[i,j+1]
                    self.tgts.Nu_mb[:,:,map_trcks[i]] = Nu_tmp[:,:,i,j+1]
            else:
                r[-1,j] = r[-1,j]*marg_prob[i,j+1]
                if r[-1,j]>0.05:
                    not_assigned[j] = -1 # Here the jth meas is assigned. However we should say "this is a poisson that took it" -> -1 is assigned

        nd_mb = np.nonzero(nd_mb)[0]
        
        for i in nd_mb:
           #print("not detected track",map_trcks[i])
            print("marj_prob non detection : ", marg_prob[i,0])
            print("label", self.tgts.labels[:,map_trcks[i]])
            self.tgts.r[map_trcks[i]] = marg_prob[i,0]*r[i,0]
            self.tgts.state_v_mb[:,map_trcks[i]] = state_v[:,i,0]
            self.tgts.state_c_mb[:,:,map_trcks[i]] = state_c[:,:,i,0]
            self.tgts.alpha_mb[map_trcks[i]] = alpha_tmp[i,0]
            self.tgts.beta_mb[map_trcks[i]] = beta_tmp[i,0]
            self.tgts.nu_mb[map_trcks[i]] = nu_tmp[i,0]
            self.tgts.Nu_mb[:,:,map_trcks[i]] = Nu_tmp[:,:,i,0]

        return not_assigned

    def concatenateMultiBern(self, not_assigned, offset, r, state_v, state_c, alpha, beta, nu, Nu):
        
        ind = np.where(not_assigned==-1)[0]

        if len(self.tgts.r)>0 and len(ind):
            self.tgts.r = np.concatenate((self.tgts.r,r[-1,ind]))
            self.tgts.state_v_mb = np.concatenate((self.tgts.state_v_mb,state_v[:,-1,ind]),axis=1)
            self.tgts.state_c_mb = np.concatenate((self.tgts.state_c_mb,state_c[:,:,-1,ind]),axis=2)
            #self.tgts.n_mb += len(ind)
            self.tgts.alpha_mb = np.concatenate((self.tgts.alpha_mb,alpha[-1,ind]))
            self.tgts.beta_mb = np.concatenate((self.tgts.beta_mb,beta[-1,ind]))
            self.tgts.nu_mb = np.concatenate((self.tgts.nu_mb,nu[-1,ind]))
            self.tgts.Nu_mb = np.concatenate((self.tgts.Nu_mb,Nu[:,:,-1,ind]),axis=2)
            new_labels = np.array((self.timestamp*np.ones(len(ind)),np.arange(offset,offset+len(ind))),dtype=int)
            self.tgts.labels = np.concatenate((self.tgts.labels,new_labels),axis=1)
            self.tracks_map = np.concatenate((self.tracks_map,np.ndarray(len(ind),dtype=int)))
        elif len(ind):
            self.tgts.r = r[-1,ind]
            self.tgts.state_v_mb = state_v[:,-1,ind]
            self.tgts.state_c_mb = state_c[:,:,-1,ind]
            self.tgts.alpha_mb =alpha[-1,ind]
            self.tgts.beta_mb = beta[-1,ind]
            self.tgts.nu_mb = nu[-1,ind]
            self.tgts.Nu_mb = Nu[:,:,-1,ind]
            #self.tgts.n_mb = len(ind)
            self.tgts.labels = np.array((self.timestamp*np.ones(len(ind)),np.arange(len(ind))),dtype=int)
            self.tracks_map = np.ndarray(len(ind),dtype=int)

        return len(ind)

    def munk_assignement(self, marg_prob, r, state_v, state_c, n_meas):
        # TODO: solve linear assignement problems
        # TODO: use murty's algorithm to obtain 1st, 2nd and 3rd best association hypothesis
#        if map_meas.shape[0]==0:
#            map_meas = np.arange(n_meas)
#            map_trcks = np.arange(n_tracks)

        tmp = np.copy(marg_prob[:,1:])
        tmp[:self.tgts.n_mb,:] = tmp[:self.tgts.n_mb,:]/np.outer(marg_prob[:self.tgts.n_mb,0]+MINI_FLOAT,np.ones(n_meas))
        tmp = tmp+MINI_FLOAT
        ind_lines, ind_cols = linear_sum_assignment(-np.log(tmp))
        not_assigned = np.ones((n_meas),dtype=int)
        nd_mb = np.ones((self.tgts.n_mb),dtype=int)
       #print("r before = ",self.tgts.r)
        for k in range(len(ind_lines)):
            i=ind_lines[k]
            j=ind_cols[k]
            if i<self.tgts.n_mb:
                if marg_prob[i,0]<marg_prob[i,j+1]:
                    nd_mb[i]=0
                    not_assigned[j] = 0 # here the jth meas is assigned
                    self.tgts.r[i] = marg_prob[i,j+1]*r[i,j+1]
                    self.tgts.state_v_mb[:,i] = state_v[:,i,j+1]
                    self.tgts.state_c_mb[:,:,i] = state_c[:,:,i,j+1]
                   #print("w_tmp selected", w_tmp[i,j+1])
                   #print("marg_prob selected", marg_prob[i,:])
            else:
                r[-1,j] = r[-1,j]*marg_prob[i,j+1]
                if r[-1,j]>0.1:
                    not_assigned[j] = -1 # Here the jth meas is assigned. However we should say "this is a poisson that took it" -> -1 is assigned

        nd_mb = np.nonzero(nd_mb)[0]
        n_old_tracks = self.tgts.n_mb
        for i in nd_mb:
            self.tgts.r[i] = marg_prob[i,0]*r[i,0]
            self.tgts.state_v_mb[:,i] = state_v[:,i,0]
            self.tgts.state_c_mb[:,:,i] = state_c[:,:,i,0]
       #print("r after = ", self.tgts.r)
        ind = np.where(not_assigned==-1)[0]

        if self.tgts.n_mb>0 and len(ind):
            self.tgts.r = np.concatenate((self.tgts.r,r[-1,ind]))
            self.tgts.state_v_mb = np.concatenate((self.tgts.state_v_mb,state_v[:,-1,ind]),axis=1)
            self.tgts.state_c_mb = np.concatenate((self.tgts.state_c_mb,state_c[:,:,-1,ind]),axis=2)
            self.tgts.n_mb += len(ind)
            new_labels = np.array((self.timestamp*np.ones(len(ind)),np.arange(len(ind))),dtype=int)
            self.tgts.labels = np.concatenate((self.tgts.labels,new_labels),axis=1)
            self.tracks_map = np.concatenate((self.tracks_map,np.ndarray(len(ind),dtype=int)))
        elif len(ind):
            self.tgts.r = (r[-1,ind])
            self.tgts.state_v_mb = (state_v[:,-1,ind])
            self.tgts.state_c_mb = (state_c[:,:,-1,ind])
            self.tgts.n_mb = len(ind)
            self.tgts.labels = np.array((self.timestamp*np.ones(len(ind)),np.arange(len(ind))),dtype=int)
            self.tracks_map = np.ndarray(len(ind),dtype=int)

        if self.tgts.n_mb:
            for i in range(self.tgts.n_mb):
                self.Target2Track(i,n_old_tracks)

        return not_assigned

    def gatingKirubarajan(self,scan, vmax=100):
        # Kirubarajan style gating
        thresh_x = self.t*vmax+2*np.sqrt(self.tgts.state_c_mb[0,0,:])

        thresh_y = self.t*vmax+2*np.sqrt(self.tgts.state_c_mb[3,3,:])

        thresh = np.concatenate((thresh_x,thresh_y)).reshape((2,self.tgts.n_mb))

        X = self.tgts.state_v_mb[0:4:3,:]

        res = np.zeros((self.tgts.n_mb,scan.shape[1]),dtype=int)

        for k in range(scan.shape[1]):
            Z = np.outer(scan[:,k],np.ones(self.tgts.n_mb))
            tmp = Z-X <= thresh
            res[:,k] = tmp[0,:] & tmp[1,:]

        return res


    # The threshold policy is a part of the filter:
    # it is not just about getting rid of weak Poisson hypothesis,
    # it is also about getting rid of Poisson hypothesis turned into
    # Bernoulli hypothesis AND getting rid of weak Poisson hypothesis.
    # What is important is the way the threshold is defined: an hypothesis
    # is allowed to live during three iterations of the algorithm, so:
    # threshold = self.tgts.init_weight * filter.p_s^2 * (1-filter.p_d)^3,
    # this way after three iterations, unassociated hypothesis are discarded.
    def threshold(self, not_assigned, poiss_id, survival = 3):
        # Discard assigned Poisson Hypothesis:
        #    poiss_id link a poisson comp k with a meas j:
        #    if this poisson k successfully created a bernoulli i with meas j,
        #    discard k!

        ind = poiss_id[not_assigned==-1]

        # Insure unicity:
        ind = np.unique(ind)
        self.tgts.lambda_p[ind] = 0

        # Discard low weight Poisson Hypothesis:
        threshold = self.tgts.init_weight*self.p_s**(survival-1)*(1-self.p_d)**(survival)
        ind = np.where(self.tgts.lambda_p>threshold)[0]

        # Clean up:
        self.tgts.state_v_p = self.tgts.state_v_p[:,ind]
        self.tgts.state_c_p = self.tgts.state_c_p[:,:,ind]
        self.tgts.lambda_p = self.tgts.lambda_p[ind]
        self.tgts.alpha_p = self.tgts.alpha_p[ind]
        self.tgts.beta_p = self.tgts.beta_p[ind]
        self.tgts.nu_p = self.tgts.nu_p[ind]
        self.tgts.Nu_p = self.tgts.Nu_p[:,:,ind]
        
        self.tgts.n_p = len(ind)

        # Clean Multi Bernoulli:
        if self.tgts.n_mb>0: # TODO: recycling
            ind = np.where(self.tgts.r<0.05)[0]
            if len(ind):
                self.tgts.state_c_mb[:,:,ind] = 4*self.tgts.state_c_mb[:,:,ind]
                #self.tgts.r[ind] = self.tgts.r[ind]/self.tgts.r[ind]
            ind = np.where(self.tgts.r>threshold/2)[0]
            self.tgts.state_v_mb = self.tgts.state_v_mb[:,ind]
            self.tgts.state_c_mb = self.tgts.state_c_mb[:,:,ind]
            self.tgts.r = self.tgts.r[ind]
            self.tgts.alpha_mb = self.tgts.alpha_mb[ind]
            self.tgts.beta_mb = self.tgts.beta_mb[ind]
            self.tgts.nu_mb = self.tgts.nu_mb[ind]
            self.tgts.Nu_mb = self.tgts.Nu_mb[:,:,ind]
            self.tgts.labels = self.tgts.labels[:,ind]
            self.tracks_map = self.tracks_map[ind]
            self.tgts.n_mb = len(ind)


    def LBP2(self, w_tmp, n_meas, eps=0.01):
        n_tracks = w_tmp.shape[0]-1
        mu_ba = np.ones((n_tracks, n_meas), dtype=float)
        mu_bat = np.zeros((n_tracks, n_meas), dtype=float)
        mu_ab = np.zeros((n_tracks, n_meas), dtype=float)
        marg_prob = np.zeros((n_tracks+n_meas, 1+n_meas), dtype=float)
        if n_tracks>0:

            while np.max(np.abs(mu_ba-mu_bat))>eps:
                mu_bat = np.copy(mu_ba)
                for i in range(n_tracks):
                    s = w_tmp[i,0]+np.sum(w_tmp[i,1:]*mu_ba[i,:])
                    mu_ab[i,:] = w_tmp[i,1:]/(s-w_tmp[i,1:]*mu_ba[i,:])
                for j in range(n_meas):
                    s= w_tmp[-1,j] + np.sum(mu_ab[:,j])
                    mu_ba[:,j] = 1/(s-mu_ab[:,j])

            for i in range(n_tracks):
                s = w_tmp[i,0]+np.sum(w_tmp[i,1:]*mu_ba[i,:])
                marg_prob[i,0] = w_tmp[i,0]/s
                marg_prob[i,1:] = w_tmp[i,1:]*mu_ba[i,:]/s

        for j in range(n_meas):
            s = w_tmp[-1,j]+np.sum(mu_ab[:,j])
            marg_prob[n_tracks+j,1+j]=w_tmp[-1,j]/s
        #marg_prob[marg_prob>1]=1
        return marg_prob

    def LBP(self, w_tmp, n_meas, eps=0.001):
        mu_ba = np.ones((self.tgts.n_mb, n_meas), dtype=float)
        mu_bat = np.zeros((self.tgts.n_mb, n_meas), dtype=float)
        mu_ab = np.ndarray((self.tgts.n_mb, n_meas), dtype=float)
        marg_prob = np.zeros((self.tgts.n_mb+1, n_meas+1), dtype=float)
        if self.tgts.n_mb>0:
            while np.max(np.abs(mu_ba-mu_bat))>eps:
                mu_bat = np.copy(mu_ba)
            
                for i in range(self.tgts.n_mb):
                    s = w_tmp[i,0]+np.sum(w_tmp[i,1:]*mu_ba[i,:])
                    mu_ab[i,:] = w_tmp[i,1:]/(s-w_tmp[i,1:]*mu_ba[i,:])
                for j in range(n_meas):
                    s= w_tmp[-1,j] + np.sum(mu_ab[:,j])
                    mu_ba[:,j] = 1/(s-mu_ab[:,j])
            
            for i in range(self.tgts.n_mb):
                s = w_tmp[i,0]+np.sum(w_tmp[i,1:]*mu_ba[i,:])
                marg_prob[i,0] = w_tmp[i,0]/s
                marg_prob[i,1:] = w_tmp[i,1:]*mu_ba[i,:]/s
        
            for j in range(n_meas):
                s = w_tmp[-1,j]+np.sum(mu_ab[:,j])
                marg_prob[-1,j]=w_tmp[-1,j]/s

        return marg_prob

    def TOMBP(self, marg_prob, r, state_v, state_c, n_meas):
        for i in range(self.tgts.n_mb):
            self.tgts.r[i] = np.sum(marg_prob[i,:]*r[i,:])
            tmp = np.outer(np.ones((state_v.shape[0])),marg_prob[i,:]*r[i,:])
            self.tgts.state_v_mb[:,i] = np.sum(tmp*state_v[:,i,:], axis=1)/self.tgts.r[i]
            self.tgts.state_c_mb[:,:,i] = 0
            for j in range(n_meas+1):
                tmp = np.outer(self.tgts.state_v_mb[:,i]-state_v[:,i,j],self.tgts.state_v_mb[:,i]-state_v[:,i,j])
                self.tgts.state_c_mb[:,:,i] += (marg_prob[i,j]*r[i,j])*(state_c[:,:,i,j]+tmp)
            self.tgts.state_c_mb[:,:,i] = self.tgts.state_c_mb[:,:,i]/self.tgts.r[i]
        r[-1,:-1] = r[-1,:-1]*marg_prob[-1,:-1]
        if self.tgts.n_mb>0:
            self.tgts.r = np.concatenate((self.tgts.r,r[-1,:-1]))
            self.tgts.state_v_mb = np.concatenate((self.tgts.state_v_mb,state_v[:,-1,:-1]),axis=1)
            self.tgts.state_c_mb = np.concatenate((self.tgts.state_c_mb,state_c[:,:,-1,:-1]),axis=2)
            self.tgts.n_mb += self.tgts.r.shape[0]
        else:
            self.tgts.r = (r[-1,:-1])
            self.tgts.state_v_mb = (state_v[:,-1,:-1])
            self.tgts.state_c_mb = (state_c[:,:,-1,:-1])
            self.tgts.n_mb = self.tgts.r.shape[0]
        return 0

    def initF(self):
            self.F = np.identity(3, dtype=float)
            self.F[0,1] = self.t
            self.F[1,2] = self.t
            self.F[0,2] = 0.5*self.t**2
            self.F[2,2] = 1#+np.exp(-self.t/self.theta)
            self.F = np.kron(np.identity(self.d),self.F)

###############################################################################
#################### Required Methods for Benjamin's code #####################
###############################################################################
    # No use for this function here
    def setTargets(self,_tgts):
        return
    
    # TODO: empty memory (tgts,ptgts,marg_prob,...)
    def clear(self):
        del self.tracks
        del self.tgts
        del self.time
        del self.prev_scan
        del self.prev_cov
        del self.scan
        del self.prev_not_assigned

        self.timestamp = 0
        self.scan    = None
        self.time = QDateTime()
        self.prev_scan = np.ndarray(())
        self.prev_cov = np.ndarray(())
        self.tgts = Tgts()
        self.prev_not_assigned = np.zeros((1),dtype=int)
        self.tracks  = []

    # TODO: check, but this might stay the same
    def isTracked(self,idTarget):
        #retourne vrai si le plot est associé à une cible à tracker

        for _target in self.tracks:
            if _target.id == idTarget:
                return True
        return False


    #TODO: turn scan into my vscan
    def receiveScan(self,_scan):
        #scan to my vscan
        #################
        
        scan = np.ndarray((self.d,len(_scan.plots)))
        scan_cov = np.ndarray((self.d,self.d,len(_scan.plots)))
        for i,meas in enumerate(_scan.plots):
            scan[0,i] = meas.z_XY[0]#-_scan.sensor.node.Position.x
            scan[1,i] = meas.z_XY[1]#-_scan.sensor.node.Position.y
            scan_cov[:,:,i]=meas.R_XY[:,:] # TODO: test another covariance

        if self.timestamp==0:
            self.t = _scan.sensor.timeOfSampling
            self.time = _scan.sensor.lastScanTime
            self.p_d = _scan.sensor.sensorCoverage[0].parameters.pd-0.1
            self.lambda_fa =  _scan.sensor.sensorCoverage[0].parameters.pfa+10**-9
            self.initF()
        else:
            time=_scan.sensor.lastScanTime
            self.t = self.time.msecsTo(time)/1000    
            self.time = time
            self.initF()

        if len(_scan.plots)==0:
            ptgts = Tgts()
            self.prediction(ptgts)
        else:
            self.run(scan, scan_cov)
        

    #TODO: clearly, this is the main of my code: should be treated as such
    def run(self,scan,cov):
        not_assigned, poiss_id, scan2, cov2, ext2, card2 = self.correction(scan,cov)
        # index_partition , clusters = filter.prune_merge(tgts, vscan, clusters, index_partition,0.1,100,omega)
	    # TODO: update not_assigned after tgts thresholding
        self.threshold(not_assigned, poiss_id)
        self.timestamp+=1
        if self.tracks != [] and self.timestamp%10:
            self.updatedTracks.emit(self.tracks)
        # TODO: attention si lambda f est nul, alors la piste poisson est validée automatiquement...
       	#print(card.shape)
        ptgts = Tgts(scan2, cov2, ext2, card2, not_assigned, self.prev_scan, self.prev_cov, self.prev_ext, self.prev_card, self.prev_not_assigned,self.t)
        self.prev_scan = np.copy(scan2)
        self.prev_not_assigned = np.copy(not_assigned)
        self.prev_cov=np.copy(cov2)
        self.prev_ext=np.copy(ext2)
        self.prev_card=np.copy(card2)
        self.prediction(ptgts)
        #print("r=",self.tgts.r)
       #print("state_p shape", self.tgts.state_v_p.shape)
       #print("state_mb shape", self.tgts.state_v_mb.shape)
        return

    def Target2Track(self,i,n_old_tracks):
            trackid = float(str(self.tgts.labels[0,i])+'.'+str(self.tgts.labels[1,i]))
            if i>=n_old_tracks:
                state = np.ndarray((4))
                cov = np.ndarray((4,4))
                state[:2]      = self.tgts.state_v_mb[:2,i]
                state[2:]      = self.tgts.state_v_mb[3:5,i]
                cov[:2,:2] = self.tgts.state_c_mb[:2,:2,i]
                cov[2:,2:] = self.tgts.state_c_mb[3:5,3:5,i]
                extent = self.tgts.Nu_mb[:,:,i]/(self.tgts.nu_mb[i]-2*self.d-2)
                self.tracks.append(Track())
                self.tracks[-1].initialize(time = self.time, cov = cov, state = state, extent = extent, ftype = 2)
                self.tracks[-1].id = trackid
                self.tracks_map[i] = len(self.tracks)-1
                return
            j = self.tracks_map[i]
            if self.tracks[j].id==trackid:
                currentStates = []
                self.tracks[j].tree.getChilds(currentStates)
                for _cState in currentStates:
                    new_state= State.copyState(_cState.data)
                    new_state.state[:2]      = self.tgts.state_v_mb[:2,i]
                    new_state.state[2:]      = self.tgts.state_v_mb[3:5,i]
                    new_state.covariance[:2,:2] = self.tgts.state_c_mb[:2,:2,i]
                    new_state.covariance[2:,2:] = self.tgts.state_c_mb[3:5,3:5,i]
                    new_state.X = self.tgts.Nu_mb[:,:,i]/(self.tgts.nu_mb[i]-2*self.d-2)
                    new_state.location.setXYZ(float(new_state.state[0]),float(new_state.state[2]),0.0)
                    new_state.updateCovariance()
                    new_state.time = self.time
                    self.tracks[j].addState(new_state,_cState)
            else:
                print("Problem with the target/track id match")
            
            return

    def getTracks(self):
        return self.tracks

#    def Targets2Tracks(self):
#        for i in range(self.tgts.n_mb):
#            trackid = float(str(self.tgts.labels[0,i])+'.'+str(self.tgts.labels[1,i]))
#            found = 0
#            currentStates = []
#            for j in range(len(self.tracks)):
#                if self.tracks[j].id==trackid:
#                    found=1
#                    currentStates.clear()
#                    self.tracks[j].tree.getChilds(currentStates)
#                    for _cState in currentStates:
#                        new_state= State.copyState(_cState.data)
#                        new_state.state[:2]      = self.tgts.state_v_mb[:2,i]
#                        new_state.state[2:]      = self.tgts.state_v_mb[3:5,i]
#                        new_state.covariance[:2,:2] = self.tgts.state_c_mb[:2,:2,i]
#                        new_state.covariance[2:,2:] = self.tgts.state_c_mb[3:5,3:5,i]
#                        new_state.location.setXYZ(float(new_state.state[0]),float(new_state.state[2]),0.0)
#                        new_state.updateCovariance()
#                        new_state.time = self.time
#                        self.tracks[j].addState(new_state,_cState)
#            if found==0:
#                state = np.ndarray((4))
#                cov = np.ndarray((4,4))
#                state[:2]      = self.tgts.state_v_mb[:2,i]
#                state[2:]      = self.tgts.state_v_mb[3:5,i]
#                cov[:2,:2] = self.tgts.state_c_mb[:2,:2,i]
#                cov[2:,2:] = self.tgts.state_c_mb[3:5,3:5,i]
#                self.tracks.append(Track())
#                self.tracks[-1].initialize(time = self.time, cov = cov, state = state, ftype = 1)
#                self.tracks[-1].id = trackid
