"""The Brackens' ground: heath, peat and the stony drove road, as new kit materials (additive: no
existing material, transition or bake changes, so every existing ground and its hash stays).

    python3 -m scripts.art.kit.sets.moor        # writes the terrain and transition pieces (kept unless --force)

**The editor's tiles.** Each material is a terrain piece whose `fill` is one of the kit's existing
periodic fills with its own arguments (scripts/art/kit/fills.py, unchanged): heath a dark, cool,
calm `lawn`; peat a dark `dirt`; the drove road a stony `dirt`. Their transitions use the kit's
existing edge painters (edges.sunken, edges.plain). `python3 -m scripts.art.kit.build` builds them
into game/kit/terrain/ like any material.

**The painted ground.** `terrain.paint` names the painters here. bake.py dispatches only on the
painters it knows (dirt, scree, water) and paints the rest as lawn; teaching it new ones would
change its source and so every baked zone's input hash. So a plan using the moor is baked as it is
(the drove road is a `dirt` recipe and bakes natively, with its sunken edges), and `dress` then
paints the moor over the bake: heather clumps in purple-brown, bilberry green, bleached grass
tussocks, sheep trods as narrow worn lines, gritstone outcrops breaking through, peat hags with
their dark faces and pools, and the drove road's ruts and grass middle. Pieces' cast shadows are
read from a second bake without the pieces and laid back over the moor two ramp steps down, so
nothing loses its shadow. A zone that ships on the moor needs bake.py to call `dress` (one hook);
that change moves every bake's hash, so it waits for its own PR.
"""
from __future__ import annotations

import argparse
import math
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

from scripts.art.kit.schema import PIECES
from scripts.art.kit.sets import _common as K
from scripts.art.kit.sets._common import C, hsh, rpaint
from scripts.art.native import village as V
from scripts.art.native.palette import to_rgba

STANDARD = "eastward-edges.md 5.1 and 5.5, art-style.md density 3; the Brackens brief (heather, peat, gritstone)"
BIOMES = ['brackens']


def _terrain(mid, name, mat_id, priority, surface, route, fill, paint, nav, note):
    return {
        'schema': 'napattack.piece/1', 'id': mid, 'name': name, 'kind': 'terrain', 'biomes': list(BIOMES), 'version': 1,
        'approval': {'state': 'candidate', 'by': None, 'at': None, 'standard': STANDARD, 'note': note},
        'terrain': {'material_id': mat_id, 'priority': priority,
                    'fill': {'module': 'scripts.art.kit.fills', 'fn': fill[0], 'args': fill[1]},
                    'walkable': True, 'surface': surface, 'route': route, 'water': None, 'swatch': [96, 96], 'paint': paint},
        'placement': {'snap': 'cell'},
        'gameplay': {'blocks_move': False, 'blocks_shots': False, 'nav_cost': nav},
        'audit': {'painter': {'module': paint['module'], 'fn': paint['fn'], 'args': paint.get('args', {})}, 'size_class': 'ground',
                  'eastward_ref': 'Eastward 12 (the long grass, the stepping stones), 15 (the marsh), 37 (the lawn); refs local only'},
    }


def _transition(upper, lower, fn, dressing=None, note=''):
    return {
        'schema': 'napattack.piece/1', 'id': '%s_over_%s' % (upper, lower), 'name': '%s over %s' % (upper.capitalize(), lower),
        'kind': 'transition', 'biomes': list(BIOMES), 'version': 1,
        'approval': {'state': 'candidate', 'by': None, 'at': None, 'standard': STANDARD, 'note': note},
        'transition': {'upper': upper, 'lower': lower, 'painter': {'module': 'scripts.art.kit.edges', 'fn': fn,
                                                                    'args': {'fray': True} if fn == 'sunken' else {}},
                       'variants': 1, 'shape': 'lower', 'dressing': dressing},
        'audit': {'painter': {'module': 'scripts.art.kit.sets.moor', 'fn': 'dress', 'args': {}},
                  'eastward_ref': 'Eastward 12 and 13, crops 10-grass-dirt'},
    }


SUNKEN_DRESS = {'density': 0.6, 'south': ['tuft_0', 'tuft_1', 'tuft_2', 'tuft_3', 'pebble_0'],
                'north': ['blades_0', 'blades_1', 'pebble_1', 'pebble_2'], 'side': ['pebble_0', 'pebble_1', 'tuft_2']}
DROVE_PAINT = {'module': 'scripts.art.native.softground', 'fn': 'dirt',
               'args': {'seed': 1303, 'fam': 'path', 'cell': 13, 'stones': 2.4, 'shape': {'seed': 1304, 'smooth': 3}}}


def pieces():
    t = [
        _terrain('heath', 'Heather moor', 8, 29, 'turf', False,
                 ('lawn', {'seed': 1301, 'fam': 'leaf', 'base': 2, 'lush': 0.6, 'flowers': 0.2, 'mottle': 4.0}),
                 {'module': 'scripts.art.kit.sets.moor', 'fn': 'heath', 'args': {'seed': 1301}}, 1.1,
                 'Heather, bilberry and bleached grass over peaty ground, sheep trods and gritstone breaking through '
                 '(painted by sets/moor.dress; the editor tile is a dark lawn fill).'),
        _terrain('peat', 'Peat hag', 9, 18, 'earth', False,
                 ('dirt', {'seed': 1302, 'fam': 'earth', 'cell': 10.0, 'stones': 0.1, 'joints': 0.6, 'lit': 0.3, 'blades': 0.2}),
                 {'module': 'scripts.art.kit.sets.moor', 'fn': 'peat', 'args': {'seed': 1302}}, 1.3,
                 'Bare peat where the heath has eroded: a dark face under the heather\'s lip, fibrous peat, black pools.'),
        _terrain('drove', 'Drove road', 10, 19, 'earth', True,
                 ('dirt', {'seed': 1303, 'fam': 'path', 'cell': 13.0, 'stones': 2.4, 'joints': 0.5, 'lit': 0.5, 'blades': 0.8}),
                 DROVE_PAINT, 0.8,
                 'A stony drove road: packed earth and stones (the bake\'s dirt), two ruts with puddles and grass along '
                 'the middle (sets/moor.dress).'),
    ]
    tr = [
        _transition('heath', 'drove', 'sunken', SUNKEN_DRESS, 'The heath\'s lip over the road\'s verge.'),
        _transition('heath', 'path', 'sunken', SUNKEN_DRESS, 'The heath over a trod.'),
        _transition('heath', 'worn', 'sunken', SUNKEN_DRESS, 'The heath over trodden ground.'),
        _transition('heath', 'peat', 'sunken', None, 'The hag\'s edge: heath over the bare peat below it.'),
        _transition('lawn', 'heath', 'plain', None, 'Grazed grass (a fold\'s floor) meeting the heath.'),
        _transition('path', 'drove', 'plain', None, 'A trod joining the road.'),
        _transition('worn', 'drove', 'plain', None, 'Trodden ground at the road\'s side.'),
    ]
    return t, tr


def write_pieces(force=False):
    t, tr = pieces()
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


# ------------------------------------------------------------------------------------------------
# the painters (over a baked ground, in palette codes)
# ------------------------------------------------------------------------------------------------
HEATHER = [('soot', 'dusk_cool', 'dusk_cool'), ('soot', 'earth_cool', 'dusk_cool'), ('dusk_cool', 'earth_cool', 'earth_cool')]
BILBERRY = [('soot', 'leaf_cool', 'grass_cool'), ('leaf_cool', 'grass_cool', 'leaf')]
GRIT = [('stone_cool', 'stone_warm', 'ashlar_warm'), ('earth_cool', 'stone_warm', 'ashlar_warm'), ('stone_cool', 'stone', 'ashlar')]
BLEACHED = [('earth_cool', 'sand_cool', 'sand_cool'), ('earth_cool', 'earth', 'sand_cool')]


def _ellipse(H, W, cx, cy, rx, ry):
    Y, X = np.mgrid[0:H, 0:W] + 0.5
    return ((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2


def _win(H, W, cx, cy, rx, ry, pad=2):
    """The window round an ellipse: (slices, X, Y) for painting it without touching the whole canvas."""
    y0, y1 = max(0, int(cy - ry) - pad), min(H, int(cy + ry) + pad + 1)
    x0, x1 = max(0, int(cx - rx) - pad), min(W, int(cx + rx) + pad + 1)
    Y, X = np.mgrid[y0:y1, x0:x1] + 0.5
    return (slice(y0, y1), slice(x0, x1)), X, Y


def heath(cv, m, seed, keep=None):
    """Heather moor over mask m, calm at a distance and busy only close to: a dark mottled ground of
    short grass and peaty soil; heather in beds of merged clumps (dusky purple-brown, lit mauve on
    their upper west, tucked dark under their lower rim, a shadow east and down, a few lilac flower
    heads); bilberry in smaller green patches; bleached grass tussocks scattered in the open turf."""
    H, W = cv.shape
    rng = np.random.default_rng(seed)
    n1 = K.noise((H, W), rng, 7.0)
    n2 = K.noise((H, W), rng, 3.0)
    beds = K.noise((H, W), rng, 16.0)
    t = 2.2 + np.round((n1 - 0.5) * 2.0) * 0.5
    rpaint(cv, m, [('soot', 'grass_cool', 'grass_cool'), ('earth_cool', 'grass_cool', 'leaf_cool'), ('soot', 'earth_cool', 'grass_cool')],
           t, np.where(n2 > 0.8, 0.9, np.where(n1 < 0.25, 0.5, 0.1)))
    ok = m.copy() if keep is None else (m & ~keep)
    sp = 9
    cands = []
    for gy in range(0, H + sp, sp):
        for gx in range(0, W + sp, sp):
            cx = gx + (hsh(seed, gx, gy, 1) - 0.5) * sp * 0.8 + (sp / 2 if (gy // sp) % 2 else 0)
            cy = gy + (hsh(seed, gx, gy, 2) - 0.5) * sp * 0.7
            if not (0 <= cx < W and 0 <= cy < H) or not ok[int(cy), int(cx)]:
                continue
            b = beds[int(cy), int(cx)]
            r = hsh(seed, gx, gy, 3)
            if b < 0.42:
                kind = 'heather' if r < 0.95 else None
            elif b < 0.56:
                kind = 'bilberry' if r < 0.6 else ('heather' if r < 0.8 else None)
            else:
                kind = 'tussock' if r < 0.16 else None
            if kind:
                cands.append((cy, cx, kind, hsh(seed, gx, gy, 4)))
    veg = np.zeros((H, W), bool)
    # the clumps' shadows first, on the open ground only (a bed reads as one mass, not pebbles)
    for cy, cx, kind, h in cands:
        if kind == 'tussock':
            continue
        rx = (6.5 + 2.5 * h) if kind == 'heather' else (4.5 + 1.5 * h)
        ry = rx * 0.6
        (sy, sx), X, Y = _win(H, W, cx + 2, cy + 2, rx, ry)
        veg[sy, sx] |= ((((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2) <= 1.0) & ok[sy, sx]
    shadow = np.zeros((H, W), bool)
    shadow[2:, 2:] = veg[:-2, :-2]
    V._step(cv, shadow & ~veg & ok, -1)
    for cy, cx, kind, h in sorted(cands):
        if kind == 'tussock':
            _tussock(cv, ok & ~veg, cx, cy, h)
            continue
        rx = (6.5 + 2.5 * h) if kind == 'heather' else (4.5 + 1.5 * h)
        ry = rx * 0.6
        (sy, sx), X, Y = _win(H, W, cx + 2, cy + 2, rx, ry)
        sub, okw = cv[sy, sx], ok[sy, sx]
        d = ((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2
        th = np.arctan2((Y - cy) / ry, (X - cx) / rx)
        ph = h * 6.28
        d = d * (1 + 0.16 * np.sin(5 * th + ph) + 0.09 * np.sin(9 * th + 2 * ph))   # a lumpy outline
        body = (d <= 1.0) & okw
        if not body.any():
            continue
        lam = -0.6 * (X - cx) / rx - 0.75 * (Y - cy) / ry
        Xi, Yi = X.astype(int), Y.astype(int)
        sprig = K.vhash(Xi // 2, Yi // 2, int(h * 997))           # sprigs in 2 x 2 clusters
        if kind == 'heather':
            tt = 2.4 + 1.2 * lam - 0.8 * ((d > 0.7) & (Y > cy + ry * 0.3))
            tt = tt + 1.0 * ((sprig > 0.78) & (lam > -0.1)) - 1.0 * ((sprig < 0.16) & (lam < 0.3))
            rpaint(sub, body, HEATHER, tt, h)
            if h > 0.45:                                 # lilac flower heads on the lit crown
                fl = body & (lam > 0.25) & (sprig > 0.9)
                sub[fl] = C('dusk_cool', 4)
        else:
            tt = 2.4 + 1.3 * lam - 1.0 * ((d > 0.6) & (Y > cy)) + 1.0 * ((sprig > 0.8) & (lam > 0))
            rpaint(sub, body, BILBERRY, tt, h)
    return cv


def _tussock(cv, ok, cx, cy, h):
    """A bleached grass tussock: a dark root, upright blades two texels wide fanning from it, their
    tips pale."""
    H, W = cv.shape
    n = 5 + int(h * 3)
    for k in range(n):
        x = int(cx - n / 2.0 + k)
        ht = 6 + int(hsh(int(cx), int(cy), k, 7) * 4) - abs(k - n // 2)
        lean = (k - n / 2.0) * 0.8
        fam = BLEACHED[int(h * 2) % 2]
        for j in range(ht):
            yy = int(cy) - j
            xx = int(round(x + lean * j / max(1, ht)))
            t = 1 if j < 2 else (4 if (j >= ht - 3 and k % 2 == 0) else 3)
            col = C(fam[0] if t <= 1 else (fam[2] if t >= 4 else fam[1]), t)
            if 0 <= yy < H and 0 <= xx < W and ok[yy, xx]:
                cv[yy, xx] = col


def trod_mask(shape, pts, width=5):
    """A trod's ground: the polyline densified and wandering a texel or two, `width` across.
    Returns (mask, core)."""
    H, W = shape
    m = np.zeros((H, W), bool)
    core = np.zeros((H, W), bool)
    q = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        L = max(1.0, math.hypot(x1 - x0, y1 - y0))
        nx, ny = -(y1 - y0) / L, (x1 - x0) / L
        for k in range(int(L // 10)):
            u = k * 10 / L
            w = 1.8 * math.sin(0.11 * (x0 + u * (x1 - x0)) + 0.07 * (y0 + u * (y1 - y0)))
            q.append((x0 + u * (x1 - x0) + nx * w, y0 + u * (y1 - y0) + ny * w))
    q.append(tuple(pts[-1]))
    for (x0, y0), (x1, y1) in zip(q, q[1:]):
        m |= V.seg_mask((H, W), x0, y0, x1, y1, width / 2.0)
        core |= V.seg_mask((H, W), x0, y0, x1, y1, max(1.0, width / 2.0 - 1.5))
    return m, core


def trod(cv, mask, core, seed=0):
    """A sheep trod: a narrow worn line through the heather, short grazed grass at its sides and bare
    earth along its middle, lit where a hoof has scuffed it."""
    H, W = cv.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    rpaint(cv, mask & ~core, [('grass_cool', 'grass_cool', 'grass')], 2.6, 0.0)
    bare = core & (K.vhash(Xg // 3, Yg // 2, seed + 11) > 0.25)
    rpaint(cv, core & ~bare, [('grass_cool', 'grass_cool', 'grass')], 2.2, 0.0)
    rpaint(cv, bare, [('earth_cool', 'earth', 'earth')], 2.6 + 0.8 * (K.vhash(Xg // 2, Yg, seed + 12) > 0.75), 0.0)
    return mask


def peat_shape(m, seed):
    """A hag's ragged outline inside its cells: the edge pulled in by noise so the peat breaks
    through the heath, not as a block."""
    H, W = m.shape
    dist = ndi.distance_transform_edt(m)
    n = K.noise((H, W), np.random.default_rng(seed + 9), 5.0)
    n = K.noise((H, W), np.random.default_rng(seed + 9), 9.0)
    return m & (dist + (n - 0.5) * 44 > 12)


def peat(cv, m, seed):
    """A peat hag: bare black-brown peat with fibres and a black pool; along its north edge the
    heather's lip over a dark face of cut peat, uneven in height, roots hanging in it; its south
    edge a lit rim of turf."""
    H, W = cv.shape
    rng = np.random.default_rng(seed)
    n1 = K.noise((H, W), rng, 3.0)
    rpaint(cv, m, [('soot', 'earth_cool', 'earth_cool'), ('soot', 'soot', 'earth_cool')], 1.5 + np.round((n1 - 0.5) * 2) * 0.5, n1)
    Yg, Xg = np.mgrid[0:H, 0:W]
    fib = m & (K.vhash(Xg // 4, Yg, seed) > 0.9)
    cv[fib] = C('earth_cool', 2)
    # the face under the north lip: 4 to 8 rows below the heath, darker, with roots
    hgt = 4 + np.round(K.noise((1, W), np.random.default_rng(seed + 4), 4.0)[0] * 4).astype(int)
    above = np.zeros((H, W), bool)
    for k in range(1, 9):
        sel = np.zeros((H, W), bool)
        sel[k:] = ~m[:-k]
        above |= sel & (k <= hgt)[None, :]
    face = m & above
    rpaint(cv, face, [('soot', 'soot', 'earth_cool')], 0.9 + 0.6 * ((Xg % 5) < 2), 0.0)
    roots = face & (K.vhash(Xg // 2, Yg // 3, seed + 1) > 0.86)
    cv[roots] = C('earth_cool', 2)
    lip2 = np.zeros((H, W), bool)
    lip2[:-1] = m[1:] & ~m[:-1]
    cv[lip2 & (cv >= 0)] = C('grass_cool', 3)
    # a black pool in the middle of each hag
    lab, n = ndi.label(m & ~ndi.binary_dilation(face, iterations=2))
    for k in range(1, n + 1):
        ys, xs = np.nonzero(lab == k)
        if len(ys) < 160:
            continue
        cy, cx = ys.mean(), xs.mean()
        pool = (_ellipse(H, W, cx, cy, 9, 3.5) <= 1.0) & (lab == k)
        rpaint(cv, pool, [('void', 'water_cool', 'water_cool')], 1.0, 0.0)
        g = pool & (np.abs(Yg - int(cy - 1)) < 1) & (np.abs(Xg - int(cx - 3)) < 2)
        cv[g] = C('sky', 3)
    # the south rim: the turf below the hag catches the light
    south = ~m & np.roll(m, 1, 0)
    cv[south & (cv >= 0) & (cv % 8 < 5)] += 1
    return cv


def drove_dress(cv, net, seed):
    """The drove road over its baked packed earth: two ruts worn by carts, damp, a puddle here and
    there, and grass along the middle where no wheel or hoof goes; stones kicked to the sides."""
    H, W = cv.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    cols = net.any(0)
    top = np.where(cols, np.argmax(net, 0), 0)
    bot = np.where(cols, H - np.argmax(net[::-1], 0), 0)
    mid = (top + bot) / 2.0
    hw = (bot - top) / 2.0
    off = Yg - mid[None, :]
    rel = off / np.maximum(1.0, hw[None, :])
    rut = net & (np.abs(np.abs(rel) - 0.42) < 0.12)
    rpaint(cv, rut, [('earth_cool', 'earth_cool', 'path')], 1.6 + (K.vhash(Xg // 3, Yg // 2, seed) > 0.7) * 0.8, 0.0)
    lip = net & ~rut & np.roll(rut, -1, 0) & (rel < 0)
    cv[lip] = C('path', 4)
    # puddles in the ruts
    for x0 in range(0, W, 41):
        if hsh(seed, x0, 1) > 0.5:
            continue
        cx = x0 + int(hsh(seed, x0, 2) * 15)
        if cx >= W or not cols[cx]:
            continue
        for sgn in (-1, 1):
            if hsh(seed, x0, sgn, 3) > 0.5:
                continue
            cy = mid[cx] + sgn * hw[cx] * 0.42
            pud = (_ellipse(H, W, cx, cy, 7 + hsh(seed, x0, 4) * 5, 2.2) <= 1.0) & net
            rpaint(cv, pud, [('water_cool', 'water_cool', 'water')], 1.6 + (Yg > cy) * 0.8, 0.0)
            cv[pud & (Yg == int(round(cy))) & (np.abs(Xg - cx + 3) < 3)] = C('sky', 4)
    # the grass in the middle: clumps two texels across, thicker where the road is wide
    midg = net & (np.abs(rel) < 0.17 + 0.05 * (K.vhash(Xg // 3, Yg // 2, seed + 7) > 0.5)) & (K.vhash(Xg // 3, Yg // 2, seed + 5) > 0.12)
    rpaint(cv, midg, [('grass_cool', 'grass_cool', 'grass'), ('grass_cool', 'grass', 'grass_warm')],
           2.6 + 0.8 * (K.vhash(Xg // 2, Yg // 2, seed + 6) > 0.6), 0.4)
    # stones to the verges: 3 x 2 lit on top, a dark foot
    for j in range(int(net.sum() / 260)):
        x, y = int(hsh(seed, j, 7) * W), int(hsh(seed, j, 8) * H)
        if 0 < y < H - 3 and 0 < x < W - 4 and net[y, x] and abs((y - mid[x]) / max(1, hw[x])) > 0.62:
            cv[y, x:x + 3] = C('stone', 4)
            cv[y + 1, x:x + 3] = C('stone', 3)
            cv[y + 2, x:x + 3] = C('stone_cool', 1)
    return cv


def outcrop(rx, ry, seed):
    """A gritstone outcrop breaking through the turf: a few flat lichened slabs, low, as a ground
    piece (its own outline, a cast shadow east and down). Returns (codes, ox, oy)."""
    rng = np.random.default_rng(seed)
    sc = K.Scene(-rx - 6, rx + 8, -ry - 6, ry + 6, 14)
    for k in range(4 + int(rx / 6)):
        x = rng.uniform(-rx * 0.6, rx * 0.6)
        y = rng.uniform(-ry * 0.5, ry * 0.5)
        r = rng.uniform(4.0, 7.0)
        sc.ellipsoid(x, y, 0.6, r, r * 0.7, rng.uniform(2.5, 4.0), GRIT, base=2.5 + rng.uniform(-0.4, 0.5), k=1.8,
                     tag='stone', mix=rng.random(), flat=2.2)
    sc.render()
    a = sc.shade(crevice=1, rim=0.6)
    for i in range(len(sc.solids)):
        ys, xs = np.nonzero(sc.label == i)
        if len(ys) > 10 and hsh(seed, i) < 0.6:
            k = int(hsh(seed, i, 2) * len(ys))
            y, x = ys[k], xs[k]
            if y + 1 < a.shape[0] and x + 1 < a.shape[1] and (sc.label[y:y + 2, x:x + 2] == i).all():
                a[y:y + 2, x:x + 2] = C('brass', 4) if hsh(seed, i, 3) > 0.5 else C('sand_cool', 5)
    K.despeckle(a)
    V.outline(a)
    return a, sc.ox, sc.oy


def mat_px(mat, h, w):
    """The plan's material per texel."""
    return np.repeat(np.repeat(mat, h // mat.shape[0], 0), w // mat.shape[1], 1)


def dress(plan, img_with, img_without, lib=None):
    """Paint the moor over a baked plan (img_with: the bake; img_without: the bake of the same plan
    with no pieces, whose difference is the pieces' shadows and low items). Returns an RGBA image."""
    from scripts.art.kit import bake as BK
    lib = lib or BK._pieces_lib()
    rows = plan['rows']
    R, Cn = len(rows), len(rows[0])
    h, w = R * K.CELL, Cn * K.CELL
    mat = np.array([[plan['legend'].get(c, '') for c in r] for r in rows])
    base = np.asarray(img_with.convert('RGBA')).copy()
    plain = np.asarray(img_without.convert('RGBA'))
    lum = lambda im: im[..., :3].astype(float) @ np.array([0.3, 0.59, 0.11])   # noqa: E731
    shadow = (np.abs(base[..., :3].astype(int) - plain[..., :3].astype(int)).sum(-1) > 0) & (lum(base) < lum(plain) * 0.95)
    cv = np.full((h, w), -1, np.int32)
    paint_mask = np.zeros((h, w), bool)
    # the routes' outlines as the bake drew them, and the verge kept round them (their lips)
    routes = np.zeros((h, w), bool)
    for m_id, p in BK.material_paints(mat.ravel(), lib).items():
        if p.get('fn') == 'dirt':
            routes |= BK._shape(mat == m_id, h, w, p.get('args', {}).get('shape', {}))
    verge = ndi.binary_dilation(routes, iterations=5) & ~routes
    # the verge's outer turf as grazed moor grass (the bake's lip, two texels, stays)
    outer = verge & ~ndi.binary_dilation(routes, iterations=2) & (mat_px(mat, h, w) == 'heath')
    nv = K.noise((h, w), np.random.default_rng(77), 3.0)
    rpaint(cv, outer, [('grass_cool', 'grass_cool', 'grass')], 2.4 + np.round((nv - 0.5) * 2) * 0.5, 0.0)
    paint_mask |= outer
    shapes = {}
    for m_id in ('heath', 'peat'):
        if m_id not in lib or not (mat == m_id).any():
            continue
        a = lib[m_id]['terrain']['paint'].get('args', {})
        shapes[m_id] = (BK._shape(mat == m_id, h, w, {'seed': a.get('seed', 41), 'r_out': 0.6, 'r_in': 0.4}) & ~routes & ~verge,
                        a.get('seed', 41))
    hag = np.zeros((h, w), bool)
    if 'peat' in shapes:
        pm, ps = shapes['peat']
        hag = peat_shape(pm, ps)
    heath_m = np.zeros((h, w), bool)
    if 'heath' in shapes:
        heath_m = shapes['heath'][0]
    if 'peat' in shapes:
        heath_m = heath_m | (shapes['peat'][0] & ~hag)          # the heath round a hag's ragged edge
    trods = np.zeros((h, w), bool)
    cores = np.zeros((h, w), bool)
    for t in plan.get('trods', []):
        tm, tc = trod_mask((h, w), t)
        trods |= tm & heath_m
        cores |= tc & heath_m
    if heath_m.any():
        heath(cv, heath_m, shapes.get('heath', (None, 1301))[1], keep=trods)
        paint_mask |= heath_m
    if hag.any():
        peat(cv, hag, shapes['peat'][1])
        paint_mask |= hag
    if trods.any():
        trod(cv, trods, cores)
    for k, (x, y, rx, ry) in enumerate(plan.get('outcrops', [])):
        a_, ox, oy = outcrop(rx, ry, 1400 + k)
        hh, ww = a_.shape
        x0, y0 = int(x - ox), int(y - oy)
        sub = cv[y0:y0 + hh, x0:x0 + ww]
        sel = a_[:sub.shape[0], :sub.shape[1]] >= 0
        shd = np.zeros_like(sel)
        shd[2:, 3:] = sel[:-2, :-3]
        shd &= ~sel & (sub >= 0)
        V._step(sub, shd, -2)
        sub[sel] = a_[:sub.shape[0], :sub.shape[1]][sel]
        paint_mask[y0:y0 + hh, x0:x0 + ww] |= sel | shd
    if 'drove' in lib and (mat == 'drove').any():
        dp = lib['drove']['terrain']['paint'].get('args', {})
        net = BK._shape(mat == 'drove', h, w, dp.get('shape', {}))
        # start from the bake's own packed earth, read back as codes is not possible (RGB), so the
        # ruts, puddles, grass and stones are drawn alone and laid over it
        road = np.full((h, w), -1, np.int32)
        sub = np.full((h, w), C('path', 3), np.int32)
        drove_dress(sub, net, dp.get('seed', 1303))
        changed = net & (sub != C('path', 3))
        road[changed] = sub[changed]
        cv = np.where(road >= 0, road, cv)
        paint_mask |= changed
    # the pieces' shadows laid back over what was painted: two ramp steps down
    sel = paint_mask & shadow & (cv >= 0)
    V._step(cv, sel, -2)
    out = base.copy()
    rgba = to_rgba(np.maximum(cv, 0))
    pm = paint_mask & (cv >= 0) & ~((shadow) & ~sel & paint_mask)
    out[pm] = rgba[pm]
    # keep the pieces' low items drawn into the bake (where the bake differs and is not a shadow)
    items = (np.abs(base[..., :3].astype(int) - plain[..., :3].astype(int)).sum(-1) > 0) & ~shadow
    out[items] = base[items]
    return Image.fromarray(out, 'RGBA')


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--force', action='store_true')
    a = ap.parse_args(argv)
    print('moor: %d pieces written' % write_pieces(force=a.force))
    return 0


if __name__ == '__main__':
    sys.exit(main())

