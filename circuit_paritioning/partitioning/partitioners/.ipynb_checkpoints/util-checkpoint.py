from collections import defaultdict
import networkx as nx

def memoize(f):
    cache = {}
    def replace_f(*args, **kwargs):
        key = (tuple(args), tuple(sorted(kwargs.items())))
        if key in cache:
            val = cache[key]
        else:
            val = f(*args, **kwargs)
            cache[key] = val
        return val
    return replace_f

def iter_take_n(iterable, n):
    '''Yields the first n items of the iterable'''
    for i, val in zip(range(n), iterable):
        yield val

def num_qubits_in_partitioning(parts):
    return sum(map(len, parts))

def pad_partitioning(parts, n=None, p=0, k=0):
    '''
    Pads a partitioning

    Args:
        parts: A partitioning (list of sets of numbers from 0 to n-1)
        n: The number of used qubits
        p: The size of each bucket (must be specified)
        k: The number of buckets (must be specified)

    Returns:
        A new padded partitioning
    '''
    # TODO: add assertions to verify the partitioning is valid
    if n is None:
        n = num_qubits_in_partitioning(parts)
    pad_iter = iter(range(n, p*k))
    return [set(bucket) | set(iter_take_n(pad_iter, p-len(bucket)))
            for bucket in parts]

def unpad_partitioning(parts, n, p=None, k=None):
    '''
    Removes padding from a partitioning

    Args:
        parts: A partitioning (list of sets of numbers from 0 to n-1)
        n: The number of used qubits (must be specified)
        p: The size of each bucket
        k: The number of buckets

    Returns:
        A new unpadded partitioning
    '''
    # TODO: add assertions to verify the partitioning is valid
    used_qubits = set(range(n))
    return [used_qubits.intersection(bucket)
            for bucket in parts]

def match_partitions_minimum_swap(partA, partB, graph_size=None):
    '''Returns partB with the partitions reordered to minimize the swaps from
    A to B.'''
    assert len(partA) == len(partB), 'Partitions must be the same length.'

    counts = defaultdict()
    for i in range(len(partB)):
        counts[i] = defaultdict(int)

    for i in range(len(partA)):
        for e in partA[i]:
            if graph_size is None or e < graph_size:
                for j in range(len(partB)):
                    if e in partB[j]:
                        counts[j][i] += 1

    G = nx.Graph()
    G.add_nodes_from(['a' + str(i) for i in range(len(partA))])
    G.add_nodes_from(['b' + str(i) for i in range(len(partB))])

    for i in range(len(partA)):
        for j in range(len(partB)):
            G.add_edge('a' + str(i), 'b' + str(j), weight=counts[i][j] + 1)

    M = nx.algorithms.matching.max_weight_matching(G)

    b_assignments = [-1 for _ in range(len(partB))]
    for e in M:
        if e[0][0] == 'b':
            b_assignments[int(e[0][1:])] = int(e[1][1:])
        else:
            b_assignments[int(e[1][1:])] = int(e[0][1:])

    new_partB = [partB[i] for i in b_assignments]

    return new_partB


def static_cost_function(ig, partitions):
    """
        Assumes the following fact:
            If a pair p interacts at time t, then in exactly 1 swap, the two can be made adjacent

        To consider: there exist schemes in which _both_ qubits must be moved into a different trap
        Consider the following:
            A - B, C - D, E - F at time t_0 with trap layout
            {A, B, E} {C, D, F} {}
        In order for E and F to interact, either 1. both need to move to trap 3
        or 2. We delay the operation of E and F until either A - B or C - D finishes

        If we care more about error rates of gates and qubit movements, we will tend to choose
        option 2. If coherence times are more important (not the case for NISQ algorithms)
        choose option 1.

        We choose option 2. Therefore the swap cost is always exactly 2.
        Choosing which to swap with depends on many factors, we won't choose one

        ~~~idea: choose which qubits to swap with in a way which minimizes average num
        of interactions~~~
    """
    # First color the nodes according to partitions
    for n in ig.nodes:
        for i, s in enumerate(partitions):
            if n in s:
                ig.nodes[n]['color'] = i

    total_move_cost = 0

    for e in ig.edges:
        # Edges which exist have weight 1, i.e. they interact
        if ig.nodes[e[0]]['color'] != ig.nodes[e[1]]['color']:
            # In a different trap. Move only one of them. No
            # preference in which to displace temporarily
            total_move_cost += 2 * ig.edges[e]['weight']

    return total_move_cost
