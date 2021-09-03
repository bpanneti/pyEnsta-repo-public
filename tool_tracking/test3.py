# -*- coding: utf-8 -*-
"""
Created on Mon Dec  2 18:21:41 2019

@author: bpanneti
"""
from scipy.optimize import linear_sum_assignment
import numpy as np

cost = np.array([[4, 1, 3,500], [2, 0, 5,500], [3, 2, 2,500]])
print(np.asmatrix(cost))
row_ind, col_ind = linear_sum_assignment(np.asmatrix(cost))
print([row_ind, col_ind])
for r in range(0,len(row_ind)):
     print([row_ind[r],',',col_ind[r]])
