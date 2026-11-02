"""The Crossroads cottage slice: four candidate cottages on a north-south road, as a review study.

    python3 -m scripts.art.kit.crossroads_slice OUT.png          # the native frame (960 x 1008)

Claude A's review of PR #416 (1 Nov) asked for six fixes, all made here:
1. no two buildings overlap: plots one cell apart beyond the eaves; rules.building_overlap in
   scripts/review/ground_rules.py checks every plan, and this slice's plan is strict there;
2. the road keeps its width class (three cells: wheel ruts, a grass crown), the spurs are lanes
   two cells wide;
3. each spur leaves its door's centre over a doorstep slab, runs straight south (four cells, past
   the gate), turns once and
   meets the road in a T on the soft grid (cell 8 world px, 24 art px);
4. road and spurs are the woodland kit's packed earth: the slice is a kit plan (cells of
   game/kit/pieces/terrain/path.json) baked by scripts/art/kit/bake.py, the woodland_kit zone's
   bake, so the material, its variants, soft-grid edge and turf lip are the same pixels' recipe;
5. the road's edge is the kit's soft-grid outline (turns at 0.4 cell), its ruts the kit's class-3
   treatment (surface.path_widths) and the crown grown over;
6. every cottage has a plot. Matt, 2 Nov: "what is the point of fences if they don't enclose
   anything?" Each fence now closes a rectangle beside the spur, away from the road: a kitchen
   garden (soil beds with cabbages, leeks, lettuces or carrots) or a paddock (a trough and hay).
   Its runs meet post on post at the corners, its gate is in the side facing the spur, a trodden
   way (a two-cell route) leads from the spur through the gap, and the gate stands open, swung in on
   its north post clear of the way. Front yards stay open. rules.fences in ground_rules.py checks
   that every run closes a loop or ends against a wall and every gate opens onto a route. The
   woodpiles are stacked against the gable walls, the barrels beside the houses, the tubs by the
   doors, a pair of the kit's bushes behind each house. The fence, gate, bed and hay painters are
   in this file (village.py helpers); the other props are candidate kit props.

The cottages are the native HD cottages (houses.py via village.building), unapproved candidates.
Nothing here changes a game rule, a playable zone or the piece library.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import math

import numpy as np
from scipy import ndimage as ndi

from scripts.art.kit.schema import ROOT

D = 3
W_WORLD, H_WORLD = 320, 336          # the review frame: 40 x 42 cells, 960 x 1008 art px
CELL = 8

# the four candidate cottages (the looks of the #416 fixture), door x on a cell line so a two-cell
# spur is centred on it; the east pair stands three cells lower so no two spurs meet the road
# opposite each other (each junction is a T)
LOOK = {"kind": "cottage", "roof": "slate", "w": 64, "depth": 48, "wall_h": 44, "roof_h": 40,
        "chimney_h": 14, "door": 32, "door_h": 32, "door_w": 14, "overhang": 3, "windows": [16, 48],
        "win_w": 13, "win_h": 13, "win_top": 32, "shutters": True, "box": True}
COTTAGES = [
    # id, door (world px), look
    ("cottage_nw", (88, 104), dict(LOOK, wall="stone", paint="berry", chimney=[12], seed=1389)),
    ("cottage_ne", (232, 128), dict(LOOK, wall="frame", paint="brass", posts=[4, 24, 40, 60], chimney=[52], seed=1389)),
    ("cottage_sw", (88, 256), dict(LOOK, wall="frame", paint="dusk", posts=[4, 24, 40, 60], chimney=[52], seed=1390)),
    ("cottage_se", (232, 280), dict(LOOK, wall="frame", paint="sky", posts=[4, 24, 40, 60], chimney=[12], seed=1382)),
]
ROAD_X = 152                         # the road's line: three cells, x 144 to 168
ROAD_W, SPUR_W = 32, 24              # route widths (town.py: cells = (width - 8) / 8)
SPUR_RUN = 40                        # door to the spur's turn: four cells straight (past the gates), then the bend


def _spur(door):
    x, y = door
    turn = y + SPUR_RUN
    return [[x, y + CELL], [x, turn], [ROAD_X, turn]]


# Matt, 2 Nov: "what is the point of fences if they don't enclose anything?" Each plot's fence now
# encloses something with a reason: a kitchen garden (soil beds with crops) or a small paddock (a
# trough and hay), a closed rectangle beside the spur on the side away from the road, its gate in
# the side that faces the spur, opening straight onto the path. Front yards stay open.
# (kind, enclosure x0, y0, x1, y1 as post centres in world px, gate y0, y1 on the spur side)
ENCLOSURE = {
    'cottage_nw': ('garden', (16, 114, 78, 166), (124, 148)),
    'cottage_ne': ('pen', (242, 140, 304, 190), (148, 172)),
    'cottage_sw': ('pen', (16, 266, 78, 318), (276, 300)),
    'cottage_se': ('garden', (242, 290, 304, 334), (300, 324)),
}


def _fences(cid, door):
    """The enclosure's fence lines as (id, kind, a, b) in world px, kind 'fence' or 'gate': the far
    side, north and south runs whole, the spur side split round its gate."""
    _kind, (x0, y0, x1, y1), (g0, g1) = ENCLOSURE[cid]
    west = door[0] < ROAD_X
    xi, xo = (x1, x0) if west else (x0, x1)          # the inner (spur) side and the outer side
    return [(cid + '_fence_n', 'fence', (x0, y0), (x1, y0)),
            (cid + '_fence_s', 'fence', (x0, y1), (x1, y1)),
            (cid + '_fence_o', 'fence', (xo, y0), (xo, y1)),
            (cid + '_fence_i0', 'fence', (xi, y0), (xi, g0)),
            (cid + '_gate', 'gate', (xi, g0), (xi, g1)),
            (cid + '_fence_i1', 'fence', (xi, g1), (xi, y1))]


def _gate_way(cid, door):
    """The trodden way through the gate: two cells wide, from the spur's centre line straight
    through the gap and two cells into the enclosure (a route, so it is baked as the path)."""
    _kind, (x0, _y0, x1, _y1), (g0, g1) = ENCLOSURE[cid]
    west = door[0] < ROAD_X
    gc = (g0 + g1) // 2
    return [[door[0], gc], [x1 - 14 if west else x0 + 14, gc]]


def _plot(cid, door):
    """The plot's props as (id, kind, foot world px, extra): the enclosure's contents, a hedge of the
    kit's bushes behind the house on the outer side, frontage props on grass beside the door."""
    x, y = door
    west = x < ROAD_X
    side = -1 if west else 1
    kind, (x0, y0, x1, y1), (g0, g1) = ENCLOSURE[cid]
    out = []
    xi = x1 if west else x0
    if kind == 'garden':
        # three soil beds in rows, a trodden strip between them and the gate's swing kept clear
        bx0, bx1 = (x0 + 7, xi - 24) if west else (xi + 24, x1 - 7)
        rows = [fy for fy in range(y0 + 13, y1 - 13, 14)]       # the last row clear of the south fence
        crops = ('cabbage', 'leek', 'lettuce') if cid == 'cottage_nw' else ('lettuce', 'carrot')
        for k, fy in enumerate(rows):
            out.append((cid + '_bed_%d' % k, 'bed', ((bx0 + bx1) / 2, fy),
                        dict(w=bx1 - bx0, h=9, crop=crops[k % len(crops)])))
    else:
        # a paddock: the trough along the north fence, hay at the far side
        out.append((cid + '_trough', 'trough', ((x0 + x1) / 2 + side * 8, y0 + 14), {}))
        out.append((cid + '_hay', 'hay', ((x0 + 17) if west else (x1 - 17), y1 - 16), dict(variant=len(cid) % 2)))
    # the gate stands open, swung in on its north post, clear of the way through
    out.append((cid + '_gate_leaf', 'gate_leaf', (xi, g0), dict(w=g1 - g0 - 2, dir=side)))
    # the woodpile is stacked against the house's outer gable wall, under the eaves
    if cid in ('cottage_ne', 'cottage_sw'):
        out.append((cid + '_woodpile', 'woodpile', (x + side * 45, y - 6), dict(variant=0)))
    else:
        out.append((cid + '_barrel', 'barrel', (x - side * 40, y - 4), dict(variant=1)))
    out.append((cid + '_tub', 'flower_tub', (x - side * 17, y + 9), dict(variant=(len(cid) + 3 * west) % 7)))
    hx = 16 if west else W_WORLD - 16
    for k, hy in enumerate((y - 72, y - 46)):
        out.append((cid + '_hedge_%d' % k, 'hedge', (hx, hy), dict(variant=(k + len(cid)) % 7)))
    return out


def plan() -> dict:
    """The slice's plan in world px, the shape scripts/review/ground_rules.py reads: buildings with
    floor, door and look, routes, objects (id, kind, x, y, w, h: foot at the bottom centre)."""
    buildings, looks, routes, objects = [], {}, [], []
    routes.append({'id': 'road', 'kind': 'road', 'width': ROAD_W, 'points': [[ROAD_X, 0], [ROAD_X, H_WORLD]]})
    sizes = {'hedge': (16, 6), 'bed': None, 'flower_tub': (12, 6), 'barrel': (10, 8), 'woodpile': (24, 8),
             'trough': (30, 8), 'hay': (22, 8), 'gate_leaf': (14, 2)}
    fences = []
    for cid, door, look in COTTAGES:
        x, y = door
        buildings.append({'id': cid, 'name': cid.replace('_', ' '), 'rect': [x - 32, y - look['depth'], 64, look['depth']],
                          'door': [x, y]})
        looks[cid] = look
        routes.append({'id': cid + '_spur', 'kind': 'spur', 'width': SPUR_W, 'points': _spur(door)})
        routes.append({'id': cid + '_gate_way', 'kind': 'spur', 'width': SPUR_W, 'points': _gate_way(cid, door)})
        for oid, kind, (fx, fy), ex in _plot(cid, door):
            w, h = sizes[kind] or (ex.get('w', 16), ex.get('h', 6))
            if kind == 'gate_leaf':
                fx += ex['dir'] * w / 2            # the open leaf lies inside, from the hinge post
            objects.append([oid, kind, fx - w / 2, fy - h, w, h])
        fences += [{'id': fid, 'kind': k, 'a': list(a), 'b': list(b)} for fid, k, a, b in _fences(cid, door)]
    return {'id': 'crossroads_slice', 'box': [0, 0, W_WORLD, H_WORLD], 'ground_rules': True,
            'note': 'Review study (scripts/art/kit/crossroads_slice.py), not a playable zone.',
            'buildings': buildings, 'routes': routes, 'objects': objects, 'fences': fences, 'art': {'looks': looks}}


def kit_plan(p: dict) -> dict:
    """The slice as a kit zone plan: lawn and path cells from its routes (softgrid.cells_route, as
    woodland_kit.py lays the woodland's), the doors as context for the path's variants."""
    from scripts.art.native import softgrid as SG
    h, w = H_WORLD * D, W_WORLD * D
    grid = np.full(SG.grid_shape(h, w), '.', '<U1')
    for r in p['routes']:
        n = max(1, int(round((r['width'] - 8) / 8.0)))
        grid[SG.cells_route(r['points'], n, h, w)] = '#'
    return {'zone': 'crossroads_slice', 'legend': {'.': 'lawn', '#': 'path'},
            'rows': [''.join(r) for r in grid], 'pieces': [],
            'spawns': {b['id']: [b['door'][0] * D, b['door'][1] * D] for b in p['buildings']}}


def doorstep(cv: np.ndarray, door) -> None:
    """A flat stone slab at the door's foot (in codes): 16 world px across, 5 deep, its lit top
    worn paler at the middle, a lit north-west edge, a dark front edge and the joint between two
    stones."""
    from scripts.art.native.palette import C
    x, y = door
    x0, x1 = (x - 8) * D + 1, (x + 8) * D - 1
    y0, y1 = y * D, (y + 5) * D
    yy, xx = np.mgrid[y0:y1, x0:x1]
    cut = ((xx == x0) | (xx == x1 - 1)) & ((yy == y0) | (yy == y1 - 1))         # rounded corners
    top = np.full(yy.shape, C('stone', 4), np.int32)
    top[(np.abs(xx - x * D) < 9) & (yy > y0 + 2) & (yy < y1 - 4)] = C('stone_warm', 4)   # worn middle
    top[yy == y0] = C('stone', 5)
    top[xx == x0] = C('stone', 5)
    top[yy >= y1 - 3] = C('stone', 2)                                            # the front face
    top[yy == y1 - 1] = C('stone_cool', 1)
    top[(xx == x * D + 4) & (yy < y1 - 3)] = C('stone', 2)                       # the joint
    sub = cv[y0:y1, x0:x1]
    sub[~cut] = top[~cut]


# ------------------------------------------------------------------------------------------------
# the plot painters: fence runs along x and along y that meet post on post at the corners, the
# gate's posts and its open leaf, soil beds with crops (village.py's helpers, the house light)
# ------------------------------------------------------------------------------------------------
POST, POST_H, GATE_H = 3, 15, 17        # post width, height and gatepost height (world px)
RAILS = (12, 6)                         # rail heights above the ground (world px)


def _canvas(w, h, up):
    from scripts.art.native import village as V
    pad = 4
    pic = V.Pic(V.q(w + 2 * POST) + 2 * pad, V.q(h + up) + 2 * pad, pad + V.q(POST), V.q(h + up) + pad)
    return pic


def _post(a, cx, yb, tall, rng):
    """A square post centred on cx with its foot at row yb (texels): lit top and west face, the east
    side in shade; a gatepost is taller and carries a cap board."""
    from scripts.art.native import village as V
    q = V.q
    x0 = int(round(cx - q(POST) / 2))
    V.prism(a, x0, yb - q(tall), x0 + q(POST), yb, q(1.4), 'timber', 3, side=q(1.1))
    if tall > POST_H:
        V.prism(a, x0 - 1, yb - q(tall) - 2, x0 + q(POST) + 1, yb - q(tall) + 2, 2, 'timber_cool', 3, side=1)


def _fence_h(xa, xb, seed, gate_ends=()):
    """A run along x from post centre xa to xb (world px): posts about 16 px apart, two sawn rails
    nailed across them. Foot (anchor) at (xa, the line)."""
    from scripts.art.native import village as V
    q = V.q
    rng = np.random.default_rng(seed)
    p = _canvas(xb - xa, 0, GATE_H + 3)
    a, ax, yb = p.a, p.ax, p.ay
    n = max(2, int(round((xb - xa) / 16)) + 1)
    xs = [ax + q((xb - xa) * k / (n - 1)) for k in range(n)]
    for yy in RAILS:
        y = yb - q(yy)
        V.board(a, xs[0], y + int(rng.integers(-1, 2)), xs[-1] - xs[0], q(1.8), 0, 'timber_warm', 3, rng)
        sh = V._rect(a.shape, xs[0], y + q(1.8), xs[-1], y + q(2.4)) & (a >= 0)
        a[sh] = np.maximum((a[sh] // 8) * 8, a[sh] - 1)
    for k, x in enumerate(xs):
        _post(a, x, yb, GATE_H if k in gate_ends else POST_H, rng)
        for yy in RAILS:
            V.nail(a, int(x - 1), yb - q(yy) + 2, rng=rng)
    return V.finish(p)


def _fence_v(ya, yb_, seed, gate_ends=()):
    """A run along y from post (ya) to post (yb_) (world px): the posts one behind the other, the
    rails seen end-on to the light: their top edge and lit west face as a strip between the posts
    at each rail's height. Foot (anchor) at the south post."""
    from scripts.art.native import village as V
    q = V.q
    rng = np.random.default_rng(seed)
    L = yb_ - ya
    p = _canvas(0, L, GATE_H + 3)
    a, ax, yb = p.a, p.ax, p.ay
    n = max(2, int(round(L / 14)) + 1)
    ys = [yb - q(L) + q(L * k / (n - 1)) for k in range(n)]
    gate_ends = {0 if g == 0 else n - 1 for g in gate_ends}
    x0 = int(round(ax - q(1.0)))
    for k in range(n):
        if k:                                     # the rails of the bay north of this post
            for yy in RAILS:
                top, bot = ys[k - 1] - q(yy), ys[k] - q(yy) + q(1.8)
                V.board(a, x0, bot, bot - top, q(2.0), -90, 'timber_warm', 3, rng)
        _post(a, ax, ys[k], GATE_H if k in gate_ends else POST_H, rng)
    return V.finish(p)


def _gate_leaf(w, d, seed):
    """The gate standing open inside the enclosure, swung back against nothing: a frame of two
    rails, a stile at each end and a diagonal brace, lying along x from the hinge post (foot at the
    hinge, `d` = +1 east, -1 west)."""
    from scripts.art.native import village as V
    q = V.q
    rng = np.random.default_rng(seed)
    p = _canvas(w, 0, GATE_H)
    if d < 0:
        p.ax = p.W - 1 - p.ax                                  # hinge on the east end, the leaf west of it
    a, ax, yb = p.a, p.ax, p.ay
    xh = ax + q(POST) // 2 * d                                 # the hinge side, at the post's face
    xf = xh + q(w - POST) * d
    l, r = min(xh, xf), max(xh, xf)
    top, bot = yb - q(14), yb - q(3)
    for y in (top, bot - q(1.8)):
        V.board(a, l, y, r - l, q(1.8), 0, 'timber_warm', 3, rng)
    V.bar(a, l + 2, bot - 2, r - 2, top + 3, q(0.7), 'timber', 3) if d > 0 else \
        V.bar(a, l + 2, top + 3, r - 2, bot - 2, q(0.7), 'timber', 3)
    for x in (l, r - q(1.6)):
        V.prism(a, x, top - 1, x + q(1.6), bot, 2, 'timber', 3, side=1)
    return V.finish(p)


def _bed(w, h, crop, seed):
    """A kitchen bed dug into the plot: a low mound of worked soil (lit along its north and west
    rims, its south lip and east end a step down into shade), furrows along it and a row of crops
    on each ridge, every plant lit on its upper left with a speck of shade at its foot."""
    from scripts.art.native import village as V
    q = V.q
    rng = np.random.default_rng(seed)
    p = V._pic(w, h, up=6, side=1)
    a, cx, yb = p.a, p.ax, p.ay
    Y, X = V.grid(a)
    x0, x1, y0 = cx - q(w / 2), cx + q(w / 2), yb - q(h)
    lip = q(1.4)
    rr = q(2.0)
    body = (((X - np.clip(X, x0 + rr, x1 - rr)) / rr) ** 2 + ((Y - np.clip(Y, y0 + rr, yb - rr)) / rr) ** 2 <= 1)
    pn = ndi.gaussian_filter(rng.random(a.shape), 1.4)
    pn = (pn - pn.mean()) / max(1e-6, pn.std())
    nrow = max(1, int(round(h / 4.5)))
    ry = (Y - y0) / max(1.0, (yb - lip - y0) / nrow)
    fr = ry - np.floor(ry)
    t = 3.0 + 0.9 * np.cos(fr * 2 * math.pi + 1.2) + 0.3 * np.clip(pn, -1.5, 1.5)
    t = t + 0.8 * (X < x0 + q(1.2)) + 0.8 * (Y < y0 + q(1.0)) - 0.8 * (X > x1 - q(1.6))
    V.paint(a, body, ('earth_cool', 'earth', 'earth_warm'), t)
    face = body & (Y >= yb - lip)
    V.paint(a, face, ('earth_cool', 'earth', 'earth_warm'), 1.6 - 0.8 * (Y >= yb - 2) - 0.6 * (X > x1 - q(1.6)))
    for _ in range(int(w * h / 10)):                      # clods, lit on their upper left
        px, py = int(rng.uniform(x0 + 3, x1 - 4)), int(rng.uniform(y0 + 3, yb - lip - 3))
        if body[py, px]:
            a[py, px:px + 2] = V.code('earth_warm', 4)
            a[py + 1, px + 1:px + 3] = V.code('earth_cool', 1)
    # the crops, one row per ridge
    for j in range(nrow):
        cy = y0 + (j + 0.45) * (yb - lip - y0) / nrow
        step = {'cabbage': 6.5, 'lettuce': 5.0, 'leek': 3.4, 'carrot': 3.6}[crop]
        k = int((w - 5) // step)
        for i in range(k + 1):
            px = x0 + q(2.5) + (x1 - x0 - q(5)) * i / max(1, k) + int(rng.integers(-1, 2))
            if crop == 'cabbage':
                m = V.ellipse_mask(a.shape, px, cy, q(2.6), q(2.1))
                V.blob(a, m, 'leaf_cool', 3)
                inner = V.ellipse_mask(a.shape, px - 1, cy - 1, q(1.4), q(1.1))
                V.blob(a, inner, 'leaf', 4)
                a[V.ellipse_mask(a.shape, px - 2, cy - 2, q(0.5), q(0.4))] = V.code('leaf_warm', 5)
                a[(np.abs(X - px - 1) < 0.6) & (Y > cy + q(0.4)) & (Y < cy + q(1.8))] = V.code('leaf_cool', 1)
            elif crop == 'lettuce':
                m = V.ellipse_mask(a.shape, px, cy, q(1.9), q(1.5))
                V.blob(a, m, 'leaf_warm', 3)
                a[V.ellipse_mask(a.shape, px - 1, cy - 1, q(0.8), q(0.6))] = V.code('leaf_warm', 5)
            else:
                tall = q(4.2) if crop == 'leek' else q(2.6)
                fam = 'leaf_cool' if crop == 'leek' else 'leaf'
                for dx in (-1.6, 0, 1.6):
                    tip = px + q(dx * (0.8 if crop == 'leek' else 1.0))
                    V.bar(a, px, cy + 1, tip, cy + 1 - tall, 0.9, fam, 3 if dx > 0 else 4)
                if crop == 'carrot':
                    a[V.ellipse_mask(a.shape, px, cy - q(2.2), q(1.4), q(0.9))] = V.code('leaf_warm', 4)
            a[V.ellipse_mask(a.shape, px + 2, cy + q(1.9), q(1.6), q(0.5)) & body] = V.code('earth_cool', 1)
    return V.finish(p)


def _hay(w, h, seed):
    """A heap of loose hay forked out for the stock: a low dome of straw lit on its upper left, its
    east flank and foot in shade, strands lying across it, a few stalks fallen round its foot."""
    from scripts.art.native import village as V
    q = V.q
    rng = np.random.default_rng(seed)
    p = V._pic(w, h, up=9, side=2)
    a, cx, yb = p.a, p.ax, p.ay
    Y, X = V.grid(a)
    rx, ry = q(w / 2), q(h / 2 + 2.5)
    cy = yb - ry
    rough = ndi.gaussian_filter(rng.random(a.shape), 0.7)
    m = (((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2 <= 1 + 0.9 * (rough - 0.5)) & (Y < yb - 1)
    nx, ny = (X - cx) / rx, (Y - cy) / ry
    lit = -0.55 * nx - 0.6 * ny + 0.5 * np.sqrt(np.clip(1 - nx ** 2 - ny ** 2, 0, 1))
    pn = ndi.gaussian_filter(rng.random(a.shape), 0.8)
    V.paint(a, m, ('brass', 'brass_warm', 'sand_warm'), 2.6 + 1.8 * lit + 1.4 * (pn - 0.5))
    for _ in range(int(w * h / 2.5)):                     # strands
        x0, y0 = rng.uniform(cx - rx * 0.9, cx + rx * 0.9), rng.uniform(cy - ry * 0.8, yb - 3)
        ang = rng.uniform(-0.6, 0.6) + (math.pi if rng.random() < 0.5 else 0)
        L = q(rng.uniform(1.5, 3.5))
        ss = [(int(x0 + k * math.cos(ang)), int(y0 + k * math.sin(ang))) for k in range(L)]
        for x_, y_ in ss:
            if 0 <= y_ < a.shape[0] and 0 <= x_ < a.shape[1] and m[y_, x_]:
                a[y_, x_] = V.code('brass', max(1, a[y_, x_] % 8 - 1))
            if 0 <= y_ - 1 < a.shape[0] and 0 <= x_ < a.shape[1] and m[y_ - 1, x_] and rng.random() < 0.5:
                a[y_ - 1, x_] = V.code('sand_warm', min(5, a[y_ - 1, x_] % 8 + 1))
    for _ in range(6):                                    # stalks fallen round the foot
        x0 = rng.uniform(cx - rx * 1.1, cx + rx * 1.1)
        V.bar(a, x0, yb - 1, x0 + q(rng.uniform(-2, 2)), yb - 1 - q(rng.uniform(0, 0.8)), 0.6, 'brass', 3)
    return V.finish(p)


def _sprites(p: dict):
    """(id, image, anchor texels, foot texels) for every building, fence run and prop."""
    from PIL import Image
    from scripts.art.native import village as V

    def kit(piece, variant):
        vs = json.load(open(os.path.join(ROOT, 'game', 'kit', 'pieces', 'prop', piece + '.json')))['variants']
        v = vs[variant % len(vs)]
        img = Image.open(os.path.join(ROOT, 'game', v['png'][len('res://'):])).convert('RGBA')
        return img, tuple(v['foot'])

    def at(x, y):
        return int(round(x * D)), int(round(y * D))

    out = []
    for cid, door, look in COTTAGES:
        b = V.building(dict(look), seed=look['seed'], hd=True)
        out.append((cid, b.base.rgba(), (b.base.ax, b.base.ay), at(*door)))
    for cid, door, _look in COTTAGES:
        fl = _fences(cid, door)
        gate = [(a_, b_) for _f, k, a_, b_ in fl if k == 'gate'][0]
        gends = {tuple(gate[0]), tuple(gate[1])}
        for fid, k, a_, b_ in fl:
            if k == 'gate':
                continue
            seed = sum(map(ord, fid))
            ge = [i for i, e in enumerate((a_, b_)) if tuple(e) in gends]
            ge = [0 if i == 0 else 99 for i in ge]
            if a_[1] == b_[1]:
                pic = _fence_h(a_[0], b_[0], seed)
                foot = at(a_[0], a_[1])
            else:
                pic = _fence_v(a_[1], b_[1], seed, gate_ends=ge)
                foot = at(b_[0], b_[1])
            out.append((fid, pic.rgba(), (pic.ax, pic.ay), foot))
        for oid, kind, (fx, fy), ex in _plot(cid, door):
            seed = sum(map(ord, oid))
            if kind == 'bed':
                pic = _bed(ex['w'], ex['h'], ex['crop'], seed)
                img, anc = pic.rgba(), (pic.ax, pic.ay)
            elif kind == 'hay':
                pic = _hay(22, 8, seed)
                img, anc = pic.rgba(), (pic.ax, pic.ay)
            elif kind == 'gate_leaf':
                pic = _gate_leaf(ex['w'], ex['dir'], seed)
                img, anc = pic.rgba(), (pic.ax, pic.ay)
                fy -= 0.4                                    # drawn behind the hinge post
            else:
                piece = {'hedge': 'crossroads_bush_nonblocking', 'flower_tub': 'crossroads_flower_tub',
                         'barrel': 'crossroads_barrel', 'woodpile': 'crossroads_woodpile',
                         'trough': 'crossroads_trough'}[kind]
                img, anc = kit(piece, ex.get('variant', 0))
            out.append((oid, img, anc, at(fx, fy)))
    return out


def render(p: dict | None = None):
    """The frame: the kit bake of the slice's cells, the doorsteps, every sprite's cast shadow by
    the bake's own rule (compose.cast_shadows), the sprites sorted by their feet."""
    from scripts.art.kit import bake as BK
    from scripts.art.native import compose as CO
    from scripts.art.native import screen as SN
    from scripts.art.native.palette import LUT
    p = p or plan()
    ground, _ = BK.bake(kit_plan(p))
    rgb = np.asarray(ground)[..., :3]
    cv = SN.to_codes(ground)
    assert (LUT[cv] == rgb).all(), 'the baked ground is not on the house palette'
    for b in p['buildings']:
        doorstep(cv, b['door'])
    H, W = cv.shape
    sprites = _sprites(p)
    casts, things = [], []
    for _id, img, anc, foot in sprites:
        a = np.asarray(img)[..., 3] > 0
        casts.append(CO.shadow_mask(a, anc, D, W, H, foot, *CO.SHADOW))
        things.append((foot[1] / D, img, anc, foot))
    G = CO.ground_from_codes(cv, D)
    CO.cast_shadows(G, casts, [], things, D)
    out = G.rgba()
    for _id, img, anc, foot in sorted(sprites, key=lambda s: s[3][1]):
        CO.paste(out, img, anc, foot)
    return out.convert('RGB')


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('out')
    a = ap.parse_args(argv)
    img = render()
    assert img.size == (W_WORLD * D, H_WORLD * D)
    img.save(a.out)
    print('wrote', a.out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
