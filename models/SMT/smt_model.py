import z3
import time

from models.Abstract_model import Abstract_model
from instance import Instance


class Z3_smt_model(Abstract_model):

    def __init__(self, lib: 'str', instance: Instance):
        super().__init__(lib, instance)
        self._optimal_solution_found = False

        self._table = []

        self._solver = z3.Solver()

        for k in range(self._instance.m):
            rows = []
            for i in range(instance.origin):
                cols = []
                for j in range(self._instance.origin):
                    cols.append(z3.Bool(f'table_{k}_{i}_{j}'))
                rows.append(cols)
            self._table.append(rows)

        self._courier_distance = [z3.Int(f'courier_distance_{k}') for k in range(self._instance.m)]

        # Lower and upper bounds on the courier distance for each courier
        for k in range(self._instance.m):
            self._solver.add(self._courier_distance[k] >= 0)
            self._solver.add(self._courier_distance[k] <= self._instance.max_path)

        self._u = []
        for k in range(instance.m):
            for i in range(instance.origin):
                self._u.append(z3.Int(f'u_{k}_{i}'))
                # Lower and upper bounds on the auxiliary variables
                self._solver.add(self._u[(k * instance.m) + i] >= 0)
                self._solver.add(self._u[(k * instance.m) + i] <= instance.origin - 1)

    def solve(self) -> None:
        obj = z3.Int('obj')
        # Upper and lower bounds on the objective

        self._solver.add(obj <= self._instance.max_path)
        self._solver.add(obj >= self._instance.min_path)

        # Calculate the courier distance for each courier
        for k in range(self._instance.m):
            self._courier_distance[k] = z3.Sum(
                [z3.If(self._table[k][i][j], 1, 0) * self._instance.distances[i][j] for i in
                 range(self._instance.origin) for j in
                 range(self._instance.origin)])

        # Objective
        for k in range(self._instance.m):
            self._solver.add(obj >= self._courier_distance[k])

        self.add_constraints()

        self._end_time = time.time()
        self._inst_time = self._end_time - self._start_time

        if self._inst_time >= 300:
            self._result['time'] = round(self._inst_time, 3)
            self._result['optimal'] = self._optimal_solution_found
            self._result['obj'] = None
            self._result['sol'] = None

        self._solver.set("timeout", int(300 - self._inst_time) * 1000)

        while self._solver.check() == z3.sat:
            model = self._solver.model()
            self._solver.add(obj < model[obj])

            # Check if the solution is optimal
            if self._solver.check() == z3.unsat:
                self._end_time = time.time()
                self._inst_time = self._end_time - self._start_time

                # Convert table to a list of lists of booleans
                self._table = [[[model[self._table[k][i][j]] for j in range(self._instance.origin)] for i in
                                range(self._instance.origin)] for k
                               in
                               range(self._instance.m)]

                self._optimal_solution_found = True

        self._result['time'] = round(self._inst_time, 3)
        self._result['optimal'] = self._optimal_solution_found
        self._result['obj'] = model[obj].as_long()
        self._result['sol'] = self._get_solution()

        print(type(model[obj]))

    def add_constraints(self) -> None:
        # Constraints
        for i in range(self._instance.origin):
            for k in range(self._instance.m):
                # A courier can't move to the same item
                self._solver.add(self._table[k][i][i] == False)

                # If an item is reached, it is also left by the same courier
                self._solver.add(z3.Sum([self._table[k][i][j] for j in range(self._instance.origin)])
                                 == z3.Sum([self._table[k][j][i] for j in range(self._instance.origin)]))

        for j in range(self._instance.origin - 1):
            # Every item is delivered using PbEq
            self._solver.add(z3.PbEq(
                [(self._table[k][i][j], 1) for k in range(self._instance.m) for i in range(self._instance.origin)], 1))

        for k in range(self._instance.m):
            # Couriers start at the origin and end at the origin
            self._solver.add(
                z3.Sum([self._table[k][self._instance.origin - 1][j] for j in range(self._instance.origin - 1)]) == 1)
            self._solver.add(
                z3.Sum([self._table[k][j][self._instance.origin - 1] for j in range(self._instance.origin - 1)]) == 1)

            # Each courier can carry at most max_load items
            self._solver.add(z3.Sum(
                [self._instance.size[j] * self._table[k][i][j] for i in range(self._instance.origin) for j in
                 range(self._instance.origin - 1)]) <= self._instance.max_load[k])

            # Each courier must visit at least min_packs items and at most max_path_length items
            self._solver.add(z3.Sum(
                [self._table[k][i][j] for i in range(self._instance.origin) for j in
                 range(self._instance.origin - 1)]) >= self._instance.min_packs)
            self._solver.add(z3.Sum([self._table[k][i][j] for i in range(self._instance.origin) for j in
                                     range(self._instance.origin - 1)]) <= self._instance.max_path_length)

        # If a courier goes for i to j then it cannot go from j to i, except for the origin
        # (this constraint it is not necessary for the model to work, but check if it improves the solution)
        for k in range(self._instance.m):
            for i in range(self._instance.origin - 1):
                for j in range(self._instance.origin - 1):
                    if i != j:
                        # solver.add(z3.If(table[k][i][j],1,0) + z3.If(table[k][j][i],1,0) <= 1)
                        self._solver.add(z3.PbLe([(self._table[k][i][j], 1), (self._table[k][j][i], 1)], 1))

        # Sub-tour elimination
        for k in range(self._instance.m):
            for i in range(self._instance.origin - 1):
                for j in range(self._instance.origin - 1):
                    if i != j:
                        self._solver.add(self._u[(k * self._instance.m) + j] >= self._u[
                            (k * self._instance.m) + i] + 1 - self._instance.origin * (
                                                 1 - z3.If(self._table[k][i][j], 1, 0)))
