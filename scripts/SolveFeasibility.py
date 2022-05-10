from parsers.parser import parse_raw
from scripts.PowerflowFeasibility import PowerFlowFeasibility
from scripts.process_results import process_results
from scripts.process_results_Guan import process_results_Guan
from scripts.initialize import initialize
from models.Buses import Buses
from models.FeasibilitySource import FeasibilitySource


def solve_feasibility(TESTCASE, SETTINGS):
    """Run the feasibility analysis.

    Args:
        TESTCASE (str): A string with the path to the test case.
        SETTINGS (dict): Contains all the solver settings in a dictionary.

    Returns:
        None
    """
    # TODO: PART 1, STEP 0 - Initialize all the model classes in the models directory (models/) and familiarize
    #  yourself with the parameters of each model. Use the docs/DataFormats.pdf for assistance.

    # # # Parse the Test Case Data # # #
    case_name = TESTCASE
    parsed_data = parse_raw(case_name)

    # # # Assign Parsed Data to Variables # # #
    bus = parsed_data['buses']
    slack = parsed_data['slack']
    generator = parsed_data['generators']
    transformer = parsed_data['xfmrs']
    branch = parsed_data['branches']
    shunt = parsed_data['shunts']
    load = parsed_data['loads']
    
    #understand the circuit
    """
    print ('Understand the circuit:')
    for ele in load:
        print ('load connected to bus= ', ele.Bus)
    for ele in generator:
        print ('gen connected to bus= ', ele.Bus)
    for ele in slack:
        print ('slack connected to bus= ', ele.Bus)
    for ele in shunt:
        print ('shunt connected to bus= ', ele.Bus)
    #for ele in transformer:
    #    print ('trans connected to bus= ', ele.Bus)
    print ('\n')
    """


    # Create some feasibility current sources to use
    # TODO: you need to implement most of the functionality
    #       for this new model
    feasibility_sources = []
    for ele in bus:
        feasibility_sources.append(FeasibilitySource(ele.Bus))
    #Is this the If, Is in V? 

    # # # Solver Settings # # #
    tol = SETTINGS['Tolerance']  # NR solver tolerance
    max_iters = SETTINGS['Max Iters']  # maximum NR iterations
    enable_limiting = SETTINGS['Limiting']  # enable/disable voltage and reactive power limiting

    # # # Assign System Nodes Bus by Bus # # #
    # We can use these nodes to have predetermined node number for every node in our Y matrix and J vector.
    bus_ind = 0
    for ele in bus:
        ele.assign_primal_nodes()
        # TODO: You need to implement this function!
        ele.assign_dual_nodes()
        Buses.bus_key_[ele.Bus] = bus_ind
        bus_ind += 1
    
    # Assign any slack nodes
    for ele in slack:
        ele.assign_nodes(bus)
        # TODO: you need to implement this function!
        ele.assign_dual_nodes(bus)

    # Assign nodes for the feasibility sources
    for ele in feasibility_sources:
        # You might need some arguments for this function
        ele.assign_nodes(bus)

    #check node assignment # If Slack (3) or PQ Bus (1)  
    """
    for ele in bus:
        if ele.Type == 1 or ele.Type == 3:
            print ('PQ and slack bus node Vr Vi: ', ele.node_Vr, ele.node_Vi)
            print ('PQ and slack bus node lambda_r lambda_i: ', ele.lambda_Vr, ele.lambda_Vi)
        elif ele.Type == 2:
            print ('PV bus node Vr Vi Q: ', ele.node_Vr, ele.node_Vi, ele.node_Q)
            print ('PV bus node lambda_r lambda_i lambda_Q: ', ele.lambda_Vr, ele.lambda_Vi, ele.lambda_Q)
    for ele in slack:
        print ('slack current node Ir Ii: ', ele.Slack_Ir_node, ele.Slack_Ii_node)
        print ('slack current node lambda_r lambda_i: ', ele.Slack_lambda_Ir_node, ele.Slack_lambda_Ii_node)
    for ele in feasibility_sources:
        print ('feas node ir ii: ', ele.Feas_Ir_node, ele.Feas_Ii_node)

    print ('\n')
    """

    # set system node indexes for all other devices
    # HINT: in addition to telling each device the Vr and Vi node indices
    # for the bus it's attached to, you might want to save the
    # lambda_r and lambda_i node indices as well...
    for ele in generator:
        ele.assign_indexes(bus)
    for ele in transformer:
        ele.assign_indexes(bus)
    for ele in branch:
        ele.assign_indexes(bus)
    for ele in shunt:
        ele.assign_indexes(bus)
    for ele in load:
        ele.assign_indexes(bus)

    #check device node indexces:
    """
    print ('Check device node indexces')
    for ele in generator:
        print ('gen bus =', ele.Bus, 'generator node Vr Vi: ', ele.Vr_node, ele.Vi_node, 'generator node Qr: ', ele.Q_node, 'generator lambda Vr Vi Q: ', ele.lambda_Vr, ele.lambda_Vi, ele.lambda_Q)   
    for ele in slack:
        print ('slack bus =', ele.Bus, 'slack node Vr Vi: ', ele.Vr_node, ele.Vi_node, 'slack lambda Vr Vi: ', ele.lambda_Vr, ele.lambda_Vi) 
        print ('slack bus =', ele.Bus, 'slack node Ir Ii: ', ele.Slack_Ir_node, ele.Slack_Ii_node, 'slack lambda Ir Ii: ', ele.Slack_lambda_Ir_node, ele.Slack_lambda_Ii_node) 
    
    for ele in branch:
        print ('branch from bus =', ele.from_bus, 'from node Vr Vi: ', ele.Vr_from_node, ele.Vi_from_node, 'from node lambda_Vr lambda_Vi: ', ele.Vr_from_node_lambda, ele.Vi_from_node_lambda)
        print ('branch to bus =', ele.to_bus,'to node Vr Vi: ', ele.Vr_to_node, ele.Vi_to_node, 'to node lambda_Vr lambda_Vi: ', ele.Vr_to_node_lambda, ele.Vi_to_node_lambda)

    #No Shunt for the 4 bus case    
    for ele in shunt:
        print ('shunt bus =', ele.Bus, 'shunt node Vr Vi: ', ele.Vr_node, ele.Vi_node, 'shunt lambda Vr Vi: ', ele.lambda_Vr, ele.lambda_Vi) 
    for ele in load:
        print ('load bus =', ele.Bus, 'load node Vr Vi: ', ele.Vr_node, ele.Vi_node, 'load lambda Vr Vi: ', ele.lambda_Vr, ele.lambda_Vi)
    for ele in feasibility_sources:
        print ('feas Bus =', ele.Bus, 'feas node ir ii: ', ele.Feas_Ir_node, ele.Feas_Ii_node, 'KCL lambda Vr Vi: ', ele.lambda_Vr, ele.lambda_Vi, 'Primal Vr Vi: ', ele.Vr_node, ele.Vi_node)
    for ele in branch:
        print ('branch from bus =', ele.from_bus, 'from node Vr Vi: ', ele.Vr_from_node, ele.Vi_from_node, 'from node lambda_Vr lambda_Vi: ', ele.Vr_from_node_lambda, ele.Vi_from_node_lambda)
        print ('branch to bus =', ele.to_bus,'to node Vr Vi: ', ele.Vr_to_node, ele.Vi_to_node, 'to node lambda_Vr lambda_Vi: ', ele.Vr_to_node_lambda, ele.Vi_to_node_lambda)

    print ('\n')
    """

    # # # Initialize Solution Vector - V and Q values # # #

    # determine the size of the Y matrix by looking at the total number of nodes in the system
    size_Y = Buses._node_index.__next__()
    #print ('size_Y =', size_Y)
    

    # TODO: PART 1, STEP 1 - Complete the function to initialize your solution vector v_init.
    v_init = initialize(size_Y, bus, generator, slack, feasibility_sources, flat_start=False)
    #print ('First_V =', v_init)

    # # # Run Power Flow # # #
    feas_solver = PowerFlowFeasibility(case_name, tol, max_iters, enable_limiting)

    # TODO: PART 1, STEP 2 - Complete the PowerFlowFeasibility class and build your run_feas_analysis function to solve Equivalent
    #  Circuit Formulation powerflow. The function will return a final solution vector v. Remove run_pf and the if
    #  condition once you've finished building your solver.
    run_feas = True
    if run_feas:
        v = feas_solver.run_feas_analysis(v_init, bus, slack, generator, transformer, branch, shunt, load, feasibility_sources, size_Y)
    
    # # # Process Results # # #
    # TODO: PART 1, STEP 3 - Write a process_results function to compute the relevant results.
    #  You should display whether or not the case is feasible, and if it isn't, display to the user
    #  The buses where there are the three largest real and imaginary feasibility injections.
    #  You can decide which arguments to pass to this function yourself if you want to change it.
    #process_results(v, bus, slack, generator)
    
    process_results_Guan(v, bus, slack, generator, feasibility_sources)
