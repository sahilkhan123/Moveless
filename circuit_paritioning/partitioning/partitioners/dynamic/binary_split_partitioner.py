from .. import partitioner
from ..static.oee_partitioner import OeeStaticPartitioner

from ..swap_count import (
    count_true_swaps
    )
from ..partitioner import PartitionerArgs

import networkx as nx
#from ..baselines import static_cost_function

from scipy.stats import expon, norm, halfnorm
from ..util import match_partitions_minimum_swap
from ..path_util import unlabeled_path_to_labled_path

from ...graph import add_graphs

class BinarySplitPartitioner(partitioner.PartitionerAbc):
    SUPPORTED_DISTRIBUTIONS = {
            None: None,
            'none': None,
            'expon': expon,
            'norm': norm,
            'halfnorm': halfnorm,
        }


    def __init__(self, distribution='expon', sigma=1,
        local_partitioner=OeeStaticPartitioner(),
        stitching_cost_function=count_true_swaps):
        self.distribution = distribution
        self.sigma = sigma
        self.local_partitioner = local_partitioner
        self.stitching_cost_function = stitching_cost_function

    def partition_graph(self, args):

        def _new_convolution(moments, dist, scale=1):
            # Modify the moment weights inplace based on the distribution
            for i, m in enumerate(moments):
                for edge in m.edges:
                    for j in range(i):
                        n = moments[j]
                        if edge not in n.edges:
                            n.add_edge(*edge, weight=dist.pdf(abs(j-i) * m.edges[edge]['weight'], scale=scale))
                        else:
                            n.edges[edge]['weight'] += dist.pdf(abs(j-i), scale=scale) * m.edges[edge]['weight']
            return moments

        if self.distribution not in self.SUPPORTED_DISTRIBUTIONS:
            return None
        else:
            distribution = self.SUPPORTED_DISTRIBUTIONS[self.distribution]


        ig, mgs = args.ig, args.mgs
        T = len(mgs)
        if T <= 1:
            part = self.local_partitioner.partition_graph(args)
            return partitioner.PartitionResult(path=part.path)

        weighted_partitions = [nx.Graph(g) for g in mgs]
        if distribution is not None:
            _new_convolution(weighted_partitions, distribution, self.sigma)


        partition = self.local_partitioner.partition_graph(args)
        p_list = [(partition, args)]
        finished_partitions = []

        while len(p_list) > 0:
            partition, cargs = p_list.pop()
            mgs = cargs.mgs
            T = len(mgs)
            if T == 1:
                finished_partitions.append(partition)
                continue
            split = T//2
            left_args = PartitionerArgs(None, add_graphs(weighted_partitions[0:split]), mgs[0:split], args.p, args.k, init_parts=partition.path[0])
            right_args = PartitionerArgs(None, add_graphs(weighted_partitions[split:T]), mgs[split:T], args.p, args.k, init_parts=partition.path[-1])
            p_left = self.local_partitioner.partition_graph(left_args)
            p_right = self.local_partitioner.partition_graph(right_args)
            stitch = self.stitching_cost_function(p_left.path[-1], match_partitions_minimum_swap(p_left.path[-1], p_right.path[0]))

            if stitch + p_left.total_swaps + p_right.total_swaps <= partition.total_swaps:
                p_list.append((p_right, right_args))
                p_list.append((p_left, left_args))
            else:
                finished_partitions.append(partition)

        final_path = []
        for i in range(len(finished_partitions)):
            final_path.extend(finished_partitions[i].path)
        pr = partitioner.PartitionResult(path=unlabeled_path_to_labled_path(final_path))
        return pr
