from models.Cp.model import CpModel
from models.SAT.SAT_model import Sat_model
from models.MIP.my_mip import Mip_model, Or_model, Pulp_model
from instance import Instance
from os import listdir
from os.path import isfile, join
import argparse
import json
from json_parser import Json_parser

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--configuration_file", type=str)
json_parser = Json_parser()


def load_parameters():
    args = parser.parse_args()
    f = open(args.configuration_file)
    parameters = json.load(f)
    f.close()
    return parameters


def load_instances(instances_path: 'str') -> 'list[Instance]':
    instances_names = sorted([f for f in listdir(instances_path) if isfile(join(instances_path, f))])
    instances = []

    for instance_name in instances_names:
        instances.append(Instance(join(instances_path, instance_name)))

    return instances


def solve_cp(config: 'dict', instances_path: 'str', just_time: 'bool', verbose: 'bool'):
    solver = CpModel('./models/Cp/Cp_model.mzn')
    print(f'loaded models {solver.model_name}')
    instances = load_instances(instances_path)
    for instance in instances:
        print("============================================================================")
        print(f"solving instance {instance.name}")
        for cp_solver in config['solvers']:
            solver.add_instance(instance, cp_solver)
            solution = solver.solve(config['timeout'], processes=config['processes'])
            result = solution.get_result()
            json_parser.save_results('cp', instance.name, result)
            print("<----------------------------------------------->")
            print(f'solution for solver {cp_solver}:')

            solution.print(just_time, verbose)


def solve_sat(config: 'dict', instance_path: 'str', verbose: 'bool'):
    solver = Sat_model()
    print('loaded sat model')
    instances = load_instances(instance_path)
    for instance in instances:
        print("============================================================================")
        print(f"solving instance {instance.name}")
        print("building model...")
        solver.add_instance(instance, build=True)
        print("model built, now solving...")
        solutions = solver.minimize(timeout=config['timeout'], processes=config['processes'])
        if verbose:
            print(solutions[-1])


def solve_mip(config: 'dict', instance_path: 'str', verbose: 'bool'):
    library = config['mip']  # list ['mip','ortools', 'pull]
    instances = load_instances(instance_path)
    for lib in library:
        print(f'loaded Mip model implemented with library: {lib}')
        for instance in instances:
            print("============================================================================")
            print(f"solving instance {instance.name}")
            print("building model...")
            if lib == 'mip':
                solver = Mip_model(instance, h=False, param=0)
            elif lib == 'ortools':
                solver = Or_model(instance)
            else:
                solver = Pulp_model(instance)

            result = solver.get_result()

            json_parser.save_results('cp', instance.name, result)
            print("<----------------------------------------------->")
            print(f'solution for library {lib}:')
            # IT IS NECESARY TO PRINT THE SOLUTION


def main(config: 'dict'):
    # solve_cp(config['cp'], config['instances_path'], config['just_time'], config['verbose'])
    # solve_sat(config['sat'], config['instances_path'], config['verbose'])
    instances = load_instances(config['instances_path'])
    for instance in instances:
        instance.save_dzn('instances/parsed_instances')

if __name__ == '__main__':
    main(load_parameters())
