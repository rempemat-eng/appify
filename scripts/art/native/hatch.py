"""The Undercroft's hatch in the woodland: a weathered oak trapdoor in a stone kerb, closed or open.

    python3 -m scripts.art.native.hatch            # writes game/zones/woodland/art/hatch_closed.png, hatch_open.png
    python3 -m scripts.art.native.hatch --check    # fails if the committed pictures differ from the painter

Lane R, 3 Nov: the door `Doors/ToUndercroft` (woodland.tscn, a 30 x 24 texel collision) had only a
flat placeholder rectangle, which #417 removed, leaving nothing drawn. The opening is exactly that
collision; a kerb of dressed stones four texels wide rings it (its south course shows a two-texel
front, the kerb standing a little proud of the turf).

- closed: oak planks running north to south, each its own tone (oak, warm, cool), lit along its west
  edge and dark at its east joint, grain in short dashes, weathered patches; the kerb's north and west
  inner edges throw a texel of shade onto the lid (light from the upper left); two iron straps with a
  lit top edge and rivets; a ring pull on a plate near the south edge; moss in the kerb's joints.
- open: the lid thrown back over its north hinge, lying on the turf upside down (its underside: the
  planks and two battens); in the opening the shaft's north wall in shade, then steps going down, each
  tread lit on its nosing and a tone darker the deeper it lies, the bottom in the dark with a faint
  cool draught dithered over it. No animation.

Both pictures share one canvas, so the scene places them with the same offset. The scene stands the
opening's south edge on the soft grid at (112, 344) world px (texels 336, 1032), and the door's
collision sits exactly over the opening (centre 336, 1020). Drawn at density 3 in
house palette codes (palette.py); the outline is the stone's own darkest tone; no lone texels inside
(village.tidy).
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np
from PIL import Image

from scripts.art.native.palette import C, to_rgba

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUT = os.path.join(ROOT, 'game', 'zones', 'woodland', 'art')
OW, OH = 30, 24                # the opening: the door's collision, texels
K = 4                          # kerb width
LID_H = 26                     # room above the kerb for the thrown-back lid
W = OW + 2 * K                 # 38
H = LID_H + OH + 2 * K + 2     # 60: lid room, kerb, opening, kerb, front
X0, Y0 = K, LID_H + K          # the opening's top-left in the canvas
FOOT = (X0 + OW // 2, Y0 + OH)  # the opening's south edge centre: the scene's anchor


def _tidy(a, keep=None):
    from scripts.art.native.village import tidy
    tidy(a, passes=2, keep=keep)


def _kerb(a, rng):
    """Dressed stones round the opening: blocks along each side, lit top-left, dark bottom-right,
    cool joints with moss in a few, the south course's front face, the outline in the stone's own
    darkest tone."""
    ring = np.zeros(a.shape, bool)
    ring[Y0 - K:Y0 + OH + K, X0 - K:X0 + OW + K] = True
    ring[Y0:Y0 + OH, X0:X0 + OW] = False
    fams = ('stone', 'stone_warm', 'stone_cool', 'stone')
    blocks = []
    # north and south courses run east-west, the west and east courses north-south (corner blocks
    # belong to the north and south courses)
    for (ya, yb) in ((Y0 - K, Y0), (Y0 + OH, Y0 + OH + K)):
        x = X0 - K
        while x < X0 + OW + K:
            L = int(rng.integers(6, 10))
            blocks.append((x, ya, min(x + L, X0 + OW + K), yb))
            x += L
    for (xa, xb) in ((X0 - K, X0), (X0 + OW, X0 + OW + K)):
        y = Y0
        while y < Y0 + OH:
            L = int(rng.integers(6, 9))
            blocks.append((xa, y, xb, min(y + L, Y0 + OH)))
            y += L
    for k, (xa, ya, xb, yb) in enumerate(blocks):
        f = fams[int(rng.integers(0, 4))]
        t = int(rng.choice([3, 3, 4]))
        a[ya:yb, xa:xb] = C(f, t)
        a[ya, xa:xb] = C(f, min(5, t + 1))                    # lit top edge
        a[ya:yb, xa] = C(f, min(5, t + 1))                    # lit west edge
        a[yb - 1, xa:xb] = C(f, t - 1)                        # its south arris in shade
        a[ya:yb, xb - 1] = C('stone_cool', 1)                 # the joint east of it
        a[yb - 1, xb - 1] = C('stone_cool', 1)
        if xb - xa >= 6 and yb - ya >= 3 and rng.random() < 0.5:   # a weathered pit, 2 x 1
            px, py = int(rng.integers(xa + 2, xb - 3)), int(rng.integers(ya + 1, yb - 1))
            a[py, px:px + 2] = C(f, t - 1)
    # moss in a few joints: a small cluster of two greens where a joint meets the turf
    for (xa, ya, xb, yb) in blocks[::3]:
        jx, jy = xb - 2, yb - 2
        if 0 <= jy and jy + 2 <= a.shape[0] and 0 <= jx and jx + 3 <= a.shape[1]:
            a[jy:jy + 2, jx:jx + 2] = C('leaf', 2)
            a[jy, jx] = C('leaf', 3)
            a[jy, jx + 1] = C('leaf', 3)
    # the kerb's front: the south course stands two texels proud of the turf
    a[Y0 + OH + K:Y0 + OH + K + 2, X0 - K:X0 + OW + K] = C('stone_cool', 2)
    a[Y0 + OH + K + 1, X0 - K:X0 + OW + K] = C('stone_cool', 1)
    for (xa, ya, xb, yb) in blocks:
        if yb == Y0 + OH + K:
            a[Y0 + OH + K:Y0 + OH + K + 2, xb - 1] = C('stone_cool', 0)
    return ring


def _planks(a, x0, y0, w, h, rng, underside=False):
    """Oak planks running north to south over the box, each its own tone, lit down its west edge and
    dark at its east joint, grain in dashes, a few weathered patches."""
    n = 5
    pw = w // n
    # (warm and lit in the west, cool to the east: the whole lid turns from the upper-left light)
    fams = ('timber_warm', 'timber_warm', 'timber', 'timber', 'timber_cool', 'timber_cool')
    for k in range(n):
        xa = x0 + k * pw
        xb = x0 + w if k == n - 1 else xa + pw
        f = fams[k + int(rng.integers(0, 2))]
        t = (3 if not underside else 2) - (1 if k == n - 1 else 0)
        a[y0:y0 + h, xa:xb] = C(f, t)
        a[y0:y0 + h, xa] = C(f, t + 1)                        # lit west edge
        a[y0:y0 + h, xb - 1] = C('timber_cool', 0 if underside else 1)    # the joint
        for _ in range(3):                                    # grain: vertical dashes, 3 to 6 long
            gx = int(rng.integers(xa + 1, xb - 1))
            gy = int(rng.integers(y0 + 1, y0 + h - 6))
            a[gy:gy + int(rng.integers(3, 7)), gx] = C(f, t - 1)
        if rng.random() < 0.6:                                # weathered: a silvered streak, 2 x 3
            gx = int(rng.integers(xa + 1, xb - 3))
            gy = int(rng.integers(y0 + 2, y0 + h - 4))
            a[gy:gy + 3, gx:gx + 2] = C('timber_cool', t + 1)
        a[y0 + h - 1, xa:xb - 1] = C(f, t - 1)                # the plank's end in shade


def _outline(a):
    """The silhouette's edge in each material's own darkest tone: a texel darker on the lower right,
    a tone lighter on the lit upper left (house rule 1, edges broken where the light hits)."""
    from scripts.art.native.palette import step
    inside = a >= 0
    P = np.pad(inside, 1)
    up, down, left, right = ~P[:-2, 1:-1], ~P[2:, 1:-1], ~P[1:-1, :-2], ~P[1:-1, 2:]
    edge = inside & (up | down | left | right)
    lit = edge & (up | left) & ~down & ~right
    a[edge & ~lit] = step(a[edge & ~lit], -3)
    a[lit] = step(a[lit], -1)


def closed(seed=7):
    rng = np.random.default_rng(seed)
    a = np.full((H, W), -1, np.int64)
    _kerb(a, rng)
    _planks(a, X0, Y0, OW, OH, rng)
    # the kerb's shade on the lid: a texel along its north and west inner edges
    a[Y0, X0:X0 + OW] = C('timber_cool', 1)
    a[Y0:Y0 + OH, X0] = C('timber_cool', 1)
    # two iron straps: a lit top edge, a dark lower edge, rivets on the lit edge
    for sy in (Y0 + 5, Y0 + OH - 8):
        a[sy, X0 + 1:X0 + OW - 1] = C('iron', 4)
        a[sy + 1, X0 + 1:X0 + OW - 1] = C('iron', 2)
        a[sy + 2, X0 + 1:X0 + OW - 1] = C('iron', 1)
        for rx in range(X0 + 3, X0 + OW - 2, 6):
            a[sy:sy + 2, rx] = C('iron', 5)
    # the ring pull on its plate near the south edge: an iron ring, lit on its upper left
    cx, cy = X0 + OW // 2, Y0 + OH - 5
    a[cy - 2:cy, cx - 2:cx + 2] = C('iron', 2)                # the plate the ring hangs from
    a[cy - 2, cx - 2:cx + 2] = C('iron', 3)
    yy, xx = np.mgrid[0:H, 0:W]
    e = ((xx - cx + 0.5) / 4.0) ** 2 + ((yy - cy - 1.0) / 2.8) ** 2
    ring = (e <= 1.0) & (e >= 0.4)
    a[ring] = C('iron', 1)
    a[ring & ((xx < cx) & (yy <= cy))] = C('iron', 4)
    a[ring & ((xx >= cx) & (yy > cy))] = C('iron', 0)
    _tidy(a)
    _outline(a)
    return a


def opened(seed=7):
    rng = np.random.default_rng(seed)
    a = np.full((H, W), -1, np.int64)
    _kerb(a, rng)
    # the shaft: its north wall's face in shade (courses), then the steps going down to the dark
    a[Y0:Y0 + OH, X0:X0 + OW] = C('void', 0)
    face = 5
    a[Y0:Y0 + face, X0:X0 + OW] = C('stone_cool', 1)
    a[Y0 + 2, X0:X0 + OW] = C('stone_cool', 0)
    for jx in range(X0 + 3, X0 + OW, 7):
        a[Y0:Y0 + 2, jx] = C('stone_cool', 0)
    for jx in range(X0 + 6, X0 + OW, 7):
        a[Y0 + 3:Y0 + face, jx] = C('stone_cool', 0)
    # steps: the nearest (south) lit, each deeper one a tone down, nosing lit, riser dark
    treads = [(Y0 + OH - 5, 5, ('stone', 3)), (Y0 + OH - 9, 4, ('stone', 2)),
              (Y0 + OH - 12, 3, ('stone_cool', 2)), (Y0 + OH - 14, 2, ('stone_cool', 1))]
    for (ty, th, (f, t)) in treads:
        a[ty:ty + th, X0 + 2:X0 + OW - 2] = C(f, t)
        a[ty, X0 + 2:X0 + OW - 2] = C(f, min(5, t + 1))      # the nosing catches the light
        a[ty + th - 1, X0 + 2:X0 + OW - 2] = C(f, max(0, t - 1))   # the riser below it
        a[ty:ty + th, X0 + OW - 3] = C(f, max(0, t - 1))      # the east end in shade
    # the side walls of the shaft, shaded (west a little lighter than east)
    a[Y0 + face:Y0 + OH, X0:X0 + 2] = C('stone_cool', 1)
    a[Y0 + face:Y0 + OH, X0 + OW - 2:X0 + OW] = C('stone_cool', 0)
    # a faint cool draught over the dark bottom: a 2 x 2 checker of the cool sky's darkest tone
    yy, xx = np.mgrid[0:H, 0:W]
    chk = ((xx // 2 + yy // 2) % 2) == 0
    dark = (a == C('void', 0)) & (yy >= Y0 + face) & (yy < Y0 + OH - 14) & (xx >= X0 + 2) & (xx < X0 + OW - 2)
    sparse = chk & (((yy // 2) % 2) == 0)                     # one 2 x 2 cell in four
    a[dark & sparse] = C('void', 1)
    a[dark & sparse & (((xx // 4 + yy // 4) % 2) == 0)] = C('sky_cool', 0)
    # the lid thrown back over its north hinge, upside down on the turf: planks and two battens,
    # its south edge (the hinge side) showing the board's thickness
    ly = Y0 - K - 2 - OH
    _planks(a, X0, ly, OW, OH, rng, underside=True)
    for by in (ly + 4, ly + OH - 7):
        a[by:by + 3, X0 + 1:X0 + OW - 1] = C('timber_warm', 3)
        a[by, X0 + 1:X0 + OW - 1] = C('timber_warm', 4)
        a[by + 2, X0 + 1:X0 + OW - 1] = C('timber_warm', 2)
    a[ly + OH:ly + OH + 2, X0:X0 + OW] = C('timber_cool', 1)  # the board's thickness, in shade
    a[ly + OH + 1, X0:X0 + OW] = C('timber_cool', 0)
    for hx in (X0 + 5, X0 + OW - 7):                          # the hinge straps over the kerb
        a[ly + OH:Y0 - K + 2, hx:hx + 2] = C('iron', 2)
        a[ly + OH:Y0 - K + 2, hx] = C('iron', 4)
    _tidy(a)
    _outline(a)
    return a


def pictures() -> dict:
    return {'hatch_closed': closed(), 'hatch_open': opened()}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--out', default=OUT)
    a = ap.parse_args(argv)
    bad = []
    for name, codes in pictures().items():
        img = Image.fromarray(to_rgba(codes), 'RGBA')
        path = os.path.join(a.out, name + '.png')
        if a.check:
            if not os.path.exists(path) or not np.array_equal(np.asarray(Image.open(path).convert('RGBA')), np.asarray(img)):
                bad.append(name)
        else:
            img.save(path, optimize=True)
            print('wrote', os.path.relpath(path, ROOT), img.size)
    if bad:
        print('hatch: stale pictures: ' + ', '.join(bad) + ' (python3 -m scripts.art.native.hatch)', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
