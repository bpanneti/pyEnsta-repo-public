from munkres import Munkres, print_matrix, make_cost_matrix, DISALLOWED
import numpy as np
matrix  =[]
M = [5,   DISALLOWED ] 
matrix .append(M)
M = [10, DISALLOWED ] 
matrix .append(M)
#M = [8, 7, 4 , DISALLOWED] 
#matrix .append(M)
#print(M[:][3])
#cost_matrix = make_cost_matrix(matrix, lambda cost: (sys.maxsize - cost) if
 #                                     (cost != DISALLOWED) else DISALLOWED)
m = Munkres()
indexes = m.compute(matrix)
print_matrix(matrix, msg='Highest profit through this matrix:')
total = 0
for row, column in indexes:
    value = matrix[row][column]
    total += value
    print(f'({row}, {column}) -> {value}')
print(f'total profit={total}')
