from numpy import *

import timer as _timer

from munkres import Munkres

def gospa_ospa_distances(X,Y,alpha=2,p=1,c=15):
    """ Compute the OSPA metric between two sets of points. """
    # X and Y should be in the shape m*d and n*d where d 
    # is the dimension of the problem and m and n are respectively the
    # numbers of predictions and real targets.
    
    
    # check for empty sets
    if size(X) == 0 and size(Y) == 0:
        return (0,0,array((0,0)),0)
    elif size(X) == 0 or size(Y) == 0 :
        cardinals = array((len(Y),len(X)))
        return (((max(len(X),len(Y))/alpha*c**p))**(1/p),(c**p)**(1/p),cardinals,0)
        

    # we assume that Y is the larger set
    m = size(X,0)
    n = size(Y,0)
    cardinals = array((n,m))

    if m > n:
        X,Y = Y,X
        m,n = n,m    
    
    # compute the cost matrix using Euclidean distance
    dists = empty([m,n])

    i = 0
    for x in X:
        diff = x - Y 
        if diff.ndim > 1:
            dist_row = sqrt(sum(diff**2,axis=1))
        else:
            dist_row = sqrt(diff**2)
        dist_row[ dist_row > c ] = c    # apply the cutoff        
        dists[i,:] = dist_row 
        i += 1
       
    # pad the matrix with dummy points
    if n > m:
        dists[m:n,:] = c
    munkres_mat = copy(dists)
    munkres = Munkres()
    indices = munkres.compute(munkres_mat)
 # compute the optimal assignment using the Hungarian (Munkres) algorithm
    #assignment = Munkres2()
    #indices = assignment.compute(dists)
    # compute the OSPA metric
    total_loc = 0
    mse = 0
    card = 0
    for [i,j] in indices:
        total_loc += min(dists[i][j],c)**p
        # Compute the mean square error of what has been
        # detected (missed targets are not taken into account)
        if min(dists[i][j],c)<c:
            mse += dists[i][j]**2
            card += 1
    if card>0: mse = mse/card
    #err_cn = sgn*(n-m)
    #err_loc = (float(total_loc)/n)**(1/p) 
    gospa_err = ( float(total_loc + (n-m)/alpha*c**p))**(1/p)
    ospa_err = ( float(total_loc + (n-m)*c**p)/n)**(1/p)
    # GOSPA metric, OSPA metric, Localization error, Cardinality error
    return gospa_err,ospa_err,cardinals,mse

    
if __name__ == '__main__':
    # test routine
    X = array(((0.1,-0.1,0,0.3),(0.1,0.5,0.2,0.3)),dtype='float').T
    Y = array(((0.2,-0.2,0),(0.1,0.5,0.2)),dtype='float').T
    X = arange(6,dtype='float')
    Y = array([0,-3,-6],dtype='float')
    d,_,_,_ = gospa_ospa_distances(X,Y)
    print(d)

class Metrics():

    def __init__(self, parent, filename):
        self.parent = parent
        self.filename = filename
        self.n_nodes = 0

    def computeOSPA(self):
        ground_truth = self.parent.loader.newArray(self.filename+"/gt.db")

        self.n_nodes = ground_truth.shape[3]

        n_times = ground_truth.shape[2]

        self.gospa = zeros((n_times,self.n_nodes))
        self.ospa = zeros((n_times,self.n_nodes))
        self.mask = zeros((n_times,self.n_nodes))
        self.cards = zeros((2,n_times,self.n_nodes))
        self.mse = zeros((n_times,self.n_nodes))

        self.parent.timer.progressBar.setMinimum(1)
        self.parent.timer.progressBar.setMaximum(100)
        time = _timer.getReferenceTime()

        for k in range(100):
            time_c = time.addMSecs(k+1)
            self.parent.timer.setRunTime(time_c)
            run = self.parent.loader.newArray(self.filename+"/run_%d.db"%k)
            for j in range(self.n_nodes):
                for t in range(n_times):
                    if (ground_truth[:,2,t,j]>0).any():
                        if (ground_truth[:,2,t,j]==2).any():
                            Y = zeros((0,2))
                        else:
                            Y = ground_truth[ground_truth[:,2,t,j]>0,:2,t,j]
                        if (run[:,2,t,j]>0).any():
                            X = run[run[:,2,t,j]>0,:2,t,j]
                        else:
                            X = zeros((0,2))
                        tmp1,tmp2,tmp3,tmp4 = gospa_ospa_distances(X,Y)
                        self.gospa[t,j] += tmp1
                        self.ospa[t,j] += tmp2
                        self.cards[0,t,j] += tmp3[0]
                        self.cards[1,t,j] += tmp3[1]
                        self.mse[t,j] += tmp4
                        self.mask[t,j] = 1

    def storeOSPA(self):
        if self.n_nodes == 0:
            return

        for j in range(self.n_nodes):
            maskj = nonzero(self.mask[:,j])[0]
            gospaj = self.gospa[maskj,j]/100
            ospaj = self.ospa[maskj,j]/100
            cardsj = self.cards[:,maskj,j]/100
            msej = self.mse[maskj,j]/100
            gospa_ospa = concatenate((gospaj,ospaj,cardsj[0,:],cardsj[1,:],msej)).reshape((5,len(maskj)))
            self.parent.saveNumpy(self.filename+"/gospa_ospa_node_%d.db"%j,gospa_ospa)
