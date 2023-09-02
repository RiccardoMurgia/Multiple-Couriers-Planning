import os
import json
from numpy import argsort

def main():
    sub = "SMT"
    path_end = f'results/{sub}'
    path_start = 'instances'
    files = [f for f in os.listdir(path_end) if os.path.isfile(os.path.join(path_end,f))]
    for file in files:
        name = file.split('.')[0]
        original = open(os.path.join(path_start, f'{name}.dat'), 'r')
        line = original.read().splitlines()[2].replace('\n', '')
        original_load = [int(i) for i in line.split(' ')]
        original.close()
        reorderded = argsort(original_load)
        sol_file = open(os.path.join(path_end,file),'r')
        sol = json.loads(sol_file.read())
        sol_file.close()
        if not sol[sub]['sol'] is None:
            new_sol = sol[sub]['sol'].copy()
            for i in range(len(reorderded)):
                new_sol[i] = sol[sub]['sol'][reorderded[i]]
                for j in range(len(new_sol[i])):
                    new_sol[i][j] = new_sol[i][j] + 1
            sol[sub]['sol'] = new_sol
            new_content = json.dumps(sol)
            sol_file = open(os.path.join(path_end,file),'w')
            sol_file.write(new_content)
            sol_file.close()

main()
