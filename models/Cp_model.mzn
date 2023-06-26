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
int: max_path_length;
int: number_of_origin_stops;
int: origin;
int: min_packs;

array[1..m, 1..max_path_length] of var 1..n+1: courier_route; % route of each courier
array[1..m] of var int: courier_distance; % distance traveled by each courier

var int: max_distance; % max distance traveled

constraint forall(j in 1..m)(
	courier_route[j,1] = origin /\ courier_route[j, max_path_length] = origin
); % each courier start from the origin, end at the origin and at time 2 his path must start

constraint forall(j in 1..m, i in 2..min_packs+1)(
	courier_route[j,i] != origin
);

constraint global_cardinality_closed(courier_route, n_array, count_array);
constraint forall(j in 1..m)(
	all_before(courier_route[j,2..max_path_length], origin)
);

constraint count(courier_route,origin, number_of_origin_stops);

constraint alldifferent_except(courier_route, {origin});

constraint forall(j in 1..m)(
	max_load[j] >= sum(i in 1..n)(count(courier_route[j,2..max_path_length-1],i) * size[i])
);


constraint forall(j in 1..m) (
  courier_distance[j] = sum(i in 2..max_path_length) (dist[courier_route[j,i-1], courier_route[j,i]])
); % compute courier distance

constraint max_distance = max(j in 1..m) (courier_distance[j]); % minimize maximum distance traveled

constraint max_distance >= min_path; % do not search for impossible solutions
constraint max_distance <= max_path;

solve:: restart_luby(1000) minimize max_distance;



predicate all_before(array[int] of var int: x, int: o) =
	forall(i in index_set(x) where x[i] != o)(i < arg_max(x))