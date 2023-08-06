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
    def __at_least_one(self, bool_vars: list):
        return Or(bool_vars)

    def __at_most_one(self, bool_vars: list):
        return [
            Not(And(pair[0], pair[1])) for pair in combinations(bool_vars, 2)
        ]

    def __exactly_one(self, bool_vars: list):
        return self.__at_most_one(bool_vars) + [self.__at_least_one(bool_vars)]

    def __build_base_model(self, instance):
        s = Solver()
        min_path = D2B(instance.min_path)
        s.add(min_path.get_constraints())
        max_path = D2B(instance.max_path)
        s.add(max_path.get_constraints())
        max_load = [D2B(instance.max_load[j]) for j in range(instance.m)]
        sizes = [D2B(instance.size[i]) for i in range(instance.n)]
        distances = [D2B(0, "zero") for _ in range(instance.m)]
        loads = [D2B(0, "zero") for _ in range(instance.m)]
        courier_load = np.empty(shape=(instance.m, instance.n), dtype=object)
        courier_route = np.empty(shape=(instance.m, instance.n + 1, instance.n + 1), dtype=object)
        s = Solver()
        for load in max_load:
            s.add(load.get_constraints())
        for size in sizes:
            s.add(size.get_constraints())
        
        for j in range(instance.m):
            for i in range(instance.n+1):
                for k in range(instance.n+1):
                    courier_route[j,i,k] = Bool(f"courier_{j}_goes_from_{i}_to_{k}")
            for i in range(instance.n):
                courier_load[j,i] = Bool(f"courier_{j}_pack{i}")

        for j in range(instance.m):
            s.add(self.__at_least_one(courier_load[j,:].tolist()))
            for i in range(instance.n):
                loads[j] += sizes[i] * courier_load[j,i]
            s.add(loads[j].get_constraints())
            s.add(max_load[j].add_geq(loads[j]))
        for i in range(instance.n):
            s.add(self.__exactly_one(courier_load[:,i].tolist()))
        
        for j in range(instance.m):
            s.add(self.__exactly_one(flatten(courier_route[j, instance.n, :instance.n].tolist())))
            s.add(self.__exactly_one(flatten(courier_route[j, :instance.n, instance.n].tolist())))
            s.add(Not(courier_route[j,instance.n,instance.n]))
            for i in range(instance.n):
                s.add(self.__at_most_one(flatten(courier_route[j,i,:].tolist())))
                s.add(self.__at_most_one(flatten(courier_route[j,:,i].tolist())))
                s.add(iff(courier_load[j,i], Or(courier_route[j,i,:].tolist())))
            for i in range(instance.n+1):
                for k in range(instance.n+1):
                    distances[j] += D2B(instance.distances[i,k], f"distance_{i}_{k}") * courier_route[j,i,k]
            s.add(distances[j].get_constraints())
        max_len = max(distances, key= lambda d: d.binary_length).binary_length
        max_distance = D2B(binary=[Bool(f"max_distance_{f}") for f in range(max_len + 2)])
        s.add(min_path.add_geq(max_distance))
        s.add(max_path.add_leq(max_distance))
        for j in range(instance.m):
            s.add(distances[j].add_geq(max_distance))

        return s, courier_load, courier_route, loads, distances, max_load, max_distance

    def __update_max_distance(self, s, max_distance, model):
        new_min_path = D2B(max_distance.to_decimal(model), "new_min_path")
        s.add(new_min_path)
        s.add(new_min_path.add_geq(max_distance))

    def solve(self, instance: 'Instance'):
        
        s, courier_load, courier_route, loads, distances, max_load, max_distance = self.__build_base_model(instance)

        print()
        print("constraints created")
        if s.check() == sat:
            m = s.model()
            for j in range(instance.m):
                print(
                    "=========================================================================")
                print("courier ", j)
                print("packs ", [i + 1 for i in range(instance.n) if m.evaluate(courier_load[j,i])])
                print("route\n", self.get_route(courier_route[j,:,:], m, instance.n, instance.n))
                print("load ", loads[j].to_decimal(m))
                print("max load ", max_load[j].to_decimal(m))
                print("distance ", distances[j].to_decimal(m))
            print(
                "=========================================================================")
            print("max distance", max_distance.to_decimal(m))
        else:
            print("unsat")

    def get_route(self, route_matrix, model, start, end):
        return "\n".join([" ".join(["1" if model.evaluate(route_matrix[i,j]) else "0" for j in range(start+1)]) for i in range(start+1)])
        def get_next(line, model):
            for i in range(len(line)):
                if model.evaluate(line[i]):
                    return i
        
        route = [start]
        i = start
        while True:
            i = get_next(flatten(route_matrix[i,:].tolist()), model)
            route.append(i)
            if i == end:
                return route
            


Sat_model().solve(Instance('instances/inst00.dat'))
