import subprocess as sp
import os
import csv
import math

def compute_is_an_optimal_ancilla(n, name, ions): #NOT USED ANYMORE
    #ASSUMPTION: NUM_ANCILLA = NUM TRAPS because more ancilla can't parallelize
    arr = name.split("code")
    remain = arr[1]
    num = remain.split("Ancilla")[0]
    number = int(num)
    ions = int(ions) + 2 #get the real trap capacity
    amount = math.ceil((n + number)/ions)
    return amount == number

def find_optimal_ancilla(n, ions):
    #new thing
    #return 1
    ions = int(ions) + 2
    for i in range(n): #stabilizer rows = n - k, columns = 2n
        if (math.ceil((i + n)/ions) == i):
            return i
def checkAncilla(optimal, name):
    arr = name.split("code")
    remain = arr[1]
    num = remain.split("Ancilla")[0]
    number = int(num)
    return number == optimal

def checkModAncilla(optimal, name, stepsize):
    arr = name.split("code")
    remain = arr[1]
    num = remain.split("Ancilla")[0]
    number = int(num)
    step = optimal/stepsize
    valid = []
    for i in range(1, stepsize + 1):
        valid.append(int(step * i))
    return number in valid

#PROG=["programs/5-1-3_code1Ancilla.qasm", "programs/5-1-3_code2Ancilla.qasm"]

filename = "TestingGithubSetup"
#PROG_FOLDER = "5-1-3" ###CHANGEABLE LINES
#n = 5 ###CHANGEABLE LINES
csv_string = f"{filename}.csv"
#n = int(PROG_FOLDER[0]) can't use this if double digit n


PROG=[]

#TODO: Put in line that makes a difference at hyperbolic codes: k = int(circ.split("-"[1])), ITS NOT MINUS 1

###COLOR CODES

arr = os.listdir("Circuits/CodeFamilies/ColorCodes/")
for x in arr:
    #arr = x.split("Circuits/Circuits/")
    circ = x
    n = int(circ.split("-")[0])
    max_ancillas = n - 1
    ancilla_of_circuit = circ.split("_code")[1] 
    real_ancilla_of_circuit = int(ancilla_of_circuit.split("Ancilla")[0])
    if (real_ancilla_of_circuit == 1 or real_ancilla_of_circuit == round(0.2 * max_ancillas) or real_ancilla_of_circuit == round(0.4 * max_ancillas) or real_ancilla_of_circuit == round(0.6 * max_ancillas) or real_ancilla_of_circuit == round(0.8 * max_ancillas) or real_ancilla_of_circuit == max_ancillas):
    #if (real_ancilla_of_circuit == max_ancillas or real_ancilla_of_circuit == 1):
    #if (n <= 18):
        if (n != 217 and not(real_ancilla_of_circuit == max_ancillas or real_ancilla_of_circuit == 1)): #TOGGLE THIS ONE BACK ON AFTER DELETING BELOW IF EVER RUNNING AGAIN
            PROG.append("Circuits/CodeFamilies/ColorCodes/" + x)



###STABILIZER CODES
"""
arr = os.listdir("Circuits/Arbitrary_Stabilizer/")
for x in arr:
    lines = [
    "5-1-3",
    "8-2-3",
    "10-1-4",
    "11-1-5",
    "12-2-4",
    "13-1-5",
    "14-2-5",
    "15-1-5",
    "16-2-6",
    "17-1-7",
    "19-1-7",
    "20-2-6",
    "21-1-7",
    "23-2-7",
    "25-1-9"]
    #arr = x.split("Circuits/Circuits/")
    circ = x
    n = int(circ.split("-")[0])
    k = int(circ.split("-")[1])
    d = int(circ.split("-")[2].split("_code")[0])
    max_ancillas = n - k
    ancilla_of_circuit = circ.split("_code")[1] 
    real_ancilla_of_circuit = int(ancilla_of_circuit.split("Ancilla")[0])
    if (real_ancilla_of_circuit == 1 or real_ancilla_of_circuit == round(0.2 * max_ancillas) or real_ancilla_of_circuit == round(0.4 * max_ancillas) or real_ancilla_of_circuit == round(0.6 * max_ancillas) or real_ancilla_of_circuit == round(0.8 * max_ancillas) or real_ancilla_of_circuit == max_ancillas):
    #if (real_ancilla_of_circuit == max_ancillas):
        if (f"{n}-{k}-{d}" in lines):
            PROG.append("Circuits/Arbitrary_Stabilizer/" + x)
"""


###SURFACE CODES
"""
arr = os.listdir("Circuits/CodeFamilies/SurfaceCodes/")
for x in arr:
    #arr = x.split("Circuits/Circuits/")
    circ = x
    n = int(circ.split("-")[0])
    max_ancillas = n - 1
    ancilla_of_circuit = circ.split("_code")[1] 
    real_ancilla_of_circuit = int(ancilla_of_circuit.split("Ancilla")[0])
    if (real_ancilla_of_circuit == 1 or real_ancilla_of_circuit == round(0.2 * max_ancillas) or real_ancilla_of_circuit == round(0.4 * max_ancillas) or real_ancilla_of_circuit == round(0.6 * max_ancillas) or real_ancilla_of_circuit == round(0.8 * max_ancillas) or real_ancilla_of_circuit == max_ancillas):
        if (real_ancilla_of_circuit == max_ancillas or real_ancilla_of_circuit == 1):
            PROG.append("Circuits/CodeFamilies/SurfaceCodes/" + x)
"""




"""
arr = os.listdir("Circuits/CodeFamilies/HyperbolicSurfaceCodes/")
for x in arr:
    #arr = x.split("Circuits/Circuits/")
    circ = x
    n = int(circ.split("-")[0])
    max_ancillas = n - 1
    ancilla_of_circuit = circ.split("_code")[1] 
    real_ancilla_of_circuit = int(ancilla_of_circuit.split("Ancilla")[0])
    #if (real_ancilla_of_circuit == 1 or real_ancilla_of_circuit == round(0.2 * max_ancillas) or real_ancilla_of_circuit == round(0.4 * max_ancillas) or real_ancilla_of_circuit == round(0.6 * max_ancillas) or real_ancilla_of_circuit == round(0.8 * max_ancillas) or real_ancilla_of_circuit == max_ancillas):
    #if (n <= 18):
    if (real_ancilla_of_circuit == max_ancillas):
        PROG.append("Circuits/CodeFamilies/HyperbolicSurfaceCodes/" + x)
print(PROG)

circ_lib_string = "no_cycles/circuits/" + PROG_FOLDER
arr = os.listdir(circ_lib_string)
for x in arr:
    PROG.append(circ_lib_string + "/" + x)
log_file_string = "no_cycles/logs/" + PROG_FOLDER + ".log"
"""
log_file_string = f"{filename}.log" 
output_file = open(log_file_string,'w')

#MACHINE=["G10x6"]
#machine_choices = ["L6"]



#IONS = ["3", "4", "5", "6", "7"] # max ion trap capacity should be capped at #data qubits + 1
#MACHINE = machine_choices

MAPPINGS = ["Greedy"] #TODO: Always change between Greedy and Custom as Necessary for MMO/Baseline
#mapper = "Greedy"
#mapper = "Custom"
reorder = "Naive"

#csv_string = "no_cycles/data/" + PROG_FOLDER + ".csv"


row = ["Program Name","Ions Per Trap","Machine","Mapping Choice","Number of Ancilla", "Fidelity"]
with open(csv_string, 'w', newline='') as outfile:
    writer = csv.writer(outfile)
    writer.writerow(row)


COMPILERS = ["Moveless"]
print("REAL PROG", PROG)
for p in PROG:
    split_arr = p.split("-")
    remain = split_arr[0]
    k = int(split_arr[1])
    #num = remain.split("Cycles/")[1]
    num = remain.split("Codes/")[1]
    n = int(num)
    C = n - k
    IONS = ["5"]
    
    CONSTANT = 1
    number_traps = math.ceil(C/CONSTANT)
    mach_string = "L" + str(number_traps)
    print("NUMBER OF TRAPS", number_traps)
    #IONS = ["241", "121", "81", "49", "25", "13", "9", "5"] #ions per trap (depending on the machine there are different amounts of traps, ex: L6 has 6) 
    #MACHINE = ["L1", "L2", "L3", "L5", "L10", "L20", "L30", "L50"]
    IONS = ["5"]
    #IONS.append(4)
    MACHINE=[mach_string]
    #MACHINE = ["G10x6"]


    #SPLIT_MERGES = [80, 64, 48, 32, 16]
    """
    trap_map_dict = {}
    for i in range(len(IONS)):
        trap_map_dict[IONS[i]] = MACHINE[i]
    print("trap map", trap_map_dict)
    """
    
    """
    THIS PART ABOVE IS MEANT TO SET #TRAPS =  FIXED AMOUNTS
    
    
    for i in range(3, n+2): #3->n+1 inclusive, which range takes as n+2
        IONS.append(str(i))
    """
    #print(IONS)
    #OPTIMAL_RANGE = [1,2,3,4]
    
    for i in IONS:
        #optimal = find_optimal_ancilla(n, i)
        optimal = C
        #for o in OPTIMAL_RANGE:
            #optimal = o #temporary m for sensitivity
            #if (compute_is_an_optimal_ancilla(n, p, i)):
        #if (checkModAncilla(optimal, p, 4)):
        for m in MACHINE:
            #if (trap_map_dict[i] == m):
            #for s in SPLIT_MERGES:
                for compiler in COMPILERS:
                    sp.call(["python", "run.py", p, m, i, compiler, 
                                reorder, "1", "0", "0", "FM", "GateSwap", 
                                csv_string, "80", "True"], stdout=output_file) #adjust for actual capacity




print("Done Generating Logs and CSV!")
#Do this on a different file, for parallelism
#print("Creating Plots...")

