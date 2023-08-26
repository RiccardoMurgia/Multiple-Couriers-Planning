import mip
import z3
from ortools.linear_solver import pywraplp
import pulp

import os
import time
import multiprocessing
import datetime
import json
import jsbeautifier

from instance import Instance

LAMBDA = 0.1


class Mip_model:
    def __init__(self, instance: 'Instance', param, h: 'bool' = False, verbose: 'bool' = False):
        self.__lib = 'mip'
        self.__start_time = time.time()
        self.__end_time = None
        self.__inst_time = None
        self.__instance = instance
        self.__param = param
        self.__h = h
        self.__u = {}
        self.__result = {}

        # Create model
        self.__model = mip.Model(solver_name=mip.CBC)

        # Create variables
        self.__table = {}
        for k in range(self.__instance.m):
            for i in range(self.__instance.origin):
                for j in range(self.__instance.origin):
                    self.__table[k, i, j] = self.__model.add_var(var_type=mip.INTEGER, name=f'table_{k}_{i}_{j}')

        self.__courier_routes = None
        self.__courier_distance = [self.__model.add_var(var_type=mip.INTEGER, name=f'courier_distance_{k}') for k in
                                   range(self.__instance.m)]

        if not verbose:
            self.__model.verbose = 0

    def __get_solution(self) -> 'list':

        # Create a dictionary to store the routes for each courier
        courier_routes = {k: [] for k in range(self.__instance.m)}

        # Extract and populate courier routes
        for k in range(self.__instance.m):
            if self.__lib == "mip":
                self.__courier_routes[k] = [[i, j] for i in range(self.__instance.origin) for j in
                                            range(self.__instance.origin) if
                                            self.__table[k, i, j].x == 1]
            elif self.__lib == "ortools":
                self.__courier_routes[k] = [[i, j] for i in range(self.__instance.origin) for j in
                                            range(self.__instance.origin) if
                                            self.__table[k, i, j].solution_value() == 1]
            elif self.__lib == "pulp":
                self.__courier_routes[k] = [[i, j] for i in range(self.__instance.origin) for j in
                                            range(self.__instance.origin) if
                                            self.__table[k, i, j].value() == 1]
            elif self.__lib == "z3":
                self.__courier_routes[k] = [[i, j] for i in range(self.__instance.origin) for j in
                                            range(self.__instance.origin) if
                                            self.__table[k][i][j]]

        # Reorder the routes to start from the origin
        for k in range(self.__instance.m):
            origin_index = next(
                (i for i, route in enumerate(courier_routes[k]) if route[0] == self.__instance.origin - 1),
                None)
            if origin_index is not None:
                courier_routes[k] = courier_routes[k][origin_index:] + courier_routes[k][:origin_index]

        # Reorder it in a way that the first element of the tuple i is the second element of the tuple i-1
        for k in range(self.__instance.m):
            for i in range(1, len(courier_routes[k])):
                if courier_routes[k][i][0] != courier_routes[k][i - 1][1]:
                    for j in range(i + 1, len(courier_routes[k])):
                        if courier_routes[k][i][0] == courier_routes[k][j][1]:
                            courier_routes[k][i], courier_routes[k][j] = courier_routes[k][j], courier_routes[k][i]
                            break

        # Remove instance.origin - 1 from the routes
        for k in range(self.__instance.m):
            courier_routes[k] = [route[0] for route in courier_routes[k]]
            if len(courier_routes[k]) > 0:
                courier_routes[k].pop(0)

        # Create a list to store the routes for each courier
        routes = [courier_routes[k] for k in range(self.__instance.m)]

        # print(routes)
        return routes

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

    def __add_constraint(self) -> None:

        # Constraints
        for i in range(self.__instance.origin):
            for k in range(self.__instance.m):
                # A courier can't move to the same item
                self.__model += self.__table[k, i, i] == 0
                # If an item is reached, it is also left by the same courier
                self.__model += mip.xsum(self.__table[k, i, j] for j in range(self.__instance.origin)) == mip.xsum(
                    self.__table[k, j, i] for j in range(self.__instance.origin))

        # Every item is delivered
        for j in range(self.__instance.origin - 1):
            self.__model += mip.xsum(
                self.__table[k, i, j] for k in range(self.__instance.m) for i in range(self.__instance.origin)) == 1

        for k in range(self.__instance.m):
            # Couriers start at the origin and end at the origin
            self.__model += mip.xsum(
                self.__table[k, self.__instance.origin - 1, j] for j in range(self.__instance.origin - 1)) == 1
            self.__model += mip.xsum(
                self.__table[k, j, self.__instance.origin - 1] for j in range(self.__instance.origin - 1)) == 1

            # Each courier can carry at most max_load items
            self.__model += mip.xsum(
                self.__table[k, i, j] * self.__instance.size[j] for i in range(self.__instance.origin) for j in
                range(self.__instance.origin - 1)) <= self.__instance.max_load[k]

            # Each courier must visit at least min_packs items and at most max_path_length items
            self.__model += mip.xsum(self.__table[k, i, j] for i in range(self.__instance.origin) for j in
                                     range(self.__instance.origin - 1)) >= self.__instance.min_packs
            self.__model += mip.xsum(self.__table[k, i, j] for i in range(self.__instance.origin) for j in
                                     range(self.__instance.origin - 1)) <= self.__instance.max_path_length

            # If a courier goes for i to j then it cannot go from j to i, except for the origin
            # (this constraint it is not necessary for the model to work, but check if it improves the solution)
            for k in range(self.__instance.m):
                for i in range(self.__instance.origin - 1):
                    for j in range(self.__instance.origin - 1):
                        if i != j:
                            self.__model += self.__table[k, i, j] + self.__table[k, j, i] <= 1

            # Sub-tour elimination
            for k in range(self.__instance.m):
                for i in range(self.__instance.origin - 1):
                    for j in range(self.__instance.origin - 1):
                        if i != j:
                            self.__model += self.__u[k, j] - self.__u[k, i] >= 1 - self.__instance.origin * (
                                    1 - self.__table[k, i, j])

    def solve(self, timeout: 'int' = 300000, processes: 'int' = 1) -> None:
        # Auxiliary variables to avoid sub-tours

        for k in range(self.__instance.m):
            for i in range(self.__instance.origin):
                self.__u[k, i] = self.__model.add_var(var_type=mip.INTEGER, lb=1, ub=self.__instance.origin,
                                                      name=f'u_{k}_{i}')

        # Objective
        obj = self.__model.add_var(var_type=mip.INTEGER, name='obj')

        for k in range(self.__instance.m):
            self.__model += self.__courier_distance[k] == mip.xsum(
                self.__instance.distances[i][j] * self.__table[k, i, j] for i in range(self.__instance.origin) for j in
                range(self.__instance.origin))

        # Upper and lower bounds
        self.__model += obj <= self.__instance.max_path
        self.__model += obj >= self.__instance.min_path

        for k in range(self.__instance.m):
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
            initial_routes = self.clark_wright_savings(self.__instance.dist, self.__instance.max_load[0])

            # Initialize routes using Clark and Wright Savings Algorithm
            for k, route in enumerate(initial_routes):
                for i, j in zip(route, route[1:]):
                    self.__table[k, i, j].start = 1

            print('Using warm start CWS: Initial solution found in {} seconds'.format(time.time() - self.__start_time))

        self.__end_time = time.time()
        self.__inst_time = self.__end_time - self.__start_time

        if self.__inst_time >= 300:
            self.__result['time'] = round(self.__inst_time, 3)
            self.__result['optimal'] = False
            self.__result['obj'] = None
            self.__result['sol'] = None

        # IT IS NECESSARY TO HANDLE THE ABSENCE OF THE RETURN

        status = self.__model.optimize(max_seconds=int(300 - self.__inst_time))
        self.__end_time = time.time()  # fixme
        self.__inst_time = self.__end_time - self.__start_time

        # Output
        if ((status == mip.OptimizationStatus.OPTIMAL or status == mip.OptimizationStatus.FEASIBLE)
                and not self.__result):
            self.__result['time'] = round(self.__inst_time, 3)
            self.__result['optimal'] = status == mip.OptimizationStatus.OPTIMAL
            self.__result['obj'] = self.__model.objective_value
            self.__result['sol'] = self.__get_solution()

        else:
            self.__result['time'] = round(self.__inst_time, 3)
            self.__result['optimal'] = status == mip.OptimizationStatus.OPTIMAL
            self.__result['obj'] = None
            self.__result['sol'] = None

    def get_result(self) -> dict:
        return self.__result


class Or_model:

    def __init__(self, instance, solv='CBC_MIXED_INTEGER_PROGRAMMING'):
        self.__lib = 'ortools'
        self.__start_time = time.time()
        self.__end_time = None
        self.__inst_time = None
        self.__instance = instance
        self.__u = {}
        self.__result = {}

        # Create solver
        self.__solver = pywraplp.Solver.CreateSolver(solv)

        self.__table = {}
        for k in range(instance.m):
            for i in range(instance.origin):
                for j in range(instance.origin):
                    self.__table[k, i, j] = self.__solver.IntVar(0, 1, f'table_{k}_{i}_{j}')

        self.__courier_distance = [self.__solver.IntVar(0, instance.max_path, f'courier_distance_{k}') for k in
                                   range(self.__instance.m)]
        self.__courier_routes = None

    def solve(self, timeout: 'int' = 300000, processes: 'int' = 1) -> None:
        # Auxiliary variables to avoid sub-tours
        for k in range(self.__instance.m):
            for i in range(self.__instance.origin):
                self.__u[k, i] = self.__solver.IntVar(0, self.__instance.origin - 1, f'u_{k}_{i}')

        # Objective
        obj = self.__solver.IntVar(0, self.__instance.max_path, 'obj')

        for k in range(self.__instance.m):
            self.__courier_distance[k] = self.__solver.Sum(
                self.__instance.distances[i][j] * self.__table[k, i, j] for i in range(self.__instance.origin) for j in
                range(self.__instance.origin))

        # Upper and lower bounds
        self.__solver.Add(obj <= self.__instance.max_path)
        self.__solver.Add(obj >= self.__instance.min_path)

        for k in range(self.__instance.m):
            self.__solver.Add(obj >= self.__courier_distance[k])

        self.add_constraint()

        # Set the objective
        self.__solver.Minimize(obj)

        self.__end_time = time.time()
        self.__inst_time = self.__end_time - self.__start_time

        if self.__inst_time >= 300:
            self.__result['time'] = round(self.__inst_time, 3)
            self.__result['optimal'] = False
            self.__result['obj'] = None
            self.__result['sol'] = None

        # IT IS NECESSARY TO HANDLE THE ABSENCE OF THE RETURN
        self.__solver.SetTimeLimit(int((300 - self.__inst_time) * 1000))

        # Solve the model
        status = self.__solver.Solve()
        self.__end_time = time.time()
        self.__inst_time = self.__end_time - self.__start_time

        # Output
        if ((status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE)
                and not self.__result):
            self.__result['time'] = round(self.__inst_time, 3)
            self.__result['optimal'] = status == pywraplp.Solver.OPTIMAL
            self.__result['obj'] = self.__solver.Objective().Value()
            self.__result['sol'] = self.__get_solution()

        else:

            self.__result['time'] = round(self.__inst_time, 3)
            self.__result['optimal'] = status == pywraplp.Solver.OPTIMAL
            self.__result['obj'] = None
            self.__result['sol'] = None

    def add_constraint(self) -> None:
        # Constraints
        for i in range(self.__instance.origin):
            for k in range(self.__instance.m):
                # A courier can't move to the same item
                self.__solver.Add(self.__table[k, i, i] == 0)
                # If an item is reached, it is also left by the same courier
                self.__solver.Add(self.__solver.Sum(
                    self.__table[k, i, j] for j in range(self.__instance.origin)) == self.__solver.Sum(
                    self.__table[k, j, i] for j in range(self.__instance.origin)))

        for j in range(self.__instance.origin - 1):
            # Every item is delivered
            self.__solver.Add(self.__solver.Sum(
                self.__table[k, i, j] for k in range(self.__instance.m) for i in range(self.__instance.origin)) == 1)

        for k in range(self.__instance.m):
            # Couriers start at the origin and end at the origin
            self.__solver.Add(self.__solver.Sum(
                self.__table[k, self.__instance.origin - 1, j] for j in range(self.__instance.origin - 1)) == 1)
            self.__solver.Add(self.__solver.Sum(
                self.__table[k, j, self.__instance.origin - 1] for j in range(self.__instance.origin - 1)) == 1)

            # Each courier can carry at most max_load items
            self.__solver.Add(self.__solver.Sum(
                self.__table[k, i, j] * self.__instance.size[j] for i in range(self.__instance.origin) for j in
                range(self.__instance.origin - 1)) <= self.__instance.max_load[k])

            # Each courier must visit at least min_packs items and at most max_path_length items
            self.__solver.Add(self.__solver.Sum(self.__table[k, i, j] for i in range(self.__instance.origin) for j in
                                                range(self.__instance.origin - 1)) >= self.__instance.min_packs)
            self.__solver.Add(self.__solver.Sum(self.__table[k, i, j] for i in range(self.__instance.origin) for j in
                                                range(self.__instance.origin - 1)) <= self.__instance.max_path_length)

        # If a courier goes for i to j then it cannot go from j to i, except for the origin
        # (this constraint it is not necessary for the model to work, but check if it improves the solution)
        for k in range(self.__instance.m):
            for i in range(self.__instance.origin - 1):
                for j in range(self.__instance.origin - 1):
                    if i != j:
                        self.__solver.Add(self.__table[k, i, j] + self.__table[k, j, i] <= 1)

        # Sub-tour elimination
        for k in range(self.__instance.m):
            for i in range(self.__instance.origin - 1):
                for j in range(self.__instance.origin - 1):
                    if i != j:
                        self.__solver.Add(
                            self.__u[k, j] >= self.__u[k, i] + 1 - self.__instance.origin * (1 - self.__table[k, i, j]))

    def __get_solution(self) -> list:

        # Create a dictionary to store the routes for each courier
        courier_routes = {k: [] for k in range(self.__instance.m)}

        # Extract and populate courier routes
        for k in range(self.__instance.m):
            if self.__lib == "mip":
                self.__courier_routes[k] = [[i, j] for i in range(self.__instance.origin) for j in
                                            range(self.__instance.origin) if
                                            self.__table[k, i, j].x == 1]
            elif self.__lib == "ortools":
                self.__courier_routes[k] = [[i, j] for i in range(self.__instance.origin) for j in
                                            range(self.__instance.origin) if
                                            self.__table[k, i, j].solution_value() == 1]
            elif self.__lib == "pulp":
                self.__courier_routes[k] = [[i, j] for i in range(self.__instance.origin) for j in
                                            range(self.__instance.origin) if
                                            self.__table[k, i, j].value() == 1]
            elif self.__lib == "z3":
                self.__courier_routes[k] = [[i, j] for i in range(self.__instance.origin) for j in
                                            range(self.__instance.origin) if
                                            self.__table[k][i][j]]

        # Reorder the routes to start from the origin
        for k in range(self.__instance.m):
            origin_index = next(
                (i for i, route in enumerate(courier_routes[k]) if route[0] == self.__instance.origin - 1),
                None)
            if origin_index is not None:
                courier_routes[k] = courier_routes[k][origin_index:] + courier_routes[k][:origin_index]

        # Reorder it in a way that the first element of the tuple i is the second element of the tuple i-1
        for k in range(self.__instance.m):
            for i in range(1, len(courier_routes[k])):
                if courier_routes[k][i][0] != courier_routes[k][i - 1][1]:
                    for j in range(i + 1, len(courier_routes[k])):
                        if courier_routes[k][i][0] == courier_routes[k][j][1]:
                            courier_routes[k][i], courier_routes[k][j] = courier_routes[k][j], courier_routes[k][i]
                            break

        # Remove instance.origin - 1 from the routes
        for k in range(self.__instance.m):
            courier_routes[k] = [route[0] for route in courier_routes[k]]
            if len(courier_routes[k]) > 0:
                courier_routes[k].pop(0)

        # Create a list to store the routes for each courier
        routes = [courier_routes[k] for k in range(self.__instance.m)]

        # print(routes)
        return routes

    def get_result(self) -> dict:
        return self.__result


class Pulp_model:

    def __init__(self, instance):
        self.__lib = "pulp"
        self.__start_time = time.time()
        self.__end_time = None
        self.__inst_time = None
        self.__instance = instance
        self.__result = {}

        # Create model
        self.__model = pulp.LpProblem("CourierProblem", pulp.LpMinimize)

        # Create variables
        self.__table = pulp.LpVariable.dicts("table",
                                             ((k, i, j) for k in range(instance.m) for i in range(instance.origin) for j
                                              in
                                              range(instance.origin)),
                                             lowBound=0, upBound=1, cat=pulp.LpBinary)

        self.__courier_routes = None
        self.__courier_distance = pulp.LpVariable.dicts("courier_distance", (range(instance.m)), cat=pulp.LpInteger,
                                                        lowBound=0, upBound=instance.max_path)

        # Auxiliary variables to avoid sub-tours
        self.__u = {}

        for k in range(self.__instance.m):
            for i in range(self.__instance.origin):
                self.__u[k, i] = pulp.LpVariable(f'u_{k}_{i}', lowBound=1, upBound=self.__instance.origin,
                                                 cat=pulp.LpInteger)

    def solve(self, timeout: 'int' = 300000, processes: 'int' = 1) -> None:
        # Objective
        obj = pulp.LpVariable('obj', cat=pulp.LpInteger)

        for k in range(self.__instance.m):
            self.__model += self.__courier_distance[k] == pulp.lpSum(
                self.__instance.distances[i][j] * self.__table[k, i, j] for i in range(self.__instance.origin) for j in
                range(self.__instance.origin))

        # Upper and lower bounds
        self.__model += obj <= self.__instance.max_path
        self.__model += obj >= self.__instance.min_path

        for k in range(self.__instance.m):
            self.__model += obj >= self.__courier_distance[k]

        # Constraints
        self.add_constraint()

        # Set the objective
        self.__model += obj

        self.__end_time = time.time()
        self.__inst_time = self.__end_time - self.__start_time

        if self.__inst_time >= 300:
            self.__result['time'] = round(self.__inst_time, 3)
            self.__result['optimal'] = False
            self.__result['obj'] = None
            self.__result['sol'] = None

        # IT IS NECESSARY TO HANDLE THE ABSENCE OF THE RETURN

        # Solve the problem
        solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=int(300 - self.__inst_time))
        status = self.__model.solve(solver)

        self.__end_time = time.time()
        self.__inst_time = self.__end_time - self.__start_time

        # Output
        if (status == pulp.LpStatusOptimal or status == pulp.LpStatusNotSolved) and not self.__result:
            self.__result['time'] = round(self.__inst_time, 3)
            self.__result['optimal'] = status == pulp.LpStatusOptimal
            self.__result['obj'] = pulp.value(self.__model.objective)
            self.__result['sol'] = self.__get_solution()

        else:
            self.__result['time'] = round(self.__inst_time, 3)
            self.__result['optimal'] = status == pulp.LpStatusOptimal
            self.__result['obj'] = None
            self.__result['sol'] = None

            result = {
                "time": round(self.__inst_time, 3),
                "optimal": status == pulp.LpStatusOptimal,
                "obj": None,
                "sol": None
            }

    def add_constraint(self) -> None:
        for i in range(self.__instance.origin):
            for k in range(self.__instance.instance.m):
                # A courier can't move to the same item
                self.__model += self.__table[k, i, i] == 0
                # If an item is reached, it is also left by the same courier
                self.__model += pulp.lpSum(self.__table[k, i, j] for j in range(self.__instance.origin)) == pulp.lpSum(
                    self.__table[k, j, i] for j in range(self.__instance.origin))

        for j in range(self.__instance.origin - 1):
            # Every item is delivered
            self.__model += pulp.lpSum(
                self.__table[k, i, j] for k in range(self.__instance.m) for i in range(self.__instance.origin)) == 1

        for k in range(self.__instance.m):
            # Couriers start at the origin and end at the origin
            self.__model += pulp.lpSum(
                self.__table[k, self.__instance.origin - 1, j] for j in range(self.__instance.origin - 1)) == 1
            self.__model += pulp.lpSum(
                self.__table[k, j, self.__instance.origin - 1] for j in range(self.__instance.origin - 1)) == 1

            # Each courier can carry at most max_load items
            self.__model += pulp.lpSum(
                self.__table[k, i, j] * self.__instance.size[j] for i in range(self.__instance.origin) for j in
                range(self.__instance.origin - 1)) <= self.__instance.max_load[k]

            # Each courier must visit at least min_packs items and at most max_path_length items
            self.__model += pulp.lpSum(self.__table[k, i, j] for i in range(self.__instance.origin) for j in
                                       range(self.__instance.origin - 1)) >= self.__instance.min_packs
            self.__model += pulp.lpSum(self.__table[k, i, j] for i in range(self.__instance.origin) for j in
                                       range(self.__instance.origin - 1)) <= self.__instance.max_path_length

        # If a courier goes for i to j then it cannot go from j to i, except for the origin
        # (this constraint it is not necessary for the model to work, but check if it improves the solution)
        for k in range(self.__instance.m):
            for i in range(self.__instance.origin - 1):
                for j in range(self.__instance.origin - 1):
                    if i != j:
                        self.__model += self.__table[k, i, j] + self.__table[k, j, i] <= 1

        # Sub-tour elimination
        for k in range(self.__instance.m):
            for i in range(self.__instance.origin - 1):
                for j in range(self.__instance.origin - 1):
                    if i != j:
                        self.__model += self.__u[k, j] - self.__u[k, i] >= 1 - self.__instance.origin * (
                                1 - self.__table[k, i, j])

    def __get_solution(self) -> 'list':

        # Create a dictionary to store the routes for each courier
        courier_routes = {k: [] for k in range(self.__instance.m)}

        # Extract and populate courier routes
        for k in range(self.__instance.m):
            if self.__lib == "mip":
                self.__courier_routes[k] = [[i, j] for i in range(self.__instance.origin) for j in
                                            range(self.__instance.origin) if
                                            self.__table[k, i, j].x == 1]
            elif self.__lib == "ortools":
                self.__courier_routes[k] = [[i, j] for i in range(self.__instance.origin) for j in
                                            range(self.__instance.origin) if
                                            self.__table[k, i, j].solution_value() == 1]
            elif self.__lib == "pulp":
                self.__courier_routes[k] = [[i, j] for i in range(self.__instance.origin) for j in
                                            range(self.__instance.origin) if
                                            self.__table[k, i, j].value() == 1]
            elif self.__lib == "z3":
                self.__courier_routes[k] = [[i, j] for i in range(self.__instance.origin) for j in
                                            range(self.__instance.origin) if
                                            self.__table[k][i][j]]

        # Reorder the routes to start from the origin
        for k in range(self.__instance.m):
            origin_index = next(
                (i for i, route in enumerate(courier_routes[k]) if route[0] == self.__instance.origin - 1),
                None)
            if origin_index is not None:
                courier_routes[k] = courier_routes[k][origin_index:] + courier_routes[k][:origin_index]

        # Reorder it in a way that the first element of the tuple i is the second element of the tuple i-1
        for k in range(self.__instance.m):
            for i in range(1, len(courier_routes[k])):
                if courier_routes[k][i][0] != courier_routes[k][i - 1][1]:
                    for j in range(i + 1, len(courier_routes[k])):
                        if courier_routes[k][i][0] == courier_routes[k][j][1]:
                            courier_routes[k][i], courier_routes[k][j] = courier_routes[k][j], courier_routes[k][i]
                            break

        # Remove instance.origin - 1 from the routes
        for k in range(self.__instance.m):
            courier_routes[k] = [route[0] for route in courier_routes[k]]
            if len(courier_routes[k]) > 0:
                courier_routes[k].pop(0)

        # Create a list to store the routes for each courier
        routes = [courier_routes[k] for k in range(self.__instance.m)]

        # print(routes)
        return routes

    def get_result(self) -> dict:
        return self.__result
