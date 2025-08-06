import sys
from parse import InputParse
from mappers import *
from machine import Machine, MachineParams, Trap, Segment
from ejf_schedule import Schedule, EJFSchedule
from analyzer import *
from test_machines import *
import numpy as np
import customScheduler
import csv


def closest_ratio(ratio):
    targets = [0, 0.2, 0.4, 0.6, 0.8, 1]
    closest = min(targets, key=lambda x: abs(ratio - x))
    return closest

#Mapped into hand seperated containers - wanted to manually enforce 1-to-1 mappings on smaller codes.
def real_closest_ratio(name, ratio):
    ratio = round(ratio, 5)
    ratios_dict = {("7-1-3", round(2/7, 5)): 0.2, ("7-1-3", round(4/7, 5)): 0.4, 
                   ("7-1-3", round(5/7, 5)): 0.6, ("7-1-3", round(6/7, 5)): 0.8, 
                   ("7-1-3", round(6/7, 5)): 1, ("9-1-3", round(2/9, 5)): 0.2, 
                   ("9-1-3", round(3/9, 5)): 0.4, ("9-1-3", round(5/9, 5)): 0.6, 
                   ("9-1-3", round(6/9, 5)): 0.8, ("9-1-3", round(8/9, 5)): 1, 
                   ("19-1-5", round(4/19, 5)): 0.2, ("19-1-5", round(7/19, 5)): 0.4,
                   ("19-1-5", round(11/19, 5)): 0.6, ("19-1-5", round(14/19, 5)): 0.8, 
                   ("19-1-5", round(18/19, 5)): 1, ("25-1-5", round(5/25, 5)): 0.2, 
                   ("25-1-5", round(10/25, 5)): 0.4, ("25-1-5", round(14/25, 5)): 0.6, 
                   ("25-1-5", round(19/25, 5)): 0.8, ("25-1-5", round(24/25, 5)): 1, 
                   ("37-1-7", round(7/37, 5)): 0.2, ("37-1-7", round(14/37, 5)): 0.4,  
                   ("37-1-7", round(22/37, 5)): 0.6,  ("37-1-7", round(29/37, 5)): 0.8, 
                   ("37-1-7", round(36/37, 5)): 1, ("49-1-7", round(10/49, 5)): 0.2, 
                   ("49-1-7", round(19/49, 5)): 0.4, ("49-1-7", round(29/49, 5)): 0.6, 
                   ("49-1-7", round(38/49, 5)): 0.8, ("49-1-7", round(48/49, 5)): 1, 
                   ("61-1-9", round(12/61, 5)): 0.2, ("61-1-9", round(24/61, 5)): 0.4,
                   ("61-1-9", round(36/61, 5)): 0.6, ("61-1-9", round(48/61, 5)): 0.8,
                   ("61-1-9", round(60/61, 5)): 1, ("81-1-9", round(16/81, 5)): 0.2,
                   ("81-1-9", round(32/81, 5)): 0.4, ("81-1-9", round(48/81, 5)): 0.6,
                   ("81-1-9", round(64/81, 5)): 0.8, ("81-1-9", round(80/81, 5)): 1,
                   ("91-1-11", round(18/91, 5)): 0.2, ("91-1-11", round(36/91, 5)): 0.4,
                   ("91-1-11", round(54/91, 5)): 0.6, ("91-1-11", round(72/91, 5)): 0.8,
                   ("91-1-11", round(90/91, 5)): 1, ("121-1-11", round(24/121, 5)): 0.2,
                   ("121-1-11", round(48/121, 5)): 0.4, ("121-1-11", round(72/121, 5)): 0.6,
                   ("121-1-11", round(96/121, 5)): 0.8, ("121-1-11", round(120/121, 5)): 1
                   }
    return ratios_dict[(name, ratio)]

np.random.seed(12345)


#Command line args
#Machine attributes
openqasm_file_name = sys.argv[1]
machine_type = sys.argv[2]
num_ions_per_region = int(sys.argv[3])
print("num ions per region (trap capacity) is", num_ions_per_region)
compiler_mode = sys.argv[4]
reorder_choice = sys.argv[5]
serial_trap_ops = int(sys.argv[6])
serial_comm = int(sys.argv[7])
serial_all = int(sys.argv[8])
gate_type = sys.argv[9]
swap_type = sys.argv[10]
csv_string = sys.argv[11]
split_merge = int(sys.argv[12])
write_timings = sys.argv[13]
#converting from string to boolean value, only strings can be passed in subprocess
if (write_timings == "True"):
    write_timings = True
else:
    assert(write_timings == "False")
    write_timings = False

##########################################################
mpar_model1 = MachineParams()
mpar_model1.alpha = 0.003680029
mpar_model1.beta = 39.996319971
mpar_model1.split_merge_time = split_merge
mpar_model1.shuttle_time = 5
mpar_model1.junction2_cross_time = 5
mpar_model1.junction3_cross_time = 100
mpar_model1.junction4_cross_time = 120
mpar_model1.gate_type = gate_type
mpar_model1.swap_type = swap_type
mpar_model1.ion_swap_time = 42
machine_model = "MPar1"

'''
mpar_model2 = MachineParams()
mpar_model2.alpha = 0.003680029
mpar_model2.beta = 39.996319971
mpar_model2.split_merge_time = 80
mpar_model2.shuttle_time = 5
mpar_model2.junction2_cross_time = 5
mpar_model2.junction3_cross_time = 100
mpar_model2.junction4_cross_time = 120
mpar_model2.alpha
machine_model = "MPar2"
'''

print("Simulation")
print("Program:", openqasm_file_name)
print("Machine:", machine_type)
print("Model:", machine_model)
print("Ions:", num_ions_per_region)
print("Compiler:", compiler_mode)
print("Reorder:", reorder_choice)
print("SerialTrap:", serial_trap_ops)
print("SerialComm:", serial_comm)
print("SerialAll:", serial_all)
print("Gatetype:", gate_type)
print("Swaptype:", swap_type)

#Create a test machine
if machine_type == "G2x3":
    m = test_trap_2x3(num_ions_per_region, mpar_model1)
elif machine_type == "G2x6":
    m = test_trap_2x6(num_ions_per_region, mpar_model1)
elif machine_type == "L6":
    m = make_linear_machine(6, num_ions_per_region, mpar_model1)
elif machine_type == "H6":
    m = make_single_hexagon_machine(num_ions_per_region, mpar_model1)
elif machine_type[0] == "C":
    mach_arr = machine_type.split("C")
    num = mach_arr[1]
    #print("Error reading machine type, give one number")
    n = int(num)
    #print("n is", n)
    #m = make_circle_machine_4(num_ions_per_region, mpar_model1)
    m = make_circle_machine_length_n(num_ions_per_region, mpar_model1, n)
elif machine_type == "L8":
    m = make_linear_machine(8, num_ions_per_region, mpar_model1)
elif machine_type[0] == "L":
    nums = machine_type.split("L")
    num = nums[1]
    n_traps = int(num)
    m = make_linear_machine(n_traps, num_ions_per_region, mpar_model1)
elif (machine_type == "G10x6"):
    m = grid_10x6(num_ions_per_region, mpar_model1)
elif (machine_type[:2] == "GR"):
    remove_number = int(machine_type[2:])
    m = grid_removed(remove_number, num_ions_per_region, mpar_model1)
else:
    print("machine type was", machine_type)
    assert 0

"""
for x in m.junctions:
    print("junction", x.id)
    print(m.junction_cross_time(x))
"""

#Parse the input program DAG
ip = InputParse()
ip.parse_ir(openqasm_file_name)


#Map the program onto the machine regions
#For every program qubit, this gives a region id
qm = QubitMapGreedy(ip, m)
mapping = qm.compute_mapping()

#print("how mapping is SUPPOSED to look like", mapping)


#ending_name = openqasm_file_name.split("Circuits/")[1]
#ending_name = openqasm_file_name.split("Cycles/")[1]

ending_name = openqasm_file_name.split("Codes/")[1]
num_ancilla = int(openqasm_file_name.split("_code")[1].split("Ancilla")[0])
n = int(ending_name.split("-")[0])
k = int(ending_name.split("-")[1])
d = int(ending_name.split("-")[2].split("_code")[0])


#Reorder qubits within a region to increse the use of high fidelity operations
if compiler_mode == "Baseline":
    init_qubit_layout = mapping
elif compiler_mode == "Moveless" or compiler_mode == "MAO": #now it's changed to something meaningful
    if (machine_type == "G10x6"):
        print("For a grid, using greedy mapping...")
        init_qubit_layout = mapping
    else:
        init_qubit_layout = customScheduler.get_custom_mapping(openqasm_file_name, m, machine_type)
    #except:
        #init_qubit_layout = mapping
else:
    qo = QubitOrdering(ip, m, mapping)
    if reorder_choice == "Naive":
        init_qubit_layout = qo.reorder_naive()
    elif reorder_choice == "Fidelity":
        init_qubit_layout = qo.reorder_fidelity()
    else:
        assert 0


ejfs = EJFSchedule(ip.gate_graph, ip.cx_gate_map, m, init_qubit_layout, serial_trap_ops, serial_comm, serial_all)
if (compiler_mode == "Moveless"):
    ejfs.run_enhancement(openqasm_file_name, dynamic_scheduling=True, stabilizer_mode=False)
elif (compiler_mode == "MAO"):
    ejfs.run_enhancement(openqasm_file_name, dynamic_scheduling=False, stabilizer_mode=False)
else:
    assert(compiler_mode == "Baseline")
    ejfs.run()

print("Ending machine state", ejfs.sys_state.trap_ions)


#Analyze the output schedule and print statistics

name = f"{str(n)}-{str(k)}-{str(d)}"

if (num_ancilla == 1):
    ratio_num = -1
else:
    ratio_num = real_closest_ratio(name, num_ancilla/n)
if (ratio_num == -1):
    ratio_string = "1m"
elif (ratio_num == 1):
    ratio_string = "maxm"
else:
    ratio_string = str(ratio_num) + "m"

print("Ratio string", ratio_string)

#Custom code if we want to print timings for a baseline - can comment out


"""
print("ending name", ending_name)
machNumber = -1
if machine_type == "G10x6":
    machNumber = 1
elif machine_type[0] == "C":
    machNumber = 2
elif machine_type[0] == "L":
    machNumber = 3 
assert(machNumber != -1)
"""

#UNCOMMENT/RECOMMENT TOGGLE ON THESE NEXT FEW LINES FOR TIMINGS FILES OR NOT
"""
timings_file_name = "QCE_Dynamic_Timings/" + ratio_string + "/" + ending_name.split(".qasm")[0] + ".pkl" 
#timings_file_name = "Sensitivity_Timings/" + str(machNumber) + "_machine" + "/" + ending_name.split(".qasm")[0] + ".pkl" 
analyzer = Analyzer(ejfs.schedule, m, init_qubit_layout, True, timings_file_name)
"""
if (compiler_mode == "Moveless" and write_timings == True):
    timings_file_name = "Demo_Moveless_Timings/" + ratio_string + "/" + ending_name.split(".qasm")[0] + ".pkl"
    analyzer = Analyzer(ejfs.schedule, m, init_qubit_layout, True, timings_file_name)
elif (compiler_mode == "MAO" and write_timings == True):
    timings_file_name = "Demo_MAO_Timings/" + ratio_string + "/" + ending_name.split(".qasm")[0] + ".pkl"
    analyzer = Analyzer(ejfs.schedule, m, init_qubit_layout, True, timings_file_name)
elif (compiler_mode == "Baseline" and write_timings == True):
    timings_file_name = "Demo_Baseline_Timings/" + ratio_string + "/" + ending_name.split(".qasm")[0] + ".pkl"
    analyzer = Analyzer(ejfs.schedule, m, init_qubit_layout, True, timings_file_name)
else:
    assert(write_timings == False) #No write timings support for MAO yet, it is unnecessary. 
    analyzer = Analyzer(ejfs.schedule, m, init_qubit_layout)

fidelity, execution_time = analyzer.move_check()
print("SplitSWAP:", ejfs.split_swap_counter)
num_ancilla = customScheduler.countAncilla(openqasm_file_name)
row = [openqasm_file_name, num_ions_per_region, machine_type, compiler_mode, num_ancilla, fidelity, execution_time]
print("ROW", row)
with open(csv_string, 'a', newline='') as outfile:
    writer = csv.writer(outfile)
    #reader = csv.reader(outfile, delimiter=' ')
    #for x in reader:
    writer.writerow(row)


#analyzer.print_events()
print("----------------")
