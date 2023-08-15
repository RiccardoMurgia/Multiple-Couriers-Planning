include "globals.mzn";
%include "../instances/parsed_instances/cp/inst11.dzn";
int: m; % number of couriers
int: n; % number of items

array[1..m] of int: max_load; % maximum load size for each courier
array[1..n] of int: size; % size of each item
array[1..n+1, 1..n+1] of int: dist; % distance matrix

int: min_path; % lower bound
int: max_path; % lower bound
array[1..n+1] of int: n_array;
array[1..n+1] of int: count_array;
int: max_path_length;
int: number_of_origin_stops;
int: origin;
int: min_packs;

array[1..m,1..max_path_length,1..n+1] of var bool: courier_route;

array[1..m] of var int: courier_distance;
var int: max_distance;

constraint forall(j in 1..m)(
    courier_route[j,1,origin] = true /\ courier_route[j,max_path_length,origin] = true /\
    forall (i in 2..min_packs+1)(
        courier_route[j,i,origin] = false
    )
);


constraint forall(i in 1..n)(
    count_eq(courier_route[1..m,2..max_path_length-1,i],true,1)
);

constraint forall (j in 1..m, i in 2..max_path_length)(
    not(courier_route[j,i,origin]) \/ forall(s in i+1..max_path_length)(courier_route[j,s,origin])
);


constraint forall(j in 1..m)(
    max_load[j] >= sum(i in 2..max_path_length-1, k in 1..n)(bool2int(courier_route[j,i,k]) * size[k]) /\
    courier_distance[j] = sum(i in 2..max_path_length)(
        dist[
            sum(k in 1..n+1)(bool2int(courier_route[j,i-1,k]) * k),
            sum(k in 1..n+1)(bool2int(courier_route[j,i,k]) * k)
            ])
);

constraint max_distance = max(courier_distance);

constraint max_distance >= min_path; % do not search for impossible solutions
constraint max_distance <= max_path; % do not search for impossible solutions

solve:: restart_luby(1000) minimize max_distance;
