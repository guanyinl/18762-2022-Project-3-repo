import numpy as np

#  You should display whether or not the case is feasible, and if it isn't, display to the user
#  The buses where there are the three largest real and imaginary feasibility injections.
#  You can decide which arguments to pass to this function yourself if you want to change it.

def sort_current_real(v_for_sort, feasibility_sources, bus):
    I_largest = np.zeros(3, dtype=np.float)
    I_largest_bus = np.zeros(3, dtype=np.float)
    for i in range(0, 3):
        for ele in feasibility_sources:
            if abs(v_for_sort[ele.Feas_Ir_node])> abs(I_largest[i]):
                I_largest[i] = v_for_sort[ele.Feas_Ir_node] 
                I_largest_node = ele.Feas_Ir_node
                for ele1 in bus:
                    if ele.Bus == ele1.Bus:
                        I_largest_bus[i] = ele.Bus
        f = int(I_largest_node)
        v_for_sort[f]=0
    return (I_largest, I_largest_bus)

def sort_current_imag(v_for_sort, feasibility_sources, bus):
    I_largest = np.zeros(3, dtype=np.float)
    I_largest_bus = np.zeros(3, dtype=np.float)
    for i in range(0, 3):
        for ele in feasibility_sources:
            if abs(v_for_sort[ele.Feas_Ii_node])> abs(I_largest[i]):
                I_largest[i] = v_for_sort[ele.Feas_Ii_node] 
                I_largest_node = ele.Feas_Ii_node
                for ele1 in bus:
                    if ele.Bus == ele1.Bus:
                        I_largest_bus[i] = ele.Bus
        f = int(I_largest_node)
        v_for_sort[f]=0
    return (I_largest, I_largest_bus)

def process_results_Guan(v, bus, slack, generator, feasibility_sources):
    print('\nBUS Results:')

    #check if the case is infeasible: 
    abs_current_th =1E-5
    infeasible = 0
    for ele in feasibility_sources:
        if abs(v[ele.Feas_Ir_node]) > abs_current_th:
            infeasible =1
        if abs(v[ele.Feas_Ii_node]) > abs_current_th:
            infeasible =1
    
    if infeasible == 1:
        print ('The case is infeasible! Current threshold (abs):',abs_current_th)
    else:
        print ('The case is feasible! Current threshold (abs):',abs_current_th)

    #Sort infeasibility current values on buses.
    v_for_sort = np.copy(v)

    (I_real_largest, I_real_largest_bus) = sort_current_real(v_for_sort, feasibility_sources, bus)
    (I_imag_largest, I_imag_largest_bus) = sort_current_imag(v_for_sort, feasibility_sources, bus)

    print ('The largest 3 real currect values are:', I_real_largest)
    print ('At Bus:', I_real_largest_bus)
    print ('The largest 3 imag currect values are:', I_imag_largest)
    print ('At Bus:', I_imag_largest_bus)
    print ('\n')

    #print all infeasibility current values on buses.
    for ele in feasibility_sources:
        print ('Bus:', ele.Bus, 'Real Infeasibility Current:', v[ele.Feas_Ir_node], 'Imag Infeasibility Current:', v[ele.Feas_Ii_node])
        #print (v[ele.Feas_Ii_node])
        #print (ele.Feas_Ir_node, ele.Feas_Ii_node)
    print ('\n')

    for ele in bus:
        # PQ bus
        if ele.Type == 1:
            Vr = v[ele.node_Vr]
            Vi = v[ele.node_Vi]
            Vmag = np.sqrt(Vr**2 + Vi**2)
            Vth = np.arctan2(Vi, Vr) * 180/np.pi
            print("%d, Vmag: %.3f p.u., Vth: %.3f deg" % (ele.Bus, Vmag, Vth))
        # PV bus
        elif ele.Type == 2:
            Vr = v[ele.node_Vr]
            Vi = v[ele.node_Vi]
            Vmag = np.sqrt(Vr**2 + Vi**2)
            Vth = np.arctan2(Vi, Vr) * 180.0/np.pi
            Qg = v[ele.node_Q]*100
            print("%d: Vmag: %.3f p.u., Vth: %.3f deg, Qg: %.3f MVAr" % (ele.Bus, Vmag, Vth, Qg))
        elif ele.Type == 3:
            Vr = v[ele.node_Vr]
            Vi = v[ele.node_Vi]
            Vmag = np.sqrt(Vr**2 + Vi**2)
            Vth = np.arctan2(Vi, Vr) * 180/np.pi
            Pg, Qg = slack[0].calc_slack_PQ(v)
            print("SLACK: %d, Vmag: %.3f p.u., Vth: %.3f deg, Pg: %.3f MW, Qg: %.3f MVar" % (ele.Bus, Vmag, Vth, Pg*100, Qg*100))
        

