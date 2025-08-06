from .. import partitioner
from ..static.oee_partitioner import OeeStaticPartitioner
# from ..smt.smt_static_partitioner import SmtStaticPartitioner


from ..swap_count import (
	count_true_swaps
)

from ..util import (
	match_partitions_minimum_swap
)

from ..path_util import (
	unlabeled_path_to_labled_path
)

from ..partitioner import PartitionerArgs

import networkx as nx

from scipy.stats import expon, norm, halfnorm

from .fixed_slice_partitioner import FixedSlicePartitioner

import itertools


class BestFixedSlicePartitioner(partitioner.PartitionerAbc):
	SUPPORTED_DISTRIBUTIONS = {
            None: None,
            'none': None,
            'expon': expon,
            'norm': norm,
            'halfnorm': halfnorm,
    }

	def __init__(self, distribution='expon',
						sigma=1,
						one_sided=True,
						local_partitioner=OeeStaticPartitioner(),
						**kwargs):

		self.distribution = distribution
		self.sigma = sigma
		self.one_sided = one_sided
		self.local_partitioner = local_partitioner
		self.kwargs = kwargs

	def partition_graph(self, args):
		if self.distribution not in self.SUPPORTED_DISTRIBUTIONS:
			return None
		else:
			distribution = self.SUPPORTED_DISTRIBUTIONS[self.distribution]

		ig, mgs = args.ig, args.mgs
		T = len(mgs)


		best_cost = float('inf')
		best_path = None
		for slice_length in itertools.chain(range(1, int((T+1)/2)), [T+1]):
			new_args = args.copy()
			new_args.slice_len = slice_length

			r = FixedSlicePartitioner(distribution=self.distribution,
										sigma=self.sigma,
										local_partitioner=self.local_partitioner,
										one_sided=self.one_sided,
										**self.kwargs
										).partition_graph(new_args)
			if r.total_swaps < best_cost:
				best_cost = r.total_swaps
				best_path = r.path

		return partitioner.PartitionResult(path=best_path)
			
