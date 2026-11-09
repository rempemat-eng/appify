"""Checker dither inside a sprite: a patch drawn as a 1-texel checkerboard of two colours (or of a
colour and holes), which house-style.md 4 allows only on ground for an atmospheric fade, never on a
sprite and never to shade a form (the detail audit of the Act 1 props, round 2: the net rack's foot,
"a 1 px checker, which is dither on a sprite").

**The measure.** Each 2 x 2 window of the picture is a checker when its two diagonals each hold one
colour (or both are transparent on one diagonal) and the two diagonals differ, with at least one
opaque texel. Windows along a single diagonal line (a stroke, a mesh's twine) touch only at their
corners; a dithered patch is a block of checker windows side by side. The finding is the largest
4-connected block of checker windows, against `MIN_WINDOWS`.

**The threshold** rests on our own art alone: the Eastward references are JPEG, so an exact-colour
checker never occurs in them (their largest block is 5). In the sweep of round 3 of the Act 1 detail
audit (2,770 sprites) the highest non-exempt picture outside the known fault scored 6
(`waterfall_3`, `waterfall_3_tall`, Ashe's `primary_W` sheet) and the v4 net 5, while the v3 net's
foot scored 9; 7 keeps a margin on both sides. `crossroads/square_puddles` scores 58: its damp
margins are a 1-texel checker on a ground-overlay sprite, a true positive left flagged for its own
fix.

    python3 -m scripts.review.checker_dither PNG [PNG ...]
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

from .core import Finding

MIN_WINDOWS = 7      # a block of 7 checker windows (about 3 x 5 texels of dither) is a dithered patch
EFFECTS = ('flow', 'smoke', 'mist', 'spray', '_shadow', '/fx')   # effects and shadows may fade in a checker


def checker_windows(rgba: np.ndarray) -> np.ndarray:
    """(H-1, W-1) bool: the 2 x 2 windows that are a checker."""
    a = rgba.astype(np.int64)
    op = a[..., 3] > 128
    key = np.where(op, (a[..., 0] // 8) * 1024 + (a[..., 1] // 8) * 32 + a[..., 2] // 8, -1)
    tl, tr, bl, br = key[:-1, :-1], key[:-1, 1:], key[1:, :-1], key[1:, 1:]
    any_op = op[:-1, :-1] | op[:-1, 1:] | op[1:, :-1] | op[1:, 1:]
    return (tl == br) & (tr == bl) & (tl != tr) & any_op


def measure(rgba: np.ndarray):
    """(the largest block of checker windows, its box (x0, y0, x1, y1))."""
    w = checker_windows(rgba)
    lab, n = ndi.label(w)
    if n == 0:
        return 0, (0, 0, 0, 0)
    sizes = np.bincount(lab.ravel())[1:]
    k = int(np.argmax(sizes)) + 1
    ys, xs = np.nonzero(lab == k)
    return int(sizes[k - 1]), (int(xs.min()), int(ys.min()), int(xs.max()) + 2, int(ys.max()) + 2)


def check(rgba: np.ndarray, H: float, subject: str) -> list[Finding]:
    """The asset gate's checker-dither finding on one object picture (RGBA, holes included)."""
    if any(e in subject for e in EFFECTS):
        return []
    n, box = measure(rgba)
    if n < MIN_WINDOWS:
        return []
    return [Finding('detail.dither', 'fault', box,
                    f'{subject}: a patch of {n} 2 x 2 windows is a 1-texel checker: dither on a sprite',
                    'draw the material instead (a net as twine in diamonds 3 to 4 texels across with the ground showing '
                    'between them, a shade as a solid band a tone down); dither belongs only to ground, for an '
                    'atmospheric fade (house-style.md 4)', score=float(n), threshold=float(MIN_WINDOWS), subject=subject)]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('png', nargs='+')
    a = ap.parse_args(argv)
    for p in a.png:
        im = np.asarray(Image.open(p).convert('RGBA'))
        n, box = measure(im)
        print('%-50s checker block %4d windows %s' % (os.path.basename(p), n, box))
    return 0


if __name__ == '__main__':
    sys.exit(main())
