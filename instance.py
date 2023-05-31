import numpy as np

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
    
    def compute_min_path(self) -> 'None':
        n = self.n
        min_paths = []
        o = n
        
        for i in range(n):
            min_paths.append(self.distances[o,i] + self.distances[i,o])

        self.min_path = int(max(min_paths))
