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
        self.compute_bounds()
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
            dist[nodes] = np.max(dist) + 1
            c = np.min(dist)
            i, = np.where(dist == c)
            return i[0], c

        ordered_size = sorted(self.size)

        k = 1
        while sum(ordered_size[k:]) > max_weight:
            k +=1
        
        self.min_path = int(max([compute_path(self.distances[o,i], [o, i], min_select,k) for i in range(self.n)], key=lambda b: b['c'])['c'])

        k = 1
        while sum(ordered_size[:self.n-k]) > max_weight:
            k +=1
        self.min_packs = k

        k = 1
        while sum(ordered_size[:k]) < self.max_load[-1] and k < self.n:
            k+=1
        
        self.max_packs = k

        self.max_path_length = min(self.max_packs + 2, self.max_path_length)

        def max_select(nodes):
            dist = np.copy(self.distances[nodes[-1], :])
            dist[nodes] = -1
            c = np.max(dist)
            i, = np.where(dist == c)
            return i[0], c

        self.max_path = int(min([compute_path(self.distances[o,i], [o, i], max_select,k) for i in range(self.n)], key=lambda b: b['c'])['c'])

        # enc = bin(self.n)[2:]
        # self.encoding = len(enc)
        # self.origin_encoding = [str(i + 1) for i in range(self.encoding) if enc[i] == '1']
        # self.pow = [str(2 ** i) for i in range(len(enc))]


    def save_dzn(self, file_path=None):
        distaces_list = self.distances
        distaces_str_arr = [", ".join([str(int(i)) for i in distaces_list[j]]) for j in range(len(distaces_list))]
        distaces_str = '\n                      | '.join(distaces_str_arr)
        instance = f'''m = {self.m};
        
n = {self.n};
max_load = {self.max_load};
size = {self.size};
dist = [|{distaces_str}|];
min_path = {self.min_path};
max_path = {self.max_path};
max_path_length = {self.max_path_length};
origin  = {self.origin};
number_of_origin_stops = {self.number_of_origin_stops};
n_array = {self.n_array};
count_array = {self.count_array};
min_packs = {self.min_packs};
        '''
        name = self.name
        path = "."
        if not file_path is None:
            path = file_path
        file = open(f"{path}/{name}.dzn", "w")
        file.write(instance)
