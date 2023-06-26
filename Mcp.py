#!/usr/bin/python3
from model import CpModel, TerminalCpModel
from solutions import CpSolution
from instance import Instance
from os import listdir
from os.path import isfile, join
import argparse


parser = argparse.ArgumentParser()
parser.add_argument("-t", "--timeout", type=int)
parser.add_argument("-s", "--solver", type=str)
parser.add_argument("-i", "--instances", type=str)
parser.add_argument("-v", "--verbose", type=int)
parser.add_argument("-jt", "--justTime", type=int)
parser.add_argument("-sv", "--save", type=str)

def get_arguments():
    args = parser.parse_args()
    main_args = {}
    if not args.timeout is None:
        main_args['timeout'] = args.timeout 
    if not args.instances is None:
        main_args['instances_path'] = args.instances 
    if not args.solver is None:
        main_args['solver_name'] = args.solver 
    if not args.verbose is None:
        main_args['verbose'] =  args.verbose == 1
    if not args.justTime is None:
        main_args['just_time'] =  args.justTime == 1
    if not args.save is None:
        main_args['save'] =  args.save
    return main_args



def load_instances(instances_path:'str')->'list[Instance]':
    
    instances_names = sorted([f for f in listdir(instances_path) if isfile(join(instances_path, f))])
    instances = []

    for instance_name in instances_names:
        instances.append(Instance(join(instances_path, instance_name)))
    
    return instances

def main__legacy(solver_name:'str' = 'cp', instances_path:'str'='./instances/', timeout:'int'=300, verbose:'bool'=False, just_time:'bool'=False):

    solver = None

    if solver_name == 'cp':
        solver = CpModel('./models/Cp_model.mzn')
        print(f'loaded model {solver.model_name}')
    else:
        print(f'solver {solver_name} not found, please specify a valid solver')
    
    instances = load_instances(instances_path)
    print(f'found {len(instances)} instances')

    solved_instances = 0

    for instance in instances:
        print(f'solving instance {instance.name}')
        solver.add_instance(instance)
        solution = solver.solve(timeout)
        if not solution[0] is None:
            print(f'solved instance {instance.name}')
            solved_instances +=1
            if verbose:
                print(solver.get_solution_string(solution[0]))
                print(f'stats:\n{solution[1]}\n')
            elif just_time:
                print(f'init time: {solution[1]["initTime"]}\nsolving time: {solution[1]["solveTime"]}\ntotal time: {solution[1]["initTime"] + solution[1]["solveTime"]}\n')
        else:
            print(f'solution for instance {instance.name} not found\n')

    print('all solution runned')
    print(f'solved {solved_instances}/{len(instances)} instances')

def main(solver_name:'str' = 'cp', instances_path:'str'='instances/parsed_instances', timeout:'int'=300000, verbose:'bool'=False, just_time:'bool'=False):
    solver = None

    if solver_name == 'cp':
        solver = TerminalCpModel('./models/Cp_model.mzn')
        instances_path += '/cp'
        print(f'loaded model {solver.model_name}')
    else:
        print(f'solver {solver_name} not found, please specify a valid solver')
    
    instances = sorted([ join(instances_path,f) for f in listdir(instances_path) if isfile(join(instances_path, f))])
    print(f'found {len(instances)} instances')

    solved_instances = 0

    for instance in instances:
        print("=============================================================")
        print(f'solving instance {instance}')
        solver.add_instance(instance)
        solution = solver.solve(timeout)
        if solution.is_solved(timeout):
            print(f'solved instance {instance}')
            solved_instances +=1
        else:
            print(f'solution for instance {instance} not found\n')
        solution.print(just_time, verbose, timeout)

    print('all solution runned')
    print(f'solved {solved_instances}/{len(instances)} instances')
        
def save_instances(solver_name:'str' = 'cp', instances_load_path:'str'='./instances/', instances_save_path:'str' = './instancecs/parsed/instances/cp'):
    
    instances = load_instances(instances_load_path)
    if solver_name == 'cp':
        for instance in instances:
            instance.save_dzn(instances_save_path)



if __name__ == '__main__':

    args = get_arguments()
    if 'save' in args.keys() is not None:
        save_instances(instances_save_path=args['save'], 
                       instances_load_path=args['instances_path'] if 'instances_path' in args.keys() else './instances/')
    else:
        main(**args)