from .. import partitioner
from ..static.oee_partitioner import OeeStaticPartitioner

from ..swap_count import (
    count_true_swaps
    )
from ..partitioner import PartitionerArgs

import networkx as nx
#from ..baselines import static_cost_function

from scipy.stats import expon, norm, halfnorm
from heapq import heappush, heappop, heapify # heap used for A*
from ..util import match_partitions_minimum_swap, memoize
from ..path_util import unlabeled_path_to_labled_path

from ...graph import add_graphs

class AStarPartitioner(partitioner.PartitionerAbc):
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
            return add_graphs(weighted_partitions[i:j])

        @memoize
        def _slice_partitions(i, j):
            if i >= j:
                return None
            pargs = PartitionerArgs(None, _slice_ig(i, j), args.mgs[i:j], args.p, args.k)
            partition = self.local_partitioner.partition_graph(pargs)
            return partition

        @memoize
        def _slice_costs(i, j):
            if i >= j:
                return 0
            return _slice_partitions(i,j).total_swaps

        @memoize
        def _stitch(i, j, k):
            if i >= j or j >= k or i >= k:
                return 0
            leftp = _slice_partitions(i, j)
            rightp = _slice_partitions(j, k)
            return self.stitching_cost_function(leftp.path[-1], match_partitions_minimum_swap(leftp.path[-1], rightp.path[0]))


        if self.distribution not in self.SUPPORTED_DISTRIBUTIONS:
            return None
        else:
            distribution = self.SUPPORTED_DISTRIBUTIONS[self.distribution]


        ig, mgs = args.ig, args.mgs
        T = len(mgs)
        weighted_partitions = [nx.Graph(g) for g in mgs]
        if distribution is not None:
            _new_convolution(weighted_partitions, distribution, self.sigma)

        # Implementation of the A* algorithm
        open_list = []
        for i in range(1,T+1):
            # f = g + h
            cost_to_slice = _slice_costs(0,i) + _slice_costs(i,T) + _stitch(0,i,T)
            # partition cost, start, stop, and parent, running cost
            open_list.append((cost_to_slice, 0, i, None, _slice_costs(0,i)))
        heapify(open_list)
        #closed_list = []
        while len(open_list) > 0:
            current_node = heappop(open_list)
            #closed_list.append(current_node)
            if current_node[2] >= T:
                # we can reach the end with minimum estimated cost
                break
            # create the childeren
            for i in range(current_node[2]+1,T+1):
                left_part = _slice_partitions(current_node[1], current_node[2])
                right_part = _slice_partitions(current_node[2], i)
                heuristic = _slice_costs(i, T) + _stitch(current_node[2], i, T)
                stitch_cost = _stitch(current_node[1], current_node[2], i)
                # compute heuristic
                cost_so_far = current_node[4] + right_part.total_swaps + stitch_cost
                child = (cost_so_far + heuristic, current_node[2], i, current_node, cost_so_far)
                heappush(open_list, child)

        best_node = current_node

        final_path = []
        while current_node[3] is not None:
            final_path.extend(_slice_partitions(current_node[1], current_node[2]).path)
            current_node = current_node[3]
        final_path.extend(_slice_partitions(current_node[1], current_node[2]).path)
        final_path.reverse()
        pr = partitioner.PartitionResult(path=unlabeled_path_to_labled_path(final_path))
        return pr
