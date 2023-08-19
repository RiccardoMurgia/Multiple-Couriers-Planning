from itertools import combinations
from z3 import Bool, Not, And, Or, Xor, Implies, Solver, sat
from z3.z3 import BoolRef
import numpy as np
import uuid


class SatInteger:
    def __init__(self, decimal_number: 'int' = 0, name: 'str' = "number",
                 binary: 'list' = [], pre_operations: 'list' = []) -> None:
        if len(binary) > 0:
            self.binary_length = len(binary)
            self.__representation = binary
            self.name = name
            self.__operations = pre_operations
            self.is_bool = self.binary_length == 1
            return

        self.__operations = pre_operations
        self.binary_length = self.__get_length(decimal_number)
        self.__representation = self.__convert(decimal_number,
                                               self.binary_length)
        self.name = name
        self.is_bool = self.binary_length == 1

    def __get_length(self, number: 'int') -> int:
        return len(bin(number)[2:])

    def __convert(self, number: 'int', length: 'int'):
        num = []
        str_num = bin(number)[2:]
        for i in range(length):
            ni = Bool(str(uuid.uuid4()))
            num.append(ni)
            if str_num[i] == '1':
                self.__operations.append(ni == True)
            else:
                self.__operations.append(ni == False)
        return np.array(num)

    def get(self, index: 'int'):
        return self.__representation[index]

    def all(self):
        return self.__representation

    def get_constraints(self) -> 'list':
        return self.__operations

    def add_greater(self, other):
        min_length = min(self.binary_length, other.binary_length)
        max_length = max(self.binary_length, other.binary_length)

        constraints = []
        for i in range(1, min_length + 1):
            constraint_i = [And(self.get(self.binary_length - i), Not(other.get(other.binary_length - i)))]
            for k in range(i + 1, min_length + 1):
                constraint_i.append(Or(
                    And(Not(self.get(self.binary_length - k)), Not(other.get(other.binary_length - k))),
                    self.get(self.binary_length - k)))

            constraints.append(And(constraint_i))
        constraints = [Or(constraints)]
        if min_length == self.binary_length:
            constraints += [
                Not(other.get(other.binary_length - i))
                for i in range(min_length + 1, max_length + 1)
            ]
        if min_length == other.binary_length:
            constraints += [
                self.get(self.binary_length - i) for i in range(min_length + 1, max_length + 1)
            ]
            constraints = [Or(constraints)]
        return constraints

    def add_less(self, other):
        min_length = min(self.binary_length, other.binary_length)
        max_length = max(self.binary_length, other.binary_length)

        constraints = []
        for i in range(1, min_length + 1):
            constraint_i = [And(Not(self.get(self.binary_length - i), other.get(other.binary_length - i)))]
            for k in range(i + 1, min_length + 1):
                constraint_i.append(Or(
                    And(Not(self.get(self.binary_length - k)), Not(other.get(other.binary_length - k))),
                    other.get(other.binary_length - k)))
            constraints.append(And(constraint_i))
        constraints = [Or(constraints)]
        if max_length == self.binary_length:
            constraints += [Not(self.get(self.binary_length - i))
                            for i in range(min_length + 1, max_length + 1)
                            ]
        if max_length == other.binary_length:
            constraints += [
                other.get(other.binary_length - i) for i in range(min_length + 1, max_length + 1)
            ]
            constraints = [Or(constraints)]
        return constraints

    def add_equal(self, other):
        min_length = min(self.binary_length, other.binary_length)
        max_length = max(self.binary_length, other.binary_length)

        constraints = [
            self.get(self.binary_length - i) ==
                other.get(other.binary_length - i)
            for i in range(1, min_length+1)]
        if min_length == max_length:
            return constraints

        longer = self
        if self.binary_length == min_length:
            longer = other

        constraints += [
            Not(longer.get(longer.binary_length - i))
            for i in range(min_length+1, max_length+1)
        ]
        return constraints

    def add_geq(self, other):
        return [Or(And(self.add_greater(other)),
                   And(self.add_equal(other)))]

    def add_leq(self, other):
        return [Or(And(self.add_less(other)),
                   And(self.add_equal(other)))]

    def to_decimal(self, model):
        num_list = []
        for i in reversed(range(self.binary_length)):
            num_list.append(self.__get_value(i,model))
        num = 0
        for i in range(self.binary_length):
            num += num_list[i]        
        return num

    def __get_value(self, i, model):
        value = False
        try:
            value = bool(model.evaluate(self.get(i)))
        except:
            pass
        if value:
            return 2 ** (self.binary_length - i - 1)
        return 0

    def __str__(self):
        return self.name + " " + str(self.__representation)

    def add_is_not_zero(self):
        return Or([b == True for b in self.all()])

    def add_is_zero(self):
        return Not(Or(self.all()))

    def set_to(self, number:'int', keep_constraint:'bool' = False):
        if not keep_constraint:
            self.__operations = []
        self.binary_length = self.__get_length(number)
        self.__representation = self.__convert(number, self.binary_length)
        self.is_bool = self.binary_length == 1

    def __add__(self, other):
        operations = []
        min_length = min(self.binary_length, other.binary_length)
        max_length = max(self.binary_length, other.binary_length)
        max_len_num = self
        min_len_num = other
        if max_length == other.binary_length:
            max_len_num = other
            min_len_num = self
        min_l = min_len_num.binary_length
        max_l = max_len_num.binary_length

        new_num = []
        num = Bool(str(uuid.uuid4()))
        operations.append(Xor(max_len_num.get(max_l - 1),
                                  min_len_num.get(min_l - 1)) == num)
        carry = And(max_len_num.get(max_l - 1),
                                  min_len_num.get(min_l - 1))
        new_num.append(num)
        for i in range(2, min_length + 1):
            formula = Xor(max_len_num.get(max_l - i),
                          min_len_num.get(min_l - i))
            final_num = Bool(str(uuid.uuid4()))
            operations.append(Xor(formula, carry) == final_num)
            carry = Or(And(formula, carry),
                                     And(max_len_num.get(max_l - i),
                                         min_len_num.get(min_l - i)))
            new_num.append(final_num)

        if min_length != max_length:

            for i in range(min_length+1, max_length+1):
                current_num = Bool(str(uuid.uuid4()))
                operations.append(
                    Xor(max_len_num.get(max_l - i), carry) == current_num)

                carry = And(max_len_num.get(max_l - i), carry)
                new_num.append(current_num)

        final_num = Bool(str(uuid.uuid4()))
        operations.append(carry == final_num)
        new_num.append(final_num)
        operations = operations + self.get_constraints() + other.get_constraints()
        return SatInteger(binary=list(reversed(new_num)),
                   name=f"({self.name} + {other.name})",
                   pre_operations=operations)

    def __mul__(self, other):

        not_boolean, boolean, not_boolean_operations, boolean_operations = self.__get_operands(
            self, other)
        new_num = []
        operations = []
        for n in not_boolean.all():
            new_n = Bool(str(uuid.uuid4()))
            operations.append(And(n, boolean) == new_n)
            new_num.append(new_n)
        operations = operations + not_boolean_operations + boolean_operations
        return SatInteger(binary=new_num,
                   name=f'({self.name} * {other})',
                   pre_operations=operations)

    def __get_operands(self, first, second):
        if isinstance(second, BoolRef):
            return first, second, first.get_constraints(), []
        if isinstance(first, BoolRef):
            return second, first, second.get_constraints(), []
        if isinstance(first, SatInteger) and isinstance(second, SatInteger):
            if second.is_bool:
                return first, second.get(0), first.get_constraints(), second.get_constraints()
            if first.is_bool:
                return second, first.get(0), second.get_constraints(), first.get_constraints()
        
        raise Exception("Error: implelemented mul only between Integer and booleans")

    __rmul__ = __mul__

def iff(left, right):
    return Or(
        And(left, right),
        And(Not(left), Not(right))
    )

def variable(variable_type:'str' = "bool", variable_length:'int' = 1, variable_name:'str'="name"):
    if variable_type == "bool":
        return Bool(variable_name)
    if variable_type == "int":
        return SatInteger(binary=[Bool(f"{variable_name}_{i}") for i in range(variable_length)])
    raise Exception(f"unknown variable type {variable_type}") 

amo = lambda x: And([Not(And(pair[0], pair[1])) for pair in combinations(x,2)])


def at_most_one(bool_vars):
    if len(bool_vars) < 5:
        return amo(bool_vars)

    y = Bool(str(uuid.uuid4()))
    return And(
        And(amo(bool_vars[:3] + [y])),
        at_most_one(bool_vars[3:] + [Not(y)])
    )

def at_least_one(bool_vars):
    return Or(bool_vars)

def exactly_one(bool_vars):
    return And(at_least_one(bool_vars), at_most_one(bool_vars))

def at_most_k(bool_vars, k):
    n = len(bool_vars)
    s = np.empty(shape=(k,n-1), dtype=object)
    for i in range(s.shape[0]):
        for j in range(s.shape[1]):
            s[i,j] = Bool(str(uuid.uuid4()))
    constraints = [Or(Not(bool_vars[0]), s[0,0])] + \
        [Not(s[0,j]) for j in range(1,k)]
    for i in range(1, n-1):
        constraints.append(Or(Not(bool_vars[i]), s[i,0]))
        constraints.append(Implies(s[i-1,0], s[i,0]))
        constraints.append(Implies(bool_vars[i], Not(s[i-1,k-1])))
        for j in range(i,k):
            constraints.append(Or(Not(bool_vars[i]), Not(s[i-1,j-1]), s[i,j]))
            constraints.append(Implies(s[i-1,j], s[i,j]))
    constraints.append(Implies(bool_vars[n-1], Not(s[n-2,k-1])))
    return And(constraints)

def at_least_k(bool_vars,k):
    if k == 1:
        return at_most_one(bool_vars)
    return at_most_k([Not(b) for b in bool_vars], len(bool_vars) - k)

def exactly_k(bool_vars,k):
    return And(at_least_k(bool_vars,k), at_most_k(bool_vars,k))

def usage():
    s = Solver()
    seven = SatInteger(7, "seven")
    three = SatInteger(3, "three")
    six = SatInteger(6, "six")
    ten = seven + three
    one = SatInteger(1, "one")
    res = seven * one
    b = Bool('zero')    
    res2 = seven * b
    s.add(Not(b))
    s.add(seven.get_constraints())
    s.add(three.get_constraints())
    s.add(ten.get_constraints())
    s.add(one.get_constraints())
    s.add(res.get_constraints())
    s.add(res2.get_constraints())
    _18 = SatInteger(18, '18')
    _24 = SatInteger(24, '24')
    s.add(_18.get_constraints())
    s.add(_24.get_constraints())
    # s.add(_18.add_greater(_24))
    s.add(seven.add_greater(six))
    s.add(six.add_less(seven))
    _2 = SatInteger(2, "2")
    _4 = SatInteger(4, "4")
    s.add(_2.get_constraints())
    s.add(_4.get_constraints())
    _six = SatInteger(binary=[Bool("six1"), Bool("six2"), Bool("six3"), Bool("six4"), Bool("six5")])
    s.add(_six.get_constraints())
    s.add(six.add_geq(_six))
    s.add(six.add_leq(_six))
    # s.add(_24.add_less(_18))
    _1234 = SatInteger(1234, "1234")
    _5678 = SatInteger(5678, "5678")
    s.add(_1234.get_constraints())
    s.add(_5678.get_constraints())
    r = _1234 + _5678
    s.add(r.get_constraints())
    _5 = SatInteger(5, "five")
    a = _5 * b
    op = _six * one
    a += op
    k = Bool("f")
    s.add(Not(k))
    op = _4 * k
    a += op
    s.add(a.get_constraints())
    print(s.check())
    if s.check() == sat:
        m = s.model()
        print("three",
              [m.evaluate(v) for v in three.all()], three.to_decimal(m))
        print("seven",
              [m.evaluate(v) for v in seven.all()], seven.to_decimal(m))
        print("res",
              [m.evaluate(v) for v in res.all()], res.to_decimal(m))
        print("res2",
              [m.evaluate(v) for v in res2.all()], res2.to_decimal(m))
        print("ten",
              [m.evaluate(v) for v in ten.all()], ten.to_decimal(m))
        print("one",
              [m.evaluate(v) for v in one.all()], one.to_decimal(m))
        print("six",
              [m.evaluate(v) for v in six.all()], six.to_decimal(m))
        print("_six",
              [m.evaluate(v) for v in _six.all()], _six.to_decimal(m))
        print("_18",
              [m.evaluate(v) for v in _18.all()], _18.to_decimal(m))
        print("_24",
              [m.evaluate(v) for v in _24.all()], _24.to_decimal(m))
        print("r",
              [m.evaluate(v) for v in r.all()], r.to_decimal(m))
        print("a", a.to_decimal(m))


if __name__ == "__main__":
    usage()
