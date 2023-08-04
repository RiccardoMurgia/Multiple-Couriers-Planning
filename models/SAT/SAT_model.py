from z3 import *
from itertools import combinations


class MySatModel:

    def __init__(self):
        self.my_solver = Solver()
        self.my_optimizer = Optimize()

    @staticmethod
    def __at_most_one_pack_constraint(bool_vars: list):
        return [Not(And(pair[0], pair[1])) for pair in combinations(bool_vars, 2)]


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
        my_constraint_1 = MySatModel.__at_most_one_pack_constraint(bool_vars[:, 1: max_path - 2, current_pack])
        my_constraint_2 = [MySatModel.__at_least_one_pack_constraint(bool_vars[:, 1: max_path - 2, current_pack])]
        return my_constraint_1 + my_constraint_2

    @staticmethod
    def __go_stay_at_the_origin__if_finished_constraint(bool_vars: list, rider: int, pack: int, origin: int, N: int):
        return Implies(bool_vars[rider][pack][N], And(bool_vars[rider][pack + 1][N], bool_vars[rider][pack][origin]))

    def courier_routing_sat(self, M, N, cap, size, D, max_path, number_of_origin_stops, min_packs, origin: int):
        courier_route = [[[Bool(f"P_{m}_{k}_{n}") for m in range(M)] for k in range(max_path)] for n in range(origin)]

        # riders must be in the origin at the first and the last steps
        start_constraint, end_constraint = MySatModel.__start_end_origin_constraint(courier_route, origin, N, max_path)
        self.my_solver.add(start_constraint)
        self.my_solver.add(end_constraint)

        # riders must be outside the origin if they have to deliver some packs
        works_constraint = MySatModel.__package_delivery_constraint()
        self.my_solver.add(works_constraint)

        # riders must have at least one package assigned
        rider_loading_constraint = MySatModel.__at_least_one_pack_constraint(courier_route)  # TODO at last n packs
        self.my_solver.add(rider_loading_constraint)

        # packs must be delivered, and destinations visited only once
        for i in range(N - 1):
            MySatModel.__each_receiver_only_one_visit_constraint(courier_route, max_path, i)

        # riders stay at the origin if they have finished delivery
        for j in range(M):
            for i in range(1, max_path - 2):
                self.my_solver.add(MySatModel.__go_stay_at_the_origin__if_finished_constraint)

        # check maxload                      ##todo
        max_num = max(cap)
        binary_cap_length = MySatModel.__get_number_of_bit(max_num)

        bool_size = self.bool_encode(size, N, binary_cap_length, "S")
        bool_cap = self.bool_encode(cap, M, binary_cap_length, "C")

        bool_sum = [[False for _ in range(M)] for _ in range(N)]
        for j in range(M):
            indexes = []
            for i in range(N):
                if MySatModel.__at_least_one_pack_constraint(courier_route[j, : max_path - 2, i]):  # if it has pack
                    indexes.append(i)

            # Sum bitwise
            carry = False
            for k in indexes:
                for b in range(binary_cap_length):
                    tmp_value = bool_sum[j][b]
                    bool_sum[j][b] = Xor(Xor(bool_size[k][b], bool_sum[j][b]), carry)
                    carry = And(bool_size[k][b], tmp_value)

            # A >= B  =>  (A AND (NOT B)) OR (A nxor B)
            comparison = False
            for b in range(binary_cap_length, 0, -1):
                tmp_and = True
                for k in range(b, binary_cap_length):
                    my_xor = Not(Xor(bool_sum[j][k], bool_cap[j][k]))
                    tmp_and = And(tmp_and, my_xor)

                tmp = And(bool_cap[j][b], Not(bool_sum[j][b]))
                comparison = Or(And(tmp, tmp_and), comparison)

            self.my_solver.add(comparison)

        self.my_solver.add(bool_sum <= bool_cap)

        # minimizzare distanza massima peercorsa dei corrieri
        binary_D = [[Bool(f"D_{k}_{b}") for k in range(N)] for b in range(self.__get_number_of_bit(max(D)))]

        # Constraints to represent binary encoding for distances
        for k in range(N):
            binary_num = self.__binary_encode(D[k], len(binary_D))
            for b in range(len(binary_D)):
                if binary_num[b] == "1":
                    self.my_solver.add(binary_D[b][k])
                else:
                    self.my_solver.add(Not(binary_D[b][k]))

        # Define binary variables for courier distances
        courier_distance_vars = [[Bool(f"courier_distance_{j}_{b}") for j in range(M)] for b in range(len(binary_D))]

        # Constraints to calculate the binary distance for each courier
        for j in range(M):
            for b in range(len(binary_D)):
                self.my_solver.add(courier_distance_vars[b][j] ==
                                   Sum([If(courier_route[j][i][k], binary_D[b][k], False)
                                        for i in range(max_path) for k in range(N)]))

        # Minimize the maximum distance
        max_distance = courier_distance_vars[-1][0]  # Most significant bit represents the maximum distance
        self.my_optimizer.minimize(max_distance)

        if self.my_solver.check() == sat:
            return self.my_solver.model()
        else:
            print("Failed to solve")
            return None


myMode = MySatModel()
