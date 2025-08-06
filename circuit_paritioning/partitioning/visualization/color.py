
from matplotlib import cm


def make_color_list(n, name='jet', bytes=False):
    '''Returns an array of n distinguishable colors as rgba values.'''
    viridis = cm.get_cmap(name, n)
    return viridis(range(n), bytes=bytes)

def convert_colors4_to_code(color_array, bytes=False):
    '''Returns a list of HTML color codes.'''
    if bytes:
        return tuple(f'#{r:02x}{g:02x}{b:02x}'
                     for r,g,b,a in color_array)
    else:
        return tuple(f'#{int(round(r*255)):02x}'
                     f'{int(round(g*255)):02x}'
                     f'{int(round(b*255)):02x}'
                     for r,g,b,a in color_array)

def convert_colors3_to_code(color_array, bytes=False):
    '''Returns a list of HTML color codes.'''
    if bytes:
        return tuple(f'#{r:02x}{g:02x}{b:02x}'
                     for r,g,b in color_array)
    else:
        return tuple(f'#{int(round(r*255)):02x}'
                     f'{int(round(g*255)):02x}'
                     f'{int(round(b*255)):02x}'
                     for r,g,b in color_array)

def make_color_code_list(n, name='jet'):
    '''Returns an array of n distinguishable colors as HTML color codes.'''
    return convert_colors4_to_code(make_color_list(n, name=name, bytes=True),
                                   bytes=True)

def paired_color(r, g, b, bytes=False):
    '''Returns a good color for foreground text over this background color.'''
    if bytes:
        r, g, b = r/255, g/255, g/255
        results = ((0,0,0), (255,255,255))
    else:
        results = ((0,0,0), (1,1,1))
    brightness = (r**2+g**2+b**2)**0.5 / 3
    return results[brightness <= 0.28]

def make_color_code_pairs(n, name='jet'):
    '''Returns an array of pairs of HTML color codes.  The pairs are
    (background color, foreground color)'''
    color_list = make_color_list(n, name=name, bytes=True)
    paired_color_list = (paired_color(r, g, b, bytes=True)
                         for (r,g,b,a) in color_list)
    return tuple(zip(convert_colors4_to_code(color_list, bytes=True),
                     convert_colors3_to_code(paired_color_list, bytes=True)))
