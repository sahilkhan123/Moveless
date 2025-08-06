
import itertools

import networkx as nx


def _gen_circuit_moment_interactions(c):
    for moment in c:
        concurrent_interactions = tuple(_gen_moment_interactions(moment))
        if concurrent_interactions:
            yield concurrent_interactions

def _gen_moment_interactions(moment):
    for op in moment.operations:
        if len(op.qubits) < 2:
            continue
        elif len(op.qubits) > 2:
            raise ValueError(
                'Cannot determine interactions of a gate '
                'with more than 2 qubits.')
        q0, q1 = op.qubits
        yield q0, q1

def circuit_to_time_graph(c, n=None):
    qs = set()
    for op in c:
        for q in op[1]:
            qs.add(q.index)
    qubits = list(range(c.num_qubits))
    
    # qubits = sorted(c.all_qubits())
    qubit_index_map = {q:i for i, q in enumerate(qubits)}
    n_used = len(qubits)
    if n is None:
        n = n_used
    if n_used > n:
        raise ValueError('Circuit uses more qubits that are available on the hardware.')

    interactions_list = []
    
    moments_by_t = {}
    
    q_last_used = {}
    for op in c:
        if len(op[1]) == 2:
            max_t = 0
            for q in op[1]:
                if q.index not in q_last_used:
                    q_last_used[q.index] = 0
                max_t = max(q_last_used[q.index], max_t)
            for q in op[1]:
                q_last_used[q.index] = max_t
            if max_t not in moments_by_t:
                moments_by_t[max_t] = []
            moments_by_t[max_t].append((op[1][0].index, op[1][1].index))
            
    interactions_list = [moments_by_t[k] for k in sorted(moments_by_t.keys())]
            
        
   #  interactions_list = tuple(_gen_circuit_moment_interactions(c))
    duration = len(interactions_list)

    g = nx.Graph()
    # Add nodes
    g.add_nodes_from(range(n * duration))
    # Add time edges
    g.add_edges_from(
        (t*n + i, (t+1)*n + i)
        for t, i in itertools.product(range(duration-1), range(n_used))
    )
    # Add interaction edges
    g.add_edges_from(
        (t*n+qubit_index_map[q0], t*n+qubit_index_map[q1])
        for t, interactions in enumerate(interactions_list)
        for q0, q1 in interactions
    )
    return g


def ion_trap_time_graph(trap_size, trap_count, duration):
    return irregular_ion_trap_time_graph((trap_size,) * trap_count, duration)

def irregular_ion_trap_time_graph(trap_size_list, duration):
    n = sum(trap_size_list)

    g = nx.Graph()
    # Add nodes
    g.add_nodes_from(range(n * duration))
    # Add time edges
    g.add_edges_from(
        (t*n + i, (t+1)*n + i)
        for t, i in itertools.product(range(duration-1), range(n))
    )
    # Add cluster edges
    g.add_edges_from(
        (t*n + i1, t*n + i2)
        for t in range(duration)
        for b, b_offset in zip(trap_size_list, itertools.accumulate(trap_size_list))
        for i1, i2 in itertools.combinations(range(b_offset-b, b_offset), 2)
    )
    return g
