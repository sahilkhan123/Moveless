from .. import partitioner
from ..swap_count import (
        count_true_swaps
    )

from ..partitioner import PartitionerArgs

import numpy as np
import networkx as nx

from scipy.stats import expon, norm, halfnorm
from ..util import ( match_partitions_minimum_swap, unpad_partitioning )
from ..path_util import unlabeled_path_to_labled_path
from collections import Counter
import operator
from ..static.oee_partitioner import OeeStaticPartitioner



class ExponLin:
    @staticmethod
    def pdf(x, scale=1):
        return (1/2**x + ((1/1e2 - x/(scale*1e8)) * (x >= 0)))

class Expon:
    @staticmethod
    def pdf(x, scale=1):
        return (2**(-x/scale)) * (x >= 0)

class HalfNorm:
    @staticmethod
    def pdf(x, scale=1):
        return (np.e**(-x**2 / scale**2)) * (x >= 0)

class Constant:
    @staticmethod
    def pdf(x, scale=1):
        return (x <= scale) * (x >= 0)


class LazyLookaheadPartitioner(partitioner.PartitionerAbc):
	SUPPORTED_DISTRIBUTIONS = {
            None: None,
            'none': None,
            'expon': Expon,
            'norm': norm,
            'halfnorm': HalfNorm,
            'const': Constant,
            'normalized-linear': 'nl',
        }

	def __init__(self, distribution='expon',
					sigma=1,
					local_partitioner=OeeStaticPartitioner(),
					**kwargs):
		self.local_partitioner = local_partitioner
		self.distribution = distribution
		self.sigma = sigma

	@staticmethod
	def convolve(mgs, distribution, sigma):
		"""
		returns a COPIED set of moments, with modified weights

		"""
		moments = [nx.Graph(m) for m in mgs]

		for i, m in enumerate(moments):
			for edge in m.edges:
				for j in range(i):
					n = moments[j]
					if edge not in n.edges:
						n.add_edge(*edge, weight=distribution.pdf(abs(j-i), scale=sigma) * m.edges[edge]['weight'])
					else:
						n.edges[edge]['weight'] += distribution.pdf(abs(j-i), scale=sigma) * m.edges[edge]['weight']
		return moments

	@staticmethod
	def normalized_distance_weights(mgs):
		moments = [nx.Graph(m) for m in mgs]

		for i, m in enumerate(moments):
			for edge in m.edges:
				most_recent_interaction = 0
				for j, m2 in enumerate(moments):
					if j < i:
						if edge in m2.edges:
							most_recent_interaction = j
							break
				for j in range(most_recent_interaction, i):
					moments[j].add_edge(*edge, weight=(j-most_recent_interaction) / (i - most_recent_interaction))
		return moments


	@staticmethod
	def next_step(seed_part, cmg, mg):

		def finished(part, mg):
			for edge in mg.edges:
				together = False
				for p in part:
					if edge[0] in p and edge[1] in p:
						together = True
				if not together:
					return False
			return True

		new_part = []
		for b in seed_part:
			nb = set()
			for e in b:
				nb.add(e)
			new_part.append(nb)

		color = {}
		for i in range(len(new_part)):
			for e in new_part[i]:
				color[e] = i

		while not finished(new_part, mg):
			W = Counter()
			for edge in cmg.edges:
				W[edge[0], color[edge[1]]] += cmg.edges[edge]['weight']
				W[edge[1], color[edge[0]]] += cmg.edges[edge]['weight']

			D = Counter()
			for v in cmg.nodes:
				for i in range(len(new_part)):
					D[v, i] = W[v, i] - W[v, color[v]]

			g = Counter() 
			for v in cmg.nodes:
				for w in cmg.nodes:
					if color[w] != color[v]:
						if (v, w) not in cmg.edges:
							cmg.add_edge(v, w, weight=0)
						g[v, w] = D[v, color[w]] + D[w, color[v]] - 2*cmg.edges[(v, w)]['weight']

			swap_key = max(g.items(), key=operator.itemgetter(1))[0]

			new_part[color[swap_key[0]]].remove(swap_key[0])
			new_part[color[swap_key[0]]].add(swap_key[1])

			new_part[color[swap_key[1]]].remove(swap_key[1])
			new_part[color[swap_key[1]]].add(swap_key[0])	

			color_hold = color[swap_key[0]]
			color[swap_key[0]] = color[swap_key[1]]
			color[swap_key[1]] = color_hold	

		return new_part	

	def partition_graph(self, args):
		if self.distribution not in self.SUPPORTED_DISTRIBUTIONS:
			self.distribution = None
		else:
			distribution = self.SUPPORTED_DISTRIBUTIONS[self.distribution]


		if distribution == 'nl':
			cmgs = self.normalized_distance_weights(args.mgs)
		else:			
			cmgs = self.convolve(args.mgs, distribution, self.sigma)


		mgs = args.mgs
		p, k = args.p, args.k

		# Pad with 0 weight edges
		fake_nodes = list(range(len(args.ig.nodes), p*k))
		for m in cmgs:
			m.add_nodes_from(fake_nodes)
			for v in fake_nodes:
				for w in m.nodes:
					m.add_edge(v, w, weight=0)

		# Spike the real edges
		for i, m in enumerate(cmgs):
			for edge in mgs[i].edges:
				m.edges[edge]['weight'] += 100

		# Start with a "good" partition generated via self.local_partitioner
		start_part = self.local_partitioner.partition_graph(args).static_partition

		# must return a static_partition in the partition result
		assert start_part is not None, 'Given local_partitioner does not return a static starting partition.'


		start_part = [set(g) for g in start_part]
		# Add the dummy nodes to the start_part
		i = 0
		for g in start_part:
			while len(g) < args.p:
				g.add(fake_nodes[i])
				i += 1


		path = [start_part]

		for i in range(len(cmgs)):
			path.append(self.next_step(path[-1], cmgs[i], mgs[i]))

		clean_path = [unpad_partitioning(_, len(args.ig.nodes)) for _ in path[1:]]

		assert len(clean_path) == len(args.mgs), 'Generated invalid path length'


		return partitioner.PartitionResult(path=clean_path)



