
import itertools
import functools

import drawsvg as drawSvg


def draw_graph_with_positions(g, xy_map, box_list=(), name_map=None,
                              color_map=None, edge_color_map=None,
                              extra_g=None,
                              scale=40, background=None):
    if name_map is None:
        name_map = {}
    if color_map is None:
        color_map = {}
    if edge_color_map is None:
        edge_color_map = {}

    # Find bounding box
    def min_max(iterator, default=None):
        low, high = functools.reduce(lambda mm, v: (v, v) if mm is None
                                                   else (min(v, mm[0]),
                                                         max(v, mm[1])),
                                     iterator, default)
        return low, high
    x_list, y_list = zip(*xy_map.values())
    x_boxes = tuple(x_corner for x, y, w, h in box_list
                             for x_corner in (x, x+w))
    y_boxes = tuple(y_corner for x, y, w, h in box_list
                             for y_corner in (y, y+h))
    x_min, x_max = min_max(itertools.chain(x_list, x_boxes))
    y_min, y_max = min_max(itertools.chain(y_list, y_boxes))

    # Create drawing
    border = 0.25
    d = drawSvg.Drawing(x_max-x_min+border*2, y_max-y_min+border*2,
                        (x_min-border, y_min-border))
    d.set_pixel_scale(scale)

    # Draw background
    if background is not None:
        d.draw(drawSvg.Rectangle(x_min-border-1, y_min-border-1,
                                 x_max-x_min+border*2+2,
                                 y_max-y_min+border*2+2,
                                 fill=background))

    # Draw boxes
    for x, y, w, h in box_list:
        stroke = 'black'
        fill = 'none'
        d.draw(drawSvg.Rectangle(x, y, w, h,
                                 stroke=stroke, stroke_width=0.06, fill=fill))

    # Draw edges
    edges = g.edges
    if extra_g is not None:
        edges = itertools.chain(edges, extra_g.edges)
    for n1, n2 in edges:
        x1, y1 = xy_map.get(n1, (0,0))
        x2, y2 = xy_map.get(n2, (0,0))
        stroke = edge_color_map.get((n1, n2), 'black')
        d.draw(drawSvg.Line(x1, y1, x2, y2,
                            stroke=stroke, stroke_width=0.03))

    # Draw nodes
    for node in g.nodes:
        x, y = xy_map.get(node, (0,0))
        radius = 0.25
        font_size = 0.4
        color = color_map.get(node, 'red')
        fg_color = 'black'
        if not isinstance(color, str):
            color, fg_color = color
        d.draw(drawSvg.Circle(x, y, radius, fill=color))
        name = name_map.get(node)
        if name is not None:
            d.draw(drawSvg.Text(name, font_size, x,
                                y+font_size*0.13, center=True,
                                fill=fg_color))

    return d
