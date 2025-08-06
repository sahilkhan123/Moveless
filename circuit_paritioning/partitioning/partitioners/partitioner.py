import abc
import itertools
import collections

import networkx as nx

from .. import interaction_graphs
from ..graph import add_graphs
from ..time_graph import circuit_to_time_graph
from ..visualization.time_graph import draw_partitioned_graph
from .swap_count import count_path_true_swaps
from .path_util import path_from_static_partition, unlabeled_path_to_labled_path
from . import util


class ExtraProperties:
    defaults = dict()

    def __getattr__(self, attr):
        try:
            d = super().__getattribute__('kwargs')
            return d.get(attr, self.defaults.get(attr, None))
        except AttributeError:
            return self.defaults.get(attr, None)

    def __setattr__(self, attr, val):
        if attr in self.__dict__:
            self.__dict__[attr] = val
        else:
            try:
                kwargs = super().__getattribute__('kwargs')
            except AttributeError:
                kwargs = None
            if kwargs is None:
                self.__dict__[attr] = val
            else:
                kwargs[attr] = val

class PartitionerArgs(ExtraProperties):
    defaults = dict(
        slice_len=1,
        repeat=0,
        relabel=True,
        depth_limit=10**6,
    )
    ignored = set(
        'depth_limit',
    )

    def __init__(self, circuit, ig, mgs, p, k, **kwargs):
        self.circuit = circuit
        self.ig = ig
        self.mgs = mgs
        self.p = p
        self.k = k
        # Assign self.kwargs last
        self.kwargs = kwargs

    def copy(self):
        return PartitionerArgs(self.circuit, self.ig, self.mgs, self.p, self.k,
                               **self.kwargs)

    def __str__(self):
        return f'{", ".join(f"{k}={v!r}" for k,v in self.as_key())}'

    def __repr__(self):
        kwargs = dict(circuit=self.circuit, ig=self.ig, mgs=self.mgs,
                      p=self.p, k=self.k)
        kwargs.update(self.kwargs)
        return (f'PartitionerArgs('
                f'{", ".join(f"{k}={v!r}" for k,v in kwargs.items())})')

    def as_key(self):
        '''Returns a hashable representation of the object.'''
        hashable_data = dict(
            p=self.p,
            k=self.k,
        )
        hashable_data.update((k, v) for k, v in self.kwargs.items()
                                    if isinstance(v, collections.abc.Hashable)
                                    if v not in self.ignored
                                    if v != self.defaults.get(k, None))
        return tuple(sorted(hashable_data.items()))

    def __hash__(self):
        return hash((PartitionerArgs, self.as_key()))

    def __eq__(self, other):
        if not isinstance(other, PartitionerArgs):
            return NotImplemented
        return self.as_key() == other.as_key()

    @staticmethod
    def for_benchmark(partr, c_gen, n, m, p, k, **kwargs):
        kwargs.update(partr=partr, c_gen=c_gen, n=n, m=m, p=p, k=k)
        kwargs.setdefault('circuit', None)
        kwargs.setdefault('ig', None)
        kwargs.setdefault('mgs', None)
        return PartitionerArgs(**kwargs)

    @staticmethod
    def from_circuit(circuit, p, k, **kwargs):
        ig, mgs = interaction_graphs.circuit_to_graphs(circuit)
        kwargs.update(circuit=circuit, ig=ig, mgs=mgs, p=p, k=k)
        return PartitionerArgs(**kwargs)

    def init_graphs_from_circuit(self, circuit=None):
        if circuit is not None:
            self.circuit = circuit
        ig, mgs = interaction_graphs.circuit_to_graphs(self.circuit)
        self.ig = ig
        self.mgs = mgs

    @staticmethod
    def from_moment_graphs(self, mgs, p, k, ig=None, **kwargs):
        if ig is None:
            ig = add_graphs(mgs)
        return PartitionerArgs(None, ig, mgs, p, k, **kwargs)

    @staticmethod
    def from_total_graph(self, ig, p, k, **kwargs):
        return PartitionerArgs(None, ig, None, p, k, **kwargs)


class PartitionerAbc(metaclass=abc.ABCMeta):
    def __init__(self):
        '''
        Override the __init__ method in a concrete base class to take
        partitioner specific parameters
        '''

    def run(self, circuit, p, k, **kwargs):
        args = PartitionerArgs.from_circuit(circuit, p, k, **kwargs)
        return self.partition_circuit(args)

    def partition_circuit(self, args):
        r = self.partition_graph(args)
        r.circuit = args.circuit
        return r

    @abc.abstractmethod
    def partition_graph(self, args):
        '''
        Runs the partitioning algorithm on a circuit with.

        Args:
            ig: Total circuit interaction graph
            mgs: List of moment interaction graphs
            p: The size of each bucket
            k: The number of buckets

        Returns:
            A PartitionResult object
        '''


class StaticPartitionerAbc(PartitionerAbc, metaclass=abc.ABCMeta):
    def __init__(self):
        '''
        Override the __init__ method in a concrete base class to take
        partitioner specific parameters
        '''

    def partition_graph(self, args):
        '''
        Runs the partitioning algorithm on a circuit with.

        Args:
            ig: Total circuit interaction graph
            mgs: List of moment interaction graphs
            p: The size of each bucket
            k: The number of buckets

        Returns:
            A PartitionResult object
        '''
        r = self.partition_static(args)
        static_swaps = util.static_cost_function(args.ig, r.partition)
        path = path_from_static_partition(r.partition, args.mgs, args.p,
                                          args.k, args.relabel)

        return PartitionResult(path, static_swaps=static_swaps,
                               static_partition=[list(s) for s in r.partition],
                               **r.kwargs)

    @abc.abstractmethod
    def partition_static(self, args):
        '''
        Runs the partitioning algorithm on a circuit with.

        Args:
            ig: Total circuit interaction graph
            mgs: List of moment interaction graphs
            p: The size of each bucket
            k: The number of buckets

        Returns:
            A StaticPartitionResult object
        '''


class StaticPartitionResult:
    def __init__(self, partition, graph_size=None, **kwargs):
        if graph_size is not None:
            partition = util.unpad_partitioning(partition, graph_size)
        else:
            graph_size = util.num_qubits_in_partitioning(partition)
        self.partition = partition
        self.graph_size = graph_size
        self.kwargs = kwargs


class PartitionResult(ExtraProperties):
    defaults = dict(
        run_time=-1,
    )

    def __init__(self, path, total_swaps=None, circuit=None, **kwargs):
        '''
        Args:
            path: The partitions over time
            total_swaps: How many swaps (at least) will it take to perform this
                partitioning.
            kwargs: Any other parameters are stored in self.kwargs
        '''

        if total_swaps is None:
            total_swaps = count_path_true_swaps(path)

        self.path = path
        self.total_swaps = total_swaps
        self.circuit = circuit
        # Assign self.kwargs last
        self.kwargs = kwargs

    def __repr__(self):
        return (f'PartitionResult(path={self.path}, '
                f'total_swaps={self.total_swaps})')

    def copy(self):
        return PartitionResult(self.path, self.total_swaps, self.circuit,
                               **self.kwargs)

    def to_dict(self):
        out = dict(
            path=[[tuple(sorted(bucket)) for bucket in time_slice]
                  for time_slice in self.path],
            total_swaps=self.total_swaps,
            **self.kwargs,
        )
        if self.circuit is not None:
            out.update(
                circuit_depth=self.get_circuit_depth(),
                cnot_count=self.get_cnot_count(),
            )
        return out

    def get_circuit_depth(self):
        return len(self.circuit)

    def get_cnot_count(self):
        return sum(1 for _ in self.circuit.all_operations())

    def get_n_qubits(self):
        return max((sum(len(bucket) for bucket in time_step)
                    for time_step in self.path),
                   default=0)

    def get_p(self):
        return max((len(bucket)
                    for time_step in self.path for bucket in time_step),
                   default=0)

    def get_k(self):
        return max((len(time_step) for time_step in self.path), default=0)

    def get_duration(self):
        return len(self.path)

    def draw(self, show_time_edges=False,
             x_scale=3, y_scale=1, background=None):
        n = self.get_n_qubits()
        duration = self.get_duration()

        if duration <= 0:
            return None

        # Make swap graph
        if self.circuit is not None:
            # Make swap graph including within-bucket interactions
            
            qs = set()
            for op in self.circuit:
                for q in op[1]:
                    qs.add(q.index)
            qubits = list(range(self.circuit.num_qubits))
            
            # qubits = sorted(self.circuit.all_qubits())
            g = circuit_to_time_graph(self.circuit)
            name_map = {
                t*n+i: str(qubits[i])
                for t, i in itertools.product(range(duration), range(n))
            }
        else:
            g = nx.Graph()
            g.add_nodes_from(range(n*duration))
            name_map = None

        for t in range(len(self.path)-1):
            time_step1 = self.path[t]
            time_step2 = self.path[t+1]
            if not show_time_edges:
                for (i1, bucket1), (i2, bucket2) in (
                    itertools.product(enumerate(time_step1),
                                      enumerate(time_step2))):
                    for qubit in bucket1:
                        if qubit in bucket2:
                            edge = (t*n+qubit, (t+1)*n+qubit)
                            if i1 == i2 and edge in g.edges:
                                g.remove_edge(*edge)
                            elif i1 != i2:
                                g.add_edge(*edge)
            else:
                g.add_edges_from((t*n+i, (t+1)*n+i) for i in range(n))

        return draw_partitioned_graph(g, n, self.path,
                    x_scale=x_scale, y_scale=y_scale, background=background,
                    name_map=name_map)
