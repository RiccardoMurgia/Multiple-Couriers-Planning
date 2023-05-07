include "nosets.mzn"; % Support for set variables for all solvers% input data
include "data.dzn";
include "alldifferent.mzn";

int: m; % number of couriers
int: n; % number of items
array[1..m] of int: max_load; % maximum load size for each courier
array[1..n] of int: size; % size of each item
array[1..n+1, 1..n+1] of int: dist; % distance matrix

% decision variables
array[1..m, 1..n] of var 0..1: courier_item; % 1 if item is assigned to courier, 0 otherwise
array[1..m, 1..n+1] of var 1..n+1: courier_route; % route for each courier, starts and ends at origin

% auxiliary variables
array[1..m] of var int: courier_load; % load for each courier
array[1..m] of var int: courier_distance; % distance traveled by each courier
var int: max_distance; % maximum distance traveled by any courier

% constraints
constraint forall(i in 1..n) (
    sum(j in 1..m) (courier_item[j,i]) = 1 % each item is assigned to exactly one courier
);
constraint forall(j in 1..m) (
    sum(i in 1..n) (size[i] * courier_item[j,i]) <= max_load[j] % courier load is within its limit
);

set of int: S = {n+1};
constraint forall(j in 1..m) (
    all_different_except([ courier_route[j,i] | i in 2..n],S)
 );
/*
constraint alldifferent([ courier_route[j,i] | j in 1..m, i in 2..n])::domain;
*/
constraint forall(j in 1..m, i in 2..n) (
    courier_item[j,courier_route[j,i]] = 1 %all packages delivery
);
constraint forall(j in 1..m) (
    courier_route[j,1] = n+1 /\ courier_route[j,n+1] = n+1 % courier route starts and ends at origin
);
constraint forall(j in 1..m) (
    courier_load[j] = sum(i in 1..n) (size[i] * courier_item[j,i]) % compute courier load
);
constraint forall(j in 1..m) (
    courier_distance[j] = sum(k in 2..n+1) (dist[courier_route[j,k-1], courier_route[j,k]]) % compute courier distance
);
constraint max_distance <= sum(j in 1..m) (courier_distance[j]); % minimize maximum distance traveled

% objective function
solve minimize max_distance;

% output solution
output [
    "Courier " ++ show(j) ++ " route: " ++ show(courier_route[j,1..n+1]) ++ "\n" ++
    "Courier " ++ show(j) ++ " load: " ++ show(courier_load[j]) ++ "\n" ++
    "Courier " ++ show(j) ++ " distance: " ++ show(courier_distance[j]) ++ "\n" ++
    "Courier " ++ show(j) ++ " item: " ++ show(courier_item[j,1..n]) ++ "\n" | j in 1..m
];
