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
        self._courier_routes = {k: [] for k in range(self._instance.m)}

        # Extract and populate courier routes
        for k in range(self._instance.m):
            if self._lib == "mip":
                self._courier_routes[k] = [[i, j] for i in range(self._instance.origin) for j in
                                           range(self._instance.origin) if
                                           self._table[k, i, j].x == 1]

            elif self._lib == "ortools":
                self._courier_routes[k] = [[i, j] for i in range(self._instance.origin) for j in
                                           range(self._instance.origin) if
                                           self._table[k, i, j].solution_value() == 1]
            elif self._lib == "pulp":
                self._courier_routes[k] = [[i, j] for i in range(self._instance.origin) for j in
                                           range(self._instance.origin) if
                                           self._table[k, i, j].value() == 1]
            elif self._lib == "z3":
                self._courier_routes[k] = [[i, j] for i in range(self._instance.origin) for j in
                                           range(self._instance.origin) if
                                           self._table[k][i][j]]

        # Reorder the routes to start from the origin
        for k in range(self._instance.m):
            origin_index = next(
                (i for i, route in enumerate(self._courier_routes[k]) if route[0] == self._instance.origin - 1),
                None)
            if origin_index is not None:
                self._courier_routes[k] = self._courier_routes[k][origin_index:] + self._courier_routes[k][
                                                                                   :origin_index]

        # Reorder it in a way that the first element of the tuple I is the second element of the tuple i-1
        for k in range(self._instance.m):
            for i in range(1, len(self._courier_routes[k])):
                if self._courier_routes[k][i][0] != self._courier_routes[k][i - 1][1]:
                    for j in range(i + 1, len(self._courier_routes[k])):
                        if self._courier_routes[k][i][0] == self._courier_routes[k][j][1]:
                            self._courier_routes[k][i], self._courier_routes[k][j] = self._courier_routes[k][j], \
                                self._courier_routes[k][i]
                            break

        # Remove instance.origin - 1 from the routes
        for k in range(self._instance.m):
            self._courier_routes[k] = [route[0] for route in self._courier_routes[k]]
            if len(self._courier_routes[k]) > 0:
                self._courier_routes[k].pop(0)

        # Create a list to store the routes for each courier
        routes = [self._courier_routes[k] for k in range(self._instance.m)]

        # print(routes)
        return routes

    def get_result(self) -> dict:
        return self._result
