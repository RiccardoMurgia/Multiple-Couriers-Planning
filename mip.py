from mip import Model, xsum, INTEGER, MINIMIZE, MAXIMIZE, minimize, BINARY, OptimizationStatus
from ortools.linear_solver import pywraplp
from instance import Instance
import time
import multiprocessing
import os
import json
import jsbeautifier
import pulp
import datetime


# Define the paths for each approach's result folder
results_folder = "res"
approach_folders = {
    "MIP": os.path.join(results_folder, "MIP"),
    "SAT": os.path.join(results_folder, "SAT"),
    "CP": os.path.join(results_folder, "CP"),
    "SMT": os.path.join(results_folder, "SMT")
}

def get_solution(lib,instance, table):

    # Create a dictionary to store the routes for each courier
    courier_routes = {k: [] for k in range(instance.m)}

    # Extract and populate courier routes
    for k in range(instance.m):
        if lib == "mip":
            courier_routes[k] = [[i, j] for i in range(instance.origin) for j in range(instance.origin) if table[k, i, j].x == 1]
        elif lib == "ortools":
            courier_routes[k] = [[i, j] for i in range(instance.origin) for j in range(instance.origin) if table[k, i, j].solution_value() == 1]
        elif lib == "pulp":
            courier_routes[k] = [[i, j] for i in range(instance.origin) for j in range(instance.origin) if table[k, i, j].value() == 1]

    # Reorder the routes to start from the origin
    for k in range(instance.m):
        origin_index = next((i for i, route in enumerate(courier_routes[k]) if route[0] == instance.origin - 1), None)
        if origin_index is not None:
            courier_routes[k] = courier_routes[k][origin_index:] + courier_routes[k][:origin_index]

    # Reorder it in a way that the first element of the tuple i is the second element of the tuple i-1
    for k in range(instance.m):
        for i in range(1, len(courier_routes[k])):
            if courier_routes[k][i][0] != courier_routes[k][i - 1][1]:
                for j in range(i + 1, len(courier_routes[k])):
                    if courier_routes[k][i][0] == courier_routes[k][j][1]:
                        courier_routes[k][i], courier_routes[k][j] = courier_routes[k][j], courier_routes[k][i]
                        break

    # Remove instance.origin - 1 from the routes
    for k in range(instance.m):
        courier_routes[k] = [route[0] for route in courier_routes[k]]
    
    # Create a list to store the routes for each courier
    routes = [courier_routes[k] for k in range(instance.m)]

    #print(routes)
    return routes  

def save_results(approach_name,instance_number,result):

    # Create the approach's result folder if it doesn't exist
    if approach_name in approach_folders:
        if not os.path.exists(approach_folders[approach_name]):
            os.makedirs(approach_folders[approach_name])

    # Save the result to a JSOinstance.origin file
    instance_path = os.path.join(approach_folders[approach_name], f"{instance_number}.json")
    with open(instance_path, "w") as json_file:      
        options = jsbeautifier.default_options()
        options.indent_size = 4
        json_string = jsbeautifier.beautify(json.dumps({approach_name: result}), options)
        json_file.write(json_string)

def clark_wright_savings(distances, capacity):
        # Calculate savings for all pairs of nodes
        savings = []
        for i in range(1, len(distances)):
            for j in range(i + 1, len(distances)):
                savings.append((i, j, distances[0][i] + distances[0][j] - distances[i][j]))

        # Sort savings in descending order
        savings.sort(key=lambda x: x[2], reverse=True)

        # Initialize routes
        routes = [[0] for _ in range(len(distances))]
        used_capacity = [0] * len(distances)

        # Greedily assign customers to routes
        for i, j, s in savings:
            route_i = None
            route_j = None
            for r in range(len(routes)):
                if i in routes[r]:
                    route_i = r
                if j in routes[r]:
                    route_j = r
            if route_i is not None and route_j is not None and route_i != route_j:
                if used_capacity[route_i] + used_capacity[route_j] + distances[i][j] <= capacity:
                    routes[route_i].remove(i)
                    routes[route_j].remove(j)
                    routes[route_i] += [i, j]
                    used_capacity[route_i] += distances[i][j]
                    used_capacity[route_j] += distances[i][j]

        return routes

def mip_model(instance, param, h = False):

    lib = "mip"

    start_time = time.time()

    # Create model
    model = Model(solver_name='CBC')
    model.verbose = 0  # Set verbosity level if desired

    # Create variables
    table = {}
    for k in range(instance.m):
        for i in range(instance.origin):
            for j in range(instance.origin):
                table[k, i, j] = model.add_var(var_type=INTEGER, name=f'table_{k}_{i}_{j}')

    courier_distance = [model.add_var(var_type=INTEGER, name=f'courier_distance_{k}') for k in range(instance.m)]

    # Auxiliary variables to avoid subtours
    u = {}
    for k in range(instance.m):
        for i in range(instance.origin):
            u[k, i] = model.add_var(var_type=INTEGER, lb=1, ub= instance.origin, name=f'u_{k}_{i}')
    
    # Objective
    obj = model.add_var(var_type=INTEGER, name='obj')

    for k in range(instance.m):
        model += courier_distance[k] == xsum(instance.distances[i][j] * table[k, i, j] for i in range(instance.origin) for j in range(instance.origin))

    # Upper and lower bounds
    model += obj <= instance.max_path
    model += obj >= instance.min_path

    for k in range(instance.m):
        model += obj >= courier_distance[k]

    # Constraints
    for i in range(instance.origin):
        for k in range(instance.m):
            # A courier can't move to the same item
            model += table[k, i, i] == 0
            # If an item is reached, it is also left by the same courier
            model += xsum(table[k, i, j] for j in range(instance.origin)) == xsum(table[k, j, i] for j in range(instance.origin))

    for j in range(instance.origin - 1):
        # Every item is delivered
        model += xsum(table[k, i, j] for k in range(instance.m) for i in range(instance.origin)) == 1

    for k in range(instance.m):
        # Couriers start at the origin and end at the origin
        model += xsum(table[k, instance.origin - 1, j] for j in range(instance.origin - 1)) == 1
        model += xsum(table[k, j, instance.origin - 1] for j in range(instance.origin - 1)) == 1

        # Each courier can carry at most max_load items
        model += xsum(table[k, i, j] * instance.size[j] for i in range(instance.origin) for j in range(instance.origin - 1)) <= instance.max_load[k]

        # Each courier must visit at least min_packs items and at most max_path_length items
        model += xsum(table[k, i, j] for i in range(instance.origin) for j in range(instance.origin - 1)) >= instance.min_packs
        model += xsum(table[k, i, j] for i in range(instance.origin) for j in range(instance.origin - 1)) <= instance.max_path_length
        
    # If a courier goes for i to j then it cannot go from j to i, except for the origin 
    # (this constraint it is not necessary for the model to work, but check if it improves the solution)
    for k in range(instance.m):
        for i in range(instance.origin - 1):
            for j in range(instance.origin - 1):
                if i != j:
                    model += table[k, i, j] + table[k, j, i] <= 1
   
    # Subtour elimination
    for k in range(instance.m):
        for i in range(instance.origin - 1):
            for j in range(instance.origin - 1):
                if i != j:
                    model += u[k, j] - u[k, i] >= 1 - instance.origin * (1 - table[k, i, j])

    # Set the objective
    model.objective = minimize(obj)

    # Parameters
    #model.emphasis = 2  # Set to 1 or 2 to get progressively better solutions
    model.cuts = param  # Enable Gomory cuts
    #model.heuristics = 1  # Enable simple rounding heuristic
    #model.pump_passes = 1  # Perform one pass of diving heuristics
    #model.probing_level = 3  # Enable probing
    #model.rins = 1  # Enable RINS heuristic
    #model.threads = multiprocessing.cpu_count()

    if h:
        # Call the Clark and Wright Savings Algorithm
        initial_routes = clark_wright_savings(instance.dist, instance.max_load[0])

        # Initialize routes using Clark and Wright Savings Algorithm
        for k, route in enumerate(initial_routes):
            for i, j in zip(route, route[1:]):
                table[k, i, j].start = 1

        print('Usign warm start CWS: Initial solution found in {} seconds'.format(time.time() - start_time))


    status = model.optimize(max_seconds=300)
    end_time = time.time()
    inst_time = end_time - start_time
 
    # Output
    if status == OptimizationStatus.OPTIMAL or status == OptimizationStatus.FEASIBLE:
        result = {
            "time": round(inst_time,3),
            "optimal": status == OptimizationStatus.OPTIMAL,
            "obj": model.objective_value,
            "sol": get_solution(lib,instance, table)
        }
    else:
        result = {
            "time": round(inst_time,3),
            "optimal": status == OptimizationStatus.OPTIMAL,
            "obj": None,
            "sol": None
        }
    
    return result

def or_model(instance, solv='CBC_MIXED_INTEGER_PROGRAMMING'):

    lib = "ortools"

    start_time = time.time()

    # Create solver
    solver = pywraplp.Solver.CreateSolver(solv)
    solver.SetTimeLimit(300 * 1000)

    # Create variables
    table = {}
    for k in range(instance.m):
        for i in range(instance.origin):
            for j in range(instance.origin):
                table[k, i, j] = solver.IntVar(0, 1, f'table_{k}_{i}_{j}')

    courier_distance = [solver.IntVar(0, instance.max_path, f'courier_distance_{k}') for k in range(instance.m)]

    # Auxiliary variables to avoid subtours
    u = {}
    for k in range(instance.m):
        for i in range(instance.origin):
            u[k, i] = solver.IntVar(0, instance.origin - 1, f'u_{k}_{i}')

    # Objective
    obj = solver.IntVar(0, instance.max_path, 'obj')

    for k in range(instance.m):
        courier_distance[k] = solver.Sum(instance.distances[i][j] * table[k, i, j] for i in range(instance.origin) for j in range(instance.origin))

    # Upper and lower bounds
    solver.Add(obj <= instance.max_path)
    solver.Add(obj >= instance.min_path)

    for k in range(instance.m):
        solver.Add(obj >= courier_distance[k])

    # Constraints
    for i in range(instance.origin):
        for k in range(instance.m):
            # A courier can't move to the same item
            solver.Add(table[k, i, i] == 0)
            # If an item is reached, it is also left by the same courier
            solver.Add(solver.Sum(table[k, i, j] for j in range(instance.origin)) == solver.Sum(table[k, j, i] for j in range(instance.origin)))

    for j in range(instance.origin - 1):
        # Every item is delivered
        solver.Add(solver.Sum(table[k, i, j] for k in range(instance.m) for i in range(instance.origin)) == 1)

    for k in range(instance.m):
        # Couriers start at the origin and end at the origin
        solver.Add(solver.Sum(table[k, instance.origin - 1, j] for j in range(instance.origin - 1)) == 1)
        solver.Add(solver.Sum(table[k, j, instance.origin - 1] for j in range(instance.origin - 1)) == 1)

        # Each courier can carry at most max_load items
        solver.Add(solver.Sum(table[k, i, j] * instance.size[j] for i in range(instance.origin) for j in range(instance.origin - 1)) <= instance.max_load[k])

        # Each courier must visit at least min_packs items and at most max_path_length items
        solver.Add(solver.Sum(table[k, i, j] for i in range(instance.origin) for j in range(instance.origin - 1)) >= instance.min_packs)
        solver.Add(solver.Sum(table[k, i, j] for i in range(instance.origin) for j in range(instance.origin - 1)) <= instance.max_path_length)

    # If a courier goes for i to j then it cannot go from j to i, except for the origin 
    # (this constraint it is not necessary for the model to work, but check if it improves the solution)
    for k in range(instance.m):
        for i in range(instance.origin - 1):
            for j in range(instance.origin - 1):
                if i != j:
                    solver.Add(table[k, i, j] + table[k, j, i] <= 1)

    # Subtour elimination
    for k in range(instance.m):
        for i in range(instance.origin - 1):
            for j in range(instance.origin - 1):
                if i != j:
                    solver.Add(u[k, j] >= u[k, i] + 1 - instance.origin * (1 - table[k, i, j]))

    # Set the objective
    solver.Minimize(obj)

    # Solve the model
    status = solver.Solve()
    end_time = time.time()
    inst_time = end_time - start_time

    # Output
    if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
        result = {
            "time": round(inst_time,3),
            "optimal": status == pywraplp.Solver.OPTIMAL,
            "obj": solver.Objective().Value(),
            "sol": get_solution(lib,instance,table)
        }
    else:
        result = {
            "time": round(inst_time,3),
            "optimal": status == pywraplp.Solver.OPTIMAL,
            "obj": None,
            "sol": None
        }
    
    return result

def pulp_model(instance,solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=300)):

    lib = "pulp"

    start_time = time.time()

    # Create model
    model = pulp.LpProblem("CourierProblem", pulp.LpMinimize)

    # Create variables
    table = pulp.LpVariable.dicts("table", ((k, i, j) for k in range(instance.m) for i in range(instance.origin) for j in range(instance.origin)), 
                            lowBound=0, upBound=1, cat=pulp.LpBinary)
    
    courier_distance = pulp.LpVariable.dicts("courier_distance", (range(instance.m)), cat=pulp.LpInteger, lowBound=0, upBound=instance.max_path)

    # Auxiliary variables to avoid subtours
    u = {}
    for k in range(instance.m):
        for i in range(instance.origin):
            u[k, i] = pulp.LpVariable(f'u_{k}_{i}', lowBound=1, upBound= instance.origin, cat=pulp.LpInteger)

    # Objective
    obj = pulp.LpVariable('obj', cat=pulp.LpInteger)

    for k in range(instance.m):
        model += courier_distance[k] == pulp.lpSum(instance.distances[i][j] * table[k, i, j] for i in range(instance.origin) for j in range(instance.origin))

    # Upper and lower bounds
    model += obj <= instance.max_path
    model += obj >= instance.min_path

    for k in range(instance.m):
        model += obj >= courier_distance[k]

    # Constraints
    for i in range(instance.origin):
        for k in range(instance.m):
            # A courier can't move to the same item
            model += table[k, i, i] == 0
            # If an item is reached, it is also left by the same courier
            model += pulp.lpSum(table[k, i, j] for j in range(instance.origin)) == pulp.lpSum(table[k, j, i] for j in range(instance.origin))

    for j in range(instance.origin - 1):
        # Every item is delivered
        model += pulp.lpSum(table[k, i, j] for k in range(instance.m) for i in range(instance.origin)) == 1

    for k in range(instance.m):
        # Couriers start at the origin and end at the origin
        model += pulp.lpSum(table[k, instance.origin - 1, j] for j in range(instance.origin - 1)) == 1
        model += pulp.lpSum(table[k, j, instance.origin - 1] for j in range(instance.origin - 1)) == 1

        # Each courier can carry at most max_load items
        model += pulp.lpSum(table[k, i, j] * instance.size[j] for i in range(instance.origin) for j in range(instance.origin - 1)) <= instance.max_load[k]

        # Each courier must visit at least min_packs items and at most max_path_length items
        model += pulp.lpSum(table[k, i, j] for i in range(instance.origin) for j in range(instance.origin - 1)) >= instance.min_packs
        model += pulp.lpSum(table[k, i, j] for i in range(instance.origin) for j in range(instance.origin - 1)) <= instance.max_path_length

    # If a courier goes for i to j then it cannot go from j to i, except for the origin 
    # (this constraint it is not necessary for the model to work, but check if it improves the solution)
    for k in range(instance.m):
        for i in range(instance.origin -1):
            for j in range(instance.origin -1):
                if i != j:
                    model += table[k, i, j] + table[k, j, i] <= 1

    # Subtour elimination
    for k in range(instance.m):
        for i in range(instance.origin - 1):
            for j in range(instance.origin - 1):
                if i != j:
                    model += u[k, j] - u[k, i] >= 1 - instance.origin * (1 - table[k, i, j])

    # Set the objective
    model += obj

    # Solve the problem
    status = model.solve(solver)

    end_time = time.time()
    inst_time = end_time - start_time

    # Output
    if status == pulp.LpStatusOptimal or status == pulp.LpStatusNotSolved:
        result = {
            "time": round(inst_time,3),
            "optimal": status == pulp.LpStatusOptimal,
            "obj": pulp.value(model.objective),
            "sol": get_solution(lib,instance, table)
        }
    else:
        result = {
            "time": round(inst_time,3),
            "optimal": status == pulp.LpStatusOptimal,
            "obj": None,
            "sol": None
        }

    return result




# Log file
log = open("res/MIP/log.txt", "a")

# Print in the log file and in the console
def print_log(string):
    log.write(str(string) + "\n")
    print(string)

# Print the header
print_log("\n\n---------------------------------------------- LOGGING {} ----------------------------------------------\n\n"
          .format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

#Solve all the instances
start_tot_time = time.time()
for i in [0,1,2,3,4,5]: #[0,1,2,3,4,5,6,7,8,9,10,12,13,16,19,21]
    if i < 10:
        instance = Instance("instances/inst0" + str(i) + ".dat")
    else:
        instance = Instance("instances/inst" + str(i) + ".dat")

    print_log("\n------------------------------------------------------------------------")
    print_log("Instance " + str(i))
    print_log("------------------------------------------------------------------------")

    print_log("\nMIP MODEL")
    result = mip_model(instance,h=False, param=0)
    print_log(result)
    save_results("MIP",instance.name,result)

    #print("\nMIP MODEL with Clark and Wright Savings Algorithm")
    #result = mip_model(instance,h=True)

    print_log("\nOR MODEL")
    result = or_model(instance)
    print_log(result)

    print_log("\nPULP MODEL")
    result = pulp_model(instance)
    print_log(result)

    ## PARAMETER TUNING
    #for param in [1,2,3]:
    #    print("\nMIP MODEL with " + str(param) + " cuts")
    #    mip_model(instance,param)

end_tot_time = time.time()
print_log('\n\nTotal time: {} seconds'.format(round(end_tot_time - start_tot_time,3)))

# Close the log file
log.close()