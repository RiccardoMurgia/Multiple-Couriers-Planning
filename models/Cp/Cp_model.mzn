include "globals.mzn";
int: m; % number of couriers
int: n; % number of items

array[1..m] of int: max_load; % maximum load size for each courier
array[1..n] of int: size; % size of each item
array[1..n+1, 1..n+1] of int: dist; % distance matrix

int: min_path; % lower bound
int: max_path; % lower bound
array[1..n+1] of int: n_array;
array[1..n+1] of int: count_array;
int: max_packs;
int: origin;
int: min_packs;
array[int] of set of int: similars;

int: max_path_length = max_packs +2;

array[1..m, 1..max_path_length] of var 1..n+1: courier_route; % route of each courier
array[1..m] of var int: courier_distance; % distance traveled by each courier
array[1..n] of var 1..m: packs;
var int: max_distance; % max distance traveled

constraint forall(j in 1..m)(
	courier_route[j,1] = origin /\ courier_route[j,max_path_length] = origin
); % each courier start from the origin, end at the origin and at time 2 his path must start

constraint forall(j in 1..m, i in 2..min_packs+1)(
	courier_route[j,i] != origin
);

constraint bin_packing_capa(max_load, packs, size);

constraint redundant_constraint(
	forall(i in 2..max_path_length-1)(
		all_different_except(courier_route[1..m,i], {origin})
	)
);

constraint forall(j in 1..m, i in 1..n)(
		member(courier_route[j,2..max_path_length-1], i) <-> packs[i] = j
); % each package must be delivered at some point and a location can be visited only one time

constraint forall(j in 1..m, i in 2..max_path_length-1)(
	courier_route[j,i] = origin -> forall(k in i..max_path_length-1)(courier_route[j,k] = origin)
);

constraint global_cardinality_closed(courier_route, n_array, count_array);

constraint forall(j in 1..m) (
  courier_distance[j] = sum(i in 2..max_path_length) (dist[courier_route[j,i-1], courier_route[j,i]])
); % compute courier distance

constraint max_distance = max(j in 1..m) (courier_distance[j]); % minimize maximum distance traveled

constraint max_distance >= min_path; % do not search for impossible solutions
constraint max_distance <= max_path; % do not search for impossible solutions

constraint symmetry_breaking_constraint(
	let{array[1..m] of var int: load = [sum(i in 1..n where packs[i] = j)(size[i]) | j in 1..m]} in
		forall(i in index_set(similars))(
			increasing(load[similars[i]]) /\ increasing(courier_distance[similars[i]])
		)
);

solve:: restart_luby(1000) minimize max_distance;



