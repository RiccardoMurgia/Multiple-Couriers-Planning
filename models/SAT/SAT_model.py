from z3 import *
from itertools import combinations


class MySatModel:

    def __init__(self):
        self.my_solver = Solver()
        self.my_optimizer = Optimize()

    @staticmethod
    def __get_number_of_bit(number: int) -> int:
        num_bit = 0
        if number == 0:
            return 0
        while number > 0:
            num_bit += 1
            number = number // 2
        return num_bit

    @staticmethod
    def __binary_encode(number: int, size: int) -> str:
        if number == 0:
            return "0"

        binary_digits = []
        i = 0

        while i < size:
            remainder = number % 2
            binary_digits.append(str(remainder))
            number //= 2
            i = i + 1

        binary_string = "".join(binary_digits)
        return binary_string

    @staticmethod
    def __sum_enc(first_n: str, second_n: str) -> str:
        carry = 0
        result = []
        i, j = len(first_n) - 1, len(second_n) - 1

        while i >= 0 or j >= 0 or carry:
            bit1 = int(first_n[i]) if i >= 0 else 0
            bit2 = int(second_n[j]) if j >= 0 else 0
            current_sum = bit1 + bit2 + carry

            result.insert(0, str(current_sum % 2))
            carry = current_sum // 2

            i -= 1
            j -= 1

        return ''.join(result)

    @staticmethod
    def __binary_greater(binary_str1: str, binary_str2: str, equal=True) -> bool:
        # Remove leading zeros from the binary strings
        binary_str1 = binary_str1.lstrip('0')
        binary_str2 = binary_str2.lstrip('0')

        # Compare lengths of the binary strings after removing leading zeros
        len1 = len(binary_str1)
        len2 = len(binary_str2)

        # If the lengths are different, return the result directly based on length
        if len1 > len2:
            return True
        elif len1 < len2:
            return False

        # If lengths are equal, compare bit by bit
        for bit1, bit2 in zip(binary_str1, binary_str2):
            bit1, bit2 = int(bit1), int(bit2)
            if bit1 > bit2:
                return True
            elif bit1 < bit2:
                return False

        # If all bits are equal and 'equal' is True, the two binary strings are considered equal
        return equal

    @staticmethod
    def __at_least_one(bool_vars: list):
        return Or(bool_vars)

    @staticmethod
    def __at_most_one(bool_vars: list):
        return [Not(And(pair[0], pair[1])) for pair in combinations(bool_vars, 2)]

    @staticmethod
    def __exactly_one(bool_vars: list):
        return MySatModel.__at_most_one(bool_vars) + [MySatModel.__at_least_one(bool_vars)]

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

    def courier_routing_sat(self, M, N, cap, size, D, max_path, number_of_origin_stops, min_packs, origin: int):
        courier_route = [[[Bool(f"P_{m}_{k}_{n}") for m in range(M)] for k in range(max_path)] for n in range(origin)]

        # essere inizio e fine in origine
        start = And(courier_route[:, 0, origin])
        end = And(courier_route[:, max_path - 1, N])
        self.my_solver.add(And(start, end))
        self.my_solver.add(Not(courier_route[:, 1:min_packs, N]))

        # ogni corriere almeno un pacco
        self.my_solver.add(MySatModel.__at_least_one(courier_route[:, : max_path - 1, :]))  # todo at_least_n_pack

        # ogni pacco deve essere consegnato, ongi zona va passata un volta sola
        for i in range(N - 1):
            self.my_solver.add(MySatModel.__exactly_one(courier_route[:, 1: max_path - 2, i]))

        # rimanere all'origine una volta che ci arrivi
        for j in range(M):
            for i in range(max_path - 2):
                self.my_solver.add(Implies(courier_route[j][i][N], And(courier_route[j][i + 1][N],
                                                                       courier_route[j][i][origin])))

                # self.my_solver.add(Implies(courier_route[j][i][N], And(courier_route[j, i + 1: max_path - 1, N])))
                # Implies sostituiisce questo:
                # not_origin = Not(courier_route[j][i][N])
                # origin = And(courier_route[j, i + 1 : max_path - 1, N])
                # self.my_solver.add(Or(not_origin, origin))  

        # controllare la max load
        max_num = max(cap)
        binary_cap_length = MySatModel.__get_number_of_bit(max_num)

        bool_size = self.bool_encode(size, N, binary_cap_length, "S")
        bool_cap = self.bool_encode(cap, M, binary_cap_length, "C")

        bool_sum = [[False for _ in range(M)] for _ in range(N)]
        for j in range(M):
            indexes = []
            for i in range(N):
                if MySatModel.__at_least_one(courier_route[j, : max_path - 2, i]):  # if it has pack
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
