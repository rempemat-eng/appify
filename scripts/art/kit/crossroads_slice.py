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
6. every cottage has a plot, and every fence has a reason (Matt, 2 Nov: "what is the point of
   fences if they don't enclose anything?", then "think deeply about parts of the game like
   fences. where would they be? what would they fence in?"; docs/vision/placement-logic.md): a
   wattle kitchen garden with soil beds in a dug patch, a sheep fold of hurdles with three sheep,
   a field shelter and a trough on trodden ground, a low wattle chicken run with hens and their
   coop on scratched earth, and a low whitewashed picket front garden with flower beds, its gate
   on the door path. Runs close their loops (the front garden uses the house wall), side gates
   face the spur with a trodden way through them; rules.fences and rules.enclosures in
   ground_rules.py check loops, gates, contents and sizes. Woodpiles stand against the gable
   walls, barrels beside the houses, tubs by the doors. The fence, gate, bed, hay, sheep, hen,
   coop and shelter painters are in this file (village.py helpers); the other props are candidate
   kit props.
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


# Matt, 2 Nov: "what is the point of fences if they don't enclose anything?" and "think deeply about
# parts of the game like fences. where would they be? what would they fence in?"
# (docs/vision/placement-logic.md). Every fence keeps something in, keeps something out or marks a
# front garden, closes a loop (or uses the house wall as a side), and has its gate on the path its
# owner walks:
#   north-west  a kitchen garden in wattle (keeps the deer and hens out): soil beds in a dug patch;
#   south-west  a sheep fold of wattle hurdles at the village edge: four sheep, a field shelter, a
#               trough and hay, the ground worn bare by the trough and the gate;
#   north-east  a chicken run of low wattle, four cells square: hens and their coop on scratched earth;
#   south-east  a front garden behind a low whitewashed picket from the house's corners, flower beds
#               either side of the door path and its gate on that path.
# The others' fronts stay open, so the lane has variety. Gates of the side enclosures face the spur
# and a two-cell trodden way leads through them; the front garden's gate stands on the spur itself.
# id: holds, style, (x0, y0, x1, y1) post centres in world px, gate (side, a0, a1)
ENCLOSURES = {
    'cottage_nw': ('crops', 'wattle', (16, 114, 78, 166), ('e', 124, 148)),
    'cottage_sw': ('sheep', 'hurdle', (16, 266, 78, 318), ('e', 276, 300)),
    'cottage_ne': ('chickens', 'low_wattle', (242, 138, 274, 170), ('w', 144, 160)),
    'cottage_se': ('flowers', 'picket', (200, 280, 264, 304), ('s', 222, 242)),
}


def _fences(cid, door):
    """The enclosure's runs as (id, kind, a, b, style) in world px, kind 'fence' or 'gate'. A side
    enclosure: north, south and outer runs whole, the spur side split round its gate. A front
    garden: two side runs from the house's front corners and the front run split round its gate;
    the house wall is its fourth side."""
    _h, st, (x0, y0, x1, y1), (side, a0, a1) = ENCLOSURES[cid]
    if side == 's':
        return [(cid + '_fence_w', 'fence', (x0, y0), (x0, y1), st),
                (cid + '_fence_e', 'fence', (x1, y0), (x1, y1), st),
                (cid + '_fence_s0', 'fence', (x0, y1), (a0, y1), st),
                (cid + '_gate', 'gate', (a0, y1), (a1, y1), st),
                (cid + '_fence_s1', 'fence', (a1, y1), (x1, y1), st)]
    xi, xo = (x1, x0) if side == 'e' else (x0, x1)
    return [(cid + '_fence_n', 'fence', (x0, y0), (x1, y0), st),
            (cid + '_fence_s', 'fence', (x0, y1), (x1, y1), st),
            (cid + '_fence_o', 'fence', (xo, y0), (xo, y1), st),
            (cid + '_fence_i0', 'fence', (xi, y0), (xi, a0), st),
            (cid + '_gate', 'gate', (xi, a0), (xi, a1), st),
            (cid + '_fence_i1', 'fence', (xi, a1), (xi, y1), st)]


def _gate_way(cid, door):
    """The trodden way through a side gate: two cells wide, from the spur's centre line straight
    through the gap and on into the enclosure (a route, baked as the path). None for a front gate."""
    _h, _st, (x0, _y0, x1, _y1), (side, a0, a1) = ENCLOSURES[cid]
    if side == 's':
        return None
    gc = (a0 + a1) // 2
    reach = 6 if _h == 'chickens' else 14                  # into the run only as far as its coop allows
    return [[door[0], gc], [x1 - reach if side == 'e' else x0 + reach, gc]]


def _plot(cid, door):
    """The plot's props as (id, kind, foot world px, extra): the enclosure's contents, the open gate
    leaf, the woodpile against a gable wall or a barrel beside the house, a tub by the door and a
    pair of the kit's bushes behind the house on the outer side."""
    x, y = door
    west = x < ROAD_X
    side = -1 if west else 1
    holds, _st, (x0, y0, x1, y1), (gs, a0, a1) = ENCLOSURES[cid]
    out = []
    if holds == 'crops':
        bx0, bx1 = x0 + 7, x1 - 24
        for k, fy in enumerate(range(y0 + 13, y1 - 13, 14)):        # rows clear of the south fence
            out.append((cid + '_bed_%d' % k, 'bed', ((bx0 + bx1) / 2, fy),
                        dict(w=bx1 - bx0, h=9, crop=('cabbage', 'leek', 'lettuce')[k % 3])))
    elif holds == 'sheep':
        out.append((cid + '_shelter', 'shelter', (x0 + 15, y0 + 15), {}))           # back corner, its open side south
        out.append((cid + '_trough', 'trough', (x1 - 20, y1 - 14), {}))             # near the gate, where it is filled
        for k, (sx, sy, face, pose) in enumerate(((x0 + 12, y0 + 30, 1, 'graze'), (x0 + 30, y0 + 26, 1, 'graze'),
                                                  (x0 + 14, y1 - 12, -1, 'lie'))):
            out.append((cid + '_sheep_%d' % k, 'sheep', (sx, sy), dict(face=face, pose=pose)))
    elif holds == 'chickens':
        out.append((cid + '_coop', 'coop', (x1 - 10, y0 + 12), {}))                  # the run's back corner
        for k, (cx_, cy_, face, col) in enumerate(((x0 + 8, y1 - 4, 1, 'plaster'), (x0 + 20, y1 - 6, -1, 'fox'),
                                                   (x1 - 6, y0 + 20, -1, 'plaster'))):
            out.append((cid + '_hen_%d' % k, 'chicken', (cx_, cy_), dict(face=face, col=col)))
    elif holds == 'flowers':
        for k, (fx0, fx1) in enumerate(((x0 + 3, a0 - 3), (a1 + 3, x1 - 3))):
            out.append((cid + '_flowers_%d' % k, 'flowers', ((fx0 + fx1) / 2, y1 - 4), dict(w=fx1 - fx0, h=10)))
    if gs in ('e', 'w'):
        # the gate stands open, swung in on its north post, clear of the way through
        xi = x1 if gs == 'e' else x0
        out.append((cid + '_gate_leaf', 'gate_leaf', (xi, a0), dict(w=a1 - a0 - 2, dir=-1 if gs == 'e' else 1)))
    # fuel stacked against the outer gable wall, under the eaves; goods by the house; a tub by the door
    if cid in ('cottage_ne', 'cottage_sw'):
        out.append((cid + '_woodpile', 'woodpile', (x + side * 45, y - 6), dict(variant=0)))
    else:
        out.append((cid + '_barrel', 'barrel', (x - side * 40, y - 4), dict(variant=1)))
    if holds != 'flowers':
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
    sizes = {'hedge': (16, 6), 'bed': None, 'flowers': None, 'flower_tub': (12, 6), 'barrel': (10, 8),
             'woodpile': (24, 8), 'trough': (30, 8), 'hay': (22, 8), 'gate_leaf': (14, 2), 'shelter': (22, 10),
             'coop': (14, 8), 'sheep': (16, 6), 'chicken': (5, 3)}
    fences, enclosures = [], []
    for cid, door, look in COTTAGES:
        x, y = door
        buildings.append({'id': cid, 'name': cid.replace('_', ' '), 'rect': [x - 32, y - look['depth'], 64, look['depth']],
                          'door': [x, y]})
        looks[cid] = look
        routes.append({'id': cid + '_spur', 'kind': 'spur', 'width': SPUR_W, 'points': _spur(door)})
        gw = _gate_way(cid, door)
        if gw:
            routes.append({'id': cid + '_gate_way', 'kind': 'spur', 'width': SPUR_W, 'points': gw})
        holds, style, rect, _g = ENCLOSURES[cid]
        enclosures.append({'id': cid + '_enclosure', 'holds': holds, 'style': style, 'rect': list(rect)})
        for oid, kind, (fx, fy), ex in _plot(cid, door):
            w, h = sizes[kind] or (ex.get('w', 16), ex.get('h', 6))
            if kind == 'gate_leaf':
                fx += ex['dir'] * w / 2            # the open leaf lies inside, from the hinge post
            objects.append([oid, kind, fx - w / 2, fy - h, w, h])
        fences += [{'id': fid, 'kind': k, 'a': list(a), 'b': list(b), 'style': st} for fid, k, a, b, st in _fences(cid, door)]
    return {'id': 'crossroads_slice', 'box': [0, 0, W_WORLD, H_WORLD], 'ground_rules': True,
            'note': 'Review study (scripts/art/kit/crossroads_slice.py), not a playable zone.',
            'buildings': buildings, 'routes': routes, 'objects': objects, 'fences': fences, 'enclosures': enclosures, 'art': {'looks': looks}}


def kit_plan(p: dict) -> dict:
    """The slice as a kit zone plan: lawn and path cells from its routes (softgrid.cells_route, as
    woodland_kit.py lays the woodland's), the doors as context for the path's variants."""
    from scripts.art.native import softgrid as SG
    h, w = H_WORLD * D, W_WORLD * D
    grid = np.full(SG.grid_shape(h, w), '.', '<U1')
    # ground worn bare by stock: the hens scratch their whole run, the sheep tread the corner by
    # their trough and gate (the kit's worn ground, under the paths)
    for e in p.get('enclosures', []):
        x0, y0, x1, y1 = e['rect']
        if e['holds'] == 'chickens':
            grid[SG.cells_rects([[x0 + 2, y0 + 2, x1 - x0 - 4, y1 - y0 - 4]], h, w)] = 'w'
        elif e['holds'] == 'sheep':
            grid[SG.cells_rects([[x1 - 38, y1 - 26, 36, 20]], h, w)] = 'w'
    for r in p['routes']:
        n = max(1, int(round((r['width'] - 8) / 8.0)))
        grid[SG.cells_route(r['points'], n, h, w)] = '#'
    return {'zone': 'crossroads_slice', 'legend': {'.': 'lawn', '#': 'path', 'w': 'worn'},
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
# the boundary styles (placement-logic.md): wattle for the kitchen garden, hurdles for the sheep
# fold, low wattle for the hens, a low whitewashed picket for the front garden. Height (world px),
# stake spacing, stake width, family.
STYLES = {'wattle': dict(h=10, every=8, stake=1.6, fam='timber_warm'),
          'hurdle': dict(h=11, every=11, stake=1.8, fam='timber_warm'),
          'low_wattle': dict(h=7, every=7, stake=1.4, fam='timber_warm'),
          'picket': dict(h=8, every=16, stake=2.2, fam='plaster')}


def _canvas(w, h, up):
    from scripts.art.native import village as V
    pad = 4
    return V.Pic(V.q(w + 6) + 2 * pad, V.q(h + up) + 2 * pad, pad + V.q(3), V.q(h + up) + pad)


def _stake(a, cx, yb, h, w, fam, cap=False):
    """A stake or post centred on cx, foot at row yb (texels): lit west face, shaded east side, its
    top cut and lit; a gatepost a little taller."""
    from scripts.art.native import village as V
    q = V.q
    x0 = int(round(cx - q(w) / 2))
    fam_ = 'timber' if fam == 'timber_warm' else fam
    V.prism(a, x0, yb - q(h), x0 + max(2, q(w)), yb, max(2, q(0.8)), fam_, 3, side=max(1, q(w) // 3))
    if cap:
        V.prism(a, x0 - 1, yb - q(h) - 2, x0 + max(2, q(w)) + 1, yb - q(h) + 1, 2, fam_, 4, side=1)


def _weave(a, x0, x1, y0, yb, stakes, fam, rng):
    """Hazel rods woven between stakes, seen from the south: courses about a world px and a half
    apart, each rod bulging out (lit) where it passes in front of a stake and sinking (shaded) where
    it passes behind; a twisted binding rod along the top, the bottom course in the grass's shade."""
    from scripts.art.native import village as V
    Y, X = V.grid(a)
    m = (X >= x0) & (X < x1) & (Y >= y0) & (Y < yb)
    course = max(3, V.q(1.4))
    k = ((Y - y0) // course).astype(int)
    # which stake bay, and whether this course passes in front (odd bays on odd courses)
    sx = np.asarray(sorted(stakes), float)
    bay = np.searchsorted(sx, X) if len(sx) else np.zeros_like(X, int)
    front = ((bay + k) % 2) == 0
    near = np.min(np.abs(X[..., None] - sx[None, None, :]), axis=-1) if len(sx) else np.full(X.shape, 99.0)
    t = 3.0 + 0.8 * front - 0.9 * (~front & (near < V.q(2.0))) + 0.5 * (((Y - y0) % course) == 0) \
        - 0.9 * (((Y - y0) % course) == course - 1) + 0.35 * np.sin(X * 0.7 + k * 1.9)
    t = t - 0.6 * (Y >= yb - course)
    V.paint(a, m, ('timber_cool', 'timber', 'timber_warm'), t - 0.4)
    top = (X >= x0) & (X < x1) & (Y >= y0 - 2) & (Y < y0 + 1)
    V.paint(a, top, ('timber_cool', 'timber', 'timber_warm'), 3.6 - 1.2 * ((X // 4) % 2) - 1.0 * (Y == y0))


def _run_h(xa, xb, style, seed, gate_ends=(), gate=False):
    """A run along x from post centre xa to xb (world px), foot (anchor) at (xa, the line). Wattle:
    stakes with rods woven between. Picket: corner posts, two rails, pointed palings nailed on, all
    whitewashed. `gate`: a gate filling the gap (a picket gate with its ledges and brace)."""
    from scripts.art.native import village as V
    q = V.q
    S = STYLES[style]
    rng = np.random.default_rng(seed)
    p = _canvas(xb - xa, 0, S['h'] + 4)
    a, ax, yb = p.a, p.ax, p.ay
    L = xb - xa
    if style == 'picket':
        n = max(2, int(round(L / S['every'])) + 1)
        posts = [ax + q(L * k / (n - 1)) for k in range(n)]
        if gate:
            posts = [posts[0], posts[-1]]
        for yy in (2.4, 5.8):                                  # the rails behind the palings
            V.board(a, posts[0], yb - q(yy), posts[-1] - posts[0], q(1.2), 0, 'plaster', 2, rng, split=False)
        x = posts[0] + q(1.8)
        while x < posts[-1] - q(1.8):
            pw = q(1.3)
            V.prism(a, int(x), yb - q(S['h'] - 1), int(x) + pw, yb, 1, 'plaster', 4, side=1)
            a[yb - q(S['h'] - 1) - 1, int(x) + 1:int(x) + pw - 1] = V.code('plaster', 4)      # the point
            a[yb - q(S['h'] - 1) - 2, int(x) + pw // 2] = V.code('plaster', 5)
            x += q(2.7)
        if gate:                                               # the gate's brace across its palings
            V.bar(a, posts[0] + q(2), yb - q(2.2), posts[-1] - q(2), yb - q(5.4), q(0.5), 'plaster_warm', 2)
        for k, px in enumerate(posts):
            _stake(a, px, yb, S['h'] + (2 if (k in gate_ends or gate) else 0), S['stake'], 'plaster',
                   cap=(k in gate_ends or gate))
        return V.finish(p)
    n = max(2, int(round(L / S['every'])) + 1)
    xs = [ax + q(L * k / (n - 1)) for k in range(n)]
    _weave(a, xs[0], xs[-1], yb - q(S['h'] - 1.5), yb, xs, S['fam'], rng)
    for k, x in enumerate(xs):
        last = k == n - 1
        ge = (k == 0 and 0 in gate_ends) or (last and 99 in gate_ends)
        _stake(a, x, yb, S['h'] + (3 if ge else 0.5), S['stake'], 'timber', cap=ge)
    return V.finish(p)


def _run_v(ya, yb_, style, seed, gate_ends=()):
    """A run along y from ya to yb_ (world px), foot (anchor) at the south end. Seen end on to the
    light: wattle shows the woven panel's top edge and lit west face as a strip, its stakes rising
    through it; a picket shows its palings one behind the other, a sawtooth of points."""
    from scripts.art.native import village as V
    q = V.q
    S = STYLES[style]
    rng = np.random.default_rng(seed)
    L = yb_ - ya
    p = _canvas(0, L, S['h'] + 4)
    a, ax, yb = p.a, p.ax, p.ay
    n = max(2, int(round(L / S['every'])) + 1)
    ys = [yb - q(L) + q(L * k / (n - 1)) for k in range(n)]
    ends = {0 if g == 0 else n - 1 for g in gate_ends}
    Y, X = V.grid(a)
    x0 = int(round(ax - q(0.9)))
    if style == 'picket':
        y = ys[0] + q(1.4)
        while y < ys[-1]:
            V.prism(a, x0, int(y) - q(S['h'] - 1), x0 + q(1.8), int(y), 1, 'plaster', 4, side=1)
            y += q(1.6)
    else:
        top, bot = ys[0] - q(S['h'] - 1.5), ys[-1]
        m = (X >= x0) & (X < x0 + q(1.8)) & (Y >= top) & (Y < bot)
        course = max(3, q(1.4))
        V.paint(a, m, ('timber_cool', 'timber', 'timber_warm'), 2.8 + 0.9 * (X < x0 + 2) - 1.0 * (X >= x0 + q(1.8) - 1)
                + 0.6 * (((Y - top) % course) == 0) - 0.5 * (((Y - top) % course) == course - 1))
    for k in range(n):
        g = k in ends
        _stake(a, ax, ys[k], S['h'] + (3 if g else 0.5) if style != 'picket' else S['h'] + (2 if g else 0),
               S['stake'], 'plaster' if style == 'picket' else 'timber', cap=g)
    return V.finish(p)


def _gate_leaf(w, d, style, seed):
    """The gate standing open inside the enclosure, swung back on its hinge post: a hurdle the
    width of the gap (stakes at its ends, rods woven between), lying along x from the hinge (foot
    at the hinge, `d` = +1 east, -1 west)."""
    from scripts.art.native import village as V
    q = V.q
    S = STYLES[style]
    rng = np.random.default_rng(seed)
    p = _canvas(w, 0, S['h'] + 3)
    if d < 0:
        p.ax = p.W - 1 - p.ax
    a, ax, yb = p.a, p.ax, p.ay
    xh = ax + q(1.5) * d
    xf = xh + q(w - 1.5) * d
    l, r = min(xh, xf), max(xh, xf)
    _weave(a, l, r, yb - q(S['h'] - 2.5), yb - q(1.2), [l, (l + r) // 2, r], S['fam'], rng)
    for x in (l, r):
        _stake(a, x, yb - q(0.6), S['h'] - 1, S['stake'] * 0.8, 'timber')
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
        step = {'cabbage': 6.5, 'lettuce': 5.0, 'leek': 3.4, 'carrot': 3.6, 'flowers': 3.2}[crop]
        k = int((w - 5) // step)
        for i in range(k + 1):
            px = x0 + q(2.5) + (x1 - x0 - q(5)) * i / max(1, k) + int(rng.integers(-1, 2))
            if crop == 'flowers':
                # a cottage border: leafy clumps, each topped with its own colour, lit on the upper left
                m = V.ellipse_mask(a.shape, px, cy - q(0.6), q(1.7), q(1.6))
                V.blob(a, m, 'leaf', 3)
                fam = ('berry', 'brass', 'dusk', 'plaster', 'sky', 'berry')[int(rng.integers(0, 6))]
                for _ in range(3):
                    fx, fy = int(px) + int(rng.integers(-3, 3)), int(cy - q(1.6)) + int(rng.integers(-2, 2))
                    a[fy:fy + 2, fx:fx + 2] = V.code(fam, 4)
                    a[fy, fx] = V.code(fam, 5)
                continue
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


def _sheep(face, pose, seed):
    """A black-faced sheep (about 16 x 10 world px): a fleece of curls lit on its upper left and
    shading to its belly and rump, the black face and ears at the front (lowered to the grass when
    it grazes, up when it stands or lies), four thin black legs (the far pair a step darker); lying,
    its legs folded under and its fleece on the grass."""
    from scripts.art.native import village as V
    q = V.q
    rng = np.random.default_rng(seed)
    p = V._pic(18, 6, up=10, side=1)
    a, cx, yb = p.a, p.ax, p.ay
    Y, X = V.grid(a)
    lie = pose == 'lie'
    by = yb - q(3.6 if lie else 5.6)
    rx, ry = q(6.6), q(3.6 if lie else 3.8)
    bcx = cx - face * q(0.8)
    if not lie:                                              # legs first, the body hides their tops
        for lx, far in ((-4.2, True), (2.6, True), (-3.0, False), (3.8, False)):
            x = bcx + face * q(lx)
            V.prism(a, int(x), by + q(1.5), int(x) + max(2, q(0.9)), yb, 1, 'soot', 1 if far else 2, side=1)
    body = np.zeros(a.shape, bool)
    for _ in range(26):                                      # a fleece of curls
        ux, uy = rng.uniform(-1, 1), rng.uniform(-1, 1)
        if ux * ux + uy * uy > 1:
            continue
        body |= V.ellipse_mask(a.shape, bcx + ux * (rx - q(1.2)), by + uy * (ry - q(1.0)), q(1.5), q(1.3))
    body |= V.ellipse_mask(a.shape, bcx, by, rx - q(0.8), ry - q(0.6))
    nx, ny = (X - bcx) / rx, (Y - by) / ry
    lit = -0.5 * nx - 0.7 * ny
    curl = np.sin(X * 1.3) * np.sin(Y * 1.5)
    V.paint(a, body, ('sand', 'plaster_warm', 'plaster_warm'), 3.0 + 1.6 * lit + 0.6 * curl)
    # the head: black, at the front, lowered when grazing
    hx = bcx + face * (rx + q(0.6))
    hy = by + (q(2.0) if pose == 'graze' else -q(1.2))
    head = V.ellipse_mask(a.shape, hx, hy, q(1.7), q(2.1))
    V.blob(a, head, 'soot', 2)
    a[V.ellipse_mask(a.shape, hx - q(0.5), hy - q(0.8), q(0.6), q(0.5)) & head] = V.code('soot', 4)
    ear = V.ellipse_mask(a.shape, hx - face * q(1.5), hy - q(1.4), q(1.1), q(0.5))
    a[ear & ~head] = V.code('soot', 2)
    return V.finish(p)


def _chicken(face, col, seed):
    """A hen (about 5 x 5 world px): a round body lit on top, the tail feathers cocked up behind,
    the head forward with its red comb and wattle and a yellow beak, two thin yellow legs."""
    from scripts.art.native import village as V
    q = V.q
    p = V._pic(6, 3, up=5, side=1)
    a, cx, yb = p.a, p.ax, p.ay
    for dx in (-0.6, 0.6):
        x = cx + q(dx)
        a[yb - q(1.3):yb, int(x):int(x) + 2] = V.code('brass', 3)
    by = yb - q(2.6)
    body = V.ellipse_mask(a.shape, cx, by, q(2.3), q(1.6))
    tail = V.ellipse_mask(a.shape, cx - face * q(2.0), by - q(1.4), q(0.9), q(1.4))
    V.blob(a, body | tail, col, 3)
    a[V.ellipse_mask(a.shape, cx - q(0.5), by - q(0.9), q(1.2), q(0.5)) & body] = V.code(col, 5 if col == 'plaster' else 4)
    hx, hy = cx + face * q(2.0), by - q(1.6)
    head = V.ellipse_mask(a.shape, hx, hy, q(1.0), q(1.0))
    V.blob(a, head, col, 4)
    a[int(hy - q(1.3)):int(hy - q(0.7)), int(hx - 2):int(hx + 2)] = V.code('berry', 4)          # comb
    a[int(hy + q(0.4)):int(hy + q(1.0)), int(hx + face * 1):int(hx + face * 1) + 2] = V.code('berry', 3)   # wattle
    bx = int(hx + face * q(1.0))
    a[int(hy) - 1:int(hy) + 1, min(bx, bx + face * 3):max(bx, bx + face * 3)] = V.code('brass', 4)  # beak
    a[int(hy) - 1, int(hx + face * 1)] = V.code('soot', 0)                                       # eye
    return V.finish(p)


def _coop(seed):
    """A hen house (14 x 8 world px) on short legs: boarded walls lit on the west, a pitched board
    roof with its ridge and a dark overhang shadow, a pop hole with a ramp down to the run."""
    from scripts.art.native import village as V
    q = V.q
    rng = np.random.default_rng(seed)
    p = V._pic(14, 8, up=15, side=2)
    a, cx, yb = p.a, p.ax, p.ay
    x0, x1 = cx - q(6), cx + q(6)
    for lx in (x0 + q(0.6), x1 - q(1.6)):                     # legs
        V.prism(a, int(lx), yb - q(3), int(lx) + q(1), yb, 1, 'timber', 2, side=1)
    wt, wb = yb - q(10.5), yb - q(2.6)
    V.prism(a, x0, wt, x1, wb, q(3.0), 'timber', 3, side=q(2.0))
    Y, X = V.grid(a)
    planks = (X >= x0) & (X < x1) & (Y >= wt + q(3.0)) & (Y < wb) & (((X - x0) % q(2.2)) == 0)
    a[planks] = V.code('timber', 1)
    # the roof: two board planes meeting at a ridge, seen from the south, overhanging the walls
    rt = wt - q(4.2)
    for k in range(int(q(5.0))):
        y = rt + k
        V.board(a, x0 - q(1.0), y, (x1 - x0) + q(2.0), 1, 0, 'timber_cool', 3 if k < q(2.5) else 2, rng, split=False, grain=False)
    a[rt, x0 - q(1.0):x1 + q(1.0)] = V.code('timber_cool', 4)
    a[rt + q(5.0) - 1:rt + q(5.0) + 1, x0 - q(1.0):x1 + q(1.0)] = V.code('timber_cool', 1)
    # the pop hole and its ramp
    hx = cx + q(2.0)
    a[wb - q(3.0):wb - q(0.6), int(hx - q(1.2)):int(hx + q(1.2))] = V.code('soot', 0)
    V.bar(a, hx, wb, hx + q(4.5), yb - 1, q(0.6), 'timber_warm', 3)
    for k in range(3):
        t = 0.25 + 0.25 * k
        V.bar(a, hx + q(4.5) * t - 2, wb + (yb - 1 - wb) * t, hx + q(4.5) * t + 2, wb + (yb - 1 - wb) * t, 0.6, 'timber', 1)
    return V.finish(p)


def _shelter(seed):
    """A field shelter for the flock (22 x 10 world px): a boarded back wall, two front posts, a
    single-pitch roof of boards falling to the front with a dark eave, the inside in deep shade
    and straw on its floor."""
    from scripts.art.native import village as V
    q = V.q
    rng = np.random.default_rng(seed)
    p = V._pic(22, 10, up=16, side=2)
    a, cx, yb = p.a, p.ax, p.ay
    Y, X = V.grid(a)
    x0, x1 = cx - q(11), cx + q(11)
    back = yb - q(10)
    # the back wall (its boards seen inside, in shade) and the dark inside
    V.prism(a, x0, back - q(11), x1, back, 1, 'timber', 2, side=0)
    a[(X >= x0) & (X < x1) & (Y >= back - q(11)) & (Y < back) & (((X - x0) % q(2.4)) == 0)] = V.code('timber', 0)
    inside = (X >= x0) & (X < x1) & (Y >= back) & (Y < yb)
    V.paint(a, inside, ('earth_cool', 'earth', 'earth_warm'), 1.2 + 0.6 * np.sin(X * 0.9 + Y * 0.4))
    straw = inside & (Y > yb - q(5)) & (np.sin(X * 1.7 + Y * 2.3) > 0.4)
    a[straw] = V.code('brass', 2)
    # posts and roof
    for px in (x0, x1 - q(1.8)):
        V.prism(a, int(px), yb - q(12.5), int(px) + q(1.8), yb, 1, 'timber', 3, side=1)
    rt, rb = back - q(14.5), yb - q(12.5)
    for k, y in enumerate(range(rt, rb)):
        f = k / max(1, rb - rt)
        V.board(a, x0 - q(1.0), y, (x1 - x0) + q(2.0), 1, 0, 'timber_cool', 4 if f < 0.15 else (3 if f < 0.8 else 2), rng,
                split=False, grain=False)
    seams = (X >= x0 - q(1.0)) & (X < x1 + q(1.0)) & (Y >= rt) & (Y < rb) & (((X - x0) % q(3.2)) == 0)
    a[seams] = V.code('timber_cool', 1)
    a[rb:rb + 2, x0 - q(1.0):x1 + q(1.0)] = V.code('timber_cool', 1)
    return V.finish(p)


def dug_patch(cv: np.ndarray, rect, seed) -> None:
    """The kitchen garden's ground: dug soil (in codes) inside its fence, lumpy at the edge where
    the spade stopped short of the grass, worked into a crumb with clods lit on their upper left."""
    from scripts.art.native.palette import C, FI
    x0, y0, x1, y1 = [int(round(v * D)) for v in rect]
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[y0:y1, x0:x1]
    n = ndi.gaussian_filter(rng.random(yy.shape), 2.0)
    n = (n - n.mean()) / max(1e-6, n.std())
    d = np.minimum.reduce([xx - x0, x1 - 1 - xx, yy - y0, y1 - 1 - yy]).astype(float)
    m = d + 2.0 * n > 3
    t = np.clip(np.round(2.6 + 0.5 * n + 0.6 * (np.sin(yy * 0.9) > 0.6)), 1, 4).astype(int)
    fam = np.where(t >= 4, FI['earth_warm'], np.where(t <= 1, FI['earth_cool'], FI['earth']))
    code = fam * 8 + t
    edge = m & ~ndi.binary_erosion(m, iterations=2)
    code[edge] = C('earth_cool', 1)
    sub = cv[y0:y1, x0:x1]
    sub[m] = code[m]


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
        gate = [(a_, b_) for _f, k, a_, b_, _s in fl if k == 'gate'][0]
        gends = {tuple(gate[0]), tuple(gate[1])}
        for fid, k, a_, b_, st in fl:
            seed = sum(map(ord, fid))
            ge = [0 if i == 0 else 99 for i, e in enumerate((a_, b_)) if tuple(e) in gends]
            if k == 'gate':
                if st != 'picket':
                    continue                                 # a side gate stands open (its leaf below)
                pic = _run_h(a_[0], b_[0], st, seed, gate=True)    # the front gate, shut on its path
                foot = at(a_[0], a_[1] + 0.3)
            elif a_[1] == b_[1]:
                pic = _run_h(a_[0], b_[0], st, seed, gate_ends=ge)
                foot = at(a_[0], a_[1])
            else:
                pic = _run_v(a_[1], b_[1], st, seed, gate_ends=ge)
                foot = at(b_[0], b_[1])
            out.append((fid, pic.rgba(), (pic.ax, pic.ay), foot))
        style = ENCLOSURES[cid][1]
        painters = {'bed': lambda ex, sd: _bed(ex['w'], ex['h'], ex['crop'], sd),
                    'flowers': lambda ex, sd: _bed(ex['w'], ex['h'], 'flowers', sd),
                    'hay': lambda ex, sd: _hay(22, 8, sd),
                    'gate_leaf': lambda ex, sd: _gate_leaf(ex['w'], ex['dir'], style, sd),
                    'sheep': lambda ex, sd: _sheep(ex['face'], ex['pose'], sd),
                    'chicken': lambda ex, sd: _chicken(ex['face'], ex['col'], sd),
                    'coop': lambda ex, sd: _coop(sd),
                    'shelter': lambda ex, sd: _shelter(sd)}
        for oid, kind, (fx, fy), ex in _plot(cid, door):
            seed = sum(map(ord, oid))
            if kind in painters:
                pic = painters[kind](ex, seed)
                img, anc = pic.rgba(), (pic.ax, pic.ay)
                if kind == 'gate_leaf':
                    fy -= 0.4                                # drawn behind the hinge post
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
    for e in p.get('enclosures', []):
        if e['holds'] == 'crops':
            x0, y0, x1, y1 = e['rect']
            dug_patch(cv, (x0 + 3, y0 + 3, x1 - 20, y1 - 2), sum(map(ord, e['id'])))
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
