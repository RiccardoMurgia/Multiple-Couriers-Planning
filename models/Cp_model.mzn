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


array[1..m, 1..max_path_length] of var 1..n+1: courier_route; % route of each courier
array[1..m] of var int: courier_distance; % distance traveled by each courier
array[1..m,1..n] of var 0..1: courier_load;
array[1..m] of var int: steps;
var int: min_steps;
var int: max_steps;

var int: max_distance; % max distance traveled

constraint forall(j in 1..m)(
	courier_route[j,1] = origin /\ courier_route[j,max_path_length] = origin /\ courier_route[j,2] != origin
); % each courier start from the origin, end at the origin and at time 2 his path must start

constraint forall(j in 1..m)(
	sum(courier_load[j,1..n]) >= 1 /\ 
	max_load[j] >= sum(i in 1..n)(courier_load[j,i] * size[i]) /\ 
	sum(courier_load[j,1..n]) < max_path_length
);

constraint forall(j in 1..m)(
	steps[j] = sum(courier_load[j,1..n]) + 1 /\ steps[j] < max_path_length
);


constraint min_steps = min(steps[1..m]);
constraint max_steps = max(steps[1..m]);

constraint forall(i in 2..min_steps)(
	all_different(courier_route[m..1,i])
);
constraint forall(i in max_steps+1..max_path_length)(
	courier_route[1,i] = origin /\
	all_equal(courier_route[m..1,i])
);

constraint forall(j in 1..m, i in 1..n)(
	count_eq(courier_route[j,2..max_path_length], i, courier_load[j,i])
); % each package must be delivered at some point and a location can be visited only one time

constraint global_cardinality_closed(courier_route[1..m,1..max_path_length], n_array, count_array);
constraint nvalue(n+1, courier_route[1..m,1..max_path_length]);

constraint forall(j in 1..m) (
  courier_distance[j] = sum(i in 2..max_path_length) (dist[courier_route[j,i-1], courier_route[j,i]])
); % compute courier distance

constraint max_distance = max(j in 1..m) (courier_distance[j]); % minimize maximum distance traveled

constraint max_distance >= min_path; % do not search for impossible solutions
constraint max_distance <= max_path;

solve:: restart_luby(1000) minimize max_distance;

