from __future__ import division
import numpy as np
from models.Buses import Buses
from models.Buses import Buses
from scripts.stamp_helpers import *
from models.global_vars import global_vars

class FeasibilitySource:

    def __init__(self,
                 Bus):
        """Initialize slack bus in the power grid.

        Args:
            Bus (int): the bus number corresponding to this set of feasibility currents
        """
        self.Bus = Bus
        
        self.Ir_init = 0
        self.Ii_init = 0
        

    def assign_nodes(self,bus):
        """Assign the additional slack bus nodes for a slack bus.
        Args:
            You decide :)
        Returns:
            None
        """
        # TODO: You decide how to implement variables for the feasibility injections
        
        # Guan: Each bus needs 1 slack bus. and this contributes to bus*2 nodes. 
        self.Feas_Ir_node = Buses._node_index.__next__()
        self.Feas_Ii_node = Buses._node_index.__next__()

        #feasible current does not extend the matrix, but it this to know the primal Vr and Vi node to stamp.
        self.Vr_node = bus[Buses.bus_key_[self.Bus]].node_Vr
        self.Vi_node = bus[Buses.bus_key_[self.Bus]].node_Vi

        #feasible current source has no its labmda, this is the lambda where it corresponds to in KCL.
        self.lambda_Vr = bus[Buses.bus_key_[self.Bus]].lambda_Vr
        self.lambda_Vi = bus[Buses.bus_key_[self.Bus]].lambda_Vi

        pass

    def stamp(self, V, Y_val, Y_row, Y_col, J_val, J_row, idx_Y, idx_J):
        # You need to implement this.
        idx_Y = stampY(self.Vr_node, self.Feas_Ir_node, 1, Y_val, Y_row, Y_col, idx_Y)
        idx_Y = stampY(self.Vi_node, self.Feas_Ii_node, 1, Y_val, Y_row, Y_col, idx_Y)

        return (idx_Y, idx_J)

    def stamp_dual(self, V, Ydulin_val, Ydulin_row, Ydulin_col, Jdulin_val, Jdulin_row, idx_Y, idx_Jlf):
        # You need to implement this.

        #print ('feasible bus lambda_vr lambda_vi =', self.Bus, self.lambda_Vr, self.lambda_Vi)
        #2Ir and 2Ii
        idx_Y = stampY(self.Feas_Ir_node, self.Feas_Ir_node, 2, Ydulin_val, Ydulin_row, Ydulin_col, idx_Y)
        idx_Y = stampY(self.Feas_Ii_node, self.Feas_Ii_node, 2, Ydulin_val, Ydulin_row, Ydulin_col, idx_Y)
        
        # correspong KCL lambda Vr and lambda Vi
        idx_Y = stampY(self.Feas_Ir_node, self.lambda_Vr, 1, Ydulin_val, Ydulin_row, Ydulin_col, idx_Y)
        idx_Y = stampY(self.Feas_Ii_node, self.lambda_Vi, 1, Ydulin_val, Ydulin_row, Ydulin_col, idx_Y)
        

        return (idx_Y, idx_Jlf)
