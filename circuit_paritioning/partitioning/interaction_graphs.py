import networkx as nx
from collections import defaultdict


def circuit_to_graphs(c):
    ig = nx.Graph()
    
    for i in range(c.num_qubits):
        ig.add_node(i)
    
    total_interactions = defaultdict(int)
    interactions = []
    

    
    # First find the "moments" of the circuit
    circuit_moments = {}
    qubit_last_used = {}
    
    curr_t = 0
    for op in c:
        max_t = 0
        for q in op[1]:
            ind = q.index
            if ind not in qubit_last_used:
                qubit_last_used[ind] = curr_t
            if qubit_last_used[ind] > max_t:
                max_t = qubit_last_used[ind]
        for q in op[1]:
            qubit_last_used[q.index] = max_t + 1
        if max_t + 1 not in circuit_moments:
            circuit_moments[max_t + 1] = []

        circuit_moments[max_t + 1].append(op)
    
    for t in circuit_moments:
        interactions.append(defaultdict(int))
        for op in circuit_moments[t]:
            if len(op[1]) == 2:
                q1, q2 = op[1][0].index, op[1][1].index
                interactions[-1][frozenset({q1, q2})] += 1
                total_interactions[frozenset({q1, q2})] += 1
                
    for interaction in total_interactions:
        l = list(interaction)
        ig.add_edge(l[0], l[1], weight=total_interactions[interaction])
        
    graphs = []
    for e in interactions:
        graphs.append(nx.Graph())
        for inter in e:
            l = list(inter)
            graphs[-1].add_edge(l[0], l[1], weight=1)
        for b in qubit_last_used.keys():
            graphs[-1].add_node(b)
            
        for i in range(c.num_qubits):
            graphs[-1].add_node(i)

    return ig, graphs