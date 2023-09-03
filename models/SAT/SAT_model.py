from z3 import Bool, And, Or, Not, Implies, sat, Solver
from instance import Instance
from json_parser import Json_parser
import numpy as np
from models.SAT.Sat_utils import SatInteger, at_least_k, variable, exactly_one, at_most_k, SatSequences

from time import time

def flatten(e):
    if len(e) == 0:
        return []
    if isinstance(e[0], list):
        return flatten(e[0]) + flatten(e[1:])
    return [e[0]] + flatten(e[1:])

def get_solution(sol:'list[list]') -> 'list[list]':
    new_sol = []
    for path in sol:
        m = max(path)
        new_sol.append(list(filter(lambda d: d < m, path)))
    return new_sol
class Sat_model:

    def __init__(self) -> None:
        self.s = Solver()

    @staticmethod
    def __buil_variables(_m, _n, _max_path_length, _s):

        distances = []
        loads = []
        courier_route = np.empty(shape=(_m, _n+1, _n+1), dtype=object)
        times = np.empty(shape=(_m, _n+1), dtype=object)

        
        for j in range(_m):
            distances.append(SatInteger(0, "zero"))
            loads.append(SatInteger(0, "zero"))
            for i in range(_n+1):
                for k in range(_n+1):
                    courier_route[j,i,k] = Bool(f"courier_{j}_goes_from_{i}_to_{k}")
                times[j,i] = SatSequences(_max_path_length)
                _s.add(times[j,i].add())

        return distances, loads, courier_route, times

    @staticmethod
    def __go_everywhere_once(s, n, courier_load):
        for i in range(n):
            s.add(exactly_one(courier_load[:,i].tolist()))
    
    @staticmethod
    def __compute_max_distance(s, distances, min_path, max_path, m):

        max_len = max(distances, key= lambda d: d.binary_length).binary_length
        
        max_distance = variable(
            variable_length= max_len, 
            variable_name="max_distance")
        
        s.add(And([And(max_distance.add_geq(distances[j])) for j in range(m)]))
        s.add(max_distance.add_geq_int(min_path))
        s.push()
        s.add(max_distance.add_leq_int(max_path))

        return max_distance

    @staticmethod
    def __build_base_model(s, min_path, max_path, max_load, size, distance_matrix, m, n, origin, max_path_length, min_packs, max_packs):
        distances, \
        loads, \
        courier_route, \
        times = \
            Sat_model.__buil_variables(m, n, max_path_length, s)
                    
        courier_load = np.empty(shape=(m,n), dtype=object)
        
        for j in range(m):
            for i in range(n):
                courier_load[j,i] = Not(times[j,i].is_zero)
        
        origin_index = origin - 1
        
        Sat_model.__go_everywhere_once(s, n, courier_load)
        
        for j in range(m):
            # # every courier has at least a package
            s.add(at_least_k(courier_load[j,:].tolist(),k=min_packs))
            s.add(at_most_k(courier_load[j,:].tolist(), k=max_packs))
            # each courier start and ends at the origin
            s.add(exactly_one(flatten(courier_route[j, origin_index, :origin_index].tolist())))
            s.add(exactly_one(flatten(courier_route[j, :origin_index, origin_index].tolist())))
            s.add(courier_route[j, origin_index, origin_index] == False)

            for i in range(n):
                 
                j_at_i = courier_route[j, i, :].tolist()
            
                # if a courier goes at position i, it does not stop there
                s.add([
                    exactly_one(j_at_i) == courier_load[j,i],
                    exactly_one(courier_route[j, :, i].tolist()) == courier_load[j,i],
                    times[j,i].is_zero == Not(Or(j_at_i)),
                    times[j,i].is_zero == Not(Or(courier_route[j, :, i].tolist())),
                ])

                # add size of pack i to load of courier j if it brings that package
                loads[j] = loads[j].add_int(size[i], courier_load[j,i])

                for k in range(n):
                    # do not go to i from k if we've already been at i
                    s.add(Not(And(courier_route[j, i, k], courier_route[j, k, i])))
                    # for each place i, if j goes to k, then, the moment at which j is at k is greater 
                    # then the moment at which j is at i
                    if i != k:
                        s.add(Implies(
                            courier_route[j, i, k], 
                            And(times[j, k].next(times[j, i]))
                        ))
                
                # courier j do not stay at i 
                s.add(courier_route[j,i,i] == False)
            

            #compute distance for courier j
            for i in range(origin):
                for k in range(origin):
                    if i != k:
                        distances[j] = distances[j].add_int(distance_matrix[i,k], courier_route[j,i,k])        
            s.add(distances[j].get_constraints())
            s.add(loads[j].get_constraints())
            s.add(loads[j].add_leq_int(max_load[j]))
        
        max_distance = Sat_model.__compute_max_distance(s, distances, min_path, max_path, m)

        return times, courier_route, loads, distances, max_load, max_distance

    
    def __update_max_distance(self, s, upper_bound, max_distance):
        s.pop()
        s.push()
        u = SatInteger(upper_bound)
        s.add(u.get_constraints())
        s.add(max_distance.add_less(u))
        s.add(max_distance.get_constraints())

    @staticmethod
    def __get_route(route_matrix, model, start, end):
        pairs = [(i+1,j+1) for i in range(route_matrix.shape[0]) for j in range(route_matrix.shape[1]) if model.evaluate(route_matrix[i,j])]
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

    @staticmethod
    def __convert_solution(solution, model,m, origin):
        sol = {}
        sol["times"] = []
        sol["route"] = []
        sol["load"] = []
        sol["distance"] = []
        sol["max_distance"] = solution["max_distance"].to_decimal(model)
        for j in range(m):
            sol["times"].append([t.to_decimal(model) for t in solution["times"][j,:]])
            sol["route"].append(Sat_model.__get_route(solution["courier_route"][j,:,:], model, origin, origin))
            sol["load"].append(solution["loads"][j].to_decimal(model))
            sol["distance"].append(solution["distances"][j].to_decimal(model))
        return sol

    def add_instance(self, instance:'Instance', build:'bool' = True) -> None:
        self.instance = instance

        if build:
            self.build()

    def build(self):
        self.s = Solver()
        times, courier_route, loads, distances, max_load, max_distance = \
            Sat_model.__build_base_model(
            self.s,
            self.instance.min_path,
            self.instance.max_path,
            self.instance.max_load,
            self.instance.size,
            self.instance.distances,
            self.instance.m,
            self.instance.n,
            self.instance.origin,
            self.instance.max_packs,
            self.instance.min_packs,
            self.instance.max_packs
            )
        
        solution = {}
        solution["times"] = times
        solution["courier_route"] = courier_route
        solution["loads"] = loads
        solution["distances"] = distances
        solution["max_load"] = max_load
        solution["max_distance"] = max_distance

        self.__solution = solution

    def minimize(self, processes=1, timeout=300000):
        start = time()
        self.s.set("threads", processes)
        self.s.set("timeout",timeout)

        if self.s.check() != sat:
            print(self.s.check())
            return []

        solutions = []
        current_time = 0
        while self.s.check() == sat:

            sol = self.__convert_solution(self.__solution, self.s.model(), self.instance.m, self.instance.origin)
            current_time = int(time()-start)
            solutions.append({"solution":sol, "time":current_time})
            self.s.set("timeout", timeout - (current_time * 1000))
            print(sol["max_distance"])
            if sol["max_distance"] == self.instance.min_path:
                break

            if current_time >= 300:
                break
            self.__update_max_distance(self.s,sol["max_distance"], self.__solution["max_distance"])

        final_solution = {
            'optimal': solutions[-1]['solution']["max_distance"] == self.instance.min_path or current_time < 300,
            'time' : time() - start,
            'obj': solutions[-1]['solution']["max_distance"],
            'sol': get_solution(solutions[-1]['solution']['route'])
        }
        return final_solution

    
    def split_search(self, processes=1, timeout=300000):
        start = time()
        self.s.set("threads", processes)
        self.s.set("timeout",timeout)
        result = self.s.check()
        if result != sat:
            print(result)
            return []
        
        min_distance = self.instance.min_path
        solutions = []
        current_time = 0
        cond = 0
        old_max = 0
        sol = {}
        while cond != 2:
            current_time = int(time()-start)
            if current_time * 1000 > timeout:
                break
            if result == sat:
                sol = self.__convert_solution(self.__solution, self.s.model(), self.instance.m, self.instance.origin)
                solutions.append({"solution":sol, "time":current_time})
                self.s.set("timeout", timeout - (current_time * 1000))
                if sol["max_distance"] == self.instance.min_path:
                    break
                cond = 0
                old_max = sol["max_distance"]
                new_max = (sol["max_distance"] - min_distance)//2 + min_distance
                new_max = max(new_max, self.instance.min_path + 1)
                self.__update_max_distance(self.s,new_max, self.__solution["max_distance"])
                print("Success in", current_time, "s")
                print("Solution: ", sol["max_distance"], "Now tryin with New Max: ", new_max, " and New Min: ", min_distance)
            else:  
                cond += 1
                min_distance = (old_max - min_distance)//2 + min_distance
                self.__update_max_distance(self.s,old_max, self.__solution["max_distance"])
                print("Fail, time spent:", current_time, "s")
                print("Solution: ", old_max, "Now tryin with New Max: ", old_max, " and New Min: ", min_distance)
            result = self.s.check()
        final_solution = {
            'optimal': solutions[-1]['solution']["max_distance"] == self.instance.min_path or cond == 2,
            'time' : time() - start,
            'obj': solutions[-1]['solution']["max_distance"],
            'sol': get_solution(solutions[-1]['solution']['route'])
        }
        return final_solution
        
if __name__ == "__main__":
    model = Sat_model()
    start = time()
    instance = Instance('instances/inst02.dat')
    model.add_instance(instance)
    print("created in", time() - start)
    res = model.split_search()
    print(res)
    json_parser = Json_parser()
    json_parser.save_results('SAT', instance.name, res, instance.max_load_indexes)
