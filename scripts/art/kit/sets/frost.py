"""The Frostline set (docs/vision/regions/home-valley-frostline-brackens.md; the Frostline zone,
game/kit/zones/frostline.json): the ground and props the Col hut's cirque needs, drawn to the
Brackens bar with the Brackens' renderer and helpers (scripts/art/kit/sets/brackens.py, _common.py).

**Ground** (additive, as the moor's: no existing material, transition or bake hash moves):

- `snow`: lying snow, the cirque's floor. The kit's periodic `lawn` fill in the snow ramps (a calm
  field, soft cool hollows, lit drifts, a few dead grass blades through it);
- `snow_trod`: the Col Path trodden into the snow, the kit's `dirt` fill in the snow ramps (packed
  clods of snow, a few stones kicked up);
- transitions: the snow's soft lip over the trod, the scree and the tarn's bank.

Like the moor's, the Frostline's ground shows the editor's live tiles: bake.py dispatches only on
the painters it knows, and teaching it snow moves every baked zone's hash (its own PR).

**Props.** Snow lies on whatever faces the sky (frost_props.py, 18 Oct): `snow_on` lays it on a
picture's tops, as a lumpy cap with a lit upper west, its body, a cool lower edge and a shadow
under its lip, so the valley's approved pictures carry it without being redrawn.

- the Col hut: a stone bothy under slate (the house builder, scripts/art/native/houses.py, as the
  mill), snow lying on the roof to a ragged line above the eave, icicles, a drift against its foot,
  the stove's smoke looping over the pot (8 frames);
- the snowy pine: the woodland's pine (approved, 9 Nov) with snow on its boughs, two loads;
- the snowy boulder: the woodland's boulders with a snow cap;
- the snowy cairn: the Brackens' cairn under snow, a waymark on the Col Path;
- the ice-cutter's sledge: a plank sledge on two runners, three cut blocks of lake ice roped on it,
  the saw leaning against it.

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
# the valley's pictures the snow is laid on (approved or candidate: the source keeps its own record)
SOURCES = {
    'pine': os.path.join(ROOT, 'game', 'zones', 'woodland', 'art', 'pine.png'),
    'boulder_0': os.path.join(ROOT, 'game', 'kit', 'props', 'art', 'woodland_boulder_0.png'),
    'boulder_1': os.path.join(ROOT, 'game', 'kit', 'props', 'art', 'woodland_boulder_1.png'),
    'cairn': os.path.join(ROOT, 'game', 'kit', 'props', 'art', 'brackens', 'brackens_cairn_standing.png'),
}
OAK = B.OAK
ICE = [('water_cool', 'sky_cool', 'sky'), ('water_cool', 'water', 'sky_cool')]
ROPE = [('earth_cool', 'sand_cool', 'sand_warm')]
IRON = [('soot', 'iron', 'stone_cool')]


# ================================================================================================
# snow
# ================================================================================================
def codes_of(path: str) -> V.Pic:
    """A house picture (RGBA on the house palette) back in codes, its foot the middle of its bottom
    row, as the woodland's generator places it (screen.foot_at_bottom_centre)."""
    im = np.asarray(Image.open(path).convert('RGBA'))
    lut = {}
    for i in range(len(LUT) - 1, -1, -1):
        lut[tuple(int(v) for v in LUT[i])] = i
    H, W = im.shape[:2]
    p = V.Pic(W, H, W // 2, H - 1)
    for y, x in zip(*np.nonzero(im[..., 3] > 0)):
        p.a[y, x] = lut[tuple(int(v) for v in im[y, x, :3])]
    return p


def _grow(p: V.Pic, top: int, side: int = 0) -> V.Pic:
    """The same picture on a canvas `top` texels taller (and `side` wider each side), so snow can
    lie above its old silhouette."""
    q = V.Pic(p.W + 2 * side, p.H + top, p.ax + side, p.ay + top)
    q.a[top:, side:side + p.W] = p.a
    return q


def snow_on(a: np.ndarray, seed: int, depth=(2, 4), mound=0.55, where=None, inner=True, keep=None) -> np.ndarray:
    """Lay snow on the picture's sky-facing tops, in place; returns the snow's mask.

    A top is an opaque texel with nothing above it (the silhouette) or, with `inner`, one whose
    texel above is two tones darker in a foliage or stone ramp (a bough or a ledge over its own
    shadow). From each top the snow runs down `depth` texels (a lumpy run per column, hashed in
    pairs so it lies in soft clumps), and on the silhouette it heaps up to two texels above it in
    rounded mounds (`mound` of the columns). Tones: a lit upper west, a body, the cool lower edge
    and a one-texel shadow under the lip on what it lies on. `where` limits it; `keep` is never
    painted."""
    H, W = a.shape
    op = a >= 0
    above = np.full_like(a, -1)
    above[1:] = a[:-1]
    top = op & (above < 0)
    if inner:
        fa, ta = above // 8, above % 8
        f, t = a // 8, a % 8
        ramps = [FI[n] for n in ('leaf', 'leaf_cool', 'leaf_warm', 'grass', 'grass_cool', 'grass_warm')]
        darker = (above >= 0) & np.isin(fa, ramps) & np.isin(f, ramps) & (ta + 1 <= t) & (t >= 3)
        # a bough's top lies in a run of at least three texels: the snow lies in clumps, never specks
        darker = ndi.binary_opening(darker, structure=np.ones((1, 3), bool))
        top |= op & darker
    if where is not None:
        top &= where
    if keep is not None:
        top &= ~keep
    rng = np.random.default_rng(seed)
    Yg, Xg = np.mgrid[0:H, 0:W]
    run = depth[0] + np.floor(K.vhash(Xg // 2, Yg // 3, seed + 1) * (depth[1] - depth[0] + 1)).astype(int)
    snow = np.zeros((H, W), bool)
    lvl = np.zeros((H, W), int)              # texels below the snow's top
    for y, x in zip(*np.nonzero(top)):
        n = run[y, x]
        for k in range(n):
            yy = y + k
            if yy >= H or a[yy, x] < 0 or (keep is not None and keep[yy, x]):
                break
            if not snow[yy, x]:
                snow[yy, x] = True
                lvl[yy, x] = k
    # mounds above the silhouette, rounded: a column heaps one texel where its neighbours do too
    heap = np.zeros((H, W), bool)
    sil = top & (above < 0)
    hq = K.vhash(Xg // 3, Yg // 4, seed + 2)
    for y, x in zip(*np.nonzero(sil)):
        if hq[y, x] < mound and y >= 1 and a[y - 1, x] < 0:
            heap[y - 1, x] = True
            if hq[y, x] < mound * 0.45 and y >= 2 and a[y - 2, x] < 0:
                heap[y - 2, x] = True
    # a heap texel needs a neighbour in its row (no single spikes)
    row_nb = np.zeros_like(heap)
    row_nb[:, 1:] |= heap[:, :-1]
    row_nb[:, :-1] |= heap[:, 1:]
    heap &= row_nb
    snow |= heap
    lvl[heap] = 0
    # the shadow under the lip, on what the snow lies on
    under = np.zeros((H, W), bool)
    under[1:] = snow[:-1]
    under &= op & ~snow
    if keep is not None:
        under &= ~keep
    # tones: lit west and top, the body, the cool lower edge
    lowest = np.zeros((H, W), bool)
    lowest[:-1] = snow[:-1] & ~snow[1:]
    lowest[-1] = snow[-1]
    westlit = np.zeros((H, W), bool)
    westlit[:, 1:] = snow[:, 1:] & ~snow[:, :-1]
    q = K.vhash(Xg // 2, Yg // 2, seed + 3)
    tone = np.where(lvl == 0, 5, 4)
    tone = np.where(westlit, 5, tone)
    tone = np.where(lowest & (lvl > 0), 3, tone)
    fam = np.where(lowest & (lvl > 0), FI['snow_cool'], np.where(q > 0.82, FI['snow_warm'], FI['snow']))
    # the east third of each picture's snow cools a tone (the light is from the upper left)
    xs = np.nonzero(snow.any(0))[0]
    if xs.size:
        x0, x1 = xs.min(), xs.max()
        east = Xg > x0 + (x1 - x0) * 0.68
        tone = np.where(east & (lvl > 0), tone - 1, tone)
        fam = np.where(east & (q < 0.45), FI['snow_cool'], fam)
    codes = fam * 8 + np.clip(tone, 1, 5)
    a[snow] = codes[snow]
    V._step(a, under, -1)
    # the snow's own outline on its free side (above and west of a heap or a top that was the edge)
    o = np.where(snow | heap, a, -1)
    V.outline(o)
    edge = (o >= 0) & (a < 0)
    a[edge] = C('snow_cool', 2)
    snow |= edge
    del rng
    return snow


def icicles(a: np.ndarray, row: np.ndarray, seed: int, rate=0.35, length=(2, 6)) -> None:
    """Icicles hanging from the texels marked in `row` (a lip): one texel wide, lit at their root,
    every few texels."""
    H, W = a.shape
    for y, x in zip(*np.nonzero(row)):
        hv = hsh(seed, x // 2, y)
        if x % 2 or hv > rate:
            continue
        n = length[0] + int(hsh(seed + 1, x, y) * (length[1] - length[0] + 1))
        for k in range(1, n + 1):
            yy = y + k
            if yy >= H:
                break
            a[yy, x] = C('snow', 5) if k == 1 else (C('sky_cool', 4) if k < n else C('sky_cool', 3))


# ================================================================================================
# the ground
# ================================================================================================
SNOW_FILL = ('lawn', {'seed': 1401, 'fam': 'snow', 'base': 3, 'lush': 0.3, 'flowers': 0.0, 'grain': 0.4, 'mottle': 5.0})
TROD_FILL = ('dirt', {'seed': 1402, 'fam': 'snow', 'cell': 14.0, 'stones': 0.3, 'joints': 0.72, 'lit': 0.5, 'blades': 0.1,
                      'soft_joints': True})


def _terrain(mid, name, mat_id, priority, surface, route, fill, nav, note):
    return {
        'schema': 'napattack.piece/1', 'id': mid, 'name': name, 'kind': 'terrain', 'biomes': list(BIOMES), 'version': 1,
        'approval': {'state': 'candidate', 'by': None, 'at': None, 'standard': STANDARD, 'note': note},
        'terrain': {'material_id': mat_id, 'priority': priority,
                    'fill': {'module': 'scripts.art.kit.fills', 'fn': fill[0], 'args': fill[1]},
                    'walkable': True, 'surface': surface, 'route': route, 'water': None, 'swatch': [96, 96],
                    'paint': {'module': 'scripts.art.kit.sets.frost', 'fn': 'paint_' + mid, 'args': {}}},
        'placement': {'snap': 'cell'},
        'gameplay': {'blocks_move': False, 'blocks_shots': False, 'nav_cost': nav},
        'audit': {'painter': {'module': 'scripts.art.kit.fills', 'fn': fill[0], 'args': fill[1]}, 'size_class': 'ground',
                  'eastward_ref': 'Eastward 22 to 24 (the snowfield, the trodden path); refs local only'},
    }


def _transition(upper, lower, fn, dressing=None, note=''):
    return {
        'schema': 'napattack.piece/1', 'id': '%s_over_%s' % (upper, lower), 'name': '%s over %s' % (upper.capitalize(), lower),
        'kind': 'transition', 'biomes': list(BIOMES), 'version': 1,
        'approval': {'state': 'candidate', 'by': None, 'at': None, 'standard': STANDARD, 'note': note},
        'transition': {'upper': upper, 'lower': lower, 'painter': {'module': 'scripts.art.kit.edges', 'fn': fn,
                                                                    'args': {'fray': True} if fn == 'sunken' else {}},
                       'variants': 1, 'shape': 'lower', 'dressing': dressing},
        'audit': {'painter': {'module': 'scripts.art.kit.edges', 'fn': fn, 'args': {}},
                  'eastward_ref': 'Eastward 22 and 23 (snow over the trod and the shore)'},
    }


STONES = {'density': 0.35, 'south': ['pebble_0', 'pebble_1'], 'north': ['pebble_1', 'pebble_2'], 'side': ['pebble_0']}


def terrain_pieces():
    t = [
        _terrain('snow', 'Lying snow', 13, 31, 'snow', False, SNOW_FILL, 1.2,
                 'The cirque\'s floor: lying snow, calm, soft cool hollows and lit drifts, dead grass blades through it.'),
        _terrain('snow_trod', 'Trodden snow', 14, 22, 'snow', True, TROD_FILL, 0.9,
                 'The Col Path trodden into the snow: packed clods of snow, a few stones kicked up.'),
    ]
    tr = [
        _transition('snow', 'snow_trod', 'sunken', None, 'The snow\'s soft lip over the trodden path.'),
        _transition('snow', 'scree', 'sunken', STONES, 'Snow lying over the moraine\'s stones.'),
        _transition('snow', 'water', 'bank', STONES, 'The tarn\'s shore under snow.'),
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


def paint_snow_trod(cv, m, seed=0, **_kw):
    """The trod's painted ground for a future bake hook: its periodic fill laid by world position."""
    _fill_into(cv, m, TROD_FILL)


# ================================================================================================
# the props
# ================================================================================================
HUT_SPEC = dict(kind='hut', w=64, depth=34, wall_h=30, roof_h=22, wall='stone', roof='slate', paint='timber',
                doors=[[22, 'timber']], door_w=14, door_h=24, windows=[46], win_w=10, win_h=10, win_top=22,
                shutters=False, slate_calm=True, eave_dark=True, roof_moss=0, roof_lichen=0, chimney=[52],
                chimney_w=7, chimney_h=12)


def col_hut(seed=31):
    """The Col hut: a stone bothy under slate built by the house builder (as the mill), snow lying on
    the roof down to a ragged line two thirds of the way to the eave with slate showing below it,
    icicles off the eave, snow capping the chimney and the bargeboards' feet, a drift banked against
    the wall's foot, and the stove's smoke looping over the pot (the still has none)."""
    from scripts.art.native import houses as HS
    b = HS.building(HUT_SPEC, seed=seed)
    p = _grow(b.base, 6, 4)
    a = p.a
    H, W = a.shape
    rm = np.zeros((H, W), bool)
    rm[6:, 4:4 + b.base.W] = b.info['roof']
    y_r, y_e = b.info['y_r'] + 6, b.info['y_eave'] + 6
    Yg, Xg = np.mgrid[0:H, 0:W]
    # the chimney: the stone (and its clay pot) standing in the roof's span, every row of it
    stoneish = np.isin(a // 8, [FI[n] for n in ('stone', 'stone_cool', 'stone_warm', 'ashlar', 'ashlar_warm')])
    chim_cols = (stoneish & (Yg < y_r + 4)).sum(0) > 4
    chim_cols = ndi.binary_dilation(chim_cols, iterations=1)
    chim = chim_cols[None, :] & (Yg < y_e)
    rm &= ~chim
    rows = np.nonzero(rm.any(1))[0]
    cols = np.nonzero(rm.any(0))[0]
    # the roof's snow: everything above a ragged line, a slow lumpy profile along the eave
    xs1 = np.arange(W, dtype=float)
    prof = ndi.gaussian_filter1d(np.random.default_rng(seed + 5).random(W), 5.0, mode='wrap')
    prof = (prof - prof.mean()) / (prof.std() + 1e-9)
    wave = 0.62 + 0.06 * prof + 0.03 * np.sin(xs1 / 13.0 + 0.7)
    line = y_r + (y_e - y_r) * wave[None, :]
    cover = rm & (Yg < line)
    # the ridge and the finials above the roof's top row (not the chimney)
    ridge = (a >= 0) & (Yg < rows.min() + 3) & (Xg >= cols.min() - 4) & (Xg <= cols.max() + 4) & ~chim
    cover |= ridge
    lv = (Yg - y_r) / max(1, (y_e - y_r))
    # broad soft swells drawn out along the slope (wind-laid snow), no specks: a lit crown, the body,
    # cooler bands lower down and toward the east gable
    sw_ = ndi.gaussian_filter(np.random.default_rng(seed + 6).random((H, W)), (1.2, 6.0))
    sw_ = (sw_ - sw_.mean()) / (sw_.std() + 1e-9)
    tone = np.where(lv < 0.1, 5, 4) + (sw_ > 0.9) - (sw_ < -0.8) - (lv > 0.5)
    eastm = Xg > cols.min() + 0.72 * (cols.max() - cols.min())
    fam = np.where(eastm | (sw_ < -0.4), FI['snow_cool'], np.where(sw_ > 1.3, FI['snow_warm'], FI['snow']))
    tone = np.where(eastm, tone - 0, tone)
    codes = fam * 8 + np.clip(tone, 2, 5)
    a[cover] = codes[cover]
    # its top: a lit row along the ridge and the snow's own edge tone above it
    topr = cover & ~np.roll(cover, 1, 0)
    a[topr & ~chim] = C('snow', 5)
    # the snow's lower edge: a cool row, then the slate under it in shadow
    low = cover & ~np.roll(cover, -1, 0)
    a[low] = C('snow_cool', 3)
    shade = np.roll(low, 1, 0) & rm & ~cover
    V._step(a, shade, -1)
    # snow lying along each course of slate below the line (a lit texel on the course's top)
    course = rm & ~cover & ~shade & (np.roll(a, 1, 0) // 8 == a // 8) & (K.vhash(Xg // 3, Yg, seed + 7) > 0.78)
    course &= (a // 8 == FI['slate']) | (a // 8 == FI['slate_cool']) | (a // 8 == FI['slate_warm'])
    course &= np.roll(a, 1, 0) % 8 < a % 8
    a[course] = C('snow', 4)
    # caps on the chimney, the bargeboards' feet and the sill; nothing on the walls' faces
    snow_on(a, seed + 8, depth=(2, 3), mound=0.6, where=Yg < y_e + 2, inner=False, keep=cover)
    # icicles from the eave's lowest row
    eave = np.zeros((H, W), bool)
    er = min(H - 1, y_e + 1)
    for x in range(cols.min(), cols.max() + 1):
        ys_ = np.nonzero(rm[:, x])[0]
        if ys_.size:
            y = ys_.max() + 1
            while y < H and a[y, x] >= 0 and a[y, x] // 8 in (FI['timber'], FI['timber_cool'], FI['timber_warm'],
                                                               FI['slate'], FI['slate_cool'], FI['iron']):
                y += 1
            if y < H:
                eave[y - 1, x] = True
    del er
    icicles(a, eave, seed + 9)
    # a drift against the wall's foot: a low bank of snow, highest at the corners, the door kept clear
    foot = p.ay
    L, R = b.info['L'] + 4, b.info['R'] + 4
    door_x = [L + V.q(d) for d, _p in HUT_SPEC['doors']]
    for x in range(L - 3, R + 4):
        clear = any(dx - 3 <= x <= dx + V.q(HUT_SPEC['door_w']) + 2 for dx in door_x)
        h = 0 if clear else int(3 + 4 * (abs((x - (L + R) / 2.0) / ((R - L) / 2.0 + 3)) ** 2) + 2 * hsh(seed, x // 3, 1))
        for k in range(h):
            y = foot - k
            if 0 <= y < H and 0 <= x < W:
                a[y, x] = C('snow', 5 if k == h - 1 else 4) if k > 0 else C('snow_cool', 3)
    p.a = a
    V.tidy(p.a)
    q_ = K.crop(p.a, p.ax, p.ay)
    # the stove's smoke over the pot (the Brackens' smoke frames)
    pots = b.info.get('pots') or []
    if pots:
        px, py = pots[0]
        pot_x, pot_y = int(px + 4 - p.ax + q_.ax), int(py + 6 - p.ay + q_.ay)
    else:
        pot_x, pot_y = q_.W - 20, 6
    sw, sh = B.SMOKE_BOX
    up = max(0, sh - pot_y + 2)
    east = max(0, pot_x - 6 + sw - q_.W)
    r = V.Pic(q_.W + east, q_.H + up, q_.ax, q_.ay + up)
    r.a[up:, :q_.W] = q_.a
    region = (pot_x - 6, pot_y + up - sh, sw, sh)
    frames = [V.Pic(sw, sh, 0, sh) for _ in range(B.SMOKE_FRAMES)]
    for i, fr in enumerate(frames):
        fr.a[:] = B._smoke_frame(i, seed)
    return r, {'frames': frames, 'fps': 6.0, 'clip': 'smoke', 'region': region}


def pine(load='heavy', seed=41):
    """The woodland's pine with snow on its boughs: `heavy` on every bough top, `light` on the upper
    boughs and the silhouette only."""
    p = _grow(codes_of(SOURCES['pine']), 3)
    H = p.H
    where = None
    if load == 'light':
        Yg = np.mgrid[0:H, 0:p.W][0]
        where = Yg < H * 0.62
    snow_on(p.a, seed, depth=(2, 4) if load == 'heavy' else (1, 3), mound=0.6 if load == 'heavy' else 0.4,
            where=where, inner=True)
    V.tidy(p.a)
    return p


def boulder(which=0, seed=43):
    """A woodland boulder with snow lying on its top."""
    p = _grow(codes_of(SOURCES['boulder_%d' % which]), 3)
    snow_on(p.a, seed + which, depth=(3, 5), mound=0.7, inner=False)
    V.tidy(p.a)
    return p


def cairn(seed=47):
    """The Brackens' cairn with snow on each ring's top and a cap on the upright."""
    p = _grow(codes_of(SOURCES['cairn']), 3)
    snow_on(p.a, seed, depth=(1, 3), mound=0.5, inner=False)
    # each ring's ledge holds a little snow too: a stone texel under a darker crevice row
    Yg = np.mgrid[0:p.H, 0:p.W][0]
    a = p.a
    above = np.full_like(a, -1)
    above[1:] = a[:-1]
    stone = (a >= 0) & np.isin(a // 8, [FI['stone'], FI['stone_warm'], FI['ashlar'], FI['ashlar_warm'], FI['sand_warm']])
    ledge = stone & (above >= 0) & (above % 8 + 2 <= a % 8) & (K.vhash(np.mgrid[0:p.H, 0:p.W][1] // 2, Yg, seed + 1) > 0.35)
    a[ledge] = C('snow', 4)
    V.tidy(p.a)
    return p


def sledge(seed=53):
    """The ice-cutter's sledge: two curled runners, a plank bed on short posts, three blocks of lake ice
    roped on it (clear blue-grey with lit edges and a frosted top), the bow saw leaning on its east
    end."""
    sc = K.Scene(-40, 40, -22, 14, 80)
    # runners: long low boxes, their fronts curled up (a stacked rise at the west end)
    for y0 in (-13.0, 2.0):
        sc.box(-30, y0, 0, 30, y0 + 3, 3, OAK, base=2.4, k=1.5, tag='runner', round_=1.0)
        sc.box(-34, y0, 2, -29, y0 + 3, 7, OAK, base=2.6, k=1.5, tag='runner', round_=1.5)
        sc.box(-37, y0, 6, -33, y0 + 3, 10, OAK, base=2.8, k=1.5, tag='runner', round_=1.5)
    for x in (-22, 0, 22):                      # posts
        for y0 in (-13.0, 2.0):
            sc.box(x - 2, y0, 3, x + 2, y0 + 3, 8, OAK, base=2.0, k=1.4, tag='post')
    sc.box(-28, -14, 8, 28, 6, 11, OAK, base=2.8, k=1.6, tag='bed', round_=0.8, tex='wood')
    # three cut blocks of ice
    blocks = [(-25, -10, -10, 13, 12), (-7, -12, 7, 15, 10), (10, -9, 25, 12, 13)]
    for k, (x0, y0, x1, y1, h) in enumerate(blocks):
        sc.box(x0, y0, 11, x1, y0 + y1, 11 + h, ICE, base=3.4, k=1.3, tag='ice', round_=1.5, mix=0.25 * k)
    # the rope over them
    sc.box(-27, -3, 11, 24, -1, 30, ROPE, base=2.6, k=1.4, tag='rope_bed')
    # the saw: a bow frame leaning on the east end
    sc.box(29, -3, 4, 31, 0, 34, OAK, base=2.6, k=1.4, tag='saw')
    sc.box(31, -3, 30, 38, 0, 33, OAK, base=2.6, k=1.4, tag='saw')
    sc.box(36, -3, 6, 38, 0, 33, IRON, base=2.4, k=1.4, tag='blade')
    sc.render()
    a = sc.shade(crevice=1.0, rim=0.6)
    H, W = a.shape
    lab = sc.label
    tagm = {t: np.isin(lab, [i for i, s_ in enumerate(sc.solids) if s_.tag == t]) for t in ('ice', 'rope_bed', 'bed')}
    # the rope: only a two-texel band where it crosses the ice (it lies over the blocks)
    rope = tagm['rope_bed']
    a[rope & ~ndi.binary_dilation(tagm['ice'], iterations=1)] = -1
    Yg, Xg = np.mgrid[0:H, 0:W]
    keep_rope = rope & ((Xg - sc.ox) % 22 < 2)
    a[rope & ~keep_rope] = -1
    sc.label[rope & ~keep_rope] = -1
    # recompute what shows under the cut rope: the ice (render again without the rope)
    sc2 = K.Scene(-40, 40, -22, 14, 80)
    sc2.solids = [s_ for s_ in sc.solids if s_.tag != 'rope_bed']
    sc2.render()
    a2 = sc2.shade(crevice=1.0, rim=0.6)
    gap = (rope & ~keep_rope)
    a[gap] = a2[gap]
    # the ice: clear, a frosted lit top, inner streaks (refraction), a lit west edge
    ice = (a >= 0) & np.isin(sc2.label, [i for i, s_ in enumerate(sc2.solids) if s_.tag == 'ice']) & ~keep_rope
    up = sc2.n[..., 2] > 0.6 if sc2.n.ndim == 3 and sc2.n.shape[-1] >= 3 else np.zeros((H, W), bool)
    a[ice & up] = np.where(K.vhash(Xg // 3, Yg // 2, seed)[ice & up] > 0.55, C('snow_cool', 4), C('sky_cool', 5))
    streak = ice & ~up & ((Xg + 2 * Yg) % 9 == 0) & (K.vhash(Xg // 3, Yg // 4, seed + 2) > 0.5)
    a[streak] = C('sky', 5)
    K.despeckle(a)
    V.tidy(a)
    V.outline(a)
    return K.crop(a, sc.ox, sc.oy)


# ================================================================================================
# the pieces
# ================================================================================================
def _rel(rel, what, cells=None, note=None):
    return B._rel(rel, what, cells, note)


def _piece(pid, name, variants, size, cells, purpose, role, **kw):
    pc = B._piece(pid, name, variants, size, cells, purpose, role, **kw)
    pc['biomes'] = list(BIOMES)
    pc['approval']['standard'] = STANDARD
    for v in pc['variants']:
        v['png'] = v['png'].replace(B.RES, RES)
    if pc['rendering'].get('animations'):
        for an in pc['rendering']['animations']:
            an['strip'] = an['strip'].replace(B.RES, RES)
    pc['audit']['painter'] = {'module': 'scripts.art.kit.sets.frost', 'fn': kw.get('fn') or pid.replace('frost_', ''), 'args': {}}
    pc['audit']['seeded_from'] = 'scripts/art/kit/sets/frost.py'
    return pc


NATURE = B.NATURE
OFF_ROUTE = B.OFF_ROUTE


def prop_jobs():
    """(piece id, [(variant id, thunk)], piece kwargs)."""
    return [
        ('frost_col_hut', [('still', lambda: col_hut())], dict(
            name='Col hut', purpose='live', role='house', cells=(10, 4), fp=B._fp(9, 3),
            collision={'shape': 'rect', 'rect': [-34.0, -26.0, 68, 26]}, shadow=(64, 9), composition='edge',
            door_cells=[[-1, 0], [0, 0]], doors=[{'x': [-30, 12], 'faces': 's'}],
            requires=[_rel('near', 'route', 3, 'on the Col Path, its door on the trod')], forbids=NATURE,
            extra={'provides': ['home', 'hearth']},
            size_class='hut (148 to 252 tall, 178 to 296 wide: size-guide "stone refuge, shepherd\'s bothy: as a hut")',
            eastward='12 (the stone hut: 2.5 A to the ridge, 3 A wide)', fn='col_hut',
            note='The hut warden\'s bothy on the Col Path: rubble granite under slate, snow on the roof and banked at its '
                 'foot, icicles off the eave, a warm window; the stove\'s smoke loops (8 frames) over the still.')),
        ('frost_pine', [('heavy', lambda: pine('heavy')), ('light', lambda: pine('light'))], dict(
            name='Snowy pine', purpose='grow', role='tree', cells=(4, 2), fp=B._fp(2, 1),
            collision={'shape': 'rect', 'rect': [-5.0, -4.0, 10, 4]}, shadow=(30, 6), composition='cluster',
            forbids=NATURE, size_class='tree (the woodland\'s pine: 79 world px)', eastward='12 (the pines, 3 A)', fn='pine',
            note='The woodland\'s pine (approved 9 Nov, PR #446) with snow lying on its boughs, heavy or light.')),
        ('frost_boulder', [('a', lambda: boulder(0)), ('b', lambda: boulder(1))], dict(
            name='Snowy boulder', purpose='mark', role='rock', cells=(3, 2), fp=B._fp(2, 1),
            collision={'shape': 'rect', 'rect': [-8.0, -6.0, 16, 6]}, shadow=(16, 4), composition='cluster',
            forbids=NATURE, size_class='boulder (the woodland\'s boulders)', eastward='13 (the boulder, 0.35 x 0.42 A)',
            fn='boulder', note='The woodland\'s boulders with a cap of snow: the boulder field below the High Fells.')),
        ('frost_cairn', [('standing', lambda: cairn())], dict(
            name='Snowy cairn', purpose='guide', role='marker', cells=(2, 2), fp=B._fp(2, 1),
            collision={'shape': 'rect', 'rect': [-5.0, -4.0, 10, 4]}, shadow=(12, 3), composition='edge',
            requires=[_rel('near', 'route', 2, 'a waymark beside the Col Path')], extra={'provides': ['feature']},
            forbids=NATURE, size_class='cairn (size-guide: 12 to 28 tall, 12 to 24 wide in world px)', eastward='13 (the boulder)',
            fn='cairn', note='The Brackens\' cairn under snow: a waymark on the Col Path.')),
        ('frost_sledge', [('still', lambda: sledge())], dict(
            name="Ice-cutter's sledge", purpose='work', role='story', cells=(4, 2), fp=B._fp(4, 1),
            collision={'shape': 'rect', 'rect': [-13.0, -6.0, 26, 6]}, shadow=(28, 4), composition='edge',
            requires=[_rel('near', 'water', 4, 'drawn up on the tarn\'s shore, where the ice is cut')], forbids=NATURE,
            size_class='cart (52 to 89 tall, 67 to 126 wide)', eastward='04 (the stall cart), 17 (the farm cart)', fn='sledge',
            note='A plank sledge on curled runners, three blocks of lake ice roped on it and the bow saw leaning on it.')),
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
                anim = {'clip': frames['clip'], 'loop': True, 'frames': len(frames['frames']), 'fps': frames['fps'],
                        'strip': RES + png[:-4] + '_loop.png', 'frame_px': [f0.W, f0.H], 'reduced_motion': 'hold:0',
                        'on_screen_only': True, 'region_px': list(frames['region'])}
                kw['anim'] = anim
        size = (max(r.W for _v, r, _f, _p in pics), max(r.H for _v, r, _f, _p in pics))
        variants = [(vid, w, png, foot) for (vid, w, png, foot) in variants]
        pc = _piece(pid, name, [(v, w, png, f) for v, w, png, f in variants], size, cells, purpose, role, fp=fp, **kw)
        pieces.append(pc)
    if write:
        os.makedirs(ART, exist_ok=True)
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
