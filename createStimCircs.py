import circuit_generator
import pickle as pkl
import math
import copy
import os 

def reverse_2d_array(arr):
    # Reverse the order of the 1D arrays and reverse each 1D array
    return [row[::-1] for row in arr[::-1]]

def calculate_pauli_twirling(t, p):
   

    #endpoints used for fitting were 1e-4 - 1e-3, with 100 and 10s coherence times respectively
    #  
    #formula for log T1: ln(T1) = -0.99998246709278*ln(p) + 9.2104211120632
    #formula for log T2: ln(T2) = -0.99998246709278x + 9.2104211120632 # let's inject equal t1, t2
    
    if (p != 0):
        logT1 = -0.99998246709278*math.log(p) + 9.2104211120632
        logT2 = -0.99998246709278*math.log(p) + 9.2104211120632
        T1 = math.exp(logT1)
        T2 = math.exp(logT2)
        x = (1 - math.exp(-t/T1))/4
        y = x
        z = (1-math.exp(-t/T2))/2 - (1 - math.exp(-t/T1))/4
        return x, y, z
    else: #don't fit on no error, only used for debugging/checking correctness (0 p phys gives expected LER)
        return 0, 0, 0
    
def check_color(color_dict, stabilizer):
    color = -1
    found = False
    #print("color dict", color_dict)
    #print("stabilizer", stabilizer)
    for x in color_dict.keys():
        #if (stabilizer in color_dict[x] or stabilizer[::-1] in color_dict[x]):
        if (any(set(stabilizer) == set(stabilizer_generator) for stabilizer_generator in color_dict[x])):
            assert(found != True)
            color = x
            found = True
    assert(color != -1)
    return color


def createStimBaselineandSOA(file_path, cx_lists, cx_timings, p, distance, stabilizer_matrix, surface_code=True, color_metadata=None, numAncilla=1, sensitivity_wildcard=None):
    NUM_CYCLES = distance * 10
    z_ancillas = []
    #assert(len(cx_timings) == len(cx_lists) + 2) #for both sets of h gates - this is the structure of the timing in time slices: H| ... gates ... | H
    #print("total time", sum(cx_timings))
    #("file path", file_path)
    name_arr = file_path.split("-")
    k = int(name_arr[1])
    if (sensitivity_wildcard == None):
        n = int(name_arr[0].split("m/")[1])
    else:
        print(name_arr[0].split(sensitivity_wildcard + "/"))
        n = int(name_arr[0].split(sensitivity_wildcard + "/")[1])
    total_time = sum(cx_timings) + (n - 1) * 100 #add in measurement delay 
    x_s, z_s, cx_arr , _ = circuit_generator.parse_to_tuple(stabilizer_matrix, n)
    #print("x's", x_s)
    #print("z's", z_s)
    data = []
    ancilla = []
    interval = n + (numAncilla)
    data_string = ""
    ancilla_string = ""
    for i in range(int(interval)):
        if (i < n):
            data.append(i)
            data_string += str(i) + " "
        else:
            ancilla.append(i)
            ancilla_string += str(i) + " "
    if (not(surface_code)): #do some preprocessing, COLOR DICT LOOKS COMPLETELY DIFFERENT IN THE BASELINE/SOA VERSION
        color_dict = {}
        for i in range(3):
            color_dict[i] = []
        for i in range(len(cx_arr)): 
            color_dict[color_metadata[i]].append(cx_arr[i])
    #print("cx arr", cx_arr)

    #print("color_dict", color_dict)
    ancilla_dict = {}
    for x in ancilla:
        ancilla_dict[x] = []
    counter_pointer = 0
    for i in range(len(z_s)):
        if (len(z_s[i]) > 0):
            ancilla_dict[ancilla[counter_pointer % len(ancilla)]] = z_s[i]
            counter_pointer += 1

    #NOW INITIALIZATION COMPLETE, CREATING THE CIRUIT
    master_measurement = []


    with open(file_path, 'w') as file:
        tabString = "" #tab string is the part of the file that will later be indented. Since it is a copy, it is easier to write simultaneously.
        errorX, errorY, errorZ = calculate_pauli_twirling(total_time, p)

        #First put cycle errors off pauli twirling from Cyclone/Naive compiler
        file.write("X_ERROR(" + str(errorX) + ") " + data_string + ancilla_string + "\n")
        tabString += "  X_ERROR(" + str(errorX) + ") " + data_string + ancilla_string + "\n"
        file.write("Y_ERROR(" + str(errorY) + ") " + data_string + ancilla_string + "\n")
        tabString += "  Y_ERROR(" + str(errorY) + ") " + data_string + ancilla_string + "\n"
        file.write("Z_ERROR(" + str(errorZ) + ") " + data_string + ancilla_string + "\n")
        tabString += "  Z_ERROR(" + str(errorZ) + ") " + data_string + ancilla_string + "\n"
       

        #Now time for CNOTS
        #print("cx lists", cx_lists)
        Z_check_ready = False
        Z_check_done = False
        #print("z ancillas", z_ancillas)
        #print("ancilla", ancilla)
        #print("cx lists", cx_lists)
        tup_count = 0
        X_check_count = 0
        total_checks = 0
        #print(stabilizer_matrix)
        #print("cx arr", cx_arr)
        for array in cx_arr:
            for check in array:
                total_checks += 1
        assert(total_checks // 2 == total_checks / 2)
        copy_CX_x = copy.deepcopy(x_s)
        building_cx_x = {} #7:[1,2,3,4]
        for b in range(numAncilla):
            building_cx_x[b + n] = []
        copy_CX_z = copy.deepcopy(z_s)
        building_cx_z = {} #7:[1,2,3,4]
        for b in range(numAncilla):
            building_cx_z[b + n] = []
        #do measurements after the checks
        #print("num Ancilla", numAncilla)
        for layer in cx_lists:
            used = []
            cx_layer_string_x = ""
            cx_layer_string_z = ""
            measure_ancilla_string_x = ""
            measure_ancilla_string_z = ""
            for tup in layer:
                source = tup[0]
                target = tup[1] #another way of saying ancilla
                if (source > target):
                    if (len(building_cx_x[source]) == 0):
                        H_string = "H "
                        H_string += str(source) + " "
                        file.write(H_string + "\n")
                        tabString += "  " + H_string + "\n"
                    building_cx_x[source].append(target)
                    cx_layer_string_x += str(source) + " "
                    cx_layer_string_x += str(target) + " "
                else:
                    building_cx_z[target].append(source)
                    cx_layer_string_z += str(source) + " "
                    cx_layer_string_z += str(target) + " "
                    
                    
                    
                
                
                
                used.append(source)
                used.append(target)
                        
            measurement_xs = [] 
            measurement_zs = []
            #print("HIT HERE AT END OF LAYER")
            #print("building cx x", building_cx_x)
            #print("building cx z", building_cx_z)
            #print("length", len(building_cx_x[list(building_cx_x.keys())[0]]))
            #print("copy CX x", copy_CX_x)
            #print("copy CX z", copy_CX_z)
            
            for pos in building_cx_x.keys():
                if (len(building_cx_x[pos]) > 0):
                    for stabilizer_generator in copy_CX_x:
                        if set(stabilizer_generator) == set(building_cx_x[pos]):
                            measurement_xs.append(pos)
                            copy_CX_x.remove(stabilizer_generator)
                            measure_ancilla_string_x += str(pos)
                            measure_ancilla_string_x += " "
                            master_measurement.append(("X", pos, building_cx_x[pos]))
                            building_cx_x[pos] = [] # for ancilla reuse case we need to reset it to nothing
                            break  # Exit the loop since we found a match
            for pos in building_cx_z.keys():
                if (len(building_cx_z[pos]) > 0):
                    for stabilizer_generator in copy_CX_z:
                        if set(stabilizer_generator) == set(building_cx_z[pos]): 
                            measurement_zs.append(pos)
                            copy_CX_z.remove(stabilizer_generator)
                            measure_ancilla_string_z += str(pos)
                            measure_ancilla_string_z += " "
                            master_measurement.append(("Z", pos, building_cx_z[pos]))
                            building_cx_z[pos] = [] # for ancilla reuse case we need to reset it to nothing   
                            break
            file.write("CX " + cx_layer_string_x + cx_layer_string_z + "\n")
            tabString += "  CX " + cx_layer_string_x + cx_layer_string_z + "\n"
            file.write("DEPOLARIZE2(" + str(p) + ") " + cx_layer_string_x + cx_layer_string_z + "\n")
            tabString += "  " + "DEPOLARIZE2(" + str(p) + ") " + cx_layer_string_x + cx_layer_string_z + "\n"
            if (len(measurement_xs) > 0): #assumes we CAN finish an X and a Z in a parallel step
                    H_string = "H "
                    H_string += measure_ancilla_string_x + " " #assumes never measuring an x and a z stabilizer in same step
                    file.write(H_string + "\n")
                    tabString += "  " + H_string + "\n"
                ###QUEUE a  measurement and reset of the ancilla here
                    file.write("X_ERROR(" + str(p) + ") " + measure_ancilla_string_x + "\n")
                    tabString += "  " + "X_ERROR(" + str(p) + ") " + measure_ancilla_string_x + "\n"
                    file.write("MR " + measure_ancilla_string_x + "\n")
                    tabString += "  " + "MR " + measure_ancilla_string_x + "\n"
                    reset_error = p/10
                    file.write("X_ERROR(" + str(reset_error) + ") " + measure_ancilla_string_x + "\n")
                    tabString += "  " + "X_ERROR(" + str(reset_error) + ") " + measure_ancilla_string_x + "\n"
                    depolarize_after_h = p/10
                    depolarize_after_h_string = "DEPOLARIZE1(" + str(depolarize_after_h) + ") "
                    for i in ancilla:
                        depolarize_after_h_string += str(i) + " "
                    depolarize_after_h_string += "\n"
                
                ###QUEUE a  measurement and reset of the ancilla here
                    
            if (len(measurement_zs) > 0):
                file.write("X_ERROR(" + str(p) + ") " + measure_ancilla_string_z + "\n")
                tabString += "  " + "X_ERROR(" + str(p) + ") " + measure_ancilla_string_z + "\n"
                file.write("MR " + measure_ancilla_string_z + "\n")
                tabString += "  " + "MR " + measure_ancilla_string_z + "\n"
                reset_error = p/10
                file.write("X_ERROR(" + str(reset_error) + ") " + measure_ancilla_string_z + "\n")
                tabString += "  " + "X_ERROR(" + str(reset_error) + ") " + measure_ancilla_string_z + "\n"
                
            unused = []
            for i in data:
                if (i not in used):
                    unused.append(i)
            for i in ancilla:
                if (i not in used):
                    unused.append(i)
            unused_string = ""
            for i in unused:
                unused_string += str(i) + " "
            depolarize_unused_cx = p/10
            tup_count += 1
        
        if (surface_code):
            for i in range(len(master_measurement)):
                    if (master_measurement[i][0] == "Z"):
                        number = -len(master_measurement) + i
                        file.write("DETECTOR(0,0,0,0) " + "rec[" + str(number) + "]\n")
        else:
            for i in range(len(master_measurement)):
                    if (master_measurement[i][0] == "Z"):
                        number = -len(master_measurement) + i
                        print("color dict", color_dict)
                        file.write("DETECTOR(0,0,0," + str(check_color(color_dict, master_measurement[i][2])) + ") " + "rec[" + str(number) + "]\n")
        
        #NOW TIME FOR REPEAT BLOCK
        #file.write("REPEAT " + str(distance) + " {\n")
        file.write("REPEAT " + str(int(NUM_CYCLES/2 - 1)) + " {\n")
        ###NOW TIME FOR COPY AND PASTE BACKWARDS PASS

        back_master_measurement = []

        backString = ""
        backString += "  X_ERROR(" + str(errorX) + ") " + data_string + ancilla_string + "\n"
        backString += "  Y_ERROR(" + str(errorY) + ") " + data_string + ancilla_string + "\n"
        backString += "  Z_ERROR(" + str(errorZ) + ") " + data_string + ancilla_string + "\n"

        Z_check_ready = False
        Z_check_done = False
        #print("z ancillas", z_ancillas)
        #print("ancilla", ancilla)
        #print("cx lists", cx_lists)
        tup_count = 0
       
        X_check_count = 0
        total_checks = 0
        #print(stabilizer_matrix)
        #print("cx arr", cx_arr)
        for array in cx_arr:
            for check in array:
                total_checks += 1
        assert(total_checks // 2 == total_checks / 2)
        copy_CX_x = copy.deepcopy(x_s)
        building_cx_x = {} #7:[1,2,3,4]
        for b in range(numAncilla):
            building_cx_x[b + n] = []
        copy_CX_z = copy.deepcopy(z_s)
        building_cx_z = {} #7:[1,2,3,4]
        for b in range(numAncilla):
            building_cx_z[b + n] = []
        #do measurements after the checks
        back_cx_lists = reverse_2d_array(cx_lists)
        for layer in back_cx_lists:
            used = []
            cx_layer_string_x = ""
            cx_layer_string_z = ""
            measure_ancilla_string_x = ""
            measure_ancilla_string_z = ""
            for tup in layer:
                source = tup[0]
                target = tup[1] #another way of saying ancilla
                if (source > target):
                    if (len(building_cx_x[source]) == 0):
                        H_string = "H "
                        H_string += str(source) + " "
                        backString += "  " + H_string + "\n"
                        #tabString += "  " + H_string + "\n"
                    building_cx_x[source].append(target)
                    cx_layer_string_x += str(source) + " "
                    cx_layer_string_x += str(target) + " "
                else:
                    building_cx_z[target].append(source)
                    cx_layer_string_z += str(source) + " "
                    cx_layer_string_z += str(target) + " "
        
                used.append(source)
                used.append(target)
                        
            measurement_xs = [] 
            measurement_zs = []
            for pos in building_cx_x.keys():
                if (len(building_cx_x[pos]) > 0):
                    for stabilizer_generator in copy_CX_x:
                        if set(stabilizer_generator) == set(building_cx_x[pos]):
                            measurement_xs.append(pos)
                            copy_CX_x.remove(stabilizer_generator)
                            measure_ancilla_string_x += str(pos)
                            measure_ancilla_string_x += " "
                            back_master_measurement.append(("X", pos, building_cx_x[pos]))
                            building_cx_x[pos] = [] # for ancilla reuse case we need to reset it to nothing
                            break  # Exit the loop since we found a match
            for pos in building_cx_z.keys():
                if (len(building_cx_z[pos]) > 0):
                    for stabilizer_generator in copy_CX_z:
                        if set(stabilizer_generator) == set(building_cx_z[pos]): 
                            measurement_zs.append(pos)
                            copy_CX_z.remove(stabilizer_generator)
                            measure_ancilla_string_z += str(pos)
                            measure_ancilla_string_z += " "
                            back_master_measurement.append(("Z", pos, building_cx_z[pos]))
                            building_cx_z[pos] = [] # for ancilla reuse case we need to reset it to nothing   
                            break
            backString += "  CX " + cx_layer_string_x + cx_layer_string_z + "\n"
            backString += "  " + "DEPOLARIZE2(" + str(p) + ") " + cx_layer_string_x + cx_layer_string_z + "\n"
            if (len(measurement_xs) > 0): #assumes we CAN finish an X and a Z in a parallel step
                    H_string = "H "
                    H_string += measure_ancilla_string_x + " " #assumes never measuring an x and a z stabilizer in same step
                    backString += "  " + H_string + "\n"
                    #tabString += "  " + H_string + "\n"
                ###QUEUE a  measurement and reset of the ancilla here
                    backString += "  " + "X_ERROR(" + str(p) + ") " + measure_ancilla_string_x + "\n"
                    #tabString += "  " + "X_ERROR(" + str(p) + ") " + measure_ancilla_string + "\n"
                    backString += "  " + "MR " + measure_ancilla_string_x + "\n"
                    #tabString += "  " + "MR " + measure_ancilla_string + "\n"
                    reset_error = p/10
                    backString += "  " + "X_ERROR(" + str(reset_error) + ") " + measure_ancilla_string_x + "\n"
                    #tabString += "  " + "X_ERROR(" + str(reset_error) + ") " + measure_ancilla_string + "\n"
                    depolarize_after_h = p/10
                    depolarize_after_h_string = "DEPOLARIZE1(" + str(depolarize_after_h) + ") "
                    for i in ancilla:
                        depolarize_after_h_string += str(i) + " "
                    depolarize_after_h_string += "\n"
            if (len(measurement_zs) > 0):   
                #tabString += "  " + "DEPOLARIZE2(" + str(p) + ") " + cx_layer_string + "\n"
                backString += "  " + "X_ERROR(" + str(p) + ") " + measure_ancilla_string_z + "\n"
                #tabString += "  " + "X_ERROR(" + str(p) + ") " + measure_ancilla_string + "\n"
                backString += "  " + "MR " + measure_ancilla_string_z + "\n"
                #tabString += "  " + "MR " + measure_ancilla_string + "\n"
                reset_error = p/10
                backString += "  " + "X_ERROR(" + str(reset_error) + ") " + measure_ancilla_string_z + "\n"
                #tabString += "  " + "X_ERROR(" + str(reset_error) + ") " + measure_ancilla_string + "\n"
            unused = []
            for i in data:
                if (i not in used):
                    unused.append(i)
            for i in ancilla:
                if (i not in used):
                    unused.append(i)
            unused_string = ""
            for i in unused:
                unused_string += str(i) + " "
            depolarize_unused_cx = p/10
            tup_count += 1
            ###WRITE DOUBLE DETECTORS BACKWARDS
        if (surface_code):
            for i in range(len(back_master_measurement)):
                #negative = -(len(back_master_measurement)) 
                number = -len(back_master_measurement) + i
                stabilizer = back_master_measurement[i][2]
                second = 100
                for s in range(len(master_measurement)):
                    if (master_measurement[s][2] == stabilizer[::-1]):
                        second = -len(back_master_measurement) - len(master_measurement) + s
                #if (i + n % 2 in ancilla): #because each ancilla is assigned
                assert (second != 100)
                backString += "  DETECTOR(0,0,0,0) " + "rec[" + str(number) + "] " + "rec[" + str(second) + "]\n"
                
        else:
            for i in range(len(back_master_measurement)):
                number = -len(back_master_measurement) + i
                stabilizer = back_master_measurement[i][2]
                second = 100
                for s in range(len(master_measurement)):
                    if (master_measurement[s][2] == stabilizer[::-1] and back_master_measurement[i][0] == master_measurement[s][0]): #check types match as well because color codes have 2 stabilizers that fit this
                        second = -len(back_master_measurement) - len(master_measurement) + s
                #if (i + n % 2 in ancilla): #because each ancilla is assigned
                #print("master measurement", master_measurement)
                assert (second != 100)
                if (back_master_measurement[i][0] == "Z"):
                    backString += "  DETECTOR(0,0,0," + str(check_color(color_dict, back_master_measurement[i][2])) + ") " + "rec[" + str(number) + "] " + "rec[" + str(second) + "]\n"
                else: #Write the x version of the color if not a z stabilizer
                    backString += "  DETECTOR(0,0,0," + str((check_color(color_dict, back_master_measurement[i][2])) + 3) + ") " + "rec[" + str(number) + "] " + "rec[" + str(second) + "]\n"

        file.write(backString) #tabString already has this
        file.write(tabString)
        #FILL IN THE DOUBLED DETECTORS
        #master measurement from forward pass should be preserved
        #print("master measurement", master_measurement)
        if (surface_code):
            for i in range(len(master_measurement)):
                number = -len(master_measurement) + i
                stabilizer = master_measurement[i][2]
                second = 100
                for s in range(len(back_master_measurement)):
                    if (back_master_measurement[s][2] == stabilizer[::-1]):
                        second = -len(master_measurement) - len(back_master_measurement) + s
                #print("cx arr", cx_lists)
                #print("z_s", z_s)
                #print("length master measurement", len(master_measurement))
                assert(second != 100)

                #if (i + n % 2 in ancilla): #because each ancilla is assigned
                file.write("  DETECTOR(0,0,0,0) " + "rec[" + str(number) + "] " + "rec[" + str(second) + "]\n")
        else:
            for i in range(len(master_measurement)):
                number = -len(master_measurement) + i
                stabilizer = master_measurement[i][2]
                second = 100
                #print("master measurement", master_measurement)
                for s in range(len(back_master_measurement)):
                    if (back_master_measurement[s][2] == stabilizer[::-1]  and master_measurement[i][0] == back_master_measurement[s][0]):
                        second = -len(master_measurement) - len(back_master_measurement) + s
                assert(second != 100)
                if (master_measurement[i][0] == "Z"):
                    file.write("  DETECTOR(0,0,0," + str(check_color(color_dict, master_measurement[i][2])) + ") " + "rec[" + str(number) + "] " + "rec[" + str(second) + "]\n")
                else: #Write the x version of the color if not a z stabilizer
                    file.write("  DETECTOR(0,0,0," + str((check_color(color_dict, master_measurement[i][2])) + 3) + ") " + "rec[" + str(number) + "] " + "rec[" + str(second) + "]\n")

        #NOW CLOSE LOOP
        file.write("}\n")
        #file.write("  X_ERROR(" + str(errorX) + ") " + data_string + ancilla_string + "\n")
        #file.write("  Y_ERROR(" + str(errorY) + ") " + data_string + ancilla_string + "\n")
        #file.write("  Z_ERROR(" + str(errorZ) + ") " + data_string + ancilla_string + "\n")
        file.write(backString) #ITS INDENTED THO


        #NOW START MEASURE DATA 
        file.write("X_ERROR(" + str(p) + ") " + data_string + "\n")
        file.write("M " + data_string + "\n")
        negative_dict = {}
        count = -1
        for i in range(len(data)):
            negative_dict[len(data) + count] = count
            count -= 1
        #print("negative dict is", negative_dict)

        #DETECTORS ON STABILIZERS
        a_count = 0
        for i in range(len(back_master_measurement)):
            x = back_master_measurement[i]
            if (x[0] == "Z"):
                data_list = x[2]
                #print("data list", data_list)
                if (surface_code):
                        detector_string = "DETECTOR(0,0,0,0) "
                        for d in data_list:
                            detector_string += "rec[" + str(negative_dict[d]) + "] " 
                        ancilla_measurement = -len(back_master_measurement) - len(data) + i
                        detector_string += "rec[" + str(ancilla_measurement) + "]"
                        file.write(detector_string + "\n")
                else:
                        detector_string = "DETECTOR(0,0,0," + str(check_color(color_dict, x[2])) + ") "
                        for d in data_list:
                            detector_string += "rec[" + str(negative_dict[d]) + "] " 
                        ancilla_measurement = -len(back_master_measurement) - len(data) + i
                        detector_string += "rec[" + str(ancilla_measurement) + "]"
                        file.write(detector_string + "\n")
                a_count += 1
        
        #LASTLY, THE OBSERVABLE ON DATA
        obs_string = "OBSERVABLE_INCLUDE(0) "
        for x in negative_dict.keys():
            obs_string += "rec[" + str(negative_dict[x]) + "] "
        file.write(obs_string)
        print("Successfully wrote stim file!")

def read_pickled_info(cxs_name, timings_name):
    baseline_mode = False
    with open(cxs_name, 'rb') as handle:
        cxs = pkl.load(handle)
    with open(timings_name, 'rb') as handle:
        timings = pkl.load(handle)
    if ("baseline_timings" in cxs_name):
        assert("baseline_timings" in timings_name)
        #print("cxs name", cxs_name)
        #print("timings name", timings_name)
        baseline_mode = True
    return cxs, timings, baseline_mode

def run_create_stim_circs(pphys_range=[1e-4, 2e-4, 3e-4, 4e-4, 5e-4, 6e-4, 7e-4, 8e-4, 9e-4, 1e-3]):
    #pphys_range = [1e-4, 2e-4, 3e-4, 4e-4, 5e-4, 6e-4, 7e-4, 8e-4, 9e-4, 1e-3]
    compiler_range = ["Moveless", "Baseline"]


    ancilla_proportion = [1, 0.2, 0.4, 0.6, 0.8, -1] 
    for compiler_mode in compiler_range:
        for pphys in pphys_range:
            for prop in ancilla_proportion:
            
                all_timings = []
                all_cxs = []
                all_codes = []
                
                if (compiler_mode == "Baseline"):
                    if (prop == 1):
                        prop_string = "1"
                    elif (prop == -1):
                        prop_string = "max"
                    else:
                        prop_string = str(prop)
                    arr = os.listdir(f"Demo_Baseline_Timings/{prop_string}m/")
                    file_prepend = f"Demo_Baseline_Timings/{prop_string}m/"
                    mode_file_string = "stim_files_Baseline/"
                elif (compiler_mode == "Moveless"):
                    if (prop == 1):
                        prop_string = "1"
                    elif (prop == -1):
                        prop_string = "max"
                    else:
                        prop_string = str(prop)
                    arr = os.listdir(f"Demo_Moveless_Timings/{prop_string}m/")
                    file_prepend = f"Demo_Moveless_Timings/{prop_string}m/"
                    mode_file_string = "stim_files_Moveless/"
                else:
                    print("Unknown circuit generation mode")
                    assert(0)
                #print("arr is", arr)
                for x in arr:
                    if ("Cxs" in x):
                        all_cxs.append(x)
                    if ("Timings" in x):
                        all_timings.append(x)
                    if ("code" in x):
                        all_codes.append(x)
                #Must follow naming convetion of n-k-d_CxsCyclone.stim
                assert(len(all_timings) == len(all_cxs))
                assert(len(all_codes) == len(all_timings))
                
                #MAKE SURE THESE ARE BOTH IN SAME RELATIVE ORDER. IF RUNNING THE SCRIPT ABOVE IN PARSE TIMINGS THIS WILL ALWAYS BE THE CASE.
                #print("cxs", all_cxs)
                #print("timings", all_timings)
                #print("all codes", all_codes) #AGAIN, THIS PART IS SUPER IMPORTANT - DIRECTORY LISTED IS IN RELATIVE STABLE ORDER
        
                

                for x in range(len(all_timings)):
                    #print(all_timings[x])
                    #leftover = all_timings[x].split("/")[1]
                    leftover = all_timings[x]
                    short_name = leftover.split("_")[0]
                    #print("short name", short_name)
                    code = all_codes[x]
                    ancilla = int(code.split("_code")[1].split("Ancilla")[0])
                    #print("ancilla", ancilla)
                    assert(code[:2] == all_timings[x][:2]) # CHECKING RELATIVE ORDERING
                    number = leftover.split("-")[0]
                    distance = int(short_name.split("-")[2])
                    stabilizer_string = "stabilizer_metadata/" + short_name + "matrix.pkl"
                        
                    with open(stabilizer_string, "rb") as stabilizer_file:
                        stabilizer_matrix = pkl.load(stabilizer_file)

                    if (number == "7" or number == "19" or number == "37" or number == "61" or number == "91"): #quick and easy way to determine color codes
                        surface_code=False
                    else:
                        surface_code=True

                    if (surface_code): 
                    
                        full_name = mode_file_string + "surface_codes/" + prop_string + "m/" + short_name + "p="+ str(pphys)+ "d=" + str(distance)+ ".stim"
                        c = file_prepend + all_cxs[x]
                        t = file_prepend + all_timings[x]
                        cx_lists, timings, file_baseline_mode = read_pickled_info(c, t)  #file_baseline_mode deprecated
                        #ADDING SYMPATHETIC COOLING 9/23/2024
                        #print("timings for baseline", timings)
                        for i in range(len(timings)): #BASELINE METHOD FOR ADDING TIMINGS ADDED 11/19/24
                            if (timings[i] != 100): #then it must be a shuttling op (when ion chain lengths are bounded at 5, 100 is fine. If doing sensitivity analysis it must change according to trap scaling to find gate time and filter it out)
                                timings[i] += 473
                            
                        #print("timings after sympathetic cooling on each merge", timings)
                        
                        createStimBaselineandSOA(full_name, cx_lists, timings, pphys, distance, stabilizer_matrix, surface_code, numAncilla=ancilla)
                        
                    else:
                        
                        colors_string = "stabilizer_metadata/" + short_name + "colors.pkl"
                        with open(colors_string, "rb") as color_file:
                            colors = pkl.load(color_file)
                        #print("colors", colors)
                        
                        full_name = mode_file_string + "color_codes/" + prop_string + "m/" + short_name + "p="+ str(pphys)+ "d=" + str(distance)+ ".stim"
                        c = file_prepend + all_cxs[x]
                        t = file_prepend + all_timings[x]
                        cx_lists, timings, file_baseline_mode = read_pickled_info(c, t) 
                        #ADDING SYMPATHETIC COOLING 9/23/2024, BASELINE METHOD 11/19/24 
                        for i in range(len(timings)): #BASELINE METHOD FOR ADDING TIMINGS ADDED 11/19/24
                            if (timings[i] != 100): #then it must be a shuttling op (same thing with gate times as noted above, if ion trap capacity increases, need to adjust filter for gate times accordingly)
                                timings[i] += 473
                            
                        #print("timings after sympathetic cooling on each merge", timings)
                        
                        createStimBaselineandSOA(full_name, cx_lists, timings, pphys, distance, stabilizer_matrix, surface_code=surface_code, color_metadata=colors, numAncilla=ancilla)
###RUN CODE
if (__name__ == "__main__"):
    run_create_stim_circs()            