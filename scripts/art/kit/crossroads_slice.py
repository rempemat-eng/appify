"""The Crossroads cottage slice: four candidate cottages on a north-south road, as a review study.

    python3 -m scripts.art.kit.crossroads_slice OUT.png          # the native frame (960 x 1008)

Claude A's review of PR #416 (1 Nov) asked for six fixes, all made here:
1. no two buildings overlap: plots one cell apart beyond the eaves; rules.building_overlap in
   scripts/review/ground_rules.py checks every plan, and this slice's plan is strict there;
2. the road keeps its width class (three cells: wheel ruts, a grass crown), the spurs are lanes
   two cells wide;
3. each spur leaves its door's centre over a doorstep slab, runs straight south, turns once and
   meets the road in a T on the soft grid (cell 8 world px, 24 art px);
4. road and spurs are the woodland kit's packed earth: the slice is a kit plan (cells of
   game/kit/pieces/terrain/path.json) baked by scripts/art/kit/bake.py, the woodland_kit zone's
   bake, so the material, its variants, soft-grid edge and turf lip are the same pixels' recipe;
5. the road's edge is the kit's soft-grid outline (turns at 0.4 cell), its ruts the kit's class-3
   treatment (surface.path_widths) and the crown grown over;
6. every cottage has a plot: a post-and-rail front fence with a gap for its spur, a side hedge, a
   garden bed or woodpile and a few frontage props, all existing candidate kit props or the native
   painters those props were made with (village.p_fence, p_beds_hd).

The cottages are the native HD cottages (houses.py via village.building), unapproved candidates.
Nothing here changes a game rule, a playable zone or the piece library.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

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
SPUR_RUN = 32                        # door to the spur's turn: two cells straight, then the bend


def _spur(door):
    x, y = door
    turn = y + SPUR_RUN
    return [[x, y + CELL], [x, turn], [ROAD_X, turn]]


def _plot(cid, door):
    """The plot's props as (id, kind, foot world px, extra): fence runs, hedge, bed or woodpile,
    frontage. West plots run from the frame's edge to the road; east plots mirror them."""
    x, y = door
    west = x < ROAD_X
    out = []
    fence_y = y + SPUR_RUN - CELL            # the fence stands on the spur's north edge, a gate gap for it
    lo, hi = (8, ROAD_X - 12) if west else (ROAD_X + 20, W_WORLD - 8)
    gap0, gap1 = x - CELL - 2, x + CELL + 2
    out.append((cid + '_fence_a', 'fence', ((lo + gap0) / 2, fence_y), dict(w=gap0 - lo)))
    out.append((cid + '_fence_b', 'fence', ((gap1 + hi) / 2, fence_y), dict(w=hi - gap1)))
    # the outer side (away from the road): a hedge of the kit's bushes along the back, a garden
    # bed or a woodpile in front of it; frontage props at the door and the road-side corner
    side = -1 if west else 1
    hx = lo + 12 if west else hi - 12
    if cid in ('cottage_nw', 'cottage_se'):
        hedge = (y - 76, y - 48, y - 20)
        out.append((cid + '_bed', 'beds_dug', (lo + 22 if west else hi - 22, fence_y - 11), dict(w=40, h=18)))
        out.append((cid + '_tub', 'flower_tub', (x - side * 17, y + 9), dict(variant=len(cid) % 7)))
        out.append((cid + '_barrel', 'barrel', (x - side * 42, y - 2), dict(variant=1)))
    else:
        hedge = (y - 62, y - 34)
        out.append((cid + '_woodpile', 'woodpile', (x + side * 50, y - 2), dict(variant=0)))
        out.append((cid + '_tub', 'flower_tub', (x - side * 17, y + 9), dict(variant=(len(cid) + 3) % 7)))
        out.append((cid + '_sacks', 'sacks', (x + side * 21, y + 12), {}))
    for k, hy in enumerate(hedge):
        out.append((cid + '_hedge_%d' % k, 'hedge', (hx, hy), dict(variant=(k + len(cid)) % 7)))
    return out


def plan() -> dict:
    """The slice's plan in world px, the shape scripts/review/ground_rules.py reads: buildings with
    floor, door and look, routes, objects (id, kind, x, y, w, h: foot at the bottom centre)."""
    buildings, looks, routes, objects = [], {}, [], []
    routes.append({'id': 'road', 'kind': 'road', 'width': ROAD_W, 'points': [[ROAD_X, 0], [ROAD_X, H_WORLD]]})
    sizes = {'fence': None, 'hedge': (16, 6), 'beds_dug': None, 'flower_tub': (12, 6), 'barrel': (10, 8),
             'woodpile': (22, 8), 'sacks': (14, 8), 'bench': (24, 6)}
    for cid, door, look in COTTAGES:
        x, y = door
        buildings.append({'id': cid, 'name': cid.replace('_', ' '), 'rect': [x - 32, y - look['depth'], 64, look['depth']],
                          'door': [x, y]})
        looks[cid] = look
        routes.append({'id': cid + '_spur', 'kind': 'spur', 'width': SPUR_W, 'points': _spur(door)})
        for oid, kind, (fx, fy), ex in _plot(cid, door):
            w, h = sizes[kind] or (ex.get('w', 16), ex.get('h', 6))
            objects.append([oid, kind, fx - w / 2, fy - h, w, h])
    return {'id': 'crossroads_slice', 'box': [0, 0, W_WORLD, H_WORLD], 'ground_rules': True,
            'note': 'Review study (scripts/art/kit/crossroads_slice.py), not a playable zone.',
            'buildings': buildings, 'routes': routes, 'objects': objects, 'art': {'looks': looks}}


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


def _sprites(p: dict):
    """(id, image, anchor texels, foot texels, casts shadow) for every building and prop."""
    from PIL import Image
    from scripts.art.native import village as V

    def kit(piece, variant):
        vs = json.load(open(os.path.join(ROOT, 'game', 'kit', 'pieces', 'prop', piece + '.json')))['variants']
        v = vs[variant % len(vs)]
        img = Image.open(os.path.join(ROOT, 'game', v['png'][len('res://'):])).convert('RGBA')
        return img, tuple(v['foot'])

    out = []
    for cid, door, look in COTTAGES:
        b = V.building(dict(look), seed=look['seed'], hd=True)
        out.append((cid, b.base.rgba(), (b.base.ax, b.base.ay), (door[0] * D, door[1] * D)))
    for cid, door, _look in COTTAGES:
        for oid, kind, (fx, fy), ex in _plot(cid, door):
            if kind in ('fence', 'beds_dug'):
                pic = V.prop(kind, ex['w'], ex.get('h', 6), seed=sum(map(ord, oid)), hd=True)
                img, anc = pic.rgba(), (pic.ax, pic.ay)
            else:
                piece = {'hedge': 'crossroads_bush_nonblocking', 'flower_tub': 'crossroads_flower_tub',
                         'barrel': 'crossroads_barrel', 'woodpile': 'crossroads_woodpile',
                         'sacks': 'crossroads_sacks', 'bench': 'crossroads_bench'}[kind]
                img, anc = kit(piece, ex.get('variant', 0))
            out.append((oid, img, anc, (int(round(fx * D)), int(round(fy * D)))))
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
