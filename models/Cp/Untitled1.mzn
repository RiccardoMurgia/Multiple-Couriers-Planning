include "globals.mzn";
include "../../../instances/parsed_instances/inst16.dzn";
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

array[1..m,1..n+1,1..n+1] of var 0..1: courier_route;
array[1..m] of var 1..max_path: distances;
array[1..m,1..n+1] of var 0..max_path_length: steps;
%array[1..m] of var int: load;
%array[1..n] of var 1..n: packs;
var min_path..max_path: max_distance;

constraint count_eq(courier_route,1,n+m);

%constraint bin_packing_capa(max_load,packs,size);

constraint forall(j in 1..m)(
	sum(courier_route[j,1..n+1,1..n+1]) >= min_packs + 1
	/\ max_load[j] >= sum(i in 1..n)(sum(courier_route[j,i,1..n+1]) * size[i])
	/\ distances[j] = sum(i in 1..n+1, k in 1..n+1 where courier_route[j,i,k] = 1)(dist[i,k])
	/\ sum(courier_route[j,origin,1..n+1]) = 1 /\ sum(courier_route[j,1..n+1,origin]) = 1
	/\ courier_route[j,origin,origin] != 1
	/\ forall(i in 1..n)(
		%(packs[i] = j -> sum(courier_route[j,i,1..n+1]) = 1) /\
	
		sum(courier_route[j,i,1..n+1]) = sum(courier_route[j,1..n+1,i])
		/\ (sum(courier_route[j,i,1..n+1]) = 0 -> steps[j,i] = 0)
		/\ forall (k in 1..n)(
			not(courier_route[j,i,k] = 1 /\ courier_route[j,k,i] = 1)
			/\ (courier_route[j,i,k] = 1 -> steps[j,k] = (steps[j,i]) + 1)
		)
	)
);

constraint forall(i in 1..n)(
	sum(courier_route[1..m,i,1..n+1]) = 1 /\ sum(courier_route[1..m,1..n+1,i]) = 1 
	/\ sum(courier_route[1..m,i,i]) = 0
);


%constraint symmetry_breaking_constraint(increasing(load));

constraint max_distance = max(distances);

solve:: restart_luby(1000) minimize max_distance;




