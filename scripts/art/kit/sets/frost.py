"""The Frostline set (docs/vision/regions/home-valley-frostline-brackens.md; the Frostline zone,
game/kit/zones/frostline.json), round 2 after the detail and logic audits of #478. Drawn with the
Brackens' renderer and helpers (scripts/art/kit/sets/_common.py) and the house builder.

**Ground** (additive: no existing material, transition or bake hash moves; the painters are
scripts/art/kit/fills.py snow, snow_trod, moraine, ice and scripts/art/kit/edges.py snow_lip,
snow_fray, cornice_bank, ice_edge):

- `snow`: a calm plane in three tones laid by the wind in long drifts, each crest's lee a cool row;
- `snow_trod`: packed snow a tone cooler, worn patches, bootprints in staggered pairs;
- `moraine`: cold granite grit with stones of three sizes, lit caps, dark east sides, old snow;
- `ice`: the tarn frozen over, clear blue ice under wind-laid white, cracks; not walkable;
- transitions: the snow's lip over the trod (an overhang and two rows of shade under a north lip,
  a lit south lip, nothing on the sides), snow thinning over the moraine (stones breaking through
  as edge dressing), a snow cornice over a granite bank on the water and the ice, shore ice on
  open water, the ice's cut edge at the hole.

The Frostline still shows the editor's live tiles: bake.py dispatches only on the painters it
knows, and teaching it these moves every baked zone's hash (its own PR).

**Props.** Snow is modelled as solids lying on what faces the sky, so it is shaded and outlined
like any material. The Col hut at the Frostline hut scale; conifers in four silhouettes from the
woodland pine's tiered painter with snow shelves on the tiers, and a dead snag; granite boulders,
a boulder cluster, stones and headwall crags; granite cairns (standing, toppled, small); the
climbers' fire ring under snow; the sledge and the cut ice stack; the warden's yard (woodpile, skis
and shovel), a bench, a noticeboard, a snow pole and a lost hat; the cirque's 32 px granite face
with its stair and its frozen fall; a plank footbridge over the outlet.

    python3 -m scripts.art.kit.sets.frost           # paint and write the pieces
    python3 -m scripts.art.kit.sets.frost --check   # exit 1 if a picture is stale
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

from scripts.art.kit.schema import PIECES, ROOT
from scripts.art.kit.sets import _common as K
from scripts.art.kit.sets import brackens as B
from scripts.art.kit.sets._common import C, hsh
from scripts.art.native import village as V
from scripts.art.native.palette import FI, LUT, to_rgba

ART = os.path.join(ROOT, 'game', 'kit', 'props', 'art', 'frost')
RES = 'res://kit/props/art/frost/'
STANDARD = ("eastward-edges.md 5.1 and 5.5, art-style.md density 3; the Frostline brief (snow lying on what faces the "
            "sky, granite and slate, lake ice)")
BIOMES = ['frostline']
OAK = B.OAK


# ================================================================================================
# helpers
# ================================================================================================
def _grow(p: V.Pic, top: int, side: int = 0) -> V.Pic:
    """The same picture on a canvas `top` texels taller (and `side` wider each side)."""
    q = V.Pic(p.W + 2 * side, p.H + top, p.ax + side, p.ay + top)
    q.a[top:, side:side + p.W] = p.a
    return q


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


# stones breaking through the snow's last texels over the moraine (the edge dressing's decals)
STONES = {'density': 0.85, 'south': ['bankstone_0', 'bankstone_1', 'pebble_2', 'pebble_3'],
          'north': ['bankstone_1', 'bankstone_2', 'pebble_1'], 'side': ['bankstone_0', 'pebble_2', 'pebble_3']}


def terrain_pieces():
    t = [
        _terrain('snow', 'Lying snow', 13, 31, 'snow', False, SNOW_FILL, 1.2,
                 'The cirque\'s floor: lying snow, a calm plane in three tones laid by the wind in long soft drifts.'),
        _terrain('snow_trod', 'Trodden snow', 14, 22, 'snow', True, TROD_FILL, 0.9,
                 'The Col Path trodden into the snow: a packed plane a tone cooler, worn patches, bootprints.'),
        _terrain('moraine', 'Moraine', 15, 16, 'rock', False, MORAINE_FILL, 1.0,
                 'The High Fells\' moraine: cold grey granite grit with stones of three sizes, old snow in their lee.'),
        _terrain('ice', 'Lake ice', 16, 12, 'water', False, ICE_FILL, 9.0,
                 'The tarn frozen over: clear blue ice under wind-laid white, cracks. Kept off (the white ice breaks).',
                 walkable=False),
    ]
    tr = [
        _transition('snow', 'snow_trod', 'snow_lip', None, 'The snow hanging over the trod\'s north side, lit on its south.'),
        _transition('snow', 'moraine', 'snow_fray', STONES, 'Snow thinning over the moraine, stones breaking through.'),
        _transition('snow', 'water', 'cornice_bank', None, 'A snow cornice over a granite bank, shore ice on the open water.',
                    {'rim': 'ice'}),
        _transition('snow', 'ice', 'cornice_bank', None, 'A snow cornice over the tarn\'s granite bank.', {'rim': 'lip'}),
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


# ================================================================================================
# the props (round 2: the detail audit of #478, F-H1 to F-S1 and Z2, Z5, Z6; the logic audit's B5, B6)
# ================================================================================================
# Scene units are ground texels at density 3 (a cell is 24, an adult 74). Snow is drawn as solids
# lying on what faces the sky (a cap on a stone's top plane, a slab on a ledge), so the renderer
# shades it with the light and closes its outline like any material: no halo, no flecks.
GRANITE = [('slate_cool', 'slate', 'slate'), ('iron', 'slate', 'slate'), ('slate_cool', 'iron', 'slate')]
SNOW = [('snow_cool', 'snow', 'snow'), ('snow_cool', 'snow', 'snow_warm')]
WEATHERED = [('soot', 'ash', 'ash'), ('stone_cool', 'ash', 'ash')]
RED = [('berry_cool', 'berry', 'clay')]
HUT_SPEC = dict(kind='hut', w=64, depth=34, wall_h=41, roof_h=26, wall='stone', roof='slate', paint='timber',
                doors=[[22, 'timber']], door_w=13, door_h=29, windows=[47], win_w=10, win_h=11, win_top=30,
                shutters=False, slate_calm=True, eave_dark=True, roof_moss=0, roof_lichen=0, chimney=[52],
                chimney_w=7, chimney_h=12)


def _solo(sc, dress=None):
    return B._solo(sc, dress=dress)


def _snowcap(sc, cx, cy, ztop, rx, ry, th=3.2, seed=0):
    """A cap of snow on a top plane: a flattened mass, a little west of centre (the wind lays it from
    the east), lit by the renderer on its top and west, cool on its east fall."""
    sc.ellipsoid(cx - rx * 0.06, cy - ry * 0.05, ztop + th * 0.25, rx, ry, th, SNOW, base=3.9, k=1.1, tag='snow',
                 mix=hsh(seed, 3) * 0.6, flat=1.5)


def _drift_west(sc, x, y, r, seed=0):
    """A drift banked against an object's west foot (the windward side)."""
    sc.ellipsoid(x - r * 0.4, y + 1.5, 0.6, r, r * 0.55, r * 0.32, SNOW, base=3.8, k=1.0, tag='drift', mix=hsh(seed, 5) * 0.6,
                 flat=1.1)


def _cracks(sc, a, tags=('rock',), n=2, seed=0):
    """Crack lines on stone: short bending runs down a face in the shade tone, a lit texel on their
    west side."""
    lab = sc.label
    m = np.isin(lab, [i for i, s_ in enumerate(sc.solids) if s_.tag in tags])
    ys, xs = np.nonzero(m)
    if not len(ys):
        return
    rng = np.random.default_rng(seed)
    for _ in range(n):
        k = int(rng.integers(0, len(ys)))
        y, x = float(ys[k]), float(xs[k])
        for _j in range(int(rng.integers(5, 11))):
            yi, xi = int(y), int(x)
            if not (0 <= yi < a.shape[0] and 0 <= xi < a.shape[1]) or not m[yi, xi]:
                break
            a[yi, xi] = C('slate_cool', 1)
            if xi - 1 >= 0 and m[yi, xi - 1]:
                a[yi, xi - 1] = C('slate', 4)
            y += 1.0
            x += rng.choice((-1, 0, 0, 1)) * 0.6


def _rock(sc, cx, cy, rx, ry, rz, seed, cap=True, drift=True):
    """A granite boulder: a low rounded mass wider than it is tall (granite weathers to blocks with
    rounded arrises: a superellipsoid's flat faces), one or two shoulders breaking its outline, its
    top plane under a snow cap, a drift at its west foot."""
    rng = np.random.default_rng(seed)
    h = rz * 0.75
    sc.ellipsoid(cx, cy, h, rx, ry, h, GRANITE, base=2.9, k=1.8, tag='rock', mix=rng.random(), flat=3.2, tex='stone')
    sc.ellipsoid(cx + rx * 0.55, cy + ry * 0.3, h * 0.55, rx * 0.6, ry * 0.65, h * 0.6, GRANITE, base=2.6, k=1.8,
                 tag='rock', mix=rng.random(), flat=3.0, tex='stone')
    if rx > 10:
        sc.ellipsoid(cx - rx * 0.7, cy + ry * 0.45, h * 0.4, rx * 0.45, ry * 0.5, h * 0.45, GRANITE, base=2.7, k=1.8,
                     tag='rock', mix=rng.random(), flat=3.0, tex='stone')
    if cap:
        _snowcap(sc, cx - rx * 0.1, cy - ry * 0.12, 2 * h - 1.5, rx * 0.72, ry * 0.62, th=max(2.4, rz * 0.2), seed=seed)
    if drift:
        _drift_west(sc, cx - rx * 1.0, cy + ry * 0.4, max(4.0, rx * 0.45), seed)


def boulder(kind='a', seed=43):
    """A Frostline granite boulder (not the woodland's): `a` and `b` mid-sized, `large` a cluster
    of a big block with two smaller ones in its lee, `small` a stone a cell across."""
    sc = K.Scene(-60, 60, -40, 24, 120)
    if kind == 'a':
        _rock(sc, 0, -6, 15, 10, 12, seed)
    elif kind == 'b':
        _rock(sc, -2, -6, 13, 9, 15, seed + 1)
    elif kind == 'large':
        _rock(sc, -6, -10, 24, 15, 22, seed + 2)
        _rock(sc, 22, 0, 10, 7, 8, seed + 3, drift=False)
        _rock(sc, 30, -12, 7, 5, 6, seed + 4, drift=False)
    else:
        _rock(sc, 0, -4, 8, 5, 6, seed + 5)
    a = _solo(sc, dress=lambda s, a: _cracks(s, a, n=3 if kind == 'large' else 2, seed=seed))
    return K.crop(a, sc.ox, sc.oy)


def crag(kind='a', seed=61):
    """A crag of the headwall's foot: a wide jumble of granite masses of mixed size, staggered in
    depth and height (none a tower), snow lying on every top and ledge, drifts at its west foot.
    The zone's north frame (B8, Z1)."""
    rng = np.random.default_rng(seed + (0 if kind == 'a' else 9))
    sc = K.Scene(-110, 110, -60, 24, 160)
    n = 8 if kind == 'a' else 7
    xs = np.sort(rng.uniform(-70, 70, n))
    for k in range(n):
        rx = rng.uniform(20, 36)
        ry = rx * rng.uniform(0.6, 0.8)
        h = rx * rng.uniform(0.5, 0.8) * (1.2 if abs(xs[k]) < 35 else 1.0) * (1.0 if kind == 'a' else 1.08)
        cy = rng.uniform(-34, 6)
        sc.ellipsoid(xs[k], cy, h, rx, ry, h, GRANITE, base=2.6 + rng.uniform(-0.3, 0.3), k=1.8, tag='rock',
                     mix=rng.random(), flat=3.0 + rng.uniform(0, 0.8), tex='stone')
        _snowcap(sc, xs[k] - rx * 0.1, cy - ry * 0.1, 2 * h - 2.0, rx * 0.72, ry * 0.62, th=4.0, seed=seed + k)
    _drift_west(sc, xs[0] - 14, 8, 12, seed)
    _drift_west(sc, xs[n // 2] - 12, 14, 8, seed + 1)
    a = _solo(sc, dress=lambda s, a: _cracks(s, a, n=8, seed=seed))
    return K.crop(a, sc.ox, sc.oy)


def cairn(kind='standing', seed=47):
    """A Frostline waymark of granite (not the Brackens' gritstone): stones laid in shrinking rings,
    each ring's top under a ledge of snow, the upright capped, a drift at the west foot; `toppled`
    spilled east, `small` a two-ring marker."""
    sc = K.Scene(-44, 48, -30, 20, 90)
    rng = np.random.default_rng(seed)
    if kind == 'standing':
        rings = [(11.0, 8, 0.0, 6.0, 0.55), (8.0, 6, 7.0, 5.4, 0.55), (5.5, 5, 13.5, 4.8, 0.6), (3.0, 4, 19.5, 4.2, 0.6)]
    elif kind == 'toppled':
        rings = [(11.0, 8, 0.0, 6.0, 0.55), (7.5, 6, 6.5, 5.2, 0.5)]
    else:
        rings = [(8.2, 6, 0.0, 4.8, 0.55), (4.2, 4, 5.8, 4.2, 0.6)]
    B.stone_pile(sc, rings, seed, tag='rock', sets=GRANITE, base=2.8, flat=1.9,
                 spill=[(19, 4, 4.2), (25, -3, 3.6), (14, 9, 3.4), (-15, 8, 3.2)] if kind == 'toppled' else None)
    for r, n, z, size, sq in rings:
        _snowcap(sc, -1.0, -0.8, z + size * sq * 1.45, r * 0.8 + 1.5, r * 0.62 + 1.2, th=2.2, seed=int(z * 7) + seed)
    if kind != 'toppled':
        top = rings[-1][2] + rings[-1][3] * rings[-1][4] * 1.5
        sc.ellipsoid(0.5, -0.5, top + 7.5, 3.0, 2.5, 8.5, GRANITE, base=3.0, k=1.9, tag='rock', mix=0.4, flat=1.7)
        _snowcap(sc, 0.0, -0.5, top + 15.2, 2.8, 2.3, th=2.0, seed=seed + 2)
    else:
        sc.box(16, -6, 0, 34, 0, 5, GRANITE, base=2.8, k=1.6, tag='rock', round_=2.2, mix=0.55)
        sc.box(17, -5, 4.5, 30, -1, 6.5, SNOW, base=3.9, k=1.0, tag='snow', round_=1.0)
    _drift_west(sc, -rings[0][0] - 2, 3, 6.0 if kind != 'small' else 4.0, seed)
    del rng
    a = _solo(sc)
    return K.crop(a, sc.ox, sc.oy)


def fire_ring(seed=67):
    """The fallen climbers' camp's hearth, cold under snow: a ring of granite stones capped with
    snow, snow lying in the hearth, the soot and a charred brand showing only where it was scraped
    clear on its south-east side. No green (Z6)."""
    sc = K.Scene(-30, 30, -24, 16, 40)
    rng = np.random.default_rng(seed)
    for k in range(11):
        ang = 2 * math.pi * k / 11 + rng.uniform(-0.2, 0.2)
        x, y = 13.5 * math.cos(ang), 9.5 * math.sin(ang)
        sz = rng.uniform(3.2, 4.4)
        sc.ellipsoid(x, y, sz * 0.5, sz, sz * 0.75, sz * 0.62, GRANITE, base=2.7, k=1.8, tag='rock', mix=rng.random(), flat=1.8)
        _snowcap(sc, x, y, sz * 1.05, sz * 0.75, sz * 0.55, th=1.4, seed=seed + k)
    sc.ellipsoid(-1.5, -1.0, 0.2, 10.5, 7.2, 1.6, SNOW, base=3.7, k=0.9, tag='snow', flat=1.4)       # snow in the hearth
    sc.ellipsoid(3.5, 2.5, 0.6, 3.6, 2.2, 0.9, [('soot', 'soot', 'ash')], base=1.8, k=0.6, tag='soot', flat=1.2)
    sc.box(1, 2, 0.8, 9, 4, 2.4, [('soot', 'timber_cool', 'timber')], base=1.4, k=1.0, tag='brand', round_=0.8)
    a = _solo(sc)
    return K.crop(a, sc.ox, sc.oy)


# ------------------------------------------------------------------------------------------------
# the Col hut (B5: door 87, eaves 123 art px; F-H1, F-H2)
# ------------------------------------------------------------------------------------------------
def _plume_frame(i, n, W, H, seed):
    """One frame of the stove's smoke: a connected plume rising from the pot and leaning east, a
    lit west edge and a cool body, breaking into two or three thinning puffs at its top; cool grey."""
    a = np.full((H, W), -1, np.int32)
    Y, X = np.mgrid[0:H, 0:W] + 0.5
    ph = i / float(n)
    v = (H - Y) / H                                     # 0 at the pot, 1 at the top
    cx = 6 + 16 * v ** 1.4 + 1.6 * np.sin(2 * math.pi * (v * 1.3 - ph))
    wdt = 2.2 + 5.5 * v
    body = np.abs(X - cx) < wdt
    # the plume breaks into puffs in its upper half: gaps travelling up with the phase
    gap = (v > 0.45) & (np.sin(2 * math.pi * (v * 2.4 - ph)) < -0.35)
    body &= ~gap & (v < 0.97)
    lit = body & (X < cx - wdt * 0.35)
    a[body] = C('ash', 4)
    a[body & (X > cx + wdt * 0.25)] = C('ash', 3)
    a[lit] = C('snow_cool', 3)
    a[body & (v > 0.75)] = np.where(lit[body & (v > 0.75)], C('snow_cool', 2), C('ash', 3))
    K.despeckle(a, size=3)
    return a


def col_hut(seed=31):
    """The Col hut at the size guide's Frostline scale (huts: eaves 40 to 44, door about 32 world px):
    rubble granite under slate from the house builder, door leaf 87 art px, eaves at 123. On the roof
    a mass of snow with thickness: a lit top plane, a slight lit crest at the ridge, its end thickness
    showing at each verge, a soft cornice hanging over the eave, a wind scoop in the chimney's lee.
    Icicles 2 texels at the root, gathered at the corners and over the door. A drift banked against
    the foot, rising to the corners and the west, the doorway dug clear. The stove's smoke loops
    as a connected plume (8 frames)."""
    from scripts.art.native import houses as HS
    b = HS.building(HUT_SPEC, seed=seed)
    p = _grow(b.base, 10, 8)
    a = p.a
    H, W = a.shape
    oy, ox = 10, 8
    rm = np.zeros((H, W), bool)
    rm[oy:, ox:ox + b.base.W] = b.info['roof']
    y_r, y_e = b.info['y_r'] + oy, b.info['y_eave'] + oy
    Yg, Xg = np.mgrid[0:H, 0:W]
    stoneish = np.isin(a // 8, [FI[n] for n in ('stone', 'stone_cool', 'stone_warm', 'ashlar', 'ashlar_warm')])
    chim_cols = ndi.binary_dilation((stoneish & (Yg < y_r + 4)).sum(0) > 4, iterations=1)
    stack = chim_cols[None, :] & (Yg < y_e) & (stoneish | (a // 8 == FI['soot']))
    chim = ndi.binary_dilation(stack, structure=np.ones((1, 3), bool))
    roof = rm & ~chim
    cols = np.nonzero(roof.any(0))[0]
    rows = np.nonzero(roof.any(1))[0]
    L, R, top = cols.min(), cols.max(), rows.min()
    rng = np.random.default_rng(seed)
    # the cornice's lower edge: a slow lumpy line about the eave, hanging 1 to 3 texels over it
    prof = ndi.gaussian_filter1d(rng.random(W), 4.0, mode='nearest')
    prof = (prof - prof.mean()) / (prof.std() + 1e-9)
    hang = np.clip(np.round(1.5 + 1.0 * prof), 0, 3).astype(int)
    low = (y_e + hang)[None, :]
    span = (Xg >= L - 2) & (Xg <= R + 2)
    # the ridge: snow heaped over it in soft mounds (1 to 4 texels), not a ruled line
    rp = ndi.gaussian_filter1d(rng.random(W), 3.0, mode='nearest')
    rp = (rp - rp.min()) / max(1e-6, rp.max() - rp.min())
    heap = np.round(1 + 3 * rp).astype(int)
    mass = span & (Yg >= (top - heap)[None, :]) & (Yg <= low)
    # the chimney's lee scoop: the snow thins east of the stack, in a soft hollow
    cx0, cx1 = np.nonzero(chim_cols)[0].min(), np.nonzero(chim_cols)[0].max()
    lee = (((Xg - cx1 - 6) / 9.0) ** 2 + ((Yg - top - 6) / 7.0) ** 2) < 1.0
    mass &= ~chim
    # tones: the top plane lit near the ridge and on the west, the body, cooler to the east and down,
    # broad wind-laid swells (no specks)
    lv = (Yg - top) / max(1, (y_e - top))
    sw_ = ndi.gaussian_filter(rng.random((H, W)), (1.2, 7.0))
    sw_ = (sw_ - sw_.mean()) / (sw_.std() + 1e-9)
    east = (Xg - L) / max(1, R - L)
    tone = 4.6 - 0.9 * lv - 0.6 * east + 0.45 * np.clip(sw_, -1.2, 1.2)
    fam = np.where(east + 0.12 * sw_ > 0.72, FI['snow_cool'], FI['snow'])
    codes = fam * 8 + np.clip(np.round(tone), 2, 5).astype(int)
    a[mass] = codes[mass]
    a[mass & lee] = C('snow_cool', 3)
    # the ridge's lit crest and the snow's top outline
    crest = mass & ~np.roll(mass, 1, 0)
    a[crest] = C('snow', 5)
    above = np.roll(crest, -1, 0) & ~mass & ~chim
    a[above & (Xg >= L) & (Xg <= R)] = C('snow_cool', 2)
    # the cornice's front: its last three rows (lit top row, cool front, a dark underside line)
    edge = mass & ~np.roll(mass, -1, 0)
    for k_, code in ((0, C('snow_cool', 2)), (1, C('snow_cool', 3)), (2, C('snow', 5))):
        sel = np.roll(edge, -k_, 0) & mass
        a[sel] = code
    # the verges: the snow's end thickness (two texels of cool snow down each gable edge)
    for xv, code_v in ((L - 3, C('snow_cool', 2)), (L - 2, C('snow', 5)), (L - 1, C('snow', 5)), (R + 1, C('snow_cool', 3)),
                       (R + 2, C('snow_cool', 3)), (R + 3, C('snow_cool', 2))):
        ys_ = np.nonzero(mass[:, min(max(xv, L - 2), R + 2)])[0]
        if len(ys_):
            a[ys_.min() + 1:ys_.max() + 1, xv] = code_v
    # a cap on the chimney
    ctop = np.nonzero((a[:, cx0:cx1 + 1] >= 0).any(1))[0].min()
    for x in range(cx0 - 1, cx1 + 2):
        for k_ in range(3):
            y = ctop - 1 + k_
            if 0 <= y < H:
                a[y, x] = C('snow', 5 if k_ == 0 else 4) if k_ < 2 else C('snow_cool', 3)
    # icicles under the cornice: gathered at the corners and over the door, 2 texels at the root
    door_l = ox + b.info['L'] + V.q(HUT_SPEC['doors'][0][0])
    door_r = door_l + V.q(HUT_SPEC['door_w'])
    groups = [(L + 2, L + 16), (R - 16, R - 2), (door_l - 2, door_r + 2)]
    for g0, g1 in groups:
        x = g0 + int(rng.integers(0, 3))
        while x < g1:
            col_ = np.nonzero(mass[:, x])[0]
            if len(col_):
                y0 = col_.max() + 1
                n = int(rng.integers(4, 11))
                for k_ in range(n):
                    y = y0 + k_
                    if y >= H:
                        break
                    wide = k_ < max(2, n // 2)
                    a[y, x] = C('snow', 5) if k_ == 0 else C('sky_cool', 5)
                    if wide and x + 1 < W:
                        a[y, x + 1] = C('sky_cool', 4) if k_ > 0 else C('snow', 4)
            x += int(rng.integers(4, 7))
    # the drift against the foot: rises toward the corners and the west, the doorway clear; a lit
    # crest, a cool east fall, a blue shade row on the wall above it
    foot = p.ay
    wl, wr = ox + b.info['L'], ox + b.info['R']
    for x in range(wl - 6, wr + 5):
        if door_l - 4 <= x <= door_r + 3:
            continue
        u = (x - wl) / max(1, wr - wl)
        h = 5 + 9 * max(0.0, 0.35 - u) / 0.35 + 6 * max(0.0, u - 0.8) / 0.2 + 2.0 * prof[x % W]
        if x < wl or x > wr:
            h = max(2, h - 3 * abs(x - (wl if x < wl else wr)))
        h = int(round(h))
        for k_ in range(h):
            y = foot - k_
            if 0 <= y < H:
                a[y, x] = C('snow', 5) if k_ == h - 1 else (C('snow_cool', 4) if x > wr - 10 else C('snow', 4))
        y = foot - h
        if 0 <= y < H and a[y, x] >= 0 and wl <= x <= wr:
            a[y, x] = C('sky_cool', 2)
    V.tidy(p.a)
    q_ = K.crop(p.a, p.ax, p.ay)
    pots = b.info.get('pots') or []
    if pots:
        px, py = pots[0]
        pot_x, pot_y = int(px + ox - p.ax + q_.ax), int(py + oy - p.ay + q_.ay) - 2
    else:
        pot_x, pot_y = int(cx0 + (cx1 - cx0) / 2 - p.ax + q_.ax), int(ctop - p.ay + q_.ay) - 2
    sw, sh = 36, 60
    up = max(0, sh - pot_y + 2)
    east = max(0, pot_x - 6 + sw - q_.W)
    r = V.Pic(q_.W + east, q_.H + up, q_.ax, q_.ay + up)
    r.a[up:, :q_.W] = q_.a
    region = (pot_x - 6, pot_y + up - sh, sw, sh)
    frames = [V.Pic(sw, sh, 0, sh) for _ in range(8)]
    for i, fr in enumerate(frames):
        fr.a[:] = _plume_frame(i, 8, sw, sh, seed)
    return r, {'frames': frames, 'fps': 6.0, 'clip': 'smoke', 'region': region}


# ------------------------------------------------------------------------------------------------
# conifers (F-P1, Z2): the woodland pine's painter at other sizes, snow lying as shelves on its tiers
# ------------------------------------------------------------------------------------------------
CONIFERS = {'spruce': ((0.8, 1.22), 503), 'pine': ((1.0, 1.0), 511), 'squat': ((1.18, 0.74), 521),
            'krummholz': ((1.25, 0.44), 531)}


def _shelves(code, mask, seed, load=1.0):
    """Snow lying on the tiers of a conifer's crown, in place: on every bough top (an opaque texel
    with nothing above it, or with its tier's dark underside above it) a continuous shelf 3 to 6
    texels thick on the west and top, thinning to nothing at the east tips; none in the east third
    of the lower crown; a cool lower edge and a dark green row of shade under it."""
    H, W = mask.shape
    above = np.full_like(code, -1)
    above[1:] = code[:-1]
    leafy = np.isin(code // 8, [FI[n] for n in ('leaf', 'leaf_cool', 'leaf_warm', 'grass', 'grass_cool', 'grass_warm')])
    tops = mask & ((above < 0) | (leafy & (above >= 0) & (above % 8 + 2 <= code % 8)))
    tops = ndi.binary_closing(tops, structure=np.ones((1, 5), bool)) & mask
    ys, xs = np.nonzero(mask)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    snow = np.zeros_like(mask)
    lvl = np.zeros(mask.shape, int)
    lab, n = ndi.label(tops, structure=np.array([[0, 0, 0], [1, 1, 1], [0, 0, 0]]))
    for k in range(1, n + 1):
        ry, rx = np.nonzero(lab == k)
        if len(rx) < 4:
            continue
        xl, xr, yr = rx.min(), rx.max(), int(np.median(ry))
        mid = (xl + xr) / 2.0
        ux = (mid - x0) / max(1, x1 - x0)
        uy = (yr - y0) / max(1, y1 - y0)
        if ux > 0.62 and uy > 0.45:
            continue
        thick = (3.0 + 3.0 * (1 - ux)) * load * (1.0 if uy < 0.8 else 0.7)
        for y, x in zip(ry, rx):
            u = (x - xl) / max(1, xr - xl)
            t = int(round(thick * (1 - u) ** 1.2))
            for j in range(t):
                if y + j < H and mask[y + j, x]:
                    snow[y + j, x] = True
                    lvl[y + j, x] = j
    # tones: top row lit on the west, body, cool lower edge, the shade row under it
    lowest = snow & ~np.roll(snow, -1, 0)
    Xg = np.mgrid[0:H, 0:W][1]
    ux = (Xg - x0) / max(1, x1 - x0)
    c = np.where(lvl == 0, np.where(ux < 0.55, C('snow', 5), C('snow', 4)), C('snow', 4))
    c = np.where(lowest & (lvl > 0), C('snow_cool', 3), c)
    c = np.where(ux > 0.7, np.where(lvl == 0, C('snow', 4), C('snow_cool', 3)), c)
    code[snow] = c[snow]
    under = np.roll(lowest, 1, 0) & mask & ~snow
    code[under] = C('leaf_cool', 0)
    del seed
    return snow


def conifer(form='pine', load=1.0, seed=None):
    """A conifer of the Frostline: the woodland pine's tiered painter (woodtrees.pine_tiers and
    pine_crown, the approved pine's recipe) at another size and seed, so the forms differ in
    silhouette (`spruce` tall and narrow, `pine`, `squat` wind-cropped, `krummholz` a low
    tree-line shrub), with snow as shelves on its tiers and a small heap at the trunk's west foot."""
    from scripts.art.native import compose as CO
    from scripts.art.native import screen as SCR
    from scripts.art.native import woodtrees as WT
    from scripts.art.native import ctx
    scale, s0 = CONIFERS[form]
    seed = s0 if seed is None else seed
    arr = np.asarray(CO.old_sprite(SCR._master('zones_props_pine.png'), raw=True)[0])
    tw = SCR.tree_dims('zones_props_pine.png')['tw']
    d = ctx.D
    rng = np.random.default_rng(seed * 7 + 31)
    fams, wts, lo, hi = WT.LOOKS['pine']
    lad = WT.Ladder(fams, wts)
    S, foot, _ = WT.master_crown(arr, d, size=scale)
    tiers = WT.pine_tiers(S, rng)
    code, mask, _v = WT.pine_crown(S, tiers, lad, rng, lo, hi, fams, wts)
    _shelves(code, mask, seed, load)
    T = tw * d * (0.8 if form == 'krummholz' else 1.0)
    cols = int(round(foot[0]))
    half_t = max(2, int(T / 2))
    band = mask[:, max(0, cols - half_t):cols + half_t + 1]
    bots = [np.nonzero(band[:, j])[0].max() for j in range(band.shape[1]) if band[:, j].any()]
    cb = min(bots) if bots else foot[1] - 10 * d
    length = int(foot[1] - cb + (4 if form == 'krummholz' else 10))
    tc, tm, (tfx, tfy), _ty = WT.trunk2('oak', length, T * 0.6, T * 1.05, rng, lean=2, twist=1.0, roots=3, limbs=0,
                                        limb_rise=12.0, limb_spread=0.0, bark='oak', front_root=False,
                                        root_rows=(5, 12), root_reach=(1, 8), root_w=(0.45, 3.4))
    out, ft = WT._compose((tc, tm, (tfx, tfy)), code, mask, foot)
    WT._close_pinholes(out)
    out, ft = WT._crop(out, ft)
    # the heap of snow at the trunk's west foot
    fx, fy = int(round(ft[0])), int(round(ft[1]))
    pad = 6
    big = np.full((out.shape[0] + 2, out.shape[1] + 2 * pad), -1, np.int64)
    big[:out.shape[0], pad:pad + out.shape[1]] = out
    fx += pad
    for x in range(fx - 14, fx - 1):
        h = int(round(3.2 - abs(x - (fx - 8)) * 0.38))
        for k_ in range(max(0, h)):
            y = fy - k_
            if 0 <= y < big.shape[0]:
                big[y, x] = C('snow', 5) if k_ == h - 1 else C('snow', 4)
    out = big
    pic = K.crop(out.astype(np.int32), fx, fy)
    return pic


def snag(seed=541):
    """A dead pine at the tree line: a weathered grey bole leaning a little east and tapering, its
    top snapped into two jagged points, four stub limbs of different lengths, snow on the break and
    the stubs, a drift at its west foot, a root flare."""
    sc = K.Scene(-36, 36, -16, 14, 200)
    rng = np.random.default_rng(seed)
    h = 0.0
    r = 7.0
    x = 0.0
    sc.ellipsoid(0, 0, 2.0, 11, 7, 4.0, WEATHERED, base=2.4, k=1.6, tag='wood', flat=1.2)          # the root flare
    for k in range(8):
        z1 = h + 17 + rng.uniform(-2, 2)
        sc.cylinder(x, 0, r, h, z1, WEATHERED, base=2.7, k=1.7, tag='wood', mix=rng.random(), tex='wood_v')
        h = z1
        r = max(2.2, r - 0.6)
        x += 0.6 + k * 0.08
    sc.cylinder(x - 1.2, 0, 1.6, h, h + 14, WEATHERED, base=2.9, k=1.7, tag='wood')                 # the snapped points
    sc.cylinder(x + 1.4, 0, 1.3, h, h + 8, WEATHERED, base=2.6, k=1.7, tag='wood')
    for (z, ln, side) in ((58, 9, -1), (78, 13, 1), (101, 7, -1), (119, 10, 1)):
        xx = x * z / max(1.0, h)
        x0, x1 = (xx - ln - 2, xx - 1) if side < 0 else (xx + 1, xx + ln + 2)
        sc.box(x0, -1.3, z, x1, 1.3, z + 2.6, WEATHERED, base=2.8, k=1.6, tag='wood', round_=0.8)
        sc.box(x0 + 1, -1.3, z + 2.3, x1 - 1, 1.3, z + 4.0, SNOW, base=3.9, k=1.0, tag='snow', round_=0.6)
    _snowcap(sc, x - 1.2, 0.0, h + 14.5, 1.8, 1.6, th=1.4, seed=seed)
    _drift_west(sc, -9, 2, 9, seed)
    a = _solo(sc)
    return K.crop(a, sc.ox, sc.oy)


# ------------------------------------------------------------------------------------------------
# the ice-cutter's sledge and the cut blocks (F-S1, B4)
# ------------------------------------------------------------------------------------------------
ICE = [('water_cool', 'sky_cool', 'sky_cool')]
ROPE = [('earth_cool', 'sand_cool', 'sand_warm')]
IRON = [('soot', 'iron', 'iron')]


def _ice_faces(sc, a, seed):
    """The cut blocks drawn as translucent lake ice: a frosted lit top plane, front faces in bands
    deepening downward, a lit west edge, a dark east face, saw-cut striations, a crack line and air
    bubbles in clusters."""
    rng = np.random.default_rng(seed)
    ids = [i for i, s_ in enumerate(sc.solids) if s_.tag == 'ice']
    for i in ids:
        m = sc.label == i
        if not m.any():
            continue
        nz, ny, nx = sc.n[..., 2], sc.n[..., 1], sc.n[..., 0]
        topm = m & (nz > 0.6)
        front = m & (ny > 0.5) & ~topm
        eastm = m & (nx > 0.5) & ~topm
        a[topm] = np.where(sc.gy[topm] < np.median(sc.gy[topm]) if topm.any() else False, C('snow', 5), C('snow', 4))
        if front.any():
            ys, xs = np.nonzero(front)
            yt, yb = ys.min(), ys.max()
            v = (ys - yt) / max(1, yb - yt)
            band = np.where(v < 0.25, C('sky_cool', 5), np.where(v < 0.55, C('sky_cool', 4), np.where(v < 0.85, C('sky_cool', 3),
                                                                                                             C('water_cool', 3))))
            a[ys, xs] = band
            xl = xs.min()
            a[ys[xs == xl], xl] = C('snow_cool', 4)                               # the lit west edge
            stri = ((ys - yt) % 4 == 2) & (xs > xl + 1) & (np.array([hsh(seed, x // 3, i) for x in xs]) > 0.35)
            a[ys[stri], xs[stri]] = np.where(v[stri] < 0.5, C('sky_cool', 3), C('water_cool', 2))
            # a crack and a cluster of bubbles
            cx = int(rng.integers(xs.min() + 2, max(xs.min() + 3, xs.max() - 2)))
            for k_ in range(int((yb - yt) * 0.7)):
                y = yt + 1 + k_
                x = cx + (k_ // 3) % 2
                if 0 <= y < a.shape[0] and front[y, x]:
                    a[y, x] = C('sky_cool', 2)
            bx, by = int(rng.integers(xs.min() + 2, max(xs.min() + 3, xs.max() - 3))), int(yt + (yb - yt) * 0.6)
            for dx, dy in ((0, 0), (2, -1), (1, 2)):
                if 0 <= by + dy < a.shape[0] and 0 <= bx + dx < a.shape[1] and front[by + dy, bx + dx]:
                    a[by + dy, bx + dx] = C('sky_cool', 5)
        if eastm.any():
            a[eastm] = C('water_cool', 2)


def _line(a, p0, p1, code, w=1):
    n = int(max(abs(p1[0] - p0[0]), abs(p1[1] - p0[1]))) + 1
    for t in np.linspace(0, 1, n):
        x = int(round(p0[0] + (p1[0] - p0[0]) * t))
        y = int(round(p0[1] + (p1[1] - p0[1]) * t))
        for k_ in range(w):
            if 0 <= y < a.shape[0] and 0 <= x + k_ < a.shape[1]:
                a[y, x + k_] = code


def sledge(seed=53):
    """The ice-cutter's sledge: two runners turned up at the front in a smooth curl with iron
    shoeing, a plank bed on short posts, three blocks of lake ice lashed on it with a rope that
    crosses them diagonally to knots at the bed rail, and the bow saw leaning against its east end
    at an angle (a curved timber bow, a toothed blade catching the light)."""
    sc = K.Scene(-52, 52, -24, 14, 90)
    for y0 in (-13.0, 3.0):
        sc.box(-30, y0, 0, 30, y0 + 3, 3, OAK, base=2.5, k=1.5, tag='runner', round_=1.0)
        sc.box(-30, y0, -0.5, 31, y0 + 3, 0.6, IRON, base=2.6, k=1.4, tag='iron')
        for k in range(10):                                 # the curl, in one-texel steps on an arc
            ang = math.pi * k / 18.0
            x = -30 - 6 * math.sin(ang)
            z = 6 - 6 * math.cos(ang)
            sc.box(x - 1.2, y0, z, x + 0.2, y0 + 3, z + 2.6, OAK, base=2.7, k=1.5, tag='runner', round_=0.6)
    for x in (-22, 0, 22):
        for y0 in (-13.0, 3.0):
            sc.box(x - 2, y0, 3, x + 2, y0 + 3, 8, OAK, base=2.1, k=1.4, tag='post')
    sc.box(-28, -15, 8, 28, 7, 11, OAK, base=2.8, k=1.6, tag='bed', round_=0.8, tex='wood')
    sc.box(-28, 6, 9, 28, 8, 13, OAK, base=2.4, k=1.6, tag='rail', round_=0.6)
    blocks = [(-25, -11, -10, 3, 13), (-7, -12, 7, 4, 11), (10, -10, 25, 3, 14)]
    for k, (x0, y0, x1, y1, h) in enumerate(blocks):
        sc.box(x0, y0, 11, x1, y1, 11 + h, ICE, base=3.4, k=1.3, tag='ice', round_=1.2)
    sc.render()
    a = sc.shade(crevice=1.0, rim=0.6)
    _ice_faces(sc, a, seed)
    V.tidy(a)
    V.outline(a)
    # the rope: two diagonals over the load to knots on the rail
    oxn, oyn = sc.ox, sc.oy
    p = lambda x, y, z: (oxn + x, oyn + y - z)     # noqa: E731
    for (x0, x1) in ((-26, 8), (26, -8)):
        _line(a, p(x0, 7, 12), p(x1 * 0.2, -2, 26), C('sand_cool', 3))
        _line(a, p(x0, 7, 12), p(x0 + (1 if x0 < 0 else -1), 7, 10), C('earth_cool', 1))
        kx, ky = p(x0, 7, 12)
        for dx, dy in ((0, 0), (1, 0), (0, 1)):
            if 0 <= ky + dy < a.shape[0] and 0 <= kx + dx < a.shape[1]:
                a[ky + dy, kx + dx] = C('sand_warm', 4)
    # the bow saw against the east end, leaning: the bow (a curve), the blade (straight, toothed)
    bx0, by0 = p(33, 4, 0)
    bx1, by1 = p(44, 4, 34)
    n = 26
    for k in range(n + 1):
        t = k / n
        x = bx0 + (bx1 - bx0) * t + 5 * math.sin(math.pi * t)
        y = by0 + (by1 - by0) * t
        for dx in (0, 1):
            xi, yi = int(round(x)) + dx, int(round(y))
            if 0 <= yi < a.shape[0] and 0 <= xi < a.shape[1]:
                a[yi, xi] = C('timber', 3) if dx == 0 else C('timber_cool', 2)
    for k in range(n + 1):
        t = k / n
        x = int(round(bx0 + (bx1 - bx0) * t)) - 1
        y = int(round(by0 + (by1 - by0) * t))
        if 0 <= y < a.shape[0] and 0 <= x < a.shape[1]:
            a[y, x] = C('iron', 4) if k % 3 else C('snow', 5)
    return K.crop(a, sc.ox, sc.oy)


def ice_stack(seed=59):
    """The ice-cut's stack on the shore: cut blocks in two courses, frosted on top, a little snow
    blown against their west end."""
    sc = K.Scene(-40, 40, -24, 14, 80)
    blocks = [(-26, -12, 0, -9, 2, 14), (-7, -13, 0, 10, 1, 13), (12, -11, 0, 28, 3, 15), (-17, -10, 14, 0, 0, 26),
              (3, -11, 13, 19, -1, 25)]
    for (x0, y0, z0, x1, y1, z1) in blocks:
        sc.box(x0, y0, z0, x1, y1, z1, ICE, base=3.4, k=1.3, tag='ice', round_=1.2)
    _drift_west(sc, -28, 0, 7, seed)
    sc.render()
    a = sc.shade(crevice=1.0, rim=0.6)
    _ice_faces(sc, a, seed)
    V.tidy(a)
    V.outline(a)
    return K.crop(a, sc.ox, sc.oy)


# ------------------------------------------------------------------------------------------------
# the hut's yard and the Col Path's markers (Z5)
# ------------------------------------------------------------------------------------------------
def woodpile(seed=71):
    """The warden's woodpile against the cold: split logs stacked between two stakes, their cut ends
    to the south (rings drawn on them), a slab of snow on top and against its west end."""
    sc = K.Scene(-40, 40, -20, 12, 70)
    sc.box(-30, -8, 0, 30, 6, 24, B.OAK, base=2.6, k=1.5, tag='pile', round_=2.0, tex='wood')
    for x in (-32, 31):
        sc.box(x - 1.5, -2, 0, x + 1.5, 1, 30, B.OAK, base=2.2, k=1.5, tag='stake')
    sc.box(-30, -9, 23.5, 26, 6, 28, SNOW, base=3.9, k=1.0, tag='snow', round_=2.0)
    _drift_west(sc, -32, 4, 7, seed)
    sc.render()
    a = sc.shade()
    rng = np.random.default_rng(seed)
    m = np.isin(sc.label, [i for i, s_ in enumerate(sc.solids) if s_.tag == 'pile']) & (sc.n[..., 1] > 0.5)
    ys, xs = np.nonzero(m)
    if len(ys):
        for row in range(ys.min() + 3, ys.max() - 1, 7):
            for col in range(xs.min() + 3 + (row // 7 % 2) * 3, xs.max() - 2, 7):
                r = rng.uniform(2.4, 3.2)
                for dy in range(-3, 4):
                    for dx in range(-3, 4):
                        q = (dx * dx + dy * dy) / (r * r)
                        y, x = row + dy, col + dx
                        if q <= 1 and 0 <= y < a.shape[0] and 0 <= x < a.shape[1] and m[y, x]:
                            a[y, x] = C('sand_warm', 4) if q < 0.3 else (C('sand_cool', 3) if q < 0.75 else C('timber_cool', 1))
    V.tidy(a)
    V.outline(a)
    return K.crop(a, sc.ox, sc.oy)


def hut_tools(seed=73):
    """Stuck in a heap of snow by the hut door: a pair of wooden skis with turned-up tips and two
    poles, and a snow shovel."""
    sc = K.Scene(-30, 30, -14, 12, 90)
    sc.ellipsoid(0, 0, 1, 16, 8, 6, SNOW, base=3.8, k=1.0, tag='snow', flat=1.2)
    for x in (-9, -4):
        sc.box(x, -1, 2, x + 3, 1, 62, B.OAK, base=2.9, k=1.5, tag='ski', round_=1.0)
        sc.box(x, -2.5, 60, x + 3, -0.5, 66, B.OAK, base=3.1, k=1.5, tag='ski', round_=1.0)
    for x in (1, 5):
        sc.cylinder(x, 1, 0.8, 2, 52, IRON, base=2.6, k=1.4, tag='pole')
        sc.cylinder(x, 1, 1.6, 10, 11, [('soot', 'earth_cool', 'earth')], base=2.0, k=1.0, tag='basket')
    sc.cylinder(13, 2, 1.0, 4, 46, B.OAK, base=2.7, k=1.5, tag='shovel')
    sc.box(9, 0, 2, 17, 3, 15, IRON, base=2.6, k=1.5, tag='blade', round_=0.6)
    a = _solo(sc)
    return K.crop(a, sc.ox, sc.oy)


def bench(seed=79):
    """A granite slab bench by the Col Path, the snow brushed off the west half of the seat."""
    sc = K.Scene(-40, 40, -16, 10, 50)
    for x in (-23, 17):
        sc.box(x, -6, 0, x + 6, 3, 13, GRANITE, base=2.6, k=1.7, tag='rock', round_=1.2, tex='stone')
    sc.box(-30, -8, 13, 30, 5, 18, GRANITE, base=2.9, k=1.7, tag='rock', round_=1.5, tex='stone')
    sc.box(0, -8, 17.5, 29, 5, 20.5, SNOW, base=3.9, k=1.0, tag='snow', round_=1.4)
    _drift_west(sc, -28, 5, 6, seed)
    a = _solo(sc, dress=lambda s, a: _cracks(s, a, n=1, seed=seed))
    return K.crop(a, sc.ox, sc.oy)


def noticeboard(seed=83):
    """The warden's board at the foot of the col: two posts, a plank board under a little pent roof
    with snow on it, notices pinned (weather, the ring shut)."""
    sc = K.Scene(-36, 36, -10, 10, 110)
    for x in (-20, 17):
        sc.box(x, -2, 0, x + 3, 1, 78, B.OAK, base=2.4, k=1.5, tag='post')
    sc.box(-24, -2, 40, 24, 1, 74, B.OAK, base=2.7, k=1.4, tag='board', tex='wood')
    sc.box(-27, -6, 74, 27, 4, 78, [('slate_cool', 'slate', 'slate')], base=2.6, k=1.6, tag='roof', round_=0.8)
    sc.box(-26, -6, 77.5, 25, 4, 81.5, SNOW, base=3.9, k=1.0, tag='snow', round_=1.5)
    _drift_west(sc, -22, 3, 7, seed)
    sc.render()
    a = sc.shade()
    p = lambda x, y, z: (sc.ox + x, sc.oy + y - z)     # noqa: E731
    for (x0, z0, x1, z1, fam) in ((-20, 70, -4, 50, 'plaster'), (0, 68, 18, 56, 'plaster_warm'), (-2, 52, 12, 44, 'plaster')):
        X0, Y0 = p(x0, 1, z0)
        X1, Y1 = p(x1, 1, z1)
        a[Y0:Y1, X0:X1] = C(fam, 4)
        for yy in range(Y0 + 2, Y1 - 1, 2):
            a[yy, X0 + 2:X1 - 2 - (yy % 3)] = C('stone_cool', 2)
        a[Y0, X0 + (X1 - X0) // 2] = C('berry', 3)
    V.tidy(a)
    V.outline(a)
    return K.crop(a, sc.ox, sc.oy)


def snow_pole(seed=89):
    """A snow pole marking the Col Path where drifts cover it: a tall stake banded red and white,
    a cap of snow, a drift at its foot."""
    sc = K.Scene(-14, 14, -8, 8, 110)
    for k in range(8):
        z0 = k * 11.0
        sets = RED if k % 2 else [('plaster', 'plaster', 'plaster_warm')]
        sc.cylinder(0, 0, 1.8, z0, z0 + 11.0, sets, base=3.0, k=1.4, tag='pole')
    _snowcap(sc, 0, 0, 88.6, 2.4, 2.0, th=1.4, seed=seed)
    _drift_west(sc, -2, 2, 6, seed)
    a = _solo(sc)
    return K.crop(a, sc.ox, sc.oy)


def lost_hat(seed=97):
    """A story detail on the path: a red bobble hat dropped in the snow, half drifted over."""
    sc = K.Scene(-14, 14, -10, 8, 20)
    sc.ellipsoid(0, 0, 2.5, 6, 4.5, 4.0, RED, base=2.8, k=1.5, tag='hat', flat=1.2)
    sc.box(-6, -1, 0, 6, 3, 2.2, [('plaster', 'plaster', 'plaster_warm')], base=3.4, k=1.0, tag='band', round_=1.0)
    sc.ellipsoid(1, -1, 7.2, 2.2, 2.0, 2.0, [('plaster', 'plaster', 'plaster_warm')], base=3.6, k=1.0, tag='bobble')
    sc.ellipsoid(4.5, 1.5, 1.6, 5, 3.5, 2.2, SNOW, base=3.8, k=0.9, tag='snow', flat=1.3)
    a = _solo(sc)
    return K.crop(a, sc.ox, sc.oy)


# ------------------------------------------------------------------------------------------------
# the cirque's step (B7): a 32 px granite face with a snow lip, its stair and its frozen fall
# ------------------------------------------------------------------------------------------------
FACE_PX = 96          # the face's height in art px (32 world px, one Frostline tier: size guide)
LIP_PX = 12


def _face(width, seed, ends=(True, True), fall=None, stair=None):
    """A south-facing granite face `width` texels wide: a snow lip hanging over its top (a lit row,
    a cool front, a blue shade row on the rock), courses of granite blocks 12 to 20 texels tall lit
    on their top rows and west ends, dark joints and east ends, snow lying on some course tops,
    cracks, the lower third in shade, a dark foot and drifts banked against it. Side bands at the
    ends (lit facing west, in shade facing east). `fall`: (x0, x1) a frozen fall over the face;
    `stair`: the face cut by a granite stair (treads snow-dusted, risers in shade, cheeks)."""
    rng = np.random.default_rng(seed)
    H = LIP_PX + FACE_PX + 6
    W = width
    a = np.full((H, W), -1, np.int32)
    Yg, Xg = np.mgrid[0:H, 0:W]
    lip = (LIP_PX - 4 + 2.0 * ndi.gaussian_filter1d(rng.standard_normal(W), 4.0, mode='nearest')).round().astype(int)
    lip = np.clip(lip, 5, LIP_PX)
    top = Yg < lip[None, :]
    yf = LIP_PX + FACE_PX                                  # the foot line
    face = (Yg >= lip[None, :]) & (Yg < yf)
    # granite in jointed facets (not masonry): a Voronoi of blocks taller than wide, each facet a
    # tone of its own turned toward or away from the light, its top-left rim lit, its bottom-right
    # joint dark; the lower third in shade; snow lying on some facets' tops
    n_seed = max(4, W * FACE_PX // 900)
    sx = rng.uniform(0, W, n_seed)
    sy = rng.uniform(LIP_PX - 6, yf + 6, n_seed)
    dx = (Xg[..., None] - sx[None, None, :]) / 1.0
    dy = (Yg[..., None] - sy[None, None, :]) / 1.6
    lab = np.argmin(dx * dx + dy * dy, -1)
    turn = rng.uniform(-1, 1, n_seed)                     # a facet's turn to the light
    fam_k = rng.random(n_seed)
    depth = (Yg - LIP_PX) / FACE_PX
    ytop = np.array([sy[k] - 18 for k in range(n_seed)])
    grain = K.texture('stone', Xg, Yg, seed)
    tone = 3.0 + 0.6 * turn[lab] - 1.4 * depth - 0.5 * np.clip((Yg - ytop[lab]) / 40.0, 0, 1) + 0.7 * grain
    fam = np.where(fam_k[lab] > 0.75, FI['iron'], FI['slate'])
    a[face] = (fam * 8 + np.clip(np.round(tone), 1, 4).astype(int))[face]
    up_ = np.roll(lab, 1, 0)
    lf_ = np.roll(lab, 1, 1)
    dn_ = np.roll(lab, -1, 0)
    rt_ = np.roll(lab, -1, 1)
    rim_tl = face & ((up_ != lab) | (lf_ != lab)) & (Yg > 0) & (Xg > 0)
    rim_br = face & ((dn_ != lab) | (rt_ != lab))
    # only near-level tops catch the light or hold snow (a slanted joint is a joint, not a ledge)
    toprow = face & (up_ != lab)
    level = toprow & np.roll(toprow, 2, 1) & np.roll(toprow, -2, 1)
    lit_rim = level & (turn[lab] > 0.25)
    a[lit_rim] = np.clip(a[lit_rim] % 8 + 1, 0, 4) + (a[lit_rim] // 8) * 8
    dark = rim_br & (dn_ != lab)
    a[dark] = np.where(depth[dark] > 0.5, C('slate_cool', 0), C('slate_cool', 1))
    side = rim_br & (rt_ != lab) & (dn_ == lab) & (turn[lab] < 0.2)
    a[side] = C('slate_cool', 1)
    for k in range(n_seed):
        if hsh(seed + 2, k) > 0.55 and LIP_PX + 8 < sy[k] < yf - 20:
            top_edge = level & (lab == k)
            ys_, xs_ = np.nonzero(top_edge)
            for y, x in zip(ys_, xs_):
                if hsh(seed + 3, x // 5, k) > 0.35:
                    for k_ in range(3):
                        if y + k_ < yf and lab[y + k_, x] == k:
                            a[y + k_, x] = C('snow', 5) if k_ == 0 else (C('snow', 4) if k_ == 1 else C('snow_cool', 3))
    # cracks
    for _ in range(max(2, W // 40)):
        x = float(rng.integers(4, W - 4))
        yy = float(LIP_PX + rng.integers(6, 40))
        for _j in range(int(rng.integers(10, 30))):
            xi, yi = int(x), int(yy)
            if yi >= yf or not (0 <= xi < W):
                break
            a[yi, xi] = C('slate_cool', 0)
            if xi > 0:
                a[yi, xi - 1] = C('slate', 4)
            yy += 1
            x += rng.choice((-1, 0, 0, 1)) * 0.7
    # the lip: snow over the top, its front a lit row, a cool front, and a blue shade row on the rock
    a[top] = C('snow', 4)
    sw_ = ndi.gaussian_filter1d(rng.random(W), 6.0, mode='nearest')
    a[top & (Yg < 3) & (sw_[None, :] > np.median(sw_))] = C('snow', 5)
    for x in range(W):
        l = lip[x]
        a[l - 2, x] = C('snow', 5)
        a[l - 1, x] = C('snow_cool', 3)
        if l < yf:
            a[l, x] = C('sky_cool', 2)
    # the foot: a dark contact row, drifts banked against the face
    a[yf - 1] = C('slate_cool', 0)
    dp = ndi.gaussian_filter1d(rng.random(W), 7.0, mode='nearest')
    dp = (dp - dp.min()) / max(1e-6, dp.max() - dp.min())
    for x in range(W):
        h = int(round(9 * dp[x] - 2))
        for k_ in range(max(0, h)):
            yy = yf - 1 - k_
            a[yy, x] = C('snow', 5) if k_ == h - 1 else (C('snow', 4) if dp[x] > 0.5 else C('snow_cool', 4))
    for k_ in range(6):
        a[yf + k_, :] = -1
    # ends: side bands
    if ends[0]:
        band = face & (Xg < 5)
        a[band] = np.where(Xg[band] == 0, C('slate_cool', 1), C('slate', 4))
    if ends[1]:
        band = face & (Xg >= W - 5)
        a[band] = np.where(Xg[band] == W - 1, C('slate_cool', 0), C('slate_cool', 1))
    if fall is not None:
        f0, f1 = fall
        col = (Xg >= f0) & (Xg < f1) & (Yg >= lip[None, :] - 2) & (Yg < yf + 3)
        # icicle columns of varied widths and lengths, lit on their west, blue in their bodies
        a[col] = C('slate_cool', 1)
        x = f0
        while x < f1:
            w = int(rng.integers(2, 6))
            ln = int(FACE_PX * rng.uniform(0.55, 1.0))
            for xx in range(x, min(f1, x + w)):
                k_ = xx - x
                for yy in range(lip[xx] - 1, min(yf + 3, lip[xx] + ln - (k_ % 2) * 3)):
                    a[yy, xx] = (C('snow', 5) if k_ == 0 else C('sky_cool', 5) if k_ == 1 else
                                 C('sky_cool', 4) if k_ < w - 1 else C('sky_cool', 3))
            x += w + int(rng.integers(0, 2))
        a[yf - 3:yf + 3, f0:f1] = C('snow_cool', 4)
        a[yf - 1, f0 + 2:f1 - 2] = C('sky_cool', 5)
    if stair is not None:
        s0, s1 = stair
        n = 6
        mid0, mid1 = s0 + (s1 - s0) * 0.22, s1 - (s1 - s0) * 0.22
        for k_ in range(n):
            ty = LIP_PX + int(FACE_PX * k_ / n) - 2
            by = LIP_PX + int(FACE_PX * (k_ + 1) / n) - 2
            span = (Xg >= s0) & (Xg < s1)
            tread = span & (Yg >= ty) & (Yg < ty + 4)
            worn = tread & (Xg >= mid0 + (k_ % 2) * 3) & (Xg < mid1 - ((k_ + 1) % 2) * 3)
            a[tread] = C('slate', 3)
            a[span & (Yg == ty)] = C('slate', 4)                       # the step's lit nose
            a[worn] = C('snow_cool', 4)
            a[worn & (Yg == ty)] = C('snow', 5)
            a[tread & ~worn & (Yg == ty + 1) & (Xg % 7 < 3)] = C('snow', 4)   # snow lodged at the sides
            riser = span & (Yg >= ty + 4) & (Yg < by)
            rv = (Yg - ty - 4) / max(1, by - ty - 4)
            a[riser] = np.where(rv[riser] < 0.3, C('slate', 2), C('slate_cool', 1))
            a[riser & ((Xg + k_ * 5) % 23 == 0)] = C('slate_cool', 0)   # the joints between the step stones
            a[span & (Yg == by - 1)] = C('slate_cool', 0)
            for xx in range(int(mid0) + 6 + (k_ % 2) * 8, int(mid1) - 6, 18):
                a[ty + 1:ty + 3, xx:xx + 2] = C('snow_cool', 2)          # bootprints in the worn snow
        a[(Yg < LIP_PX) & (Xg >= s0) & (Xg < s1)] = C('snow_cool', 4)       # the trod's top cut through the lip
        for xs_ in range(s0 - 3, s0 + 1):
            if 0 <= xs_ < W:
                a[LIP_PX - 4:yf, xs_] = C('slate', 4) if xs_ >= s0 - 1 else C('slate', 3)
        for xs_ in range(s1, s1 + 4):
            if 0 <= xs_ < W:
                a[LIP_PX - 4:yf, xs_] = C('slate_cool', 0) if xs_ == s1 else C('slate_cool', 1)
    return V.Pic(W, H, W // 2, yf - 1), a


def rockface(width_cells=6, seed=101, ends=(True, True)):
    pic, a = _face(width_cells * 24, seed, ends=ends)
    pic.a[:] = a
    return pic


def rockface_fall(seed=113):
    """The face where the tarn's outlet comes over it, frozen into a curtain of icicles."""
    pic, a = _face(4 * 24, seed, ends=(False, False), fall=(12, 84))
    pic.a[:] = a
    return pic


def rock_stair(seed=127):
    """The Col Path's stair up the face: five cells (40 world px, over the 34 a stair needs), six
    granite steps with snow-dusted treads, cut through the lip."""
    pic, a = _face(5 * 24, seed, ends=(False, False), stair=(4, 116))
    pic.a[:] = a
    return pic


def footbridge(seed=131):
    """The Col Path's crossing of the tarn's outlet: a plank bridge five cells long, its planks
    across the way with snow in their joints and along the rails, two low log rails capped with
    snow, granite abutments at the ends."""
    W, H = 5 * 24, 2 * 24 + 18
    a = np.full((H, W), -1, np.int32)
    rng = np.random.default_rng(seed)
    y0, y1 = 14, H - 6
    for x in range(10, W - 10):
        pk = (x - 10) // 6
        edge = (x - 10) % 6 == 5
        a[y0:y1, x] = C('snow_cool', 3) if edge else C('timber', 3 if pk % 2 else 2)
        a[y0, x] = C('snow', 4)
        if not edge and hsh(seed, pk) > 0.5:
            a[y0 + 4:y0 + 4 + int(rng.integers(2, 6)), x] = C('snow', 4)
    a[y1:y1 + 3, 10:W - 10] = C('timber_cool', 1)
    for yr in (y0 - 6, y1 - 3):
        a[yr:yr + 5, 6:W - 6] = C('timber', 3)
        a[yr, 6:W - 6] = C('snow', 5)
        a[yr + 1, 6:W - 6] = C('snow', 4)
        a[yr + 4, 6:W - 6] = C('timber_cool', 1)
    for (xa, xb) in ((0, 12), (W - 12, W)):
        a[y0 - 8:y1 + 4, xa:xb] = C('slate', 3)
        a[y0 - 8, xa:xb] = C('snow', 5)
        a[y0 - 7:y0 - 4, xa:xb] = C('snow', 4)
        a[y1 + 3, xa:xb] = C('slate_cool', 0)
    V.outline(a)
    pic = V.Pic(W, H, W // 2, H - 1)
    pic.a[:] = a
    return pic


# ================================================================================================
# the pieces
# ================================================================================================
def _rel(rel, what, cells=None, note=None):
    return B._rel(rel, what, cells, note)


def _piece(pid, name, variants, size, cells, purpose, role, **kw):
    shadow = kw.pop('shadow', None)
    deck = kw.pop('deck', None)
    zsort = kw.pop('z_sort', None)
    pc = B._piece(pid, name, variants, size, cells, purpose, role, shadow=None, **kw)
    pc['biomes'] = list(BIOMES)
    pc['approval']['standard'] = STANDARD
    for v in pc['variants']:
        v['png'] = v['png'].replace(B.RES, RES)
    if pc['rendering'].get('animations'):
        for an in pc['rendering']['animations']:
            an['strip'] = an['strip'].replace(B.RES, RES)
    # the cast shadow (B6, Z4): an ellipse no wider than the footprint and a tenth, its west end at
    # the object's west edge and thrown a little east and down from there; nothing reaches west.
    # (size is the ellipse's radii in world px, dir its centre's offset from the foot.)
    if shadow:
        hw, ry = shadow
        rx = round(hw * 1.1, 1)
        pc['rendering']['cast_shadow'] = {'shape': 'ellipse', 'size': [rx, ry], 'dir': [round(rx - hw, 1), round(ry * 0.6, 1)]}
    else:
        pc['rendering']['cast_shadow'] = {'shape': 'none'}
    if deck:
        pc['gameplay']['deck'] = deck
    if zsort:
        pc['geometry']['z_sort'] = zsort
    pc['audit']['painter'] = {'module': 'scripts.art.kit.sets.frost', 'fn': kw.get('fn') or pid.replace('frost_', ''), 'args': {}}
    pc['audit']['seeded_from'] = 'scripts/art/kit/sets/frost.py'
    return pc


NATURE = B.NATURE
OFF_ROUTE = B.OFF_ROUTE
OFF_WATER = B.OFF_WATER
NEAR_HUT = _rel('within', 'house', 4, 'the warden\'s yard: by the Col hut it serves')


def prop_jobs():
    """(piece id, [(variant id, thunk)], piece kwargs)."""
    trees = dict(purpose='grow', role='tree', composition='cluster', forbids=NATURE, eastward='22 (the tiered pines)')
    return [
        ('frost_col_hut', [('still', lambda: col_hut())], dict(
            name='Col hut', purpose='live', role='house', cells=(10, 4), fp=B._fp(9, 3),
            collision={'shape': 'rect', 'rect': [-34.0, -26.0, 68, 26]}, shadow=(34.0, 5.0), composition='edge',
            door_cells=[[-1, 0], [0, 0]], doors=[{'x': [-30, 12], 'faces': 's'}],
            requires=[_rel('near', 'route', 3, 'on the Col Path, its door on the trod')], forbids=NATURE,
            extra={'provides': ['home', 'hearth']},
            size_class='hut (148 to 252 tall, 178 to 296 wide: size-guide Frostline "huts (eaves 40 to 44, door 32)")',
            eastward='12 (the stone hut: 2.5 A to the ridge, 3 A wide; doors 0.96 to 1.02 A)', fn='col_hut',
            note='The hut warden\'s bothy: rubble granite under slate at the Frostline hut scale (door leaf 87 art px, eaves '
                 '123), snow lying on the roof as a mass with a cornice, icicles at the corners and over the door, a drift '
                 'at the foot with the doorway dug clear; the stove\'s plume loops (8 frames) over the still.')),
        ('frost_spruce', [('still', lambda: conifer('spruce'))], dict(
            name='Snowy spruce', cells=(3, 2), fp=B._fp(2, 1), collision={'shape': 'rect', 'rect': [-5.0, -4.0, 10, 4]},
            size_class='conifer (a tall spruce)', fn='conifer',
            note='A tall narrow spruce from the woodland pine\'s tiered painter, snow as shelves on its tiers.', **trees)),
        ('frost_pine', [('still', lambda: conifer('pine'))], dict(
            name='Snowy pine', cells=(4, 2), fp=B._fp(2, 1), collision={'shape': 'rect', 'rect': [-5.0, -4.0, 10, 4]},
            size_class='conifer (the woodland\'s pine, 79 world px)', fn='conifer',
            note='The woodland pine\'s painter with snow as shelves on its tiers (thick west, thinning east).', **trees)),
        ('frost_pine_squat', [('still', lambda: conifer('squat'))], dict(
            name='Wind-cropped pine', cells=(4, 2), fp=B._fp(2, 1), collision={'shape': 'rect', 'rect': [-5.0, -4.0, 10, 4]},
            size_class='conifer (wind-cropped, three quarters of the pine)', fn='conifer',
            note='A squat pine cropped by the wind, its snow shelves on the west.', **trees)),
        ('frost_krummholz', [('still', lambda: conifer('krummholz'))], dict(
            name='Krummholz', cells=(4, 2), fp=B._fp(3, 1), collision={'shape': 'rect', 'rect': [-9.0, -4.0, 18, 4]},
            size_class='conifer (krummholz: a wind-flattened spruce at the tree line)', fn='conifer',
            note='A pine at the tree line grown low and wide, snow on its tiers.', **trees)),
        ('frost_snag', [('still', lambda: snag())], dict(
            name='Dead pine', cells=(2, 2), fp=B._fp(1, 1), collision={'shape': 'rect', 'rect': [-3.0, -3.0, 6, 3]},
            size_class='snag (a dead spruce, its crown gone)', fn='snag',
            note='A weathered dead pine with a broken top and two stub limbs, snow on the break and the stubs.', **trees)),
        ('frost_boulder', [('a', lambda: boulder('a')), ('b', lambda: boulder('b'))], dict(
            name='Granite boulder', purpose='mark', role='rock', cells=(3, 2), fp=B._fp(2, 1),
            collision={'shape': 'rect', 'rect': [-6.0, -5.0, 12, 5]}, shadow=(6.0, 2.0), composition='cluster',
            forbids=NATURE, size_class='boulder (a Frostline granite boulder)', eastward='13 (the boulder, 0.35 x 0.42 A)',
            fn='boulder', note='A granite boulder of two or three facetted masses, a snow cap on its top plane, a west drift.')),
        ('frost_boulder_large', [('still', lambda: boulder('large'))], dict(
            name='Granite boulder cluster', purpose='mark', role='rock', cells=(5, 3), fp=B._fp(4, 2),
            collision={'shape': 'rect', 'rect': [-12.0, -9.0, 26, 9]}, shadow=(13.0, 3.0), composition='cluster',
            forbids=NATURE, size_class='boulder (a large block with two in its lee)', eastward='13 and 17 (the rocks)',
            fn='boulder', note='A big granite block with two smaller ones in its lee, snow on each top.')),
        ('frost_stone', [('still', lambda: boulder('small'))], dict(
            name='Granite stone', purpose='mark', role='rock', cells=(2, 1), fp=B._fp(1, 1),
            collision={'shape': 'rect', 'rect': [-3.0, -3.0, 6, 3]}, shadow=(3.0, 1.0), composition='cluster',
            forbids=NATURE, size_class='rock (a stone a cell across)', eastward='13', fn='boulder',
            note='A small granite stone with a snow cap, for a cluster\'s lee.')),
        ('frost_crag', [('a', lambda: crag('a')), ('b', lambda: crag('b'))], dict(
            name='Headwall crag', purpose='exclude', role='rock', cells=(7, 3), fp=B._fp(6, 2),
            collision={'shape': 'rect', 'rect': [-24.0, -14.0, 48, 14]}, shadow=None, composition='edge',
            forbids=NATURE, size_class='crag (a granite outcrop of the headwall\'s foot, the zone\'s frame)',
            eastward='12 (the cliff\'s stones)', fn='crag',
            note='Granite blocks stacked in a jagged mass with snow on every ledge: the north frame of the cirque.')),
        ('frost_cairn', [('standing', lambda: cairn('standing')), ('toppled', lambda: cairn('toppled')),
                         ('small', lambda: cairn('small'))], dict(
            name='Granite cairn', purpose='guide', role='marker', cells=(2, 2), fp=B._fp(2, 1),
            collision={'shape': 'rect', 'rect': [-5.0, -4.0, 10, 4]}, shadow=(5.0, 1.5), composition='edge',
            requires=[_rel('near', 'route', 2, 'a waymark beside the Col Path')], extra={'provides': ['feature']},
            forbids=NATURE, size_class='cairn (size-guide: 12 to 28 tall, 12 to 24 wide in world px)', eastward='13 (the boulder)',
            fn='cairn', note='A granite waymark with snow on each ring: standing, toppled east, or a small marker.')),
        ('frost_fire_ring', [('still', lambda: fire_ring())], dict(
            name='Cold fire ring under snow', purpose='mark', role='story', cells=(2, 2), fp=B._fp(2, 2),
            collision={'shape': 'rect', 'rect': [-5.0, -6.0, 10, 6]}, shadow=None, blocks=False, composition='free',
            forbids=NATURE, size_class='campfire (a cold fire ring of stones about a metre across)', eastward='05 and 37 (the camp fires)',
            fn='fire_ring', note='The fallen climbers\' camp: a ring of granite under snow, soot only where scraped.')),
        ('frost_sledge', [('still', lambda: sledge())], dict(
            name="Ice-cutter's sledge", purpose='work', role='story', cells=(5, 2), fp=B._fp(4, 1),
            collision={'shape': 'rect', 'rect': [-13.0, -6.0, 26, 6]}, shadow=(13.0, 2.0), composition='edge',
            requires=[_rel('near', 'water', 4, 'drawn up on the tarn\'s shore, by the ice-cut')], forbids=NATURE,
            size_class='pile (a low sledge under its load of ice blocks: the load is what stands)', eastward='04, 17',
            fn='sledge', note='Curled runners shod with iron, three blocks of lake ice lashed on, the bow saw leaning on it.')),
        ('frost_ice_stack', [('still', lambda: ice_stack())], dict(
            name='Cut ice blocks', purpose='store', role='story', cells=(3, 2), fp=B._fp(3, 1),
            collision={'shape': 'rect', 'rect': [-10.0, -5.0, 20, 5]}, shadow=(10.0, 2.0), composition='edge',
            requires=[_rel('near', 'water', 4, 'stacked on the shore by the ice-cut')], forbids=NATURE,
            size_class='pile (18 to 52 tall)', eastward='17 (stacked stores)', fn='ice_stack',
            note='Blocks of lake ice cut at the hole, stacked in two courses on the shore.')),
        ('frost_woodpile', [('still', lambda: woodpile())], dict(
            name="Warden's woodpile", purpose='store', role='store', cells=(3, 1), fp=B._fp(3, 1),
            collision={'shape': 'rect', 'rect': [-11.0, -4.0, 22, 4]}, shadow=(11.0, 2.0), composition='edge',
            requires=[NEAR_HUT], forbids=NATURE, size_class='woodpile', eastward='17 (stacked logs)', fn='woodpile',
            note='Split logs between two stakes, cut ends south, snow on top and at the west end.')),
        ('frost_hut_tools', [('still', lambda: hut_tools())], dict(
            name='Skis and shovel', purpose='work', role='story', cells=(2, 1), fp=B._fp(2, 1),
            collision={'shape': 'rect', 'rect': [-5.0, -3.0, 10, 3]}, shadow=(5.0, 1.5), composition='edge',
            requires=[NEAR_HUT], forbids=NATURE, size_class='tall_furniture (skis, a shovel and an axe stood in a rack against the wall, 0.9 A)', eastward='17', fn='hut_tools',
            note='A pair of skis, two poles and a snow shovel stuck in a heap of snow by the hut door.')),
        ('frost_bench', [('still', lambda: bench())], dict(
            name='Granite bench', purpose='rest', role='seat', cells=(3, 1), fp=B._fp(3, 1),
            collision={'shape': 'rect', 'rect': [-9.0, -3.0, 18, 3]}, shadow=(9.0, 1.5), composition='edge',
            requires=[_rel('near', 'route', 2, 'beside the Col Path, looking at the view')], forbids=NATURE,
            size_class='bench (37 to 68 tall, 70 to 107 wide)', eastward='12 and 38 (the bench)', fn='bench',
            note='A granite slab on two blocks, the snow brushed off half the seat.')),
        ('frost_noticeboard', [('still', lambda: noticeboard())], dict(
            name="Warden's noticeboard", purpose='guide', role='sign', cells=(3, 1), fp=B._fp(3, 1),
            collision={'shape': 'rect', 'rect': [-8.0, -2.0, 16, 2]}, shadow=(8.0, 1.5), composition='edge',
            requires=[_rel('near', 'route', 2, 'where the Col Path comes up')], forbids=NATURE,
            size_class='notice_board', eastward='04 (the noticeboards)', fn='noticeboard',
            note='Two posts, a board under a pent roof with snow on it, notices pinned.')),
        ('frost_snow_pole', [('still', lambda: snow_pole())], dict(
            name='Snow pole', purpose='guide', role='marker', cells=(1, 1), fp=B._fp(1, 1),
            collision={'shape': 'rect', 'rect': [-1.5, -1.5, 3, 2]}, shadow=(2.0, 1.0), composition='edge',
            requires=[_rel('near', 'route', 2, 'marking the Col Path where drifts cover it')], forbids=NATURE,
            size_class='pole (a snow pole marking the trod over the drifts)', eastward='04 (posts)', fn='snow_pole',
            note='A stake banded red and white to find the path under drifts.')),
        ('frost_lost_hat', [('still', lambda: lost_hat())], dict(
            name='Lost hat', purpose='mark', role='story', cells=(1, 1), fp=[], blocks=False,
            collision={'shape': 'none'}, shadow=None, composition='free', forbids=NATURE,
            size_class='unsized (a dropped hat on the snow: no clothing kind in the guide)', eastward='-', fn='lost_hat',
            note='The brief\'s "lost hat": a red bobble hat half drifted over by the path.')),
        ('frost_rockface', [(v, (lambda e=e, v=v: rockface(6, 101 + len(v), ends=e))) for v, e in [('plain', (False, False)), ('west', (True, False)), ('east', (False, True)), ('both', (True, True))]], dict(
            name='Granite face', purpose='exclude', role='rock', cells=(6, 5), fp=[[c, r] for c in range(-3, 3) for r in range(-4, 0)],
            collision={'shape': 'rect', 'rect': [-24.0, -32.0, 48, 32]}, shadow=None, composition='edge', forbids=NATURE,
            size_class='unsized (a 32 world px face, one Frostline tier: size guide "faces 32 in rock with snow lips")',
            eastward='12 (the cliff faces)', fn='rockface',
            note='A south granite face 32 world px high with a snow lip, jointed facets, drifts at its foot; side bands '
                 'where it jogs (west, east, both).')),
        ('frost_rockface_short', [(v, (lambda e=e, v=v: rockface(4, 211 + len(v), ends=e))) for v, e in [('plain', (False, False)), ('west', (True, False)), ('east', (False, True)), ('both', (True, True))]], dict(
            name='Granite face, short', purpose='exclude', role='rock', cells=(4, 5),
            fp=[[c, r] for c in range(-2, 2) for r in range(-4, 0)],
            collision={'shape': 'rect', 'rect': [-16.0, -32.0, 32, 32]}, shadow=None, composition='edge', forbids=NATURE,
            size_class='unsized (a 32 world px face)', eastward='12', fn='rockface', note='A four-cell length of the face.')),
        ('frost_icefall', [('still', lambda: rockface_fall())], dict(
            name='Frozen fall', purpose='exclude', role='rock', cells=(4, 5), fp=[[c, r] for c in range(-2, 2) for r in range(-4, 0)],
            collision={'shape': 'rect', 'rect': [-16.0, -32.0, 32, 32]}, shadow=None, composition='edge',
            size_class='unsized (a fall frozen over the face)', eastward='-', fn='rockface_fall',
            note='The tarn\'s outlet over the face, frozen into a curtain of icicles.')),
        ('frost_rock_stair', [('still', lambda: rock_stair())], dict(
            name='Granite stair', purpose='climb', role='rock_steps', cells=(5, 5), fp=[], blocks=False,
            collision={'shape': 'none'}, shadow=None, composition='axis', z_sort='ground',
            size_class='unsized (rough steps cut up the granite face: no stair kind in the guide; 40 world px wide, at least 34)', eastward='12 (the stairs)', fn='rock_stair',
            note='Six granite steps up the face with snow-dusted treads: the Col Path\'s way up the cirque\'s step.')),
        ('frost_footbridge', [('still', lambda: footbridge())], dict(
            name='Plank footbridge over the outlet', purpose='cross', role='bridge', cells=(5, 2), fp=[], blocks=False,
            collision={'shape': 'none'}, shadow=None, composition='axis', z_sort='ground', deck=[-20.0, -16.0, 40.0, 16.0],
            requires=[_rel('on', 'water', None, 'spans the tarn\'s outlet, three cells wide, west to east')],
            size_class='unsized (a plank footbridge five cells long)', eastward='12 (the plank bridge)', fn='footbridge',
            note='Planks across the way, snow in their joints and on the log rails, granite abutments.')),
    ]


def build(write=True, force=False, only=None):
    out = {}
    pieces = []
    for pid, vs, kw in prop_jobs():
        if only and pid not in only:
            continue
        pics = []
        for vid, thunk in vs:
            r = thunk()
            frames = None
            if isinstance(r, tuple):
                r, frames = r
            png = '%s_%s.png' % (pid, vid) if len(vs) > 1 or vid != 'still' else pid + '.png'
            pics.append((vid, r, frames, png))
            out[os.path.join(ART, png)] = to_rgba(r.a)
            if frames:
                out[os.path.join(ART, png[:-4] + '_loop.png')] = to_rgba(K.strip(frames['frames']))
        kw = dict(kw)
        name, purpose, role = kw.pop('name'), kw.pop('purpose'), kw.pop('role')
        cells, fp = kw.pop('cells'), kw.pop('fp')
        variants = []
        for vid, r, frames, png in pics:
            variants.append((vid, 1.0 if not variants else 0.6, png, (r.ax, r.ay)))
            if frames:
                f0 = frames['frames'][0]
                kw['anim'] = {'clip': frames['clip'], 'loop': True, 'frames': len(frames['frames']), 'fps': frames['fps'],
                              'strip': RES + png[:-4] + '_loop.png', 'frame_px': [f0.W, f0.H], 'reduced_motion': 'hold:0',
                              'on_screen_only': True, 'region_px': list(frames['region'])}
        size = (max(r.W for _v, r, _f, _p in pics), max(r.H for _v, r, _f, _p in pics))
        pieces.append(_piece(pid, name, variants, size, cells, purpose, role, fp=fp, **kw))
    if write:
        os.makedirs(ART, exist_ok=True)
        for p in os.listdir(ART):
            if p.endswith('.png') and os.path.join(ART, p) not in out:
                os.remove(os.path.join(ART, p))
        for p, a in out.items():
            Image.fromarray(a, 'RGBA').save(p, optimize=True)
        for pc in pieces:
            path = os.path.join(PIECES, 'prop', pc['id'] + '.json')
            if force or not os.path.exists(path):
                with open(path, 'w') as f:
                    json.dump(pc, f, indent=1)
                    f.write('\n')
    return out


def check() -> int:
    bad = []
    for p, a in build(write=False).items():
        if not os.path.exists(p) or not np.array_equal(np.asarray(Image.open(p).convert('RGBA')), a):
            bad.append(os.path.relpath(p, ROOT))
    if bad:
        print('frost: stale pictures %s (run python3 -m scripts.art.kit.sets.frost)' % ', '.join(bad[:6]))
        return 1
    print('frost: pictures current')
    return 0


AUDIT = {pid: (kw['purpose'], kw['role'], None, None, 'fine', 'Frostline set (scripts/art/kit/sets/frost.py): ' + kw['note'])
         for pid, _vs, kw in prop_jobs()}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--force', action='store_true')
    a = ap.parse_args(argv)
    if a.check:
        return check()
    n = write_terrain(force=a.force)
    print('frost: %d pictures, %d ground pieces written' % (len(build(force=a.force)), n))
    return 0


if __name__ == '__main__':
    sys.exit(main())
