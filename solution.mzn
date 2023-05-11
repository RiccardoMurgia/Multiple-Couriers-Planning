% input data
include "d2.dzn";
include "globals.mzn";

int: m; % number of couriers
int: n; % number of items
array[1..m] of int: max_load; % maximum load size for each courier
array[1..n] of int: size; % size of each item
array[1..n+1, 1..n+1] of int: dist; % distance matrix

array[1..m,1..n+2,1..n+1] of var 0..1: route;
array[1..m,1..n] of var 0..1: courier_load;

array[1..m, 1..n+2] of var 1..n+1: courier_route;
array[1..m] of var int: courier_distance; % distance traveled by each courier
var int: max_distance;

constraint forall(j in 1..m)(
	route[j,1,n+1] = 1 /\ route[j,n+2,n+1] = 1 /\ route[j,2,n+1] = 0 %parte e finisce all'origine
);

constraint forall(i in 1..n)(
	sum(j in 1..m)(courier_load[j,i]) = 1 %tutto deve essere assegnato
);

constraint forall(j in 1..m)(
	max_load[j] >= sum(i in 1..n)(courier_load[j,i] * size[i]) %ognuno ha al massimo peso quanto ne può portare
);

constraint forall(j in 1..m, i in 1..n)(
	sum(k in 2..n+1)(route[j,k,i]) = courier_load[j,i] %passiamo sempre da dove dobbiamo consegnare i pacchi
);

constraint forall(j in 1..m, k in 1..n+1)(
	sum(i in 1..n+1)(route[j,k,i]) = 1
);

constraint forall(j in 1..m) (
    courier_distance[j] = sum(k in 2..n+2) (dist[courier_route[j,k-1], courier_route[j,k]]) % compute courier distance
);

constraint max_distance = max(j in 1..m) (courier_distance[j]); % minimize maximum distance traveled

% objective function
solve minimize max_distance;

constraint forall(j in 1..m, k in 1..n+2)(
	courier_route[j,k] = sum(i in 1..n+1)(route[j,k,i] * i)
);
