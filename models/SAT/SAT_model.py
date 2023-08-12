from z3 import And, Or, Not, Implies, sat, Solver, Bool
from instance import Instance
import numpy as np
from itertools import combinations
from models.SAT.Sat_numbers import D2B, iff


def flatten(e):
    if len(e) == 0:
        return []
    if isinstance(e[0], list):
        return flatten(e[0]) + flatten(e[1:])
    return [e[0]] + flatten(e[1:])


class Sat_model:

    def __init__(self):
        self.my_solver = Solver()

    @staticmethod
    def __at_least_one(bool_vars: list):
        return Or(bool_vars)

    @staticmethod
    def __at_most_one(bool_vars: list):
        return [
            Not(And(pair[0], pair[1])) for pair in combinations(bool_vars, 2)
        ]

    @staticmethod
    def __exactly_one(bool_vars: list):
        return Sat_model.__at_most_one(bool_vars) + [Sat_model.__at_least_one(bool_vars)]

    def __path_length_boundaries_constraint(self, min_p, max_p):
        self.my_solver.add(min_p)
        self.my_solver.add(max_p)

    def __courier_load_constraint(self, max_load_list):
        for load in max_load_list:
            self.my_solver.add(load.get_constraints())

    def __packages_size_constraint(self, sizes):
        for size in sizes:
            self.my_solver.add(size.get_constraints())

    def __at_least_one_pack_constraint(self, m, courier_load):
        for j in range(m):
            self.my_solver.add(self.__at_least_one(courier_load[j, :].tolist()))

    def __max_load_constraint(self, m, n, courier_load, loads, max_load_list, sizes):
        for j in range(m):
            for i in range(n):
                loads[j] += sizes[i] * courier_load[j, i]
            self.my_solver.add(loads[j].get_constraints())
            self.my_solver.add(max_load_list[j].add_geq(loads[j]))

    def __unique_assignment(self, n, courier_load):
        for i in range(n):
            self.my_solver.add(self.__exactly_one(courier_load[:, i].tolist()))

    def __build_base_model(self, instance):
        # Reading instance features
        m = instance.m
        n = instance.n
        max_path = instance.max_path
        min_path = instance.min_path
        max_load = instance.max_load
        size = instance.size
        dm = np.array([[D2B(instance.distances[i, j]) for i in range(n + 1)] for j in range(n + 1)])

        # Bynirization
        max_load_list = [D2B(max_load[j]) for j in range(m)]
        sizes = [D2B(size[i]) for i in range(n)]
        distances = [D2B(0, "zero") for _ in range(m)]
        loads = [D2B(0, "zero") for _ in range(m)]
        min_path = D2B(min_path)
        max_path = D2B(max_path)

        # Auxiliary matrices initialization
        courier_route = np.empty(shape=(m, n + 1, n + 1), dtype=object)
        courier_load = np.empty(shape=(m, n), dtype=object)
        indices_cl = np.indices(courier_load.shape)
        indices_cr = np.indices(courier_route.shape)

        for j, i, k in zip(indices_cr[0].flatten(), indices_cr[1].flatten(), indices_cr[2].flatten()):
            courier_route[j, i, k] = Bool(f"courier_{j}_goes_from_{i}_to_{k}")

        for j, i, in zip(indices_cl[0].flatten(), indices_cl[1].flatten()):
            courier_load[j, i] = Bool(f"courier_{j}_pack{i}")

        # Constraints adding

        self.__path_length_boundaries_constraint(min_path.get_constraints(), max_path.get_constraints())

        self.__courier_load_constraint(max_load_list)

        self.__packages_size_constraint(sizes)

        self.__at_least_one_pack_constraint(m, courier_load)

        self.__max_load_constraint(m, n, courier_load, loads, max_load_list, sizes)

        self.__unique_assignment(n, courier_load)

        for j in range(m):
            self.my_solver.add(self.__exactly_one(flatten(courier_route[j, n, :n].tolist())))
            self.my_solver.add(self.__exactly_one(flatten(courier_route[j, :n, n].tolist())))
            self.my_solver.add(Not(courier_route[j, n, n]))
            for i in range(n):
                self.my_solver.add(self.__at_most_one(flatten(courier_route[j, i, :].tolist())))
                self.my_solver.add(self.__at_most_one(flatten(courier_route[j, :, i].tolist())))
                self.my_solver.add(iff(courier_load[j, i],
                                       And(Or(courier_route[j, i, :].tolist()), Or(courier_route[j, :, i].tolist()))))
                self.my_solver.add(iff(Not(courier_load[j, i]),
                                       And([Not(e) for e in courier_route[j, i, :]] + [Not(e) for e in
                                                                                       courier_route[j, :, i]])))

                for k in range(n):
                    self.my_solver.add(Not(And(courier_route[j, i, k], courier_route[j, k, i])))
                    self.my_solver.add(Not(courier_route[j, i, i]))
            for i in range(n + 1):
                for k in range(n + 1):
                    d = dm[i, k] * courier_route[j, i, k]
                    distances[j] += d * courier_route[j, i, k]
            self.my_solver.add(distances[j].get_constraints())

        max_len = max(distances, key=lambda d: d.binary_length).binary_length
        max_distance = D2B(binary=[Bool(f"max_distance_{f}") for f in range(max_len + 1)])
        self.my_solver.add(Or([And(distances[j].add_equal(max_distance)) for j in range(m)]))
        self.my_solver.add(And([And(max_distance.add_geq(distances[j])) for j in range(m)]))
        self.my_solver.add(min_path.add_leq(max_distance))
        self.my_solver.add(max_path.add_geq(max_distance))
        return self.my_solver, courier_load, courier_route, loads, distances, max_load_list, max_distance

    def __update_max_distance(self, s, max_distance, model):
        new_min_path = D2B(max_distance.to_decimal(model), "new_min_path")
        s.add(new_min_path.get_constraints())
        s.add(new_min_path.add_greater(max_distance))
        return s

    def solve(self, instance: 'Instance'):

        s, courier_load, courier_route, loads, distances, max_load, max_distance = self.__build_base_model(instance)
        print()
        print("constraints created")
        while (s.check() == sat):
            m = s.model()
            for j in range(instance.m):
                print(
                    "=========================================================================")
                print("courier", j)
                print("packs", [i + 1 for i in range(instance.n) if m.evaluate(courier_load[j, i])])
                print("route", self.get_route(courier_route[j, :, :], m, instance.n + 1, instance.n + 1))
                print("load ", loads[j].to_decimal(m))
                print("max load ", max_load[j].to_decimal(m))
                print("distance ", distances[j].to_decimal(m))
            print(
                "=========================================================================")
            print("max distance", max_distance.to_decimal(m))
            print("========================================NEW SOLUTION===============================")
            s = self.__update_max_distance(s, max_distance, m)

    def get_route(self, route_matrix, model, start, end):
        pairs = [(i + 1, j + 1) for i in range(route_matrix.shape[0]) for j in range(route_matrix.shape[1]) if
                 model.evaluate(route_matrix[i, j])]
        route = [start]
        current = start
        print(pairs)

        def get_next(current):
            for pair in pairs:
                if pair[0] == current:
                    return pair[1]

        while True:
            current = get_next(current)
            route.append(current)
            if current == end:
                return route


Sat_model().solve(Instance('instances/inst00.dat'))