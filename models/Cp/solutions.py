LAMBDA = 0.1

class CpSolution:
    def __init__(self, solution_str:'str') -> None:
        try:
            self.solved = True
            self.satisfiable = True
            if '=====UNKNOWN=====' in solution_str:
                self.solved = False
                return
            if '=====UNSATISFIABLE=====' in solution_str:
                self.satisfiable = False
                return
            

            if '==========' in solution_str:
                first_split = solution_str.split('==========')
            else:
                first_split = solution_str.split('----------\n%%%mzn-stat')
            total_statistics_string = first_split[1]
            second_split = first_split[0].split('%%%mzn-stat-end')
            all_solutions_string = second_split[1]
            self.parse_statistics(total_statistics_string)
            self.parse_solutions(all_solutions_string)
        except:
            self.solved = False
            self.init_time = 0
            self.solve_time = 0
            self.total_time = 0
            self.all_statistics = []
            self.solutions = None
            self.last_solution = None
            print(solution_str)
            print('error')
        #self.parse_flat_statistics(second_split[0])
    
    def is_solved(self, timeout):
        return self.solved and self.satisfiable and abs(self.total_time - timeout) > LAMBDA

    def parse_statistics(self, stat_str:'str'):
        all_stat = stat_str.split('%%%mzn-stat: ')
        self.init_time = [stat.split('=')[1] for stat in all_stat if 'initTime' in stat ]
        self.init_time = float(self.init_time[0]) if len(self.init_time) > 0 else 0
        self.solve_time = [stat.split('=')[1] for stat in all_stat if 'solveTime' in stat ]
        self.solve_time = float(self.solve_time[0]) if len(self.solve_time) > 0 else 300000
        self.total_time = self.init_time + self.solve_time
        self.all_statistics = all_stat

    def parse_solutions(self, solutions_str:'str'):
        all_solutions = solutions_str.split('----------')
        self.solutions = []
        for solution in all_solutions:
            parsed_solution = solution.replace('\n','')
            if parsed_solution != '':
                sol = {}
                sol_arr = parsed_solution.split(';')
                for el in sol_arr:
                    c = el.replace(" ","")
                    components = c.split("=")
                    if components[0] != '':
                        sol[components[0]] = components[1]
                self.solutions.append(sol)
        self.all_solutions_str = all_solutions
        self.last_solution = self.solutions[-1]
        self.n_solutions = len(self.solutions)

    def parserfn(sol):
        sol = sol.replace("----------","").replace("==========","").replace("\n","")
        sol_arr = sol.split(';')
        elements = {}
        for el in sol_arr:
            c = el.replace(" ","")
            components = c.split("=")
            if components[0] != '':
                elements[components[0]] = components[1]

        return elements

    def print(self, jt:'bool', v:'bool', timeout:'int' = 300000):
        if not self.solved:
            print("solution not found")
            return
        if not self.satisfiable:
            print("instance unsatisfiable")
            return
        if abs(self.total_time - timeout) < LAMBDA:
            print("optimal solution not found")
        
        if v:
            print("solution = ")
            for key in self.last_solution.keys():
                print(key, " = ", self.last_solution[key])
            
            print("------------------------------------------------------------")
        if v or jt:
            print("solution statistics =")
            print("init time = ", self.init_time)
            print("solve time = ", self.solve_time)
            print("total time = ", self.total_time)
            print("number of solutions = ", self.n_solutions)

    
