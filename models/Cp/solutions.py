LAMBDA = 0.1


class CpSolution:

    def __init__(self, info: 'dict') -> None:
        self.__last_solution = None
        self.__solved = True
        self.__satisfiable = True
        self.__found_optimal_solution = False
        self.__n_solutions = None
        self.__solve_time = 0
        self.__result = {}


        solutions = info['solutions']
        statistics = info['statistics']

        if len(solutions) != 0:
            self.parse_statistics(statistics)
            self.parse_solutions(solutions)
        status = self.get_status(info['states'], len(solutions) > 0, int(self.__solve_time) >= 299000)
        if status == 'OPTIMAL_SOLUTION':
            self.__found_optimal_solution = True
        if status == 'UNKNOWN':
            self.__solved = False
            return
        if status == "UNSATISFIABLE":
            self.__satisfiable = False
            return

        self.__result['time'] = self.__solve_time
        self.__result['optimal'] = self.__found_optimal_solution
        self.__result['obj'] = self.__last_solution['max_distance']
        self.__result['sol'] = self.__last_solution['courier_route']


    def get_status(self, states, has_solutions, has_timeouted):
        if len(states) > 0:
            return states[0]['status']
        if not has_solutions and has_timeouted:
            return 'UNKNOWN'
        if not has_solutions and not has_timeouted:
            return "UNSATISFIABLE"
        if has_solutions and not has_timeouted:
            return 'OPTIMAL_SOLUTION'

    def is_solved(self, timeout: int = 300000) -> bool:
        return self.__solved and self.__satisfiable and abs(self.__solve_time - timeout) < LAMBDA

    def parse_statistics(self, statistics: 'dict') -> None:
        try:
            self.__n_solutions = statistics[-1]['statistics']['nSolutions']
            self.__solve_time = statistics[-2]['statistics']['solveTime']
        except:
            try:
                self.__n_solutions = statistics[-2]['statistics']['nSolutions']
                self.__solve_time = statistics[-1]['statistics']['solveTime']
            except:
                self.__n_solutions = 0
                self.__solve_time = 300

    def parse_solutions(self, all_solutions: 'dict') -> None:
        self.solutions = all_solutions
        self.__last_solution = self.solutions[-1]
        self.__n_solutions = len(self.solutions)

    def get_result(self) -> dict:
        return self.__result

    def print(self, jt: 'bool', v: 'bool', timeout: 'int' = 300000) -> None:
        if not self.__solved:
            print("Solution not found")
            return None
        if not self.__satisfiable:
            print("Instance unsatisfiable")
            return None
        if abs(self.__solve_time - timeout) < LAMBDA or not self.__found_optimal_solution:
            print("Optimal solution not found")
        elif self.__found_optimal_solution:
            print('Optimal solution found')

        if v or jt:
            print("-------------------------------------------------")
            print("SOLUTION STATISTICS :")
            print("- Solve time = ", self.__solve_time)
            print("- Number of solutions = ", self.__n_solutions)
            if self.__found_optimal_solution:
                print('- Optimal Solution:', self.__last_solution)
            else:
                print('- Solution', self.__last_solution)
