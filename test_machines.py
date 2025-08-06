from machine import Machine, Trap, Segment, MachineParams

def grid_10x6(capacity, mparams):
    m = Machine(mparams)
    t = [m.add_trap(i, capacity) for i in range(60)]
    j = [m.add_junction(i) for i in range(50)]
    for i in range(10):
        m.add_segment(i, t[i], j[i], 'R')
    for i in range(9):
        m.add_segment(9, j[i], j[i + 1])
    for i in range(10, 20):
        m.add_segment(i, t[i], j[i-10], 'L')

    for i in range(10, 20):
        m.add_segment(i, t[i], j[i], 'R')
    for i in range(10, 19):
        m.add_segment(19, j[i], j[i + 1])
    for i in range(20, 30):
        m.add_segment(i, t[i], j[i-10], 'L')
    
    for i in range(20, 30):
        m.add_segment(i, t[i], j[i], 'R')
    for i in range(20, 29):
        m.add_segment(29, j[i], j[i + 1])
    for i in range(30, 40):
        m.add_segment(i, t[i], j[i-10], 'L')
    
    for i in range(30, 40):
        m.add_segment(i, t[i], j[i], 'R')
    for i in range(30, 39):
        m.add_segment(39, j[i], j[i + 1])
    for i in range(40, 50):
        m.add_segment(i, t[i], j[i-10], 'L')
    
    for i in range(40, 50):
        m.add_segment(i, t[i], j[i], 'R')
    for i in range(40, 49):
        m.add_segment(39, j[i], j[i + 1])
    for i in range(50, 60):
        m.add_segment(i, t[i], j[i-10], 'L')
    
    return m

"""
def grid_removed(remove_num, capacity, mparams):
    #3x3
    m = Machine(mparams)
    t = [m.add_trap(i, capacity) for i in range(9)]
    j = [m.add_junction(i) for i in range(6)]
    m.add_segment(0, j[0], j[1])
    m.add_segment(0, j[1], j[2])
    m.add_segment(1, j[3], j[4])
    m.add_segment(1, j[4], j[5])

    m.add_segment(2, t[0], j[0], 'R')
    m.add_segment(3, t[1], j[1], 'R')
    m.add_segment(4, t[2], j[2], 'R')
    m.add_segment(5, t[3], j[2], 'L')
    m.add_segment(6, t[4], j[1], 'L')
    m.add_segment(7, t[5], j[0], 'L')
    m.add_segment(8, t[3], j[3], 'R')
    m.add_segment(9, t[4], j[4], 'R')
    m.add_segment(10, t[5], j[5], 'R')
    m.add_segment(11, t[6], j[3], 'L')
    m.add_segment(12, t[7], j[4], 'L')
    m.add_segment(13, t[8], j[5], 'L')
    return m
"""

def grid_removed(remove_num, capacity, mparams):
    # 3x3
    m = Machine(mparams)
    t = [m.add_trap(i, capacity) for i in range(10)]
    j = [m.add_junction(i) for i in range(20)]

    """
    TAINTED_segment_data 3x3 = [
        (0, j[0], j[1]), (0, j[1], j[2]),
        (1, j[3], j[4]), (1, j[4], j[5]),
        (2, t[0], j[0], 'R'), (3, t[1], j[1], 'R'),
        (4, t[2], j[2], 'R'), (5, t[3], j[2], 'L'),
        (6, t[3], j[1], 'L'), (7, t[3], j[0], 'L'),
        (8, t[3], j[3], 'R'), (9, t[3], j[4], 'R'),
        (10, t[3], j[5], 'R'), (11, t[3], j[3], 'L'),
        (12, t[3], j[4], 'L'), (13, t[3], j[5], 'L')
    ]"""

    """ ORIGINAL 3x3 segment_data = [
        (0, j[0], j[1]), (0, j[1], j[2]),
        (1, j[3], j[4]), (1, j[4], j[5]),
        (2, t[0], j[0], 'R'), (3, t[1], j[1], 'R'),
        (4, t[2], j[2], 'R'), (5, t[5], j[2], 'L'),
        (6, t[4], j[1], 'L'), (7, t[3], j[0], 'L'),
        (8, t[3], j[3], 'R'), (9, t[4], j[4], 'R'),
        (10, t[5], j[5], 'R'), (11, t[6], j[3], 'L'),
        (12, t[7], j[4], 'L'), (13, t[8], j[5], 'L')
    ]
    """
    segment_data = [ #should be 40 trap segments
        (0, j[0], j[1]), (0, j[1], j[2]), (0, j[2], j[3]), (0, j[3], j[4]),
        (1, j[5], j[6]), (1, j[6], j[7]), (1, j[7], j[8]), (1, j[8], j[9]),
        (2, j[10], j[11]), (2, j[11], j[12]), (2, j[12], j[13]), (2, j[13], j[14]),
        (3, j[15], j[16]), (3, j[16], j[17]), (3, j[17], j[18]), (3, j[18], j[19]),

        (4, t[0], j[0], 'R'), (5, t[1], j[1], 'R'), (6, t[2], j[2], 'R'), (7, t[3], j[3], 'R'), (8, t[4], j[4], 'R'),
        (9, t[5], j[0], 'L'), (10, t[6], j[1], 'L'), (11, t[7], j[2], 'L'), (12, t[8], j[3], 'L'), (13, t[9], j[4], 'L'),

        (14, t[5], j[5], 'R'), (15, t[6], j[6], 'R'), (16, t[7], j[7], 'R'), (17, t[8], j[8], 'R'), (18, t[9], j[9], 'R'),
        (19, t[9], j[5], 'L'), (20, t[9], j[6], 'L'), (21, t[9], j[7], 'L'), (22, t[9], j[8], 'L'), (23, t[9], j[9], 'L'),

        (24, t[9], j[9], 'R'), (25, t[9], j[9], 'R'), (26, t[9], j[9], 'R'), (27, t[9], j[9], 'R'), (28, t[9], j[9], 'R'),
        (29, t[9], j[9], 'L'), (30, t[9], j[9], 'L'), (31, t[9], j[9], 'L'), (32, t[9], j[9], 'L'), (33, t[9], j[9], 'L'),

        (34, t[9], j[9], 'R'), (35, t[9], j[9], 'R'), (36, t[9], j[9], 'R'), (37, t[9], j[9], 'R'), (38, t[9], j[9], 'R'),
        (39, t[9], j[9], 'L'), (40, t[9], j[9], 'L'), (41, t[9], j[9], 'L'), (42, t[9], j[9], 'L'), (43, t[9], j[9], 'L'),
    ]
    """ORIGINAL SEGMENT DATA 5X5
    segment_data = [ #should be 40 trap segments
        (0, j[0], j[1]), (0, j[1], j[2]), (0, j[2], j[3]), (0, j[3], j[4]),
        (1, j[5], j[6]), (1, j[6], j[7]), (1, j[7], j[8]), (1, j[8], j[9]),
        (2, j[10], j[11]), (2, j[11], j[12]), (2, j[12], j[13]), (2, j[13], j[14]),
        (3, j[15], j[16]), (3, j[16], j[17]), (3, j[17], j[18]), (3, j[18], j[19]),

        (4, t[0], j[0], 'R'), (5, t[1], j[1], 'R'), (6, t[2], j[2], 'R'), (7, t[3], j[3], 'R'), (8, t[4], j[4], 'R'),
        (9, t[5], j[0], 'L'), (10, t[6], j[1], 'L'), (11, t[7], j[2], 'L'), (12, t[8], j[3], 'L'), (13, t[9], j[4], 'L'),

        (14, t[5], j[5], 'R'), (15, t[6], j[6], 'R'), (16, t[7], j[7], 'R'), (17, t[8], j[8], 'R'), (18, t[9], j[9], 'R'),
        (19, t[10], j[5], 'L'), (20, t[11], j[6], 'L'), (21, t[12], j[7], 'L'), (22, t[13], j[8], 'L'), (23, t[14], j[9], 'L'),

        (24, t[10], j[10], 'R'), (25, t[11], j[11], 'R'), (26, t[12], j[12], 'R'), (27, t[13], j[13], 'R'), (28, t[14], j[14], 'R'),
        (29, t[15], j[10], 'L'), (30, t[16], j[11], 'L'), (31, t[17], j[12], 'L'), (32, t[18], j[13], 'L'), (33, t[19], j[14], 'L'),

        (34, t[15], j[15], 'R'), (35, t[16], j[16], 'R'), (36, t[17], j[17], 'R'), (37, t[18], j[18], 'R'), (38, t[19], j[19], 'R'),
        (39, t[20], j[15], 'L'), (40, t[21], j[16], 'L'), (41, t[22], j[17], 'L'), (42, t[23], j[18], 'L'), (43, t[24], j[19], 'L'),
    ]"""

    total_segments = len(segment_data)
    max_index = total_segments - remove_num  # Exclude the last 'remove_num' segments

    for idx, segment in enumerate(segment_data):
        if idx < max_index:
            m.add_segment(*segment)

    return m

#ISCA Test machines Begin
def test_trap_2x3(capacity, mparams): #3 rows, 2 columns
    m = Machine(mparams)
    t = [m.add_trap(i, capacity) for i in range(6)]
    j = [m.add_junction(i) for i in range(3)]
    m.add_segment(0, t[0], j[0], 'R')
    m.add_segment(1, t[1], j[1], 'R')
    m.add_segment(2, t[2], j[2], 'R')
    m.add_segment(3, t[3], j[2], 'L')
    m.add_segment(4, t[4], j[1], 'L')
    m.add_segment(5, t[5], j[0], 'L')
    m.add_segment(6, j[0], j[1])
    m.add_segment(6, j[1], j[2])
    return m
def test_trap_2x6(capacity, mparams):
    m = Machine(mparams)
    t = [m.add_trap(i, capacity) for i in range(12)]
    j = [m.add_junction(i) for i in range(6)]
    m.add_segment(0, t[0], j[0], 'R')
    m.add_segment(1, t[1], j[1], 'R')
    m.add_segment(2, t[2], j[2], 'R')
    m.add_segment(3, t[3], j[3], 'R')
    m.add_segment(4, t[4], j[4], 'R')
    m.add_segment(5, t[5], j[5], 'R')
    m.add_segment(6, t[6], j[5], 'L')
    m.add_segment(7, t[7], j[4], 'L')
    m.add_segment(8, t[8], j[3], 'L')
    m.add_segment(9, t[9], j[2], 'L')
    m.add_segment(10, t[10], j[1], 'L')
    m.add_segment(11, t[11], j[0], 'L')
    m.add_segment(12, j[0], j[1])
    m.add_segment(12, j[1], j[2])
    m.add_segment(12, j[2], j[3])
    m.add_segment(12, j[3], j[4])
    m.add_segment(12, j[4], j[5])
    return m

def make_linear_machine(zones, capacity, mparams):
    m = Machine(mparams)
    traps = []
    junctions = []
    for i in range(zones):
        traps.append(m.add_trap(i, capacity))
    for i in range(zones-1):
        junctions.append(m.add_junction(i))
    for i in range(zones-1):
        m.add_segment(2*i,   traps[i], junctions[i], 'R') #t_i ---- j_i ---- t_i+1
        m.add_segment(2*i+1, traps[i+1], junctions[i], 'L')
    for x in m.traps:
        print("RIGHT HERE CAPACITY", x.capacity)
    return m

def make_single_hexagon_machine(capacity, mparams):
    m = Machine(mparams)
    t = [m.add_trap(i, capacity) for i in range(6)]
    j = [m.add_junction(i) for i in range(6)]
    m.add_segment(0, t[0], j[0], 'R')
    m.add_segment(1, t[1], j[1], 'R')
    m.add_segment(2, t[2], j[2], 'R')
    m.add_segment(3, t[3], j[3], 'R')
    m.add_segment(4, t[4], j[4], 'R')
    m.add_segment(5, t[5], j[5], 'R')
    m.add_segment(6, t[0], j[5], 'L')
    m.add_segment(7, t[1], j[0], 'L')
    m.add_segment(8, t[2], j[1], 'L')
    m.add_segment(9, t[3], j[2], 'L')
    m.add_segment(10, t[4], j[3], 'L')
    m.add_segment(11, t[5], j[4], 'L')
    return m

def make_circle_machine_4(capacity, mparams):
    m = Machine(mparams)
    t = [m.add_trap(i, capacity) for i in range(4)]
    j = [m.add_junction(i) for i in range(4)]
    m.add_segment(0, t[0], j[0], 'R')
    m.add_segment(1, t[1], j[1], 'R')
    m.add_segment(2, t[2], j[2], 'R')
    m.add_segment(3, t[3], j[3], 'R')
    m.add_segment(4, t[0], j[3], 'L')
    m.add_segment(5, t[1], j[0], 'L')
    m.add_segment(6, t[2], j[1], 'L')
    m.add_segment(7, t[3], j[2], 'L')
    return m

def make_circle_machine_length_n(capacity, mparams, n):
    m = Machine(mparams)
    t = [m.add_trap(i, capacity) for i in range(n)]
    j = [m.add_junction(i) for i in range(n)]

    #prints should resemble the above structures exactly
    for i in range(n):
        m.add_segment(i, t[i], j[i], 'R')
        #print("added " + str(i) + ", t[" +str(i) + "], j[" + str(i) + "], " + "R")
    for i in range(n):
        if (i == 0):
            m.add_segment(n + i, t[i], j[n-1], 'L') #links the circle by connecting tail to head
            #print("added " + str(n+i) + ", t[" +str(i) + "], j[" + str(n-1) + "], " + "L")
        else:
            m.add_segment(n + i, t[i], j[i-1], 'L')
            #print("added " + str(n+i) + ", t[" +str(i) + "], j[" + str(i-1) + "], " + "L")
    
    return m

#ISCA Test machines End

def mktrap4x2(capacity):
    m = Machine()
    t0 = m.add_trap(0, capacity)
    t1 = m.add_trap(1, capacity)
    t2 = m.add_trap(2, capacity)
    t3 = m.add_trap(3, capacity)
    j0 = m.add_junction(0)
    j1 = m.add_junction(1)
    m.add_segment(0, t0, j0)
    m.add_segment(1, t1, j0)
    m.add_segment(2, t2, j1)
    m.add_segment(3, t3, j1)
    m.add_segment(4, j0, j1)
    return m

def mktrap_4star(capacity):
    m = Machine()
    t0 = m.add_trap(0, capacity)
    t1 = m.add_trap(1, capacity)
    t2 = m.add_trap(2, capacity)
    t3 = m.add_trap(3, capacity)
    j0 = m.add_junction(0)
    m.add_segment(0, t0, j0)
    m.add_segment(1, t1, j0)
    m.add_segment(2, t2, j0)
    m.add_segment(3, t3, j0)
    return m

def mktrap6x3(capacity):
    m = Machine()
    t0 = m.add_trap(0, capacity)
    t1 = m.add_trap(1, capacity)
    t2 = m.add_trap(2, capacity)
    t3 = m.add_trap(3, capacity)
    t4 = m.add_trap(4, capacity)
    t5 = m.add_trap(5, capacity)
    j0 = m.add_junction(0)
    j1 = m.add_junction(1)
    j2 = m.add_junction(2)
    m.add_segment(0, t0, j0)
    m.add_segment(1, t1, j0)
    m.add_segment(2, t2, j1)
    m.add_segment(3, t3, j1)
    m.add_segment(4, t4, j2)
    m.add_segment(5, t5, j2)
    m.add_segment(6, j0, j1)
    m.add_segment(7, j1, j2)
    return m

def mktrap8x4(capacity):
    m = Machine()
    t0 = m.add_trap(0, capacity)
    t1 = m.add_trap(1, capacity)
    t2 = m.add_trap(2, capacity)
    t3 = m.add_trap(3, capacity)
    t4 = m.add_trap(4, capacity)
    t5 = m.add_trap(5, capacity)
    t6 = m.add_trap(6, capacity)
    t7 = m.add_trap(7, capacity)

    j0 = m.add_junction(0)
    j1 = m.add_junction(1)
    j2 = m.add_junction(2)
    j3 = m.add_junction(3)

    m.add_segment(0, t0, j0)
    m.add_segment(1, t1, j0)
    m.add_segment(2, t2, j1)
    m.add_segment(3, t3, j1)
    m.add_segment(4, t4, j2)
    m.add_segment(5, t5, j2)
    m.add_segment(6, t6, j3)
    m.add_segment(7, t7, j3)

    m.add_segment(8, j0, j1)
    m.add_segment(9, j1, j2)
    m.add_segment(10, j2, j3)
    return m



def make_3x3_grid(capacity):
    m = Machine()
    t = [m.add_trap(i, capacity) for i in range(9)]
    j = [m.add_junction(i) for i in range(6)]
    m.add_segment(0, t[0], j[0])
    m.add_segment(1, t[1], j[1])
    m.add_segment(2, t[2], j[2])
    m.add_segment(3, t[3], j[3])
    m.add_segment(4, t[4], j[4])
    m.add_segment(5, t[5], j[5])
    m.add_segment(6, t[3], j[0])
    m.add_segment(7, t[4], j[1])
    m.add_segment(8, t[5], j[2])
    m.add_segment(9,  t[6], j[3])
    m.add_segment(10, t[7], j[4])
    m.add_segment(11, t[8], j[5])
    m.add_segment(12, j[0], j[1])
    m.add_segment(13, j[1], j[2])
    m.add_segment(14, j[3], j[4])
    m.add_segment(15, j[4], j[5])
    return m

def make_9trap(capacity):
    m = Machine(alpha=0.005, inter_ion_dist=1, split_factor=5.0, move_factor=1.0)
    t = [m.add_trap(i, capacity) for i in range(9)]
    j = [m.add_junction(i) for i in range(9)]

    m.add_segment(0, t[0], j[0])
    m.add_segment(1, t[1], j[1])
    m.add_segment(2, t[2], j[2])

    m.add_segment(3, t[3], j[2])
    m.add_segment(4, t[4], j[5])
    m.add_segment(5, t[5], j[8])

    m.add_segment(6, t[6], j[8])
    m.add_segment(7, t[7], j[7])
    m.add_segment(8, t[8], j[6])

    m.add_segment(9, j[0], j[1])
    m.add_segment(10, j[0], j[3])
    m.add_segment(11, j[3], j[6])
    m.add_segment(12, j[3], j[4])
    m.add_segment(13, j[6], j[7])
    m.add_segment(14, j[1], j[4])
    m.add_segment(15, j[1], j[2])
    m.add_segment(16, j[4], j[7])
    m.add_segment(17, j[4], j[5])
    m.add_segment(18, j[7], j[8])
    m.add_segment(19, j[2], j[5])
    m.add_segment(20, j[5], j[8])
    return m
