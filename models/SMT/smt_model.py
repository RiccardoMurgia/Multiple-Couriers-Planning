import z3
import time
import numpy as np

from os.path import join
from models.Abstract_model import Abstract_model
from instance import Instance


class Z3_smt_model(Abstract_model):

    def __init__(self, lib: 'str', instance: Instance):
        super().__init__(lib, instance)
        self._model = None
        self._optimal_solution_found = False

        self._solver = z3.Solver()

        self._table = np.array([[[z3.Bool(f'table_{k}_{i}_{j}') for j in range(self._instance.origin)]
                                 for i in range(self._instance.origin)] for k in range(self._instance.m)])

        self._courier_distance = np.array([z3.Int(f'courier_distance_{k}') for k in range(self._instance.m)])

        # Lower and upper bounds on the courier distance for each courier
        for k in range(self._instance.m):
            self._solver.add(self._courier_distance[k] >= 0)
            self._solver.add(self._courier_distance[k] <= self._instance.max_path)

        # Auxiliary variables to avoid Sub-tours
        self._u = np.array(
            [[z3.Int(f'u_{k}_{i}') for i in range(self._instance.origin)] for k in range(self._instance.m)])

        # Lower and upper bounds on the auxiliary variables
        for k in range(instance.m):
            for i in range(instance.origin):
                self._solver.add(self._u[k][i] >= 0)
                self._solver.add(self._u[k][i] <= instance.origin - 1)

        self.__build()
        self._end_time = time.time()

    def __build(self):
        self.obj = z3.Int('obj')

        # Upper and lower bounds on the objective
        self._solver.add(self.obj <= self._instance.max_path)
        self._solver.add(self.obj >= self._instance.min_path)

        # Calculate the courier distance for each courier
        for k in range(self._instance.m):
            self._courier_distance[k] = z3.Sum(
                [z3.If(self._table[k][i][j], 1, 0) * self._instance.distances[i][j]
                 for i in range(self._instance.origin) for j in range(self._instance.origin)])

        # Objective
        for k in range(self._instance.m):
            self._solver.add(self.obj >= self._courier_distance[k])

        self.add_constraints()

    def save(self, save_folder: 'str'):
        f = open(join(save_folder, f'{self._instance.name}.smt2'), "x")
        smt_file = self._solver.to_smt2()
        f.write(smt_file)
        f.close()
        print(f"exported model to file {self._instance.name} into folder {save_folder}")

    def solve(self, processes=1, timeout: 'int' = 300) -> None:
        self._inst_time = self._end_time - self._start_time

        if self._inst_time >= timeout:
            self._result['time'] = round(self._inst_time, 3)
            self._result['optimal'] = self._optimal_solution_found
            self._result['obj'] = None
            self._result['sol'] = None

        self._solver.set("timeout", int(timeout - self._inst_time) * 1000)
        if processes > 1:
            self._solver.set("threads", processes)
        while self._solver.check() == z3.sat:
            self._model = self._solver.model()
            self._solver.add(self.obj < self._model[self.obj])

            # Check if the solution is optimal
            if self._solver.check() == z3.unsat:
                self._end_time = time.time()
                self._inst_time = self._end_time - self._start_time

                # Convert table to a list of lists of booleans
                self._table = [[[self._model[self._table[k][i][j]] for j in range(self._instance.origin)] for i in
                                range(self._instance.origin)] for k
                               in
                               range(self._instance.m)]

                self._optimal_solution_found = True

        self._result['time'] = round(self._inst_time, 3)
        self._result['optimal'] = self._optimal_solution_found
        self._result['obj'] = self._model[self.obj].as_long()
        self._result['sol'] = self._get_solution()

    def add_constraints(self) -> None:
        # Constraints
        for k in range(self._instance.m):
            for i in range(self._instance.origin):
                # A courier can't move to the same item
                self._solver.add(self._table[k][i][i] == False)
                # If an item is reached, it is also left by the same courier
                self._solver.add(z3.Sum([self._table[k][i][j] for j in range(self._instance.origin)])
                                 == z3.Sum([self._table[k][j][i] for j in range(self._instance.origin)]))
                # REDUNDANT
                self._solver.add(z3.Or([self._table[k][i][j] for j in range(self._instance.origin)]) == z3.Or(
                    [self._table[k][j][i] for j in range(self._instance.origin)]))
                self._solver.add(
                    z3.PbEq([(self._table[k][i][j], 1) for j in range(self._instance.origin)], 1) == z3.PbEq(
                        [(self._table[k][j][i], 1) for j in range(self._instance.origin)], 1))

        for j in range(self._instance.origin - 1):
            # Every item is delivered using PbEq
            self._solver.add(
                z3.PbEq(
                    [(self._table[k][i][j], 1) for k in range(self._instance.m) for i in range(self._instance.origin)],
                    1))
            # REDUNDANT
            self._solver.add(
                z3.PbEq(
                    [(self._table[k][j][i], 1) for k in range(self._instance.m) for i in range(self._instance.origin)],
                    1))

        for k in range(self._instance.m):
            # Each courier can carry at most max_load items
            self._solver.add(
                z3.PbLe([(self._table[k][i][j], self._instance.size[j]) for i in range(self._instance.origin) for j in
                         range(self._instance.origin - 1)], self._instance.max_load[k]))

            # Couriers start at the origin and end at the origin
            self._solver.add(
                z3.Sum([self._table[k][self._instance.origin - 1][j] for j in range(self._instance.origin - 1)]) == 1)
            self._solver.add(
                z3.Sum([self._table[k][j][self._instance.origin - 1] for j in range(self._instance.origin - 1)]) == 1)

            # Each courier must visit at least min_packs items and at most max_path_length items
            self._solver.add(z3.Sum(
                [self._table[k][i][j] for i in range(self._instance.origin) for j in
                 range(self._instance.origin - 1)]) >= self._instance.min_packs)
            self._solver.add(z3.Sum([self._table[k][i][j] for i in range(self._instance.origin) for j in
                                     range(self._instance.origin - 1)]) <= self._instance.max_path)

        for k in range(self._instance.m):
            for i in range(self._instance.origin - 1):
                for j in range(self._instance.origin - 1):
                    if i != j:
                        # If a courier goes for i to j then it cannot go from j to i, except for the origin
                        self._solver.add(z3.Not(z3.And(self._table[k][i][j], self._table[k][j][i])))

                        # Sub-tour elimination
                        self._solver.add(self._u[k][j]
                                         >= self._u[k][i] + 1 - self._instance.origin * (
                                                 1 - z3.If(self._table[k][i][j], 1, 0)))
