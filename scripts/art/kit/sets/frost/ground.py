"""Frostline ground and transition painters."""
from __future__ import annotations

from ._shared import (
    BIOMES,
    PIECES,
    STANDARD,
    json,
    np,
    os,
)

# ================================================================================================
# the ground
# ================================================================================================
SNOW_FILL = ('snow', {'seed': 1401})

TROD_FILL = ('snow_trod', {'seed': 1402})

MORAINE_FILL = ('moraine', {'seed': 1403})

ICE_FILL = ('ice', {'seed': 1404})



def _terrain(mid, name, mat_id, priority, surface, route, fill, nav, note, walkable=True):
    return {
        'schema': 'napattack.piece/1', 'id': mid, 'name': name, 'kind': 'terrain', 'biomes': list(BIOMES), 'version': 1,
        'approval': {'state': 'candidate', 'by': None, 'at': None, 'standard': STANDARD, 'note': note},
        'terrain': {'material_id': mat_id, 'priority': priority,
                    'fill': {'module': 'scripts.art.kit.fills', 'fn': fill[0], 'args': fill[1]},
                    'walkable': walkable, 'surface': surface, 'route': route, 'water': None, 'swatch': [96, 96],
                    'paint': {'module': 'scripts.art.kit.sets.frost', 'fn': 'paint_' + mid, 'args': {}}},
        'placement': {'snap': 'cell'},
        'gameplay': {'blocks_move': not walkable, 'blocks_shots': False, 'nav_cost': nav},
        'audit': {'painter': {'module': 'scripts.art.kit.fills', 'fn': fill[0], 'args': fill[1]}, 'size_class': 'ground',
                  'eastward_ref': 'Eastward 22 to 24 (the snowfield, the trodden path); refs local only'},
    }



def _transition(upper, lower, fn, dressing=None, note='', args=None):
    return {
        'schema': 'napattack.piece/1', 'id': '%s_over_%s' % (upper, lower), 'name': '%s over %s' % (upper.capitalize(), lower),
        'kind': 'transition', 'biomes': list(BIOMES), 'version': 1,
        'approval': {'state': 'candidate', 'by': None, 'at': None, 'standard': STANDARD, 'note': note},
        'transition': {'upper': upper, 'lower': lower, 'painter': {'module': 'scripts.art.kit.edges', 'fn': fn,
                                                                    'args': dict(args or {})},
                       'variants': 1, 'shape': 'lower', 'dressing': dressing},
        'audit': {'painter': {'module': 'scripts.art.kit.edges', 'fn': fn, 'args': dict(args or {})},
                  'eastward_ref': 'Eastward 22 and 23 (snow over the trod and the shore)'},
    }



# stones breaking through the snow's last texels over the moraine: since round 4 of #541 they are the
# moraine's own slate stones drawn by edges.snow_fray (the lawn kit's warm decals read as sandstone),
# so this edge carries no decal dressing
STONES = None



def terrain_pieces():
    t = [
        _terrain('snow', 'Lying snow', 13, 31, 'snow', False, SNOW_FILL, 1.2,
                 'The cirque\'s floor: lying snow, wind-laid drifts lit on their north-west faces with cool shade in '
                 'their lee, a few clusters of wind-cut sastrugi; nothing dark on the open snow.'),
        _terrain('snow_trod', 'Trodden snow', 14, 22, 'snow', True, TROD_FILL, 0.9,
                 'The Col Path trodden into the snow: a packed grey-blue plane with a gentle drift of tone, large soft '
                 'compacted patches packed harder at their cores, boot dents 5 to 9 texels in loose groups (filled '
                 'pockets, most of them old crescents), no lanes, so it reads the same whichever way it runs.'),
        _terrain('moraine', 'Moraine', 15, 16, 'rock', False, MORAINE_FILL, 1.0,
                 'The High Fells\' moraine: graded granite stones (boulders knee high to pebbles) broken on flat planes, '
                 'contact shade on a calm cold grit of two- and three-texel grains, dark grit at the stones\' feet, a '
                 'crack on some boulders and old snow lying on their tops.'),
        _terrain('ice', 'Lake ice', 16, 12, 'water', False, ICE_FILL, 9.0,
                 'The tarn frozen over: clear blue ice under wind-laid white, cracks. Kept off (the white ice breaks).',
                 walkable=False),
    ]
    tr = [
        _transition('snow', 'snow_trod', 'snow_lip', None, 'The snow hanging over the trod\'s north side in rounded lobes, '
                    'lit on its south, loose snow frayed over its other edges.'),
        _transition('snow', 'moraine', 'snow_fray', STONES, 'Snow thinning over the moraine, frayed at its sides, the '
                    'moraine\'s slate stones breaking through.'),
        _transition('snow', 'water', 'cornice_bank', None, 'A snow cornice over open water: on its north shore a bank of '
                    'large outlined granite stones with the light waterline in the gaps, shore ice on every other shore.',
                    {'rim': 'ice'}),
        _transition('snow', 'ice', 'cornice_bank', None, 'A snow cornice over the tarn: on its north shore a bank of large '
                    'outlined granite stones, gaps moving from cell to cell with the light waterline in them, a plain '
                    'rim on every other shore.',
                    {'rim': 'lip'}),
        _transition('snow_trod', 'water', 'cornice_bank', None, 'The trod\'s end at the water, shore ice.', {'rim': 'ice'}),
        _transition('ice', 'water', 'ice_edge', None, 'The ice cut back from open water: its thickness on the north edge.'),
    ]
    return t, tr



def write_terrain(force=False):
    t, tr = terrain_pieces()
    n = 0
    for kind, items in (('terrain', t), ('transition', tr)):
        for pc in items:
            path = os.path.join(PIECES, kind, pc['id'] + '.json')
            if force or not os.path.exists(path):
                with open(path, 'w') as f:
                    json.dump(pc, f, indent=1)
                    f.write('\n')
                n += 1
    return n



def _fill_into(cv, m, fill):
    from scripts.art.kit import fills as FL
    f = getattr(FL, fill[0])(**fill[1])
    P = f.shape[0]
    H, W = cv.shape
    yy, xx = np.mgrid[0:H, 0:W]
    cv[m] = f[yy % P, xx % P][m]



def paint_snow(cv, m, seed=0, **_kw):
    """The snow's painted ground for a future bake hook: its periodic fill laid by world position."""
    _fill_into(cv, m, SNOW_FILL)



def paint_moraine(cv, m, seed=0, **_kw):
    """The moraine's painted ground for a future bake hook."""
    _fill_into(cv, m, MORAINE_FILL)



def paint_snow_trod(cv, m, seed=0, **_kw):
    """The trod's painted ground for a future bake hook."""
    _fill_into(cv, m, TROD_FILL)



def paint_ice(cv, m, seed=0, **_kw):
    """The tarn's ice for a future bake hook."""
    _fill_into(cv, m, ICE_FILL)
