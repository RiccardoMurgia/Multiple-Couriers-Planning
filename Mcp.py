#!/usr/bin/python3
from model import CpModel
from instance import Instance
from os import listdir
from os.path import isfile, join
import argparse


parser = argparse.ArgumentParser()
parser.add_argument("-t", "--timeout", type=int)
parser.add_argument("-s", "--solver", type=str)
parser.add_argument("-i", "--instances", type=str)
parser.add_argument("-v", "--verbose", type=int)

def get_arguments():
    args = parser.parse_args()
    main_args = {}
    if not args.timeout is None:
        main_args['timeout'] = args.timeout 
    if not args.timeout is None:
        main_args['instances_path'] = args.instances 
    if not args.timeout is None:
        main_args['solver_name'] = args.solver 
    if not args.verbose is None:
        main_args['verbose'] =  args.verbose == 1
    return main_args



def load_instances(instances_path:'str')->'list[Instance]':
    
    instances_names = sorted([f for f in listdir(instances_path) if isfile(join(instances_path, f))])
    instances = []

    for instance_name in instances_names:
        instances.append(Instance(join(instances_path, instance_name)))
    
    return instances

def main(solver_name:'str' = 'cp', instances_path:'str'='./instances/', timeout:'int'=300, verbose:'bool'=False):

    solver = None

    if solver_name == 'cp':
        solver = CpModel('./models/Cp_model.mzn')
        print(f'loaded model {solver.model_name}')
    else:
        print(f'solver {solver_name} not found, please specify a valid solver')
    
    instances = load_instances(instances_path)
    print(f'found {len(instances)} instances')

    for instance in instances:
        print(f'solving instance {instance.name}')
        solver.add_instance(instance)
        solution = solver.solve(timeout)
        if not solution[0] is None:
            print(f'solved instance {instance.name}')
            if verbose:
                print(solver.get_solution_string(solution[0]))
                print(f'stats:\n{solution[1]}\n')
        else:
            print(f'solution for instance {instance.name} not found')

    print('all solution runned')
        

if __name__ == '__main__':

    args = get_arguments()
    main(**args)