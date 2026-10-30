"""Approval sheets for the terrain kit (the library gate, docs/world-editor.md).

    python3 -m scripts.art.kit.sheet OUT_DIR [--layout lab]

writes OUT_DIR/kit_tiles_3x.png (every transition's 14 masks x variants, 3x, on the dual grid),
OUT_DIR/kit_<layout>.png (the test layout rendered by compose.render, 1:1) and
OUT_DIR/kit_<layout>_3x.png (its middle at 3x), plus kit_<layout>.cells.json for Godot.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

from scripts.art.kit.build import Kit  # configures the density
from scripts.art.kit import compose
from scripts.art.kit.edges import CELL
from scripts.art.native.palette import to_rgba

# The lab: a lawn crossed by a path network that exercises every mask: straight runs 2 and 3
# cells wide, turns both ways, a T and a crossing, a one-cell spur, a plaza with a lawn island,
# a lone lawn cell and a lone path cell, and a diagonal saddle; a stream two cells wide falling
# into a pond with an island and a river three cells wide. '.' lawn, '#' path, '~' water.
LAB = """
........................................
.....................................~~.
..##############..............###....~~.
..##############..............###....~~.
..##........................#####....~~.
..##........................#####....~~.
..##..........######..........###....~~.
..##..........######..........###....~~.
..############################.......~~.
..############################.......~~.
..............##..##..........#......~~.
....#.........######...........#.....~~.
...........................##........~~.
..........................##.........~~.
...######......#####.....##.....~~~~~~~.
...######......#...#...........~~~~~~~~.
...##..##......#####.....##....~~~.~~~~.
...######...............####...~~~~~~~..
................................~~~~~...
...~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~..
...~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~..
...~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~..
........................................
"""


def parse(text: str, kit: Kit) -> np.ndarray:
    rows = [r for r in text.strip('\n').split('\n')]
    key = {'.': kit.ids['lawn'], '#': kit.ids['path'], '~': kit.ids['water']}
    return np.array([[key[c] for c in r] for r in rows], np.int32)


def masks_sheet(kit: Kit, s: int = 3, per_mask: int = 18) -> Image.Image:
    """Each mask's first `per_mask` tiles (its crossing profiles times the variants), the upper
    material over the lower, at s x: one row per mask."""
    from scripts.art.native.palette import step
    from scripts.art.kit.edges import OP_ABS, OP_DELTA, OP_UPPER, layout
    pad = 6
    blocks = []
    for (u, lname), tid in kit.pairs.items():
        lo = kit.ids[lname] if lname in kit.ids else u
        rows = {}
        for idx, k, prof, v in layout(kit.variants):
            row = rows.setdefault(k, [])
            if len(row) >= per_mask:
                continue
            t = kit.over[tid][idx]
            op, val = t[..., 0], t[..., 1]
            y0, x0 = 96 + 24 * len(row), 96 + 24 * k
            fu = kit.fills[u][y0:y0 + CELL, x0:x0 + CELL]
            fl = kit.fills[lo][y0:y0 + CELL, x0:x0 + CELL]
            code = fl.copy()
            code = np.where(op == OP_UPPER, step(fu, val - 128), code)
            code = np.where(op == OP_DELTA, step(code, val - 128), code)
            code = np.where(op == OP_ABS, val, code)
            row.append(code)
        blocks.append(rows)
    cw = (CELL + pad) * s
    W = per_mask * cw + pad * s
    H = sum(len(b) for b in blocks) * cw + pad * s
    out = Image.new('RGB', (W, H), (36, 36, 40))
    d = ImageDraw.Draw(out)
    y = pad * s
    for rows in blocks:
        for k in sorted(rows):
            d.text((2, y), '%d' % k, fill=(160, 160, 170))
            for n, code in enumerate(rows[k]):
                im = Image.fromarray(to_rgba(code)[..., :3]).resize((CELL * s, CELL * s), Image.NEAREST)
                out.paste(im, (pad * s + n * cw, y))
            y += cw
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('out')
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    kit = Kit()
    cells = parse(LAB, kit)
    img = compose.render(cells, kit)
    rgb = to_rgba(img)[..., :3]
    Image.fromarray(rgb).save(os.path.join(a.out, 'kit_lab.png'))
    h, w = rgb.shape[:2]
    crop = rgb[h // 2 - 160:h // 2 + 160, w // 2 - 280:w // 2 + 280]
    Image.fromarray(crop).resize((crop.shape[1] * 3, crop.shape[0] * 3), Image.NEAREST).save(os.path.join(a.out, 'kit_lab_3x.png'))
    masks_sheet(kit).save(os.path.join(a.out, 'kit_tiles_3x.png'))
    json.dump({'cells': cells.tolist()}, open(os.path.join(a.out, 'kit_lab.cells.json'), 'w'))
    print('wrote', a.out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
