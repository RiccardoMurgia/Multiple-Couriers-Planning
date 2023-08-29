import mip
from ortools.linear_solver import pywraplp
import pulp

import multiprocessing
import time


from models.Abstract_model import Abstract_model
from instance import Instance


class Mip_model(Abstract_model):
    def __init__(self, lib: 'str', i: 'Instance', param, h: 'bool' = False, verbose: 'bool' = False):
        super().__init__(lib, i)
        self._table = {}
        self.__param = param
        self.__h = h

        # Create model
        self.__model = mip.Model(solver_name=mip.CBC)

        # Create variables
        self._table = {}
        for k in range(self._instance.m):
            for i in range(self._instance.origin):
                for j in range(self._instance.origin):
                    self._table[k, i, j] = self.__model.add_var(var_type=mip.INTEGER, name=f'table_{k}_{i}_{j}')

        self.__courier_distance = [self.__model.add_var(var_type=mip.INTEGER, name=f'courier_distance_{k}') for k in
                                   range(self._instance.m)]

        # Auxiliary variables to avoid sub-tours
        for k in range(self._instance.m):
            for i in range(self._instance.origin):
                self._u[k, i] = self.__model.add_var(var_type=mip.INTEGER, lb=1, ub=self._instance.origin,
                                                     name=f'u_{k}_{i}')

        if not verbose:
            self.__model.verbose = 0

    @staticmethod
    def clark_wright_savings(distances: 'list', capacity: int):
        # Calculate savings for all pairs of nodes
        savings = []
        for i in range(1, len(distances)):
            for j in range(i + 1, len(distances)):
                savings.append((i, j, distances[0][i] + distances[0][j] - distances[i][j]))

        # Sort savings in descending order
        savings.sort(key=lambda x: x[2], reverse=True)

        # Initialize routes
        routes = [[0] for _ in range(len(distances))]
        used_capacity = [0] * len(distances)

        # Greedily assign customers to routes
        for i, j, s in savings:
            route_i = None
            route_j = None
            for r in range(len(routes)):
                if i in routes[r]:
                    route_i = r
                if j in routes[r]:
                    route_j = r
            if route_i is not None and route_j is not None and route_i != route_j:
                if used_capacity[route_i] + used_capacity[route_j] + distances[i][j] <= capacity:
                    routes[route_i].remove(i)
                    routes[route_j].remove(j)
                    routes[route_i] += [i, j]
                    used_capacity[route_i] += distances[i][j]
                    used_capacity[route_j] += distances[i][j]

        return routes

    def solve(self) -> None:

        # Objective
        obj = self.__model.add_var(var_type=mip.INTEGER, name='obj')

        for k in range(self._instance.m):
            self.__model += self.__courier_distance[k] == mip.xsum(
                self._instance.distances[i][j] * self._table[k, i, j] for i in range(self._instance.origin) for j in
                range(self._instance.origin))

        # Upper and lower bounds
        self.__model += obj <= self._instance.max_path
        self.__model += obj >= self._instance.min_path

        for k in range(self._instance.m):
            self.__model += obj >= self.__courier_distance[k]

        self.__add_constraint()

        # Set the objective
        self.__model.objective = mip.minimize(obj)

        # Parameters
        # model.emphasis = 2  # Set to 1 or 2 to get progressively better solutions
        self.__model.cuts = self.__param  # Enable Gomory cuts
        # model.heuristics = 1  # Enable simple rounding heuristic
        # model.pump_passes = 1  # Perform one pass of diving heuristics
        # model.probing_level = 3  # Enable probing
        # model.rins = 1  # Enable RINS heuristic
        self.__model.threads = multiprocessing.cpu_count()

        if self.__h:
            # Call the Clark and Wright Savings Algorithm
            initial_routes = self.clark_wright_savings(self._instance.distances, self._instance.max_load[0])

            # Initialize routes using Clark and Wright Savings Algorithm
            for k, route in enumerate(initial_routes):
                for i, j in zip(route, route[1:]):
                    self._table[k, i, j].start = 1

            print('Using warm start CWS: Initial solution found in {} seconds'.format(time.time() - self._start_time))

        self._end_time = time.time()
        self._inst_time = self._end_time - self._start_time
        self._status = self.__model.optimize(max_seconds=int(300 - self._inst_time - self._instance.presolve_time))

        # Output
        if self._status == mip.OptimizationStatus.OPTIMAL or self._status == mip.OptimizationStatus.FEASIBLE:
            self._result['time'] = round(self._inst_time, 3)
            self._result['optimal'] = self._status == mip.OptimizationStatus.OPTIMAL
            self._result['obj'] = self.__model.objective_value
            self._result['sol'] = self._get_solution()

        else:
            self._result['time'] = round(self._inst_time, 3)
            self._result['optimal'] = self._status == mip.OptimizationStatus.OPTIMAL
            self._result['obj'] = None
            self._result['sol'] = None

    def __add_constraint(self) -> None:

        # Constraints
        for i in range(self._instance.origin):
            for k in range(self._instance.m):
                # A courier can't move to the same item
                self.__model += self._table[k, i, i] == 0
                # If an item is reached, it is also left by the same courier
                self.__model += mip.xsum(self._table[k, i, j] for j in range(self._instance.origin)) == mip.xsum(
                    self._table[k, j, i] for j in range(self._instance.origin))

        # Every item is delivered
        for j in range(self._instance.origin - 1):
            self.__model += mip.xsum(
                self._table[k, i, j] for k in range(self._instance.m) for i in range(self._instance.origin)) == 1

        for k in range(self._instance.m):
            # Couriers start at the origin and end at the origin
            self.__model += mip.xsum(
                self._table[k, self._instance.origin - 1, j] for j in range(self._instance.origin - 1)) == 1
            self.__model += mip.xsum(
                self._table[k, j, self._instance.origin - 1] for j in range(self._instance.origin - 1)) == 1

            # Each courier can carry at most max_load items
            self.__model += mip.xsum(
                self._table[k, i, j] * self._instance.size[j] for i in range(self._instance.origin) for j in
                range(self._instance.origin - 1)) <= self._instance.max_load[k]

            # Each courier must visit at least min_packs items and at most max_path_length items
            self.__model += mip.xsum(self._table[k, i, j] for i in range(self._instance.origin) for j in
                                     range(self._instance.origin - 1)) >= self._instance.min_packs
            self.__model += mip.xsum(self._table[k, i, j] for i in range(self._instance.origin) for j in
                                     range(self._instance.origin - 1)) <= self._instance.max_packs

        # If a courier goes for i to j then it cannot go from j to i, except for the origin
        # (this constraint it is not necessary for the model to work, but check if it improves the solution)
        for k in range(self._instance.m):
            for i in range(self._instance.origin - 1):
                for j in range(self._instance.origin - 1):
                    if i != j:
                        self.__model += self._table[k, i, j] + self._table[k, j, i] <= 1

            # Sub-tour elimination
        for k in range(self._instance.m):
            for i in range(self._instance.origin - 1):
                for j in range(self._instance.origin - 1):
                    if i != j:
                        self.__model += self._u[k, j] - self._u[k, i] >= 1 - self._instance.origin * (
                                1 - self._table[k, i, j])


class Or_model(Abstract_model):

    def __init__(self, lib: 'str', instance: 'Instance', solv: 'str' = 'CBC_MIXED_INTEGER_PROGRAMMING'):
        super().__init__(lib, instance)
        self._table = {}

        # Create solver
        self.__solver = pywraplp.Solver.CreateSolver(solv)

        self.__table = {}
        for k in range(instance.m):
            for i in range(instance.origin):
                for j in range(instance.origin):
                    self.__table[k, i, j] = self.__solver.IntVar(0, 1, f'table_{k}_{i}_{j}')

        self.__courier_distance = [self.__solver.IntVar(0, instance.max_path, f'courier_distance_{k}') for k in
                                   range(self._instance.m)]

        # Auxiliary variables to avoid sub-tours
        for k in range(self._instance.m):
            for i in range(self._instance.origin):
                self._u[k, i] = self.__solver.IntVar(0, self._instance.origin - 1, f'u_{k}_{i}')

    def solve(self) -> None:

        # Objective
        obj = self.__solver.IntVar(0, self._instance.max_path, 'obj')

        for k in range(self._instance.m):
            self.__courier_distance[k] = self.__solver.Sum(
                self._instance.distances[i][j] * self.__table[k, i, j] for i in range(self._instance.origin) for j in
                range(self._instance.origin))

        # Upper and lower bounds
        self.__solver.Add(obj <= self._instance.max_path)
        self.__solver.Add(obj >= self._instance.min_path)

        for k in range(self._instance.m):
            self.__solver.Add(obj >= self.__courier_distance[k])

        self.add_constraint()

        # Set the objective
        self.__solver.Minimize(obj)

        self._end_time = time.time()
        self._inst_time = self._end_time - self._start_time

        if self._inst_time >= 300:
            self._result['time'] = round(self._inst_time, 3)
            self._result['optimal'] = False
            self._result['obj'] = None
            self._result['sol'] = None

        # IT IS NECESSARY TO HANDLE THE ABSENCE OF THE RETURN
        self.__solver.SetTimeLimit(int((300 - self._inst_time - self._instance.presolve_time) * 1000))

        # Solve the model
        status = self.__solver.Solve()
        self._end_time = time.time()
        self._inst_time = self._end_time - self._start_time

        # Output
        if ((status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE)
                and not self._result):
            self._result['time'] = round(self._inst_time, 3)
            self._result['optimal'] = status == pywraplp.Solver.OPTIMAL
            self._result['obj'] = self.__solver.Objective().Value()
            self._result['sol'] = self._get_solution()

        else:

            self._result['time'] = round(self._inst_time, 3)
            self._result['optimal'] = status == pywraplp.Solver.OPTIMAL
            self._result['obj'] = None
            self._result['sol'] = None

    def add_constraint(self) -> None:
        # Constraints
        for i in range(self._instance.origin):
            for k in range(self._instance.m):
                # A courier can't move to the same item
                self.__solver.Add(self.__table[k, i, i] == 0)
                # If an item is reached, it is also left by the same courier
                self.__solver.Add(self.__solver.Sum(
                    self.__table[k, i, j] for j in range(self._instance.origin)) == self.__solver.Sum(
                    self.__table[k, j, i] for j in range(self._instance.origin)))

        for j in range(self._instance.origin - 1):
            # Every item is delivered
            self.__solver.Add(self.__solver.Sum(
                self.__table[k, i, j] for k in range(self._instance.m) for i in range(self._instance.origin)) == 1)

        for k in range(self._instance.m):
            # Couriers start at the origin and end at the origin
            self.__solver.Add(self.__solver.Sum(
                self.__table[k, self._instance.origin - 1, j] for j in range(self._instance.origin - 1)) == 1)
            self.__solver.Add(self.__solver.Sum(
                self.__table[k, j, self._instance.origin - 1] for j in range(self._instance.origin - 1)) == 1)

            # Each courier can carry at most max_load items
            self.__solver.Add(self.__solver.Sum(
                self.__table[k, i, j] * self._instance.size[j] for i in range(self._instance.origin) for j in
                range(self._instance.origin - 1)) <= self._instance.max_load[k])

            # Each courier must visit at least min_packs items and at most max_path_length items
            self.__solver.Add(self.__solver.Sum(self.__table[k, i, j] for i in range(self._instance.origin) for j in
                                                range(self._instance.origin - 1)) >= self._instance.min_packs)
            self.__solver.Add(self.__solver.Sum(self.__table[k, i, j] for i in range(self._instance.origin) for j in
                                                range(self._instance.origin - 1)) <= self._instance.max_packs)

        # If a courier goes for i to j then it cannot go from j to i, except for the origin
        # (this constraint it is not necessary for the model to work, but check if it improves the solution)
        for k in range(self._instance.m):
            for i in range(self._instance.origin - 1):
                for j in range(self._instance.origin - 1):
                    if i != j:
                        self.__solver.Add(self.__table[k, i, j] + self.__table[k, j, i] <= 1)

        # Sub-tour elimination
        for k in range(self._instance.m):
            for i in range(self._instance.origin - 1):
                for j in range(self._instance.origin - 1):
                    if i != j:
                        self.__solver.Add(
                            self._u[k, j] >= self._u[k, i] + 1 - self._instance.origin * (1 - self.__table[k, i, j]))


class Pulp_model(Abstract_model):

    def __init__(self, lib: 'str', instance: 'Instance'):
        super().__init__(lib, instance)
        self._table = {}

        # Create model
        self.__model = pulp.LpProblem("CourierProblem", pulp.LpMinimize)
        self._inst_time = 0
        # Create variables
        self.__table = pulp.LpVariable.dicts("table",
                                             ((k, i, j) for k in range(instance.m) for i in range(instance.origin) for j
                                              in
                                              range(instance.origin)),
                                             lowBound=0, upBound=1, cat=pulp.LpBinary)

        self.__courier_distance = pulp.LpVariable.dicts("courier_distance", (range(instance.m)), cat=pulp.LpInteger,
                                                        lowBound=0, upBound=instance.max_path)

        # Auxiliary variables to avoid sub-tours
        for k in range(self._instance.m):
            for i in range(self._instance.origin):
                self._u[k, i] = pulp.LpVariable(f'u_{k}_{i}', lowBound=1, upBound=self._instance.origin,
                                                cat=pulp.LpInteger)

    def solve(self) -> None:
        # Objective
        obj = pulp.LpVariable('obj', cat=pulp.LpInteger)

        for k in range(self._instance.m):
            self.__model += self.__courier_distance[k] == pulp.lpSum(
                self._instance.distances[i][j] * self.__table[k, i, j] for i in range(self._instance.origin) for j in
                range(self._instance.origin))

        # Upper and lower bounds
        self.__model += obj <= self._instance.max_path
        self.__model += obj >= self._instance.min_path

        for k in range(self._instance.m):
            self.__model += obj >= self.__courier_distance[k]

        # Constraints
        self.add_constraint()

        # Set the objective
        self.__model += obj

        # Solve the problem
        print(self._instance.presolve_time, self._inst_time)
        solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=int(300 - self._inst_time - self._instance.presolve_time))
        self._status = self.__model.solve(solver)

        self._end_time = time.time()
        self._inst_time = self._end_time - self._start_time

        # Output
        if self._status == pulp.LpStatusOptimal or self._status == pulp.LpStatusNotSolved:
            self._result['time'] = round(self._inst_time, 3)
            self._result['optimal'] = self._status == pulp.LpStatusOptimal
            self._result['obj'] = pulp.value(self.__model.objective)
            self._result['sol'] = self._get_solution()

        else:
            self._result['time'] = round(self._inst_time, 3)
            self._result['optimal'] = self._status == pulp.LpStatusOptimal
            self._result['obj'] = None
            self._result['sol'] = None

    def add_constraint(self) -> None:
        for i in range(self._instance.origin):
            for k in range(self._instance.m):
                # A courier can't move to the same item
                self.__model += self.__table[k, i, i] == 0
                # If an item is reached, it is also left by the same courier
                self.__model += pulp.lpSum(self.__table[k, i, j] for j in range(self._instance.origin)) == pulp.lpSum(
                    self.__table[k, j, i] for j in range(self._instance.origin))

        for j in range(self._instance.origin - 1):
            # Every item is delivered
            self.__model += pulp.lpSum(
                self.__table[k, i, j] for k in range(self._instance.m) for i in range(self._instance.origin)) == 1

        for k in range(self._instance.m):
            # Couriers start at the origin and end at the origin
            self.__model += pulp.lpSum(
                self.__table[k, self._instance.origin - 1, j] for j in range(self._instance.origin - 1)) == 1
            self.__model += pulp.lpSum(
                self.__table[k, j, self._instance.origin - 1] for j in range(self._instance.origin - 1)) == 1

            # Each courier can carry at most max_load items
            self.__model += pulp.lpSum(
                self.__table[k, i, j] * self._instance.size[j] for i in range(self._instance.origin) for j in
                range(self._instance.origin - 1)) <= self._instance.max_load[k]

            # Each courier must visit at least min_packs items and at most max_path_length items
            self.__model += pulp.lpSum(self.__table[k, i, j] for i in range(self._instance.origin) for j in
                                       range(self._instance.origin - 1)) >= self._instance.min_packs
            self.__model += pulp.lpSum(self.__table[k, i, j] for i in range(self._instance.origin) for j in
                                       range(self._instance.origin - 1)) <= self._instance.max_packs

        # If a courier goes for i to j then it cannot go from j to i, except for the origin
        # (this constraint it is not necessary for the model to work, but check if it improves the solution)
        for k in range(self._instance.m):
            for i in range(self._instance.origin - 1):
                for j in range(self._instance.origin - 1):
                    if i != j:
                        self.__model += self.__table[k, i, j] + self.__table[k, j, i] <= 1

        # Sub-tour elimination
        for k in range(self._instance.m):
            for i in range(self._instance.origin - 1):
                for j in range(self._instance.origin - 1):
                    if i != j:
                        self.__model += self._u[k, j] - self._u[k, i] >= 1 - self._instance.origin * (
                                1 - self.__table[k, i, j])
