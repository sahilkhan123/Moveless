from .. import partitioner
from ... import interaction_graphs

import networkx as nx


class GreedyMergeStaticPartitioner(partitioner.StaticPartitionerAbc):
    def __init__(self):
        """
        Uses a greedy approach to partition a circuit.

        Successively merges fine partitions until they are of proper size.
        """
        pass

    def partition_static(self, args):
        G = args.ig
        p, k = args.p, args.k

        if p * k < len(G.nodes):
            raise ValueError('Too many qubits')

        # Begin with all of the vertices in their own partition
        partitions = []
        for n in G.nodes:
            partitions.append({n})

        weights = nx.get_edge_attributes(G, 'weight')

        marginal_benefit = True
        while marginal_benefit:
            # Merge until there are fewer than k groups
            # Continue to merge if you can do so and not exceed bucket size, p
            pair = None
            total = float('inf')

            for i, p_1 in enumerate(partitions):
                for j, p_2 in enumerate(partitions):
                    if i != j and len(p_1) + len(p_2) <= p:
                        total_weight = 0
                        for edge in G.edges:
                            if (edge[0] in p_1 and edge[1] in p_2) or (edge[1] in p_1 and edge[0] in p_2):
                                total_weight += weights[edge]

                        if total_weight == 0:
                            total_weight = 1e-5

                        if total_weight > 0:
                            inverse_avg = (len(p_1) + len(p_2)) / total_weight # Dissuades super groups
                            if inverse_avg <= total:
                                total = inverse_avg
                                pair = (i, j)
            if pair is None:
                marginal_benefit = False
            else:
                partitions[pair[0]] = partitions[pair[0]].union(partitions[pair[1]])
                partitions.pop(pair[1])

        # It is possible to end with more than k buckets; need to correct for this
        while len(partitions) > k:
            # merge smallest buckets to others with best weight between
            smallest_bucket = partitions[0]
            w = 0

            for i, b in enumerate(partitions):
                if len(b) < len(smallest_bucket):
                    smallest_bucket = b
                    w = i

            which = -1
            total = -float('inf')
            for i, p1 in enumerate(partitions):
                if i != w:
                    total_weight = 0
                    for edge in G.edges:
                        if (edge[0] in p1 and edge[1] in smallest_bucket) or (edge[0] in smallest_bucket and edge[1] in p1):
                            total_weight += weights[edge]

                    if total_weight >= total:
                        total = total_weight
                        which = i

            partitions[which] = partitions[which].union(partitions[w])
            partitions.pop(w)

        # This can get stuck in something like {1, 2, 3}, {4, 5, 6}, {7, 8, 9} with buckets of size 5 and only 2 buckets
        # Check if all buckets are of size <= p
        # If not, correct by moving singletons until proper sized
        while not all(len(b) <= p for b in partitions):
            # Choose the best the singleton to move
            pair = None
            which_element = None
            best_gain = -float('inf')

            for i, fr in enumerate(partitions):
                if len(fr) > p:
                    for j, to in enumerate(partitions):
                        if len(to) < p:
                            if i != j:
                                for e in fr:
                                    gain = 0
                                    for edge in G.edges:
                                        if (edge[0] == e or edge[1] == e):
                                            if edge[0] in fr and edge[1] in fr:
                                                gain -= G.edges[edge]['weight']
                                            if edge[0] in to or edge[1] in to:
                                                gain += G.edges[edge]['weight']

                                    if gain > best_gain:
                                        gain = best_gain
                                        pair = (i, j)
                                        which_element = e
            # Move the element
            partitions[pair[0]].remove(which_element)
            partitions[pair[1]].add(which_element)


        # Pad for consistency later
        while len(partitions) < k:
            partitions.append(set())

        return partitioner.StaticPartitionResult(partitions)
