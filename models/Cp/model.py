import minizinc
from instance import *
from datetime import timedelta
from pathlib import Path
from solutions import CpSolution
from multiprocessing import Process, Queue, Event
import subprocess

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
        _solver.load(Path('../../gecode_config.msc'))
        self.__instance = minizinc.Instance(_solver, self.__model)
        self.__instance['m'] = instance.m
        self.__instance['n'] = instance.n
        self.__instance['max_load'] = instance.max_load
        self.__instance['size'] = instance.size
        self.__instance['dist'] = instance.distances
        self.__instance['min_path'] = instance.min_path
        self.__instance['max_path'] = instance.max_path
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
    
class TerminalCpModel:
    def __init__(self, model_file_paths:'list[str]')-> 'None':
        
        self.__model_paths = model_file_paths
        self.model_names = [m.split('/')[-1].replace('.mzn','') for m in model_file_paths]

        self.solution = Queue()

    def add_instance(self, instance:'str', solver:'str' = 'Gecode')->'None':
        self.__instance = instance
        self.__solver = solver

    def solve(self, timeout:'int'=300000, processes:'int' = 1) -> CpSolution:

        event = Event()
        jobs = [] 
        for path in self.__model_paths:
            parameters = ['minizinc', '--solver', self.__solver, path, self.__instance, '-s', '-p', str(processes), '-i']
            if timeout > 0:
                parameters += ['--time-limit', str(timeout)]

            job = Process(target=self.__solve, args=(parameters, event, ))
            job.start()
            jobs.append(job)
            
        
        while not event.is_set():
            pass

        sol = self.solution.get()
        if sol == None:
            raise("error encountered while solving instance")
        
        for job in jobs:
            job.terminate()
        
        return CpSolution(sol)
    

    def __solve(self, parameters:'list', event:'Event'):
        solution = subprocess.run(parameters, stdout = subprocess.PIPE).stdout.decode('utf-8')
        
        self.solution.put(solution)
        event.set()

    

