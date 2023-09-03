import json
import re
from os.path import join, exists
from os import makedirs, remove
from instance import *

from models.Cp.solutions import CpSolution
import subprocess


class CpModel:

    NO_SYMMETRY = "-no-sym"
    NO_SYMMETRY_STR = "mzn_ignore_symmetry_breaking_constraints=true;"
    MODEL_PATH  = '.cache/cp/model.mzn'

    def __init__(self, model_file_path: 'str') -> 'None':
        self.__model_path = model_file_path
        self.model_name = model_file_path.split('/')[-1].replace('.mzn', '')

    def add_instance(self, instance: 'Instance', solver: 'str' = 'Gecode') -> 'None':
        self.__instance = instance
        self.__solver = solver

    def solve(self, timeout: 'int' = 300000, processes: 'int' = 1) -> CpSolution:
        if not exists('.cache'):
            makedirs('.cache')
        if not exists('.cache/cp'):
            makedirs('.cache/cp')

        solver = self.__solver
        symmetry_breaking = True
        if self.NO_SYMMETRY in self.__solver:
            solver = solver.replace(self.NO_SYMMETRY, '')
            symmetry_breaking = False
        self.__instance.save_dzn('.cache/cp')
        parameters = ['minizinc', '--solver', solver, self.MODEL_PATH , f'.cache/cp/{self.__instance.name}.dzn',
                      '-s', '-p', str(processes), '-i', '--json-stream']
        if timeout > 0:
            parameters += ['--time-limit', str(timeout)]

        model = open(self.__model_path,'r')
        model_str = model.read()
        model.close()
        if not symmetry_breaking:
            model_str += self.NO_SYMMETRY_STR

        model_final = open(self.MODEL_PATH,'w+')
        model_final.write(model_str)
        model_final.close()
        completed_process = subprocess.Popen(parameters, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        info = {}
        solutions = []
        statistics = []
        states = []
        for line in completed_process.stdout:
            message_data = json.loads(line)
            if message_data.get("type") == "solution":
                output_section = message_data.get("output", {})
                solution = manage_the_solution(output_section['dzn'])
                solutions.append(solution)
            if message_data.get("type") == "statistics":
                statistics.append(message_data)
            if message_data.get("type") == "status":
                states.append(message_data)

        completed_process.wait()
        info['solutions'] = solutions
        info['statistics'] = statistics
        info['states'] = states
        remove('.cache/cp/model.mzn')
        return CpSolution(info)

    def save(self, path):
        file_name = join(path,f'{self.__instance.name}.fnz')
        if not exists('.cache/cp'):
                makedirs('.cache/cp')
        
        solver = self.__solver
        symmetry_breaking = True
        if self.NO_SYMMETRY in self.__solver:
            solver = solver.replace(self.NO_SYMMETRY, '')
            symmetry_breaking = False
        model = open(self.__model_path,'r')
        model_str = model.read()
        model.close()
        if not symmetry_breaking:
            model_str += self.NO_SYMMETRY_STR

        model_final = open(self.MODEL_PATH,'w+')
        model_final.write(model_str)
        model_final.close()

        self.__instance.save_dzn('.cache/cp')
        parameters = ['minizinc', self.MODEL_PATH, f'.cache/cp/{self.__instance.name}.dzn', "--fzn", file_name, "-c"]
        output = subprocess.run(parameters, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stderr
        if output == "":
            print(f"exported model to file {self.__instance.name} into folder {path}")
        else:
            print(output)
        remove('.cache/cp/model.mzn')

def manage_the_solution(solution_str):
    pattern = r'(\w+)\s*=\s*((?:\[\|[\s\S]*?\|\])|(?:\[.*?\])|(?:\d+));'
    matches = re.findall(pattern, solution_str)
    parsed_data = {}

    for key, value in matches:
        if '[' in value:
            value = re.findall(r'\d+', value)
            value = [int(v) for v in value]
        elif ';' in value:
            value = value.split(';')
            value = [int(v.strip()) for v in value]
        else:
            value = int(value)
        parsed_data[key] = value

    total_size = len(parsed_data['courier_route'])
    m = len(parsed_data['courier_distance'])
    sublist_size = total_size // m

    parsed_data['courier_route'] = [parsed_data['courier_route'][i:i + sublist_size] for i in
                                    range(0, len(parsed_data['courier_route']), sublist_size)]
    new_data = []
    for sublist in parsed_data['courier_route']:
        m = max(sublist)
        new_data.append(list(filter(lambda d: d < m, sublist)))
    parsed_data['courier_route'] = new_data
    return parsed_data
