from .. import partitioner, oee, util


class OeeStaticPartitioner(partitioner.StaticPartitionerAbc):
    def __init__(self, seed=0):
        """
        Uses OEE to partition the total interaction graph as a static
        partitioning.
        """
        self.seed = seed

    def partition_static(self, args):
        """
        Warning:
            OEE may fail with odd sized bucket sizes if the circuit has more
            parallel operations than can be supported.
        """
        ig, mgs = args.ig, args.mgs
        p, k = args.p, args.k


        if args.init_parts is None:
            parts = oee.oee_on_graph(ig, p=p, k=k, seed=self.seed+args.repeat)
        else:
            parts = oee.oee_on_graph(ig, p=p, k=k, seed=self.seed+args.repeat,
                init_parts=util.pad_partitioning(args.init_parts, len(ig), p, k))
        return partitioner.StaticPartitionResult(parts, len(ig))
