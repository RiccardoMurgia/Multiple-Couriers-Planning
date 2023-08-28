LAMBDA = 0.1


class CpSolution:

    def __init__(self, info: 'dict') -> None:
        self.__all_statistics = None
        self.__last_solution = None
        self.__solved = True
        self.__satisfiable = True
        self.__found_optimal_solution = False
        self.__n_solutions = None
        self.__init_time = 0
        self.__solve_time = 0
        self.__total_time = 0
        self.__result = {}

        try:

            solutions = info['solutions']
            statistics = info['statistics']

            status = info['states'][0].get('status', {})

            if len(solutions) != 0:
                self.parse_statistics(statistics)
                self.parse_solutions(solutions)

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

        except Exception as e:
            self.__solved = False
            self.__all_statistics = []
            self.solutions = None
            print('Solution Not Found, Exception:', e)

    def is_solved(self, timeout: int = 300000) -> bool:
        return self.__solved and self.__satisfiable and abs(self.__solve_time - timeout) < LAMBDA

    def parse_statistics(self, statistics: 'dict') -> None:
        self.__n_solutions = statistics[-1]['statistics']['nSolutions']
        self.__init_time = statistics[-2]['statistics']['initTime']
        self.__solve_time = statistics[-2]['statistics']['solveTime']
        self.__total_time = self.__init_time + self.__solve_time
        self.__all_statistics = statistics

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
