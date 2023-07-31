from instance import *
from datetime import timedelta
from pathlib import Path
from solutions import CpSolution
import subprocess

class CpModel:
    def __init__(self, model_file_path:'str')-> 'None':
        
        self.__model_path = model_file_path
        self.model_name = model_file_path.split('/')[-1].replace('.mzn','')

    def add_instance(self, instance:'Instance', solver:'str' = 'Gecode')->'None':
        self.__instance = instance
        self.__solver = solver

    def solve(self, timeout:'int'=300000, processes:'int' = 1) -> CpSolution:
        self.__instance.save_dzn('.cache/cp')
        parameters = ['minizinc', '--solver', self.__solver, self.__model_path, f'.cache/cp/{self.__instance.name}.dzn', '-s', '-p', str(processes), '-i']
        if timeout > 0:
           parameters += ['--time-limit', str(timeout)]
        solution = subprocess.run(parameters, stdout = subprocess.PIPE).stdout.decode('utf-8')
        subprocess.run(["rm", f'.cache/cp/{self.__instance.name}.dzn'])
        return CpSolution(solution)
