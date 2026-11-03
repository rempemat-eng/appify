"""A farmyard built only from kit pieces, as a review study (not a playable zone): a chicken run
with its coop and hens, a sheep fold with its shelter, trough, hay and flock, and a cottage's front
garden behind a picket with its gate on the door path; every pen's gate on the trodden way to the
lane (docs/vision/placement-logic.md).

    python3 -m scripts.art.kit.farm_study OUT.png [--scale 3]     # the baked frame with every sprite

The plan has the kit zones' shape (game/kit/zones/*.json), so the editor's checks read it as they
read a zone: scripts/review/kit_rules.py, scripts/art/kit/relations.py and enclosures.py (test_kit
keeps it at 0 faults).
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np
from PIL import Image

from scripts.art.kit.schema import ROOT

CELL = 24
COLS, ROWS = 36, 22


def _ring(style, c0, c1, r0, r1, gate_col, prefix):
    """A closed loop of fence cells: y-runs on columns c0 and c1 (cell centres), x-runs on the
    bottom lines of rows r0 and r1; a gate three cells wide on the south run, centred on gate_col."""
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
    out = []
    for c in (gate_col - 1, gate_col, gate_col + 1):
        cells.pop((c, r1))
    for (c, r), j in sorted(cells.items(), key=lambda t: (t[0][1], t[0][0])):
        jn = ''.join(s for s in 'nesw' if s in j)
        straight = j in ({'e', 'w'}, {'n', 's'})
        pc = {'id': '%s_%d_%d' % (prefix, c, r), 'piece': 'fence_%s_%s' % (style, jn), 'at': [c * CELL + 12, (r + 1) * CELL]}
        if straight:
            pc['variant'] = 'post' if (c + r) % 4 == 0 and style == 'picket' else 'plain'
        out.append(pc)
    out.append({'id': prefix + '_gate', 'piece': 'fence_%s_gate_ew' % style, 'at': [gate_col * CELL + 12, (r1 + 1) * CELL],
                'variant': 'open' if style == 'wattle' else 'shut'})
    return out


def _front_garden(style, c0, c1, r_wall, r1, gate_col, prefix):
    """A front garden: side runs from the house's front wall (end posts against it, on the line
    r_wall) south to the front run on row r1's line, its gate on the door path."""
    cells = {}
    for r in range(r_wall, r1 + 1):
        for c in (c0, c1):
            j = cells.setdefault((c, r), set())
            if r > r_wall:
                j.add('n')
            if r < r1:
                j.add('s')
    for c in range(c0, c1 + 1):
        j = cells.setdefault((c, r1), set())
        if c > c0:
            j.add('w')
        if c < c1:
            j.add('e')
    for c in (gate_col - 1, gate_col, gate_col + 1):
        cells.pop((c, r1))
    out = []
    for (c, r), j in sorted(cells.items(), key=lambda t: (t[0][1], t[0][0])):
        jn = ''.join(s for s in 'nesw' if s in j)
        pc = {'id': '%s_%d_%d' % (prefix, c, r), 'piece': 'fence_%s_%s' % (style, jn), 'at': [c * CELL + 12, (r + 1) * CELL]}
        if j in ({'e', 'w'}, {'n', 's'}):
            pc['variant'] = 'plain'
        out.append(pc)
    out.append({'id': prefix + '_gate', 'piece': 'fence_%s_gate_ew' % style, 'at': [gate_col * CELL + 12, (r1 + 1) * CELL],
                'variant': 'shut'})
    return out


def plan() -> dict:
    g = np.full((ROWS, COLS), '.', '<U1')
    g[19:21, :] = '#'                                   # the lane along the bottom
    # the chicken run (4 x 3 cells), scratched bare inside, its gate's trodden way to the lane
    g[11:14, 4:7] = 'w'
    g[13:19, 5:7] = '#'
    # the sheep fold (8 x 6 cells): worn by the trough and the gate, the way to the lane
    g[8:10, 13:18] = 'w'
    g[9:19, 14:16] = '#'
    # the cottage's door path through its garden gate to the lane
    g[12:19, 26:28] = '#'
    pieces = []
    pieces += _ring('wattle', 3, 7, 10, 13, 5, 'run')
    pieces += _ring('wattle', 10, 18, 3, 9, 14, 'fold')
    pieces += _front_garden('picket', 24, 32, 11, 16, 26, 'garden')
    pieces += [
        # the run: the coop in its back corner, three hens about it
        {'id': 'coop', 'piece': 'farm_coop', 'at': [120, 288]},
        {'id': 'hen_1', 'piece': 'farm_hen_white', 'at': [108, 312]},
        {'id': 'hen_2', 'piece': 'farm_hen_brown', 'at': [156, 288]},
        {'id': 'hen_3', 'piece': 'farm_hen_speckled', 'at': [156, 312]},
        # the fold: the shelter against the north hurdles, the trough by the gate, hay, the flock
        {'id': 'shelter', 'piece': 'farm_shelter', 'at': [336, 168]},
        {'id': 'trough', 'piece': 'crossroads_trough', 'at': [408, 192]},
        {'id': 'hay', 'piece': 'crossroads_hay', 'at': [420, 120], 'variant': 'hay_heap'},
        {'id': 'sheep_1', 'piece': 'farm_sheep', 'at': [312, 216]},
        {'id': 'sheep_2', 'piece': 'farm_sheep_graze', 'at': [420, 144]},
        {'id': 'sheep_3', 'piece': 'farm_sheep_lie', 'at': [300, 192]},
        # the cottage and its front garden: two flower borders east of the door path
        {'id': 'cottage', 'piece': 'crossroads_fern_cottage', 'at': [696, 288]},
        {'id': 'border_1', 'piece': 'garden_flower_border', 'at': [708, 312]},
        {'id': 'border_2', 'piece': 'garden_flower_border', 'at': [708, 360]},
    ]
    return {'zone': 'farm_study', 'note': 'Review study (scripts/art/kit/farm_study.py), not a playable zone.',
            'legend': {'.': 'lawn', '#': 'path', 'w': 'worn'}, 'rows': [''.join(r) for r in g], 'pieces': pieces, 'decor': []}


def render(p: dict | None = None) -> Image.Image:
    """The bake of the plan's ground (its cast shadows included) and every piece's still, by foot."""
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
