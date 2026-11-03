"""A stretch of the Drover's Road through the Brackens built only from kit pieces, as a review
study (not a playable zone): the road east to west with a trod turning north at a fingerpost; a
drystone fold with its gate on the path from the road, a stile where a footpath crosses its back
wall, its trough and its flock; the drove well and the drovers' seat by the road (facing a toppled cairn across it); the shepherd's
hut with its peat stack; a broken cart and a cold fire ring on the verge; a broken fold; a cairn on
the trod; a hermit's fire up the trod; gorse at the edges
(docs/vision/regions/home-valley-frostline-brackens.md, sections 2, 3 and 5).

    python3 -m scripts.art.kit.sets.brackens_study OUT.png [--scale 3]   # the baked frame and every still

The plan has the kit zones' shape (game/kit/zones/*.json), so the editor's checks read it as they read
a zone: scripts/review/kit_rules.py, scripts/art/kit/relations.py and enclosures.py; `layout_faults`
adds the staging rules the farm study keeps (scripts/art/kit/farm_study.py). test_kit keeps all of
them at 0.
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np
from PIL import Image

from scripts.art.kit.schema import ROOT

CELL = 24
COLS, ROWS = 40, 26


def _ring(c0, c1, r0, r1, gate_col, stile_col, prefix):
    """A closed drystone loop: runs on columns c0 and c1 and on the lines under rows r0 and r1; a gate
    three cells wide on the south run at gate_col; a stile on the north run at stile_col."""
    cells = {}
    for c in range(c0, c1 + 1):
        for r in (r0, r1):
            j = cells.setdefault((c, r), set())
            if c > c0:
                j.add('w')
            if c < c1:
                j.add('e')
    for r in range(r0, r1 + 1):
        for c in (c0, c1):
            j = cells.setdefault((c, r), set())
            if r > r0:
                j.add('n')
            if r < r1:
                j.add('s')
    for c in (gate_col - 1, gate_col, gate_col + 1):
        cells.pop((c, r1))
    out = []
    for (c, r), j in sorted(cells.items(), key=lambda t: (t[0][1], t[0][0])):
        jn = ''.join(s for s in 'nesw' if s in j)
        pc = {'id': '%s_%d_%d' % (prefix, c, r), 'at': [c * CELL + 12, (r + 1) * CELL]}
        if (c, r) == (stile_col, r0):
            pc['piece'] = 'wall_drystone_stile_ew'
        else:
            pc['piece'] = 'wall_drystone_' + jn
            if jn == 'ew':
                pc['variant'] = 'b' if (c * 7 + r) % 3 == 0 else 'a'
        out.append(pc)
    out.append({'id': prefix + '_gate', 'piece': 'wall_drystone_gate_ew', 'at': [gate_col * CELL + 12, (r1 + 1) * CELL],
                'variant': 'shut'})
    return out


def plan() -> dict:
    """The Drover's Road on the moor: heath all round, two peat hags, gritstone outcrops and sheep
    trods; the stony drove road (three cells) east to west; the fold on grazed grass."""
    g = np.full((ROWS, COLS), '.', '<U1')
    g[4:12, 2:11] = ','                     # the fold's floor, grazed short
    g[17:20, :] = 'd'                       # the drove road
    g[0:17, 22:24] = '#'                    # the trod north from the junction
    g[11:17, 5:8] = '#'                     # the fold's gateway from the road
    g[0:5, 8] = '#'                         # the footpath to the stile over the fold's back wall
    g[5:11, 8] = 'w'                        # trodden inside the fold, stile to gate
    g[8:11, 3:6] = 'w'                      # worn round the trough
    g[2:4, 25:28] = 'w'                     # bare round the hermit's fire
    g[6:9, 13:18] = 'p'                     # a peat hag between the fold and the trod
    g[21:24, 30:36] = 'p'                   # and one south of the road
    pieces = _ring(2, 10, 4, 11, 6, 8, 'fold')
    pieces += [
        # the fold: the trough against the west wall, the flock spread clear of the walls and the way
        {'id': 'trough', 'piece': 'crossroads_trough', 'at': [120, 216]},
        {'id': 'sheep_1', 'piece': 'farm_sheep', 'at': [180, 168]},
        {'id': 'sheep_2', 'piece': 'farm_sheep_graze', 'at': [120, 264]},
        {'id': 'sheep_3', 'piece': 'farm_sheep_lie', 'at': [204, 240]},
        # north of the road: the drovers' seat facing a toppled cairn across it, the drove well
        {'id': 'seat', 'piece': 'brackens_bench', 'at': [48, 408]},
        {'id': 'well', 'piece': 'brackens_drove_well', 'at': [372, 408]},
        # the shepherd's hut, its door to the road, its peat stack at the gable
        {'id': 'hut', 'piece': 'brackens_shepherds_hut', 'at': [756, 408]},
        {'id': 'peat', 'piece': 'brackens_peat_stack', 'at': [912, 408]},
        # south of the road: the fingerposts opposite the two junctions (their arms point north up
        # the trod or the gateway, east and west along the road), the verge's story props
        {'id': 'fingerpost', 'piece': 'commons_fingerpost_new', 'at': [540, 504]},
        {'id': 'fingerpost_fold', 'piece': 'commons_fingerpost_new', 'at': [156, 504]},
        {'id': 'cairn_toppled', 'piece': 'brackens_cairn', 'at': [72, 528], 'variant': 'toppled'},
        {'id': 'fire_cold', 'piece': 'brackens_fire_ring_cold', 'at': [252, 552]},
        {'id': 'cart', 'piece': 'brackens_cart_broken', 'at': [372, 528]},
        {'id': 'ruin', 'piece': 'brackens_fold_ruin', 'at': [660, 600]},
        # up the trod: a cairn beside it, the hermit's fire off it
        {'id': 'cairn', 'piece': 'brackens_cairn', 'at': [492, 144], 'variant': 'standing'},
        {'id': 'hermit_fire', 'piece': 'brackens_fire_ring_lit', 'at': [636, 96]},
        # gorse at the edges
        {'id': 'gorse_1', 'piece': 'brackens_gorse', 'at': [348, 72], 'variant': 'a'},
        {'id': 'gorse_2', 'piece': 'brackens_gorse', 'at': [900, 96], 'variant': 'b'},
        {'id': 'gorse_3', 'piece': 'brackens_gorse', 'at': [876, 624], 'variant': 'a'},
        {'id': 'gorse_4', 'piece': 'brackens_gorse', 'at': [60, 624], 'variant': 'b'},
        {'id': 'gorse_5', 'piece': 'brackens_gorse', 'at': [456, 624], 'variant': 'b'},
    ]
    return {'zone': 'brackens_study', 'note': 'Review study (scripts/art/kit/sets/brackens_study.py), not a playable zone.',
            'legend': {'.': 'heath', ',': 'lawn', '#': 'path', 'w': 'worn', 'd': 'drove', 'p': 'peat'},
            'rows': [''.join(r) for r in g], 'pieces': pieces, 'decor': [],
            # the moor's dressing (sets/moor.dress): sheep trods and gritstone breaking through
            'trods': [[(272, 118), (330, 140), (400, 168), (470, 196), (526, 210)],
                      [(600, 452), (650, 470), (712, 500), (760, 520)],
                      [(940, 300), (900, 330), (860, 352), (830, 390)]],
            'outcrops': [[420, 262, 18, 9], [806, 196, 14, 7], [300, 600, 16, 8], [590, 300, 12, 6]]}


def wall_lab() -> dict:
    """Every drystone cell placed where it belongs, as data the checks read (not drawn): a yard
    of four folds (four corners, the four Ts, the cross, straights), gates along x and along y on
    the paths into two of them, sheep and a trough in each; and two walls between houses ending
    against their gables (the four end cells)."""
    W_, H_ = 44, 32
    g = np.full((H_, W_), '.', '<U1')
    cells = {}

    def add(c, r, d):
        cells.setdefault((c, r), set()).add(d)

    def run_x(r, c0, c1):
        for c in range(c0, c1 + 1):
            if c > c0:
                add(c, r, 'w')
            if c < c1:
                add(c, r, 'e')

    def run_y(c, r0, r1):
        for r in range(r0, r1 + 1):
            if r > r0:
                add(c, r, 'n')
            if r < r1:
                add(c, r, 's')
    run_x(1, 1, 15)
    run_x(9, 1, 15)
    run_x(17, 1, 15)
    run_y(1, 1, 17)
    run_y(8, 1, 17)
    run_y(15, 1, 17)
    for c in (3, 4, 5):
        cells.pop((c, 17))                      # the south-west fold's gate along x
    for r in (12, 13, 14):
        cells.pop((15, r))                      # the south-east fold's gate along y
    for r in (3, 4, 5):
        cells.pop((15, r))                      # the north-east fold's, along y
        cells.pop((1, r))                       # the north-west fold's, along y
    g[17:20, 3:6] = '#'
    g[12:15, 15:18] = '#'
    pieces = []
    for (c, r), j in sorted(cells.items(), key=lambda t: (t[0][1], t[0][0])):
        jn = ''.join(s for s in 'nesw' if s in j)
        pieces.append({'id': 'w_%d_%d' % (c, r), 'piece': 'wall_drystone_' + jn, 'at': [c * CELL + 12, (r + 1) * CELL],
                       **({'variant': 'a'} if jn == 'ew' else {})})
    pieces.append({'id': 'gate_x', 'piece': 'wall_drystone_gate_ew', 'at': [4 * CELL + 12, 18 * CELL], 'variant': 'shut'})
    pieces.append({'id': 'gate_y', 'piece': 'wall_drystone_gate_ns', 'at': [15 * CELL + 12, 14 * CELL], 'variant': 'shut'})
    pieces.append({'id': 'gate_y_ne', 'piece': 'wall_drystone_gate_ns', 'at': [15 * CELL + 12, 5 * CELL], 'variant': 'shut'})
    pieces.append({'id': 'gate_y_nw', 'piece': 'wall_drystone_gate_ns', 'at': [1 * CELL + 12, 5 * CELL], 'variant': 'shut'})
    for k, (cx, cy) in enumerate(((4, 5), (11, 5), (4, 13), (11, 13))):
        pieces.append({'id': 'trough_%d' % k, 'piece': 'crossroads_trough', 'at': [cx * CELL, cy * CELL]})
        pieces.append({'id': 'sheep_%d' % k, 'piece': 'farm_sheep', 'at': [cx * CELL + 48, (cy + 2) * CELL]})
    # walls ending against houses: along x between two huts' gables, along y from one hut's front to
    # the next one's back
    pieces += [{'id': 'hut_w', 'piece': 'brackens_shepherds_hut', 'at': [22 * CELL, 9 * CELL]},
               {'id': 'hut_e', 'piece': 'brackens_shepherds_hut', 'at': [32 * CELL, 9 * CELL]},
               {'id': 'hut_n', 'piece': 'brackens_shepherds_hut', 'at': [33 * CELL + 12, 18 * CELL]},
               {'id': 'hut_s', 'piece': 'brackens_shepherds_hut', 'at': [33 * CELL + 12, 29 * CELL]}]
    pieces += [{'id': 'end_e', 'piece': 'wall_drystone_e', 'at': [25 * CELL + 12, 8 * CELL]},
               {'id': 'mid_x', 'piece': 'wall_drystone_ew', 'at': [26 * CELL + 12, 8 * CELL], 'variant': 'b'},
               {'id': 'mid_x2', 'piece': 'wall_drystone_ew', 'at': [27 * CELL + 12, 8 * CELL], 'variant': 'a'},
               {'id': 'end_w', 'piece': 'wall_drystone_w', 'at': [28 * CELL + 12, 8 * CELL]},
               {'id': 'end_s', 'piece': 'wall_drystone_s', 'at': [33 * CELL + 12, 19 * CELL]}]
    pieces += [{'id': 'mid_y%d' % r, 'piece': 'wall_drystone_ns', 'at': [33 * CELL + 12, (r + 1) * CELL]} for r in range(19, 24)]
    pieces += [{'id': 'end_n', 'piece': 'wall_drystone_n', 'at': [33 * CELL + 12, 25 * CELL]}]
    g[10:12, 17:W_] = '#'                       # the lane past the huts' doors
    g[3:12, 16:18] = '#'                        # and up to the north-east fold's gate
    g[3:6, 15:16] = '#'
    g[3:6, 0:2] = '#'                           # the north-west fold's gate from the west
    g[18:20, 26:31] = '#'
    g[29:31, 26:W_] = '#'
    return {'zone': 'brackens_wall_lab', 'note': 'Data only: every drystone cell where it belongs.',
            'legend': {'.': 'heath', '#': 'path'}, 'rows': [''.join(r) for r in g], 'pieces': pieces, 'decor': []}


def _opaque_box(pc, idx):
    e = idx[pc['piece']]
    v = e['variants'].get(pc.get('variant')) or next(iter(e['variants'].values()))
    with Image.open(os.path.join(ROOT, 'game', v['png'][len('res://'):])) as im:
        bb = im.convert('RGBA').getbbox()
    x0, y0 = pc['at'][0] - v['foot'][0], pc['at'][1] - v['foot'][1]
    return (x0 + bb[0], y0 + bb[1], x0 + bb[2], y0 + bb[3])


def layout_faults(p: dict | None = None) -> list:
    """The staging rules (as farm_study.layout_faults): every animal's foot at least a cell from a
    wall line and off the paths; no animal, trough or prop (a building's roof may be) drawn over a
    wall behind it; no two props'
    pictures overlapping except where one stands wholly in front (a tall roof over the ground north
    of it is the three-quarter view, two props' bodies meeting is not)."""
    from scripts.art.kit import build as _B  # noqa: F401  (configures the density)
    from scripts.art.kit import compose as CO
    from scripts.art.kit import enclosures as EN
    p = p or plan()
    idx = CO.piece_index()
    lib = EN.library()
    out = []
    segs = EN.segments(p, lib)
    walls = []
    for a, b, pc, s in segs:
        x0, x1 = sorted((a[0], b[0]))
        y0, y1 = sorted((a[1], b[1]))
        walls.append((x0 - 8, y0 - 50, x1 + 8, y1 + 8, pc['id'], pc['at'][1]))
    things = [pc for pc in p['pieces'] if not (lib[pc['piece']].get('placement') or {}).get('boundary')]
    boxes = {pc['id']: _opaque_box(pc, idx) for pc in things}

    def hit(r, q, tol=3):
        return r[0] + tol < q[2] and q[0] + tol < r[2] and r[1] + tol < q[3] and q[1] + tol < r[3]
    for pc in things:
        r = boxes[pc['id']]
        building = (lib[pc['piece']].get('placement') or {}).get('role') in EN.WALLS
        for q in walls:
            # a building's roof over a wall behind it (one built against its back) is the view
            if not building and q[5] <= pc['at'][1] and hit(r, q):
                out.append('%s is drawn over the wall %s' % (pc['id'], q[4]))
        for other in things:
            if other['id'] < pc['id'] and hit(r, boxes[other['id']]):
                # the nearer one may hide the other's top only (the three-quarter view): their feet
                # at least a cell apart in y, and the farther one's ground box clear of the nearer's
                near, far = (pc, other) if pc['at'][1] > other['at'][1] else (other, pc)
                fb = boxes[far['id']]
                foot = (fb[0], far['at'][1] - 12, fb[2], fb[3])
                if near['at'][1] - far['at'][1] < CELL or hit(foot, boxes[near['id']]):
                    out.append('%s and %s are drawn over each other' % (pc['id'], other['id']))
        if lib[pc['piece']]['placement'].get('role') == 'stock':
            fx, fy = pc['at']
            for a, b, q, s in segs:
                x0, x1 = sorted((a[0], b[0]))
                y0, y1 = sorted((a[1], b[1]))
                if max(max(x0 - fx, 0, fx - x1), max(y0 - fy, 0, fy - y1)) < CELL:
                    out.append('%s stands within a cell of the wall %s' % (pc['id'], q['id']))
                    break
            if p['rows'][int((fy - 1) // CELL)][int(fx // CELL)] == '#':
                out.append('%s stands on the path' % pc['id'])
    return out


def render(p: dict | None = None) -> Image.Image:
    """The bake of the plan's ground (its cast shadows included) dressed as moor (sets/moor.dress),
    and every piece's still, by foot; a looping piece shows its frame 0 (the reduced-motion picture)."""
    from scripts.art.kit import bake as BK
    from scripts.art.kit import compose as CO
    from scripts.art.kit.sets import moor as MO
    p = p or plan()
    ground, _ = BK.bake(p)
    bare = dict(p, pieces=[])
    plain, _ = BK.bake(bare)
    img = MO.dress(p, ground, plain).convert('RGBA')
    idx = CO.piece_index()
    for pc in sorted(p['pieces'], key=lambda q: (q['at'][1], q['at'][0])):
        e = idx[pc['piece']]
        v = e['variants'].get(pc.get('variant')) or next(iter(e['variants'].values()))
        sp = Image.open(os.path.join(ROOT, 'game', v['png'][len('res://'):])).convert('RGBA')
        img.alpha_composite(sp, (int(pc['at'][0] - v['foot'][0]), int(pc['at'][1] - v['foot'][1])))
        an = e.get('anim')
        if an and not an.get('cover'):
            st = Image.open(os.path.join(ROOT, 'game', an['strip'][len('res://'):])).convert('RGBA')
            w = st.width // an['frames']
            img.alpha_composite(st.crop((0, 0, w, st.height)), (int(pc['at'][0] + an['offset'][0]), int(pc['at'][1] + an['offset'][1])))
    return img


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('out')
    ap.add_argument('--scale', type=int, default=1)
    a = ap.parse_args(argv)
    img = render()
    if a.scale > 1:
        img = img.resize((img.width * a.scale, img.height * a.scale), Image.NEAREST)
    img.save(a.out)
    print('wrote', a.out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
