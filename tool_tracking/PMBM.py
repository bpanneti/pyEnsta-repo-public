import numpy as np
import matplotlib.pyplot as plt
#from numba.decorators import njit
import math
from scipy.optimize import linear_sum_assignment

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from tool_tracking.track import Track
from tool_tracking.state import State

import sys

MINI_FLOAT = sys.float_info.min

import sys

MINI_FLOAT = sys.float_info.min

def gaussian(x,mu,sig):
    numerat = np.exp(-0.5*(x-mu).dot(np.linalg.inv(sig)).dot(x-mu))
    denom = (np.sqrt(np.linalg.det(sig))*(2*np.pi))
    return numerat/denom

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
    init_weight=0.9

    def __init__(self, pc=np.ndarray(()), cov=np.ndarray(()), not_assigned=np.zeros(()), prev_pc=np.ndarray(()), prev_cov=np.ndarray(()), prev_not_assigned=np.ndarray((0)),dt=0):
        if (prev_not_assigned>0).any():
            self.consec_init(pc, cov, not_assigned, prev_pc, prev_cov, prev_not_assigned,dt)
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
        self.lambda_p[0] = self.init_weight
        self.n_p = 1

        # Multi Bernoulli
        self.n_mb = 0
        self.r = np.ndarray(())
        self.state_v_mb = np.ndarray(())
        self.state_c_mb = np.ndarray(())
        self.labels = np.ndarray(())
            
    # TODO: initialize new targets from consecutive measurments in order to get a plausible speed!
    # Maybe inspire myself of the way the init of new mbs is done with the former Poisson!
    def consec_init(self, pc, cov, not_assigned, prev_pc, prev_cov, prev_not_assigned, dt, speed=100):
        # try to assoc in a 2m radius: it means a relative speed of 128km/h
        state = []
        state_cov = []
        
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
                init_cov = 0.5*cov[:,:,i]+0.5*prev_cov[:,:,j]
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


        # Poisson
        if len(state)==0:
            self.regular_init()
        else:
            self.state_v_p = np.array(state).T
            self.state_c_p = np.moveaxis(np.array(state_cov),(-2,-1),(0,1))
            self.lambda_p = self.init_weight*np.ones(len(state))
            self.n_p = len(state)

        # Multi Bernoulli
        self.n_mb = 0
        self.r = np.ndarray(())
        self.state_v_mb = np.ndarray(())
        self.state_c_mb = np.ndarray(())
        self.labels = np.ndarray(())

    def prediction(self,p_s,F,T):
        if self.n_mb>0:
            self.r = p_s*self.r
            self.state_v_mb = F.dot(self.state_v_mb)
            for i in range(self.n_mb):
                self.state_c_mb[:,:,i] = F.dot(self.state_c_mb[:,:,i]).dot(F.T)+Q(T,self.d,0.5)
        if self.n_p>0:
            self.lambda_p = p_s*self.lambda_p
            self.state_v_p = F.dot(self.state_v_p)
            for i in range(self.n_p):
                self.state_c_p[:,:,i] = F.dot(self.state_c_p[:,:,i]).dot(F.T)+Q(T,self.d,1)

    def correction(self, scan, scan_cov, p_d, lambda_fa, F, H, R, gatedMeas,t):
        n_meas = scan.shape[1]
        w_tmp = np.zeros((self.n_mb+1,n_meas+1))
        r_tmp = np.zeros((self.n_mb+1,n_meas+1))
        state_v_tmp = np.ndarray((self.state_v_p.shape[0],self.n_mb+1,n_meas+1))
        state_c_tmp = np.ndarray((3*self.d,3*self.d,self.n_mb+1,n_meas+1))

        if self.n_mb>0:
        # Missed detection hypothesis
        # Explanation for the norma var: during the LBP without this 
        # the weight of the missed detection hypothesis is way too high 
        # with respect to the detection hypothesis because the multivariate
        # gaussian kills the dection hypothesis weight. the solution is this 
        # trick which is just normalisation. it could be 10**-4 or the same 
        # exponent than the detection hypothesis. For now this trick works, 
        # we need to keep an eye on it anyway (it is a bit dirty)
        ##### Update: we chose to move this normalization after the update procedure
        ##### in order to get it only if their might be a match
            normalization_var = 1#((1-p_d)**(4))
            w_tmp[:-1,0] = normalization_var*(1-self.r+self.r*(1-p_d))
            r_tmp[:-1,0] = normalization_var*(self.r*(1-p_d)/w_tmp[:-1,0])
            state_v_tmp[:,:-1,0] = self.state_v_mb
            state_c_tmp[:,:,:-1,0] = self.state_c_mb

            for i in range(self.n_mb):
                # Correction components
                # TODO: check if R can be replace by the cov returned by the sensor
#                S = self.H.dot(self.tgts.state_c_mb[:,:,i]).dot(self.H.T)+self.R
#                K = self.tgts.state_c_mb[:,:,i].dot(self.H.T).dot(np.linalg.inv(S))
#                P = self.tgts.state_c_mb[:,:,i]-K.dot(self.H).dot(self.tgts.state_c_mb[:,:,i])
                J = np.nonzero(gatedMeas[i,:])[0]
                confidence = (t-self.labels[0,i])
                for j in J:
                    # Chaque mesures TODO: triple check
                    #print("state_c_mb",self.state_c_mb[:,:,i])
                    if (scan_cov[:,:,j]/confidence>R).all():
                        S = H.dot(self.state_c_mb[:,:,i]).dot(H.T)+scan_cov[:,:,j]/confidence#+R
                    else:
                        S = H.dot(self.state_c_mb[:,:,i]).dot(H.T)+R
                    nu = scan[:,j]-H.dot(self.state_v_mb[:,i])
                    #print("covariance",np.outer(nu,nu))
                    #S = S + np.outer(nu,nu)/5
                    #print("S",S)
                    K = self.state_c_mb[:,:,i].dot(H.T).dot(np.linalg.inv(S))
                    #print("K",K)
                    P = self.state_c_mb[:,:,i]-K.dot(H).dot(self.state_c_mb[:,:,i])
                    
                   #print("error=",nu)
                    w_tmp[i,j+1] = self.r[i]*p_d*gaussian(nu,np.zeros(self.d),S)
                   #print("w_tmp",w_tmp[i,j+1])
                   #print("r",self.r[i])
                    r_tmp[i,j+1] = 1
                    #print("state_v_mb", self.state_v_mb[:,i])
                    state_v_tmp[:,i,j+1] = self.state_v_mb[:,i]+K.dot(nu)
                    #print("state_v_tmp",state_v_tmp[:,i,j+1])
                    state_c_tmp[:,:,i,j+1] = P[:,:]
                #print("w_tmp",w_tmp[i,:])
                #### this is the missed detection hypothesis normalization trick.
                #### we just need to set missed detection hypothesis a bit higher
                #### than detection hypothesis in order to correct it during LBP,
                #### then we get a correct marginal probability!
                expo = np.max(np.log10(w_tmp[i,1:]+MINI_FLOAT))
                if expo>-6 and expo<-1:
                    w_tmp[i,0] = w_tmp[i,0]*10**(expo+1)

        # if self.tgts.n_p>0: -> at least 1, we keep one or two secret poisson hyp in 
        # Correction components for undetected self.tgts
        S = np.ndarray((H.shape[0],H.shape[0],self.n_p))
        K = np.ndarray((self.state_v_p.shape[0],H.shape[0],self.n_p))
        P = np.ndarray((3*self.d,3*self.d,self.n_p))
        poiss_id = np.ndarray((n_meas),dtype=int)

        #for k in range(self.n_p):
            
            
            #print("trace poisson=",np.trace(self.state_c_p[:,:,k]))

        for j in range(n_meas):
            c = np.ndarray((self.n_p))
            y = np.ndarray((self.state_v_p.shape[0],self.n_p))

            for k in range(self.n_p):
                S[:,:,k] = H.dot(self.state_c_p[:,:,k]).dot(H.T)+scan_cov[:,:,j]
                K[:,:,k] = self.state_c_p[:,:,k].dot(H.T).dot(np.linalg.inv(S[:,:,k])) 
                P[:,:,k] = self.state_c_p[:,:,k]-K[:,:,k].dot(H).dot(self.state_c_p[:,:,k])
                nu = scan[:,j]-H.dot(self.state_v_p[:,k])
                c[k] = self.lambda_p[k]*p_d*gaussian(nu,0,S[:,:,k])
                y[:,k] = self.state_v_p[:,k]+K[:,:,k].dot(nu)

            poiss_id[j] = np.where(np.max(c)==c)[0][0]
            c=c+MINI_FLOAT
            #c = c[poiss_id[j]]+MINI_FLOAT
            C=np.sum(c)
            w_tmp[-1,j] = C+lambda_fa
            r_tmp[-1,j] = C/w_tmp[-1,j]
            # todo: trick
            state_v_tmp[:,-1,j] = np.sum(np.outer(np.ones((3*self.d)),c)*y,axis=1)/C
            #state_v_tmp[:,-1,j] = (y[:,poiss_id[j]])
            tmp = np.zeros((state_c_tmp.shape[:2]))

            for k in range(self.n_p):
                tmp += c[k]*(P[:,:,k]+np.outer(state_v_tmp[:,-1,j]-y[:,k],state_v_tmp[:,-1,j]-y[:,k]))
            state_c_tmp[:,:,-1,j] = tmp/C
            #state_c_tmp[:,:,-1,j] = (P[:,:,poiss_id[j]]+np.outer(state_v_tmp[:,-1,j]-y[:,poiss_id[j]],state_v_tmp[:,-1,j]-y[:,poiss_id[j]]))

        self.lambda_p = (1-p_d)*self.lambda_p

        return w_tmp, r_tmp, state_v_tmp, state_c_tmp, poiss_id

#    def copy(self,targets):
#        self.state_v_p   = np.copy(targets.state_v_p)
#        self.state_c_p   = np.copy(targets.state_c_p)
#        self.lambda_p         = np.copy(targets.lambda_p)
#        self.n_p = targets.n_p
#
#        self.wl        = np.copy(targets.wl)
#        self.rot       = np.copy(targets.rot)
#        self.nu        = np.copy(targets.nu)
#        self.gam       = np.copy(targets.gam)
#        self.Nu        = np.copy(targets.Nu)
#
#        self.n_mb = targets.n_mb
#        self.r = np.copy(targets.r)
#        self.state_v_mb = np.copy(targets.state_v_mb)
#        self.state_c_mb = np.copy(targets.state_c_mb)



class PMBM(QThread):

            
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
    
        QThread.__init__(self, parent)    
        self.tracks  = []
        self.scan    = None
        self.time = QDateTime()

        
        self.prev_scan = np.ndarray(())
        self.prev_cov = np.ndarray(())
        self.prev_not_assigned = np.zeros((1),dtype=int)
        self.targets = []
        self.tgts = Tgts()
        

    def prediction(self,ptgts):

        self.tgts.prediction(self.p_s,self.F, self.t)
        
        ptgts.prediction(self.p_s,self.F, self.t)

        if ptgts.n_p:
            self.tgts.lambda_p = np.concatenate([self.tgts.lambda_p, ptgts.lambda_p])
            self.tgts.state_v_p = np.concatenate([self.tgts.state_v_p, ptgts.state_v_p],axis=1)
            self.tgts.state_c_p = np.concatenate([self.tgts.state_c_p, ptgts.state_c_p],axis=2)
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

        w_tmp, r_tmp, state_v_tmp, state_c_tmp, poiss_id = self.tgts.correction(scan, scan_cov, self.p_d, self.lambda_fa, self.F, self.H, self.R, gatedMeas, self.timestamp)

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

            not_assigned = np.ones((n_meas),dtype=int)
            residual_bernoullis = np.ones(n_tracks,dtype=int)
            for window in Windows:
                map_meas = np.nonzero(window[1])[0]
                map_trcks = np.nonzero(window[0])[0]
                residual_bernoullis[map_trcks] = 0
                nm=map_meas.shape[0]
                nt=map_trcks.shape[0]

                w = np.zeros((nt+1,nm+1))

                if nt>0:
                    w[:-1,0] = w_tmp[map_trcks,0]
                    w[-1,:-1] = w_tmp[-1,map_meas]
                    for i,t in enumerate(map_trcks):
                        w[i,1:] = w_tmp[t,map_meas+1]
                else:
                    w[-1,:-1] = w_tmp[-1,map_meas]

                marg_prob = self.LBP2(w,nm)

                not_assigned = self.small_munk_assignement(marg_prob, r_tmp, state_v_tmp, state_c_tmp, map_meas, map_trcks, not_assigned)

            for i in np.nonzero(residual_bernoullis)[0]:
                self.tgts.r[i] = r_tmp[i,0]
                self.tgts.state_v_mb[:,i] = state_v_tmp[:,i,0]
                self.tgts.state_c_mb[:,:,i] = state_c_tmp[:,:,i,0]
            
            self.concatenateMultiBern( not_assigned, r_tmp, state_v_tmp, state_c_tmp)

        else:
            marg_prob2 = self.LBP2( w_tmp, n_meas)

            not_assigned = self.munk_assignement( marg_prob2, r_tmp, state_v_tmp, state_c_tmp,n_meas)

        #self.TOMBP(self.tgts, marg_prob, r_tmp, state_v_tmp, state_c_tmp,n_meas)

        return not_assigned, poiss_id

# Using Munkres assignment algorithm, we match measurment with self.tgts. 
# Hence if needed, a new Bernoulli is created.
# Finally, the not assined clusters are marked so we can get reed of used Poisson
# hypothesis while creating new ones where clusters were undetected!

    def small_munk_assignement(self, marg_prob, r, state_v, state_c, map_meas, map_trcks, not_assigned):
#        if map_meas.shape[0]==0:
#            map_meas = np.arange(n_meas)
#            map_trcks = np.arange(n_tracks)
        n_tracks = map_trcks.shape[0]
        n_meas = map_meas.shape[0]

        tmp = np.copy(marg_prob[:,1:])
        tmp[:n_tracks,:] = tmp[:n_tracks,:]/np.outer(marg_prob[:n_tracks,0]+MINI_FLOAT,np.ones(n_meas))
        tmp = tmp+MINI_FLOAT
        ind_lines, ind_cols = linear_sum_assignment(-np.log(tmp))

        nd_mb = np.ones((n_tracks),dtype=int)

        for k in range(len(ind_lines)):
            i=ind_lines[k]
            j=ind_cols[k]
            if i<n_tracks:
                if marg_prob[i,0]<marg_prob[i,j+1]:
                    nd_mb[i]=0
                    not_assigned[map_meas[j]] = 0 # here the jth meas is assigned
                    self.tgts.r[map_trcks[i]] = marg_prob[i,j+1]*r[map_trcks[i],map_meas[j]+1]
                    self.tgts.state_v_mb[:,map_trcks[i]] = state_v[:,map_trcks[i],map_meas[j]+1]
                    self.tgts.state_c_mb[:,:,map_trcks[i]] = state_c[:,:,map_trcks[i],map_meas[j]+1]
            else:
                r[-1,map_meas[j]] = r[-1,map_meas[j]]*marg_prob[i,j+1]
                if r[-1,map_meas[j]]>0.1:
                    not_assigned[map_meas[j]] = -1 # Here the jth meas is assigned. However we should say "this is a poisson that took it" -> -1 is assigned

        nd_mb = np.nonzero(nd_mb)[0]
        
        for i in nd_mb:
           #print("not detected track",map_trcks[i])
            self.tgts.r[map_trcks[i]] = marg_prob[i,0]*r[map_trcks[i],0]
            self.tgts.state_v_mb[:,map_trcks[i]] = state_v[:,map_trcks[i],0]
            self.tgts.state_c_mb[:,:,map_trcks[i]] = state_c[:,:,map_trcks[i],0]

        return not_assigned

    def concatenateMultiBern(self, not_assigned, r, state_v, state_c):

        n_old_tracks = self.tgts.n_mb
        
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

        return

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
        self.tgts.n_p = len(ind)

        # Clean Multi Bernoulli:
        if self.tgts.n_mb>0: # TODO: recycling
            #ind = np.where(self.tgts.r<0.05)[0]
            #if len(ind):
            #    self.tgts.state_c_mb[:,:,ind] = 1.5*self.tgts.state_c_mb[:,:,ind]
            #    #self.tgts.r[ind] = self.tgts.r[ind]/self.tgts.r[ind]
            ind = np.where(self.tgts.r>threshold/2)[0]
            self.tgts.state_v_mb = self.tgts.state_v_mb[:,ind]
            self.tgts.state_c_mb = self.tgts.state_c_mb[:,:,ind]
            self.tgts.r = self.tgts.r[ind]
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

        for _target in self.tgts:
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
        not_assigned,poiss_id = self.correction(scan,cov)
        # index_partition , clusters = filter.prune_merge(tgts, vscan, clusters, index_partition,0.1,100,omega)
	    # TODO: update not_assigned after tgts thresholding
        self.threshold(not_assigned, poiss_id)
        self.timestamp+=1
        # TODO: attention si lambda f est nul, alors la piste poisson est validée automatiquement...
       	ptgts = Tgts(scan, cov, not_assigned, self.prev_scan, self.prev_cov, self.prev_not_assigned,self.t)
        self.prev_scan = np.copy(scan)
        self.prev_not_assigned = np.copy(not_assigned)
        self.prev_cov=np.copy(cov)
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
                self.tracks.append(Track())
                self.tracks[-1].initialize(time = self.time, cov = cov, state = state, ftype = 1)
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
