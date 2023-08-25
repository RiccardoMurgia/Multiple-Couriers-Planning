from itertools import combinations
from z3 import Bool, Not, And, Or, Xor, Implies, Solver, sat
from z3.z3 import BoolRef
from math import ceil, log2
import numpy as np
import uuid


class SatSequenceInteger:
    def __init__(self, number:'int' = 0, numbers:'list[tuple]' = [], constraints:'list' = []) -> None:
        if len(numbers) > 0:
            self.__numbers = numbers
            self.__constraints = constraints
        else:
            b = Bool(str(uuid.uuid4()))
            self.__numbers = [(number, b)]
            self. __constraints = constraints + [b == True]

        self.len = len(self.__numbers)

    def get_constraints(self):
        return self.__constraints

    def all(self):
        return self.__numbers

    def __getitem__(self, idx):
        return self.__numbers[idx]

    def __add__(self, other:'SatSequenceInteger') -> 'SatSequenceInteger':
        new_num = self.all() + other.all()
        return SatSequenceInteger(numbers=new_num, constraints=self.__constraints + other.get_constraints())

    def __mul__(self, other:'BoolRef'):
        constraints = self.__constraints
        new_num = []
        for touple in self:
            new_num.append((touple[0], And(touple[1],other)))
        return SatSequenceInteger(numbers=self.__numbers, constraints = constraints)

    def add_greater(self, other:'int'):
        upper_constraints = []
        lower_constraints = []
        new_vars = []
        for couple in self.all():
            if couple[0] > other:
                upper_constraints.append(couple[1])
            else:
                new_vars_i = [Bool(str(uuid.uuid4())) for _ in range(couple[0])]
                new_vars += new_vars_i
                lower_constraints.append(And(new_vars_i + [couple[1]]))
        if len(new_vars) > other:
            return And(Or(upper_constraints + [at_least_k(new_vars, other)]),And(lower_constraints))
        if len(new_vars) == other:
            return And(Or(upper_constraints + [And(new_vars)]),And(lower_constraints))

        return Or(upper_constraints)

    def add_less(self, other:'int'):
        return Not(self.add_geq(other))

    def add_geq(self, other:'int'):
        upper_constraints = []
        lower_constraints = []
        new_vars = []
        for couple in self.all():
            if couple[0] > other:
                upper_constraints.append(couple[1])
            else:
                new_vars_i = [Bool(str(uuid.uuid4())) for _ in range(couple[0])]
                new_vars += new_vars_i
                lower_constraints.append(And(new_vars_i + [couple[1]]))

        if len(new_vars) > other:
            return And(Or(upper_constraints + [at_least_k(new_vars, other)]),And(lower_constraints))
        if len(new_vars) == other:
            return And(Or(upper_constraints + [And(new_vars)]),And(lower_constraints))

        return Or(upper_constraints)

    def add_leq(self, other:'int'):
        return Not(self.add_greater(other))
    
    def to_decimal(self, model):
        res = 0
        for couple in self.all():
            try:
                if model.evaluate(couple[1]):
                    res += couple[0]
            except:
                pass

        return res


class SatOrderInteger:
    def __init__(self, integer:'int' = 0, sequence:'list[BoolRef]' = [], constraints:'list' = [], name:'str'="name") -> None:
        if len(sequence) > 0:
            self.__encoding = sequence
            self.name = name
            self.__constraints = constraints
            self.len = len(sequence)
            return

        self.__encoding = [Bool(str(uuid.uuid4())) for _ in range(integer)]
        self.__constraints = [And(self.__encoding)] + constraints
        self.name = name
        self.len = integer


    def get_constraints(self) -> list:
        return self.__constraints

    def all(self):
        return self.__encoding

    def __add__(self, other:'SatOrderInteger') -> 'SatOrderInteger':
        encoding = self.all() + other.all()
        constraints = self.__constraints + other.get_constraints()

        return SatOrderInteger(sequence=encoding, constraints=constraints)


    def __getitem__(self, idx):
        return self.__encoding[idx]


    def __mul__(self, other:'BoolRef') -> 'SatOrderInteger':
        encoding = [Bool(str(uuid.uuid4())) for _ in range(len(self.all()))]
        constraints = self.__constraints + [And(self[i], other) == encoding[i] for i in range(len(self.all()))]
        return SatOrderInteger(sequence=encoding, constraints=constraints)

    def to_decimal(self,model):
        res = 0
        for b in self.all():
            try:
                if model.evaluate(b):
                    res += 1

            except:
                pass
        return res


    def add_greater(self, other:'int'):
        if other + 1 == self.len:
            return And(self.all())
        return at_least_k(self.all(), other + 1)
    
    def add_less(self, other:'int'):
        return at_most_k(self.all(), other - 1)

    def add_equal(self, other:'int'):
        return exactly_k(self.all(), other)

    def add_geq(self, other:'int'):
        if self.len < other:
            print("oh, no", self.len, len(self.all()))
            return False
        return at_least_k(self.all(), other)

    def add_leq(self, other:'int'):
        if self.len < other:
            return True
        return at_most_k(self.all(), other)


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

    def __convert(self, number: 'int', length: 'int') -> 'list[BoolRef]':
        num = []
        str_num = bin(number)[2:]
        for i in range(length):
            ni = Bool(str(uuid.uuid4()))
            num.append(ni)
            if str_num[i] == '1':
                self.__operations.append(ni == True)
            else:
                self.__operations.append(ni == False)
        return num

    def __getitem__(self, index: 'int'):
        return self.__representation[index]

    def all(self):
        return self.__representation

    def get_constraints(self) -> 'list':
        return self.__operations


    def add_greater(self, other):
        max_length = max(self.binary_length, other.binary_length)

        self.extend(max_length-self.binary_length)
        other.extend(max_length-other.binary_length)
        

        constraints = []

        
        gts = [Bool(str(uuid.uuid4())) for _ in range(max_length + 1)]
        geqs = [Bool(str(uuid.uuid4())) for _ in range(max_length + 1)]

        constraints += [gts[0] == False, geqs[0] == True]
        for i in range(0,max_length):
            constraints += [
                gts[i + 1] == And(self[i], Not(other[i]), geqs[i]),
                geqs[i + 1] == And(self[i] == other[i], geqs[i]),
                
            ]

        constraints.append(Or(gts))
        return constraints

    def add_less(self, other):
        max_length = max(self.binary_length, other.binary_length)

        self.extend(max_length-self.binary_length)
        other.extend(max_length-other.binary_length)
        

        constraints = []

        
        lts = [Bool(str(uuid.uuid4())) for _ in range(max_length + 1)]
        leqs = [Bool(str(uuid.uuid4())) for _ in range(max_length + 1)]

        constraints += [lts[0] == False, leqs[0] == True]
        for i in range(0,max_length):
            constraints += [
                lts[i + 1] == And(Not(self[i]), other[i], leqs[i]),
                leqs[i + 1] == And(self[i] == other[i], leqs[i]),
                
            ]

        constraints.append(Or(lts))
        return constraints



    def add_equal(self, other):
        max_length = max(self.binary_length, other.binary_length)
        self.extend(max_length - self.binary_length)
        other.extend(max_length - other.binary_length)
        return [
            self[i] == other[i] for i in range(max_length)
        ]

    def add_geq(self, other):
        max_length = max(self.binary_length, other.binary_length)

        self.extend(max_length-self.binary_length)
        other.extend(max_length-other.binary_length)
        

        constraints = []

        
        gts = [Bool(str(uuid.uuid4())) for _ in range(max_length + 1)]
        geqs = [Bool(str(uuid.uuid4())) for _ in range(max_length + 1)]

        constraints += [gts[0] == False, geqs[0] == True]
        for i in range(0,max_length):
            constraints += [
                gts[i + 1] == And(self[i], Not(other[i]), geqs[i]),
                geqs[i + 1] == And(self[i] == other[i], geqs[i]),
                
            ]

        constraints.append(Or(gts + [And(geqs)]))
        return constraints
        

    def add_leq(self, other):
        max_length = max(self.binary_length, other.binary_length)

        self.extend(max_length-self.binary_length)
        other.extend(max_length-other.binary_length)
        

        constraints = []

        
        lts = [Bool(str(uuid.uuid4())) for _ in range(max_length + 1)]
        leqs = [Bool(str(uuid.uuid4())) for _ in range(max_length + 1)]

        constraints += [lts[0] == False, leqs[0] == True]
        for i in range(0,max_length):
            constraints += [
                lts[i + 1] == And(Not(self[i]), other[i], leqs[i]),
                leqs[i + 1] == And(self[i] == other[i], leqs[i]),
                
            ]

        constraints.append(Or(lts + [And(leqs)]))
        return constraints


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
            value = bool(model.evaluate(self[i]))
        except:
            pass
        if value:
            return 2 ** (self.binary_length - i - 1)
        return 0

    def __str__(self):
        return self.name + " " + str(self.__representation)

    def is_not_zero(self):
        return Or(self.all())

    def extend(self, n:'int'):
        extra = [Bool(str(uuid.uuid4())) for _ in range(n)]
        self.__operations.append(Not(Or(extra)))
        self.__representation = extra + self.__representation
        self.binary_length = len(self.__representation)

    def is_zero(self):
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
        new_num.append(Xor(max_len_num[max_l - 1],
                                  min_len_num[min_l - 1]))
        carry = And(max_len_num[max_l - 1],
                                  min_len_num[min_l - 1])
        for i in range(2, min_length + 1):
            formula = Xor(max_len_num[max_l - i],
                          min_len_num[min_l - i])
            new_num.append(Xor(formula, carry))
            carry = Or(And(formula, carry),
                                     And(max_len_num[max_l - i],
                                         min_len_num[min_l - i]))

        if min_length != max_length:

            for i in range(min_length+1, max_length+1):
                new_num.append(
                    Xor(max_len_num[max_l - i], carry))

                carry = And(max_len_num[max_l - i], carry)

        new_num.append(carry)
        operations = operations + self.get_constraints() + other.get_constraints()
        return SatInteger(binary=list(reversed(new_num)),
                   name=f"({self.name} + {other.name})",
                   pre_operations=operations)

    def __mul__(self, other):

        not_boolean, boolean, not_boolean_operations, boolean_operations = self.__get_operands(
            self, other)
        new_num = []
        for n in not_boolean.all():
            new_num.append(And(n, boolean))
        operations = not_boolean_operations + boolean_operations
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
                return first, second[0], first.get_constraints(), second.get_constraints()
            if first.is_bool:
                return second, first[0], second.get_constraints(), first.get_constraints()
        
        raise Exception("Error: implelemented mul only between Integer and booleans")

    __rmul__ = __mul__

class SatSequences:
    def __init__(self, length):
        self.__sequence = [Bool(str(uuid.uuid4())) for _ in range(length)]
        self.length = length
        self.is_zero = Bool(str(uuid.uuid4()))
    

    def add(self):
        return self.is_zero == Not(Or(self.__sequence))

    def __getitem__(self,index):
        return self.__sequence[index]

    def next(self, other:'SatSequences'):
        constraints = [exactly_one(self.__sequence)]

        for i in range(1,self.length):
            constraints.append(
                self[i] == other[i-1]
            )

        constraints.append(Implies(other.is_zero,self[0]))
        return constraints

    def to_decimal(self,model):
        for i in range(self.length):
            try:
                value = model.evaluate(self[i])
                if value: 
                    return i + 1
            except:
                pass
        return 0


def variable(variable_length:'int' = 1, variable_name:'str'="name")->'SatInteger':
    return SatInteger(binary=[Bool(str(uuid.uuid4())) for _ in range(variable_length)], name= variable_name)

amo = lambda x: And([Not(And(pair[0], pair[1])) for pair in combinations(x,2)])

def toBinary(num, length = None):
    num_bin = bin(num).split("b")[-1]
    if length:
        return "0"*(length - len(num_bin)) + num_bin
    return num_bin

def at_most_one(bool_vars):
    constraints = []
    n = len(bool_vars)
    m = ceil(log2(n))
    r = [Bool(str(uuid.uuid4())) for _ in range(m)]
    binaries = [toBinary(i, m) for i in range(n)]
    for i in range(n):
        for j in range(m):
            phi = Not(r[j])
            if binaries[i][j] == "1":
                phi = r[j]
            constraints.append(Or(Not(bool_vars[i]), phi))        
    return And(constraints)

def at_least_one(bool_vars):
    return Or(bool_vars)

def exactly_one(bool_vars):
    return And(at_least_one(bool_vars), at_most_one(bool_vars))

def at_most_k(bool_vars, k):
    n = len(bool_vars)
    s = np.array([[Bool(str(uuid.uuid4())) for _ in range(k)] for _ in range(n - 1)])
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
        return at_least_one(bool_vars)
    return at_most_k([Not(b) for b in bool_vars], len(bool_vars) - k)

def exactly_k(bool_vars,k):
    return And(at_least_k(bool_vars,k), at_most_k(bool_vars,k))



def usage():
    s = Solver()
    seven = SatInteger(7, "seven")
    three = SatInteger(3, "three")
    
    fifteen = SatInteger(15, "q")
    sixteen = SatInteger(16, "s")
    s.add(fifteen.get_constraints())
    s.add(sixteen.get_constraints())
    s.add(sixteen.add_greater(fifteen))
    
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
    _six = SatInteger(binary=[Bool("six1"), Bool("six2"), Bool("six3"), Bool("six4"), Bool("six5")], name="_six")
    s.add(six.add_leq(_six))
    s.add(six.add_geq(_six))
    # s.add(six.add_equal(_six))
    s.add(_six.get_constraints())
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
    seq1 = SatSequences(5)
    seq2 = SatSequences(5)
    seq3 = SatSequences(5)
    seq4 = SatSequences(5)
    s.add(seq1.add())
    s.add(seq2.add())
    s.add(seq3.add())
    s.add(seq4.add())
    s.add(seq2.next(seq1))
    s.add(seq3.next(seq2))
    s.add(seq4.next(seq3))
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
        print("seq1", seq1.to_decimal(m), m.evaluate(seq1.is_zero), [m.evaluate(seq1[i]) for i in range(5)])
        print("seq2", seq2.to_decimal(m), m.evaluate(seq2.is_zero), [m.evaluate(seq2[i]) for i in range(5)])
        print("seq3", seq3.to_decimal(m), m.evaluate(seq3.is_zero), [m.evaluate(seq3[i]) for i in range(5)])
        print("seq4", seq4.to_decimal(m), m.evaluate(seq4.is_zero), [m.evaluate(seq4[i]) for i in range(5)])

def usage_2():
    s = Solver()
    seven = SatOrderInteger(integer=7, name="seven")
    three = SatOrderInteger(3)
    
    fifteen = SatOrderInteger(15)
    sixteen = SatOrderInteger(16)
    s.add(fifteen.get_constraints())
    s.add(sixteen.get_constraints())
    s.add(sixteen.add_greater(15))
    
    six = SatOrderInteger(6)
    ten = seven + three
    one = SatOrderInteger(1)
    res = seven * one[0]
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
    s.add(seven.add_greater(6))
    s.add(six.add_less(7))
    s.add(six.get_constraints())
    _2 = SatOrderInteger(2)
    _4 = SatOrderInteger(4)
    s.add(_2.get_constraints())
    s.add(_4.get_constraints())
    # _six = SatInteger(binary=[Bool("six1"), Bool("six2"), Bool("six3"), Bool("six4"), Bool("six5")], name="_six")
    # s.add(six.add_leq(_six))
    # s.add(six.add_geq(_six))
    # s.add(six.add_equal(_six))
    # s.add(_six.get_constraints())
    # s.add(_24.add_less(_18))
    _1234 = SatOrderInteger(1234)
    _5678 = SatOrderInteger(5678)
    s.add(_1234.get_constraints())
    s.add(_5678.get_constraints())
    r = _1234 + _5678
    s.add(r.get_constraints())
    _5 = SatOrderInteger(5)
    a = _5 * b
    # op = _six * one
    # a += op
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
        # print("_six",
        #       [m.evaluate(v) for v in _six.all()], _six.to_decimal(m))
        print("_18",
              [m.evaluate(v) for v in _18.all()], _18.to_decimal(m))
        print("_24",
              [m.evaluate(v) for v in _24.all()], _24.to_decimal(m))
        print("r",
               r.to_decimal(m))
 
def usage_3():
    s = Solver()
    seven = SatSequenceInteger(7)
    three = SatSequenceInteger(3)
    
    fifteen = SatSequenceInteger(15)
    sixteen = SatSequenceInteger(16)
    s.add(fifteen.get_constraints())
    s.add(sixteen.get_constraints())
    s.add(sixteen.add_greater(15))
    
    six = SatSequenceInteger(6)
    ten = seven + three
    one = SatSequenceInteger(1)
    res = seven * one[0][1]
    b = Bool('zero')    
    res2 = seven * b
    s.add(Not(b))
    s.add(seven.get_constraints())
    s.add(three.get_constraints())
    s.add(ten.get_constraints())
    s.add(one.get_constraints())
    s.add(res.get_constraints())
    s.add(res2.get_constraints())
    _18 = SatSequenceInteger(18)
    _24 = SatSequenceInteger(24)
    s.add(_18.get_constraints())
    s.add(_24.get_constraints())
    # s.add(_18.add_greater(_24))
    s.add(seven.add_greater(6))
    s.add(six.add_less(7))
    s.add(six.get_constraints())
    _2 = SatSequenceInteger(2)
    _4 = SatSequenceInteger(4)
    s.add(_2.get_constraints())
    s.add(_4.get_constraints())
    # _six = SatInteger(binary=[Bool("six1"), Bool("six2"), Bool("six3"), Bool("six4"), Bool("six5")], name="_six")
    # s.add(six.add_leq(_six))
    # s.add(six.add_geq(_six))
    # s.add(six.add_equal(_six))
    # s.add(_six.get_constraints())
    # s.add(_24.add_less(_18))
    _1234 = SatSequenceInteger(1234)
    _5678 = SatSequenceInteger(5678)
    s.add(_1234.get_constraints())
    s.add(_5678.get_constraints())
    r = _1234 + _5678
    s.add(r.get_constraints())
    _5 = SatSequenceInteger(5)
    a = _5 * b
    # op = _six * one
    # a += op
    k = Bool("f")
    s.add(Not(k))
    op = _4 * k
    a += op
    s.add(a.get_constraints())
    print(s.check())
    if s.check() == sat:
        m = s.model()
        print("three", three.to_decimal(m))
        print("seven", seven.to_decimal(m))
        print("res", res.to_decimal(m))
        print("res2", res2.to_decimal(m))
        print("ten", ten.to_decimal(m))
        print("one", one.to_decimal(m))
        print("six", six.to_decimal(m))
        # print("_six",
        #       [m.evaluate(v) for v in _six.all()], _six.to_decimal(m))
        print("_18", _18.to_decimal(m))
        print("_24", _24.to_decimal(m))
        print("r",
               r.to_decimal(m))

if __name__ == "__main__":
    usage()