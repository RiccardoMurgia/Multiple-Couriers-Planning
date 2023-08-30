from itertools import combinations
from z3 import Bool, Not, And, Or, Xor, Implies
from z3.z3 import BoolRef
from math import ceil, log2
import numpy as np
import uuid

debug_gts = []
debug_eqs = []
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

    def __getitem__(self, index: 'int|slice')->'BoolRef|list':
        return self.__representation[index]

    def all(self) -> 'list':
        return self.__representation

    def get_constraints(self) -> 'list':
        return self.__operations


    def add_greater(self, other:'SatInteger'):
        max_length = max(self.binary_length, other.binary_length)
        min_length = min(self.binary_length, other.binary_length)
        remain = max_length - min_length
        self_all = self.all()
        other_all = other.all()
        constraints = []
        if remain == 0:
            pass
        elif self.binary_length == min_length:
            other_all = other[remain:]
            constraints.append(Not(Or(other[:remain])))
        elif other.binary_length == min_length:
            self_all = self[remain:]
            
        gts = [And(self_all[0], Not(other_all[0]))] + [Bool(str(uuid.uuid4())) for _ in range(min_length-1)]
        eqs = [self_all[0] == other_all[0]] + [Bool(str(uuid.uuid4())) for _ in range(min_length-1)]
        for i in range(1,min_length):
            constraints += [
                gts[i] == And(self_all[i], Not(other_all[i]), eqs[i-1]),
                eqs[i] == And(self_all[i] == other_all[i], eqs[i-1]),
                
            ]

        is_greater = Or(gts)
        if other.binary_length == min_length and remain != 0:
            is_greater = Or(gts + self[:remain])
        constraints.append(is_greater)

        return constraints

    def add_less(self, other:'SatInteger'):
        max_length = max(self.binary_length, other.binary_length)
        min_length = min(self.binary_length, other.binary_length)
        remain = max_length - min_length
        self_all = self.all()
        other_all = other.all()
        constraints = []
        if remain == 0:
            pass
        elif self.binary_length == min_length:
            other_all = other[remain:]
        elif other.binary_length == min_length:
            constraints.append(Not(Or(self[:remain])))
            self_all = self[remain:]
            
        lts = [And(Not(self_all[0]), other_all[0])] + [Bool(str(uuid.uuid4())) for _ in range(min_length-1)]
        eqs = [self_all[0] == other_all[0]] + [Bool(str(uuid.uuid4())) for _ in range(min_length-1)]
        for i in range(1,min_length):
            constraints += [
                lts[i] == And(Not(self_all[i]), other_all[i], eqs[i-1]),
                eqs[i] == And(self_all[i] == other_all[i], eqs[i-1]),
                
            ]

        is_smaller = Or(lts)
        if self.binary_length == min_length and remain != 0:
            is_smaller = Or(lts + other[:remain])
        constraints.append(is_smaller)
        return constraints



    def add_equal(self, other:'SatInteger'):
        max_length = max(self.binary_length, other.binary_length)
        min_length = min(self.binary_length, other.binary_length)

        bigger = self
        smaller = other
        if self.binary_length == min_length:
            smaller = self
            bigger = other

        constraints = [Not(Or(bigger[:max_length - min_length]))]
        bigger = bigger[max_length - min_length:]
        constraints +=[bigger[i] == smaller[i] for i in range(min_length)]
        return constraints

    def add_geq(self, other):
        max_length = max(self.binary_length, other.binary_length)
        min_length = min(self.binary_length, other.binary_length)
        remain = max_length - min_length
        self_all = self.all()
        other_all = other.all()
        constraints = []
        if remain == 0:
            pass
        elif self.binary_length == min_length:
            constraints.append(Not(Or(other[:remain])))
            other_all = other[remain:]
        elif other.binary_length == min_length:
            self_all = self[remain:]
            
        gts = [And(self_all[0], Not(other_all[0]))] + [Bool(str(uuid.uuid4())) for _ in range(min_length-1)]
        eqs = [self_all[0] == other_all[0]] + [Bool(str(uuid.uuid4())) for _ in range(min_length-1)]
        for i in range(1,min_length):
            constraints += [
                gts[i] == And(self_all[i], Not(other_all[i]), eqs[i-1]),
                eqs[i] == And(self_all[i] == other_all[i], eqs[i-1]),
                
            ]

        is_greater = Or(gts + [And(eqs)])
        if other.binary_length == min_length and remain != 0:
            is_greater = Or(gts + [Or(self[:remain])] + [And(eqs)])
        constraints.append(is_greater)
        return constraints        

    def add_leq(self, other):
        max_length = max(self.binary_length, other.binary_length)
        min_length = min(self.binary_length, other.binary_length)
        remain = max_length - min_length
        self_all = self.all()
        other_all = other.all()
        constraints = []
        if remain == 0:
            pass
        elif self.binary_length == min_length:
            other_all = other[remain:]
        elif other.binary_length == min_length:
            self_all = self[remain:]
            constraints.append(Not(Or(self[:remain])))
        
        lts = [And(Not(self_all[0]), other_all[0])] + [Bool(str(uuid.uuid4())) for _ in range(min_length-1)]
        eqs = [self_all[0] == other_all[0]] + [Bool(str(uuid.uuid4())) for _ in range(min_length-1)]
        for i in range(1,min_length):
            constraints += [
                lts[i] == And(Not(self_all[i]), other_all[i], eqs[i-1]),
                eqs[i] == And(self_all[i] == other_all[i], eqs[i-1]),
                
            ]

        is_smaller = Or(lts + [And(eqs)])
        if self.binary_length == min_length and remain != 0:
            is_smaller = Or(lts + [Or(other[:remain])] + [And(eqs)])
        constraints.append(is_smaller)
        return constraints

    def add_greater_int(self, number:'int'):
        str_num = bin(number)[2:]
        gts = []
        ones = []
        self_all = self.all()
        if len(str_num) > self.binary_length:
            return False
        if len(str_num) < self.binary_length:
            gts += self_all[:self.binary_length - len(str_num)]
            self_all = self_all[self.binary_length - len(str_num):]
        for i in range(len(str_num)):
            if str_num[i] == '1':
                ones.append(i)
        for i in range(0,len(str_num)):
            if str_num[i] == '0':
                constraint = [self_all[i]]
                for one in ones:
                    if one < i:
                        constraint.append(self_all[one])
                constraint = And(constraint)
                gts.append(constraint)
        return Or(gts)
    
    def add_less_int(self, number:'int'):
        str_num = bin(number)[2:]
        lts = []
        zeros = []
        extra = []
        self_all = self.all()
        if len(str_num) > self.binary_length:
            return False
        if len(str_num) < self.binary_length:
            extra.append(Not(Or(self_all[:self.binary_length - len(str_num)])))
            self_all = self_all[self.binary_length - len(str_num):]
        for i in range(len(str_num)):
            if str_num[i] == '0':
                zeros.append(i)
        for i in range(1,len(str_num)):
            if str_num[i] == '1':
                constraint = [Not(self_all[i])]
                for zero in zeros:
                    if zero < i:
                        constraint.append(Not(self_all[zero]))
                constraint = And(constraint)
                lts.append(constraint)
        return And(Or(lts), And(extra))

    def add_geq_int(self, number:'int'):
        return Not(self.add_less_int(number))
            
    def add_leq_int(self, number:'int'):
        return Not(self.add_greater_int(number))

    def add_equal_int(self, number:'int'):
        str_num = bin(number)[2:]
        eqs = []
        self_all = self.all()
        if self.binary_length < len(str_num):
            return False
        if self.binary_length > len(str_num):
            eqs.append(Not(Or(self_all[:self.binary_length - len(str_num)])))
            self_all = self_all[self.binary_length - len(str_num):]

        for i in range(len(str_num)):
            if str_num[i] == '1':
                eqs.append(self_all[i])
            if str_num[i] == '0':
                eqs.append(Not(self_all[i]))

        return And(eqs)

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
        
    def add_int(self, number:'int', multiplier):
        str_num = bin(number)[2:]
        
        if self.binary_length == len(str_num):
            return self.__sum_eqal(str_num, multiplier)
        if self.binary_length > len(str_num):
            return self.__sum_binary_greater(str_num, multiplier)
        return self.__sum_int_greater(str_num, multiplier)

    def __sum_eqal(self, str_num, multiplier):

        new_num = []
        carry = False
        sl = self.binary_length
        nl = len(str_num)
        if str_num[-1] == '1':
            carry = And(self[-1], multiplier)
            new_num.append(Xor(self[-1],multiplier))
        else:
            new_num.append(self[-1])

        for i in range(2,self.binary_length+1):
            if str_num[nl-i] == '1':
                formula = Xor(self[sl-i], multiplier)
                new_num.append(Xor(formula, carry))
                carry = Or(And(formula, carry), And(self[sl-i], multiplier))
            if str_num[nl-i] == '0':
                new_num.append(Xor(self[sl-i], multiplier))
                carry = And(self[sl-i], multiplier)
        new_num.append(carry)
        return SatInteger(binary=list(reversed(new_num)), pre_operations=self.get_constraints())

    def __sum_binary_greater(self, str_num, multiplier):
        self_all = self.all()
        nl = len(str_num)
        self_all_greater = self_all[:self.binary_length - nl]
        self_all = self_all[self.binary_length - nl:]
        sl = len(self_all)
        new_num = []
        carry = False
        if str_num[-1] == '1':
            carry = And(self_all[-1], multiplier)
            new_num.append(Xor(self_all[-1],multiplier))
        else:
            new_num.append(self_all[-1])

        for i in range(2, nl+1):
            if str_num[nl-i] == '1':
                formula = Xor(self_all[sl-i], multiplier)
                new_num.append(Xor(formula, carry))
                carry = Or(And(formula, carry), And(self_all[sl-i], multiplier))
            if str_num[nl-i] == '0':
                new_num.append(Xor(self_all[sl-i], carry))
                carry = And(self_all[sl-i], carry)

        for bool_value in reversed(self_all_greater):
            new_num.append(Xor(bool_value, carry))
            carry = And(bool_value, carry)

        new_num.append(carry)
        return SatInteger(binary=list(reversed(new_num)), pre_operations=self.get_constraints())

    def __sum_int_greater(self, str_num, multiplier):
        
        nl = len(str_num)
        str_num_smaller = str_num[nl - self.binary_length:]
        str_num_greater = str_num[:nl - self.binary_length]
        
        sl = self.binary_length
        nl = sl
        new_num = []
        carry = False
        if str_num_smaller[-1] == '1':
            carry = And(self[-1], multiplier)
            new_num.append(Xor(self[-1],multiplier))
        else:
            new_num.append(self[-1])

        for i in range(2,self.binary_length+1):
            if str_num_smaller[nl-i] == '1':
                formula = Xor(self[sl-i], multiplier)
                new_num.append(Xor(formula, carry))
                carry = Or(And(formula, carry), And(self[sl-i], multiplier))
            if str_num_smaller[nl-i] == '0':
                new_num.append(Xor(self[sl-i], carry))
                carry = And(self[sl-i], carry)

        for bool_value in reversed(str_num_greater):
            if bool_value == '1':
                new_num.append(And(Not(carry),multiplier))
                carry = And(carry,multiplier)
            if bool_value == '0':
                new_num.append(carry)
                carry = False
        new_num.append(carry)

        return SatInteger(binary=list(reversed(new_num)), pre_operations=self.get_constraints())
        
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

