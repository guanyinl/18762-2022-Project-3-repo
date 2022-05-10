from __future__ import division
from itertools import count
from scripts.global_vars import global_vars
from models.Buses import Buses
from scripts.stamp_helpers import *
from models.global_vars import global_vars

class Generators:
    _ids = count(0)
    RemoteBusGens = dict()
    RemoteBusRMPCT = dict()
    gen_bus_key_ = {}
    total_P = 0

    def __init__(self,
                 Bus,
                 P,
                 Vset,
                 Qmax,
                 Qmin,
                 Pmax,
                 Pmin,
                 Qinit,
                 RemoteBus,
                 RMPCT,
                 gen_type):
        """Initialize an instance of a generator in the power grid.

        Args:
            Bus (int): the bus number where the generator is located.
            P (float): the current amount of active power the generator is providing.
            Vset (float): the voltage setpoint that the generator must remain fixed at.
            Qmax (float): maximum reactive power
            Qmin (float): minimum reactive power
            Pmax (float): maximum active power
            Pmin (float): minimum active power
            Qinit (float): the initial amount of reactive power that the generator is supplying or absorbing.
            RemoteBus (int): the remote bus that the generator is controlling
            RMPCT (float): the percent of total MVAR required to hand the voltage at the controlled bus
            gen_type (str): the type of generator
        """

        self.Bus = Bus
        self.P_MW = P
        self.Vset = Vset
        self.Qmax_MVAR = Qmax
        self.Qmin_MVAR = Qmin
        self.Pmax_MW = Pmax
        self.Pmin_MW = Pmin
        self.Qinit_MVAR = Qinit
        self.RemoteBus = RemoteBus
        self.RMPCT = RMPCT
        self.gen_type = gen_type
        # convert P/Q to pu
        self.P = P/global_vars.base_MVA
        self.Vset = Vset
        self.Qmax = Qmax/global_vars.base_MVA
        self.Qmin = Qmin/global_vars.base_MVA
        self.Qinit = Qinit/global_vars.base_MVA
        self.Pmax = Pmax/global_vars.base_MVA
        self.Pmin = Pmin/global_vars.base_MVA

        self.id = self._ids.__next__()

    def assign_indexes(self, bus):
        # Nodes shared by generators on the same bus
        self.Vr_node = bus[Buses.bus_key_[self.Bus]].node_Vr
        self.Vi_node = bus[Buses.bus_key_[self.Bus]].node_Vi
        # run check to make sure the bus actually has a Q node
        self.Q_node = bus[Buses.bus_key_[self.Bus]].node_Q
        # check something about gen_type?? 

        #lambda shared by gnerators on the same bus
        self.lambda_Vr = bus[Buses.bus_key_[self.Bus]].lambda_Vr
        self.lambda_Vi = bus[Buses.bus_key_[self.Bus]].lambda_Vi
        self.lambda_Q = bus[Buses.bus_key_[self.Bus]].lambda_Q

    
    def stamp(self, V, Y_val, Y_row, Y_col, J_val, J_row, idx_Y, idx_J):
        P = -self.P
        Vr = V[self.Vr_node]
        Vi = V[self.Vi_node]
        Q = V[self.Q_node]

        Irg_hist = (P*Vr+Q*Vi)/(Vr**2+Vi**2)
        dIrgdVr = (P*(Vi**2-Vr**2) - 2*Q*Vr*Vi)/(Vr**2+Vi**2)**2
        dIrgdVi = (Q*(Vr**2-Vi**2) - 2*P*Vr*Vi)/(Vr**2+Vi**2)**2
        dIrgdQ = (Vi)/(Vr**2+Vi**2)
        Vr_J_stamp = -Irg_hist + dIrgdVr*Vr + dIrgdVi*Vi + dIrgdQ*Q

        idx_Y = stampY(self.Vr_node, self.Vr_node, dIrgdVr, Y_val, Y_row, Y_col, idx_Y)
        idx_Y = stampY(self.Vr_node, self.Vi_node, dIrgdVi, Y_val, Y_row, Y_col, idx_Y)
        idx_Y = stampY(self.Vr_node, self.Q_node, dIrgdQ, Y_val, Y_row, Y_col, idx_Y)
        idx_J = stampJ(self.Vr_node, Vr_J_stamp, J_val, J_row, idx_J)

        Iig_hist = (P*Vi-Q*Vr)/(Vr**2+Vi**2)
        dIigdVi = -dIrgdVr
        dIigdVr = dIrgdVi
        dIigdQ = -(Vr)/(Vr**2+Vi**2)
        Vi_J_stamp = -Iig_hist + dIigdVr*Vr + dIigdVi*Vi + dIigdQ*Q

        idx_Y = stampY(self.Vi_node, self.Vr_node, dIigdVr, Y_val, Y_row, Y_col, idx_Y)
        idx_Y = stampY(self.Vi_node, self.Vi_node, dIigdVi, Y_val, Y_row, Y_col, idx_Y)
        idx_Y = stampY(self.Vi_node, self.Q_node, dIigdQ, Y_val, Y_row, Y_col, idx_Y)
        idx_J = stampJ(self.Vi_node, Vi_J_stamp, J_val, J_row, idx_J)

        Vset_hist = self.Vset**2 - Vr**2 - Vi**2
        dVset_dVr = -2*Vr
        dVset_dVi = -2*Vi
        Vset_J_stamp = -Vset_hist + dVset_dVr*Vr + dVset_dVi*Vi

        idx_Y = stampY(self.Q_node, self.Vr_node, dVset_dVr, Y_val, Y_row, Y_col, idx_Y)
        idx_Y = stampY(self.Q_node, self.Vi_node, dVset_dVi, Y_val, Y_row, Y_col, idx_Y)
        idx_J = stampJ(self.Q_node, Vset_J_stamp, J_val, J_row, idx_J)

        return (idx_Y, idx_J)

    def stamp_dual(self, V, Ydunlin_val, Ydunlin_row, Ydunlin_col, Jdunlin_val, Jdunlin_row, idx_Y, idx_J):
        # You need to implement this.
        P = -self.P
        Pg = self.P
        Vr = V[self.Vr_node]
        Vi = V[self.Vi_node]
        Q = V[self.Q_node]
        Lbda_rg = V[self.lambda_Vr]
        Lbda_ig = V[self.lambda_Vi]
        Lbda_Q = V[self.lambda_Q]

        #print('Gen Vr Vi Q node =', self.lambda_Vr, self.lambda_Vi, self.lambda_Q)

        #=============first derivatives from the based code=============
        #dIrgdVr = (P*(Vi**2-Vr**2) - 2*Q*Vr*Vi)/(Vr**2+Vi**2)**2  #used
        #dIrgdVi = (Q*(Vr**2-Vi**2) - 2*P*Vr*Vi)/(Vr**2+Vi**2)**2  #used 
        #dIrgdQ = (Vi)/(Vr**2+Vi**2) #used

        #dIigdVi = -dIrgdVr  #used
        #dIigdVr = dIrgdVi   #used
        #dIigdQ = -(Vr)/(Vr**2+Vi**2) #used
        #===============================================================

        #first derivatives defined by Guan
        dIrgdVr =(-Pg/(Vr**2+Vi**2))-((-Pg*Vr-Q*Vi)/(Vr**2+Vi**2)**2)*2*Vr
        dIigdVr =(Q/(Vr**2+Vi**2))-((-Pg*Vi+Q*Vr)/(Vr**2+Vi**2)**2)*2*Vr
        dIqdVr = -2*Vr

        dIrgdVi = (-Q/(Vr**2+Vi**2))-((-Pg*Vr-Q*Vi)/(Vr**2+Vi**2)**2)*2*Vi
        dIigdVi = (-Pg/(Vr**2+Vi**2))-((-Pg*Vi+Q*Vr)/(Vr**2+Vi**2)**2)*2*Vi
        dIqdVi = -2*Vi

        dIrgdQ = -Vi/(Vr**2+Vi**2)
        dIigdQ = Vr/(Vr**2+Vi**2)
        dIqdQ = 0

        #calculate hist terms
        Lrg_hist = Lbda_rg*dIrgdVr+Lbda_ig*dIigdVr+Lbda_Q*dIqdVr #checked
        Lig_hist = Lbda_rg*dIrgdVi+Lbda_ig*dIigdVi+Lbda_Q*dIqdVi #checked
        Lqg_hist = Lbda_rg*dIrgdQ+Lbda_ig*dIigdQ+Lbda_Q*dIqdQ #checked

        #second derivatives
        dLrg_dLbda_rg = dIrgdVr #checked
        dLrg_dLbda_ig = dIigdVr #checked
        dLrg_dLbda_Q = -2*Vr #checked
        dLrg_dQ = Lbda_rg*(2*Vr*Vi)/(Vr**2+Vi**2)**2+Lbda_ig*(Vi**2-Vr**2)/(Vr**2+Vi**2)**2 #checked
        dLrg_dVr_1 = Lbda_rg*((6*Pg*Vr+2*Q*Vi)/(Vr**2+Vi**2)**2+(8*Vr**2*(-Pg*Vr-Q*Vi)/(Vr**2+Vi**2)**3))  #checked
        dLrg_dVr_2 = Lbda_ig*((-6*Q*Vr+2*Pg*Vi)/(Vr**2+Vi**2)**2+(8*Vr**2*(-Pg*Vi+Q*Vr)/(Vr**2+Vi**2)**3))  #checked
        dLrg_dVr_3 = -2*Lbda_Q #checked
        dLrg_dVr = dLrg_dVr_1+dLrg_dVr_2+dLrg_dVr_3  #checked

        dLrg_dVi_1 = Lbda_rg*((2*Pg*Vi+2*Q*Vr)/(Vr**2+Vi**2)**2+(8*Vr*Vi*(-Pg*Vr-Q*Vi)/(Vr**2+Vi**2)**3)) #checked
        dLrg_dVi_2 = Lbda_ig*((-2*Q*Vi+2*Pg*Vr)/(Vr**2+Vi**2)**2+(8*Vr*Vi*(-Pg*Vi+Q*Vr)/(Vr**2+Vi**2)**3)) #checked
        dLrg_dVi = dLrg_dVi_1+dLrg_dVi_2 #checked

        #The value stamps into the J matrix. 
        Lrg_J_stamp = -Lrg_hist+Lbda_rg*dLrg_dLbda_rg+Lbda_ig*dLrg_dLbda_ig+Vr*dLrg_dVr+Vi*dLrg_dVi+Lbda_Q*dLrg_dLbda_Q+Q*dLrg_dQ #checked
        
        idx_Y = stampY(self.lambda_Vr, self.lambda_Vr, dLrg_dLbda_rg, Ydunlin_val, Ydunlin_row, Ydunlin_col, idx_Y)
        idx_Y = stampY(self.lambda_Vr, self.lambda_Vi, dLrg_dLbda_ig, Ydunlin_val, Ydunlin_row, Ydunlin_col, idx_Y)
        idx_Y = stampY(self.lambda_Vr, self.Vr_node, dLrg_dVr, Ydunlin_val, Ydunlin_row, Ydunlin_col, idx_Y)
        idx_Y = stampY(self.lambda_Vr, self.Vi_node, dLrg_dVi, Ydunlin_val, Ydunlin_row, Ydunlin_col, idx_Y)
        idx_Y = stampY(self.lambda_Vr, self.lambda_Q, dLrg_dLbda_Q, Ydunlin_val, Ydunlin_row, Ydunlin_col, idx_Y)
        idx_Y = stampY(self.lambda_Vr, self.Q_node, dLrg_dQ, Ydunlin_val, Ydunlin_row, Ydunlin_col, idx_Y)
        idx_J = stampJ(self.lambda_Vr, Lrg_J_stamp, Jdunlin_val, Jdunlin_row, idx_J)

        #print ('gen i,j =', self.lambda_Vr, self.lambda_Vr, 'dLrg_dLbda_rg', dLrg_dLbda_rg)
        #print ('gen i,j =', self.lambda_Vr, self.Vr_node, 'dLrg_dVr', dLrg_dVr)
        #print ('gen i,j =', self.lambda_Vr, self.Vi_node, 'dLrg_dVi', dLrg_dVi)
        #print ('gen i,j =', self.lambda_Vr, self.lambda_Q, 'dLrg_dLbda_Q', dLrg_dLbda_Q)
        #print ('gen i,j =', self.lambda_Vr, self.Q_node, 'dLrg_dQ', dLrg_dQ)
        #print ('J[i] =', self.lambda_Vr, Lrg_J_stamp)

        dLig_dLbda_rg = dIrgdVi #checked
        dLig_dLbda_ig = dIigdVi #checked
        dLig_dLbda_Q = -2*Vi #checked
        dLig_dVrg_1 = Lbda_rg*((2*Pg*Vi+2*Q*Vr)/(Vr**2+Vi**2)**2+(8*Vr*Vi*(-Pg*Vr-Q*Vi)/(Vr**2+Vi**2)**3)) #checked
        dLig_dVrg_2 = Lbda_ig*((-2*Q*Vi+2*Pg*Vr)/(Vr**2+Vi**2)**2+(8*Vr*Vi*(-Pg*Vi+Q*Vr)/(Vr**2+Vi**2)**3)) #checked
        dLig_dVrg = dLig_dVrg_1+dLig_dVrg_2 #checked

        dLig_dVig_1 = Lbda_rg*((2*Pg*Vr+6*Q*Vi)/(Vr**2+Vi**2)**2+(8*Vi**2*(-Pg*Vr-Q*Vi)/(Vr**2+Vi**2)**3)) #checked
        dLig_dVig_2 = Lbda_ig*((-2*Q*Vr+6*Pg*Vi)/(Vr**2+Vi**2)**2+(8*Vi**2*(-Pg*Vi+Q*Vr)/(Vr**2+Vi**2)**3)) #checked
        dLig_dVig_3 = -2*Lbda_Q #checked
        dLig_dVig = dLig_dVig_1+dLig_dVig_2+dLig_dVig_3 #checked
        
        dLig_dQ = Lbda_rg*(Vi**2-Vr**2)/(Vr**2+Vi**2)**2+Lbda_ig*(-2*Vr*Vi)/(Vr**2+Vi**2)**2 #checked

        #The value stamps into the J matrix. 
        Lig_J_stamp = -Lig_hist+Lbda_rg*dLig_dLbda_rg+Lbda_ig*dLig_dLbda_ig+Vr*dLig_dVrg+Vi*dLig_dVig+Lbda_Q*dLig_dLbda_Q+Q*dLig_dQ #checked

        idx_Y = stampY(self.lambda_Vi, self.lambda_Vr, dLig_dLbda_rg, Ydunlin_val, Ydunlin_row, Ydunlin_col, idx_Y)
        idx_Y = stampY(self.lambda_Vi, self.lambda_Vi, dLig_dLbda_ig, Ydunlin_val, Ydunlin_row, Ydunlin_col, idx_Y)
        idx_Y = stampY(self.lambda_Vi, self.Vr_node, dLig_dVrg, Ydunlin_val, Ydunlin_row, Ydunlin_col, idx_Y)
        idx_Y = stampY(self.lambda_Vi, self.Vi_node, dLig_dVig, Ydunlin_val, Ydunlin_row, Ydunlin_col, idx_Y)
        idx_Y = stampY(self.lambda_Vi, self.lambda_Q, dLig_dLbda_Q, Ydunlin_val, Ydunlin_row, Ydunlin_col, idx_Y)
        idx_Y = stampY(self.lambda_Vi, self.Q_node, dLig_dQ, Ydunlin_val, Ydunlin_row, Ydunlin_col, idx_Y)
        idx_J = stampJ(self.lambda_Vi, Lig_J_stamp, Jdunlin_val, Jdunlin_row, idx_J)

        #print ('gen i,j =', self.lambda_Vi, self.lambda_Vr, 'dLig_dLbda_rg', dLig_dLbda_rg)
        #print ('gen i,j =', self.lambda_Vi, self.lambda_Vi, 'dLig_dLbda_ig', dLig_dLbda_ig)
        #print ('gen i,j =', self.lambda_Vi, self.Vr_node, 'dLig_dVrg', dLig_dVrg)
        #print ('gen i,j =', self.lambda_Vi, self.Vi_node, 'dLig_dVig', dLig_dVig)
        #print ('gen i,j =', self.lambda_Vi, self.lambda_Q, 'dLig_dLbda_Q', dLig_dLbda_Q)
        #print ('gen i,j =', self.lambda_Vi, self.Q_node, 'dLig_dQ', dLig_dQ)
        #print ('J[i] =', self.lambda_Vi, Lig_J_stamp)

        dLqg_dLbda_rg = dIrgdQ  #checked
        dLqg_dLbda_ig = dIigdQ  #checked
        dLqg_dVrg_1 = Lbda_rg*(2*Vr*Vi/(Vr**2+Vi**2)**2)  #checked
        dLqg_dVrg_2 = Lbda_ig*(1/(Vr**2+Vi**2)-2*Vr**2/(Vr**2+Vi**2)**2) #checked
        dLqg_dVrg = dLqg_dVrg_1+dLqg_dVrg_2  #checked

        dLqg_dVig_1 = Lbda_rg*(-1/(Vr**2+Vi**2)+2*Vi**2/(Vr**2+Vi**2)**2) #checked
        dLqg_dVig_2 = Lbda_ig*(-1)*2*Vr*Vi/(Vr**2+Vi**2)**2 #checked
        dLqg_dVig = dLqg_dVig_1+dLqg_dVig_2 #checked

        #The value stamps into the J matrix. 
        Lqg_J_stamp = -Lqg_hist+Lbda_rg*dLqg_dLbda_rg+Lbda_ig*dLqg_dLbda_ig+Vr*dLqg_dVrg+Vi*dLqg_dVig #checked

        idx_Y = stampY(self.lambda_Q, self.lambda_Vr, dLqg_dLbda_rg, Ydunlin_val, Ydunlin_row, Ydunlin_col, idx_Y)
        idx_Y = stampY(self.lambda_Q, self.lambda_Vi, dLqg_dLbda_ig, Ydunlin_val, Ydunlin_row, Ydunlin_col, idx_Y)
        idx_Y = stampY(self.lambda_Q, self.Vr_node, dLqg_dVrg, Ydunlin_val, Ydunlin_row, Ydunlin_col, idx_Y)
        idx_Y = stampY(self.lambda_Q, self.Vi_node, dLqg_dVig, Ydunlin_val, Ydunlin_row, Ydunlin_col, idx_Y)
        idx_J = stampJ(self.lambda_Q, Lqg_J_stamp, Jdunlin_val, Jdunlin_row, idx_J)

        #print ('gen i,j =', self.lambda_Q, self.lambda_Vr, 'dLqg_dLbda_rg', dLqg_dLbda_rg)
        #print ('gen i,j =', self.lambda_Q, self.lambda_Vi, 'dLqg_dLbda_ig', dLqg_dLbda_ig)
        #print ('gen i,j =', self.lambda_Q, self.Vr_node, 'dLqg_dVrg', dLqg_dVrg)
        #print ('gen i,j =', self.lambda_Q, self.Vi_node, 'dLqg_dVig', dLqg_dVig)
        #print ('J[i] =', self.lambda_Q, Lqg_J_stamp)

        return (idx_Y, idx_J)

    def calc_residuals(self, resid, V):
        P = -self.P
        Vr = V[self.Vr_node]
        Vi = V[self.Vi_node]
        Q = V[self.Q_node]
        resid[self.Vr_node] += (P*Vr+Q*Vi)/(Vr**2+Vi**2)
        resid[self.Vi_node] += (P*Vi-Q*Vr)/(Vr**2+Vi**2)
        resid[self.Q_node] += self.Vset**2 - Vr**2 - Vi**2

