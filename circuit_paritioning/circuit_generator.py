from qiskit import QuantumCircuit
import customScheduler
#from machine import Machine, MachineParams, Trap, Segment
#from test_machines import *


def parse_to_tuple(matrix, n): #n is the n in [[n,k,d]]
    arr = matrix.split("\n")
    x_arr = []
    z_arr = []
    cx_arr = []
    for x in arr:
        x_temp = []
        z_temp = []
        cx_temp = []
        splits = x.split("|")
        for i in range(len(splits)): #2 times
            side = splits[i]
            nums = side.split(" ")
            print("nums", nums)
            assert(len(nums) == n)
            for j in range(len(nums)):
                number = nums[j]
                number = number.replace("[", "")
                number = number.replace("]", "")
                #print("number", number)
                if (int(number) == 1):
                    if (i == 0):
                        x_temp.append(j)
                    else:
                        assert(i == 1)
                        z_temp.append(j)
                    if (j not in cx_temp):
                        cx_temp.append(j)
        #print("x temp", x_temp)
        x_arr.append(x_temp)
        z_arr.append(z_temp)
        cx_arr.append(cx_temp)

    

    return (x_arr, z_arr, cx_arr, n)

def generate_circuit(name, input_tuple, numAncilla=1): #modify this later to be generate smart circuit
    x_arr, z_arr, cx_arr, n = input_tuple
    ancillas = []
    for i in range(numAncilla):
        ancilla = n + i
        ancillas.append(ancilla)
    print("ancillas", ancillas)
    circ = QuantumCircuit(n + numAncilla)
    ancilla_pointer = 0
    assert(len(x_arr) == len(z_arr))
    for i in range(len(x_arr)):
        circ.h(i)
    for row in range(len(x_arr)):
        x_gates = x_arr[row]
        z_gates = z_arr[row]
        cx_gates = cx_arr[row]
        for c in cx_gates:
            circ.cx(c, ancillas[ancilla_pointer])
        ancilla_pointer += 1
        ancilla_pointer = ancilla_pointer % len(ancillas)
    for i in range(len(x_arr)):
        circ.h(i)
    smallName = name + "_code" + str(numAncilla) + "Ancilla.qasm"
    #nameString = "no_cycles/circuits/" + name + "/" + smallName
    nameString = "../QCCDSim/DynamicRemapping/Circuits/" + smallName
    circ.qasm(formatted=True, filename=nameString)
    print("depth", circ.depth())
    return circ

def generate_batch_circuit(name, input_tuple, cycles, numAncilla=1): #modify this later to be generate smart circuit
    x_arr, z_arr, cx_arr, n = input_tuple #try difference between adding barrier, etc
    ancillas = []
    for i in range(numAncilla):
        ancilla = n + i
        ancillas.append(ancilla)
    print("ancillas", ancillas)
    circ = QuantumCircuit(n + numAncilla)
    for cycle in range(cycles):
        ancilla_pointer = 0
        assert(len(x_arr) == len(z_arr))
        for row in range(len(x_arr)):

            x_gates = x_arr[row]
            z_gates = z_arr[row]
            cx_gates = cx_arr[row]
            for x in x_gates:
                circ.x(x)
            for z in z_gates:
                circ.z(z)
            for c in cx_gates:
                circ.cx(c, ancillas[ancilla_pointer])
            ancilla_pointer += 1
            ancilla_pointer = ancilla_pointer % len(ancillas)
        #circ.barrier()
    smallName = name + "_code" + str(numAncilla) + "Ancilla.qasm"
    nameString = "cycles/circuits/Regular/" + str(cycles) + "cycles/" + name + "/" + smallName
    circ.qasm(formatted=True, filename=nameString)
    print("depth", circ.depth())
    return circ

def max_stabilizer_weight(input_tuple):
    cx_arr = input_tuple[2]
    print("cx_arr", cx_arr)
    max_length = -1
    for x in cx_arr:
        if len(x) > max_length:
            max_length = len(x)
    return max_length

def cyclone_circuit_gen(name, input_tuple, numAncilla, machine, machString):
    trap_amount = len(machine.traps)
    machNumberArr = machString.split("C")
    machNumber = int(machNumberArr[1])
    #assert(trap_amount == machNumber) #the whole partitioning algorithm would break otherwise
    #assert(numAncilla == trap_amount)
    x_arr, z_arr, cx_arr, n = input_tuple
    ancillas = []
    for i in range(numAncilla):
        ancilla = n + i
        ancillas.append(ancilla)
    #print("ancillas", ancillas)
    circ = QuantumCircuit(n + numAncilla)
    for i in range(len(cx_arr)):
        circ.h(i)
    ancilla_pointer = 0
    ancilla_assignment = {}
    cx_assignment = {}
    for i in range(len(ancillas)):
        cx_assignment[ancillas[i]] = []
    for i in range(len(cx_arr)):
        cx_assignment[ancillas[i % len(ancillas)]].append(cx_arr[i])
    init_mapping = customScheduler.get_cyclone_mapping(cx_arr, ancillas, machine, machString)
    print("init mapping is:", init_mapping)
    print("cx_assignment is", cx_assignment)
    current_mapping = init_mapping
    while (checkEmpty(cx_assignment) == False):
        print("current mapping", current_mapping)
        for x in current_mapping.keys():
            temp = current_mapping[x]
            assignment = []
            touching_ancillas = []
            for d in temp:
                 if (d not in ancillas):
                     assignment.append(d) #this is an array that includes the ancilla, it's looking for data anyway
                 elif (d in ancillas):
                     touching_ancillas.append(d)
                 else:
                     assert(0)
            for t in touching_ancillas:
                ancilla_assignment[t] = assignment
        for a in ancilla_assignment.keys():
            temp = ancilla_assignment[a]
            for d in temp:
                cx_temp = cx_assignment[a]
                #find first nonempty
                cx_first = [] #if there is no ancilla left, then we shouldn't be looking for any data from it
                for t in range(len(cx_temp)):
                    if (len(cx_temp[t]) > 0):
                        cx_first = cx_temp[t]
                        break
                if (d in cx_first):
                    circ.cx(d, a)
                    #print("got here")
                    cx_first.remove(d)
                    assert(d not in ancillas)
        current_mapping = rotate_ancillas(current_mapping, ancillas, trap_amount)
        #print("ancilla assignment", ancilla_assignment)
        #print("cx assignment dict here", cx_assignment)
        
        #when cx'ing assert that both of them are not ancillas
    #algorithm:
    #assign each ancilla to a stabilizer in cx array
    #for each iteration while all the stabilizers are incomplete, rotate the ancilla (this is the assumption that could add some more swaps/merges at the end but we have to make), then check if any of the trap qubits are in stabilizer, pop them (this might add some additional split/merges at the end)
    
    for i in range(len(cx_arr)): #ending h gates
        circ.h(i)
    smallName = name + "_code" + str(numAncilla) + "Ancilla" + str(trap_amount) + "Traps.qasm"
    nameString = "cyclone_circs" + "/" + smallName
    circ.qasm(formatted=True, filename=nameString)
    return circ

def rotate_ancillas(current_mapping, ancillas, trap_num):
    ancilla_assignment = {}
    for x in current_mapping.keys():
        for a in current_mapping[x]:
            if (a in ancillas):
                ancilla_assignment[a] = (x + 1) % trap_num
    new_mapping = {}
    #print("ancillas here", ancillas)
    for i in range(len(ancillas)):
        new_mapping[i] = []
    for x in current_mapping.keys():
        for d in current_mapping[x]:
            if (d not in ancillas):
                new_mapping[x].append(d)
    for x in ancillas:
        assignment = ancilla_assignment[x]
        #print("assignemnt", assignment)
        new_mapping[assignment].append(x)
    return new_mapping
        

#THINGS TO CHANGE ON EACH RUN
name = "7-1-3"
n_data_qubits = 7
trap_amount = 8
num_cyclone_ancilla = 8
#adjust this when using cycle: num_ions_per_region = n_data_qubits/max_weight + 2 # a ballpark for not overcrowding
cycles = 100
stabilizer_matrix = """[1 0 0 1 0 1 1|0 0 0 0 0 0 0]
[0 1 0 1 1 1 0|0 0 0 0 0 0 0]
[0 0 1 0 1 1 1|0 0 0 0 0 0 0]
[0 0 0 0 0 0 0|1 0 0 1 0 1 1]
[0 0 0 0 0 0 0|0 1 0 1 1 1 0]
[0 0 0 0 0 0 0|0 0 1 0 1 1 1]"""



#DO NOT HAVE ANY TABS, it must be left aligned all the way except for first line
#n_data_qubits = int(name[0]) DOESN'T WORK FOR DOUBLE DIGITS

def checkEmpty(dictionary):
    for x in dictionary.keys():
        outside = dictionary[x]
        for e in outside:
            if (len(e) > 0):
                return False
    return True

#n_data_qubits = 10
if (__name__ == "__main__"):
    cycle_mode = False
    cyclone_mode = False

    if (not(cyclone_mode)):
        if (cycle_mode):
            input_tuple = parse_to_tuple(stabilizer_matrix, n_data_qubits)
            max_weight = max_stabilizer_weight(input_tuple) #this doesn't matter anymore
            rows = len(input_tuple[2])
            #print("Max stabilizer weight", max_weight)
            print("Rows", rows)
            #print("Max stabilizer weight", max_weight)
            i = 1
            while (i <= rows):
                generate_batch_circuit(name, input_tuple, cycles, numAncilla=i)
                i += 1
            print("Successfully created " + str(rows) + " circuits!")
        else:
            input_tuple = parse_to_tuple(stabilizer_matrix, n_data_qubits)
            max_weight = max_stabilizer_weight(input_tuple) #this doesn't matter anymore
            rows = len(input_tuple[2])
            #print("Max stabilizer weight", max_weight)
            print("Rows", rows)
            i = 1
            while (i <= rows):
                generate_circuit(name, input_tuple, numAncilla=i)
                i += 1
            print("Successfully created " + str(rows) + " circuits!")
    else:
        input_tuple = parse_to_tuple(stabilizer_matrix, n_data_qubits)
        max_weight = max_stabilizer_weight(input_tuple) #this doesn't matter anymore
        rows = len(input_tuple[2])
        #print("Max stabilizer weight", max_weight)
        print("Rows", rows)
        #temporary:
        trap_amount = rows
        num_cyclone_ancilla = rows
        #num_ions_per_region = int(n_data_qubits/max_weight) + 2 # a ballpark for not overcrowding
        num_ions_per_region = 4
        print("Max capacity used", num_ions_per_region)

        machStart = "C"
        i = 2
        mpar_model1 = MachineParams()
        mpar_model1.alpha = 0.003680029
        mpar_model1.beta = 39.996319971
        mpar_model1.split_merge_time = 80
        mpar_model1.shuttle_time = 5
        mpar_model1.junction2_cross_time = 5
        mpar_model1.junction3_cross_time = 100
        mpar_model1.junction4_cross_time = 120
        mpar_model1.gate_type = "FM"
        mpar_model1.swap_type = "GateSwap"
        mpar_model1.ion_swap_time = 42
        m = make_circle_machine_length_n(num_ions_per_region, mpar_model1, trap_amount)
        machString = machStart + str(trap_amount)
        cyclone_circuit_gen(name=name, input_tuple=input_tuple, machine = m, machString=machString, numAncilla=num_cyclone_ancilla)
        print("Successfully created the circuit")
        #print(checkEmpty({0: [],1: [3,4]}))
        #print(rotate_ancillas({0: [0, 1, 5], 1: [2, 6], 2: [3, 7], 3: [4, 8]}, [5,6,7,8]))