'''
Example:

```
from partitioning.circuits.random_graph_cz_circuit import rand_circuit
from partitioning.time_matching import time_graph
from partitioning.visualization.time_graph import draw_time_graph

c = rand_circuit(10, 0.5, seed=99)
n = len(c.all_qubits()) + 2
g = time_graph.circuit_to_time_graph(c, n)
d = draw_time_graph(g, n)
d
```
'''


import itertools

from . import svg


def sort_nodes_by_interaction(g, nodes):
    nodes = sorted(nodes)
    sorted_nodes = [i for i, j in itertools.combinations(nodes, 2)
                      if i <= j and (i, j) in g.edges]
    sorted_nodes.extend(i for i in nodes if i not in sorted_nodes)
    return sorted_nodes

def place_nodes(g, n, nodes, x_curr, x_step, y_offset, x_scale=3, y_scale=1, name_map=None):
    xy_map = {}
    y_map = {node: i for i, node in enumerate(nodes)}

    def place_node(node, x):
        y_i = y_map[node]
        y = y_offset-y_i*y_scale
        xy_map[node] = (x_curr, y)
        if name_map is not None:
            i = node % n
            name_map[node] = name_map.get(node, f'{i}')

    layer_edge_map = {
        y_map[i]: y_map[j]
        for i, j in itertools.product(nodes, repeat=2)
        if (i, j) in g.edges
    }
    rev_layer_edge_map = {(j, i) for i, j in layer_edge_map.items()}
    interacting_nodes = set(nodes[i] for i in layer_edge_map.keys())
    placed_nodes = set()

    node_set = set(node for node in nodes if node >= 0)
    # Place nodes that don't interact
    for node in node_set - interacting_nodes:
        place_node(node, x_curr)
        placed_nodes.add(node)

    # Place nodes that interact with an immediate neighbor
    # Only do this if there were any non-interacting nodes
    # The output looks better without this
    #if len(interacting_nodes) < n:
    #    for node in interacting_nodes:
    #        if layer_edge_map[y_map[node]] == y_map[node]+1:
    #            node2 = rev_layer_edge_map[node]
    #            place_node(node, x_curr)
    #            place_node(node2, x_curr)
    #            placed_nodes.update((node, node2+1))

    if len(placed_nodes) > 0:
        x_curr += x_step

    # Place remaining nodes in layers
    num_edges = float('inf')
    while num_edges > 0:
        covered_y = -1
        num_edges = 0
        i = 0
        while i < len(node_set):
            node = nodes[i]
            if node < 0:
                i += 1
                continue
            if node in placed_nodes:
                i += 1
                continue
            j = layer_edge_map[i]
            node2 = nodes[j]
            if node2 in placed_nodes or j <= i:
                i += 1
                continue

            place_node(node, x_curr)
            place_node(node2, x_curr)
            placed_nodes.update((node, node2))
            num_edges += 1
            i = j+1
        x_curr += x_step

    # Place remaining nodes in case this wasn't a valid time interaction graph
    x_curr += x_step
    for node in node_set - placed_nodes:
        place_node(node, x_curr)
        placed_nodes.add(node)

    return xy_map

def draw_time_graph(g, n, x_scale=3, y_scale=1, name_map=None, color_map=None,
                    edge_color_map=None, extra_g=None, background=None):
    duration = (len(g.nodes) + n-1) // n
    max_interactions_per = (n + 1) // 2
    x_step = 0.6 * x_scale / max_interactions_per

    xy_map = {}
    if name_map is None:
        name_map = {}

    for t in range(duration):
        # Place nodes in time-step t
        x_curr = t * x_scale
        xy_update = place_nodes(g, n, range(t*n, (t+1)*n), x_curr, x_step,
                        x_scale=x_scale, y_scale=y_scale, name_map=name_map)
        xy_map.update(xy_update)

    return svg.draw_graph_with_positions(g, xy_map,
                                         name_map=name_map,
                                         color_map=color_map,
                                         edge_color_map=edge_color_map,
                                         extra_g=extra_g,
                                         background=background)

def draw_partitioned_graph(g, n, path, x_scale=4, y_scale=1, name_map=None,
                           color_map=None, edge_color_map=None, extra_g=None,
                           background=None):
    duration = (len(g.nodes) + n-1) // n
    bucket_sizes = tuple(
        max(len(time_step[i]) if i < len(time_step) else 0
            for time_step in path)
        for i in range(max(len(time_step) for time_step in path)))
    max_interactions_per = (n + 1) // 2
    x_step = 0.6 * x_scale / max_interactions_per

    xy_map = {}
    if name_map is None:
        name_map = {}

    x_padding = 0.5
    x_width = (max_interactions_per-1)*x_step + 2*x_padding
    y_padding = 0.5
    y_margin = 0.6 * y_scale
    h_min = 0.1
    box_list = []
    def place_box(t, y, h):
        h = max(h, h_min-2*y_padding)
        box_list.append(
            (t*x_scale - x_padding, y-h - y_padding,
             x_width, h + 2*y_padding))

    current_bucket_orders = tuple([-1]*bucket_n for bucket_n in bucket_sizes)
    for t, time_step in enumerate(path):
        # Place nodes in time-step t
        y_curr = (n-1) * y_scale
        for bucket, bucket_n, current_order in zip(
                time_step, bucket_sizes, current_bucket_orders):
            x_curr = t * x_scale
            nodes = set(t*n+qubit for qubit in bucket)
            old_nodes = set(t*n+qubit for qubit in bucket
                                if t > 0 and (t-1)*n+qubit in current_order)
            new_nodes = sorted(nodes - old_nodes)
            j = 0
            for i in range(bucket_n):
                if current_order[i] >= 0 and current_order[i]+n in old_nodes:
                    current_order[i] += n
                else:
                    if j < len(new_nodes):
                        current_order[i] = new_nodes[j]
                        j += 1
                    else:
                        current_order[i] = -1

            xy_update = place_nodes(g, n, current_order,
                            x_curr, x_step, y_curr,
                            x_scale=x_scale, y_scale=y_scale, name_map=name_map)
            xy_map.update(xy_update)

            place_box(t, y_curr, (bucket_n-1)*y_scale)
            y_curr -= bucket_n*y_scale + y_margin

    return svg.draw_graph_with_positions(g, xy_map,
                                         box_list=box_list,
                                         name_map=name_map,
                                         color_map=color_map,
                                         edge_color_map=edge_color_map,
                                         extra_g=extra_g,
                                         background=background)
