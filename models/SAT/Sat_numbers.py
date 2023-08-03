from z3 import *
import numpy as np


class D2B:
    def __init__(self, decimal_number:'int' = 0, name:'str' = "number", binary:'list' = None, pre_operations:'list' = []) -> None:
        if not binary is None:
            self.binary_length = len(binary)
            self.__representation = binary
            self.name = name
            self.__operations = pre_operations
            self.is_bool = self.binary_length == 1
            return

        self.__operations = pre_operations
        self.binary_length = self.__get_length(decimal_number)
        self.__representation = self.__convert(decimal_number, self.binary_length, name)        
        self.name = name
        self.is_bool = self.binary_length == 1
       

    def __get_length(self, number:'int') -> int:
        return len(bin(number)[2:])

    def __convert(self, number:'int', length:'int', name:'str'):
        num = []
        str_num = bin(number)[2:]
        for i in range(length):
            ni = Bool(f'{name}_{i}')
            num.append(ni)
            if str_num[i] == '1': 
                self.__operations.append(ni)
            else:
                self.__operations.append(Not(ni))
        return np.array(num)

    def get(self, index:'int'):
        return self.__representation[index]

    def all(self):
        return self.__representation


    def get_constraints(self) -> 'list':
        return self.__operations 
    
    def add_greater(self, other):
        min_length = min(self.binary_length, other.binary_length)
        max_length = max(self.binary_length, other.binary_length)

        constraints = [Or([And(self.get(i), Not(other.get(i))) for i in range(min_length)])]
        if min_length == self.binary_length:
            constraints += [Not(other.get(i)) for i in range(min_length, max_length)]
        return constraints

    def add_less(self, other):
        min_length = min(self.binary_length, other.binary_length)
        max_length = max(self.binary_length, other.binary_length)
        
        constraints = [Or([And(Not(self.get(i), other.get(i))) for i in range(self.binary_length)])]
        if max_length == self.binary_length:
            constraints += [Not(self.get(i)) for i in range(min_length, max_length)]
        return constraints
    
    def add_equal(self, other):
        min_length = min(self.binary_length, other.binary_length)
        max_length = max(self.binary_length, other.binary_length)
        
        constraints =  [iff(self.get(i), other.get(i)) for i in range(min_length)]
        return constraints
        if min_length == max_length:
            return constraints
        
        longer = self
        if self.binary_length == min_length:
            longer = other

        constraints += [Not(longer.get(i)) for i in range(min_length, max_length)]
        return constraints

    def add_geq(self, other):
        return [Or(And(self.add_greater(self,other)), And(self.add_equal(self,other)))]
    
    def add_leq(self, other):
        return [Or(And(self.add_less(self,other)), And(self.add_equal(self,other)))]

    def __str__(self):
        return self.name + " " + str(self.__representation)

    def __add__(self, other):
        operations = []
        carry = Bool('carry')
        operations.append(Not(carry))
        min_length = min(self.binary_length, other.binary_length)
        max_length = max(self.binary_length, other.binary_length)
        new_num = []
        for i in range(1, min_length + 1):
            current_num = Bool(f'sum_{i}_{self.name}_{other.name}') 
            operations.append(iff(Xor(self.get(self.binary_length - i), other.get(other.binary_length - i)),current_num))
            final_num = Bool(f'sum_with_carry_{i}_{self.name}_{other.name}')
            operations.append(iff(Xor(current_num, carry), final_num))
            new_carry = Bool(f'carry_{i}_{self.name}_{other.name}')
            operations.append(iff(Or(And(current_num, carry), And(self.get(self.binary_length - i), other.get(other.binary_length - i))),new_carry))
            carry = new_carry
            new_num.append(final_num)

        if min_length != max_length:
             
            max_len_num = self
            if max_length == other.binary_length:
                max_len_num = other
            
            for i in range(min_length + 1, max_length + 1):
                current_num = Bool(f'sum_{i}_{self.name}_{other.name}')
                operations.append(iff(Xor(max_len_num.get(max_len_num.binary_length - i), carry), current_num))

                new_carry = Bool(f'carry_{i}_{self.name}_{other.name}')
                operations.append(iff(And(max_len_num.get(max_len_num.binary_length - i), carry),new_carry)) 
                carry = new_carry
                new_num.append(current_num)
        
        final_num = Bool(f'sum_{max_length + 1}_{self.name}_{other.name}')
        operations.append(iff(carry,final_num))
        new_num.append(final_num)
        return D2B(binary=list(reversed(new_num)), name=f"{self.name} + {other.name}", pre_operations=operations)

    def __mul__(self, other):
        
        not_boolean, boolean = self.__get_operands(self, other)
        new_num = []
        operations = []
        for n in not_boolean.all():
            new_n = Bool(f'mult_{self.name}_{n}_{other}')
            operations.append(iff(And(n,boolean),new_n))
            new_num.append(new_n)
        return D2B(binary=new_num, name=f'{self.name} * {other}', pre_operations=operations)
    
    def __get_operands(self, first, second):
        if type(second) == type(Bool('')):
            return first, second
        if type(first) == type(Bool('')):
            return second, first
        if type(first) == type(D2B(0)) and type(second) == type(D2B(0)):
            if second.is_bool:
                return first, second.get(0)
            if first.is_bool:
                return second, first.get(0)
        if not (self.is_bool or other.is_bool):
            raise("Error: implelemented multiplication only between D2B and booleans")
       
    __rmul__ = __mul__




def iff(left, right):
    return Or(
        And(left, right), 
        And(Not(left),Not(right))
    )


def usage():
    s = Solver()

    seven = D2B(7, "seven")
    three = D2B(3, "three")
    six = D2B(6,"six")
    ten = seven + three

    one = D2B(1,"one")
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

    s.add(seven.add_greater(six))
    s.add(six.add_less(seven))
    _six = D2B(2, "2") + D2B(4, "4")
    s.add(_six.get_constraints())
    s.add(six.add_equal(D2B(6,"6")))
    print(s.check())
    if s.check() == sat:
        m = s.model()
        print("three", [m.evaluate(v) for v in three.all()])
        print("seven", [m.evaluate(v) for v in seven.all()])
        print("res", [m.evaluate(v) for v in res.all()])
        print("res2", [m.evaluate(v) for v in res2.all()])
        print("ten", [m.evaluate(v) for v in ten.all()])
        print("one", [m.evaluate(v) for v in one.all()])
        print("six", [m.evaluate(v) for v in six.all()])
        print("_six", [m.evaluate(v) for v in _six.all()])

usage()
