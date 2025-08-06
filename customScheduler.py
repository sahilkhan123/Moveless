import sys
from qiskit import QuantumCircuit
import os

from circuit_paritioning.partitioning.partitioners.dynamic.merge_dynamic_partitioner import MergeDynamicPartitioner
from circuit_paritioning.partitioning.partitioners.dynamic.best_fixed_slice_partitioner import BestFixedSlicePartitioner
from circuit_paritioning.partitioning.partitioners.partitioner import PartitionerArgs
from circuit_paritioning.partitioning.partitioners.dynamic.fine_grained_partitioner import FineGrainedPartitioner
import math

def assert_unique_integers(dictionary):
    all_values = [item for sublist in dictionary.values() for item in sublist]
    print("all values", all_values)
    print("length of set", len(set(all_values)))
    print("length of all values")
    assert len(all_values) == len(set(all_values))


def get_cyclone_mapping_runnable(circuit_file, machine, machString):
    trap_amount = len(machine.traps)
    machNumberArr = machString.split("C")
    machNumber = int(machNumberArr[1])
    assert(trap_amount == machNumber)
    mapping_dict = {}
    data_list = getOneAncillaDataOrder(circuit_file)
    for i in range(trap_amount):
        mapping_dict[i] = []
    for i in range(len(data_list)):
        #NAIVE MAPPING - REPLACE WITH FIXED PARTITIONER
        mapping_dict[i % trap_amount].append(data_list[i])
    ancillas = getAncillaBits(circuit_file=circuit_file)
    #later add ancilla
    for i in range(len(ancillas)): #attempting to fix with mod because I originally wanted num_ancilla must be = num_traps
        mapping_dict[i % trap_amount].append(ancillas[i])

    return mapping_dict

def get_cyclone_mapping(cx_arr,ancillas, machine, machString):
    trap_amount = len(machine.traps)
    machNumberArr = machString.split("C")
    machNumber = int(machNumberArr[1])
    #assert(trap_amount == machNumber)
    mapping_dict = {}
    data_list = get_data_from_cx_arr(cx_arr=cx_arr)
    for i in range(trap_amount):
        mapping_dict[i] = []
    for i in range(len(data_list)):
        #NAIVE MAPPING - REPLACE WITH FIXED PARTITIONER
        mapping_dict[i % trap_amount].append(data_list[i])
    
    #later add ancilla
    for i in range(len(ancillas)): #attempting to fix with mod because I originally wanted num_ancilla must be = num_traps
        mapping_dict[i % trap_amount].append(ancillas[i])

    return mapping_dict

def get_sensitivity_cyclone_mapping(cx_arr,ancillas, machine, machString, ions):
    trap_amount = len(machine.traps)
    machNumberArr = machString.split("C")
    machNumber = int(machNumberArr[1])
    #assert(trap_amount == machNumber)
    mapping_dict = {}
    data_list = get_data_from_cx_arr(cx_arr=cx_arr)
    for i in range(trap_amount):
        mapping_dict[i] = []
    for i in range(len(data_list)):
        #NAIVE MAPPING - REPLACE WITH FIXED PARTITIONER
        mapping_dict[i % trap_amount].append(data_list[i])
    
    #later add ancilla
    for i in range(len(ancillas)): #attempting to fix with mod because I originally wanted num_ancilla must be = num_traps
        mapping_dict[i % trap_amount].append(ancillas[i])
    
    for x in mapping_dict.keys():
        pass
        #assert(len(mapping_dict[x]) <= ions) #otherwise we have exceeded maximum capacity. Above algorithm guarantees maximum dispersity of ions so that means something is wrong with numerics.
    
    return mapping_dict


def get_custom_mapping(circuit_file, machine, machString):
    circuit = QuantumCircuit.from_qasm_file(circuit_file)
    partitions = get_jonathan_mapping(circuit_file, machine, machString)
    sets = []
    trap_layout = machine.traps
    k = len(trap_layout)
    p = trap_layout[0].capacity
    #print("k is", k)
    #print("p is ", p)
    ancilla_num = countAncilla(circuit_file)
    if (ancilla_num == 1):
        ancilla_list = getAncillaBits(circuit_file)
        assert(len(ancilla_list) == 1)
        ancilla = ancilla_list[0]
        data_list = getOneAncillaDataOrder(circuit_file) #TODO: this is the problem: 11/7/24
        print("data list", data_list)
        print("ancilla", ancilla)
        for i in range(k): 
            x = 0
            set_single = []
            if (len(data_list) == 0): #this should happen most of the time
                break
            if (i == 0):
                while (x < p - 1 and len(data_list) > 0):
                    next_data = data_list.pop(0)
                    set_single.append(next_data)
                    x +=1 
                set_single.append(ancilla)
                #print("set single here: ", set_single)
            else:
                while (x < p and len(data_list) > 0):
                    next_data = data_list.pop(0)
                    set_single.append(next_data)
                    x +=1
            sets.append(set_single)

            
        
        #since data_list is a queue, now fill sets in order (while sets length is trap size - 1 fill data? Then add ancilla)

    else:
        #TODO: here's where I fill in the greedy partitions instead
        for x in partitions.keys():
            if (len(partitions[x]) != 0):
                sets.append(partitions[x])
        #print("sets", sets)
    if (machString == "G2x3"):
        fill_order = [0,5,1,4,2,3] #spread but in a certain order
    elif (machString == "H6"):
        #fill_order = [0,2,4,1,3,5] #spread apart
        fill_order = [0,1,2,3,4,5]
    else: #L6 case and others put close together
        #print("sets right here", sets)
        #print("k is ", k)
        nums = machString.split("L") ###INTERCHANGED BETWEEN L AND C DEPENDING ON WHICH MACHINE - 4/3/25
        num = nums[1]
        total_traps = int(num)
        new_sets = []
        i = p
        while (i >= 0):
            for x in sets:
                if len(x) == i:
                    new_sets.append(x)
            i -= 1
        sets = new_sets
        fill_order = [s for s in range(total_traps)] #pack together

    initial_mapping = {}
    assert(len(sets) <= len(fill_order))
    for i in range(len(fill_order)):
        if (i < len(sets)):
            initial_mapping[fill_order[i]] = sets[i]
        else:
            break
    assert(len(sets) == len(initial_mapping.keys()))
    assert(len(sets) != 0)
    for i in range(len(fill_order)):
        if (i not in initial_mapping.keys()):
            initial_mapping[i] = []
    """
    The custom one ancilla case
    if (machString == "G2x3"):
        initial_mapping = {0 : [0, 2, 5], 1: [], 2:[1], 3:[3], 4:[4], 5:[]} #spread a little?
    elif (machString == "H6"):
        initial_mapping= {0 : [0, 2, 5], 1: [], 2:[1], 3:[3], 4:[4], 5:[]} #spread apart (circular as well)
    else:
        initial_mapping = {0 : [0, 2, 5], 1: [1,3,4], 2:[], 3:[], 4:[], 5:[]} #pack together, in one ancilla case follow my own partition, not Jonathan's
    """

    print("initial mapping custom", initial_mapping)
    #print("full schedule parsed", full_schedule)
    assert_unique_integers(initial_mapping)
    return initial_mapping
    #return initial_layout_dict

def get_jonathan_mapping(circuit_file, machine, machString):
    
    circuit = QuantumCircuit.from_qasm_file(circuit_file)
    trap_layout = machine.traps
    #k = len(trap_layout)
    p = trap_layout[0].capacity
    ancilla_num = countAncilla(circuit_file)
    data_num = len(getOneAncillaDataOrder(circuit_file=circuit_file))
    total = data_num + ancilla_num
    print("CIRCUIT FILE IS", circuit_file)
    print("data num is", data_num)
    print("ancilla num is", ancilla_num)
    k = math.ceil(total/p)
    print("k", k)
    print("p", p)
    pargs = PartitionerArgs.from_circuit(circuit, k=k, p=p) #get k, p from machine number of buckets, size of each
    res = FineGrainedPartitioner().partition_circuit(pargs)
    unparsed_path = res.path
    #print("unparsed full schedule: ", unparsed_path)
    initial_layout_unparsed = unparsed_path[0]
    initial_layout_dict = {}
    full_schedule = {}
    for i in range(k):
        qubits = initial_layout_unparsed[i]
        order = []
        for x in qubits:
            order.append(x)
        initial_layout_dict[i] = order
    full_schedule = []
    for path in range(len(unparsed_path)):
        layout_dict = {}
        for i in range(k):
            qubits = unparsed_path[path][i]
            order = []
            for x in qubits:
                order.append(x)
        layout_dict[i] = order
        full_schedule.append(layout_dict)
    #print("unparsed path", unparsed_path)
    print("parsed initial mapping for jonathan", initial_layout_dict)
    #print("full schedule parsed", full_schedule)
    return initial_layout_dict

def countAncilla(circuit_file_name):
    try:
        assert("Ancilla" in circuit_file_name)
        assert("_code" in circuit_file_name)
        num = int(circuit_file_name.split("Ancilla")[0].split("_code")[1]) #this works as long as there's not 100 ancilla
        return num
    except:
        print("Invalid circuit name!")
        exit()
    

def getAncillaBits(circuit_file): #this probably doesn't work if the ancilla is ten
    circ = QuantumCircuit.from_qasm_file(circuit_file)
    ancilla_list = []
    n = int(circuit_file.split("-")[0].split("/")[-1])
    for x in circ.get_instructions("cx"):
        target = circ.find_bit(x.qubits[1])[0]
        source = circ.find_bit(x.qubits[0])[0]
        if (source not in ancilla_list and source >= n):
            ancilla_list.append(source)
        if (target not in ancilla_list and target >= n):
            ancilla_list.append(target)
        assert(source not in ancilla_list or target not in ancilla_list) #if both are in ancilla list, something is wrong
    return ancilla_list
    
def getOneAncillaDataOrder(circuit_file):
    """
    circ = QuantumCircuit.from_qasm_file(circuit_file)
    data_list = []
    for x in circ.get_instructions("cx"):
        data = circ.find_bit(x.qubits[0])[0]
        if (data not in data_list):
            data_list.append(data)
    return data_list
    """
    circ = QuantumCircuit.from_qasm_file(circuit_file)
    data_list = []
    n = int(circuit_file.split("-")[0].split("/")[-1])
    for x in circ.get_instructions("cx"):
        target = circ.find_bit(x.qubits[1])[0]
        source = circ.find_bit(x.qubits[0])[0]
        if (source not in data_list and source < n):
            data_list.append(source)
        if (target not in data_list and target < n):
            data_list.append(target)
        assert(source not in data_list or target not in data_list) #if both are in ancilla list, something is wrong
    return data_list


def get_data_from_cx_arr(cx_arr):
    data = []
    for x in cx_arr:
        for d in x:
            if (d not in data):
                data.append(d)
    return data   

#print(countAncilla("no_cycles/circuits/5-1-3/5-1-3_code1Ancilla.qasm"))
#print(countAncilla("no_cycles/circuits/10-1-4/10-1-4_code1Ancilla.qasm"))
#print(getAncillaBits("no_cycles/circuits/10-1-4/10-1-4_code8Ancilla.qasm"))
#print(get_data_from_cx_arr([[1,2,3,4], [0,4,2,3], [1,3,4,5]]))