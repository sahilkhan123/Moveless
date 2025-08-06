from scipy.stats import expon, norm, halfnorm

from ...graph import add_graphs
from .. import partitioner
from ..partitioner import PartitionerArgs
import networkx as nx
from ..static.oee_partitioner import OeeStaticPartitioner
from .lookahead_util import convolve
from ..path_util import (
	unlabeled_path_to_labled_path
)

class MergeDynamicPartitioner(partitioner.PartitionerAbc):
	SUPPORTED_DISTRIBUTIONS = {
            None: None,
            'none': None,
            'expon': expon,
            'norm': norm,
            'halfnorm': halfnorm,
    }

	def __init__(self, 
				local_partitioner=OeeStaticPartitioner(),
				distribution='expon',
				sigma=1,
				 **kwargs):

		self.distribution = distribution
		self.sigma = sigma
		self.local_partitioner = local_partitioner


	def partition_graph(self, args):
		"""
			Deciding on where to slice based on when things become too large
			for buckets

		"""

		def _get_components_(graph):
			return list(nx.algorithms.components.connected_components(graph))

		def _exceeds_p_(partition, p):
			return any([len(b) > p for b in partition])

		def _next_slice_(t_start, mgs, p):
			t_end = t_start

			current_moments = mgs[t_start]
			last_satisfying = current_moments
			current_group = _get_components_(current_moments)

			while True:
				t_end += 1

				if t_end >= len(mgs):
					return current_moments, t_end
				else:
					test_moments = add_graphs(mgs[t_start:t_end])
					test_group = _get_components_(test_moments)

					if not _exceeds_p_(test_group, p):
						current_moments	 = test_moments
					else:
						break

			return current_moments, t_end


		mgs = args.mgs

		if self.distribution in self.SUPPORTED_DISTRIBUTIONS:
			distribution = self.SUPPORTED_DISTRIBUTIONS[self.distribution]
		else:
			distribution = None

		if distribution is not None:
			lookahead_mgs = convolve(mgs, distribution, self.sigma)
		else:
			lookahead_mgs = [nx.Graph(m) for m in mgs] # Just copy with no lookahead


		# Merge moments until something exceeds the size of p
		t_start = 0
		current_moments, t_end = _next_slice_(t_start, mgs, args.p)
		slices = [current_moments]
		lookahead_slices = [add_graphs(lookahead_mgs[t_start:t_end])]
		mgs_list = [mgs[t_start:t_end]]
		t_start = t_end

		while t_start < len(mgs):
			current_moments, t_end = _next_slice_(t_start, mgs, args.p)
			lookahead_slices.append(add_graphs(lookahead_mgs[t_start:t_end]))
			slices.append(current_moments)
			mgs_list.append(mgs[t_start:t_end])
			t_start = t_end

		arg_list = [PartitionerArgs(circuit=None, ig=lookahead_slices[i], mgs=mgs_list[i], p=args.p, k=args.k, **args.kwargs)
					for i in range(len(lookahead_slices))]

		static_partition_results = [self.local_partitioner.partition_graph(x) for x in arg_list]

		total_path = static_partition_results[0].path
		for i in range(1, len(static_partition_results)):
			total_path += static_partition_results[i].path

		new_total_path = unlabeled_path_to_labled_path(total_path)

		assert len(new_total_path) == len(mgs), "Produced improper path length!"
		return partitioner.PartitionResult(path=new_total_path)



