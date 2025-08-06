import itertools

import networkx as nx


def make_transition_graph(part1, part2):
    '''Makes a graph with a node for each bucket and and edge from node i to
    node j with weight k if k qubits move from bucket i to bucket j.

    part1 and part2 must be unpadded.'''
    assert len(part1) == len(part2)
    g = nx.DiGraph()
    # One node per bucket
    g.add_nodes_from(range(len(part1)))
    # One edge if a qubit need to move from bucket i to bucket j
    # weight=number of qubits that move from bucket i to bucket j
    g.add_edges_from(
        (i, j, {'weight': k})
        for i, b1_i in enumerate(part1)
        for j, b2_j in enumerate(part2)
        if i != j
        for k in (len(b1_i & b2_j),)
        if k > 0
    )
    return g

def count_true_swaps(part1, part2):
    g = make_transition_graph(part1, part2)
    counts = nx.get_edge_attributes(g, 'weight')

    cycles = sorted((tuple(cycle) for cycle in nx.simple_cycles(g)),
                    key=lambda cycle:(len(cycle), cycle))
    def gen_count():
        for cycle in cycles:
            max_count = min(counts[(cycle[i-1], cycle[i])]
                            for i in range(len(cycle)))
            if max_count > 0:
                for i in range(len(cycle)):
                    counts[(cycle[i-1], cycle[i])] -= max_count
                yield (len(cycle)-1) * max_count
    return sum(gen_count()) + sum(counts.values())

def count_path_true_swaps(path):
    return sum(count_true_swaps(path[i-1], path[i])
               for i in range(1, len(path)))
