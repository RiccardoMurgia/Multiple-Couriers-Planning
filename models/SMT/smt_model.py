import z3
from instance import Instance
from models.MIP.mip_model import get_solution, save_results
import time
import datetime
import os


def z3_smt_model(instance):
    start_time = time.time()

    # Create a Z3 solver instance
    solver = z3.Solver()

    # Define variables
    table = []
    for k in range(instance.m):
        rows = []
        for i in range(instance.origin):
            cols = []
            for j in range(instance.origin):
                cols.append(z3.Bool(f'table_{k}_{i}_{j}'))
            rows.append(cols)
        table.append(rows)

    # Courier distance
    courier_distance = [z3.Int(f'courier_distance_{k}') for k in range(instance.m)]

    # Lower and upper bounds on the courier distance for each courier
    for k in range(instance.m):
        solver.add(courier_distance[k] >= 0)
        solver.add(courier_distance[k] <= instance.max_path)

    # Auxiliary variables to avoid subtours
    u = []
    for k in range(instance.m):
        rows = []
        for i in range(instance.origin):
            rows.append(z3.Int(f'u_{k}_{i}'))
        u.append(rows)
        
    # Lower and upper bounds on the auxiliary variables
    for k in range(instance.m):
        for i in range(instance.origin):
            solver.add(u[k][i] >= 0)
            solver.add(u[k][i] <= instance.origin - 1)

    obj = z3.Int('obj')

    # Upper and lower bounds on the objective
    solver.add(obj <= instance.max_path)
    solver.add(obj >= instance.min_path)

    # Calculate the courier distance for each courier
    for k in range(instance.m):
        courier_distance[k] = z3.Sum(
            [z3.If(table[k][i][j], 1, 0) * instance.distances[i][j] for i in range(instance.origin) for j in
             range(instance.origin)])

    # Objective
    for k in range(instance.m):
        solver.add(obj >= courier_distance[k])

    # Constraints
    for k in range(instance.m):
        for i in range(instance.origin):
            # A courier can't move to the same item
            solver.add(table[k][i][i] == False)
            # If an item is reached, it is also left by the same courier
            solver.add(z3.Sum([table[k][i][j] for j in range(instance.origin)])
                       == z3.Sum([table[k][j][i] for j in range(instance.origin)]))
            # REDUNDANT
            solver.add(z3.Or([table[k][i][j] for j in range(instance.origin)]) == z3.Or([table[k][j][i] for j in range(instance.origin)]))
            solver.add(z3.PbEq([(table[k][i][j],1) for j in range(instance.origin)], 1) == z3.PbEq([(table[k][j][i],1) for j in range(instance.origin)], 1))

    for j in range(instance.origin - 1):
        # Every items is delivered using PbEq
        solver.add(z3.PbEq([(table[k][i][j],1) for k in range(instance.m) for i in range(instance.origin)], 1))
        # REDUNDANT
        solver.add(z3.PbEq([(table[k][j][i],1) for k in range(instance.m) for i in range(instance.origin)], 1)) 
    
    for k in range(instance.m):
        
        # Each courier can carry at most max_load items
        solver.add(z3.PbLe([(table[k][i][j],instance.size[j]) for i in range(instance.origin) for j in range(instance.origin - 1)], instance.max_load[k]))

        # Couriers start at the origin and end at the origin
        solver.add(z3.Sum([table[k][instance.origin - 1][j] for j in range(instance.origin - 1)]) == 1)
        solver.add(z3.Sum([table[k][j][instance.origin - 1] for j in range(instance.origin - 1)]) == 1)

        # Each courier must visit at least min_packs items and at most max_path_length items
        solver.add(z3.Sum(
            [table[k][i][j] for i in range(instance.origin) for j in range(instance.origin - 1)]) >= instance.min_packs)
        solver.add(z3.Sum([table[k][i][j] for i in range(instance.origin) for j in
                           range(instance.origin - 1)]) <= instance.max_path_length)

    
    for k in range(instance.m):
        for i in range(instance.origin - 1):
            for j in range(instance.origin - 1):
                if i != j:
                    # If a courier goes for i to j then it cannot go from j to i, except for the origin
                    solver.add(z3.Not(z3.And(table[k][i][j], table[k][j][i])))
                    
                    # Subtour elimination
                    solver.add(u[k][j] 
                               >= u[k][i] + 1 - instance.origin * (1 - z3.If(table[k][i][j], 1, 0)))

                    

    end_time = time.time()
    inst_time = end_time - start_time

    if inst_time >= 300:
        result = {
            "time": round(inst_time, 3),
            "optimal": False,
            "obj": None,
            "sol": None
        }

    solver.set("timeout", int(300 - inst_time) * 1000)

    # Model optimization
    while solver.check() == z3.sat:
        model = solver.model()
        solver.add(obj < model[obj])

        # Check if the solution is optimal
        if solver.check() == z3.unsat:
            end_time = time.time()
            inst_time = end_time - start_time

            # Convert table to a list of lists of booleans
            table = [[[model[table[k][i][j]] for j in range(instance.origin)] for i in range(instance.origin)] for k in
                     range(instance.m)]

            lib = "z3"
            result = {
                "time": round(inst_time, 3),
                "optimal": True,
                "obj": model[obj],
                "sol": get_solution(lib, instance, table)
            }
            print(result)

            return result

    return {
        "time": round(inst_time, 3),
        "optimal": False,
        "obj": model[obj],
        "sol": get_solution(lib, instance, table)
    }


if __name__ == "__main__":

    # Create directory if it doesn't exist
    if not os.path.exists("res/SMT"):
        os.makedirs("res/SMT")

    # Log file
    log = open("res/SMT/log.txt", "a+")


    # Print in the log file and in the console
    def print_log(string):
        log.write(str(string) + "\n")
        print(string)


    # Print the header
    print_log(
        "\n\n---------------------------------------------- LOGGING {} ----------------------------------------------\n\n"
        .format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    # Solve all the instances
    start_tot_time = time.time()
    for i in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:  # [0,1,2,3,4,5,6,7,8,9,10,12,13,16,19,21]
        if i < 10:
            instance = Instance("instances/inst0" + str(i) + ".dat")
        else:
            instance = Instance("instances/inst" + str(i) + ".dat")

        print_log("\n------------------------------------------------------------------------")
        print_log("Instance " + str(i))
        print_log("------------------------------------------------------------------------")

        print_log("\nSMT MODEL")
        result = z3_smt_model(instance)
        print_log(result)
        save_results("SMT", instance.name, result)

    end_tot_time = time.time()
    print_log('\n\nTotal time: {} seconds'.format(round(end_tot_time - start_tot_time, 3)))

    # Close the log file
    log.close()