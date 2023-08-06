from z3 import *
from itertools import combinations
from instance import Instance


class MySatModel:

    def __init__(self):
        self.my_solver = Solver()
        self.my_optimizer = Optimize()

    @staticmethod
    def __at_most_one_pack_constraint(bool_vars: list):
        return [Not(And(pair[0], pair[1])) for pair in combinations(bool_vars, 2)]

    """
    def bool_encode(self, numbers: list, size: int, binary_num_length: int, name: str):  # numbers size,cap
        bool_num = [[Bool(f"{name}_{n}_{b}") for n in range(size)] for b in range(binary_num_length)]

        for i in range(size):
            binary_num = MySatModel.__binary_encode(numbers[i], binary_num_length)
            for b in range(binary_num_length):
                if binary_num[b] == '1':
                    self.my_solver.add(bool_num[i][b])
                else:
                    self.my_solver.add(Not(bool_num[i][b]))
        return bool_num

    """

    @staticmethod
    def __start_end_origin_constraint(bool_vars: list, origin: int, N: int, max_path: int) -> tuple:
        start = And(bool_vars[:, 0, origin])
        end = And(bool_vars[:, max_path - 1, N])
        return start, end

    @staticmethod
    def __package_delivery_constraint(bool_vars: list, min_packs: int, N: int) -> list:
        return Not(bool_vars[:, 1:min_packs, N])

    @staticmethod
    def __at_least_one_pack_constraint(bool_vars: list, max_path: int) -> list:
        return Or(bool_vars[:, : max_path - 1, :])

    @staticmethod
    def __each_receiver_only_one_visit_constraint(bool_vars: list, max_path: int, current_pack: int) -> list:
        my_constraint_1 = MySatModel.__at_most_one_pack_constraint(
            bool_vars[:, 1: max_path - 2, current_pack])
        my_constraint_2 = [MySatModel.__at_least_one_pack_constraint(
            bool_vars[:, 1: max_path - 2, current_pack])]
        return my_constraint_1 + my_constraint_2

    @staticmethod
    def __go_stay_at_the_origin__if_finished_constraint(bool_vars: list, rider: int, pack: int, origin: int, N: int):
        return Implies(bool_vars[rider][pack][N], And(bool_vars[rider][pack + 1][N], bool_vars[rider][pack][origin]))

    def courier_routing_sat(self, M, N, cap, size, D, max_path, number_of_origin_stops, min_packs, origin: int):
        courier_route = [[[Bool(f"P_{m}_{k}_{n}") for m in range(
            M)] for k in range(max_path)] for n in range(origin)]

        # riders must be in the origin at the first and the last steps
        start_constraint, end_constraint = MySatModel.__start_end_origin_constraint(
            courier_route, origin, N, max_path)
        self.my_solver.add(start_constraint)
        self.my_solver.add(end_constraint)

        # riders must be outside the origin if they have to deliver some packs
        works_constraint = MySatModel.__package_delivery_constraint()
        self.my_solver.add(works_constraint)

        # riders must have at least one package assigned
        rider_loading_constraint = MySatModel.__at_least_one_pack_constraint(
            courier_route)  # TODO at last n packs
        self.my_solver.add(rider_loading_constraint)

        # packs must be delivered, and destinations visited only once
        for i in range(N - 1):
            MySatModel.__each_receiver_only_one_visit_constraint(
                courier_route, max_path, i)

        # riders stay at the origin if they have finished delivery
        for j in range(M):
            for i in range(1, max_path - 2):
                self.my_solver.add(
                    MySatModel.__go_stay_at_the_origin__if_finished_constraint)

        # check max_load      # A >= B  =>  (A AND (NOT B)) OR (A nxor B)

        # Constraints to calculate the binary distance for each courier

        # Minimize the maximum distance

        max_distance = None
        self.my_optimizer.minimize(max_distance)

        if self.my_solver.check() == sat:
            return self.my_solver.model()
        else:
            print("Failed to solve")
            return None


myMode = MySatModel()


class Sat_model:
    def __at_least_one(self, bool_vars: list):
        return Or(bool_vars)

    def __at_most_one(self, bool_vars: list):
        return [Not(And(pair[0], pair[1])) for pair in combinations(bool_vars, 2)]

    def __exactly_one(self, bool_vars: list):
        return self.__at_most_one(bool_vars) + [self.__at_least_one(bool_vars)]

    def solve(self, instance: 'Instance'):
        s = Solver()
        courier_route = np.empty(
            shape=(instance.m, instance.max_path_length, instance.n+1), dtype=object)
        constraints = []
        for j in range(instance.m):
            for i in range(instance.max_path_length):
                for k in range(instance.n+1):
                    courier_route[j, i, k] = Bool(
                        f'courier_{j}_moment_{i}_pack_{k}')
        for j in range(instance.m):
            constraints.append(courier_route[j, 0, instance.n])
            constraints.append(
                courier_route[j, instance.max_path_length-1, instance.n])
            for i in range(0, instance.max_path_length):
                for k in range(instance.n):
                    constraints.append(self.__exactly_one(
                        courier_route[:, :, k].flatten().tolist()))
                constraints.append(self.__exactly_one(
                    courier_route[j, i, :].flatten().tolist()))

            for i in range(1, instance.min_packs + 1):
                constraints.append(Not(courier_route[j, i, instance.n]))

        if s.check() == sat:
            m = s.model()
            for j in range(instance.m):
                print(j, [k+1 for k in range(instance.n+1)
                      for i in range(instance.max_path_length) if m.evaluate(courier_route[j, i, k])])
        else:
            print("nope")


Sat_model().solve(Instance('instances/inst07.dat'))
