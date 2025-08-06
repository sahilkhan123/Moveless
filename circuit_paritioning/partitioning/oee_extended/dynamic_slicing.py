from .. import interaction_graphs
from .. import partitioner
from ..baselines import OeePartitionerStatic

from .true_swaps import (
		count_true_swaps
	)

from .partition_labeling import (
		clean_partition,
	)

import networkx as nx
from ..baselines import static_cost_function

from scipy.stats import expon, norm, halfnorm


class DynamicSlicingPartitioner(partitioner.PartitionerAbc):
	SUPPORTED_DISTRIBUTIONS = {
            None: None,
            'none': None,
            'expon': expon,
            'norm': norm,
            'halfnorm': halfnorm,
        }


	def __init__(self, distribution='expon', sigma=1, one_sided=True,
					spike_value=10, number_of_starting_samples=10,
					seed=None, prng=None, local_partitioner=OeePartitionerStatic(),
					internal_cost_function=static_cost_function,
					stitching_cost_function=count_true_swaps,
					partition_parameters=None, slice_length=1):

		self.distribution = distribution
		self.sigma = sigma
		self.one_sided = one_sided
		self.spike_value = spike_value
		self.number_of_starting_samples = number_of_starting_samples
		self.seed = seed
		self.prng = prng
		self.local_partitioner = local_partitioner
		self.slice_length = slice_length
		self.internal_cost_function = internal_cost_function
		self.stitching_cost_function = stitching_cost_function
		self.partition_parameters = partition_parameters # For future parameterization

	def run(self, circuit, p, k, **kwargs):

		def _compose_moments(A, B):
			'''
			takes two moments m1 and m2 and generates a new graph with
			the same set of vertices and the weights of the edges added

			Args:
				A: nx.Graph() representing the first moment
				B: nx.Graph() representing the second moment

			Returns:
				C: a moment which is the composition of A and B with edge weights added
			'''
			C = nx.compose(A, B)
			for e in C.edges:
				weight = 0
				if e in A.edges:
					weight += A.edges[e]['weight'] if 'weight' in A.edges[e].keys() else 1
				if e in B.edges:
					weight += B.edges[e]['weight'] if 'weight' in B.edges[e].keys() else 1

				C.edges[e]['weight'] = weight
			return C

		def _compose_moment_list(moments):
			'''
			given a list of moments, generates the composition of all these moments, adding edge weights
			uses _compose_moments

			Args:
				moments: a list of nx.Graph()'s representing each moment

			Returns:
				a single moment, the composition of the entire moments list
			'''
			total_moment = moments[0]
			for i in range(1, len(moments)):
				total_moment = _compose_moments(total_moment, moments[i])
			return total_moment

		def _new_convolution(moments, dist, scale=1):
			# Modify the moment weights inplace based on the distribution
			for i, m in enumerate(moments):
				for edge in m.edges:
					for j in range(i):
						n = moments[j]
						if edge not in n.edges:
							n.add_edge(*edge, weight=dist.pdf(abs(j-i), scale=scale)) * m.edges[edge]['weight']
						else:
							n.edges[edge]['weight'] += dist.pdf(abs(j-i), scale=scale) * m.edges[edge]['weight']

			return moments

		if self.distribution not in self.SUPPORTED_DISTRIBUTIONS:
			return None
		else:
			distribution = self.SUPPORTED_DISTRIBUTIONS[self.distribution]


		ig, mgs = interaction_graphs.circuit_to_graphs(circuit)

		# Initialization for the loop
		combined_moments = []
		best_overall_cost = self.internal_cost_function(ig, self.local_partitioner.run(None,p,k,graph=ig).path[0])
		current_overall_cost = best_overall_cost

		current_partitions = [[0,len(mgs), best_overall_cost, 0, 0]]
		part_list = [self.local_partitioner.run(None,p,k,graph=ig)]
		weighted_partitions = [nx.Graph(g) for g in mgs]
		if distribution is not None:
			 _new_convolution(weighted_partitions, distribution, self.sigma)

		best_partitions = current_partitions # hold intervals
		best_part_list = part_list # holds partition objects
		for cuts_made in range(1,len(mgs)-1):
			curr_slice = 0
			slice_index = -1
			slice_to_be_cut = -1
			cost_to_overwrite = current_partitions[curr_slice][2] + current_partitions[curr_slice][3] + current_partitions[curr_slice][4]
			best_change = len(mgs) * p * k

			for cut in range(1,len(mgs)):
				if current_partitions[curr_slice][1] == cut:
					curr_slice = curr_slice + 1
					cost_to_overwrite = current_partitions[curr_slice][2] + current_partitions[curr_slice][3] + current_partitions[curr_slice][4]
					continue
				left_start = current_partitions[curr_slice][0]
				right_end = current_partitions[curr_slice][1]
				left_slice = _compose_moment_list(mgs[left_start:cut])
				right_slice = _compose_moment_list(mgs[cut:right_end])

				# seed with the current partition object
				weighted_left_slice = _compose_moment_list(weighted_partitions[left_start:cut])
				weighted_right_slice = _compose_moment_list(weighted_partitions[cut:right_end])
				left_partition = self.local_partitioner.run(part_list[curr_slice].path[0], p, k, graph=weighted_left_slice)
				right_partition = self.local_partitioner.run(part_list[curr_slice].path[0], p, k, graph=weighted_right_slice)

				left_static = self.internal_cost_function(left_slice, left_partition.path[0])
				right_static = self.internal_cost_function(right_slice, right_partition.path[0])

				stitch_cost = self.stitching_cost_function(left_partition.path[0], right_partition.path[0], graph_size=len(left_slice.nodes))
				left_stitch = 0
				right_stitch = 0
				if curr_slice > 0:
					left_stitch = self.stitching_cost_function(part_list[curr_slice-1].path[0], left_partition.path[0], graph_size=len(left_slice.nodes))
				if curr_slice < len(current_partitions) - 1:
					right_stitch = self.stitching_cost_function(right_partition.path[0], part_list[curr_slice+1].path[0], graph_size=len(right_slice.nodes))
				changed_cost = left_static + right_static + stitch_cost + left_stitch + right_stitch

				if best_change > changed_cost - cost_to_overwrite: # if we can improve more
					best_change = changed_cost - cost_to_overwrite
					slice_to_be_cut = curr_slice
					slice_index = cut
					best_left = left_partition
					best_right = right_partition
					best_left_static = left_static
					best_right_static = right_static
					best_left_stitch = left_stitch
					best_right_stitch = right_stitch
					best_middle_stitch = stitch_cost

			part_list.pop(slice_to_be_cut)
			part_list.insert(slice_to_be_cut, best_right)
			part_list.insert(slice_to_be_cut, best_left)

			# update stitch costs of adjacent partitions
			if slice_to_be_cut > 0:
				current_partitions[slice_to_be_cut-1][4] = best_left_stitch
			if slice_to_be_cut < len(current_partitions) - 1:
				current_partitions[slice_to_be_cut+1][3] = best_right_stitch
			interval = current_partitions.pop(slice_to_be_cut)
			# insert the new right partition
			current_partitions.insert(slice_to_be_cut, [slice_index, interval[1], best_right_static, best_middle_stitch, best_right_stitch])
			# insert the new left partition
			current_partitions.insert(slice_to_be_cut, [interval[0], slice_index, best_left_static, best_left_stitch, best_middle_stitch])
			current_overall_cost = current_overall_cost + best_change

			# If we get overall improvement, then we save it
			if current_overall_cost < best_overall_cost:
				best_overall_cost = current_overall_cost
				best_partitions = current_partitions
				best_part_list = part_list

		final_list = [part.path[0] for part in best_part_list]
		pr = partitioner.PartitionResult(path=final_list, total_swaps=best_overall_cost, swap_order=[])

		return pr
