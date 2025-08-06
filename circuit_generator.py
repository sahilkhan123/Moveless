
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
            #print("nums", nums)
            #print(len(nums))
            #print(n)
            assert(len(nums) == n)
            #print("ROW ", x)
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

