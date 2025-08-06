from .. import partitioner
from ..static.oee_partitioner import OeeStaticPartitioner

from ..swap_count import (
        count_true_swaps
    )

from ..partitioner import PartitionerArgs

import networkx as nx

from scipy.stats import expon, norm, halfnorm
from ..util import match_partitions_minimum_swap
from ..path_util import unlabeled_path_to_labled_path
from heapq import heappush, heappop, heapify
import numpy as np

from ...graph import add_graphs

class ClusterPartitioner(partitioner.PartitionerAbc):

    def __init__(self, local_partitioner=OeeStaticPartitioner()):
        self.local_partitioner = local_partitioner

    def partition_graph(self, args):

        ig, mgs, p, k = args.ig, args.mgs, args.p, args.k

        # Initialization for the loop
        cc_list = []
        for i in range(len(mgs)):
            for j in range(i+1, len(mgs)+1):
                graph = add_graphs(mgs[i:j])
                cc = nx.number_connected_components(graph)
                #cc = nx.average_clustering(graph)
                weight = ((k / cc) + np.log(cc))
                #weight = cc / (j-i)
                cc_list.append((cc, i, j))
        heapify(cc_list)

        splits = []
        while len(cc_list) > 0:
            _, i, j = heappop(cc_list)
            for interval in splits:
                if i >= interval[0] and i < interval[1]:
                    break
                if j >= interval[0] and j < interval[1]:
                    break
                if i <= interval[0] and j > interval[0]:
                    break
                if i < interval[1] and j >= interval[1]:
                    break
            else:
                splits.append((i,j))
        splits.sort()

        fixed_splits = []
        current = 0
        for interval in splits:
            if current == interval[0]:
                fixed_splits.append(interval)
                current = interval[1]
            else:
                for i in range(current, interval[0]):
                    fixed_splits.append((i,i+1))

        splits = fixed_splits

        parts = []
        targs = PartitionerArgs(None, ig, mgs, p, k)
        seed_part = self.local_partitioner.partition_graph(targs)
        for i, j in splits:
            targs = PartitionerArgs(None, add_graphs(mgs[i:j]), mgs[i:j], p, k, init_parts=seed_part.path[0])
            seed_part = self.local_partitioner.partition_graph(targs)
            parts.append(seed_part)

        final_path = []
        for part in parts:
            final_path.extend(part.path)
        pr = partitioner.PartitionResult(path=unlabeled_path_to_labled_path(final_path))

        return pr
