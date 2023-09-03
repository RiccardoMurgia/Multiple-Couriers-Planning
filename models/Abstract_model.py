import time

from instance import Instance


class Abstract_model:
    def __init__(self, lib: 'str', instance: 'Instance'):
        self._lib = lib
        self._start_time = time.time()
        self._end_time = None
        self._inst_time = None
        self._instance = instance
        self._table = None
        self._u = {}
        self._status = None
        self._result = {}

        self._courier_routes = {k: [] for k in range(instance.m)}

    def _get_solution(self) -> 'list':
        # Create a dictionary to store the routes for each courier

        # Extract and populate courier routes
        for k in range(self._instance.m):

            if self._lib == "mip":
                self._courier_routes[k] = [[i + 1, j + 1] for i in range(self._instance.origin) for j in
                                           range(self._instance.origin) if
                                           self._table[k, i, j].x == 1]

            elif self._lib == "ortools":
                self._courier_routes[k] = [[i + 1, j + 1] for i in range(self._instance.origin) for j in
                                           range(self._instance.origin) if
                                           self._table[k, i, j].solution_value() == 1]
            elif self._lib == "pulp":
                self._courier_routes[k] = [[i + 1, j + 1] for i in range(self._instance.origin) for j in
                                           range(self._instance.origin) if
                                           self._table[k, i, j].value() == 1]
            elif self._lib == "z3":
                self._courier_routes[k] = [[i + 1, j + 1] for i in range(self._instance.origin) for j in
                                           range(self._instance.origin) if
                                           self._table[k][i][j]]


        for k in range(self._instance.m):
            self._courier_routes[k] = self.compute_route(self._instance.origin, self._instance.origin, self._courier_routes[k])
        # Reorder the routes to start from the origin
        # Remove instance.origin - 1 from the routes
        for k in range(self._instance.m):
            if len(self._courier_routes[k]) > 0:
                m = max(self._courier_routes[k])
                self._courier_routes[k] = list(filter(lambda d: d < m, self._courier_routes[k]))

        # Create a list to store the routes for each courier
        routes = [self._courier_routes[k] for k in range(self._instance.m)]
        
        # 
        # for i in range(len(routes)):
        #     for j in range(len(routes[i])):
        #         routes[i][j] += 1
        
        return routes

    def get_result(self) -> dict:
        return self._result


    def compute_route(self, start, end, pairs):
        route = [start]
        current = start
        def get_next(current):
            for pair in pairs:
                if pair[0] == current:
                    return pair[1]
        while True:
            current = get_next(current)
            route.append(current)
            if current == end:
                return route

