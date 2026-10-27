"""A kit zone's walk mask for the review tools (walk.txt, 4 world px cells, '#' blocked), derived
from the cells' metadata and the pieces' collision and decks; the game builds the same blocking
from the same data at run time (TerrainGround._build_blocked and the pieces' bodies).

    python3 -m scripts.art.kit.walk <zone>      # writes game/zones/<zone>/walk.txt
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

from scripts.art.kit.schema import ROOT
from scripts.review import kit_rules as KR

STEP = 12       # texels: 4 world px


def mask(plan) -> np.ndarray:
    mats, idx = KR.load_kit()
    g = KR.grid(plan, mats)
    H, W = g.shape
    blk = KR.blocked_cells(g, mats, plan, idx)
    k = KR.CELL // STEP
    out = np.kron(blk.astype(np.uint8), np.ones((k, k), np.uint8)).astype(bool)
    for p in plan.get('pieces', []):
        e = idx.get(p['piece'])
        if not e or not e.get('collision') or not e.get('blocks_move'):
            continue
        x, y, w, h = e['collision']
        x0, y0 = p['at'][0] + x, p['at'][1] + y
        out[max(0, int(y0 // STEP)):int(np.ceil((y0 + h) / STEP)), max(0, int(x0 // STEP)):int(np.ceil((x0 + w) / STEP))] = True
    return out


def main(argv=None) -> int:
    zone = (argv or sys.argv[1:])[0]
    plan = json.load(open(os.path.join(ROOT, 'game', 'kit', 'zones', zone + '.json')))
    m = mask(plan)
    path = os.path.join(ROOT, 'game', 'zones', zone, 'walk.txt')
    open(path, 'w').write('\n'.join(''.join('#' if v else '.' for v in r) for r in m) + '\n')
    print('walk: %s (%d x %d, %d blocked)' % (path, m.shape[1], m.shape[0], int(m.sum())))
    return 0


if __name__ == '__main__':
    sys.exit(main())
