from z3 import And, Or, Not, sat, Solver, Bool
from instance import Instance
import numpy as np
from itertools import combinations
from models.SAT.Sat_numbers import D2B


def flatten(e):
    if len(e) == 0:
        return []
    if isinstance(e[0], list):
        return flatten(e[0]) + flatten(e[1:])
    return [e[0]] + flatten(e[1:])


class Sat_model:
    def __at_least_one(self, bool_vars: list):
        return Or(bool_vars)

    def __at_most_one(self, bool_vars: list):
        return [
            Not(And(pair[0], pair[1])) for pair in combinations(bool_vars, 2)
        ]

    def __exactly_one(self, bool_vars: list):
        return self.__at_most_one(bool_vars) + [self.__at_least_one(bool_vars)]

    def solve(self, instance: 'Instance'):
        max_load = [D2B(instance.max_load[j]) for j in range(instance.m)]
        sizes = [D2B(instance.size[i]) for i in range(instance.n)]
        distances = [D2B(0, "zero") for j in range(instance.m)]
        loads = [0 for i in range(instance.m)]
        s = Solver()
        for load in max_load:
            s.add(load.get_constraints())
        for size in sizes:
            s.add(size.get_constraints())
        courier_route = np.empty(
            shape=(instance.m, instance.max_path_length, instance.n+1),
            dtype=object)
        for j in range(instance.m):
            for i in range(instance.max_path_length):
                for k in range(instance.n+1):
                    courier_route[j, i, k] = Bool(
                        f'courier_{j}_moment_{i}_pack_{k}')
        print("created the matrix")
        for j in range(instance.m):
            s.add(courier_route[j, 0, instance.n])
            s.add(
                courier_route[j, instance.max_path_length-1, instance.n])
            for i in range(0, instance.max_path_length):
                for k in range(instance.n):
                    s.add(self.__exactly_one(
                        flatten(courier_route[:, :, k].tolist())))
                s.add(self.__exactly_one(
                    flatten(courier_route[j, i, :].tolist())))

            print(
                f"{(j+1) * i /(instance.m * instance.max_path_length) * 100} complete", end='\r')
            for i in range(1, instance.min_packs + 1):
                s.add(Not(courier_route[j, i, instance.n]))

            loads[j] = D2B(0, "zero")
            for k in range(instance.n):
                op = sizes[k] * \
                    Or(flatten(courier_route[j, :, k].tolist()))
                s.add(op.get_constraints())
                loads[j] += op
                s.add(loads[j].get_constraints())

            s.add(max_load[j].add_geq(loads[j]))

        print()
        print("constraints created")
        if s.check() == sat:
            m = s.model()
            for j in range(instance.m):
                print(
                    "=========================================================================")
                print(j)
                print([k+1 for k in range(instance.n+1)
                      for i in range(instance.max_path_length)
                      if m.evaluate(courier_route[j, i, k])])
                print(loads[j].to_decimal(m))
                print(max_load[j].to_decimal(m))
        else:
            print("nope")


Sat_model().solve(Instance('instances/inst00.dat'))
