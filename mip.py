import gurobipy as gp
import numpy as np
from gurobipy import GRB
from instance import Instance
from ortools.linear_solver import pywraplp
import pulp as lp
import matplotlib.pyplot as plt



instance = Instance("instances/inst05.dat")

# Data
m = instance.m  # number of couriers
n = instance.n  # number of items

max_load = instance.max_load  # maximum load size for each courier
size = instance.size  # size of each item
dist = instance.distances  # distance matrix

min_path = instance.min_path  # lower bound
max_path = instance.max_path  # lower bound
n_array = instance.n_array  # specify values for n_array
count_array = instance.count_array  # specify values for count_array
max_path_length = instance.max_path_length  # maximum path length
number_of_origin_stops = instance.number_of_origin_stops # number of origin stops
origin = instance.origin - 1 # origin stop
min_packs = instance.min_packs  # minimum number of packs


def gurobi_model():
    # Create a new model
    model = gp.Model()

    # Variables
    courier_route = model.addMVar(shape=(m, max_path_length, n+1), lb=0, ub=1, vtype=gp.GRB.BINARY, name="courier_route")
    courier_distance = model.addMVar(shape=(m), vtype=GRB.INTEGER, name="courier_distance")
    max_distance = model.addVar(vtype=GRB.INTEGER, name="max_distance")

    # Constraints

    # i corrieri iniziano e finiscono tutti all'origine
    for j in range(m):
        model.addConstr(courier_route[j, 0, origin] == 1)
        model.addConstr(courier_route[j, max_path_length - 1, origin] == 1)

        # i corrieri non possono essere all'origine finche non hanno consegnato il numero minimo di pacchi
        for i in range(1,min_packs+1):
            model.addConstr(courier_route[j, i, origin] == 0)

        #i corrieri devono essere in un posto in ogni momento
        for i in range(max_path_length):
            model.addConstr(gp.quicksum(courier_route[j, i, k] for k in range(n+1)) == 1)

    #ogni corriere deve avere un carico massimo
    for j in range(m):
        model.addConstr(gp.quicksum(courier_route[j, i, k] * size[k] for i in range(1, max_path_length-1) for k in range(n)) <= max_load[j])

    # ogni pacco deve essere consegnato da uno ed uno sol corriere
    for k in range(n):
        model.addConstr(gp.quicksum(courier_route[j, i, k] for j in range(m) for i in range(max_path_length)) == 1)

    #se un corriere visita l'origine, rimane li fino alla fine
    for j in range(m):
        model.addConstr(courier_route[j, max_path_length - 1, origin] == courier_route[j, max_path_length - 2, origin])

    #calcola distanza percorsa da ogni corriere (not linear constraint)
    for j in range(m):
        model.addConstr(courier_distance[j] == gp.quicksum((dist[k1,k2] * courier_route[j, i-1, k1] * courier_route[j, i, k2]) 
                                                        for k1 in range(n+1) for k2 in range(n+1) for i in range(1, max_path_length)))
    #massima distanza percorsa da un corriere
    for j in range(m):
        model.addConstr(max_distance >= courier_distance[j])

    # Objective
    model.setObjective(max_distance, GRB.MINIMIZE)

    # Limit of 5 minutes
    gp.setParam("TimeLimit", 300) 

    # Optimize
    model.optimize()

    print(f"Optimal solution: {model.objVal}")

    # Get all variables in the model
    all_vars = model.getVars()

    for i in range(len(all_vars)):
        if all_vars[i].X != 0:
            print(f"{all_vars[i].VarName} = {all_vars[i].X}")


def pulp_model():

    N = n + 1

    # Model Initialization
    model = lp.LpProblem("LP_Model", lp.LpMinimize)

    # We have 2 variables, a 3D matrix as in CP and a 'u' Vector to remove loops
    table = lp.LpVariable.dicts("table", ((k, i, j) for k in range(m) for i in range(N) for j in range(N)), 
                            lowBound=0, upBound=1, cat=lp.LpBinary)
    
    courier_distance = lp.LpVariable.dicts("courier_distance", (range(m)), cat=lp.LpInteger, lowBound=0, upBound=max_path)

    # Obj definition
    obj = lp.LpVariable("obj", lowBound=0, cat=lp.LpInteger)
    for k in range(m):
        courier_distance[k] = lp.lpSum(dist[i, j] * table[k, i, j] for i in range(N) for j in range(N))

    # Upper and lower bounds
    model += obj <= max_path
    model += obj >= min_path
    for k in range(m):
        model += obj >= courier_distance[k]

    model.setObjective(obj)

    # Constraints
    for i in range(N):
        for k in range(m):
            model += table[k, i, i] == 0
            # If an item is reached, it is also left by the same courier
            model += lp.lpSum(table[k, i, j] for j in range(N)) == lp.lpSum(table[k, j, i] for j in range(N))

    # Every item is delivered
    for j in range(N-1):
        model += lp.lpSum(table[k, i, j] for k in range(m) for i in range(N)) == 1

    for k in range(m):
        # Start from the origin and come back to it at the end
        model += lp.lpSum(table[k, N-1, j] for j in range(N-1)) == 1
        model += lp.lpSum(table[k, j, N-1] for j in range(N-1)) == 1

        # Each courier can carry at most max_load items
        model += lp.lpSum(table[k, i, j] * size[j] for i in range(N) for j in range(N-1)) <= max_load[k]

        # Each courier must visit at least min_packs items
        model += lp.lpSum(table[k, i, j] for i in range(N) for j in range(N-1)) >= min_packs
        # Each courier must visit at most max_path_length items
        model += lp.lpSum(table[k, i, j] for i in range(N) for j in range(N-1)) <= max_path_length

    # Model Optimization
    model.solve(lp.PULP_CBC_CMD(timeLimit=300))

    print_results(N, table, courier_distance, size, model)


def print_results(N, table, courier_distance, size, model):
    # Create a dictionary to store the routes for each courier
    courier_routes = {k: [] for k in range(m)}

    # Extract and populate courier routes
    for k in range(m):
        taken_routes = [(i, j) for i in range(N) for j in range(N) if table[k, i, j].value() == 1]
        courier_routes[k] = taken_routes

    # Reorder the routes to start from the origin
    for k in range(m):
        origin_index = next((i for i, route in enumerate(courier_routes[k]) if route[0] == N - 1), None)
        if origin_index is not None:
            courier_routes[k] = courier_routes[k][origin_index:] + courier_routes[k][:origin_index]

    # Reorder it in a way that the first element of the tuple i is the second element of the tuple i-1
    for k in range(m):
        for i in range(1, len(courier_routes[k])):
            if courier_routes[k][i][0] != courier_routes[k][i - 1][1]:
                for j in range(i + 1, len(courier_routes[k])):
                    if courier_routes[k][i][0] == courier_routes[k][j][1]:
                        courier_routes[k][i], courier_routes[k][j] = courier_routes[k][j], courier_routes[k][i]
                        break

    # Print the routes in a readable way with arrows
    for k in range(m):
        print(f"\nCourier {k + 1} route:")
        for i in range(len(courier_routes[k])):
            if i == 0:
                print(f"{courier_routes[k][i][0]} -> {courier_routes[k][i][1]}", end="")
            else:
                print(f" -> {courier_routes[k][i][1]}", end="")

        # Print the distance for each courier
        print(f"\nCourier {k + 1} distance: {courier_distance[k].value()}")
        # Print the load for each courier
        print(f"Courier {k + 1} load: {lp.lpSum(table[k, i, j] * size[j] for i in range(N) for j in range(N-1)).value()}")
        # Print the max load for each courier
        print(f"Courier {k + 1} max load: {max_load[k]}")

    # Print the objective value
    print(f"\nOptimal solution: {model.objective.value()}")

    # Create a figure and axis
    fig, ax = plt.subplots()

    # Iterate through each courier's route
    for k in range(m):
        route = courier_routes[k]

        # Extract x and y coordinates for the route (you'll need to replace these with your actual coordinates)
        y_coords = [i for (i,j) in route]
        y_coords.append(N-1)
        x_coords = [i for i in range(1,len(route)+2)]

        # Plot the courier's route
        ax.plot(x_coords, y_coords, label=f'Courier {k + 1}', marker='o', markersize=6, linestyle='-', linewidth=1)


    # Add labels, legend, and title
    ax.set_xlabel('Time')
    ax.set_ylabel('Nodes Visited')
    ax.legend()
    ax.set_title('Courier Routes')

    # Show the plot
    plt.show()



#gurobi_model()
pulp_model()
