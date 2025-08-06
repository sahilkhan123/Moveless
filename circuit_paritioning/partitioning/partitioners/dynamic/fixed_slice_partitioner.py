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

from ...graph import add_graphs

class FixedSlicePartitioner(partitioner.PartitionerAbc):
	SUPPORTED_DISTRIBUTIONS = {
            None: None,
            'none': None,
            'expon': expon,
            'norm': norm,
            'halfnorm': halfnorm,
        }

	def __init__(self, distribution='expon',
						sigma=1,
						local_partitioner=OeeStaticPartitioner(),
						**kwargs):

		self.distribution = distribution
		self.sigma = sigma
		self.local_partitioner = local_partitioner

	def _convolve(self, mgs, distribution):
		"""
		returns a COPIED set of moments, with modified weights

		"""
		moments = [nx.Graph(m) for m in mgs]

		for i, m in enumerate(moments):
			for edge in m.edges:
				for j in range(i):
					n = moments[j]
					if edge not in n.edges:
						n.add_edge(*edge, weight=distribution.pdf(abs(j-i), scale=self.sigma) * m.edges[edge]['weight'])
					else:
						n.edges[edge]['weight'] += distribution.pdf(abs(j-i), scale=self.sigma) * m.edges[edge]['weight']
		return moments

	def partition_graph(self, args):
		if self.distribution not in self.SUPPORTED_DISTRIBUTIONS:
			self.distribution = None
		else:
			distribution = self.SUPPORTED_DISTRIBUTIONS[self.distribution]

		ig, mgs = args.ig, args.mgs
		num_moments = len(mgs)
		slice_length = args.slice_len

		# Build a list of moments of the desired length
		combined_moments = []
		slice_mgs = []
		i = 0
		while min(i + slice_length, num_moments) == i + slice_length:
			combined_moments.append(add_graphs(mgs[i:i+slice_length]))
			slice_mgs.append(mgs[i:i+slice_length])
			i += slice_length
		if i < num_moments:
			combined_moments.append(add_graphs(mgs[i:]))
			slice_mgs.append(mgs[i:])

		# Apply the lookahead function, if desired
		if distribution is not None:
			combined_moments = self._convolve(combined_moments, distribution)

		# Generate the arg lists
		targs = PartitionerArgs(circuit=None, ig=ig, mgs=mgs, p=args.p, k=args.k, **args.kwargs)
		part_result = self.local_partitioner.partition_graph(targs)
		static_partition_results = []
		for i in range(len(combined_moments)):
			targs = PartitionerArgs(circuit=None, ig=combined_moments[i], mgs=slice_mgs[i], p=args.p, k=args.k, init_parts=part_result.path[-1], **args.kwargs)
			part_result = self.local_partitioner.partition_graph(targs)
			static_partition_results.append(part_result)

		total_path = static_partition_results[0].path

		for i in range(1, len(static_partition_results)):
			total_path += static_partition_results[i].path

		new_total_path = unlabeled_path_to_labled_path(total_path)

		return partitioner.PartitionResult(path=new_total_path)
