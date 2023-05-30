include "globals.mzn";
int: m; % number of couriers
int: n; % number of items
int: min_path; % lower bound
array[1..m] of int: max_load; % maximum load size for each courier
array[1..n] of int: size; % size of each item
array[1..n+1, 1..n+1] of int: dist; % distance matrix

array[1..m, 1..n+3-m] of var 1..n+1: courier_route; % route of each courier
array[1..m] of var int: courier_distance; % distance traveled by each courier
var int: max_distance; % max distance traveled

constraint forall(j in 1..m)(
	courier_route[j,1] = n+1 /\ courier_route[j,n+3-m] = n+1 /\ courier_route[j,2] != n+1
); % each courier start from the origin, end at the origin and at time 2 his path must start


constraint forall(j in 1..m)(
	max_load[j] >= sum(i in 1..n)(count(s in courier_route[j,2..n+2-m])(i=s) * size[i])
); % each courier brings not more packages than it could

constraint forall(i in 1..n)(
	count(s in courier_route[1..m,2..n+2-m])(i=s) = 1
); % each package must be delivered at some point and a location can be visited only one time

constraint forall(j in 1..m, i in 3..n+2-m)(
	courier_route[j,i] != n+1 \/ forall(s in i+1..n+2-m)(courier_route[j,s] = n+1)
); % if a courier goes back to the origin, it must stay there

constraint forall(j in 1..m) (
  courier_distance[j] = sum(i in 2..n+3-m) (dist[courier_route[j,i-1], courier_route[j,i]])
); % compute courier distance

constraint max_distance = max(j in 1..m) (courier_distance[j]); % minimize maximum distance traveled

constraint max_distance >= min_path; % do not search for impossible solutions

solve minimize max_distance;
