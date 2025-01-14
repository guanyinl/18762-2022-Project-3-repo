from scripts.SolveFeasibility import solve_feasibility
from models.global_vars import global_vars

# path to the grid network RAW file
casename = 'testcases/GS-4_stressed.RAW' 
# the settings for the solver
settings = {
    "Tolerance": 1E-07,
    "Max Iters": 1000,
    "Limiting":  False  #Guan-Ying: Voltage limiting needs to be turned on to solve the 14_stressed2_fixed case. 
}

# run the solver
solve_feasibility(casename, settings)