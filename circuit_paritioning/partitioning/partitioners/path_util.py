from . import util

def path_from_static_partition(static_partition, moment_graphs, p, k, relabel=True):
    '''Finds a reasonable path where each partition has the fewest possible
    moved qubits from the static partition.

    static_partition is assumed to be unpadded.'''
    n = util.num_qubits_in_partitioning(static_partition)
    padded_static = util.pad_partitioning(static_partition, n, p, k)
    padded_path = padded_path_from_static_padded_partition(
                        padded_static, moment_graphs)


    if relabel:
        labeled_padded_path = unlabeled_path_to_labled_path(padded_path, n)
        labeled_unpadded_path = [util.unpad_partitioning(parts, n, p, k) for parts in labeled_padded_path]
        return labeled_unpadded_path
    else:
        path = [util.unpad_partitioning(parts, n, p, k) for parts in padded_path]
        return path

def unlabeled_path_to_labled_path(unlabled, n=None):
    lp = [unlabled[0]]
    for i in range(1, len(unlabled)):
        lp.append(util.match_partitions_minimum_swap(lp[-1], unlabled[i], n))
    return lp

def padded_path_from_static_padded_partition(static_partition, moment_graphs):
    partitions_from_start = []

    for moment in moment_graphs:
        new_partition = [set(bucket) for bucket in static_partition]

        for u, v in moment.edges:
            # Check if the two endpoints are in the same bucket
            bucket_u = None
            bucket_v = None
            for i, bucket in enumerate(new_partition):
                if u in bucket:
                    bucket_u = i
                if v in bucket:
                    bucket_v = i

            if bucket_u != bucket_v:
                # See if there is something that wants to directly swap
                w1, w2 = _direct_swap(moment, new_partition, bucket_u, bucket_v, u, v)
                if w2 == v:
                    _perform_swap(new_partition, bucket_v, bucket_u, v, w1)
                elif w2 == u:
                    _perform_swap(new_partition, bucket_u, bucket_v, u, w1)
                else:
                    # No immediate nice swaps. So just attempt to choose something that isn't bound
                    # to either bucket_u or bucket_v to swap
                    o1, o2 = _find_other(moment, new_partition, bucket_u, bucket_v, u, v)
                    if o2 == v:
                        _perform_swap(new_partition, bucket_v, bucket_u, v, o1)
                    elif o2 == u:
                        _perform_swap(new_partition, bucket_u, bucket_v, u, o1)
                    else:
                        # Its not possible to get the two elements together in this bucket. Need to find
                        # Some bucket with 2 open spaces. If we can't, there is too much parallelism
                        x, y, z = _find_open_pair(moment, new_partition, bucket_u, bucket_v)
                        assert x is not None, 'Too many parallel operations occuring!'
                        # found
                        _perform_swap(new_partition, bucket_v, x, v, y)
                        _perform_swap(new_partition, bucket_u, x, u, z)

        partitions_from_start.append(new_partition)
    assert len(partitions_from_start) == len(moment_graphs), f'?'
    return partitions_from_start

def _perform_swap(sp, b1, b2, e1, e2):
    sp[b1].remove(e1)
    sp[b2].add(e1)

    sp[b2].remove(e2)
    sp[b1].add(e2)

def _direct_swap(moment, sp, bu, bv, u, v):
    for e in sp[bu]:
        if e != u:
            for ed in moment.edges:
                if (ed[0] == e and ed[1] in sp[bv]) or (ed[1] == e and ed[0] in sp[bv]):
                    return e, v

    for e in sp[bv]:
        if e != v:
            for ed in moment.edges:
                if (ed[0] == e and ed[1] in sp[bu]) or (ed[1] == e and ed[0] in sp[bu]):
                    return e, u

    return None, None

def _find_other(m, sp, bu, bv, u, v):
    for e in sp[bu]:
        if e != u:
            in_edge_within_bucket = False
            for ed in m.edges:
                if (ed[0] == e and ed[1] in sp[bu]) or (ed[1] == e and ed[0] in sp[bu]):
                    in_edge_within_bucket = True
                    break
            if not in_edge_within_bucket:
                return e, v

    for e in sp[bv]:
        if e != v:
            in_edge_within_bucket = False
            for ed in m.edges:
                if (ed[0] == e and ed[1] in sp[bv]) or (ed[1] == e and ed[0] in sp[bv]):
                    in_edge_within_bucket = True
                    break
            if not in_edge_within_bucket:
                return e, u

    return None, None

def _find_open_pair(m, sp, bu, bv):
    for i, b in enumerate(sp):
        if i != bu and i != bv:
            free = []
            for e in b:
                in_edge_within_bucket = False
                for edge in m.edges:
                    if (edge[0] == e and edge[1] in b) or (edge[1] == e and edge[0] in b):
                        in_edge_within_bucket = True
                if not in_edge_within_bucket:
                    free.append(e)
            if len(free) >= 2:
                return i, free[0], free[1]
    return None, None, None


def process_static_partition(partition, graph, moments, p):
    # Pad the partition
    i = len(graph.nodes)
    for pt in partition:
        while len(pt) < p:
            pt.add(i)
            i += 1

    path = path_from_static_partition(partition, moments)

    labeled_path = [path[0]]
    for i in range(1, len(path)):
        labeled_path.append(partition_labeling.partition_labeling(path[i-1], path[i], len(graph.nodes)))

    cleaned_path = [partition_labeling.clean_partition(pp, len(graph.nodes)) for pp in labeled_path]
    path_cost = true_swaps.count_path_true_swaps(cleaned_path)

    r = partitioner.PartitionResult(path=cleaned_path, total_swaps=path_cost, swap_order=[], old_swaps=static_cost_function(graph, partition))
    return r
