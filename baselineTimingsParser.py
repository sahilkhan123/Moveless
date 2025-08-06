import os
import pickle as pkl
import copy
#This file was made originally in April '24 when baseline = greedy, and was coincidentally named baselineTimingsParser. The word baseline, greedy, and cyclone can all be used interchangeably.

def parseTimings():
    astrings = ["0.2m", "0.4m", "0.6m", "0.8m", "1m", "max_m"]
    #astrings = ["241_ions", "121_ions", "81_ions", "49_ions", "25_ions", "13_ions", "9_ions", "5_ions"]
    #astrings = ["16_split", "32_split", "48_split", "64_split", "80_split"]
    #astrings = ["1_machine", "2_machine", "3_machine"]
    #ION_MODE = True #turn on if ion chain length >=7, to account for appropriate gate time
    for ancilla_string in astrings:
        #arr = os.listdir("SOA_timings/" + ancilla_string + "/")
        arr = os.listdir("QCE_Dynamic_Timings/" + ancilla_string + "/") 
        print("arr", arr)
        for a in arr:
            #name = "SOA_timings/" + ancilla_string + "/" + a
            name = "QCE_Dynamic_Timings/" + ancilla_string + "/" + a
            with open(name, 'rb') as file:
                dictionary = pkl.load(file)
                cx_arr = [[]]
                timings = []
                timings.append(100)
                curr_list = []
                layer = 0 #assumes the first thing we do is a gate
                oldlayer = 0
                operations = []
                timings_set = []
                print("new a is", a)
                if (a.split("_")[1] == "CxsBaseline.pkl" or a.split("_")[1] == "TimingsBaseline.pkl"): #pass on timings baseline files already made if using this script to make additional baseline timings files
                    print("SKIPPED", a)
                    continue
                for x in dictionary:
                    #print("x is", x)
                    if (len(x[4]['ions']) == 2):
                        operations.append(x)
                        if (x[1] == 1):#is a gate
                            #assert(x[2] + 100 == x[3]) ONLY HAVE THIS ASSERTION GO OFF IF ION CHAIN LENGTH IS LOW ENOUGH
                            if (x[3] not in timings_set):
                                timings_set.append(x[3])
                            layer = x[2]
                            if (layer != oldlayer):
                                cx_arr.append([(x[4]['ions'][0], x[4]['ions'][1])])
                                oldlayer = layer
                            else:
                                cx_arr[-1].append((x[4]['ions'][0], x[4]['ions'][1]))
                                oldlayer = layer
                base = 0
                print("timings set", timings_set)
                
                for x in timings_set:
                    #print(x)
                    new_time = x - base
                    timings.append(new_time)
                    base = x
                    """ THIS PART IS ACTUALLY/WAS ACTUALLY WRONG, IT OVERCOUNTED GATE TIMES BY GATE_TIME * NUMBER OF CX GATES
                    if (ION_MODE): #this works because there is the same ion count consistent throughout folder. Also because the structure was if not anything else it was a gate op, now just calculate gate op time.
                        ion_count = int(ancilla_string.split("_")[0])
                        if (abs(new_time - max(100, 13.33*(ion_count+2)-54)) > 1): #this was a pure gate layer
                            timings.append(max(100, 13.33*(ion_count+2)-54))
                    else:
                        timings.append(100)
                    """
                    #print(operations)
                    #dump_name_cx = "SOA_timings/" + ancilla_string + "/" + a.split("_")[0] + "_CxsBaseline.pkl"
                    #dump_name_timings = "SOA_timings/" + ancilla_string + "/" + a.split("_")[0] + "_TimingsBaseline.pkl"
                    dump_name_cx = "QCE_Dynamic_Timings/" + ancilla_string + "/" + a.split("_")[0] + "_CxsBaseline.pkl"
                    dump_name_timings = "QCE_Dynamic_Timings/" + ancilla_string + "/" + a.split("_")[0] + "_TimingsBaseline.pkl"
                print(cx_arr)
                print("timings", timings)
                print(len(cx_arr))
                print(len(timings))
                print("Sum for ", ancilla_string, ":")
                print(sum(timings))
                with open(dump_name_cx, "wb") as f1:
                    pkl.dump(cx_arr, f1)
                with open(dump_name_timings, "wb") as f2:
                    pkl.dump(timings, f2)
                #pkl.dump(cx_arr, dump_name_cx)
                #pkl.dump(timings, dump_name_timings)            
                            #time_diff = layer - oldlayer_finish

                    

        #

if (__name__ == "__main__"):
    parseTimings()