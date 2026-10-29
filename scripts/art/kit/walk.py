"""A kit zone's walk mask for the review tools (walk.txt, 4 world px cells, '#' blocked), derived
from the cells' metadata and the pieces' collision and decks; the game builds the same blocking
from the same data at run time (TerrainGround._build_blocked and the pieces' bodies).
Piece positions are texels by default; coordinate_space="cells" uses 24-texel cells.
The library's collision/deck rectangles remain texels in either format.

    python3 -m scripts.art.kit.walk <zone>      # writes game/zones/<zone>/walk.txt
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np

from scripts.art.kit.schema import ROOT
from scripts.review import kit_rules as KR

STEP = 12       # texels: 4 world px


def _texel_plan(plan):
    """Copy piece positions into texels once, before both decks and solids."""
    space = plan.get('coordinate_space', 'texels')
    if space not in ('texels', 'cells'):
        raise ValueError('coordinate_space must be texels or cells')
    factor = KR.CELL if space == 'cells' else 1
    pieces = []
    for piece in plan.get('pieces', []):
        at = piece.get('at') if isinstance(piece, dict) else None
        try:
            valid = isinstance(at, (list, tuple)) and len(at) == 2 and all(
                isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
                for v in at)
            position = [v * factor for v in at] if valid else []
            valid = valid and all(math.isfinite(v) for v in position)
        except OverflowError:
            valid = False
        if not valid:
            raise ValueError('every piece needs a finite [x,y] at position')
        pieces.append(dict(piece, at=position))
    return dict(plan, pieces=pieces, coordinate_space='texels')


def mask(plan) -> np.ndarray:
    plan = _texel_plan(plan)
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
    with open(os.path.join(ROOT, 'game', 'kit', 'zones', zone + '.json')) as stream:
        plan = json.load(stream)
    try:
        m = mask(plan)
    except ValueError as error:
        print('walk: %s' % error, file=sys.stderr)
        return 1
    path = os.path.join(ROOT, 'game', 'zones', zone, 'walk.txt')
    with open(path, 'w') as stream:
        stream.write('\n'.join(''.join('#' if v else '.' for v in r) for r in m) + '\n')
    print('walk: %s (%d x %d, %d blocked)' % (path, m.shape[1], m.shape[0], int(m.sum())))
    return 0


if __name__ == '__main__':
    sys.exit(main())
