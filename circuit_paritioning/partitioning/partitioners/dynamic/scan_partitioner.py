from .. import partitioner
from ..static.oee_partitioner import OeeStaticPartitioner

from ..swap_count import (
        count_true_swaps
    )

from ..partitioner import PartitionerArgs

import networkx as nx

from scipy.stats import expon, norm, halfnorm
from ..util import match_partitions_minimum_swap, memoize
from ..path_util import unlabeled_path_to_labled_path

from ...graph import add_graphs

class ScanPartitioner(partitioner.PartitionerAbc):
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

        @memoize
        def _slice_ig(i, j):
            if i >= j:
                return None
            return add_graphs(weighted_mgs[i:j])

        @memoize
        def _slice_partitions(i, j):
            if i >= j:
                return None
            pargs = PartitionerArgs(None, _slice_ig(i, j), args.mgs[i:j], args.p, args.k)
            partition = self.local_partitioner.partition_graph(pargs)
            return partition

        def count_swaps(A, B):
            return self.stitching_cost_function(A, match_partitions_minimum_swap(A, B))

        if self.distribution not in self.SUPPORTED_DISTRIBUTIONS:
            return None
        else:
            distribution = self.SUPPORTED_DISTRIBUTIONS[self.distribution]


        ig, mgs, p, k = args.ig, args.mgs, args.p, args.k
        T = len(mgs)

        # Initialization for the loop
        initial_partition = self.local_partitioner.partition_graph(args)
        part_list = [initial_partition]
        final_part_list = part_list[:]
        stitch_costs = [0,0]
        int_list = [(0,T)]
        weighted_mgs = [nx.Graph(g) for g in mgs]
        total_cost = initial_partition.total_swaps
        curr_total_cost = total_cost
        if distribution is not None:
             weighted_mgs = _new_convolution(weighted_mgs, distribution, self.sigma)
        else:
            weighted_mgs = mgs

        for i in range(1, T):
            curr_int = 0
            improvement = -1 * p * k * len(mgs)
            best_config = (-1, -1, -1, -1, -1, -1)
            for test in range(1, T):
                # decide on a cut
                interval = int_list[curr_int]
                if test == interval[1]:
                    curr_int = curr_int + 1
                    continue
                lint = (interval[0], test)
                rint = (test, interval[1])

                lpart = _slice_partitions(lint[0], lint[1])
                rpart = _slice_partitions(rint[0], rint[1])
                prev_to_left = right_to_next = 0
                if curr_int > 0:
                    prev_to_left = count_swaps(part_list[curr_int-1].path[-1], lpart.path[0])
                left_to_right = count_swaps(lpart.path[-1], rpart.path[0])
                if curr_int < len(int_list) - 1:
                    right_to_next = count_swaps(rpart.path[-1], part_list[curr_int+1].path[0])
                new_cost = lpart.total_swaps + rpart.total_swaps + prev_to_left + left_to_right + right_to_next
                old_cost = part_list[curr_int].total_swaps
                old_cost = old_cost + stitch_costs[curr_int]
                old_cost = old_cost + stitch_costs[curr_int+1]

                if old_cost - new_cost > improvement: # we can replace it
                    improvement = old_cost - new_cost
                    best_config = (test, curr_int, lpart, rpart, prev_to_left, left_to_right, right_to_next)
            # make a cut
            test, curr_int, lpart, rpart, prev_to_left, left_to_right, right_to_next = best_config
            part_list[curr_int] = rpart
            part_list.insert(curr_int, lpart)

            stitch_costs[curr_int] = prev_to_left
            stitch_costs[curr_int+1] = right_to_next
            stitch_costs.insert(curr_int+1, left_to_right)

            interval = int_list[curr_int]
            int_list[curr_int] = (test, interval[1])
            int_list.insert(curr_int, (interval[0], test))

            curr_total_cost = curr_total_cost - improvement
            if curr_total_cost < total_cost:
                total_cost = curr_total_cost
                final_part_list = part_list[:]
                final_int_list = int_list[:]

        final_path = []
        for part in final_part_list:
            final_path.extend(part.path)
        pr = partitioner.PartitionResult(path=unlabeled_path_to_labled_path(final_path))

        return pr
