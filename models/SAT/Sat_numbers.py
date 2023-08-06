from z3 import Bool, Not, And, Or, Xor, Solver, Implies, sat
from z3.z3 import BoolRef
import numpy as np
import uuid


class D2B:
    def __init__(self, decimal_number: 'int' = 0, name: 'str' = "number",
                 binary: 'list' = None, pre_operations: 'list' = []) -> None:
        if binary is not None:
            self.binary_length = len(binary)
            self.__representation = binary
            self.name = name
            self.__operations = pre_operations
            self.is_bool = self.binary_length == 1
            return

        self.__operations = pre_operations
        self.binary_length = self.__get_length(decimal_number)
        self.__representation = self.__convert(decimal_number,
                                               self.binary_length, name)
        self.name = name
        self.is_bool = self.binary_length == 1

    def __get_length(self, number: 'int') -> int:
        return len(bin(number)[2:])

    def __convert(self, number: 'int', length: 'int', name: 'str'):
        num = []
        str_num = bin(number)[2:]
        for i in range(length):
            ni = Bool(str(uuid.uuid4()))
            num.append(ni)
            if str_num[i] == '1':
                self.__operations.append(ni)
            else:
                self.__operations.append(Not(ni))
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
        for i in range(min_length):
            constraint_i = [And(self.get(i), Not(other.get(i)))]
            for k in range(i):
                constraint_i.append(Or(
                    And(Not(self.get(k)), Not(other.get(k))),
                    self.get(k)))

            constraints.append(And(constraint_i))
        constraints = [Or(constraints)]
        if min_length == self.binary_length:
            constraints += [
                Not(other.get(i))
                for i in range(min_length, max_length)
            ]
        return constraints

    def add_less(self, other):
        min_length = min(self.binary_length, other.binary_length)
        max_length = max(self.binary_length, other.binary_length)

        constraints = []
        for i in range(min_length):
            constraint_i = [And(Not(self.get(i), other.get(i)))]
            for k in range(i):
                constraint_i.append(Or(
                    And(Not(self.get(k)), Not(other.get(k))),
                    other.get(k)))
            constraints.append(And(constraint_i))
        constraints = [Or(constraints)]
        if max_length == self.binary_length:
            constraints += [Not(self.get(i))
                            for i in range(min_length, max_length)
                            ]
        return constraints

    def add_equal(self, other):
        min_length = min(self.binary_length, other.binary_length)
        max_length = max(self.binary_length, other.binary_length)

        constraints = [
            iff(self.get(self.binary_length - i),
                other.get(other.binary_length - i))
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
        num = 0
        for i in reversed(range(self.binary_length)):
            exponent = self.binary_length - i - 1
            num += 2 ** exponent if model.evaluate(self.get(i)) else 0
        return num

    def __str__(self):
        return self.name + " " + str(self.__representation)

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
        operations.append(iff(Xor(max_len_num.get(max_l - 1),
                                  min_len_num.get(min_l - 1)), num))
        carry = Bool(str(uuid.uuid4()))
        operations.append(iff(And(max_len_num.get(max_l - 1),
                                  min_len_num.get(min_l - 1)), carry))
        new_num.append(num)
        for i in range(2, min_length + 1):
            formula = Xor(max_len_num.get(max_l - i),
                          min_len_num.get(min_l - i))
            final_num = Bool(str(uuid.uuid4()))
            operations.append(iff(Xor(formula, carry), final_num))
            new_carry = Bool(str(uuid.uuid4()))
            operations.append(iff(Or(And(formula, carry),
                                     And(max_len_num.get(max_l - i),
                                         min_len_num.get(min_l - i))),
                                  new_carry))
            carry = new_carry
            new_num.append(final_num)

        if min_length != max_length:

            for i in range(min_length+1, max_length+1):
                current_num = Bool(str(uuid.uuid4()))
                operations.append(iff(
                    Xor(max_len_num.get(max_l - i), carry), current_num))

                new_carry = Bool(str(uuid.uuid4()))
                operations.append(iff(
                    And(max_len_num.get(max_l - i), carry), new_carry))
                carry = new_carry
                new_num.append(current_num)

        final_num = Bool(str(uuid.uuid4()))
        operations.append(iff(carry, final_num))
        new_num.append(final_num)
        return D2B(binary=list(reversed(new_num)),
                   name=f"({self.name} + {other.name})",
                   pre_operations=operations)

    def __mul__(self, other):

        not_boolean, boolean = self.__get_operands(self, other)
        new_num = []
        operations = []
        for n in not_boolean.all():
            new_n = Bool(f'mult_{self.name}_{n}_{other}')
            operations.append(iff(And(n, boolean), new_n))
            new_num.append(new_n)
        return D2B(binary=new_num,
                   name=f'({self.name} * {other})',
                   pre_operations=operations)

    def __get_operands(self, first, second):
        if isinstance(second, BoolRef):
            return first, second
        if isinstance(first, BoolRef):
            return second, first
        if isinstance(first, D2B) and isinstance(second, D2B):
            if second.is_bool:
                return first, second.get(0)
            if first.is_bool:
                return second, first.get(0)
        if not (first.is_bool or second.is_bool):
            raise
            Exception(
                "Error: implelemented mul only between D2B and booleans")

    __rmul__ = __mul__


def iff(left, right):
    return Or(
        And(left, right),
        And(Not(left), Not(right))
    )


def usage():
    s = Solver()
    seven = D2B(7, "seven")
    three = D2B(3, "three")
    six = D2B(6, "six")
    ten = seven + three
    one = D2B(1, "one")
    res = seven * one
    b = Or(Bool('zero'), Bool("one"))
    res2 = seven * b
    s.add(b)
    s.add(seven.get_constraints())
    s.add(three.get_constraints())
    s.add(ten.get_constraints())
    s.add(one.get_constraints())
    s.add(res.get_constraints())
    s.add(res2.get_constraints())
    _18 = D2B(18, '18')
    _24 = D2B(24, '24')
    s.add(_18.get_constraints())
    s.add(_24.get_constraints())
    # s.add(_18.add_greater(_24))
    s.add(seven.add_greater(six))
    s.add(six.add_less(seven))
    _2 = D2B(2, "2")
    _4 = D2B(4, "4")
    s.add(_2.get_constraints())
    s.add(_4.get_constraints())
    _six = _2 + _4
    s.add(_six.get_constraints())
    s.add(six.add_equal(_six))
    # s.add(_24.add_less(_18))
    _1234 = D2B(1234, "1234")
    _5678 = D2B(5678, "5678")
    s.add(_1234.get_constraints())
    s.add(_5678.get_constraints())
    r = _1234 + _5678
    s.add(r.get_constraints())
    _5 = D2B(5, "five")
    s.add(_5.get_constraints())
    a = _5 * b
    s.add(a.get_constraints())
    op = _six * one
    s.add(op.get_constraints())
    a += op
    s.add(a.get_constraints())
    k = Bool("f")
    s.add(Not(k))
    op = _4 * k
    s.add(op.get_constraints())
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
