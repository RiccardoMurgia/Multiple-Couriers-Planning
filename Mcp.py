from models.Cp.model import CpModel
from models.SAT.SAT_model import Sat_model
from models.MIP.mip_model import Mip_model, Or_model, Pulp_model
from models.SMT.smt_model import Z3_smt_model
from instance import Instance
from os import listdir, makedirs
from os.path import isfile, join, exists
import argparse
import json
from json_parser import Json_parser

from typing import Union

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--configuration_file", type=str)
json_parser = Json_parser()


def load_parameters():
    args = parser.parse_args()
    f = open(args.configuration_file)
    parameters = json.load(f)
    f.close()
    return parameters


def load_all_instances(instances_path: 'str') -> 'list[Instance]':
    instances_names = sorted([f for f in listdir(instances_path) if isfile(join(instances_path, f))])
    instances = []

    for instance_name in instances_names:
        instances.append(Instance(join(instances_path, instance_name)))

    return instances


def load_specific_instances(instances_path: 'str', instance_to_solve: 'list[str]') -> 'list[Instance]':
    instances_names = sorted([f for f in listdir(instances_path) if isfile(join(instances_path, f))])
    instances = []

    for instance_name in instances_names:
        if instance_name in instance_to_solve:
            instances.append(Instance(join(instances_path, instance_name)))

    return instances


def solve_cp(config: 'dict', instances_path: 'str',
             instance_to_solve: Union[list[str], str] = 'all_instances'):
    solver = CpModel('./models/Cp/Cp_model.mzn')
    print("============================================================================")
    print(f'loaded models {solver.model_name}')

    if instance_to_solve == 'all_instances':
        instances = load_all_instances(instances_path)
    else:
        instances = load_specific_instances(instances_path, instance_to_solve)

    if config.get("export_folder", "") != "":
        if not exists(config['export_folder']):
            makedirs(config['export_folder'])

        for instance in instances:
            solver.add_instance(instance)
            solver.save(config['export_folder'])
    for instance in instances:
        print("============================================================================")
        print(f"solving instance {instance.name}")
        for cp_solver in config['solvers']:
            solver.add_instance(instance, cp_solver)
            print("model built, now solving...")
            solution = solver.solve(config['timeout'], processes=config['processes'])
            result = solution.get_result()
            json_parser.save_results('CP', instance.name, result, instance.max_load_indeces, cp_solver)
            print("<----------------------------------------------->")
            print(f'solution for solver {cp_solver}:')
            print(result)


def solve_sat(config: 'dict', instances_path: 'str',
              instance_to_solve: Union[list[str], str] = 'all_instances'):
    solver = Sat_model()
    print('loaded sat model')

    if instance_to_solve == 'all_instances':
        instances = load_all_instances(instances_path)
    else:
        instances = load_specific_instances(instances_path, instance_to_solve)

    for instance in instances:
        print("============================================================================")
        print(f"solving instance {instance.name}")
        print("building model...")
        solver.add_instance(instance, build=True)
        print("model built, now solving...")
        solution = solver.split_search(timeout=config['timeout'], processes=config['processes'])
        print(solution)
        json_parser.save_results('SAT', instance.name, solution, instance.max_load_indeces)


def solve_mip(config: 'dict', instances_path: 'str',
              instance_to_solve: Union[list[str], str] = 'all_instances'):
    libraries = config['library']

    if instance_to_solve == 'all_instances':
        instances = load_all_instances(instances_path)
    else:
        instances = load_specific_instances(instances_path, instance_to_solve)

    if config.get("export_folder", "") != "":
        if not exists(config['export_folder']):
            makedirs(config['export_folder'])

        for instance in instances:
            Or_model("or-tools", instance).save(config['export_folder'])

    for lib in libraries:
        for instance in instances:
            key = lib + '_solvers'
            solver_to_use = config[key]
            for solver_name in solver_to_use:
                print("============================================================================")
                print(f'loaded Mip model implemented with library {lib} and solver {solver_name}')
                print("============================================================================")
                print(f"solving instance {instance.name}")

                sub_folders = '_None_'

                if lib == 'mip':
                    solver = Mip_model(lib, instance, h=False, param=0, solver_name=solver_name)
                    if config['create_sub_folders']:
                        sub_folders = lib
                elif lib == 'ortools':
                    solver = Or_model(lib, instance, solver_name=solver_name)
                    if config['create_sub_folders']:
                        sub_folders = lib + '_' + solver_name
                elif lib == 'pulp':
                    solver = Pulp_model(lib, instance, timeout=config['timeout'])
                    if config['create_sub_folders']:
                        sub_folders = lib
                else:
                    raise Exception(f"unknown lib {lib}")
                print("model built, now solving...")
                solver.solve(processes=config['processes'], timeout=config['timeout'])
                result = solver.get_result()

                print("result pre:", result)
                json_parser.save_results('MIP', instance.name, result, instance.max_load_indeces, sub_folders)
                print("<----------------------------------------------->")
                print(f'solution for library {lib}:')
                print("result post:", result)


def solve_smt(config: 'dict', instances_path: 'str',
              instance_to_solve: Union[list[str], str] = 'all_instances'):
    if instance_to_solve == 'all_instances':
        instances = load_all_instances(instances_path)
    else:
        instances = load_specific_instances(instances_path, instance_to_solve)

    if config.get("export_folder", "") != "":
        if not exists(config['export_folder']):
            makedirs(config['export_folder'])
        print(f'loaded SMT model implemented with z3')
        for instance in instances:
            print(f"solving instance {instance.name}")
            print("building model...")
            solver = Z3_smt_model("z3", instance)
            if config.get("export_folder") != "":
                solver.save(config["export_folder"])
            print("model built, now solving...")
            solver.solve(processes=config['processes'], timeout=config['timeout'])
            result = solver.get_result()
            json_parser.save_results('SMT', instance.name, result, instance.max_load_indeces)
            print("<----------------------------------------------->")
            print(f'solution:')
            print(result)


def main(config: 'dict'):
    models_to_use = config['usage_mode']['models_to_use']
    instances_to_solve = config['usage_mode']['instances_to_solve']
    if 'cp' in models_to_use:
        print("============================================================================")
        solve_cp(config['cp'], config['instances_path'], instances_to_solve)
    if 'sat' in models_to_use:
        print("============================================================================")
        solve_sat(config['sat'], config['instances_path'], instances_to_solve)
    if 'mip' in models_to_use:
        print("============================================================================")
        solve_mip(config['mip'], config['instances_path'], instances_to_solve)
    if 'smt' in models_to_use:
        print("============================================================================")
        solve_smt(config['smt'], config['instances_path'], instances_to_solve)


if __name__ == '__main__':
    main(load_parameters())
