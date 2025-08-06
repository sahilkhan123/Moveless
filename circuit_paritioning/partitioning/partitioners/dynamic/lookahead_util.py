import networkx as nx


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
