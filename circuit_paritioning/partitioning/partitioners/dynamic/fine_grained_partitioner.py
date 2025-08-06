from .. import partitioner, oee, util
from ..partitioner import PartitionerArgs

import networkx as nx

from scipy.stats import expon, norm, halfnorm
from ..path_util import (
	unlabeled_path_to_labled_path
)

class Expon2:
    @staticmethod
    def pdf(x, scale=1):
        return (1/2**x + ((1/1e2 - x/(scale*1e8)) * (x >= 0)))
class FineGrainedPartitioner(partitioner.PartitionerAbc):
    SUPPORTED_DISTRIBUTIONS = {
            None: None,
            'none': None,
            'expon': expon,
            'norm': norm,
            'halfnorm': halfnorm,
            'expon2': Expon2,
        }

    # number of samples deprcated
    def __init__(self, distribution='expon', sigma=1, seed=0):
        self. distribution = distribution
        self.sigma = sigma
        self.seed = seed

    def _spike_and_convolve(self, mgs, distribution):
        """
        returns a COPIED set of moments, with modified weights

        """
        moments = [nx.Graph(m) for m in mgs]
        spike_val = 10

        for i, m in enumerate(moments):
            for edge in m.edges:
                moments[i].edges[edge]['weight'] = spike_val
                for j in range(i):
                    n = moments[j]
                    if edge not in n.edges:
                        n.add_edge(*edge, weight=distribution.pdf(abs(j-i), scale=self.sigma))
                        #n.add_edge(*edge, weight=1/2**(abs(j-i)))
                    else:
                        n.edges[edge]['weight'] += (distribution.pdf(abs(j-i), scale=self.sigma))
        return moments

    def partition_graph(self, args):
        if self.distribution not in self.SUPPORTED_DISTRIBUTIONS:
            self.distribution = None
        else:
            distribution = self.SUPPORTED_DISTRIBUTIONS[self.distribution]

        ig, mgs = args.ig, args.mgs
        num_moments = len(mgs)
        n = len(ig)

        if distribution is not None:
            lookahead_mgs = self._spike_and_convolve(mgs, distribution)
        else:
            lookahead_mgs = mgs

        path = []
        seed_parts = oee.oee_on_graph(ig, p=args.p, k=args.k, seed=self.seed+args.repeat)
        for i in range(num_moments):
            seed_parts = oee.oee_on_graph(lookahead_mgs[i], p=args.p, k=args.k, seed=self.seed + args.repeat, init_parts=seed_parts)
            path.append(util.unpad_partitioning(seed_parts, n, p=args.p, k=args.k))

        return partitioner.PartitionResult(path=unlabeled_path_to_labled_path(path))
