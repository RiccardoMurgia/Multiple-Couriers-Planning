import json
import re

from instance import *

from models.Cp.solutions import CpSolution
import subprocess


class CpModel:
    def __init__(self, model_file_path: 'str') -> 'None':
        self.__model_path = model_file_path
        self.model_name = model_file_path.split('/')[-1].replace('.mzn', '')
        self.__solver = None
        self.__instance = None

    def add_instance(self, instance: 'Instance', solver: 'str' = 'Gecode') -> 'None':
        self.__instance = instance
        self.__solver = solver

    def solve(self, timeout: 'int' = 300000, processes: 'int' = 1) -> CpSolution:
        self.__instance.save_dzn('.cache/cp')
        parameters = ['minizinc', '--solver', self.__solver, self.__model_path, f'.cache/cp/{self.__instance.name}.dzn',
                      '-s', '-p', str(processes), '-i', '--json-stream']
        if timeout > 0:
            parameters += ['--time-limit', str(timeout)]

        completed_process = subprocess.Popen(parameters, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        info = {}
        solutions = []
        statistics = []
        states = []

        for line in completed_process.stdout:
            try:
                message_data = json.loads(line)
                if message_data.get("type") == "solution":
                    output_section = message_data.get("output", {})
                    solution = manage_the_solution(output_section['dzn'])
                    solutions.append(solution)
                if message_data.get("type") == "statistics":
                    statistics.append(message_data)
                if message_data.get("type") == "status":
                    states.append(message_data)
            except:
                pass

        completed_process.wait()
        info['solutions'] = solutions
        info['statistics'] = statistics
        info['states'] = states

        return CpSolution(info)


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
    parsed_data['courier_load'] = [parsed_data['courier_load'][i:i + sublist_size] for i in
                                   range(0, len(parsed_data['courier_load']), sublist_size)]

    for sublist in parsed_data['courier_route']:
        del sublist[0]  # Delete the first element
        del sublist[-1]  # Delete the last element

    return parsed_data
