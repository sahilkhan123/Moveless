


class DynamicSlicingPartitioner(partitioner.PartitionerAbc):

	def __init__(self, partitionInfo):
		self.partitionInfo = partitionInfo

	def run(self, circuit, p, k, **kwargs):

		# TODO
		# If graphs are passed in eliminate this line
		ig, mgs = interaction_graphs.circuit_to_graphs(circuit)

