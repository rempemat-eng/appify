"""The four facings of the kit's characters on one review sheet (Claude J).

Bramble and the Mossling, S, N, E and W, idle frame 0 and walk frames 0 to 5, drawn at 2x
density and shown at 3x on the house grass body (grass tone 3). The sheet is assembled with
numpy (no PIL drawing) and is deterministic: the same kit gives the same bytes.

    python3 scripts/art/characters/kit_review.py [out.png]
    default out: docs/vision/characters/kit/four-facings.png
"""
from __future__ import annotations

import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from scripts.art.native import chars, palette  # noqa: E402
from scripts.art.native.rig import TIMING  # noqa: E402

DENSITY = 2
SHOW = 3
GAP = 4               # texels between cells
FACINGS = ('S', 'N', 'E', 'W')
COLUMNS = [('idle', 0)] + [('walk', i) for i in range(TIMING['walk']['frames'])]


def cells():
    rows = []
    for name, fn in (('bramble', chars.bramble), ('mossling', chars.mossling)):
        for f in FACINGS:
            rows.append([np.asarray(fn(DENSITY, a, f, i).convert('RGBA')) for a, i in COLUMNS])
    return rows


def sheet() -> Image.Image:
    rows = cells()
    cw = max(c.shape[1] for r in rows for c in r)
    rh = [max(c.shape[0] for c in r) for r in rows]
    W = GAP + len(COLUMNS) * (cw + GAP)
    H = GAP + sum(h + GAP for h in rh)
    out = np.zeros((H, W, 3), np.uint8)
    out[:] = palette.rgb('grass', 3)
    y = GAP
    for r, h in zip(rows, rh):
        x = GAP
        for c in r:
            ch, cwid = c.shape[:2]
            oy, ox = y + h - ch, x + (cw - cwid) // 2       # feet on a common line
            a = c[..., 3:4].astype(np.float32) / 255.0
            dst = out[oy:oy + ch, ox:ox + cwid].astype(np.float32)
            out[oy:oy + ch, ox:ox + cwid] = np.round(c[..., :3] * a + dst * (1 - a)).astype(np.uint8)
            x += cw + GAP
        y += h + GAP
    out = out.repeat(SHOW, axis=0).repeat(SHOW, axis=1)
    return Image.fromarray(out, 'RGB')


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    path = argv[0] if argv else os.path.join(ROOT, 'docs', 'vision', 'characters', 'kit', 'four-facings.png')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sheet().save(path, optimize=True)
    print(path)


if __name__ == '__main__':
    main()
