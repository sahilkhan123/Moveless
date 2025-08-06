'''
Schedules gates in topologically sorted order
Policy is called EJF Earliest Job First, because its similar to the famous job scheduling policy

done - handle case where both traps are full
done - handle junction traffic flow
todo - skip - handle preemption??
todo - skip - handle traffic based routing
'''

import networkx as nx
import numpy as np
from machine_state import MachineState
from utils import *
from route import *
from schedule import *
from machine import Trap, Segment, Junction
from rebalance import *
import customScheduler
import circuit_generator
import pickle as pkl
import math

class EJFSchedule:
    #Inputs are
    #1. gate dependency graph - IR
    #2. gate_info = what are the qubits used by a two-qubit gate?
    #3. M = machine object
    #4. init_map = initial qubit mapping
    def __init__(self, ir, gate_info, M, init_map, serial_trap_ops, serial_comm, global_serial_lock):
        self.ir = ir
        self.gate_info = gate_info
        self.machine = M
        self.init_map = init_map

        #Setup scheduler
        self.machine.add_comm_capacity(2) #NOTE MADE BY SAHIL 9/27/24: SYMPATHETIC COOLING IONS ARE ADDED HERE
        #Add space for 2 extra ions in each trap
        self.SerialTrapOps = serial_trap_ops # ---> serializes operations on a single trap zone
        self.SerialCommunication = serial_comm # ---> serializes all split/merge/move ops
        self.GlobalSerialLock = global_serial_lock #---> serialize gates and comm

        #SerialTrapOps enforces that all operations in a trap are serialized
        #i.e., no parallel gates in a single ion chain/region
        self.schedule = Schedule(M) #edit here
        self.router = BasicRoute(M)
        self.gate_finish_times = {}

        #Some scheduling statistics
        #Count the number of times we had to clear some traps because of traffic blocks
        self.count_rebalance = 0
        self.split_swap_counter = 0

        #Create the sys_stage object which is used to track system state
        #from the perspective of the scheduler
        trap_ions = {}
        seg_ions = {}
        for i in M.traps:
            if init_map[i.id]:
                trap_ions[i.id] = init_map[i.id][:]
            else:
                trap_ions[i.id] = []
        for i in M.segments:
            seg_ions[i.id] = []
        self.sys_state = MachineState(0, trap_ions, seg_ions)
        print("schedule right here", self.schedule.events)
        self.sys_state.print_state()

    #Find the earliest time at which a gate can be scheduled
    #Earliest time = max(dependent gate times)
    def gate_ready_time(self, gate):
        ready_time = 0
        for in_edge in self.ir.in_edges(gate):
            #Each in edge is of the form (in_gate_id, this_gate_id)
            in_gate = in_edge[0]
            if in_gate in self.gate_finish_times:
                ready_time = max(ready_time, self.gate_finish_times[in_gate])
            else:
                print("Error: Finish time of dependent gate not found", in_edge)
                assert 0
        return ready_time

    #Find the time at which a particular qubit/ion is ready for another operation
    def ion_ready_info(self, ion_id):
        s = self.schedule
        this_ion_ops = s.filter_by_ion(s.events, ion_id)
        this_ion_last_op_time = 0
        this_ion_trap = None
        #If there is some operation that has happened for this ion:
        if len(this_ion_ops):
            #The last operation on an ion is either a gate or a merge in a trap
            assert (this_ion_ops[-1][1] == Schedule.Gate) or (this_ion_ops[-1][1] == Schedule.Merge)
            #Pick up the time and location of last operation
            this_ion_last_op_time = this_ion_ops[-1][3]
            this_ion_trap = this_ion_ops[-1][4]['trap']
        else:
            #Find which trap originally held this ion
            #It shouldn't have changed because no ops have happened for this ion
            did_not_find = True
            for trap_id in self.init_map.keys():
                if ion_id in self.init_map[trap_id]:
                    this_ion_trap = trap_id
                    did_not_find = False
                    break
            if did_not_find:
                print("Did not find:", ion_id)
            assert (did_not_find == False)

        #Double checking ion location from sys_state object
        if this_ion_trap != self.sys_state.find_trap_id_by_ion(ion_id):
            print("PRINTING STUFF RIGHT BEFORE THE ERROR")
            print(ion_id, this_ion_trap, self.sys_state.find_trap_id_by_ion(ion_id))
            self.sys_state.print_state()
            assert 0
        #print("got ", (this_ion_last_op_time, this_ion_trap))
        return this_ion_last_op_time, this_ion_trap

    #Add a split operation to the current schedule
    def add_split_op(self, clk, src_trap, dest_seg, ion):
        m = self.machine
        if self.SerialTrapOps == 1:
            last_event_time_on_trap = self.schedule.last_event_time_on_trap(src_trap.id)
            split_start = max(clk, last_event_time_on_trap)
        else:
            split_start = clk

        if self.SerialCommunication == 1:
            last_comm_time = self.schedule.last_comm_event_time()
            split_start = max(split_start, last_comm_time)

        if self.GlobalSerialLock == 1:
            last_event_time_in_system = self.schedule.get_last_event_ts()
            split_start = max(split_start, last_event_time_in_system)
        split_duration, split_swap_count, split_swap_hops, i1, i2, ion_swap_hops = m.split_time(self.sys_state, src_trap.id, dest_seg.id, ion)
        #print("split duration", split_duration)
        self.split_swap_counter += split_swap_count
        split_end = split_start + split_duration
        self.schedule.add_split_or_merge(split_start, split_end, [ion], src_trap.id, dest_seg.id, Schedule.Split, split_swap_count, split_swap_hops, i1, i2, ion_swap_hops)
        return split_end

    #Add a merge operation to the current schedule
    def add_merge_op(self, clk, dest_trap, src_seg, ion):
        m = self.machine
        if self.SerialTrapOps == 1:
            last_event_time_on_trap = self.schedule.last_event_time_on_trap(dest_trap.id)
            merge_start = max(clk, last_event_time_on_trap)
        else:
            merge_start = clk

        if self.SerialCommunication == 1:
            last_comm_time = self.schedule.last_comm_event_time()
            merge_start = max(merge_start, last_comm_time)

        if self.GlobalSerialLock == 1:
            last_event_time_in_system = self.schedule.get_last_event_ts()
            merge_start = max(merge_start, last_event_time_in_system)
        merge_end = merge_start + m.merge_time(dest_trap.id)
        self.schedule.add_split_or_merge(merge_start, merge_end, [ion], dest_trap.id, src_seg.id, Schedule.Merge, 0, 0, 0, 0, 0)
        return merge_end

    #Add a move operation to the current schedule
    #This is one segment to segment move i.e., move ion from src_seg to dest_seg
    def add_move_op(self, clk, src_seg, dest_seg, junct, ion):
        m = self.machine
        move_start = clk
        if self.GlobalSerialLock == 1:
            last_event_time_in_system = self.schedule.get_last_event_ts()
            move_start = max(move_start, last_event_time_in_system)

        if self.SerialCommunication == 1:
            last_comm_time = self.schedule.last_comm_event_time()
            move_start = max(move_start, last_comm_time)

        move_end = move_start + m.move_time(src_seg.id, dest_seg.id) + m.junction_cross_time(junct)
        move_start, move_end = self.schedule.junction_traffic_crossing(src_seg, dest_seg, junct, move_start, move_end)
        self.schedule.add_move(move_start, move_end, [ion], src_seg.id, dest_seg.id)
        return move_end

    #Add a gate operation to the current schedule
    def add_gate_op(self, clk, trap_id, gate, ion1, ion2):
        fire_time = clk
        if self.SerialTrapOps == 1:
            last_event_time_on_trap = self.schedule.last_event_time_on_trap(trap_id)
            fire_time = max(clk, last_event_time_on_trap)

        if self.GlobalSerialLock == 1:
            last_event_time_in_system = self.schedule.get_last_event_ts()
            fire_time = max(fire_time, last_event_time_in_system)
        gate_duration = self.machine.gate_time(self.sys_state, trap_id, ion1, ion2)
        self.schedule.add_gate(fire_time, fire_time + gate_duration, [ion1, ion2], trap_id)
        self.gate_finish_times[gate] = fire_time + gate_duration
        return fire_time + gate_duration

    #Heuristic to determine direction of shuttling for two traps
    def shuttling_direction(self, ion1_trap, ion2_trap):
        #Other Possible policies: lookahead, traffic/path based
        m = self.machine
        ss = self.sys_state
        excess_cap1 = m.traps[ion1_trap].capacity - len(ss.trap_ions[ion1_trap])
        excess_cap2 = m.traps[ion2_trap].capacity - len(ss.trap_ions[ion2_trap])
        #both excess capacities can be 0 if the traps are full
        frac_empty = float(excess_cap1)/m.traps[ion1_trap].capacity
        #Whichever trap has more excess capacity choose that as the destination

        #TODO: Change to whichever one is the ancilla, move that one
        #Check printing of what operations to make sure that its actually doing what I want.
        if excess_cap1 > excess_cap2:
            dest_trap = ion1_trap
            source_trap = ion2_trap
        else:
            dest_trap = ion2_trap
            source_trap = ion1_trap

        if excess_cap1 <= 0 and excess_cap2 <= 0:
            print(ion1_trap, ion2_trap)
            print(ss.trap_ions)
            print("Both traps full", ion1_trap, m.traps[ion1_trap].capacity,  ss.trap_ions[ion1_trap])
            assert 0
        return source_trap, dest_trap

    #Fire an end-to-end shuttle operation from src_trap to dest_trap
    def fire_shuttle(self, src_trap, dest_trap, ion, gate_fire_time, route=[]):
        s = self.schedule
        m = self.machine
        #If route is not specified in the function args, find a route using
        #the router object passed to the scheduler
        if len(route):
            rpath = route
        else:
            rpath = self.router.find_route(src_trap, dest_trap)

        #Find the time that it will take to do this entire shuttle
        #This is required to find a feasible time for scheduling this shuttle
        t_est = 0
        for i in range(len(rpath)-1):
            src = rpath[i]
            dest = rpath[i+1]
            if type(src) == Trap and type(dest) == Junction:
                my_seg = m.graph[src][dest]['seg']
                t_est += m.mparams.split_merge_time
                #split_time(self.sys_state, src.id, my_seg.id, ion)
            elif type(src) == Junction and type(dest) == Junction:
                t_est += m.move_time(src.id, dest.id)
            elif type(src) == Junction and type(dest) == Trap:
                t_est += m.merge_time(dest.id)

        #This is the traffic-unaware/conservative version where we wait for the full path to be available
        clk = self.schedule.identify_start_time(rpath, gate_fire_time, t_est)

        #Add the shuttling operations to the schedule based on the identified start time
        clk = self._add_shuttle_ops(rpath, ion, clk)

        #self.sys_state.trap_ions[src_trap].remove(ion)
        #self.sys_state.trap_ions[dest_trap].append(ion)
        return clk

    #Helper function to implement a shuttle
    def _add_shuttle_ops(self, spath, ion, clk):
        #Decompose into trap-trap paths
        #For each trap to trap path call a split-move*-merge sequence
        trap_pos = []
        for i in range(len(spath)):
            if type(spath[i]) == Trap:
                trap_pos.append(i)
        for i in range(len(trap_pos)-1):
            idx0 = trap_pos[i]
            idx1 = trap_pos[i+1]+1
            clk = self._add_partial_shuttle_ops(spath[idx0:idx1], ion, clk)
            self.sys_state.trap_ions[spath[trap_pos[i]].id].remove(ion)
            last_junct = spath[trap_pos[i+1]-1]
            dest_trap = spath[trap_pos[i+1]]
            last_seg = self.machine.graph[last_junct][dest_trap]['seg']
            orient = dest_trap.orientation[last_seg.id]
            if orient == 'R':
                self.sys_state.trap_ions[spath[trap_pos[i+1]].id].append(ion)
            else:
                self.sys_state.trap_ions[spath[trap_pos[i+1]].id].insert(0, ion)
        return clk

    #Helper function to implement a shuttle
    def _add_partial_shuttle_ops(self, spath, ion, clk):
        assert len([item for item in spath if type(item) == Trap]) == 2
        seg_list = []
        for i in range(len(spath)-1):
            u = spath[i]
            v = spath[i+1]
            seg_list.append(self.machine.graph[u][v]['seg'])
        clk = self.add_split_op(clk, spath[0], seg_list[0], ion)
        for i in range(len(seg_list)-1):
            u = seg_list[i]
            v = seg_list[i+1]
            junct = spath[1+i]
            clk = self.add_move_op(clk, u, v, junct, ion)
        clk = self.add_merge_op(clk, spath[-1], seg_list[-1], ion)
        return clk

    #Main scheduling function for a gate
    def schedule_gate_enhancement(self, gate, ancillas, specified_time=0, dynamicMode=False):
        s = self.schedule
        #print("schedule", s.events)
        #print("schedule is ", s.events)
        #Find time at which the gate can be fired
        if (dynamicMode == False):
            ready = self.gate_ready_time(gate) #assuming there is no gate dependences in QEC circuits
        ion1 = self.gate_info[gate][0]
        ion2 = self.gate_info[gate][1]
        print("gate is", gate)
        print("ion1", ion1)
        print("ion2", ion2)
        #Find time at which ions are ready
        ion1_time, ion1_trap = self.ion_ready_info(ion1)
        ion2_time, ion2_trap = self.ion_ready_info(ion2)
        if (dynamicMode == False):
            fire_time = max(ready, ion1_time, ion2_time)
        fire_time = max(ion1_time, ion2_time)
        fire_time = max(fire_time, specified_time)

        #print("Gate", gate, "I1", ion1, "I2", ion2, "IT1", ion1_trap, "IT2", ion2_trap, "Ready", ready, "FireTime:", fire_time)

        if ion1_trap == ion2_trap:
            #Ions are co-located in a trap, no shuttling required
            print("got to adding a gate op")
            self.add_gate_op(fire_time, ion1_trap, gate, ion1, ion2)
        else:
            #Check if there is at least one path to shuttle from src to dest trap
            #rebalances the machine if needed i.e., clear traffic blocks
            rebal_flag, new_fin_time = self.rebalance_traps(focus_traps=[ion1_trap, ion2_trap], fire_time=fire_time, enhancement=True, ancillas=ancillas, ions=(ion1, ion2))
            if not rebal_flag:
                """
                source_trap, dest_trap = self.shuttling_direction(ion1_trap, ion2_trap)
                #TODO: modify right around here where we check which is the ion that has to move, needs to be ancilla
                if source_trap == ion1_trap:
                    moving_ion = ion1
                else:
                    moving_ion = ion2
                """
                if (ion1 in ancillas):
                    moving_ion = ion1
                    source_trap = ion1_trap
                    dest_trap = ion2_trap
                elif (ion2 in ancillas):
                    moving_ion = ion2
                    source_trap = ion2_trap
                    dest_trap = ion1_trap
                    #print("ERROR: they can't both be in ancillas")
                    assert(ion1 not in ancillas)
                else:
                    print("ERROR: neither of the moving ions are in ancillas?! This means a CX between data?")
                    assert(0)

                clk = self.fire_shuttle(source_trap, dest_trap, moving_ion, fire_time)
                self.add_gate_op(clk, dest_trap, gate, ion1, ion2)
            else:
                #This is for the rebalancing case, trap_ids compute till this point may be stale
                self.schedule_gate_enhancement(gate, ancillas=ancillas, specified_time=new_fin_time, dynamicMode=dynamicMode)
    
    def schedule_gate(self, gate, specified_time=0):
        s = self.schedule
        #print("schedule is ", s.events)
        #Find time at which the gate can be fired
        ready = self.gate_ready_time(gate)
        ion1 = self.gate_info[gate][0]
        ion2 = self.gate_info[gate][1]
        #Find time at which ions are ready
        ion1_time, ion1_trap = self.ion_ready_info(ion1)
        ion2_time, ion2_trap = self.ion_ready_info(ion2)
        fire_time = max(ready, ion1_time, ion2_time)
        fire_time = max(fire_time, specified_time)

        #print("Gate", gate, "I1", ion1, "I2", ion2, "IT1", ion1_trap, "IT2", ion2_trap, "Ready", ready, "FireTime:", fire_time)

        if ion1_trap == ion2_trap:
            #Ions are co-located in a trap, no shuttling required
            self.add_gate_op(fire_time, ion1_trap, gate, ion1, ion2)
        else:
            #Check if there is at least one path to shuttle from src to dest trap
            #rebalances the machine if needed i.e., clear traffic blocks
            rebal_flag, new_fin_time = self.rebalance_traps(focus_traps=[ion1_trap, ion2_trap], fire_time=fire_time)
            if not rebal_flag:
                
                source_trap, dest_trap = self.shuttling_direction(ion1_trap, ion2_trap)
                if source_trap == ion1_trap:
                    moving_ion = ion1
                else:
                    moving_ion = ion2
                
                
                clk = self.fire_shuttle(source_trap, dest_trap, moving_ion, fire_time)
                self.add_gate_op(clk, dest_trap, gate, ion1, ion2)
            else:
                #This is for the rebalancing case, trap_ids compute till this point may be stale
                self.schedule_gate(gate, specified_time=new_fin_time)

    #Checks and rebalances the machine if necessary using MCMF
    def rebalance_traps(self, focus_traps, fire_time, enhancement=False, ancillas=[], ions=(-1,-1)):
        m = self.machine
        ss = self.sys_state
        t1 = focus_traps[0]
        t2 = focus_traps[1]
        #print("trap capacity", m.traps[t1].capacity)
        #print("ions at this point", ss.trap_ions)
        excess_cap1 = m.traps[t1].capacity - len(ss.trap_ions[t1])
        excess_cap2 = m.traps[t2].capacity - len(ss.trap_ions[t2])
        #print("cap 1", excess_cap1)
        #print("cap 2", excess_cap2)
        need_rebalance = False

        ftr = FreeTrapRoute(m, ss)
        status12, route12 = ftr.find_route(t1, t2)
        status21, route21 = ftr.find_route(t2, t1)

        #If both traps are full
        if excess_cap1 == 0 and excess_cap2 == 0:
            need_rebalance = True
        else:
           #If no route exists either way
            if status12 == 1 and status21 == 1:
                need_rebalance = True
        if (enhancement): #if the non-ancilla trap is full, it needs rebalancing
            #print("GOT TO THIS POINT")
            ion1, ion2 = ions
            if (ion1 in ancillas):
                nonancilla = t2
            elif (ion2 in ancillas):
                nonancilla = t1
            else:
                #print("uh oh")
                assert(0)
            if (excess_cap1 == 0 and nonancilla == t1):
                #print("REBALANCING")
                need_rebalance = True
            if (excess_cap2 == 0 and nonancilla == t2):
                #print("REBALANCIGN 2")
                need_rebalance = True

        if need_rebalance:
            #print("Rebalance procedure", "clk=", fire_time)
            finish_time = self.do_rebalance_traps(fire_time)
            #print("Rebalance procedure", "clk=", finish_time)
        if need_rebalance:
            return 1, finish_time
        else:
            return 0, fire_time

    def do_rebalance_traps(self, fire_time):
        self.count_rebalance += 1
        rebal = RebalanceTraps(self.machine, self.sys_state)
        flow_dict = rebal.clear_all_blocks()
        shuttle_graph = nx.DiGraph()
        used_flow = {}
        clk = fire_time
        for i in flow_dict:
            for j in flow_dict[i]:
                if flow_dict[i][j] != 0:
                    shuttle_graph.add_edge(i, j, weight=flow_dict[i][j])
                    used_flow[(i, j)] = 0
        fin_time = fire_time
        for node in shuttle_graph.nodes():
            if shuttle_graph.in_degree(node) == 0 and type(node) == Trap:
                #print("Starting computation from", node.show())
                updated_graph = shuttle_graph.copy()
                for edge in used_flow:
                    if used_flow[edge] == updated_graph[edge[0]][edge[1]]['weight']:
                        updated_graph.remove_edge(edge[0], edge[1])
                T = nx.dfs_tree(updated_graph, source=node)
                for tnode in T:
                    if T.out_degree(tnode) == 0:
                        shuttle_route = nx.shortest_path(T, node, tnode)
                        break
                for i in range(len(shuttle_route)-1):
                    e0 = shuttle_route[i]
                    e1 = shuttle_route[i+1]
                    if (e0, e1) in used_flow:
                        used_flow[(e0, e1)] += 1
                    elif (e1, e0) in used_flow:
                        used_flow[(e1, e0)] += 1
                moving_ion = self.sys_state.trap_ions[node.id][0]
                ion_time, _ = self.ion_ready_info(moving_ion)
                fire_time = max(fire_time, ion_time)
                #print("moving", moving_ion, "along path")
                #for item in shuttle_route:
                #    print(item.show())
                #print('path end')
                #Fire a shuttle along this route, move first ion in the source trap for now
                fin_time_new = self.fire_shuttle(node.id, tnode.id, moving_ion, fire_time, route=shuttle_route)
                fin_time = max(fin_time, fin_time_new)
        return fin_time

    def run(self):
        #print("AT BEGINNING OF PRAKASH'S")
        self.gates = nx.topological_sort(self.ir)
        cnt = 0
        #self.sys_state.print_state()
        for g in self.gates:
            self.schedule_gate(g)
            cnt += 1
        #print("PRINTING ORDER OF EVENTS")
        #self.schedule.print_events()
        #print("PRINTING END STATE IN THEIR WAY")
        #self.sys_state.print_state()

    def run_enhancement(self, circuit, dynamic_scheduling=False, stabilizer_mode=False):
            #print("AT BEGINNING")
            self.gates = nx.topological_sort(self.ir)
            cnt = 0
            #self.sys_state.print_state()
            ancillas = customScheduler.getAncillaBits(circuit)
            #print("GATES TOPOLOGICAL SORT", list(self.gates))
            #print("GATE INFO", self.gate_info)
            if (dynamic_scheduling): #moveless compiler

                codeName = circuit.split("_code")[0].split("/")[-1]
                fileName = "stabilizer_metadata/" + codeName + "matrix.pkl"
                with open(fileName, "rb") as file:
                    stabilizerString = pkl.load(file)
                #print("stabilizerString", stabilizerString)
                n = int(codeName.split("-")[0])
                x_s, z_s, cx_arr , _ = circuit_generator.parse_to_tuple(stabilizerString, n)
                #print("stabilizers", cx_arr)
                stabilizer_dict = {}
                for i in range(len(cx_arr)):
                    stabilizer_dict[i] = cx_arr[i]
                while stabilizer_dict:
                    next_stabilizer, ancilla, move_score, stab_number, order_list = self.count_moves(ancillas, self.sys_state, stabilizer_dict)
                    if (stabilizer_mode):
                        x_direction = True
                        z_direction = True
                    else:
                        if (next_stabilizer in x_s):
                            x_direction = True
                            z_direction = False
                            x_s.remove(next_stabilizer)
                        else:
                            assert(next_stabilizer in z_s)
                            z_direction = True
                            x_direction = False
                            z_s.remove(next_stabilizer)
                    for s in order_list: #this was an enhancement that uses order_list as opposed to next stabilizer which puts a good ordering on next_stabilizer
                        #print("length of ancillas", len(ancillas))
                        #print("s", s)
                        #print("next stabilizer", next_stabilizer)
                        #print("stabilizer number", stab_number)
                        assert(x_direction or z_direction)
                        original_ancilla = stab_number % len(ancillas) + n
                        g = self.find_gate_from_gate_info(ancilla, s, original_ancilla=original_ancilla, x_direction=x_direction, z_direction=z_direction) 
                        self.schedule_gate_enhancement(gate=g, ancillas=ancillas, dynamicMode=dynamic_scheduling)
                        cnt += 1
                    del stabilizer_dict[stab_number]
                    x_direction = False
                    z_direction = False
                    #print("lowest move score", move_score)
            else:
                #print("got in the else clause")
                #print("self gates", self.gates)
                for g in self.gates:
                    self.schedule_gate_enhancement(gate=g, ancillas=ancillas, dynamicMode=dynamic_scheduling)
                    cnt += 1
            #print("PRINTING ORDER OF EVENTS")
            self.schedule.print_events()
            #print("PRINTING END STATE IN THEIR WAY")
            self.sys_state.print_state()
    
    def run_enhancement_cyclone(self, circuit, dynamic_scheduling=False):
            #print("AT BEGINNING")
            #print("self schedule events here", self.schedule.events)
            self.gates = nx.topological_sort(self.ir)
            cnt = 0
            #self.sys_state.print_state()
            ancillas = customScheduler.getAncillaBits(circuit)
            
            for g in self.gates:
                #print("schedule right here though is ", self.schedule.events) #ok so schedule updates iteratively through here which makes sense
                #print(g)
                self.schedule_gate_enhancement(gate=g, ancillas=ancillas, dynamicMode=dynamic_scheduling)
                #print("scheduled ", g)
                cnt += 1
            print("PRINTING ORDER OF EVENTS")
            self.schedule.print_events()
            #print("PRINTING END STATE IN THEIR WAY")
            #self.sys_state.print_state()
    
    def count_moves(self, ancilla, sys_state, stabilizer_dict):
        lowest = math.inf
        best_stabilizer = None
        ancilla_returned = None
        for a in ancilla:
            for s in stabilizer_dict:
                score = 0
                order_dict = {}
                for data in stabilizer_dict[s]:
                    src_trap = sys_state.find_trap_id_by_ion(data)
                    dest_trap = sys_state.find_trap_id_by_ion(a)
                    assert(dest_trap != -1 and src_trap != -1)
                    print("source trap is", src_trap)
                    print("dest trap is", dest_trap)
                    path = self.router.find_route(src_trap, dest_trap)
                    if (stabilizer_dict[s] == [1,3,4,5]):
                        print("PATH OF 1345", [p.id for p in path], src_trap, dest_trap)
                    if (len(path) == 1):
                        score += 0
                        order_dict[data] = 0
                    else:
                        score += len(path) - 1
                        order_dict[data] = len(path) - 1
                    
                    
                if (score < lowest):
                    lowest = score
                    best_stabilizer = stabilizer_dict[s]
                    ancilla_returned = a
                    stab_number = s
                    order_list = sorted(order_dict, key=order_dict.get)

                """ PATH BASED APPROACH
                path_list = set()
                for data in stabilizer_dict[s]:
                    src_trap = sys_state.find_trap_id_by_ion(data)
                    dest_trap = sys_state.find_trap_id_by_ion(ancilla)
                    path = self.router.find_route(src_trap, dest_trap)
                    for p in path:
                        path_list.add(p)
                length = len(path_list)
                if (length < lowest):
                    lowest = length
                    best_stabilizer = stabilizer_dict[s]
                    ancilla_returned = a
                    stab_number = s
                """
        assert(len(order_list) == len(best_stabilizer))
        #if (len(ancilla) == 6):
        print("RETURNING ORDER LIST", order_list)
        return best_stabilizer, ancilla_returned, lowest, stab_number, order_list
    
    def find_gate_from_gate_info(self, a, d, original_ancilla, x_direction, z_direction):
        ret_val = None
        print("ancilla is", a)
        print("data is", d)
        case1 = False
        case2 = False
        if (a != original_ancilla):
            print("GOT TO HERE", a, d, original_ancilla)
        for g in self.gate_info:
            x = self.gate_info[g]
            if (x_direction):
                if (x[0] == original_ancilla and x[1] == d):
                    ret_val = g
                    case1 = True
                    break
            if (z_direction):
                if (x[1] == original_ancilla and x[0] == d):
                    ret_val = g
                    case2 = True
                    break
        if (a != original_ancilla):
            if (case1):
                self.gate_info[g] = [a, d]
            else:
                assert(case2)
                self.gate_info[g] = [d, a]
        assert(ret_val != None)
        return ret_val