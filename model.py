import minizinc
from instance import *
from datetime import timedelta
from pathlib import Path

class CpModel:
    def __init__(self, model_file_path:'str')-> 'None':
        self.model_name = model_file_path.split('/')[-1].replace('.mzn','')
        model_file = open(model_file_path,'r')
        self.__str_model = model_file.read()
        self.__model = minizinc.Model()
        self.__model.add_string(self.__str_model)
        self.__instance = None

    def add_instance(self, instance:'Instance', solver:'str' = 'gecode')->'None':
        _solver = minizinc.Solver.lookup(solver)
        _solver.load(Path('./gecode_config.msc'))
        self.__instance = minizinc.Instance(_solver, self.__model)
        instance.compute_min_path()
        self.__instance['m'] = instance.m
        self.__instance['n'] = instance.n
        self.__instance['max_load'] = instance.max_load
        self.__instance['size'] = instance.size
        self.__instance['dist'] = instance.distances
        self.__instance['min_path'] = instance.min_path
        self.__instance['n_array'] = instance.n_array
        self.__instance['count_array'] = instance.count_array
        self.__instance['max_path_length'] = instance.max_path_length
        self.__instance['origin'] = instance.origin
        self.__instance['number_of_origin_stops'] = instance.number_of_origin_stops

    def solve(self, timeout:'int'=300):
        if self.__instance is None:
            raise('instance not initialized')
        
        if timeout > 0:
            solution = self.__instance.solve(all_solutions=False, timeout=timedelta(seconds=timeout))
        else:
            solution = self.__instance.solve(all_solutions=False)
        return (solution.solution, solution.statistics)
    

    def get_solution_string(self, solution):
        return f'''variable assignement:
courier_route = {solution.courier_route}
courier_distance = {solution.courier_distance}
max_distance = {solution.max_distance}     
        '''