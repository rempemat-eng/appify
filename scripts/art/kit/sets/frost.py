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


# granite's grain (round 3, R2-R1 and R2-F1): clusters of three or four texels that swap to a sibling
# ramp at the same value (feldspar, quartz, hornblende: shape without value noise, house-style 4),
# a few stepping a tone up on lit planes or down in shade
GR_SIB = {'slate': (('slate_warm', 0), ('slate_cool', 0), ('stone_cool', 0)),
          'slate_cool': (('slate', 0), ('iron', 1), ('slate_warm', 0)),
          'slate_warm': (('slate', 0), ('stone_cool', 0), ('ashlar', -1)),
          'iron': (('slate_cool', -1), ('soot', 1), ('slate', -1)),
          'stone_cool': (('slate_warm', 0), ('stone', 0), ('slate', 0)),
          'stone': (('stone_cool', 0), ('stone_warm', 0), ('ashlar', 0)),
          'stone_warm': (('stone', 0), ('ashlar', 0)),
          'ash': (('stone_cool', 0), ('slate_warm', 0), ('ashlar', 0)),
          'soot': (('iron', -1), ('ash', -1))}
SNOWS = {FI['snow'], FI['snow_warm'], FI['snow_cool']}


def _grain(a, m, seed, swap=0.45, step=0.10, lit=None, drop_p=0.4):
    """Granite's grain on the texels `m` (see GR_SIB): 2 x 2 cells staggered row pair to row pair,
    texels of a cell left at random (blobs of two to four, never one); `lit` (a mask) takes the steps
    up. Laid after the despeckle, so the two-texel grains stay."""
    H, W = a.shape
    Y, X = np.mgrid[0:H, 0:W]
    cx, cy = (X + (Y // 2) % 2) // 2, Y // 2
    drop = K.vhash(X, Y, seed + 1) < drop_p
    cell = (cy * 4099 + cx)
    keep = ~drop & m
    n_in = ndi.sum(keep, cell, index=None) if False else None
    flat = cell.ravel()
    cnt = np.bincount(flat - flat.min(), weights=keep.ravel().astype(float))
    lone = (cnt[flat - flat.min()] < 2).reshape(H, W)
    drop = drop | lone
    h = K.vhash(cx, cy, seed)
    pick = K.vhash(cx, cy, seed + 2)
    fam, t = a // 8, a % 8
    cl = m & (h < swap) & ~drop & (a >= 0)
    for f, sibs in GR_SIB.items():
        sel = cl & (fam == FI[f])
        k = np.minimum((pick * len(sibs)).astype(int), len(sibs) - 1)
        for j, (g, dt) in enumerate(sibs):
            s2 = sel & (k == j)
            a[s2] = FI[g] * 8 + np.clip(t[s2] + dt, 0, 5)
    st = m & (a >= 0) & (h > 1 - step) & ~drop
    if lit is None:
        lit = np.zeros_like(m)
    up, dn = st & lit, st & ~lit
    a[up] = (a[up] // 8) * 8 + np.clip(a[up] % 8 + 1, 0, 5)
    a[dn] = (a[dn] // 8) * 8 + np.clip(a[dn] % 8 - 1, 0, 5)


def _snow_light(sc, a, tags=('snow', 'drift'), swell=0.16):
    """Snow shaded by its own planes: the lit top and west (snow 5), the body (snow 4), the turn
    (snow_cool 4), the cool east and front fall (snow_cool 3), the underside where it overhangs
    (snow_cool 2), with wind-laid swells in clusters across the planes; under every snow mass that
    overhangs stone a blue shade row on the stone (the lip's shadow)."""
    ids = [i for i, s_ in enumerate(sc.solids) if s_.tag in tags]
    m = np.isin(sc.label, ids)
    if not m.any():
        return m
    L = sc.light()
    H, W = a.shape
    Y, X = np.mgrid[0:H, 0:W]
    sw = K.vhash((X + Y // 3) // 3, Y // 2, 77) * swell
    v = L + sw
    code = np.where(v > 0.86, C('snow', 5), np.where(v > 0.7, C('snow', 4), np.where(v > 0.48, C('snow_cool', 4),
                    np.where(v > 0.1, C('snow_cool', 3), C('snow_cool', 2)))))
    a[m] = code[m]
    below = np.zeros_like(m)
    below[1:] = m[:-1]
    under = below & ~m & (a >= 0) & ~np.isin(a // 8, list(SNOWS))
    a[under] = C('sky_cool', 2)
    return m


def _fractures(a, m, seed, n=2, lit_side=True):
    """Fracture lines across granite: a dark run 1 texel wide bending down and across the stone,
    a lit texel on its upper west lip; the stone east of a fracture a tone down (a plane turned
    from the light)."""
    rng = np.random.default_rng(seed)
    ys, xs = np.nonzero(m)
    if not len(ys):
        return
    H, W = a.shape
    for _ in range(n):
        k = int(rng.integers(0, len(ys)))
        y, x = float(ys[k]), float(xs[k])
        dx = rng.choice((-0.8, -0.4, 0.4, 0.8))
        path = []
        for _j in range(int(rng.integers(6, 16))):
            yi, xi = int(round(y)), int(round(x))
            if not (0 <= yi < H and 0 <= xi < W) or not m[yi, xi]:
                break
            path.append((yi, xi))
            y += 1.0
            x += dx + rng.uniform(-0.4, 0.4)
        for yi, xi in path:
            a[yi, xi] = C('slate_cool', 0)
            if lit_side and xi - 1 >= 0 and m[yi, xi - 1]:
                a[yi, xi - 1] = (a[yi, xi - 1] // 8) * 8 + min(5, a[yi, xi - 1] % 8 + 1)
            for d in (1, 2):
                if xi + d < W and m[yi, xi + d] and a[yi, xi + d] >= 0 and a[yi, xi + d] // 8 not in SNOWS:
                    a[yi, xi + d] = (a[yi, xi + d] // 8) * 8 + max(1, a[yi, xi + d] % 8 - 1)


def _granite_dress(sc, a, seed, tags=('rock',), n_frac=2, swap=0.45):
    """The granite's surface after shading: grain, fractures, the snow's own planes and the shade
    under each lip."""
    m = np.isin(sc.label, [i for i, s_ in enumerate(sc.solids) if s_.tag in tags])
    _fractures(a, m & ~(sc.n[..., 2] > 0.8), seed + 5, n=n_frac)
    _snow_light(sc, a)


def _grain_after(sc, a, seed, tags=('rock',), swap=0.6, step=0.08, crust=0.3):
    """The grain laid on a finished picture (after the despeckle and the outline): only on the
    stone's own texels, not its outline."""
    m = np.isin(sc.label, [i for i, s_ in enumerate(sc.solids) if s_.tag in tags]) & (a >= 0) & (a % 8 >= 1)
    m &= ~np.isin(a // 8, list(SNOWS)) & (a != C('sky_cool', 2))
    _grain(a, m, seed, swap=swap, step=step, lit=sc.light() > 0.45)
    if crust:
        _crust(sc, a, seed, rate=crust)


SNOW_LADDER = [C('snow_cool', 2), C('snow_cool', 3), C('snow_cool', 4), C('snow', 4), C('snow', 5)]


def _crust(sc, a, seed, tags=('snow', 'drift'), rate=0.3):
    """The snow's wind crust: short runs of two to four texels along the wind (west to east), each a
    step down the ladder on the lit planes and a step up in the cool ones; none on the outline."""
    m = np.isin(sc.label, [i for i, s_ in enumerate(sc.solids) if s_.tag in tags]) & np.isin(a, SNOW_LADDER)
    m &= ndi.binary_erosion(a >= 0)
    H, W = a.shape
    Y, X = np.mgrid[0:H, 0:W]
    off = (K.vhash(Y, Y // 2, seed + 9) * 4).astype(int)
    run = (X + off) // 3
    h = K.vhash(run, Y, seed + 4)
    tip = K.vhash(X, Y, seed + 6) < 0.25
    sel = m & (h < rate) & ~tip
    idx = {c: i for i, c in enumerate(SNOW_LADDER)}
    for c, i in idx.items():
        s2 = sel & (a == c)
        j = i - 1 if i >= 3 else i + 1
        a[s2] = SNOW_LADDER[max(0, min(4, j))]


def _block(sc, cx, cy, w, d, h, seed, base=2.8, z0=0.0, tilt=0.0):
    """One granite block: a rounded box (flat top, front, rounded arrises) with a lower shoulder
    knocked off one corner and a chamfer, so it reads as a weathered block, not a ball."""
    rng = np.random.default_rng(seed)
    mix = rng.random()
    r = min(w, d, h) * rng.uniform(0.28, 0.4)
    sc.box(cx - w / 2, cy - d / 2, z0, cx + w / 2, cy + d / 2, z0 + h, GRANITE, base=base, k=1.9, tag='rock', round_=r,
           mix=mix, tex='stone')
    # a shoulder: a lower step on the east or west of the block (a fracture plane), set forward
    side = 1 if rng.random() < 0.6 else -1
    sw = w * rng.uniform(0.3, 0.45)
    sh = h * rng.uniform(0.45, 0.7) + tilt
    x0 = cx + side * (w / 2 - sw * 0.6) - sw / 2
    sc.box(x0, cy - d / 2 + 1.5, z0, x0 + sw, cy + d / 2 + rng.uniform(0.5, 2.0), z0 + sh, GRANITE, base=base - 0.3, k=1.9,
           tag='rock', round_=min(sw, sh) * 0.35, mix=(mix + 0.37) % 1.0, tex='stone')


def _cap(sc, cx, cy, ztop, w, d, seed, th=4.0, over=1.5):
    """Snow with thickness on a block's top: a slab a little smaller than the top, heaped west of
    centre, its front hanging `over` texels past the block's front (a lip with shade under it)."""
    rng = np.random.default_rng(seed)
    sc.ellipsoid(cx - w * 0.08, cy - d * 0.1 + over * 0.5, ztop + th * 0.35, w * 0.5, d * 0.5 + over * 0.5, th, SNOW,
                 base=3.9, k=1.1, tag='snow', flat=2.2)
    if w > 14:
        sc.ellipsoid(cx - w * 0.25, cy - d * 0.15, ztop + th * 0.6, w * 0.3, d * 0.35, th * 0.9, SNOW, base=3.9, k=1.1,
                     tag='snow', flat=1.6, mix=rng.random())


def _mass(sc, cx, cy, rx, ry, rz, seed, base=3.2, flat=2.3):
    """A weathered granite mass: a superellipsoid seated on the ground (flat faces, rounded arrises)."""
    sc.ellipsoid(cx, cy, rz * 0.92, rx, ry, rz, GRANITE, base=base, k=1.9, tag='rock', mix=hsh(seed, 17), flat=flat,
                 tex='stone')


def _rock(sc, cx, cy, w, d, h, seed, cap=True, drift=True):
    """A granite boulder (round 3, R2-R1): a main mass of jointed granite with a lower mass split
    from it on the east and a chip on the west, so its outline breaks in planes; a snow cap with
    thickness on the top plane (heaped west, lumped, hanging a little over the front), a drift
    banked at the west foot."""
    rng = np.random.default_rng(seed)
    rx, ry, rz = w / 2, d / 2, h / 2
    _mass(sc, cx, cy, rx, ry, rz, seed, flat=2.4 + rng.uniform(0, 0.5))
    if w > 12:
        _mass(sc, cx + rx * 0.62, cy + ry * 0.35, rx * 0.55, ry * 0.65, rz * rng.uniform(0.5, 0.65), seed + 3, base=2.5,
              flat=2.2)
        _mass(sc, cx - rx * 0.7, cy + ry * 0.45, rx * 0.35, ry * 0.45, rz * 0.4, seed + 5, base=2.7, flat=2.0)
    if cap:
        th = max(2.4, min(4.5, h * 0.2))
        top = rz * 0.92 + rz - th * 0.45
        sc.ellipsoid(cx - rx * 0.12, cy - ry * 0.05, top, rx * 0.74, ry * 0.7, th, SNOW, base=3.9, k=1.1, tag='snow',
                     flat=1.7)
        sc.ellipsoid(cx - rx * 0.38, cy - ry * 0.2, top + th * 0.5, rx * 0.36, ry * 0.4, th * 0.85, SNOW, base=3.9, k=1.1,
                     tag='snow', flat=1.4)
        if w > 12:
            sc.ellipsoid(cx + rx * 0.62, cy + ry * 0.3, rz * 0.92 * 0.6 + rz * 0.6 * 0.95, rx * 0.36, ry * 0.4, th * 0.7, SNOW,
                         base=3.9, k=1.1, tag='snow', flat=1.5)
    if drift:
        r = max(4.0, w * 0.3)
        sc.ellipsoid(cx - rx * 0.85, cy + ry * 0.4, 0.2, r, r * 0.6, r * 0.6, SNOW, base=3.8, k=1.0, tag='drift', flat=1.0)


def _chip(sc, a, seed, tags=('rock',)):
    """Knock the arrises: notches of two and three texels taken out of the stone's outline (its
    silhouette breaks in planes, not in an ellipse)."""
    m = np.isin(sc.label, [i for i, s_ in enumerate(sc.solids) if s_.tag in tags])
    edge = m & ~ndi.binary_erosion(m)
    H, W = a.shape
    Y, X = np.mgrid[0:H, 0:W]
    out = edge & (K.vhash(X // 3, Y // 2, seed) > 0.72) & (Y < np.nonzero(m.any(1))[0].max() - 2 if m.any() else True)
    a[out] = -1
    sc.label[out] = -1


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


def _rock_r2(sc, cx, cy, rx, ry, rz, seed, cap=True, drift=True):
    """Round 2's rounded boulder, kept for the small stone (it passed the r2 audit)."""
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
        _rock(sc, 0, -6, 30, 20, 20, seed)
    elif kind == 'b':
        _rock(sc, -2, -6, 26, 18, 26, seed + 1)
    elif kind == 'large':
        _rock(sc, -10, -12, 36, 26, 38, seed + 2)
        _rock(sc, 12, -16, 26, 20, 28, seed + 6, drift=False)
        _rock(sc, 26, 4, 20, 14, 16, seed + 3, drift=False)
        _rock(sc, 36, -10, 14, 10, 12, seed + 4, drift=False)
    else:
        _rock_r2(sc, 0, -4, 8, 5, 6, seed + 5)
    if kind == 'small':
        a = _solo(sc, dress=lambda s, a: _cracks(s, a, n=2, seed=seed))
    else:
        a = _solo(sc, dress=lambda s, a: (_chip(s, a, seed), _granite_dress(s, a, seed, n_frac=6 if kind == 'large' else 3)))
        _grain_after(sc, a, seed)
    return K.crop(a, sc.ox, sc.oy)

def crag(kind='a', seed=61):
    """A crag of the headwall's foot (round 3, R2-R1): overlapping granite blocks of different sizes,
    the big ones behind and the small ones stepping down in front, staggered in depth and height
    (none a tower, no pile of equal balls), snow with thickness on every top and ledge, drifts at the
    west foot. The zone's north frame (B8, Z1)."""
    rng = np.random.default_rng(seed + (0 if kind == 'a' else 9))
    sc = K.Scene(-110, 110, -60, 24, 160)
    if kind == 'a':
        spec = [(-34, -36, 54, 30, 44), (12, -40, 62, 32, 52), (54, -28, 40, 26, 34), (-62, -16, 36, 22, 24),
                (-20, -8, 40, 22, 26), (24, -8, 34, 20, 20), (60, -2, 26, 16, 14), (-2, 8, 22, 12, 10)]
    else:
        spec = [(-28, -38, 60, 32, 58), (28, -34, 52, 28, 46), (-64, -20, 34, 22, 26), (60, -16, 36, 22, 24),
                (-4, -12, 42, 22, 24), (32, 2, 26, 14, 12), (-42, 4, 24, 14, 11)]
    for k, (x, y, w, d, h) in enumerate(spec):
        _rock(sc, x + rng.uniform(-3, 3), y, w * rng.uniform(0.9, 1.1), d, h * rng.uniform(0.9, 1.1), seed + 13 * k,
              drift=False)
    for k in (3, len(spec) - 1) if kind == 'a' else (2, len(spec) - 1):
        x, y, w, d, h = spec[k]
        r = 6 + w * 0.2
        sc.ellipsoid(x - w * 0.42, y + d * 0.3, 0.2, r, r * 0.6, r * 0.55, SNOW, base=3.8, k=1.0, tag='drift', flat=1.0)
    a = _solo(sc, dress=lambda s, a: (_chip(s, a, seed), _granite_dress(s, a, seed, n_frac=10)))
    _grain_after(sc, a, seed)
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
        _snowcap(sc, -1.0, -0.8, z + size * sq * 1.45, r * 0.8 + 1.5, r * 0.62 + 1.2, th=2.2 if kind != 'toppled' else 3.4,
                 seed=int(z * 7) + seed)
    if kind != 'toppled':
        top = rings[-1][2] + rings[-1][3] * rings[-1][4] * 1.5
        sc.ellipsoid(0.5, -0.5, top + 7.5, 3.0, 2.5, 8.5, GRANITE, base=3.0, k=1.9, tag='rock', mix=0.4, flat=1.7)
        _snowcap(sc, 0.0, -0.5, top + 15.2, 2.8, 2.3, th=2.0, seed=seed + 2)
    else:
        # (round 3, R2-R2) the fallen upright: a long granite stone lying east, its top plane lit
        # with a ledge of snow along it, its dark east end, its foot half buried in a drift
        sc.ellipsoid(25, -2, 4.2, 11.5, 4.2, 4.4, GRANITE, base=3.0, k=1.9, tag='rock', mix=0.4, flat=2.3, tex='stone')
        sc.ellipsoid(23.0, -3.0, 8.3, 8.5, 3.2, 2.6, SNOW, base=3.9, k=1.1, tag='snow', flat=1.6)
        sc.ellipsoid(33, 2.5, 0.2, 7.5, 4.5, 4.2, SNOW, base=3.8, k=1.0, tag='drift', flat=1.2)
    _drift_west(sc, -rings[0][0] - 2, 3, 6.0 if kind != 'small' else 4.0, seed)
    del rng
    if kind == 'toppled':
        a = _solo(sc, dress=lambda s, a: _granite_dress(s, a, seed, n_frac=3))
        _grain_after(sc, a, seed)
        return K.crop(a, sc.ox, sc.oy)
    a = _solo(sc)
    return K.crop(a, sc.ox, sc.oy)


def fire_ring(seed=67):
    """The fallen climbers' camp's hearth, cold (round 3, R2-P6): a ring of granite stones, each a
    block with a lit top and its grey east side showing under a small cap of snow; inside, a hollow
    scraped clear to soot-dark ash with charred brands and charcoal; snow banked round the outside.
    No green (Z6)."""
    sc = K.Scene(-30, 30, -24, 16, 40)
    rng = np.random.default_rng(seed)
    # the snow banked round the outside of the ring (low, against the stones), deeper on the west
    sc.ellipsoid(-1.5, 0.5, 0.1, 17.5, 12.0, 2.2, SNOW, base=3.8, k=1.0, tag='drift', flat=2.4)
    # the hearth: ash and soot in the scraped hollow
    sc.ellipsoid(0.5, 0.5, 1.0, 8.0, 5.4, 1.6, [('soot', 'soot', 'ash')], base=1.6, k=0.8, tag='soot', flat=1.6)
    sc.ellipsoid(-1.5, -0.5, 1.5, 4.2, 2.8, 1.4, [('soot', 'ash', 'ash')], base=2.6, k=0.8, tag='ash', flat=1.4)
    for (x0, y0, x1, y1) in ((-4, 1, 3, 2.6), (0, -2.5, 5.5, -1.2), (2, 2.4, 6, 3.6)):
        sc.box(x0, y0, 1.6, x1, y1, 3.4, [('soot', 'timber_cool', 'timber')], base=1.3, k=1.2, tag='brand', round_=0.8)
    for k in range(8):
        ang = 2 * math.pi * k / 8 + rng.uniform(-0.15, 0.15)
        x, y = 10.5 * math.cos(ang), 7.2 * math.sin(ang)
        sz = rng.uniform(3.8, 4.6)
        sc.ellipsoid(x, y, sz * 0.62, sz * 1.1, sz * 0.8, sz * 0.66, GRANITE, base=3.0, k=1.4, tag='rock', mix=rng.random(),
                     flat=2.3)
        if math.sin(ang) < -0.3:                          # the far and side stones hold snow; the near ones less
            sc.ellipsoid(x - sz * 0.25, y - sz * 0.15, sz * 1.25, sz * 0.62, sz * 0.45, sz * 0.32, SNOW, base=3.9, k=1.1,
                         tag='snow', flat=1.6)

    def dress(s_, a):
        _snow_light(s_, a, swell=0.0)
        lab = s_.label
        m = np.isin(lab, [i for i, q in enumerate(s_.solids) if q.tag == 'soot'])
        H, W = a.shape
        Y, X = np.mgrid[0:H, 0:W]
        coal = m & (K.vhash(X // 3, Y // 2, seed + 3) > 2.0)
        a[coal] = np.where(K.vhash(X, Y, seed + 4)[coal] > 0.5, C('soot', 0), C('ash', 2))
        ember = m & (K.vhash(X // 2, Y // 2, seed + 5) > 2.0)
        a[ember] = C('timber_cool', 1)
    a = _solo(sc, dress=dress)
    _grain_after(sc, a, seed, swap=0.3, step=0.0, crust=0)
    return K.crop(a, sc.ox, sc.oy)


# ------------------------------------------------------------------------------------------------
# the Col hut (B5: door 87, eaves 123 art px; F-H1, F-H2)
# ------------------------------------------------------------------------------------------------
def _plume_frame(i, n, W, H, seed):
    """One frame of the stove's smoke (round 3, R2-H2): a soft plume rising from the pot's mouth
    (the frame's bottom row, column 6), thickening as it leans east, then breaking into two or three
    puffs that rise with the loop's phase, swell, thin and fade; each part lit on its upper west,
    a cool grey body and a darker east side, no outline (smoke has none)."""
    a = np.full((H, W), -1, np.int32)
    Y, X = np.mgrid[0:H, 0:W] + 0.5
    ph = i / float(n)
    blobs = []                                   # (cx, cy, r, fade 0..1)
    for k in range(28):                           # the connected column, the lower 45 %
        t = 0.45 * k / 27.0
        blobs.append((6 + 11 * t ** 1.3 + 0.9 * math.sin(2 * math.pi * (t * 2.2 - ph)), H - 1.5 - t * (H - 4), 2.2 + 11.0 * t, 0.0))
    for k in range(3):                            # the puffs above it, travelling up with the phase
        t = 0.45 + 0.55 * ((ph + k / 3.0) % 1.0)
        r = (2.2 + 11.0 * t) * (1.0 - 0.55 * max(0.0, t - 0.7) / 0.3) * (0.9 + 0.2 * hsh(seed, k))
        if t < 0.52:
            r *= (t - 0.45) / 0.07 * 0.6 + 0.4
        blobs.append((6 + 11 * t ** 1.3 + 0.9 * math.sin(2 * math.pi * (t * 2.2 - ph)) + 1.5 * (hsh(seed, k, 2) - 0.5),
                      H - 1.5 - t * (H - 4), max(1.2, r), max(0.0, (t - 0.7) / 0.3)))
    best = np.full((H, W), 9.0)
    lx = np.zeros((H, W))
    ly = np.zeros((H, W))
    fade = np.zeros((H, W))
    for (cx, cy, r, f) in blobs:
        d = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2) / r
        win = d < best
        best = np.where(win, d, best)
        lx = np.where(win, (X - cx) / r, lx)
        ly = np.where(win, (Y - cy) / r, ly)
        fade = np.where(win, f, fade)
    body = (best <= 1.0) & (Y < H - 0.5)
    lit = lx * -0.7 + ly * -0.7                  # toward the upper west
    t_ = np.where(lit > 0.45, 3, np.where(lit > -0.1, 2, np.where(lit > -0.55, 1, 0)))
    t_ = np.minimum(3, t_ + np.round(fade * 1.5).astype(int))
    pal = np.array([C('slate', 4), C('snow_cool', 2), C('snow_cool', 3), C('snow_cool', 4)])
    a[body] = pal[t_][body]
    # the thinning tops of the high puffs break into tufts (no lone texels)
    thin = body & (fade > 0.35) & (K.vhash(np.floor(X).astype(int) // 2, np.floor(Y).astype(int) // 2, seed + i) < 0.3 * fade)
    a[thin] = -1
    K.despeckle(a, size=2)
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
    orig = a.copy()
    ladder = [C('sky_cool', 4), C('sky_cool', 5), C('snow_cool', 2), C('snow', 2), C('snow_cool', 3), C('snow', 3),
              C('snow_cool', 4), C('snow', 4), C('snow_warm', 4), C('snow', 5)]
    NL = len(ladder)
    # (round 3, R2-H1) the cornice's lower edge: a slow lumpy line hanging 2 to 3 texels over the eave
    prof = ndi.gaussian_filter1d(rng.random(W), 4.0, mode='nearest')
    prof = (prof - prof.mean()) / (prof.std() + 1e-9)
    hang = np.clip(np.round(2.4 + 0.8 * prof), 2, 4).astype(int)
    low = (y_e + hang)[None, :]
    span = (Xg >= L - 3) & (Xg <= R + 3)
    # the ridge: snow heaped over it in soft mounds (1 to 4 texels), its top edge irregular
    rp = ndi.gaussian_filter1d(rng.random(W), 3.0, mode='nearest')
    rp = (rp - rp.min()) / max(1e-6, rp.max() - rp.min())
    heap = np.round(1 + 4 * rp).astype(int)
    heap[np.abs(np.arange(W) - (L - 3)) < 3] -= 1
    heap[np.abs(np.arange(W) - (R + 3)) < 3] -= 1
    mass = span & (Yg >= (top - heap)[None, :]) & (Yg <= low)
    mass &= ~chim
    cx0, cx1 = np.nonzero(chim_cols)[0].min(), np.nonzero(chim_cols)[0].max()
    ccx = (cx0 + cx1) / 2.0
    stack_foot = int(np.nonzero(stack.any(1))[0].max())
    # the planes: the lit crest and upper plane (the slope toward the ridge faces the sky), cooling
    # down the slope and to the east, broad wind-laid swells; the slates' courses showing through
    # the thinner snow as faint cool steps
    lv = (Yg - top) / max(1, (y_e - top))
    east = (Xg - L) / max(1, R - L)
    sw_ = ndi.gaussian_filter(rng.random((H, W)), (1.4, 6.0))
    sw_ = (sw_ - sw_.mean()) / (sw_.std() + 1e-9)
    # the snow has crept on the slates into pillows (four to six across the roof), each rounded:
    # lit on its upper west, turning cool to its east crease and down its front
    edges_x = [L - 3]
    while edges_x[-1] < R - 26:
        edges_x.append(edges_x[-1] + int(rng.integers(30, 58)))
    edges_x[-1] = R + 4
    pu = np.zeros((H, W))
    pv = np.zeros((H, W))
    for j in range(len(edges_x) - 1):
        x0_, x1_ = edges_x[j], edges_x[j + 1]
        wob = 2.0 * np.sin((Yg - top) / 7.0 + j * 1.7) + (Yg - top) * 0.15
        inside = (Xg >= x0_ + wob) & (Xg < x1_ + wob)
        pu = np.where(inside, (Xg - x0_ - wob) / max(1.0, x1_ - x0_), pu)
    du = pu - 0.3
    # a pillow's crease fades toward the ridge (the snow is one mass there) and deepens down the slope
    v = (8.6 - 5.0 * np.clip(du, 0, None) ** 1.5 * (0.4 + lv) - 2.0 * np.clip(-du, 0, None) * lv - 2.8 * lv - 0.8 * east
         + 0.7 * np.clip(sw_, -1.4, 1.4))
    v = np.where((pu > 0.94) & (lv > 0.35) & (lv < 0.97), v - 2.6 * lv, v)
    # the slates' courses under the thinner snow of the lower slope: each a lit step over a cool row,
    # broken where the wind has laid the snow deeper
    seg = K.vhash((Xg + 3 * ((Yg - top) // 5)) // 7, (Yg - top) // 5, seed + 13) > 0.3
    thin = (sw_ < 0.7) & (lv > 0.3) & seg
    v = np.where(thin & ((Yg - top) % 5 == 4), v - 2.2, v)
    v = np.where(thin & ((Yg - top) % 5 == 3), v + 1.0, v)
    # the chimney's lee: a scoop east of the stack, cool, with a lit rim on its far (east) side
    dl = ((Xg - cx1 - 7) / 8.0) ** 2 + ((Yg - stack_foot + 2) / 6.0) ** 2
    v = np.where(dl < 1.0, v - 3.5 * (1 - dl), v)
    rim = (dl >= 1.0) & (dl < 1.6) & (Xg > cx1 + 7)
    v = np.where(rim, v + 1.8, v)
    idx = np.clip(np.round(v), 0, NL - 1).astype(int)
    codes = np.array(ladder)[idx]
    a[mass] = codes[mass]
    # the stove's warmth: a melt west of and under the stack, the wet slates showing, an edge of
    # slush; and a wind-scoured patch high on the east where the slates break through
    mn = ndi.gaussian_filter(rng.random((H, W)), 2.0)
    mn = (mn - mn.mean()) / (mn.std() + 1e-9)
    dm = ((Xg - ccx) / ((cx1 - cx0) / 2.0 + 6.0)) ** 2 + ((Yg - stack_foot - 1) / 4.0) ** 2 + 0.2 * mn
    melt = mass & (dm < 1.0) & (Yg > top + 3) & (Yg < y_e - 4)
    sc_ = ndi.gaussian_filter(rng.random((H, W)), (2.0, 5.0))
    sc_ = (sc_ - sc_.mean()) / (sc_.std() + 1e-9)
    # the slates' lower edges breaking through the thin snow near the eave, in short dark runs
    run_h = K.vhash((Xg + 5 * ((Yg - top) // 5)) // 4, (Yg - top) // 5, seed + 19)
    slat = np.isin(orig // 8, [FI['slate'], FI['slate_cool'], FI['slate_warm'], FI['iron']]) & (orig >= 0)
    edges_s = mass & thin & ((Yg - top) % 5 == 4) & (lv > 0.45) & (run_h > 0.55) & (sw_ < -0.15) & (Yg < y_e - 3) & \
        (pu < 0.85) & slat
    bare = melt | edges_s
    wet = orig[bare]
    a[bare] = np.where(wet >= 0, (wet // 8) * 8 + np.maximum(1, wet % 8 - 1), C('slate', 2))
    slush = ndi.binary_dilation(bare, iterations=1) & mass & ~bare
    a[slush] = np.where((Yg[slush] % 2) == 0, C('snow_cool', 3), C('sky_cool', 4))
    lit_edge = slush & ~np.roll(bare, -1, 0) & np.roll(bare, 1, 0)
    a[lit_edge] = C('sky_cool', 3)
    # the crust: short runs along the wind, a step down on the lit planes and up in the cool
    Hh = np.arange(H)[:, None]
    off = (K.vhash(Hh, Hh // 2, seed + 9) * 4).astype(int)
    run = (Xg + off) // 3
    hc = K.vhash(run, Yg, seed + 4)
    tip = K.vhash(Xg, Yg, seed + 6) < 0.25
    crust = mass & ~bare & ~slush & (hc < 0.3) & ~tip & np.isin(a, ladder)
    for i_, c_ in enumerate(ladder):
        s2 = crust & (a == c_)
        a[s2] = ladder[max(0, min(NL - 1, i_ - 2 if i_ >= 5 else i_ + 2))]
    # the ridge's lit crest along the snow's top and a cool row behind the heaps
    crest = mass & ~np.roll(mass, 1, 0)
    a[crest] = C('snow', 5)
    below_c = np.roll(crest, 1, 0) & mass & ~bare
    a[below_c & (K.vhash(Xg // 2, 0, seed) > 0.5)] = C('snow', 5)
    # the cornice: its last four rows: the lit lip, the cool front, the darker turn, the underside
    edge = mass & ~np.roll(mass, -1, 0)
    for k_, code in ((0, C('snow_cool', 2)), (1, C('snow_cool', 3)), (2, C('snow_cool', 4)), (3, C('snow', 5))):
        sel = np.roll(edge, -k_, 0) & mass & ~bare
        a[sel] = code
    under = np.roll(edge, 1, 0) & ~mass & (a >= 0)
    a[under] = C('sky_cool', 2)
    under2 = np.roll(edge, 2, 0) & ~mass & (a >= 0) & (K.vhash(Xg // 3, 1, seed) > 0.4)
    a[under2] = (a[under2] // 8) * 8 + np.maximum(0, a[under2] % 8 - 1)
    # the verges: the snow's end thickness, three texels down each gable: lit on the west end, in
    # shade on the east
    for xv, codes_v in ((L - 3, (C('snow', 5), C('snow', 4))), (L - 2, (C('snow', 4), C('snow_cool', 4))),
                        (R + 2, (C('snow_cool', 3), C('snow_cool', 2))), (R + 3, (C('snow_cool', 2), C('snow_cool', 2)))):
        ys_ = np.nonzero(mass[:, xv])[0]
        if len(ys_):
            for y in range(ys_.min() + 1, ys_.max() - 3):
                a[y, xv] = codes_v[0] if (y - ys_.min()) % 6 < 4 else codes_v[1]
    # the chimney: snow seated on the stack's cap either side of the pot, and a rim of it on the pot
    capm = stack & (Yg <= np.nonzero(stack.any(1))[0].min() + 3)
    ctop = int(np.nonzero(capm.any(1))[0].min()) if capm.any() else top
    potm = (orig >= 0) & np.isin(orig // 8, [FI['clay'], FI['clay_cool'], FI['crag'], FI['crag_warm'], FI['crag_cool']]) \
        & (Yg <= ctop) & (Xg >= cx0 - 2) & (Xg <= cx1 + 2)
    for x in range(cx0 - 1, cx1 + 2):
        col_ = np.nonzero(((orig[:, x] >= 0) & (Yg[:, x] < stack_foot)) & ~potm[:, x])[0]
        if not len(col_):
            continue
        yt = int(col_.min())
        hh = 2 if x in (cx0 - 1, cx1 + 1) else 3
        if potm[:, x].any():
            continue                                        # the warm pot melts the snow at its foot
        if potm[:, max(0, x - 1):x + 2].any():
            hh = 1
        for k_ in range(hh):
            y = yt - hh + k_
            if 0 <= y < H:
                a[y, x] = C('snow', 5) if k_ == 0 else (C('snow', 4) if x < ccx else C('snow_cool', 3))
    # snow caught on the rough wall: on the stones' top edges, more on the windward (west) half, in
    # runs of two to four texels, and on the window sill and the door's lintel
    wx0, wx1, wy0, wy1 = b.info['wall']
    wx0, wx1, wy0, wy1 = wx0 + ox, wx1 + ox, wy0 + oy + 4, wy1 + oy
    up1 = np.full_like(orig, -1)
    up1[1:] = orig[:-1]
    stone_top = (orig >= 0) & (up1 >= 0) & np.isin(orig // 8, [FI[n] for n in ('stone', 'stone_cool', 'stone_warm', 'ashlar',
                                                                               'ashlar_warm')]) & \
        (up1 % 8 + 2 <= orig % 8) & (Yg > wy0) & (Yg < wy1 - 6) & (Xg > wx0 + 1) & (Xg < wx1 - 1)
    wu = (Xg - wx0) / max(1, wx1 - wx0)
    lodge = stone_top & (K.vhash(Xg // 3, Yg, seed + 23) < 0.55 - 0.45 * wu) & (a == orig)
    a[lodge] = np.where(K.vhash(Xg, Yg, seed + 24)[lodge] > 0.4, C('snow', 5), C('snow', 4))
    lodge2 = np.roll(lodge, 1, 0) & (a == orig) & (K.vhash(Xg // 2, Yg, seed + 25) > 0.35)
    a[lodge2] = C('snow_cool', 3)
    # the sill and the lintels: snow lying along them, two texels deep, lit on top, cool at the front
    for (o0, o1, o2, o3) in b.info['openings']:
        for (yy, x0_, x1_) in ((o1 + oy - 2, o0 + ox - 1, o2 + ox + 1), (o3 + oy, o0 + ox - 2, o2 + ox + 2)):
            if yy >= y_e + 4 and yy < wy1 - 4:
                for x in range(x0_, x1_):
                    if a[yy, x] >= 0 and hsh(seed, x // 3, yy) > 0.15:
                        a[yy - 1, x] = C('snow', 5)
                        a[yy, x] = C('snow_cool', 4) if x > (x0_ + x1_) / 2 else C('snow', 4)
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
    # crest, the upper body, the cool lower body and its foot, the wind's crust, a blue shade row on
    # the wall above it
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
        cool = u > 0.55
        for k_ in range(h):
            y = foot - k_
            if not (0 <= y < H):
                continue
            f = k_ / max(1.0, h - 1.0)
            if k_ == h - 1:
                c = C('snow', 5)
            elif f > 0.6:
                c = C('snow', 4) if not cool else C('snow_cool', 4)
            elif f > 0.25:
                c = C('snow_cool', 4) if not cool else C('snow_cool', 3)
            else:
                c = C('snow_cool', 3) if not cool else C('snow_cool', 2)
            if 0 < k_ < h - 1 and K.vhash((x + (y // 2) % 2) // 3, y, seed + 21) < 0.28:
                c = C('snow', 4) if c != C('snow', 4) else C('snow_cool', 4)
            a[y, x] = c
        y = foot - h
        if 0 <= y < H and a[y, x] >= 0 and wl <= x <= wr:
            a[y, x] = C('sky_cool', 2)
    V.outline(p.a)
    V.tidy(p.a)
    q_ = K.crop(p.a, p.ax, p.ay)
    pots = b.info.get('pots') or []
    if pots:
        px, py = pots[0]
        pot_x, pot_y = int(px + ox - p.ax + q_.ax), int(py + oy - p.ay + q_.ay) - 2
    elif potm.any():
        # the plume leaves the pot's mouth (R2-H2): its foot overlaps the rim by a texel
        pys, pxs = np.nonzero(potm)
        pot_x, pot_y = int(round(pxs.mean())) - p.ax + q_.ax, int(pys.min()) - p.ay + q_.ay + 1
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
CONIFERS = {'spruce': ((0.95, 1.06), 507), 'pine': ((1.0, 1.0), 511), 'squat': ((1.18, 0.74), 521),
            'krummholz': ((1.25, 0.44), 531), 'krummholz_b': ((1.0, 0.36), 547), 'krummholz_c': ((1.4, 0.52), 559)}


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
    rng = np.random.default_rng(seed * 13 + 5)
    lab, n = ndi.label(tops, structure=np.array([[0, 0, 0], [1, 1, 1], [0, 0, 0]]))
    # (Matt's review of round 3: the snow read as one white triangle stamped on every bough) each
    # bough top carries one to three clumps of its own length and height, following the tier's top
    # edge, heaped where the bough is stiff (west, near the trunk) and sagging a row at the tip;
    # some boughs are bare; the bough's dark underside shows beneath every clump
    Nf = ndi.gaussian_filter(rng.random((H, W)), (2.5, 2.2), mode='nearest')
    Nf = (Nf - Nf.min()) / max(1e-6, Nf.max() - Nf.min())
    for k in range(1, n + 1):
        ry, rx = np.nonzero(lab == k)
        if len(rx) < 3:
            continue
        xl, xr = rx.min(), rx.max()
        for y, xx in zip(ry, rx):
            ux_ = (xx - x0) / max(1, x1 - x0)
            uy_ = (y - y0) / max(1, y1 - y0)
            if ux_ > 0.74 and uy_ > 0.45:
                continue
            v = Nf[y, xx]
            if v < 0.45:
                continue                                    # a gap between two clumps
            t = int(round((2.0 + 5.5 * (v - 0.45) / 0.55) * load * (1.3 - 0.65 * ux_) * (1.0 if uy_ < 0.8 else 0.8)))
            sag = 1 if (xr - xx) <= 1 and xr - xl >= 4 else 0  # the bough's tip bends under it
            for j in range(t):
                yy = y + j + sag
                if yy < H and mask[yy, xx]:
                    snow[yy, xx] = True
                    lvl[yy, xx] = j
    # no one-texel strip of green left between two clumps (it would read as a drawn line)
    for _ in range(2):
        gap = mask & ~snow & ((np.roll(snow, 1, 0) & np.roll(snow, -1, 0)) | (np.roll(snow, 1, 1) & np.roll(snow, -1, 1)))
        snow |= gap
        lvl[gap] = 1
    # tones: each clump's top row lit on its west, its body, a cool lower edge, the shade under it
    lowest = snow & ~np.roll(snow, -1, 0)
    Hh, Wd = H, W
    Xg = np.mgrid[0:Hh, 0:Wd][1]
    ux = (Xg - x0) / max(1, x1 - x0)
    west_end = snow & ~np.roll(snow, 1, 1)
    c = np.where(lvl == 0, np.where(ux < 0.5, C('snow', 5), C('snow', 4)), C('snow', 4))
    c = np.where(west_end & (lvl <= 1), C('snow', 5), c)
    c = np.where(lowest & (lvl > 0), C('snow_cool', 3), c)
    c = np.where((ux > 0.62) & (lvl > 0), C('snow_cool', 4), c)
    code[snow] = c[snow]
    # the bough's dark underside: two rows under the heavier clumps, so it reads as shade, not a line
    under = np.roll(lowest & (lvl >= 2), 1, 0) & mask & ~snow
    code[under] = C('leaf_cool', 1)
    under2 = np.roll(under, 1, 0) & mask & ~snow
    code[under2] = C('leaf_cool', 1)
    under3 = np.roll(under2, 1, 0) & mask & ~snow
    code[under3] = C('leaf_cool', 2)
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
    T = tw * d * (0.8 if form.startswith('krummholz') else 1.0)
    cols = int(round(foot[0]))
    half_t = max(2, int(T / 2))
    band = mask[:, max(0, cols - half_t):cols + half_t + 1]
    bots = [np.nonzero(band[:, j])[0].max() for j in range(band.shape[1]) if band[:, j].any()]
    cb = min(bots) if bots else foot[1] - 10 * d
    length = int(foot[1] - cb + (4 if form.startswith('krummholz') else 10))
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
    """The warden's woodpile against the cold (round 3, R2-P3): split and round logs stacked between
    two stakes, their cut ends to the south in several sizes, laid staggered in rough courses (each
    end a bark rim, a pale sapwood ring, the heartwood with its rings and a radial check, lit on its
    upper west), the gaps between them dark; a pillowed cap of snow on top, snow at its west end."""
    sc = K.Scene(-40, 40, -20, 12, 70)
    sc.box(-30, -8, 0, 30, 4, 24, B.OAK, base=1.6, k=1.0, tag='pile', round_=1.5, tex='wood')
    for x in (-33, 31):
        sc.box(x, -2, 0, x + 3, 1, 31, B.OAK, base=2.4, k=1.6, tag='stake', round_=0.8, tex='wood_v')
    for (cx, w, h) in ((-18, 15, 4.4), (1, 17, 5.2), (18, 14, 4.0)):
        sc.ellipsoid(cx, -2.0, 24.5, w, 7.8, h, SNOW, base=3.9, k=1.1, tag='snow', flat=1.6)
    sc.ellipsoid(-33, 3.5, 0.2, 6.5, 4.0, 6.0, SNOW, base=3.8, k=1.0, tag='drift', flat=1.2)

    a = _solo(sc, dress=lambda s_, a: _snow_light(s_, a, swell=0.1))
    _crust(sc, a, seed, rate=0.18)

    def logs(s_, a):
        rng = np.random.default_rng(seed)
        m = np.isin(s_.label, [i for i, q in enumerate(s_.solids) if q.tag == 'pile']) & (s_.n[..., 1] > 0.5)
        m &= ndi.binary_erosion(a >= 0)
        ys, xs = np.nonzero(m)
        if not len(ys):
            return
        H, W = a.shape
        a[m] = C('timber_cool', 1)                         # the dark gaps between the logs
        Yi, Xi = np.mgrid[0:H, 0:W]
        y = ys.max() + 0.5
        row = 0
        while y > ys.min() + 3:
            x = xs.min() - (2.5 if row % 2 else 0.5) + rng.uniform(0, 1.5)
            rs = []
            while x < xs.max() + 2:
                r = float(rng.choice([3.0, 3.5, 4.0, 4.6]))
                cx, cy = x + r, y - r - rng.uniform(0, 0.8)
                rs.append(r)
                d = np.sqrt((Xi + 0.5 - cx) ** 2 + (Yi + 0.5 - cy) ** 2) / r
                disc = (d <= 1.0) & m
                ddx, ddy = (Xi + 0.5 - cx) / r, (Yi + 0.5 - cy) / r
                lit = -ddx - ddy
                c = np.where(d > 0.8, np.where(lit > 0.2, C('timber', 3), C('timber_cool', 2)),
                             np.where(d > 0.58, np.where(lit > -0.2, C('sand_cool', 4), C('sand_cool', 3)),
                                      np.where((np.abs(d - 0.3) < 0.08) & (r > 3.2), C('sand_cool', 3),
                                               np.where(lit > 0.5, C('sand', 5), np.where(lit > -0.3, C('sand', 4),
                                                                                         C('sand_cool', 4))))))
                check = (ddx > 0.05) & (np.abs(ddy) < 0.12) & (d < 0.6) & (r > 3.4)
                c = np.where(check, C('sand_cool', 2), c)
                a[disc] = c[disc]
                x += 2 * r - rng.uniform(0, 0.8)
            y -= 2 * float(np.mean(rs)) * 0.86
            row += 1
    logs(sc, a)
    return K.crop(a, sc.ox, sc.oy)


def hut_tools(seed=73):
    """The warden's ice tools in a rack by the hut (round 3, R2-P4): a two-post rail, and leaning on
    it at their own angles an ice saw (a long toothed blade, its T handle up), a felling axe (a lit
    steel head with its edge catching the light, a curved haft) and a snow shovel (a broad lit blade,
    its shaft and grip); each part lit on its west side and dark on its east, snow on their tops and
    heaped at their feet."""
    sc = K.Scene(-30, 30, -14, 12, 90)
    sc.box(-21, -4, 0, 21, -1, 50, B.OAK, base=2.2, k=1.4, tag='board', round_=0.6, tex='wood_v')
    for x in (-23, 19):
        sc.box(x, -2, 0, x + 4, 1, 54, B.OAK, base=2.6, k=1.6, tag='post', round_=0.8, tex='wood_v')
    sc.box(-24, -5, 50, 24, 2, 53, B.OAK, base=2.7, k=1.6, tag='rail', round_=1.0, tex='wood')
    for (cx, w) in ((-13, 12), (5, 14), (17, 8)):
        sc.ellipsoid(cx, -1.5, 53.5, w, 4.5, 2.6, SNOW, base=3.9, k=1.1, tag='snow', flat=1.8)
    sc.ellipsoid(-1, 3, 0.2, 21, 6.0, 4.0, SNOW, base=3.8, k=1.0, tag='drift', flat=1.4)
    sc.render()
    a = sc.shade()
    _snow_light(sc, a)
    # the backboard's planks: joints, a lit west edge on each, nail heads at the rail
    H_, W_ = a.shape
    Y_, X_ = np.mgrid[0:H_, 0:W_]
    bd = np.isin(sc.label, [i for i, q in enumerate(sc.solids) if q.tag == 'board']) & (sc.n[..., 1] > 0.5)
    pl = (X_ - sc.ox + 21) % 7
    a[bd & (pl == 6)] = C('timber_cool', 1)
    a[bd & (pl == 0)] = (a[bd & (pl == 0)] // 8) * 8 + np.minimum(5, a[bd & (pl == 0)] % 8 + 1)
    V.tidy(a)
    V.outline(a)
    p = lambda x, z, y=4: (sc.ox + x, sc.oy + y - z)     # noqa: E731

    tool = set()

    def stick(x0, z0, x1, z1, w, lit_c, body_c, dark_c):
        n = int(max(abs(x1 - x0), abs(z1 - z0))) + 1
        for t in np.linspace(0, 1, n):
            X, Y = p(x0 + (x1 - x0) * t, z0 + (z1 - z0) * t)
            X, Y = int(round(X)), int(round(Y))
            for k in range(w):
                if 0 <= Y < a.shape[0] and 0 <= X + k < a.shape[1]:
                    a[Y, X + k] = lit_c if k == 0 else (dark_c if k == w - 1 else body_c)
            if 0 <= Y < a.shape[0] and 0 <= X + w < a.shape[1] and a[Y, X + w] not in tool:
                a[Y, X + w] = C('timber_cool', 0)
            for k in range(w):
                if 0 <= Y < a.shape[0] and 0 <= X + k < a.shape[1]:
                    tool.add(int(a[Y, X + k]))
    # the ice saw: a long blade leaning west of centre, teeth on its east edge, a T handle at the top
    stick(-16, 1, -11, 62, 5, C('snow', 4), C('iron', 5), C('iron', 2))
    for k in range(4, 58, 2):
        X, Y = p(-16 + 5 * k / 61 + 5, 1 + k)
        X, Y = int(round(X)), int(round(Y))
        if 0 <= Y < a.shape[0] and 0 <= X < a.shape[1]:
            a[Y, X] = C('soot', 0)
            if X + 1 < a.shape[1]:
                a[Y, X + 1] = C('iron', 3)
    stick(-17, 61, -7, 63, 3, C('timber', 4), C('timber', 3), C('timber_cool', 1))
    # the axe: its haft leaning west on the rail, the steel head at the top, its bit to the east
    stick(4, 1, -1, 52, 3, C('timber', 5), C('timber', 3), C('timber_cool', 1))
    hx, hz = 0, 41
    for dz in range(-6, 7):
        for dx in range(-2, 11):
            X, Y = p(hx + dx, hz + dz)
            X, Y = int(round(X)), int(round(Y))
            half = 2 + max(0, dx - 2) * 0.55
            if abs(dz) <= half and 0 <= Y < a.shape[0] and 0 <= X < a.shape[1]:
                if dx <= 0:
                    c = C('iron', 2)                                  # the eye round the haft
                elif dx >= 9 or abs(abs(dz) - half) < 0.6:
                    c = C('snow', 5) if dz < 0 or dx >= 9 else C('iron', 3)   # the bit's edge and the bevel
                else:
                    c = C('iron', 5) if dz < -1 else (C('iron', 4) if dz < 2 else C('iron', 2))
                a[Y, X] = c
    for dz in range(-7, 8):
        X, Y = p(hx + 11, hz + dz)
        X, Y = int(round(X)), int(round(Y))
        if abs(dz) <= 7 and 0 <= Y < a.shape[0] and 0 <= X < a.shape[1]:
            a[Y, X] = C('soot', 0)
    # the shovel: shaft leaning on the rail, a broad blade at its foot, the grip at the top
    stick(14, 14, 9, 58, 3, C('timber', 5), C('timber', 3), C('timber_cool', 1))
    stick(5, 57, 13, 59, 3, C('timber', 5), C('timber_cool', 2), C('timber_cool', 1))
    for dz in range(0, 17):
        wdt = 12 - dz // 3 if dz < 14 else 3
        for dx in range(-wdt // 2, wdt - wdt // 2):
            X, Y = p(14.5 + dx - dz * 0.1, 1 + dz)
            X, Y = int(round(X)), int(round(Y))
            if 0 <= Y < a.shape[0] and 0 <= X < a.shape[1]:
                u = (dx + wdt / 2) / max(1, wdt) + (0.25 if dz < 6 else 0.0)
                a[Y, X] = (C('snow_cool', 3) if u < 0.15 else C('slate', 5) if u < 0.35 else C('slate', 4) if u < 0.6 else
                           C('slate', 3) if u < 0.85 else C('slate_cool', 1))
    # snow on the tools' tops
    for (x, z) in ((-12, 63), (-7, 64), (-2, 53), (3, 55), (9, 59), (12, 60)):
        X, Y = p(x, z + 1)
        for k in range(3):
            if 0 <= Y < a.shape[0] and 0 <= X + k < a.shape[1]:
                a[Y, int(X) + k] = C('snow', 5)
    V.outline(a)
    _crust(sc, a, seed, rate=0.4)
    return K.crop(a, sc.ox, sc.oy)


def bench(seed=79):
    """A granite slab bench by the Col Path (round 3, R2-P1): a dressed slab with its lit top, a
    front face a step down and a dark east end, chamfered; two block legs, each with a lit top and
    a shaded east side; a pillow of snow on the east half of the seat (lit west, a cool front edge,
    shade under its lip), the west half brushed clear; the gap under the seat in shade."""
    sc = K.Scene(-40, 40, -16, 10, 50)
    for x in (-28, 20):
        sc.box(x, -5, 0, x + 8, 4.5, 13.2, GRANITE, base=2.9, k=1.9, tag='rock', round_=2.2, mix=0.3 + 0.4 * (x > 0), tex='stone')
    sc.box(-35, -8, 13, 35, 5, 18, GRANITE, base=3.1, k=1.9, tag='slab', round_=1.6, mix=0.55, tex='stone')
    sc.ellipsoid(17.0, -1.8, 18.6, 16.5, 6.6, 3.0, SNOW, base=3.9, k=1.1, tag='snow', flat=2.2)
    sc.ellipsoid(9.0, -2.5, 20.0, 6.5, 4.0, 2.2, SNOW, base=3.9, k=1.1, tag='snow', flat=1.6)
    sc.ellipsoid(-29.5, 4.0, 0.2, 5.0, 3.0, 3.6, SNOW, base=3.8, k=1.0, tag='drift', flat=1.2)

    def dress(s_, a):
        _granite_dress(s_, a, seed, tags=('rock', 'slab'), n_frac=2)
        lab = s_.label
        slab = np.isin(lab, [i for i, q in enumerate(s_.solids) if q.tag == 'slab'])
        H, W = a.shape
        Y, X = np.mgrid[0:H, 0:W]
        xs = np.nonzero(slab.any(0))[0]
        front = slab & (s_.n[..., 1] > 0.5)
        if len(xs):
            east = front & (X >= xs.max() - 3)
            a[east] = C('slate_cool', 1)
            a[slab & (X >= xs.max() - 1) & ~front] = C('slate_cool', 2)
            # the chamfer: the front's top row lit where it turns from the top
            ch = front & ~np.roll(front, 1, 0) & (X < xs.max() - 3)
            a[ch] = C('slate', 4)
            # tool marks along the dressed front
            tm = front & (K.vhash(X // 4, Y, seed + 7) > 0.8) & ~ch & (X < xs.max() - 3)
            a[tm] = C('slate_cool', 2)
        # the gap under the seat: the snow between the legs in the slab's shade
        rows = np.nonzero(slab.any(1))[0]
        if len(rows):
            yb = rows.max() + 1
            legs = np.isin(lab, [i for i, q in enumerate(s_.solids) if q.tag == 'rock'])
            lx = np.nonzero(legs.any(0))[0]
            for x in range(xs.min() + 2, xs.max() - 1):
                if legs[:, x].any() or not (lx.min() < x < lx.max()):
                    continue
                for d in range(2):
                    if yb + d < H and a[yb + d, x] < 0:
                        a[yb + d, x] = C('sky_cool', 4) if d == 0 else C('snow_cool', 3)
    a = _solo(sc, dress=dress)
    _grain_after(sc, a, seed, tags=('rock', 'slab'), swap=0.5)
    return K.crop(a, sc.ox, sc.oy)


def noticeboard(seed=83):
    """The warden's board at the foot of the col: two posts, a plank board under a little pent roof
    with snow on it, notices pinned (weather, the ring shut)."""
    sc = K.Scene(-36, 36, -10, 10, 110)
    for x in (-20, 17):
        sc.box(x, -2, 0, x + 3, 1, 78, B.OAK, base=2.4, k=1.5, tag='post')
    sc.box(-24, -2, 40, 24, 1, 74, B.OAK, base=2.7, k=1.4, tag='board', tex='wood')
    sc.box(-27, -6, 74, 27, 4, 78, [('slate_cool', 'slate', 'slate')], base=2.6, k=1.6, tag='roof', round_=0.8)
    # (round 3, R2-P5) the snow on the pent roof: a mass with thickness, heaped west, its top edge
    # lumpy, its front hanging over the roof's edge with a shade under it
    for (cx, w, h) in ((-17, 11, 4.4), (-3, 12, 5.0), (12, 11, 4.0), (22, 5, 3.0)):
        sc.ellipsoid(cx, -0.5, 78.5, w, 6.2, h, SNOW, base=3.9, k=1.1, tag='snow', flat=1.8)
    sc.ellipsoid(-21.5, 1.5, 0.2, 5.0, 3.0, 4.5, SNOW, base=3.8, k=1.0, tag='drift', flat=1.2)
    sc.render()
    a = sc.shade()
    _snow_light(sc, a)
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
    _crust(sc, a, seed, rate=0.3)
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


COURSES = [0, 17, 33, 52, 72, FACE_PX]            # the face's bedding planes (z), the same in every panel
SET_BACK = 3.0                                      # each course stands this far behind the one under it


def _wall_blocks(W, seed, ends):
    """The blocks of one panel: (x0, x1, z0, z1, y_front, base, mix, round). Courses on the shared
    bedding planes; blocks 12 to 40 texels wide, small ones in clusters (a course split in two);
    at each panel edge a bridge block whose params depend only on the course, so neighbours meet in
    one block (no seam); none at a real end."""
    rng = np.random.default_rng(seed)
    out = []
    for k in range(len(COURSES) - 1):
        z0, z1 = COURSES[k], COURSES[k + 1]
        yf = 2.0 - SET_BACK * k
        br = 9 + int(hsh(k, 41) * 8)                       # the bridge block's half width
        bb = 2.75 + 0.35 * (hsh(k, 43) - 0.5)
        bm = hsh(k, 47)
        lo = 3.0 if ends[0] else float(br)
        hi = W - 3.0 if ends[1] else W - float(br)
        if not ends[0]:
            out.append((-br, br - 1, z0, z1 - 1, yf, bb, bm, 3.5))
        if not ends[1]:
            out.append((W - br, W + br - 1, z0, z1 - 1, yf, bb, bm, 3.5))
        x = lo + (1 if not ends[0] else 0)
        while x < hi - 6:
            wdt = float(rng.choice([rng.uniform(12, 18), rng.uniform(18, 28), rng.uniform(26, 40)], p=[0.35, 0.4, 0.25]))
            x1 = min(hi - 1, x + wdt)
            if hi - 1 - x1 < 10:
                x1 = hi - 1
            jit = rng.uniform(-1.2, 1.6)
            base = 2.8 + rng.uniform(-0.35, 0.35) - 0.25 * (k == 0)
            if wdt < 18 and z1 - z0 > 15 and rng.random() < 0.7:
                zm = z0 + (z1 - z0) * rng.uniform(0.4, 0.6)
                out.append((x, x1 - 1, z0, zm - 1, yf + jit + 0.8, base - 0.15, rng.random(), 2.5))
                out.append((x + rng.uniform(-2, 2), x1 - 1, zm, z1 - 1, yf + jit, base + 0.1, rng.random(), 2.5))
            else:
                out.append((x, x1 - 1, z0, z1 - 1, yf + jit, base, rng.random(), rng.uniform(3.0, 5.5)))
            x = x1 + 1
    return out


def _face(width, seed, ends=(True, True), fall=None, stair=None):
    """A south-facing granite face `width` texels wide (round 3, R2-F1, after Eastward 12's block
    cliff): stratified granite blocks of 12 to 40 texels on shared bedding planes, each course set a
    little behind the one under it, so every block shows a lit top lip, a front in its own tone and
    a shaded underside where it tucks over the course below; dark joints, fractures, water streaks
    and snow lying on the ledges; a snow lip with thickness hanging over the top, a blue shade under
    it; a dark stony foot with drifts. Blocks run across the panel edges (bridge blocks), so a run of
    panels reads as one face; side ends only where `ends` says. `fall`: (x0, x1) the frozen fall;
    `stair`: (x0, x1) the stair cut up it."""
    rng = np.random.default_rng(seed)
    H = LIP_PX + FACE_PX + 6
    W = width
    zmax = FACE_PX + 40
    sc = K.Scene(0, W, -30, 12, zmax)
    cheeks = ends                                         # (Matt's review of round 3) an end is a stair's cheek
    ends = (False, False)
    blocks = _wall_blocks(W, seed, ends)
    bx0 = 8.0 if ends[0] else -2.0
    bx1 = W - 8.0 if ends[1] else W + 2.0
    spans = [(bx0, bx1)]
    if stair is not None:
        s0, s1 = stair
        # the cheeks: the face's blocks either side of the cut, standing a little proud, ending a
        # tread above the foot
        blocks = [(x0, min(x1, s0 + 2), z0, z1, yf + 3.0, base, mix, rnd) for (x0, x1, z0, z1, yf, base, mix, rnd) in blocks
                  if x0 < s0 - 4 and z0 >= COURSES[1]] + \
                 [(max(x0, s1 - 2), x1, z0, z1, yf + 3.0, base, mix, rnd) for (x0, x1, z0, z1, yf, base, mix, rnd) in blocks
                  if x1 > s1 + 4 and z0 >= COURSES[1]]
        spans = [(bx0, s0 + 1.0), (s1 - 1.0, bx1)]
    # the joints: the rock behind the blocks, dark
    for (j0, j1) in spans:
        sc.box(j0, -30, 0 if stair is None else COURSES[1], j1, -6 - SET_BACK * 5, FACE_PX, [('soot', 'slate_cool', 'slate_cool')],
               base=0.9, k=0.3, tag='joint')
    if stair is not None:
        _stair_steps(sc, stair, seed)
    for (x0, x1, z0, z1, yf, base, mix, rnd) in blocks:
        # (Matt's review of round 3: the pillow stones) an angular granite block on its bedding plane:
        # a flat lit top lip where the course above stands back, a flat front in its own tone, sharp
        # arrises with a texel of chamfer, its top a little out of level
        tilt = (hsh(int(x0), int(z0), 5) - 0.5) * 2.0
        sc.box(x0, yf - 16, z0, x1, yf, z1 + tilt, GRANITE, base=base + 0.1, k=1.9, tag='rock', round_=0.9 + 0.25 * rnd,
               mix=mix)
    # snow on some ledges: where a block stands proud of the one above it
    for k_, (x0, x1, z0, z1, yf, base, mix, rnd) in enumerate(blocks):
        if z1 >= FACE_PX - 1 or x1 - x0 < 10 or hsh(seed, k_, 3) < 0.45:
            continue
        sw = (x1 - x0) * rng.uniform(0.45, 0.8)
        sx = x0 + 1 + rng.uniform(0, max(0.1, (x1 - x0) - sw - 2))
        sc.ellipsoid(sx + sw / 2, yf - 2.5, z1 + 0.6, sw / 2, 2.6, 2.0, SNOW, base=3.9, k=1.1, tag='snow', flat=2.0)
    # the lip: the upper tier's snow running over the top, its front hanging over the face
    top = FACE_PX
    yl = 2.0 - SET_BACK * 5
    lx0 = -4 if not ends[0] else 0
    lx1 = W + 4 if not ends[1] else W
    lips = [(lx0, lx1)] if stair is None else [(lx0, stair[0] + 2), (stair[1] - 2, lx1)]
    for (p0, p1) in lips:
        sc.box(p0, -30, top - 1, p1, yl - 1 + (3.0 if stair is not None else 0.0), top + 4, SNOW, base=3.9, k=1.0, tag='snow',
               round_=1.5)
    n = max(3, W // 12)
    for j in range(n + 1):
        x = W * j / n + rng.uniform(-4, 4)
        r = rng.uniform(7, 12)
        if stair is not None and stair[0] - 4 < x < stair[1] + 4:
            continue
        sc.ellipsoid(x, yl + rng.uniform(-0.5, 1.5), top + 2.5, r, 4.2, 4.2 + rng.uniform(-0.8, 1.2), SNOW, base=3.9, k=1.1,
                     tag='snow', flat=1.6)
    # the foot: talus in front, drifts banked against it
    x = -3.0 if not ends[0] else 4.0
    while x < (W + 3 if not ends[1] else W - 6):
        r = rng.uniform(3, 7)
        if stair is not None and stair[0] - 2 < x + r < stair[1] + 2:
            x += r
            continue
        sc.ellipsoid(x + r, -0.5 + rng.uniform(-1, 1), r * 0.45, r, r * 0.6, r * 0.6, GRANITE, base=2.0 + rng.uniform(-0.3, 0.3),
                     k=1.7, tag='rock', mix=rng.random(), flat=1.8)
        x += r * rng.uniform(1.3, 2.2)
    dp = ndi.gaussian_filter1d(rng.random(W + 20), 5.0, mode='wrap')
    for j in range(0, W + 1, 9):
        h = 2.5 + 7 * (dp[j] - dp.min()) / max(1e-6, dp.max() - dp.min())
        if h > 4.0 and not (stair is not None and stair[0] - 6 < j < stair[1] + 6):
            sc.ellipsoid(j + rng.uniform(-3, 3), 4.5, 0.2, rng.uniform(6, 10), 4.0, h * 0.45, SNOW, base=3.8, k=1.0, tag='drift', flat=1.3)
    sc.render()
    a = sc.shade(crevice=1.6, rim=0.8)
    m = sc.label >= 0
    rockm = np.isin(sc.label, [i for i, s_ in enumerate(sc.solids) if s_.tag == 'rock'])
    # the lower courses in the shade of the step (a tone down in the lowest third)
    Y, X = np.mgrid[0:sc.H, 0:sc.W]
    zfoot = sc.oy - 0                                     # canvas row of the ground line
    low = rockm & (Y > zfoot - 30) & (sc.n[..., 2] < 0.6)
    a[low] = (a[low] // 8) * 8 + np.maximum(1, a[low] % 8 - 1)
    # the lit top lips: each block's top plane where the course above stands back, two tones up
    lip_ = rockm & (sc.n[..., 2] > 0.5)
    a[lip_] = np.where(sc.light()[lip_] > 0.6, C('slate', 5), C('slate', 4))
    lip_edge = lip_ & ~np.roll(lip_, -1, 0)
    a[lip_edge] = C('slate_warm', 4)
    # each block's front: lit high where it meets its lip, shaded low where it tucks over the course
    # below (three tones down its height)
    labm = sc.label
    fr = rockm & ~lip_
    run = np.zeros(labm.shape, int)
    for y in range(1, labm.shape[0]):
        run[y] = np.where(fr[y] & (labm[y] == labm[y - 1]), run[y - 1] + 1, 0)
    rev = np.zeros(labm.shape, int)
    for y in range(labm.shape[0] - 2, -1, -1):
        rev[y] = np.where(fr[y] & (labm[y] == labm[y + 1]), rev[y + 1] + 1, 0)
    hi_ = fr & (run <= 1) & (rev > 3)
    a[hi_] = (a[hi_] // 8) * 8 + np.minimum(5, a[hi_] % 8 + 1)
    lo_ = fr & (rev <= 2) & (run > 3)
    a[lo_] = (a[lo_] // 8) * 8 + np.maximum(1, a[lo_] % 8 - 1)
    _fractures(a, rockm & (sc.n[..., 1] > 0.5), seed + 5, n=max(2, W // 30))
    # water streaks: from under some ledges, a darker run down the face
    for j in range(max(2, W // 28)):
        xs_ = int(rng.integers(3, W - 3))
        col = np.nonzero(rockm[:, xs_] & (sc.n[:, xs_, 1] > 0.5))[0]
        if len(col) < 10:
            continue
        y0 = int(col[int(rng.integers(0, len(col) // 2))])
        for yy in range(y0, min(sc.H, y0 + int(rng.integers(6, 16)))):
            for dx in (0, 1) if rng.random() < 0.5 else (0,):
                if rockm[yy, xs_ + dx]:
                    a[yy, xs_ + dx] = C('slate_cool', max(1, a[yy, xs_ + dx] % 8 - 1))
    _snow_light(sc, a)
    if stair is not None:
        _stair_dress(sc, a, stair, seed)
    V.tidy(a)
    K.despeckle(a)
    V.outline(a)
    _grain_after(sc, a, seed, swap=0.3, step=0.04)
    if stair is not None:
        _stair_wear(sc, a, stair, seed)
    # onto the panel's canvas: the ground line at row LIP_PX + FACE_PX - 1
    yf = LIP_PX + FACE_PX
    off = sc.oy - (yf - 1)
    out = np.full((H, W), -1, np.int32)
    src0 = max(0, off)
    out[max(0, -off):max(0, -off) + min(sc.H - src0, H - max(0, -off))] = a[src0:src0 + min(sc.H - src0, H - max(0, -off))]
    # the top rows are the upper tier's snow (the picture meets the ground above it)
    first = np.argmax(out >= 0, axis=0)
    rk = np.isin(out // 8, [FI['slate'], FI['slate_cool'], FI['slate_warm'], FI['iron'], FI['stone_cool'], FI['soot']]) & (out >= 0)
    for x in range(W):
        if stair is not None and stair[0] <= x < stair[1]:
            # the trod coming over the top of the stair: packed snow, a tone cooler, worn grooves
            for y in range(first[x]):
                out[y, x] = C('snow_cool', 4) if hsh(seed, x // 3, y // 2, 11) > 0.22 else (
                    C('snow_cool', 3) if (x + y) % 3 else C('snow', 4))
        elif rk[:LIP_PX + 30, x].any():
            out[:first[x], x] = C('snow', 4)
        else:
            out[:, x] = -1
    for side, on in enumerate(cheeks):
        if on:
            _cheek(out, side, seed)
    # under the foot: the drifts' lower edge, then nothing (the ground below is the zone's)
    prof = ndi.gaussian_filter1d(np.array([hsh(seed, x, 9) for x in range(W)]), 3.0, mode='wrap')
    prof = (prof - prof.min()) / max(1e-6, prof.max() - prof.min())
    for x in range(W):
        out[yf + int(round(2.2 * prof[x])):, x] = -1
    a = out
    V.outline(a)
    if fall is not None:
        _icefall(a, fall, seed)
    return V.Pic(W, H, W // 2, yf - 1), a


def _icefall(a, fall, seed):
    """The outlet frozen over the face (round 3, R2-F3): bulging columns of ice of different widths
    that swell, pinch and merge into curtains, each lit on its west edge (snow 5, then frost white)
    and turning blue to a shaded east side; the lanes inside a column fall in long streaks; icicle
    clusters hang from the frozen lip, snow lies on its crown, and the ice spreads at the foot into
    an apron that meets the channel. Rock shows between the columns' pinches and at the edges."""
    H, W = a.shape
    rng = np.random.default_rng(seed + 31)
    f0, f1 = fall
    yf = LIP_PX + FACE_PX
    y_top, y_bot = LIP_PX - 6, yf + 1
    # columns: (centre, half width, bulge phase, bulge size, period); they overlap into curtains
    cols = []
    x = f0
    while x < f1 - 4:
        w = float(rng.choice([rng.uniform(4, 6), rng.uniform(6, 9), rng.uniform(9, 14)], p=[0.3, 0.45, 0.25]))
        w = min(w, max(3.0, (f1 - x) / 2.0))
        cols.append((x + w, w, rng.uniform(0, 2 * math.pi), rng.uniform(0.12, 0.3), rng.uniform(34, 70)))
        x += 2 * w - rng.uniform(0.5, 2.5)
    yy = np.arange(H)
    v = np.clip((yy - y_top) / float(y_bot - y_top), 0, 1)
    edges = []
    for (cx, hw, ph, bs, per) in cols:
        wy = hw * (1 + bs * np.sin(2 * math.pi * yy / per + ph)) * (0.9 + 0.25 * v)
        cxy = cx + 1.2 * np.sin(2 * math.pi * yy / (per * 1.6) + ph * 0.7)
        L_ = np.round(ndi.uniform_filter1d(cxy - wy, 5)).astype(int)
        R_ = np.round(ndi.uniform_filter1d(cxy + wy, 5)).astype(int)
        edges.append((L_, R_))
    # paint each column from its west edge (lit) to its east edge (shade); the body in lanes that
    # stay put (their tone steps only every 8 to 30 texels down), so the ice falls in streaks
    body = [C('snow', 5), C('snow', 4), C('snow', 4), C('snow_cool', 4), C('snow_cool', 4), C('sky_cool', 5), C('sky_cool', 5),
            C('sky_cool', 4), C('sky_cool', 3), C('sky_cool', 2)]
    for (L_, R_) in edges:
        lm, rm = float(L_[y_top:y_bot].mean()), float(R_[y_top:y_bot].mean())
        for y in range(y_top, y_bot):
            l, r = int(L_[y]), int(R_[y])
            for x in range(max(0, l), min(W, r + 1)):
                d, e = x - l, r - x
                if d == 0:
                    c = C('snow', 5)
                elif d <= 2:
                    c = C('snow', 4) if d == 1 or hsh(seed, x, y // 9) > 0.3 else C('snow', 5)
                elif e <= 1 + int(3.5 * x / W):
                    sg = (y + int(hsh(seed, x, 3) * 20)) // 11
                    c = (C('sky_cool', 2), C('water_cool', 3), C('sky_cool', 2), C('sky_cool', 3), C('water_cool', 2),
                         C('water', 3), C('water_cool', 4))[int(hsh(seed, x, sg, 4) * 7)] if e > 0 else C('sky_cool', 2)
                else:
                    ln = (x * 5 + int(hsh(seed, x // 2) * 3)) // 7
                    sg = (y + int(hsh(seed, ln, 1) * 30)) // (8 + int(hsh(seed, ln, 2) * 22))
                    # across the column the lanes go from frost white to blue shade, a step either way
                    rel = (x - lm) / max(1.0, rm - lm)
                    k_ = int(round(rel * 8.5 + 6.6 * x / W - 3.0 + (hsh(seed, ln, sg) - 0.5) * 2.2))
                    c = body[max(0, min(len(body) - 1, k_))]
                a[y, x] = c
    # (Matt's review of round 3: why is one part frozen and the other not?) fast water freezes last:
    # the fall still runs in one narrow column down its middle, dark and quick, white where it
    # breaks; the ice either side is its frozen flows and icicle curtains
    cxw = (f0 + f1) / 2.0 + 3
    for y in range(y_top, y_bot):
        v_ = (y - y_top) / float(y_bot - y_top)
        half = 5.0 + 1.5 * math.sin(y / 9.0) + 2.5 * v_
        c0 = cxw + 1.2 * math.sin(y / 13.0 + 1.0)
        l_, r_ = int(round(c0 - half)), int(round(c0 + half))
        for x in range(max(0, l_ - 1), min(W, r_ + 2)):
            if x == l_ - 1 or x == r_ + 1:
                a[y, x] = C('sky_cool', 3)                          # the ice's wet edge on the flow
                continue
            ln = (x * 3 + int(hsh(seed, x) * 5)) // 4
            sg = (y + int(hsh(seed, ln, 31) * 24)) // (6 + int(hsh(seed, ln, 32) * 14))
            g = hsh(seed, ln, sg, 33)
            rel = (x - l_) / max(1.0, r_ - l_)
            if rel < 0.2:
                c = C('snow', 5) if g > 0.4 else C('sky_cool', 5)
            elif g > 0.8:
                c = C('snow', 5)                                    # the water breaking white
            elif g > 0.6:
                c = C('water', 4)
            elif rel > 0.65:
                c = C('water_cool', 2) if g > 0.25 else C('sky_cool', 2)
            else:
                c = C('water', 2) if g > 0.3 else C('water', 3)
            a[y, x] = c
    # spray and rime at the foot: a soft cloud over the plunge, frost feathers on the ice beside it
    for y in range(y_bot - 16, y_bot + 1):
        for x in range(max(0, int(cxw) - 16), min(W, int(cxw) + 17)):
            d = ((x - cxw) / 15.0) ** 2 + ((y - y_bot + 3) / 10.0) ** 2
            if d < 1.0 and hsh(seed, x // 2, y // 2, 40) > 0.25 + 0.6 * d:
                a[y, x] = C('snow', 5) if d < 0.45 else C('snow_cool', 4)
    # the frozen lip: a crown of snow on the ice over the edge, icicles hanging under it in clusters
    for x in range(f0 - 2, f1 + 2):
        if not (0 <= x < W):
            continue
        hcap = 3 + int(round(2 * hsh(seed, x // 3, 5)))
        for k_ in range(hcap):
            y = y_top - 2 + k_
            a[y, x] = C('snow', 5) if k_ == 0 else (C('snow', 4) if k_ < hcap - 1 else C('snow_cool', 3))
    x = f0 + int(rng.integers(1, 4))
    while x < f1 - 1:
        if rng.random() < 0.6:
            n = int(rng.integers(2, 4))
            for j in range(n):
                xi = x + j * 2
                ln = int(rng.integers(5, 13))
                for k_ in range(ln):
                    y = y_top + 1 + k_
                    if 0 <= xi < W and y < H:
                        a[y, xi] = C('snow', 5) if k_ < ln // 2 else C('sky_cool', 5)
                        if k_ < ln // 3 and xi + 1 < W:
                            a[y, xi + 1] = C('sky_cool', 4)
            x += n * 2 + int(rng.integers(3, 7))
        else:
            x += int(rng.integers(3, 6))
    # the apron at the foot: the ice spreading in a low mound across the channel, lit on its top
    for x in range(max(0, f0 - 4), min(W, f1 + 4)):
        e = min(x - (f0 - 4), (f1 + 4) - x)
        h = int(round(min(4.0, 2 + e * 0.5) + 1.2 * hsh(seed, x // 5, 8)))
        for k_ in range(h):
            y = yf + 1 - h + k_
            if 0 <= y < H:
                a[y, x] = C('snow', 5) if k_ == 0 else (C('snow', 4) if k_ < 2 else (C('sky_cool', 5) if k_ < h - 1 else C('sky_cool', 3)))


STEPS = 6
RISE, TREAD = 6.5, 9.5          # (Matt's review of round 3) seen from above a stair is mostly treads
CHEEK = 14


def _cheek(a, side, seed):
    """The face's end where a stair is cut through it (Matt's review of round 3): a cheek 14 texels
    wide showing the cut's side wall, the face's courses running round onto it with their joints,
    lit where it faces west (the east cheek) and in shade where it faces east, a sharp arris where
    it turns from the face, the upper tier's snow capping it and a drift banked into its foot."""
    H, W = a.shape
    yf = LIP_PX + FACE_PX
    x0, x1 = (0, CHEEK) if side == 0 else (W - CHEEK, W)
    lit = side == 0
    rows_course = [yf - 1 - z for z in COURSES]
    for x in range(x0, x1):
        d = (x - x0) if side == 0 else (x1 - 1 - x)       # 0 at the stair, CHEEK-1 at the arris
        for y in range(LIP_PX - 2, yf):
            k = sum(1 for r in rows_course if y < r)
            c = C('slate', 3 if lit else 2) if lit else C('slate_cool', 2)
            if (y + d // 5) % 3 == 0 and hsh(seed, x, y // 3) > 0.6:
                c = C('slate', 4) if lit else C('slate_cool', 1)
            if any(abs(y - r) == 0 for r in rows_course):
                c = C('slate_cool', 0) if not lit else C('slate_cool', 1)
            if (d + 4 * k) % 9 == 0 and hsh(seed, k, x) > 0.4:
                c = C('slate_cool', 0) if not lit else C('slate_cool', 1)
            if d == CHEEK - 1:
                c = C('slate', 5) if lit else C('slate', 4)      # the arris where it turns from the face
            if d == 0:
                c = C('slate_cool', 0)
            a[y, x] = c
        top = LIP_PX - 6 + int(round(1.5 * hsh(seed, x // 4, 2)))
        for y in range(max(0, top), LIP_PX - 1):
            a[y, x] = C('snow', 5) if y == top else (C('snow', 4) if y < LIP_PX - 3 else C('snow_cool', 3))
        a[LIP_PX - 1, x] = C('sky_cool', 2)
        h = int(round(3 + 4 * (1 - d / CHEEK)))
        for k_ in range(h):
            y = yf - 1 - k_
            a[y, x] = C('snow', 5) if k_ == h - 1 else (C('snow', 4) if k_ > 1 else C('snow_cool', 4))


def _stair_steps(sc, stair, seed):
    """The stair's stones (round 3, R2-F2): six steps, each laid from three to five granite stones of
    their own widths and heights (a texel either way), set back a tread each step up; every stone a
    rounded block, so its nose catches the light and its riser falls into shade."""
    rng = np.random.default_rng(seed + 17)
    s0, s1 = stair
    for k in range(STEPS):
        z1 = RISE * (k + 1)
        yfr = 2.0 - TREAD * k
        x = s0 + 1.0
        while x < s1 - 1:
            w = rng.uniform(30, 62)
            x1 = min(s1 - 1.0, x + w)
            if s1 - 1 - x1 < 20:
                x1 = s1 - 1.0
            sc.box(x, yfr - TREAD - 2.5, max(0.0, z1 - RISE - 6), x1 - 1, yfr + rng.uniform(-0.6, 0.8), z1 + rng.uniform(-0.8, 0.8), GRANITE,
                   base=2.75 + rng.uniform(-0.3, 0.3), k=1.9, tag='step', round_=rng.uniform(1.6, 2.6), mix=rng.random(),
                   tex='stone')
            x = x1


def _stair_dress(sc, a, stair, seed):
    """The steps' snow before the outline: snow lying at the back of each tread and banked into its
    ends against the cheeks; the riser stepping darker toward its foot (four tones)."""
    lab = sc.label
    ids = [i for i, s_ in enumerate(sc.solids) if s_.tag == 'step']
    m = np.isin(lab, ids)
    H, W = a.shape
    Y, X = np.mgrid[0:H, 0:W]
    s0, s1 = stair
    top = m & (sc.n[..., 2] > 0.55)
    front = m & ~top
    # (Matt's review of round 3: the stair read as a brick wall) seen from above each step is a broad
    # lit tread: the stone's top in light greys, a shaded row at its back where the riser above
    # meets it, a lit nose at its front; under the nose a shallow riser in shade, darkest at its foot
    trun = np.zeros((H, W), int)
    for y in range(1, H):
        trun[y] = np.where(top[y], np.where(top[y - 1], trun[y - 1] + 1, 0), 0)
    nose = top & ~np.roll(top, -1, 0)
    g = K.vhash((X + (Y // 2) % 2) // 2, Y // 2, seed + 41)
    a[top] = np.where(g[top] > 0.78, C('slate_warm', 4), np.where(g[top] > 0.55, C('slate', 5), C('slate', 4)))
    a[top & (trun == 0)] = C('slate', 3)
    a[nose] = C('slate', 5)
    run = np.zeros((H, W), int)
    for y in range(1, H):
        run[y] = np.where(front[y], np.where(front[y - 1], run[y - 1] + 1, 0), 0)
    a[front] = np.where(run[front] == 0, C('slate', 3), np.where(run[front] <= 2, C('slate_cool', 2),
                        np.where(run[front] <= 4, C('slate_cool', 1), C('slate_cool', 0))))
    # snow at the back of each tread and in its ends
    for y in range(H):
        row = top[y]
        if not row.any():
            continue
        back = row & ~np.roll(top, 1, 0)[y]
        for x in np.nonzero(back)[0]:
            edge = min(x - s0, s1 - x)
            depth = 3 if edge < 10 else (2 if hsh(seed, x // 5, y) > 0.55 else 0)
            for d_ in range(depth):
                if y + d_ < H and top[y + d_, x]:
                    a[y + d_, x] = C('snow', 5) if d_ == 0 else C('snow_cool', 4)


def _stair_wear(sc, a, stair, seed):
    """After the grain: the trod worn into the middle of each tread (the stone smoothed a tone
    lighter, the grain gone, packed snow in the hollow), the nose lit with snow dust at intervals."""
    lab = sc.label
    ids = [i for i, s_ in enumerate(sc.solids) if s_.tag == 'step']
    m = np.isin(lab, ids) & (a >= 0)
    top = m & (sc.n[..., 2] > 0.55)
    s0, s1 = stair
    mid0, mid1 = s0 + (s1 - s0) * 0.3, s1 - (s1 - s0) * 0.3
    H, W = a.shape
    Y, X = np.mgrid[0:H, 0:W]
    wob = (K.vhash(Y, 3, seed) * 6).astype(int)
    worn = top & (X >= mid0 + wob - 3) & (X < mid1 - wob + 3) & ~np.isin(a // 8, list(SNOWS))
    a[worn] = np.where(K.vhash(X // 3, Y, seed + 2)[worn] > 0.8, C('snow_cool', 3), C('slate', 5))
    # snow banked into each tread's corners against the cheeks, deepest at the back
    rel = np.zeros_like(Y)
    for y in range(1, H):
        rel[y] = np.where(top[y], np.where(top[y - 1], rel[y - 1] + 1, 0), 0)
    lump = (K.vhash(Y // 3, 7, seed) * 5).astype(int)
    corner = top & (((X - s0) < 5 + lump) | ((s1 - X) < 6 + lump))
    a[corner] = np.where(rel[corner] <= 1, C('snow', 5), np.where(X[corner] < (s0 + s1) / 2, C('snow', 4), C('snow_cool', 4)))
    nose = top & ~np.roll(top, -1, 0) & ~np.isin(a // 8, list(SNOWS))
    a[nose] = np.where(K.vhash(X // 4, Y, seed + 3)[nose] > 0.5, C('snow', 5), C('slate', 4))


def rockface(width_cells=6, seed=101, ends=(True, True)):
    pic, a = _face(width_cells * 24, seed, ends=ends)
    pic.a[:] = a
    return pic


def rockface_fall(seed=113):
    """The face where the tarn's outlet comes over it, frozen into a curtain of icicles."""
    pic, a = _face(4 * 24, seed, ends=(False, False), fall=(0, 96))
    pic.a[:] = a
    return pic


def rock_stair(seed=127):
    """The Col Path's stair up the face: five cells (40 world px, over the 34 a stair needs), six
    granite steps with snow-dusted treads, cut through the lip."""
    pic, a = _face(5 * 24, seed, ends=(False, False), stair=(1, 119))
    pic.a[:] = a
    return pic


def footbridge(seed=131):
    """The Col Path's crossing of the tarn's outlet, seen from above in the three-quarter view
    (Matt's review of round 3: the round 3 bridge was drawn front-on like a fence). The deck's
    planks lie across the way, seen from above and a little foreshortened, each with its grain and
    a dark gap; a trodden track of packed snow runs along the deck; log kerbs edge it north and south
    on short posts, the south kerb over the deck's dark edge; the deck's shadow falls on the ice
    below it; abutments of laid stone are set into each bank, their tops under snow."""
    W, H = 5 * 24, 2 * 24 + 18
    a = np.full((H, W), -1, np.int32)
    rng = np.random.default_rng(seed)
    x0, x1 = 13, W - 13
    y0, y1 = 10, 44                                       # the deck's top, north edge to south edge
    # the shadow on the ice under the deck (south of it, the light being north-west)
    for x in range(x0 - 2, x1 + 4):
        h = 9 + int(round(2 * hsh(seed, x // 5, 3)))
        for k in range(h):
            y = y1 + 3 + k
            if y < H:
                a[y, x] = C('slate_cool', 1) if k < h - 3 else C('sky_cool', 2)
    # the deck: planks across the way
    x = x0
    k = 0
    while x < x1:
        w = int(rng.integers(5, 7))
        tone = 4 if k % 3 == 0 else 3
        for xx in range(x, min(x1, x + w)):
            u = xx - x
            for yy in range(y0, y1):
                if u == w - 1:
                    c = C('timber_cool', 1)                                   # the gap between planks
                elif u == 0:
                    c = C('timber', min(5, tone + 1))                         # the plank's lit west arris
                else:
                    g = hsh(seed + k, xx, (yy + int(hsh(seed, k) * 9)) // 5)
                    c = C('timber', tone) if g > 0.3 else (C('timber_cool', tone) if g > 0.1 else C('timber', tone - 1))
                a[yy, xx] = c
        for yy in (y0 + 3, y1 - 4):                                           # nail heads at the joists
            a[yy, x + 1] = C('iron', 2)
        x += w
        k += 1
    # the trodden track: packed snow along the deck, its edges ragged, bootprints in it
    for xx in range(x0, x1):
        t0 = y0 + 10 + int(round(2 * hsh(seed, xx // 4, 5)))
        t1 = y1 - 9 - int(round(2 * hsh(seed, xx // 4, 6)))
        for yy in range(t0, t1):
            g = hsh(seed, (xx + yy * 3) // 4, yy)
            a[yy, xx] = (C('snow', 4) if (yy - t0) == 0 else C('snow_cool', 3) if g > 0.82 else
                         C('snow', 3) if g > 0.55 else C('snow_cool', 4))
        a[t1, xx] = C('sky_cool', 4)
    for xx in range(x0 + 6, x1 - 6, 9):
        yy = y0 + 13 + (xx // 9) % 2 * 4
        a[yy:yy + 2, xx:xx + 3] = C('snow_cool', 3)
    # snow lying on the deck along the north kerb, and lodged in the plank gaps
    for xx in range(x0, x1):
        h = 3 + int(round(3 * hsh(seed, xx // 5, 7)))
        for yy in range(y0, y0 + h):
            a[yy, xx] = (C('snow', 5) if yy == y0 else C('snow_cool', 2) if yy == y0 + h - 1 else
                         C('snow_cool', 3) if yy == y0 + h - 2 else
                         C('snow', 4) if hsh(seed, xx // 3, yy) > 0.35 else C('snow_cool', 4))
        if a[y0 + h, xx] >= 0 and a[y0 + h, xx] // 8 in (FI['timber'], FI['timber_cool']):
            a[y0 + h, xx] = C('timber', 5)
    # the kerbs: logs seen from above on short posts; the south one over the deck's dark edge
    for (yr, north) in ((y0 - 4, True), (y1 - 1, False)):
        for xx in range(x0 - 3, x1 + 3):
            a[yr, xx] = C('timber', 4)
            a[yr + 1, xx] = C('timber', 3)
            a[yr + 2, xx] = C('timber_cool', 2)
            if north:
                a[yr - 1, xx] = C('snow', 5) if hsh(seed, xx // 3, 9) > 0.3 else C('snow', 4)
        for xp in range(x0 + 2, x1, 20):
            a[yr - 2:yr + 3, xp:xp + 3] = C('timber_cool', 1)
            a[yr - 2, xp:xp + 3] = C('snow', 5)
            a[yr - 1, xp] = C('timber', 4)
        if not north:
            for d in range(3):
                a[yr + 3 + d, x0 - 2:x1 + 2] = C('timber_cool', 1) if d < 2 else C('timber_cool', 0)
    # the abutments: laid stones set into the banks, seen from above, their tops under snow
    for (xa, xb) in ((0, x0 + 1), (x1 - 1, W)):
        y = y0 - 8
        row = 0
        while y < y1 + 8:
            hh = int(rng.integers(5, 8))
            x = xa - (3 if row % 2 else 0)
            while x < xb:
                w = int(rng.integers(5, 9))
                for yy in range(y, min(y + hh, y1 + 8)):
                    for xx in range(max(xa, x), min(xb, x + w)):
                        r_ = yy - y
                        if xx == x + w - 1 or r_ == hh - 1:
                            c = C('slate_cool', 0)
                        elif r_ < hh - 3:
                            c = C('slate', 4) if xx < x + w - 2 else C('slate', 3)      # the stone's top
                        else:
                            c = C('slate_cool', 2)                                     # its face, in shade
                        a[yy, xx] = c
                x += w
            y += hh
            row += 1
        for xx in range(xa, xb):
            h = 4 + int(round(4 * hsh(seed, xx // 3, 11)))
            for yy in range(y0 - 8, y0 - 8 + h):
                a[yy, xx] = C('snow', 5) if yy == y0 - 8 else C('snow', 4)
            a[y0 - 8 + h, xx] = C('snow_cool', 3)
    V.outline(a)
    pic = V.Pic(W, H, W // 2, H - 1)
    pic.a[:] = a
    return pic


# ------------------------------------------------------------------------------------------------
# open water in a frozen country (Matt's review of round 3): still water freezes first and fast water
# last, so the outlet is ice with a narrow dark lead of running water down its middle
# ------------------------------------------------------------------------------------------------
LEAD_WATER = [C('slate_cool', 1), C('slate', 1), C('slate_cool', 2), C('slate', 2), C('sky_cool', 2)]


def _lead_mask(H, W, seed, width=(5.0, 9.0), close=(), ends=True):
    """A lead's open water down a picture H tall: a channel that meanders a texel or two, swells and
    narrows, pinched shut at its ends (and where `close` lists rows, an ice bridge across it)."""
    rng = np.random.default_rng(seed)
    yy = np.arange(H)
    cx = W / 2.0 + 1.6 * np.sin(yy / 11.0 + rng.uniform(0, 6)) + 0.8 * np.sin(yy / 4.3 + rng.uniform(0, 6))
    w = width[0] + (width[1] - width[0]) * (0.5 + 0.5 * np.sin(yy / 9.0 + rng.uniform(0, 6)))
    if ends:
        taper = np.clip(np.minimum(yy + 1, H - yy) / 9.0, 0, 1)
        w = w * taper
    for (c0, c1) in close:
        w[c0:c1] = 0
    w = ndi.uniform_filter1d(w, 3)
    L = np.round(cx - w / 2).astype(int)
    R = np.round(cx + w / 2).astype(int)
    m = np.zeros((H, W), bool)
    for y in range(H):
        if R[y] - L[y] >= 2:
            m[y, max(0, L[y]):min(W, R[y])] = True
    return m


def _paint_lead(a, m, seed):
    """Open water under shelf ice: a calm dark centre, lighter shallows at its edges, a faint line of
    current; the shelf's snow-covered lip round it (lit on the west and north), the lip's shadow
    lying on the water under its south-facing edges, and a stone breaking the ice here and there."""
    H, W = a.shape
    Y, X = np.mgrid[0:H, 0:W]
    dist = ndi.distance_transform_edt(m)
    a[m] = np.where(dist[m] <= 1, C('sky_cool', 2), np.where(dist[m] <= 2, C('slate', 2), C('slate_cool', 1)))
    cur = m & (dist >= 2) & ((X + (Y // 7)) % 5 == 0) & (K.vhash(X, Y // 4, seed) > 0.55)
    a[cur] = C('slate', 2)
    l1 = ndi.binary_dilation(m, iterations=1) & ~m
    grow = K.vhash(X // 3, Y // 3, seed + 3) > 0.45
    lip = l1 | (ndi.binary_dilation(l1, iterations=1) & ~m & grow)
    lip2 = ndi.binary_dilation(lip, iterations=1) & ~m & ~lip & (K.vhash(X // 2, Y // 3, seed + 4) > 0.4)
    north = lip & np.roll(m, -1, 0) & ~np.roll(m, 1, 0)
    a[lip] = C('snow', 4)
    a[lip & np.roll(m, 1, 1)] = C('snow_cool', 3)                       # the east lip, facing west in shade
    a[lip & np.roll(m, -1, 1)] = C('snow', 5)                           # the west lip, lit
    a[lip2] = C('snow_cool', 4)
    shade = m & np.roll(lip, 1, 0) & (dist <= 2)                         # the lip's shadow on the water
    a[shade] = C('slate_cool', 0)
    a[north] = C('snow', 5)
    del seed


def lead(kind='run', seed=137):
    """A lead of open water in the frozen outlet (ground dressing laid on the ice): `run` three cells
    long, `short` two, `long` four with an ice bridge, `pool` the fall's plunge pool, half open under
    an ice rim with rime from the spray, `gap` the inflow's one dark gap."""
    if kind == 'pool':
        H, W = 2 * 24 + 6, 3 * 24 + 6
        a = np.full((H, W), -1, np.int32)
        Y, X = np.mgrid[0:H, 0:W]
        nz = ndi.gaussian_filter(np.random.default_rng(seed).random((H, W)), 3.0)
        nz = (nz - nz.mean()) / (nz.std() + 1e-9)
        d = ((X - W / 2) / (W / 2 - 3)) ** 2 + ((Y - H / 2) / (H / 2 - 3)) ** 2 + 0.12 * nz
        # the pool under the fall: open where the water lands (its north half), the ice shelf grown
        # over its south half with a ragged edge, rime from the spray on the shelf
        open_ = (d < 0.8) & (Y < H * 0.52 + 4 * np.sin(X / 7.0) + 2 * nz)
        _paint_lead(a, open_, seed)
        shelf = (d < 1.0) & ~open_ & (a < 0)
        g = K.vhash((X + Y // 4) // 4, Y // 3, seed + 5)
        a[shelf] = np.where(g[shelf] > 0.8, C('snow', 5), np.where(g[shelf] > 0.3, C('snow_cool', 4), C('sky_cool', 5)))
        return _pic(a)
    if kind in ('strip', 'strip_long'):
        # laid over a one-cell channel of the kit's water: the shelf ice grown in from both sides
        # covers the cell to its edges, the lead open down its middle and running off the zone's edge
        H, W = (60 if kind == 'strip' else 120), 24
        m = _lead_mask(H, W, seed + H, (6.0, 10.0), ends=False)
        a = np.full((H, W), -1, np.int32)
        _paint_lead(a, m, seed)
        Y, X = np.mgrid[0:H, 0:W]
        shelf = a < 0
        g = K.vhash((X + Y // 4) // 4, Y // 3, seed + 6)
        a[shelf] = np.where(g[shelf] > 0.85, C('sky_cool', 5), np.where(g[shelf] > 0.45, C('water_cool', 4), C('sky_cool', 4)))
        return _pic(a)
    if kind == 'gap':
        H, W = 24, 16
        m = _lead_mask(H, W, seed, (3.0, 5.0))
    else:
        H = {'short': 48, 'run': 72, 'long': 96}[kind]
        W = 24
        close = ((44, 52),) if kind == 'long' else ()
        m = _lead_mask(H, W, seed + H, (5.0, 10.0), close=close)
    a = np.full((H, W), -1, np.int32)
    _paint_lead(a, m, seed)
    return _pic(a)


def _pic(a):
    H, W = a.shape
    p = V.Pic(W, H, W // 2, H - 1)
    p.a[:] = a
    return p


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


def FACE_LOOKS(base):
    """The face's looks (round 3, R2-F1): three plain runs that differ block for block, so no two
    neighbours match, and the ends for a tier's real ends only."""
    return [('plain', (False, False), base + 5), ('plain_b', (False, False), base + 17), ('plain_c', (False, False), base + 29),
            ('west', (True, False), base + 4), ('east', (False, True), base + 4), ('both', (True, True), base + 4)]


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
        ('frost_spruce', [('still', lambda: conifer('spruce', load=1.0))], dict(
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
        ('frost_krummholz', [('still', lambda: conifer('krummholz', load=0.8)), ('low', lambda: conifer('krummholz_b', load=0.8)),
                             ('wide', lambda: conifer('krummholz_c', load=0.8))], dict(
            name='Krummholz', cells=(4, 2), fp=B._fp(3, 1), collision={'shape': 'rect', 'rect': [-9.0, -4.0, 18, 4]},
            size_class='conifer (krummholz: a wind-flattened spruce at the tree line)', fn='conifer',
            note='A pine at the tree line grown low and wide, snow on its tiers.', **trees)),
        ('frost_snag', [('still', lambda: snag())], dict(
            name='Dead pine', cells=(2, 2), fp=B._fp(1, 1), collision={'shape': 'rect', 'rect': [-3.0, -3.0, 6, 3]},
            size_class='snag (a dead spruce, its crown gone)', fn='snag',
            note='A weathered dead pine with a broken top and two stub limbs, snow on the break and the stubs.', **trees)),
        ('frost_boulder', [('a', lambda: boulder('a')), ('b', lambda: boulder('b', seed=46))], dict(
            name='Granite boulder', purpose='mark', role='rock', cells=(3, 2), fp=B._fp(2, 1),
            collision={'shape': 'rect', 'rect': [-6.0, -5.0, 12, 5]}, shadow=(6.0, 2.0), composition='cluster',
            forbids=NATURE, size_class='boulder (a Frostline granite boulder)', eastward='13 (the boulder, 0.35 x 0.42 A)',
            fn='boulder', note='A granite boulder of two or three facetted masses, a snow cap on its top plane, a west drift.')),
        ('frost_boulder_large', [('still', lambda: boulder('large', seed=45))], dict(
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
            collision={'shape': 'rect', 'rect': [-24.0, -14.0, 48, 14]}, shadow=(24.0, 4.0), composition='edge',
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
            name='Ice saw, axe and shovel', purpose='work', role='story', cells=(2, 1), fp=B._fp(2, 1),
            collision={'shape': 'rect', 'rect': [-5.0, -3.0, 10, 3]}, shadow=(5.0, 1.5), composition='edge',
            requires=[NEAR_HUT], forbids=NATURE, size_class='tall_furniture (skis, a shovel and an axe stood in a rack against the wall, 0.9 A)', eastward='17', fn='hut_tools',
            note='The warden\'s ice saw, felling axe and snow shovel leaning on a plank rack by the hut, snow on their tops.')),
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
        ('frost_rockface', [(v, (lambda e=e, sd=sd: rockface(6, sd, ends=e))) for v, e, sd in FACE_LOOKS(101)], dict(
            name='Granite face', purpose='exclude', role='rock', cells=(6, 5), fp=[[c, r] for c in range(-3, 3) for r in range(-4, 0)],
            collision={'shape': 'rect', 'rect': [-24.0, -32.0, 48, 32]}, shadow=None, composition='edge', forbids=NATURE,
            size_class='unsized (a 32 world px face, one Frostline tier: size guide "faces 32 in rock with snow lips")',
            eastward='12 (the cliff faces)', fn='rockface',
            note='A south granite face 32 world px high (Eastward 12\'s block cliff): stratified granite blocks with lit '
                 'tops, shaded undersides, dark joints, snow on the ledges, a snow lip over the top and a stony foot; three '
                 'plain looks that tile into one face, and ends (west, east, both) for a tier\'s real ends.')),
        ('frost_rockface_short', [(v, (lambda e=e, sd=sd: rockface(4, sd, ends=e))) for v, e, sd in FACE_LOOKS(211)], dict(
            name='Granite face, short', purpose='exclude', role='rock', cells=(4, 5),
            fp=[[c, r] for c in range(-2, 2) for r in range(-4, 0)],
            collision={'shape': 'rect', 'rect': [-16.0, -32.0, 32, 32]}, shadow=None, composition='edge', forbids=NATURE,
            size_class='unsized (a 32 world px face)', eastward='12', fn='rockface', note='A four-cell length of the face.')),
        ('frost_icefall', [('still', lambda: rockface_fall())], dict(
            name='Frozen fall', purpose='exclude', role='rock', cells=(4, 5), fp=[[c, r] for c in range(-2, 2) for r in range(-4, 0)],
            collision={'shape': 'rect', 'rect': [-16.0, -32.0, 32, 32]}, shadow=None, composition='edge',
            size_class='unsized (a fall frozen over the face)', eastward='-', fn='rockface_fall',
            note='The tarn\'s outlet frozen over the face: bulging columns of ice that merge into curtains, lit on the '
                 'west and blue in the east, icicles at the lip, an apron at the foot.')),
        ('frost_rock_stair', [('still', lambda: rock_stair())], dict(
            name='Granite stair', purpose='climb', role='rock_steps', cells=(5, 5), fp=[], blocks=False,
            collision={'shape': 'none'}, shadow=None, composition='axis', z_sort='ground',
            size_class='unsized (rough steps cut up the granite face: no stair kind in the guide; 40 world px wide, at least 34)', eastward='12 (the stairs)', fn='rock_stair',
            note='Six steps of laid granite up the face, lit noses over shaded risers, snow in the tread corners, the '
                 'trod worn into the middle, cheeks of the face either side: the Col Path\'s way up the cirque\'s step.')),
        ('frost_lead', [(v, (lambda v=v: lead(v))) for v in ('run', 'short', 'pool', 'gap', 'strip', 'strip_long')], dict(
            name='Open lead in the ice', purpose='mark', role='water', cells=(1, 3), fp=[], blocks=False,
            collision={'shape': 'none'}, shadow=None, composition='axis', z_sort='ground',
            size_class='unsized (open water in a frozen stream: ground dressing laid on the ice)', eastward='-', fn='lead',
            note='Running water left open down the middle of the frozen outlet: a calm dark centre, lighter shallows, '
                 'the shelf ice\'s snow-covered lip round it and its shadow on the water; the fall\'s plunge pool, half '
                 'open under an ice rim; the inflow\'s one dark gap.')),
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
