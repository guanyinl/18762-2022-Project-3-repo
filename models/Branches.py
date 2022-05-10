from __future__ import division
from itertools import count
from scripts.stamp_helpers import *
from models.Buses import Buses

class Branches:
    _ids = count(0)

    def __init__(self,
                 from_bus,
                 to_bus,
                 r,
                 x,
                 b,
                 status,
                 rateA,
                 rateB,
                 rateC):
        """Initialize a branch in the power grid.

        Args:
            from_bus (int): the bus number at the sending end of the branch.
            to_bus (int): the bus number at the receiving end of the branch.
            r (float): the branch resistance
            x (float): the branch reactance
            b (float): the branch susceptance
            status (bool): indicates if the branch is online or offline
            rateA (float): The 1st rating of the line.
            rateB (float): The 2nd rating of the line
            rateC (float): The 3rd rating of the line.
        """
        self.from_bus = from_bus
        self.to_bus = to_bus
        self.r = r
        self.x = x
        self.b = b
        self.status = bool(status)
        self.rateA = rateA
        self.rateB = rateB
        self.rateC = rateC

        # Set minimum x:
        if abs(self.x) < 1e-6:
            if self.x < 0:
                self.x = -1e-6
            else:
                self.x = 1e-6

        # convert to G and B
        self.G_pu = self.r/(self.r**2+self.x**2)
        self.B_pu= -self.x/(self.r**2+self.x**2)

        self.id = self._ids.__next__()

    def assign_indexes(self, bus):
        self.Vr_from_node = bus[Buses.bus_key_[self.from_bus]].node_Vr
        self.Vi_from_node = bus[Buses.bus_key_[self.from_bus]].node_Vi
        self.Vr_to_node = bus[Buses.bus_key_[self.to_bus]].node_Vr
        self.Vi_to_node = bus[Buses.bus_key_[self.to_bus]].node_Vi

        #Add for dual variables
        self.Vr_from_node_lambda = bus[Buses.bus_key_[self.from_bus]].lambda_Vr
        self.Vi_from_node_lambda = bus[Buses.bus_key_[self.from_bus]].lambda_Vi
        self.Vr_to_node_lambda = bus[Buses.bus_key_[self.to_bus]].lambda_Vr
        self.Vi_to_node_lambda = bus[Buses.bus_key_[self.to_bus]].lambda_Vi


    def stamp(self, V, Ylin_val, Ylin_row, Ylin_col, Jlin_val, Jlin_row, idx_Y, idx_J):
        #print ('self.state = ',self.status )
        if not self.status: #!!!!!!!!!!!!!!why do we need self.state? in case there is no branch?
            return (idx_Y, idx_J)
        # Line Bs
        idx_Y = stampY(self.Vr_from_node, self.Vi_from_node, -self.B_pu, Ylin_val, Ylin_row, Ylin_col, idx_Y)
        idx_Y = stampY(self.Vr_from_node, self.Vi_to_node, self.B_pu, Ylin_val, Ylin_row, Ylin_col, idx_Y)
        idx_Y = stampY(self.Vi_from_node, self.Vr_from_node, self.B_pu, Ylin_val, Ylin_row, Ylin_col, idx_Y)
        idx_Y = stampY(self.Vi_from_node, self.Vr_to_node, -self.B_pu, Ylin_val, Ylin_row, Ylin_col, idx_Y)
        idx_Y = stampY(self.Vr_to_node, self.Vi_to_node, -self.B_pu, Ylin_val, Ylin_row, Ylin_col, idx_Y)
        idx_Y = stampY(self.Vr_to_node, self.Vi_from_node, self.B_pu, Ylin_val, Ylin_row, Ylin_col, idx_Y)
        idx_Y = stampY(self.Vi_to_node, self.Vr_to_node, self.B_pu, Ylin_val, Ylin_row, Ylin_col, idx_Y)
        idx_Y = stampY(self.Vi_to_node, self.Vr_from_node, -self.B_pu, Ylin_val, Ylin_row, Ylin_col, idx_Y)

        # Line Shunts
        idx_Y = stampY(self.Vr_from_node, self.Vi_from_node, -self.b/2, Ylin_val, Ylin_row, Ylin_col, idx_Y)
        idx_Y = stampY(self.Vi_from_node, self.Vr_from_node, self.b/2, Ylin_val, Ylin_row, Ylin_col, idx_Y)
        idx_Y = stampY(self.Vr_to_node, self.Vi_to_node, -self.b/2, Ylin_val, Ylin_row, Ylin_col, idx_Y)
        idx_Y = stampY(self.Vi_to_node, self.Vr_to_node, self.b/2, Ylin_val, Ylin_row, Ylin_col, idx_Y)

        if self.r == 0:
            return (idx_Y, idx_J)

        # Line Gs
        idx_Y = stampY(self.Vr_from_node, self.Vr_from_node, self.G_pu, Ylin_val, Ylin_row, Ylin_col, idx_Y)
        idx_Y = stampY(self.Vi_from_node, self.Vi_from_node, self.G_pu, Ylin_val, Ylin_row, Ylin_col, idx_Y)
        idx_Y = stampY(self.Vr_to_node, self.Vr_to_node, self.G_pu, Ylin_val, Ylin_row, Ylin_col, idx_Y)
        idx_Y = stampY(self.Vi_to_node, self.Vi_to_node, self.G_pu, Ylin_val, Ylin_row, Ylin_col, idx_Y)
        idx_Y = stampY(self.Vr_from_node, self.Vr_to_node, -self.G_pu, Ylin_val, Ylin_row, Ylin_col, idx_Y)
        idx_Y = stampY(self.Vi_from_node, self.Vi_to_node, -self.G_pu, Ylin_val, Ylin_row, Ylin_col, idx_Y)
        idx_Y = stampY(self.Vr_to_node, self.Vr_from_node, -self.G_pu, Ylin_val, Ylin_row, Ylin_col, idx_Y)
        idx_Y = stampY(self.Vi_to_node, self.Vi_from_node, -self.G_pu, Ylin_val, Ylin_row, Ylin_col, idx_Y)
    
        return (idx_Y, idx_J)

    def stamp_dual(self, V, Ydulin_val, Ydulin_row, Ydulin_col, Jdulin_val, Jdulin_row, idx_Y, idx_J):
        # You need to implement this.
        
        # Line Bs
        idx_Y = stampY(self.Vr_from_node_lambda, self.Vi_from_node_lambda, -self.B_pu*(-1), Ydulin_val, Ydulin_row, Ydulin_col, idx_Y)
        idx_Y = stampY(self.Vr_from_node_lambda, self.Vi_to_node_lambda, self.B_pu*(-1), Ydulin_val, Ydulin_row, Ydulin_col, idx_Y)
        idx_Y = stampY(self.Vi_from_node_lambda, self.Vr_from_node_lambda, self.B_pu*(-1), Ydulin_val, Ydulin_row, Ydulin_col, idx_Y)
        idx_Y = stampY(self.Vi_from_node_lambda, self.Vr_to_node_lambda, -self.B_pu*(-1), Ydulin_val, Ydulin_row, Ydulin_col, idx_Y)
        idx_Y = stampY(self.Vr_to_node_lambda, self.Vi_to_node_lambda, -self.B_pu*(-1), Ydulin_val, Ydulin_row, Ydulin_col, idx_Y)
        idx_Y = stampY(self.Vr_to_node_lambda, self.Vi_from_node_lambda, self.B_pu*(-1), Ydulin_val, Ydulin_row, Ydulin_col, idx_Y)
        idx_Y = stampY(self.Vi_to_node_lambda, self.Vr_to_node_lambda, self.B_pu*(-1), Ydulin_val, Ydulin_row, Ydulin_col, idx_Y)
        idx_Y = stampY(self.Vi_to_node_lambda, self.Vr_from_node_lambda, -self.B_pu*(-1), Ydulin_val, Ydulin_row, Ydulin_col, idx_Y)

        # Line Shunts
        idx_Y = stampY(self.Vr_from_node_lambda, self.Vi_from_node_lambda, -self.b/2*(-1), Ydulin_val, Ydulin_row, Ydulin_col, idx_Y)
        idx_Y = stampY(self.Vi_from_node_lambda, self.Vr_from_node_lambda, self.b/2*(-1), Ydulin_val, Ydulin_row, Ydulin_col, idx_Y)
        idx_Y = stampY(self.Vr_to_node_lambda, self.Vi_to_node_lambda, -self.b/2*(-1), Ydulin_val, Ydulin_row, Ydulin_col, idx_Y)
        idx_Y = stampY(self.Vi_to_node_lambda, self.Vr_to_node_lambda, self.b/2*(-1), Ydulin_val, Ydulin_row, Ydulin_col, idx_Y)

        if self.r == 0:#no r == 0 in the 4-bus case
            return (idx_Y, idx_J)

        # Line Gs
        idx_Y = stampY(self.Vr_from_node_lambda, self.Vr_from_node_lambda, self.G_pu, Ydulin_val, Ydulin_row, Ydulin_col, idx_Y)
        idx_Y = stampY(self.Vi_from_node_lambda, self.Vi_from_node_lambda, self.G_pu, Ydulin_val, Ydulin_row, Ydulin_col, idx_Y)
        idx_Y = stampY(self.Vr_to_node_lambda, self.Vr_to_node_lambda, self.G_pu, Ydulin_val, Ydulin_row, Ydulin_col, idx_Y)
        idx_Y = stampY(self.Vi_to_node_lambda, self.Vi_to_node_lambda, self.G_pu, Ydulin_val, Ydulin_row, Ydulin_col, idx_Y)
        idx_Y = stampY(self.Vr_from_node_lambda, self.Vr_to_node_lambda, -self.G_pu, Ydulin_val, Ydulin_row, Ydulin_col, idx_Y)
        idx_Y = stampY(self.Vi_from_node_lambda, self.Vi_to_node_lambda, -self.G_pu, Ydulin_val, Ydulin_row, Ydulin_col, idx_Y)
        idx_Y = stampY(self.Vr_to_node_lambda, self.Vr_from_node_lambda, -self.G_pu, Ydulin_val, Ydulin_row, Ydulin_col, idx_Y)
        idx_Y = stampY(self.Vi_to_node_lambda, self.Vi_from_node_lambda, -self.G_pu, Ydulin_val, Ydulin_row, Ydulin_col, idx_Y)

        return (idx_Y, idx_J)

    def calc_residuals(self, resid, V):
        Vr_from = V[self.Vr_from_node]
        Vr_to = V[self.Vr_to_node]
        Vi_from = V[self.Vi_from_node]
        Vi_to = V[self.Vi_to_node]
        
        resid[self.Vr_from_node] += (Vr_from-Vr_to)*self.G_pu - (Vi_from-Vi_to)*self.B_pu - Vi_from*self.b/2
        resid[self.Vr_to_node] += (Vr_to-Vr_from)*self.G_pu - (Vi_to-Vi_from)*self.B_pu - Vi_to*self.b/2
        resid[self.Vi_from_node] += (Vr_from-Vr_to)*self.B_pu + (Vi_from-Vi_to)*self.G_pu + Vr_from*self.b/2
        resid[self.Vi_to_node] += (Vr_to-Vr_from)*self.B_pu + (Vi_to-Vi_from)*self.G_pu + Vr_to*self.b/2
