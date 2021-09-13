# -*- coding: utf-8 -*-
"""
Created on Fri Sep 10 17:27:01 2021

@author: benja
"""
from munkres import Munkres, print_matrix
import numpy as np
matrix = [[10, 9, 0],
          [10, 8, 2],
          [0, 0, 4]]
m = Munkres()
indexes = m.compute(-np.array( matrix))
print_matrix(matrix, msg='Lowest cost through this matrix:')
total = 0
for row, column in indexes:
    value = matrix[row][column]
    total += value
    print(f'({row}, {column}) -> {value}')
print(f'total cost: {total}')



matrix = [[10, 0, 0],
          [0, 8, 2],
          [0, 0, 0]]

indexes = m.compute(-np.array( matrix))
print_matrix(matrix, msg='Lowest cost through this matrix:')
total = 0
for row, column in indexes:
    value = matrix[row][column]
    total += value
    print(f'({row}, {column}) -> {value}')
print(f'total cost: {total}')

