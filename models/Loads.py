from __future__ import division
from itertools import count
from models.Buses import Buses
from scripts.stamp_helpers import *
from models.global_vars import global_vars

class Loads:
    _ids = count(0)

    def __init__(self,
                 Bus,
                 P,
                 Q,
                 IP,
                 IQ,
                 ZP,
                 ZQ,
                 area,
                 status):
        """Initialize an instance of a PQ or ZIP load in the power grid.

        Args:
            Bus (int): the bus where the load is located
            self.P (float): the active power of a constant power (PQ) load.
            Q (float): the reactive power of a constant power (PQ) load.
            IP (float): the active power component of a constant current load.
            IQ (float): the reactive power component of a constant current load.
            ZP (float): the active power component of a constant admittance load.
            ZQ (float): the reactive power component of a constant admittance load.
            area (int): location where the load is assigned to.
            status (bool): indicates if the load is in-service or out-of-service.
        """
        self.Bus = Bus
        self.P_MW = P
        self.Q_MVA = Q
        self.IP_MW = IP
        self.IQ_MVA = IQ
        self.ZP_MW = ZP
        self.ZQ_MVA = ZQ
        self.area = area
        self.status = status
        self.id = Loads._ids.__next__()

        self.P = P/global_vars.base_MVA
        self.Q = Q/global_vars.base_MVA
        self.IP = IP/global_vars.base_MVA
        self.IQ = IQ/global_vars.base_MVA
        self.ZP = ZP/global_vars.base_MVA
        self.ZQ = ZQ/global_vars.base_MVA
    
    def assign_indexes(self, bus):
        for ele in bus:
            if ele.Type == 1:
                # Nodes shared by generators on the same bus
                self.Vr_node = bus[Buses.bus_key_[self.Bus]].node_Vr
                self.Vi_node = bus[Buses.bus_key_[self.Bus]].node_Vi
                # check something about gen_type??

                #lambda shared by loads on the same bus
                self.lambda_Vr = bus[Buses.bus_key_[self.Bus]].lambda_Vr
                self.lambda_Vi = bus[Buses.bus_key_[self.Bus]].lambda_Vi

    
    def stamp(self, V, Y_val, Y_row, Y_col, J_val, J_row, idx_Y, idx_J):
        Vr = V[self.Vr_node]
        Vi = V[self.Vi_node]

        Irg_hist = (self.P*Vr+self.Q*Vi)/(Vr**2+Vi**2)
        dIrldVr = (self.P*(Vi**2-Vr**2) - 2*self.Q*Vr*Vi)/(Vr**2+Vi**2)**2
        dIrldVi = (self.Q*(Vr**2-Vi**2) - 2*self.P*Vr*Vi)/(Vr**2+Vi**2)**2
        Vr_J_stamp = -Irg_hist + dIrldVr*Vr + dIrldVi*Vi
        
        idx_Y = stampY(self.Vr_node, self.Vr_node, dIrldVr, Y_val, Y_row, Y_col, idx_Y)
        idx_Y = stampY(self.Vr_node, self.Vi_node, dIrldVi, Y_val, Y_row, Y_col, idx_Y)
        idx_J = stampJ(self.Vr_node, Vr_J_stamp, J_val, J_row, idx_J)

        Iig_hist = (self.P*Vi-self.Q*Vr)/(Vr**2+Vi**2)
        dIildVi = -dIrldVr
        dIildVr = dIrldVi
        Vi_J_stamp = -Iig_hist + dIildVr*Vr + dIildVi*Vi

        idx_Y = stampY(self.Vi_node, self.Vr_node, dIildVr, Y_val, Y_row, Y_col, idx_Y)
        idx_Y = stampY(self.Vi_node, self.Vi_node, dIildVi, Y_val, Y_row, Y_col, idx_Y)
        idx_J = stampJ(self.Vi_node, Vi_J_stamp, J_val, J_row, idx_J)

        return (idx_Y, idx_J)

    def stamp_dual(self, V, Ydunlin_val, Ydunlin_row, Ydunlin_col, Jdunlin_val, Jdunlin_row, idx_Y, idx_J):
        # You need to implement this.
        Vr = V[self.Vr_node]
        Vi = V[self.Vi_node]
        Lbda_r = V[self.lambda_Vr]
        Lbda_i = V[self.lambda_Vi]
        #print ('Bus =',self.Bus,'Lbda_r =', Lbda_r, 'V_index =', self.lambda_Vr)
        #print ('Bus =',self.Bus,'Lbda_i =', Lbda_i, 'V_index =', self.lambda_Vi)

        #first derivatives for lagrangian
        dIrldVr = (self.P*(Vi**2-Vr**2) - 2*self.Q*Vr*Vi)/(Vr**2+Vi**2)**2   #used
        dIrldVi = (self.Q*(Vr**2-Vi**2) - 2*self.P*Vr*Vi)/(Vr**2+Vi**2)**2   #used
        dIildVi = -dIrldVr   #used
        dIildVr = dIrldVi    #used

        #2nd derivatives for dVrl
        dLrl_dLbda_rl = dIrldVr*(+1)
        dLrl_dLada_il = dIildVr*(+1)
        
        dLrl_dVr_1 = Lbda_r*(self.P*(-1)*(Vr**2+Vi**2)**(-2)*2*(Vr)-((self.P)*(Vr**2+Vi**2)**-2*2*(Vr)+(self.P*Vr+self.Q*Vi)*(-2)*(Vr**2+Vi**2)**(-3)*4*Vr**2+2*(self.P*Vr+self.Q*Vi)*(Vr**2+Vi**2)**(-2)))
        dLrl_dVr_2 = Lbda_i*(self.Q*(Vr**2+Vi**2)**(-2)*2*(Vr)-(-self.Q*(Vr**2+Vi**2)**-2*2*(Vr)+(self.P*Vi-self.Q*Vr)*(-2)*(Vr**2+Vi**2)**(-3)*4*Vr**2+2*(self.P*Vi-self.Q*Vr)*(Vr**2+Vi**2)**(-2)))
        dLrl_dVr = dLrl_dVr_1+dLrl_dVr_2
        #print(dLrl_dVr)

        dLrl_dVi_1 = Lbda_r*(self.P*(-1)*(Vr**2+Vi**2)**(-2)*2*(Vi)-((self.Q)*(Vr**2+Vi**2)**-2*2*(Vr)+(self.P*Vr+self.Q*Vi)*(-2)*(Vr**2+Vi**2)**(-3)*2*Vr*2*Vi))
        dLrl_dVi_2 = Lbda_i*(self.Q*(1)*(Vr**2+Vi**2)**(-2)*2*(Vi)-((self.P)*(Vr**2+Vi**2)**-2*2*(Vr)+(self.P*Vi-self.Q*Vr)*(-2)*(Vr**2+Vi**2)**(-3)*2*Vr*2*Vi))
        dLrl_dVi = dLrl_dVi_1+dLrl_dVi_2
        #print(dLrl_dVi)
        
        idx_Y = stampY(self.lambda_Vr, self.lambda_Vr, dLrl_dLbda_rl, Ydunlin_val, Ydunlin_row, Ydunlin_col, idx_Y)
        idx_Y = stampY(self.lambda_Vr, self.lambda_Vi, dLrl_dLada_il, Ydunlin_val, Ydunlin_row, Ydunlin_col, idx_Y)
        idx_Y = stampY(self.lambda_Vr, self.Vr_node, dLrl_dVr, Ydunlin_val, Ydunlin_row, Ydunlin_col, idx_Y)
        idx_Y = stampY(self.lambda_Vr, self.Vi_node, dLrl_dVi, Ydunlin_val, Ydunlin_row, Ydunlin_col, idx_Y)
        
        Lrl_hist = Lbda_r*dIrldVr*(+1)+Lbda_i*dIildVr*(+1)
        Lrl_J_stamp = -Lrl_hist+Lbda_r*dLrl_dLbda_rl+Lbda_i*dLrl_dLada_il+Vr*dLrl_dVr+Vi*dLrl_dVi

        idx_J = stampJ(self.lambda_Vr, Lrl_J_stamp, Jdunlin_val, Jdunlin_row, idx_J)

        #print ('load i,j =', self.lambda_Vr, self.lambda_Vr, 'dLrl_dLbda_rl', dLrl_dLbda_rl)
        #print ('load i,j =', self.lambda_Vr, self.lambda_Vi, 'dLrl_dLada_il', dLrl_dLada_il)
        #print ('load i,j =', self.lambda_Vr, self.Vr_node, 'dLrl_dVr', dLrl_dVr)
        #print ('load i,j =', self.lambda_Vr, self.Vi_node, 'dLrl_dVi', dLrl_dVi)
        #print ('J[i] =', self.lambda_Vr, Lrl_J_stamp)

        #2nd derivatives for dVil
        dLil_dLbda_rl = dIrldVi*(+1)
        dLil_dLada_il = dIildVi*(+1)

        dLil_dVr_1 = Lbda_r*(self.Q*(-1)*(Vr**2+Vi**2)**(-2)*2*(Vr)-((self.P)*(Vr**2+Vi**2)**-2*2*(Vi)+(self.P*Vr+self.Q*Vi)*(-2)*(Vr**2+Vi**2)**(-3)*2*Vi*2*Vr))
        dLil_dVr_2 = Lbda_i*(self.P*(-1)*(Vr**2+Vi**2)**(-2)*2*(Vr)-((-self.Q)*(Vr**2+Vi**2)**-2*2*(Vi)+(self.P*Vi-self.Q*Vr)*(-2)*(Vr**2+Vi**2)**(-3)*2*Vi*2*Vr))
        dLil_dVr = dLil_dVr_1+dLil_dVr_2
        
        dLil_dVi_1 = Lbda_r*(self.Q*(-1)*(Vr**2+Vi**2)**(-2)*2*(Vi)-((self.Q)*(Vr**2+Vi**2)**-2*2*(Vi)+(self.P*Vr+self.Q*Vi)*(-2)*(Vr**2+Vi**2)**(-3)*4*Vi**2+2*(self.P*Vr+self.Q*Vi)*(Vr**2+Vi**2)**(-2)))
        dLil_dVi_2 = Lbda_i*(self.P*(-1)*(Vr**2+Vi**2)**(-2)*2*(Vi)-((self.P)*(Vr**2+Vi**2)**-2*2*(Vi)+(self.P*Vi-self.Q*Vr)*(-2)*(Vr**2+Vi**2)**(-3)*4*Vi**2+2*(self.P*Vi-self.Q*Vr)*(Vr**2+Vi**2)**(-2)))
        dLil_dVi = dLil_dVi_1+dLil_dVi_2

        idx_Y = stampY(self.lambda_Vi, self.lambda_Vr, dLil_dLbda_rl , Ydunlin_val, Ydunlin_row, Ydunlin_col, idx_Y)
        idx_Y = stampY(self.lambda_Vi, self.lambda_Vi, dLil_dLada_il, Ydunlin_val, Ydunlin_row, Ydunlin_col, idx_Y)
        idx_Y = stampY(self.lambda_Vi, self.Vr_node, dLil_dVr, Ydunlin_val, Ydunlin_row, Ydunlin_col, idx_Y)
        idx_Y = stampY(self.lambda_Vi, self.Vi_node, dLil_dVi, Ydunlin_val, Ydunlin_row, Ydunlin_col, idx_Y)

        Lil_hist = Lbda_r*dIrldVi*(+1)+Lbda_i*dIildVi*(+1)
        
        Lil_J_stamp = -Lil_hist+Lbda_r*dLil_dLbda_rl+Lbda_i*dLil_dLada_il+Vr*dLil_dVr+Vi*dLil_dVi

        idx_J = stampJ(self.lambda_Vi, Lil_J_stamp, Jdunlin_val, Jdunlin_row, idx_J)

        #print ('load i,j =', self.lambda_Vi, self.lambda_Vr, 'dLil_dLbda_rl', dLil_dLbda_rl)
        #print ('load i,j =', self.lambda_Vi, self.lambda_Vi, 'dLil_dLada_il', dLil_dLada_il)
        #print ('load i,j =', self.lambda_Vi, self.Vr_node, 'dLil_dVr', dLil_dVr)
        #print ('load i,j =', self.lambda_Vi, self.Vi_node, 'dLil_dVi', dLil_dVi)  
        #print ('J[i] =', self.lambda_Vi, Lil_J_stamp)      

        return (idx_Y, idx_J)

    def calc_residuals(self, resid, V):
        P = self.P
        Vr = V[self.Vr_node]
        Vi = V[self.Vi_node]
        Q = self.Q
        resid[self.Vr_node] += (P*Vr+Q*Vi)/(Vr**2+Vi**2)
        resid[self.Vi_node] += (P*Vi-Q*Vr)/(Vr**2+Vi**2)
