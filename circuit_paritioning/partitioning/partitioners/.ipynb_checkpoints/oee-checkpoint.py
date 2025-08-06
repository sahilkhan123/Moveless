from collections import namedtuple
import itertools

import numpy as np
import networkx as nx


Swap = namedtuple('Swap', 'qubit1, qubit2, part1, part2')

class Partitioning:
    def __init__(self, p, k, weights=None, weight_array=None, init_order=None,
                 parts=None):
        '''
        A partitioning of p*k qubits into k buckets of size p.

        Args:
            p: The size of each bucket.
            k: The number of buckets.
            init_order: The order to place into buckets.
                Sequential by default.
            parts: A list of sets describing the partitioning.
                init_order is ignored it this is specified.
        '''
        if init_order is None:
            init_order = range(p * k)
        assert len(init_order) == p * k
        if parts is None:
            self.parts = [
                set(init_order[part_i*p + j]
                    for j in range(p))
                for part_i in range(k)
            ]
            #self.part_map = {init_order[part_i*p + j]: part_i
            #                 for part_i in range(k)
            #                 for j in range(p)}
        else:
            self.parts = tuple(set(bucket) for bucket in parts)
        self.part_map = {
            qubit: part_i
            for part_i, bucket in enumerate(self.parts)
            for qubit in bucket
        }
        self.part_array = np.zeros((p*k, k), dtype=np.bool)
        for part_i, bucket in enumerate(self.parts):
            for qubit in bucket:
                self.part_array[qubit][part_i] = True
        self.p = p
        self.k = k

        # Init weight_array
        if weights is None:
            weights = {}
        if weight_array is None:
            self.weight_array = np.zeros((p*k, p*k))
            for (i, j), w in weights.items():
                if i == j:
                    continue
                self.weight_array[i, j] = w
                self.weight_array[j, i] = w
        else:
            self.weight_array = np.array(weight_array)

        self.swap_gain = np.zeros((p*k, p*k))
        self.bucket_gain = np.zeros((p*k, k))
        self.bucket_value = np.zeros((p*k, k))
        self._init_bucket_value()
        self._init_bucket_gain()
        self._init_swap_gain()

    def __repr__(self):
        return f'Partitioning({self.p}, {self.k}, parts={self.parts})'

    def _init_bucket_value(self):
        self.bucket_value = self.weight_array @ self.part_array

    def _init_bucket_gain(self):
        self.bucket_gain = (self.bucket_value.T
                            - np.max(self.bucket_value
                                     * self.part_array, axis=-1)).T

    def _init_swap_gain(self):
        expand = self.bucket_gain.T[np.argmax(self.part_array, axis=-1)]
        self.swap_gain = expand + expand.T - 2*self.weight_array

    def make_swap(self, qubit1, qubit2):
        return Swap(part1=self.part_map[qubit1],
                    part2=self.part_map[qubit2],
                    qubit1=qubit1,
                    qubit2=qubit2)

    def _do_swap(self, swap):
        assert self.part_map[swap.qubit1] == swap.part1
        assert self.part_map[swap.qubit2] == swap.part2
        self.part_map[swap.qubit1] = swap.part2
        self.part_map[swap.qubit2] = swap.part1
        self.parts[swap.part1].remove(swap.qubit1)
        self.parts[swap.part2].remove(swap.qubit2)
        self.parts[swap.part2].add(swap.qubit1)
        self.parts[swap.part1].add(swap.qubit2)
        self.part_array[swap.qubit1, swap.part1] = 0
        self.part_array[swap.qubit1, swap.part2] = 1
        self.part_array[swap.qubit2, swap.part2] = 0
        self.part_array[swap.qubit2, swap.part1] = 1

    def do_swap(self, swap):
        self._do_swap(swap)
        self._init_bucket_value()
        self._init_bucket_gain()
        self._init_swap_gain()

    def do_swap_list(self, swap_list):
        for swap in swap_list:
            self._do_swap(swap)
        self._init_bucket_value()
        self._init_bucket_gain()
        self._init_swap_gain()

    def _undo_swap(self, swap):
        assert self.part_map[swap.qubit1] == swap.part2
        assert self.part_map[swap.qubit2] == swap.part1
        self.part_map[swap.qubit1] = swap.part1
        self.part_map[swap.qubit2] = swap.part2
        self.parts[swap.part2].remove(swap.qubit1)
        self.parts[swap.part1].remove(swap.qubit2)
        self.parts[swap.part1].add(swap.qubit1)
        self.parts[swap.part2].add(swap.qubit2)
        self.part_array[swap.qubit1, swap.part1] = 1
        self.part_array[swap.qubit1, swap.part2] = 0
        self.part_array[swap.qubit2, swap.part2] = 1
        self.part_array[swap.qubit2, swap.part1] = 0

    def undo_swap(self, swap):
        self._undo_swap(swap)
        self._init_bucket_value()
        self._init_bucket_gain()
        self._init_swap_gain()

    def undo_swap_list(self, swap_list):
        for swap in reversed(swap_list):
            self._undo_swap(swap)
        self._init_bucket_value()
        self._init_bucket_gain()
        self._init_swap_gain()

    def swap_value(self, swap, weights):
        return self.swap_gain[swap.qubit1, swap.qubit2]

    def swap_list_value(self, swap_list, weights):
        total = 0
        for swap in swap_list:
            total += self.swap_value(swap, weights)
            self.do_swap(swap)
        for swap in reversed(swap_list):
            self.undo_swap(swap)
        return total

    def all_swap_values(self, weights, allowed_qubits=None,
                        swap_within_bucket=False):
        if allowed_qubits is None:
            allowed_qubits = range(self.p * self.k)
        #if isinstance(allowed_qubits, set):
        #    # Make order deterministic
        #    allowed_qubits = sorted(allowed_qubits)
        for qubit1, qubit2 in itertools.combinations(allowed_qubits, 2):
            if qubit1 > qubit2:
                qubit1, qubit2 = qubit2, qubit1
            swap = self.make_swap(qubit1, qubit2)
            if not swap_within_bucket and swap.part1 == swap.part2:
                continue
            val = self.swap_value(swap, weights)
            yield val, swap

    def is_valid(self, interaction_list):
        for i, j in interaction_list:
            if self.part_map[i] != self.part_map[j]:
                return False
        return True


def do_best_swap_sequence(weights, parts, swap_within_bucket, epsilon=1e-12,
                          lazy=False, weights_fallback=None, spike_value=None):
    # Do all swaps
    allowed_qubits = set(range(parts.p * parts.k))
    cur_val = 0
    done_vals_swaps = []
    i = 0
    while True:
        possible_vals_swaps = list(parts.all_swap_values(weights,
                                allowed_qubits=allowed_qubits,
                                swap_within_bucket=swap_within_bucket))
        if not possible_vals_swaps:
            break
        #if possible_vals_swaps[0][0] == possible_vals_swaps[-1][0] == 0:
        #    # All possible swaps have value zero, quit
        #    break
        best_val, best_swap = max(possible_vals_swaps)
        if lazy and best_val < spike_value - epsilon:
            # Quit early
            for _, _, swap in done_vals_swaps:
                yield swap
            return
        parts.do_swap(best_swap)
        cur_val += best_val
        done_vals_swaps.append((cur_val, -i, best_swap))
        allowed_qubits.remove(best_swap.qubit1)
        allowed_qubits.remove(best_swap.qubit2)
        i += 1

    if not done_vals_swaps:
        # No improvement in this step, stop
        return

    max_val, _, max_swap = max(done_vals_swaps)
    if max_val > epsilon:
        # Undo final bad swaps
        for _, _, swap in reversed(done_vals_swaps):
            if swap == max_swap:
                # Done undoing
                break
            parts.undo_swap(swap)

        # Yield the swaps that were used to get here
        for _, _, swap in done_vals_swaps:
            yield swap
            if swap == max_swap:
                # Done yielding
                break
    else:
        # All swaps are bad, undo all swaps
        for _, _, swap in reversed(done_vals_swaps):
            parts.undo_swap(swap)

def do_fixup_swaps(weights, parts, epsilon=1e-12, lazy=False,
                   weights_fallback=None, spike_value=None):
    # Find a pair of qubits that need to be together
    if lazy:
        max_weight = None
        for (qubit1, qubit2), w in weights_fallback.items():
            if i >= j or w <= 0:
                continue
            if parts.part_map[i] == parts.part_map[j]:
                continue
            max_weight = w
            break
    else:
        max_weight, qubit1, qubit2 = max((
            (w, i, j)
            for (i, j), w in weights.items()
            if j > i and parts.part_map[i] != parts.part_map[j]),
            default=(None, None, None)
        )

    if max_weight is None:
        return ()

    # Pick two other qubits to swap with, maximizing the value increase
    def gen_swap_options():
        for part_i, bucket in enumerate(parts.parts):
            if qubit1 in bucket or qubit2 in bucket:
                continue
            for qubit1s, qubit2s in itertools.product(bucket, repeat=2):
                if qubit1s == qubit2s:
                    continue
                swap1 = parts.make_swap(qubit1, qubit1s)
                swap2 = parts.make_swap(qubit2, qubit2s)
                val = parts.swap_list_value((swap1, swap2), weights)
                yield val, swap1, swap2

    max_val, swap1, swap2 = max(gen_swap_options(), default=(-1, None, None))
    if max_val > epsilon:
        parts.do_swap_list((swap1, swap2))
        return (swap1, swap2)
    else:
        return ()

def do_oee_swaps(weights, parts, swap_within_bucket, lazy=False,
                 weights_fallback=None, spike_value=None):
    all_swaps = []
    while True:
        # Do one step of OEE
        swap_gen = do_best_swap_sequence(weights, parts,
                        swap_within_bucket=swap_within_bucket,
                        lazy=lazy,
                        weights_fallback=weights_fallback,
                        spike_value=spike_value)
        num_before = len(all_swaps)
        all_swaps.extend(swap_gen)
        if len(all_swaps) <= num_before:
            swaps = do_fixup_swaps(weights, parts,
                                   lazy=lazy,
                                   weights_fallback=weights_fallback,
                                   spike_value=spike_value)
            all_swaps.extend(swaps)
            if len(swaps) <= 0:
                # No swaps were added, quit
                break
    return all_swaps

def mirrored_weights(weights):
    return {(ii, jj): w
            for (i, j), w in weights.items()
            for ii, jj in ((i, j), (j, i))}

def check_validity(parts, weights_fallback):
    interaction_list = tuple((i, j)
                             for (i, j), w in weights_fallback.items()
                             if w > 0)
    return parts.is_valid(interaction_list)

def check_possible(p, k, weights_fallback):
    interaction_count = len(set((i, j) if i < j else (j, i)
                                for (i, j), w in weights_fallback.items()
                                if w > 0))
    possible_interaction_count = p // 2 * k
    return interaction_count <= possible_interaction_count

def oee_swaps(weights, p, k, init_parts=None, swap_within_bucket=False,
        weights_fallback=None, mirror_weights=True, seed=None, prng=None,
        try_fallback=False, lazy=False, spike_value=None):
    if prng is None:
        prng = np.random.RandomState(seed)

    if init_parts is None:
        init_order = prng.permutation(range(p * k))
        parts = Partitioning(p, k, weights=weights, init_order=init_order)
    elif isinstance(init_parts, Partitioning):
        parts = Partitioning(p, k, weights=weights, parts=init_parts.parts)
    else:
        parts = Partitioning(p, k, weights=weights, parts=init_parts)
    if mirror_weights:
        weights = mirrored_weights(weights)
        weights_fallback = mirrored_weights(weights_fallback)

    if weights_fallback is not None:
        if not check_possible(p, k, weights_fallback):
            raise ValueError('OEE partitioning impossible: '
                             f'More than {p//2*k} swaps in a moment.')

    all_swaps = do_oee_swaps(weights, parts,
                             swap_within_bucket=swap_within_bucket,
                             lazy=lazy,
                             weights_fallback=weights_fallback,
                             spike_value=spike_value)

    if weights_fallback is not None:
        if try_fallback:
            logger.info('OEE partitioning is invalid.  '
                        'Trying again with simple weights.')
            # Check that the partitioning is valid
            if not check_validity(parts, weights_fallback):
                # Fix invalid partitioning
                all_swaps.extend(do_oee_swaps(weights_fallback, parts,
                                    swap_within_bucket=swap_within_bucket))
                #all_swaps.extend(do_oee_swaps(weights, parts,
                #                    swap_within_bucket=swap_within_bucket))
            # Check again that the partitioning is valid
            if not check_validity(parts, weights_fallback):
                # Bad
                logger.error('OEE partitioning is still invalid.')
        else:
            # Check that the partitioning is valid
            if not check_validity(parts, weights_fallback):
                # Bad
                logger.error('OEE partitioning is invalid.')

    return parts, all_swaps

def oee(weights, p, k, init_parts=None, swap_within_bucket=False,
        weights_fallback=None, mirror_weights=True, seed=None, prng=None,
        try_fallback=False, lazy=False, spike_value=None):
    parts, swaps = oee_swaps(weights, p, k,
                             init_parts=init_parts,
                             swap_within_bucket=swap_within_bucket,
                             weights_fallback=weights_fallback,
                             mirror_weights=mirror_weights,
                             seed=seed, prng=prng,
                             try_fallback=try_fallback,
                             lazy=lazy,
                             spike_value=spike_value)
    return parts.parts

def oee_on_graph(g, p, k=2, init_parts=None, seed=None, prng=None,
                 weights_fallback=None):
    weights = {
        (ii, jj): g.get_edge_data(i, j)['weight']
        for i, j in g.edges
        for ii, jj in ((i, j), (j, i))
    }

    if weights_fallback is not None:
        weights_fallback = mirrored_weights(weights_fallback)

    return oee(weights, p, k,
                init_parts=init_parts,
                weights_fallback=weights_fallback,
                mirror_weights=False,
                seed=seed, prng=prng)
