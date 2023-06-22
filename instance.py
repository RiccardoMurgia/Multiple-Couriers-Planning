import numpy as np
import sys

class Instance:

    def __init__(self, file_path:'str') -> None:
        
        self.name = file_path.split('/')[-1].replace('.dat','')
        file = open(file_path, "r")
        lines = [line.replace('\n','') for line in file]
        file.close()
        self.m = int(lines[0])
        self.n = int(lines[1])
        loads = lines[2].split(' ')
        self.max_load = sorted([int(l) for l in loads])
        sizes = lines[3].split(' ')
        self.size = [int(s) for s in sizes if s != '']
        lines = lines[4:]
        self.distances = np.zeros(shape=(self.n + 1, self.n + 1), dtype=int)
        for i in range(self.n + 1):
            line = lines[i].split(' ')
            for j in range(self.n + 1):
                self.distances[i,j] = int(line[j])

        self.optimal_paths = None
        self.min_path = 0
        self.max_path_length = self.n-self.m+3
        self.number_of_origin_stops = int((self.max_path_length * self.m) - self.n)
        self.origin = int(self.n+1)
        self.n_array = [i+1 for i in range(self.n + 1)]
        self.count_array = [1 for _ in range(self.n)] + [self.number_of_origin_stops]

    
    def compute_bounds(self) -> 'None':
        o = self.n
        def compute_path(current_cost, nodes, select, steps):
            if steps > len(nodes) - 1:
                next_step, cost = select(nodes)
                updated_nodes = nodes + [next_step]
                cost += current_cost
                return compute_path(cost, updated_nodes, select, steps)
            return {'p':nodes + [o], 'c': current_cost + self.distances[nodes[-1],o]}
        
        max_weight = sum(self.max_load[1:])
        def min_select(nodes):
            dist = np.copy(self.distances[nodes[-1], :])
            dist[nodes] = sys.maxsize
            c = np.min(dist)
            i, = np.where(dist == c)
            return i[0], c

        k = 0
        while sum(self.size[k:]) > max_weight:
            k +=1
        
        self.min_path = int(max([compute_path(self.distances[o,i], [o, i], min_select,k) for i in range(self.n)], key=lambda b: b['c'])['c'])

        k = 0
        while sum(self.size[self.n-k:]) < self.max_load[-1] and k < self.n:
            k+=1
        
        def max_select(nodes):
            dist = np.copy(self.distances[nodes[-1], :])
            dist[nodes] = -1
            c = np.max(dist)
            i, = np.where(dist == c)
            return i[0], c

        self.max_path = int(min([compute_path(self.distances[o,i], [o, i], max_select,k) for i in range(self.n)], key=lambda b: b['c'])['c'])
