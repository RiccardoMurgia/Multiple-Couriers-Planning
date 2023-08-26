LAMBDA = 0.1


class CpSolution:

    def __init__(self, info: 'dict') -> None:
        self.all_statistics = None
        self.last_solution = None
        self.solved = True
        self.satisfiable = True
        self.found_optimal_solution = False
        self.n_solutions = None
        self.init_time = 0
        self.solve_time = 0
        self.total_time = 0
        self.result = {}

        try:

            solutions = info['solutions']
            statistics = info['statistics']

            status = info['states'][0].get('status', {})

            if len(solutions) != 0:
                self.parse_statistics(statistics)
                self.parse_solutions(solutions)

            if status == 'OPTIMAL_SOLUTION':
                self.found_optimal_solution = True
            if status == 'UNKNOWN':
                self.solved = False
                return
            if status == "UNSATISFIABLE":
                self.satisfiable = False
                return

            self.result['time'] = self.solve_time
            self.result['optimal'] = self.found_optimal_solution
            self.result['obj'] = self.last_solution['max_distance']
            self.result['sol'] = self.last_solution['courier_route']

        except Exception as e:
            print(e)
            self.solved = False
            self.all_statistics = []
            self.solutions = None
            print('Solution Not Found')

    def is_solved(self, timeout: int = 300000) -> bool:
        return self.solved and self.satisfiable and abs(self.solve_time - timeout) < LAMBDA

    def parse_statistics(self, statistics: 'dict') -> None:
        self.n_solutions = statistics[-1]['statistics']['nSolutions']
        self.init_time = statistics[-2]['statistics']['initTime']
        self.solve_time = statistics[-2]['statistics']['solveTime']
        self.total_time = self.init_time + self.solve_time
        self.all_statistics = statistics

    def parse_solutions(self, all_solutions: 'dict') -> None:
        self.solutions = all_solutions
        self.last_solution = self.solutions[-1]
        self.n_solutions = len(self.solutions)

    def get_result(self) -> dict:
        return self.result

    def print(self, jt: 'bool', v: 'bool', timeout: 'int' = 300000) -> None:
        if not self.solved:
            print("Solution not found")
            return None
        if not self.satisfiable:
            print("Instance unsatisfiable")
            return None
        if abs(self.solve_time - timeout) < LAMBDA or not self.found_optimal_solution:
            print("Optimal solution not found")
        elif self.found_optimal_solution:
            print('Optimal solution found')

        if v or jt:
            print("-------------------------------------------------")
            print("SOLUTION STATISTICS :")
            print("- Solve time = ", self.solve_time)
            print("- Number of solutions = ", self.n_solutions)
            if self.found_optimal_solution:
                print('- Optimal Solution:', self.last_solution)
            else:
                print('- Solution', self.last_solution)
