"""The woodland rebuilt with the kit (docs/world-editor.md, "Prototype"): its plan as a kit zone plan.

    python3 -m scripts.art.kit.woodland_kit       # writes game/kit/zones/woodland_kit.json

From the woodland's own plan (art/scenes/woodland.json) and base scene, with nothing painted:
- cells (40 x 72): lawn; the talus band along the top as scree; the path network and the stone
  ring's worn track as path (routes two cells wide, the spur one); the river (three cells), the
  pool and the rill (two cells) as water, which wins where a route crosses it;
- pieces: every object of the woodland's base scene as its library piece at the same foot, the
  talus and the spring's boulders as the kit's boulder (nearest size), the footbridge on the
  path's crossing;
- gameplay: the woodland scene's Actors, Spawns and Doors (gameplay_from), plus its stands.

The result is a JSON plan; game/tools/kit_zone.gd turns it into zones/woodland_kit/woodland_kit.tscn.
"""
from __future__ import annotations

import json
import os
import re
import sys

import numpy as np

from scripts.art.kit import build as B
from scripts.art.kit.schema import ROOT
from scripts.art.native import softgrid as SG

D = 3
CELL_W = 8


def cells_of(plan) -> np.ndarray:
    W, H = plan['screen']['w'], plan['screen']['h']
    h, w = H * D, W * D
    gh, gw = SG.grid_shape(h, w)
    grid = np.full((gh, gw), '.', '<U1')
    # the talus under the escarpment along the top edge
    depth = int(round(np.mean(plan['rock']['talus']['depth']) / CELL_W))
    grid[:max(1, depth)] = 's'
    # routes
    for p in plan['paths']:
        n = max(1, int(round(2 * p['radius'] / 8.0)))
        grid[SG.cells_route(p['points'], n, h, w)] = '#'
    # the stone ring's worn track: cells whose centres lie between the outer and inner ellipses
    pl = plan['places']
    co, ci = pl['circle_out'], pl['circle_in']
    cy, cx = (np.mgrid[0:gh, 0:gw] + 0.5) * CELL_W
    out_ = ((cx - co['at'][0]) / co['r'][0]) ** 2 + ((cy - co['at'][1]) / co['r'][1]) ** 2 <= 1
    in_ = ((cx - ci['at'][0]) / ci['r'][0]) ** 2 + ((cy - ci['at'][1]) / ci['r'][1]) ** 2 <= 1
    grid[SG.join4(out_ & ~in_) & (grid != '#')] = 'w'    # worn ground, not a route: the stones stand on it
    # water wins where a route crosses it (the footbridge spans it)
    s = plan['water']['soft']
    wat = SG.cells_route(s['river']['points'], s['river']['cells'], h, w)
    wat |= SG.cells_rects(s['river'].get('add', []), h, w)
    wat &= ~SG.cells_rects(s['river'].get('cut', []), h, w)
    wat |= SG.cells_rects(s['pool'], h, w)
    wat |= SG.cells_route(s['rill']['points'], s['rill']['cells_plan'], h, w)
    # the rill runs on into the pool where the woodland's fall drops (the fall itself is a piece to come)
    f = plan['water']['fall']
    wat |= SG.cells_rects([[f['x0'], f['y0'], f['w'], f['y1'] - f['y0']]], h, w)
    grid[wat] = '~'
    return grid


def base_objects() -> list:
    """(name, kind, x, y) of every sprite in the woodland base scene's Objects, texels."""
    txt = open(os.path.join(ROOT, 'game', 'zones', 'woodland', 'woodland_base.tscn')).read()
    out = []
    for m in re.finditer(r'\[node name="([^"]+)" type="Sprite2D" parent="Objects"\]\nposition = Vector2\((-?[\d.]+), (-?[\d.]+)\)\n'
                         r'texture = ExtResource\("t_([a-z_]+)"\)', txt):
        out.append((m.group(1), m.group(4), float(m.group(2)), float(m.group(3))))
    return out


def stands() -> dict:
    txt = open(os.path.join(ROOT, 'game', 'zones', 'woodland', 'woodland_base.tscn')).read()
    return {m.group(1): [float(m.group(2)), float(m.group(3))]
            for m in re.finditer(r'\[node name="([^"]+)" type="Marker2D" parent="Stands"\]\nposition = Vector2\((-?[\d.]+), (-?[\d.]+)\)', txt)}


def boulder_variant(size) -> str:
    from scripts.art.kit.structures import BOULDERS
    w = size[0]
    return 'b%d' % int(np.argmin([abs(b[0] - w) for b in BOULDERS]))


def pieces_of(plan) -> list:
    out = []
    for name, kind, x, y in base_objects():
        out.append({'id': name, 'piece': 'woodland_' + kind, 'at': [int(round(x)), int(round(y))], 'variant': kind})
    for i, b in enumerate(plan['rock']['talus']['boulders'] + plan['rock']['heap']):
        out.append({'id': 'boulder-%d' % (i + 1), 'piece': 'woodland_boulder',
                    'at': [int(round(b['at'][0] * D)), int(round(b['at'][1] * D))], 'variant': boulder_variant(b['size'])})
    br = plan['places']['bridge']
    fb = json.load(open(os.path.join(ROOT, 'game', 'kit', 'pieces', 'structure', 'woodland_footbridge.json')))
    # the bridge's sprite spans the river with 24 texels above its north bank (structures.py)
    river_top = int(round((plan['water']['soft']['river']['points'][0][1] - 12) * D))
    fy = river_top - 24 + fb['geometry']['foot'][1]
    out.append({'id': 'footbridge', 'piece': 'woodland_footbridge',
                'at': [int(round((br['x0'] + br['w'] / 2) * D)), int(round(fy))], 'variant': 'river3'})
    return out


def main(argv=None) -> int:
    plan = json.load(open(os.path.join(ROOT, 'art', 'scenes', 'woodland.json')))
    kit = B.Kit()
    grid = cells_of(plan)
    st = stands()
    out = {
        'zone': 'woodland_kit',
        'note': 'The woodland rebuilt with the kit (scripts/art/kit/woodland_kit.py): its plan as cells and pieces, '
                'its gameplay from zones/woodland/woodland.tscn. Regenerate, do not edit by hand; '
                'or paint the scene and export it back (game/tools/kit_zone.gd --export).',
        'legend': {'.': 'lawn', '#': 'path', '~': 'water', 's': 'scree', 'w': 'worn'},
        'rows': [''.join(r) for r in grid],
        'pieces': pieces_of(plan),
        'gameplay_from': 'res://zones/woodland/woodland.tscn',
        'lab': True,
        'spawns': {k: v for k, v in st.items()},
    }
    for k in out['legend'].values():
        assert k in kit.ids, k
    path = os.path.join(ROOT, 'game', 'kit', 'zones', 'woodland_kit.json')
    json.dump(out, open(path, 'w'), indent=1)
    open(path, 'a').write('\n')
    print('woodland_kit: %d x %d cells, %d pieces' % (grid.shape[1], grid.shape[0], len(out['pieces'])))
    return 0


if __name__ == '__main__':
    sys.exit(main())
