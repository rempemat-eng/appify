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
COLS, ROWS = 40, 24


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
    g = np.full((ROWS, COLS), '.', '<U1')
    g[17:19, :] = '#'                       # the Drover's Road
    g[0:17, 22:24] = '#'                    # the trod north from the fingerpost
    g[11:17, 5:8] = '#'                     # the fold's gateway from the road
    g[0:5, 8] = '#'                         # the footpath to the stile over the fold's back wall
    g[5:11, 8] = 'w'                        # trodden inside the fold, stile to gate
    g[8:11, 3:6] = 'w'                      # worn round the trough
    g[16, 28:30] = 'w'                      # the hut's door step to the road
    g[2:4, 25:28] = 'w'                     # bare round the hermit's fire
    pieces = _ring(2, 10, 4, 11, 6, 8, 'fold')
    pieces += [
        # the fold: the trough against the west wall, the flock spread clear of the walls and the way
        {'id': 'trough', 'piece': 'crossroads_trough', 'at': [120, 216]},
        {'id': 'sheep_1', 'piece': 'farm_sheep', 'at': [180, 168]},
        {'id': 'sheep_2', 'piece': 'farm_sheep_graze', 'at': [120, 264]},
        {'id': 'sheep_3', 'piece': 'farm_sheep_lie', 'at': [204, 240]},
        # by the road: the drovers' seat at the west end, the drove well, the fingerpost at the junction
        {'id': 'seat', 'piece': 'brackens_bench', 'at': [48, 408]},
        {'id': 'well', 'piece': 'brackens_drove_well', 'at': [372, 384]},
        {'id': 'fingerpost', 'piece': 'commons_fingerpost_new', 'at': [516, 408]},
        {'id': 'fingerpost_fold', 'piece': 'commons_fingerpost_new', 'at': [204, 408]},
        # the shepherd's hut, its door to the road, its peat stack at the gable
        {'id': 'hut', 'piece': 'brackens_shepherds_hut', 'at': [756, 384]},
        {'id': 'peat', 'piece': 'brackens_peat_stack', 'at': [900, 384]},
        # the verge south of the road
        {'id': 'cart', 'piece': 'brackens_cart_broken', 'at': [336, 504]},
        {'id': 'fire_cold', 'piece': 'brackens_fire_ring_cold', 'at': [192, 504]},
        {'id': 'ruin', 'piece': 'brackens_fold_ruin', 'at': [588, 552]},
        {'id': 'cairn_toppled', 'piece': 'brackens_cairn', 'at': [72, 504], 'variant': 'toppled'},
        # up the trod: a cairn beside it, the hermit's fire off it
        {'id': 'cairn', 'piece': 'brackens_cairn', 'at': [492, 144], 'variant': 'standing'},
        {'id': 'hermit_fire', 'piece': 'brackens_fire_ring_lit', 'at': [636, 96]},
        # gorse at the edges
        {'id': 'gorse_1', 'piece': 'brackens_gorse', 'at': [348, 72], 'variant': 'a'},
        {'id': 'gorse_2', 'piece': 'brackens_gorse', 'at': [900, 96], 'variant': 'b'},
        {'id': 'gorse_3', 'piece': 'brackens_gorse', 'at': [804, 576], 'variant': 'a'},
        {'id': 'gorse_4', 'piece': 'brackens_gorse', 'at': [60, 576], 'variant': 'b'},
        {'id': 'gorse_5', 'piece': 'brackens_gorse', 'at': [444, 576], 'variant': 'b'},
    ]
    return {'zone': 'brackens_study', 'note': 'Review study (scripts/art/kit/sets/brackens_study.py), not a playable zone.',
            'legend': {'.': 'lawn', '#': 'path', 'w': 'worn'}, 'rows': [''.join(r) for r in g], 'pieces': pieces, 'decor': []}


def _opaque_box(pc, idx):
    e = idx[pc['piece']]
    v = e['variants'].get(pc.get('variant')) or next(iter(e['variants'].values()))
    with Image.open(os.path.join(ROOT, 'game', v['png'][len('res://'):])) as im:
        bb = im.convert('RGBA').getbbox()
    x0, y0 = pc['at'][0] - v['foot'][0], pc['at'][1] - v['foot'][1]
    return (x0 + bb[0], y0 + bb[1], x0 + bb[2], y0 + bb[3])


def layout_faults(p: dict | None = None) -> list:
    """The staging rules (as farm_study.layout_faults): every animal's foot at least a cell from a
    wall line and off the paths; no animal, trough or prop drawn over a wall behind it; no two props'
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
        for q in walls:
            if q[5] <= pc['at'][1] and hit(r, q):
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
    """The bake of the plan's ground (its cast shadows included) and every piece's still, by foot; a
    looping piece shows its frame 0 (the reduced-motion picture)."""
    from scripts.art.kit import bake as BK
    from scripts.art.kit import compose as CO
    p = p or plan()
    ground, _ = BK.bake(p)
    img = ground.convert('RGBA')
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
