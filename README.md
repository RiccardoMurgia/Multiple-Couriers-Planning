# Multiple-Couriers-Planning
This project serves as the examination assessment for the Combinatorial and Decision-Making course at the University of Bologna.  
For a comprehensive understanding of the problem and its details, please refer to the problem description provided in the accompanying 'problem_description.pdf' file

If you have any questions, please feel free to contact us  
- [Alessandro Pasi](mailto:alessandro.pasi8@studio.unibo.it)
- [Alessio Pellegrino](mailto:alessio.pellegrino@studio.unibo.it)
- [Lorenzo Massa](mailto:orenzo.massa6@studio.unibo.it)
- [Riccardo Murgia](mailto:iccardo.murgia2@studio.unibo.it)

To execute the project run the following command in terminal: 
```bash
python Mcp.py -c config.mcp
```

To execute the `Mcp.py` file, use the configurations specified in the `config.mcp` file. The configuration file contains the following fields:

1. **instances_path:** The directory path where instance files are stored.

2. **usage_mode:** This field specifies the instances to run and the templates to use. It includes the following subfields:

   - **instances_to_solve:** A list that should contain the names of the instances you wish to run(e.g \["inst00.dat"\]), or you can use the string "_all_instances_" to run all instances.

   - **models_to_use:** A list containing the names of the models you want to utilize. Available models include "mip," "cp," "sat," and "smt."

3. **cp:** Contains configurations for running the Constraint Programming (CP) model. This section includes:

   - **solvers:** A list of solver names you want to use. Possible values are: every minizinc solver installed by default and or-tools. Adding the substring "-no-sym" to the solver name will execute the solver without the symetry breaking constraint(e.g "gecode-no-sym")

   - **timeout:** The time limit expressed in milliseconds.

   - **processes:** The number of threads to use when executing the CP model.

    - **export_folder:** The directory where the built model for are to be exported.

4. **sat:** Contains configurations for running the Boolean Satisfiability Problem (SAT) model. This section includes:
   - **library:** A list of available library versions for the SAT model (z3 library only ).

   - **timeout:** The time limit expressed in milliseconds.

   - **solver:** A list of solvers compatible with the SAT model (z3 default solver only).

   - **processes:** The number of threads for running the SAT model.

5. **mip:** Contains configurations for running the Mixed-Integer Programming (MIP) model. This section includes:

   - **library:** A list of available library versions for the MIP model.

   - **mip_solvers:** A list of solvers compatible with the MIP model implemented via the "mip" library (CBC solver only).

   - **ortools_solvers:** A list of solvers compatible with the ortools version of the MIP model, including CBC_MIXED_INTEGER_PROGRAMMING, SAT_INTEGER_PROGRAMMING, and SCIP_MIXED_INTEGER_PROGRAMMING.

   - **pulp_solvers:** A list of solvers compatible with the MIP model implemented via the "pulp" library (CBC solver only).

   - **timeout:** The time limit expressed in seconds.

   - **processes:** The number of threads for running the MIP model.

    - **export_folder:** The directory where the built model for are to be exported.

6. **smt:** Contains configurations for running the Satisfiability Modulo Theories (SMT) model.
   - **library:** A list of available library versions for the SMT model(z3 library only).

   - **solver:** A list of solvers compatible with the SMT model (z3 default solver only).

   - **timeout:** The time limit expressed in seconds.
   
   - **processes:** The number of threads for running the SMT model.

   - **export_folder:** The directory where the built model for  are to be exported.


Feel free to customize the configurations in the `config.mcp` file to suit your specific needs and preferences.
