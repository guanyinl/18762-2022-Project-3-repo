from __future__ import division
import numpy as np
from models.Buses import Buses
from models.Buses import Buses
from scripts.stamp_helpers import *
from models.global_vars import global_vars

class Slack:

    def __init__(self,
                 Bus,
                 Vset,
                 ang,
                 Pinit,
                 Qinit):
        """Initialize slack bus in the power grid.

        Args:
            Bus (int): the bus number corresponding to the slack bus.
            Vset (float): the voltage setpoint that the slack bus must remain fixed at.
            ang (float): the slack bus voltage angle that it remains fixed at.
            Pinit (float): the initial active power that the slack bus is supplying
            Qinit (float): the initial reactive power that the slack bus is supplying
        """
        self.Bus = Bus
        self.Vset = Vset
        self.ang = ang
        self.Pinit_MVA = Pinit
        self.Qinit_MVA = Qinit
        self.Pinit = Pinit/global_vars.base_MVA
        self.Qinit = Qinit/global_vars.base_MVA
        
        # initialize
        self.Vr_set = Vset*np.cos(ang*np.pi/180)
        self.Vi_set = Vset*np.sin(ang*np.pi/180)

        self.Ir_init = (-self.Vr_set*self.Pinit - self.Vi_set*self.Qinit)/(Vset**2)
        self.Ii_init = (-self.Vi_set*self.Pinit + self.Vi_set*self.Qinit)/(Vset**2)

        # initialize some dual nodes
        # TODO - you can name them as you please


    def assign_nodes(self, bus):
        """Assign the additional slack bus nodes for a slack bus.
        Returns:
            None
        """
        # HINT: you might want to change this
        self.Vr_node = bus[Buses.bus_key_[self.Bus]].node_Vr
        self.Vi_node = bus[Buses.bus_key_[self.Bus]].node_Vi
        self.Slack_Ir_node = Buses._node_index.__next__()
        self.Slack_Ii_node = Buses._node_index.__next__()

    def assign_dual_nodes(self, bus):
        # You need to implement this
        # Guan: Each slack current needs one lambda  
        self.Slack_lambda_Ir_node = Buses._node_index.__next__()
        self.Slack_lambda_Ii_node = Buses._node_index.__next__()
        self.lambda_Vr = bus[Buses.bus_key_[self.Bus]].lambda_Vr
        self.lambda_Vi = bus[Buses.bus_key_[self.Bus]].lambda_Vi

        pass

    def stamp(self, V, Y_val, Y_row, Y_col, J_val, J_row, idx_Y, idx_J):
        # slack currents leaving their nodes
        idx_Y = stampY(self.Vr_node, self.Slack_Ir_node, 1, Y_val, Y_row, Y_col, idx_Y)
        #print (self.Vr_node, self.Slack_Ir_node)
        idx_Y = stampY(self.Vi_node, self.Slack_Ii_node, 1, Y_val, Y_row, Y_col, idx_Y)
        #print (self.Vi_node, self.Slack_Ii_node)
        # enforce slack constraints
        idx_Y = stampY(self.Slack_Ir_node, self.Vr_node, 1, Y_val, Y_row, Y_col, idx_Y)
        #print (self.Slack_Ir_node, self.Vr_node)
        idx_J = stampJ(self.Slack_Ir_node, self.Vr_set, J_val, J_row, idx_J)
        
        idx_Y = stampY(self.Slack_Ii_node, self.Vi_node, 1, Y_val, Y_row, Y_col, idx_Y)
        idx_J = stampJ(self.Slack_Ii_node, self.Vi_set, J_val, J_row, idx_J)


        return (idx_Y, idx_J)

    def stamp_dual(self, V, Ydulin_val, Ydulin_row, Ydulin_col, Jdulin_val, Jdulin_row, idx_Y, idx_Jlf):
        # You need to implement this.

        idx_Y = stampY(self.lambda_Vr, self.Slack_lambda_Ir_node, 1, Ydulin_val, Ydulin_row, Ydulin_col, idx_Y)
        idx_Y = stampY(self.lambda_Vi, self.Slack_lambda_Ii_node, 1, Ydulin_val, Ydulin_row, Ydulin_col, idx_Y)
        
        #for slack lambda Ir Ii rows are to be non-zero
        idx_Y = stampY(self.Slack_lambda_Ir_node, self.lambda_Vr, 1, Ydulin_val, Ydulin_row, Ydulin_col, idx_Y)
        idx_Y = stampY(self.Slack_lambda_Ii_node, self.lambda_Vi, 1, Ydulin_val, Ydulin_row, Ydulin_col, idx_Y)
        idx_Jlf = stampJ(self.Slack_lambda_Ir_node, 0, Jdulin_val, Jdulin_row, idx_Jlf)
        idx_Jlf = stampJ(self.Slack_lambda_Ii_node, 0, Jdulin_val, Jdulin_row, idx_Jlf)

        #idx_Y = stampY(self.Slack_lambda_Ir_node, self.Vr_node, 1, Ydulin_val, Ydulin_row, Ydulin_col, idx_Y)
        #idx_Y = stampY(self.Slack_lambda_Ii_node, self.Vi_node, 1, Ydulin_val, Ydulin_row, Ydulin_col, idx_Y)
        #idx_Jlf = stampJ(self.Slack_lambda_Ir_node, self.Vr_set, Jdulin_val, Jdulin_row, idx_Jlf)
        #idx_Jlf = stampJ(self.Slack_lambda_Ii_node, self.Vi_set, Jdulin_val, Jdulin_row, idx_Jlf)

        return(idx_Y, idx_Jlf)

    def calc_slack_PQ(self, V_sol):
        Ir = V_sol[self.Slack_Ir_node]
        Ii = V_sol[self.Slack_Ii_node]
        Vr = self.Vr_set
        Vi = self.Vi_set
        S = (Vr + 1j*Vi)*(Ir - 1j*Ii)
        P = -np.real(S)
        Q = np.imag(S)
        return (P, Q)

    def calc_residuals(self, resid, V):
        resid[self.Vr_node] += V[self.Slack_Ir_node]
        resid[self.Vi_node] += V[self.Slack_Ii_node]
        resid[self.Slack_Ir_node] += V[self.Vr_node] - self.Vr_set
        resid[self.Slack_Ii_node] += V[self.Vi_node] - self.Vi_set