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
M = 4                          # the worn earth ring round the kerb (even: the kerb and the opening sit on the 2 x 2 grid)
LID_H = 26                     # room above the kerb for the thrown-back lid
W = OW + 2 * K + 2 * M         # 46
H = LID_H + M + OH + 2 * K + 2 + M   # 68: lid room, ring, kerb, opening, kerb, front, ring
X0, Y0 = M + K, LID_H + M + K  # the opening's top-left in the canvas
FOOT = (X0 + OW // 2, Y0 + OH)  # the opening's south edge centre: the scene's anchor
STRAPS = (4, 8)                # the iron straps' rows: from the opening's head, and from its foot
STRAP_T = (4, 2)               # each strap: a lit top row, a dark bottom row
JOINT = ('timber_cool', 2)     # the joint between boards


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
        # (9 Nov audit, W-H1) the light from the upper left: the north and west copings a tone
        # lighter on top, the south and east copings a tone darker
        north_west = ya < Y0 or xb <= X0
        t = 4 if north_west else 2
        f = ('stone', 'stone_warm', 'stone_cool')[k % 3] if north_west else ('stone', 'stone_cool')[k % 2]
        a[ya:yb, xa:xb] = C(f, t)
        # the block's arrises as sibling swaps (warm on the lit top and west, cool on the south),
        # so the light reads by course and the blocks by their joints, not by ruled lines
        a[ya:yb, xb - 1] = C('stone_cool', max(0, t - 1))     # the joint east of it
        if xb - xa >= 6 and yb - ya >= 3 and rng.random() < 0.5:   # a weathered pit, 2 x 2, lit lip
            px, py = int(rng.integers(xa + 2, xb - 3)), int(rng.integers(ya + 1, yb - 2))
            a[py:py + 2, px:px + 2] = C(f, t - 1)
            a[py + 2, px:px + 2] = C(f, min(5, t + 1)) if py + 2 < yb - 1 else a[py + 2, px:px + 2]
    # moss in a few joints: a small cluster of two greens where a joint meets the turf
    for (xa, ya, xb, yb) in blocks[::5]:
        jx, jy = xb - 2, yb - 2
        if 0 <= jy and jy + 2 <= a.shape[0] and 0 <= jx and jx + 3 <= a.shape[1]:
            a[jy:jy + 2, jx:jx + 2] = C('leaf', 2)
            a[jy, jx] = C('leaf', 3)
            a[jy, jx + 1] = C('leaf', 3)
    # the opening's south lip, facing the light, is lit along its inner edge
    # (W3-H1) in runs of two or three tones, with a chip
    x = X0
    tones = (C('stone_warm', 5), C('stone', 4), C('stone_warm', 4))
    j = int(rng.integers(0, 3))
    while x < X0 + OW:
        n = int(rng.integers(4, 10))
        a[Y0 + OH, x:min(X0 + OW, x + n)] = tones[j % 3]
        j += 1 + int(rng.integers(0, 2))
        x += n
    cx_ = int(rng.integers(X0 + 6, X0 + OW - 8))
    a[Y0 + OH, cx_:cx_ + 2] = C('stone_cool', 2)
    a[Y0 + OH + 1, cx_] = C('stone_cool', 1)
    # the kerb's front: the south course stands two texels proud of the turf
    a[Y0 + OH + K:Y0 + OH + K + 2, X0 - K:X0 + OW + K] = C('stone_cool', 2)
    a[Y0 + OH + K + 1, X0 - K:X0 + OW + K] = C('stone_cool', 1)
    for (xa, ya, xb, yb) in blocks:
        if yb == Y0 + OH + K:
            a[Y0 + OH + K:Y0 + OH + K + 2, xb - 1] = C('stone_cool', 0)
    return ring


def _planks(a, x0, y0, w, h, rng, underside=False):
    """Three oak boards running north to south (the wood recipe, 9 Nov audit W-H1): each its own
    sibling (oak, warm, cool) and lit from the west (the western board a tone up), a dark joint line
    between boards, grain as streaks 2 to 4 texels long along each board drawn as sibling swaps at the
    same tone, and few one-tone steps (a knot or a worn end), never random value grain."""
    n = 3
    bounds = [x0, x0 + w // 3, x0 + 2 * w // 3 + (1 if w % 3 == 2 else 0), x0 + w]
    fams = ('timber_warm', 'timber', 'timber_cool')
    sib = {'timber_warm': 'timber', 'timber': 'timber_warm', 'timber_cool': 'timber'}
    for k in range(n):
        xa, xb = bounds[k], bounds[k + 1]
        f = fams[k]
        t = 3 - (1 if underside else 0)
        a[y0:y0 + h, xa:xb] = C(f, t)
        a[y0:y0 + h, xa] = C(sib[f], t)                       # the west arris, a sibling
        a[y0:y0 + h, xb - 1] = C(*JOINT)                      # the joint
        # grain: streaks along the board in the sibling at the same tone
        for _ in range(int(h * (xb - xa) / 9)):
            gx = int(rng.integers(xa + 1, xb - 1))
            gy = int(rng.integers(y0, y0 + h - 2))
            L = int(rng.integers(2, 5))
            a[gy:min(y0 + h - 1, gy + L), gx] = C(sib[f], t)
        # a knot: a dark texel ringed by the sibling grain
        kx, ky = int(rng.integers(xa + 2, xb - 3)), int(rng.integers(y0 + 3, y0 + h - 4))
        a[ky - 1:ky + 2, kx - 1:kx + 2] = C(sib[f], t)
        a[ky, kx] = C(f, t - 1)


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


def _ground(a, seed):
    """Where the kerb meets the turf (W2-H1; eastward-edges 5.1): worn earth 2 to 3 texels wide round
    the kerb whose outer edge is the turf's frayed edge, wandering in 1-texel steps, with a few bites
    of earth 3 to 5 texels deep into the turf; damper in the kerb's shade on the north and west; a
    contact shade one tone down along the south and east of the frame; 2 to 4 tufts of turf of
    different sizes over the earth and the kerb's foot (no ruled line, no even comb). Painted only
    outside what is drawn, so the kerb, the lid and the opening (the collision) stay put."""
    from scipy import ndimage as ndi
    from scripts.art.native.village import tidy
    rng = np.random.default_rng(seed + 101)
    drawn = a >= 0
    yy, xx = np.mgrid[0:H, 0:W]
    kx0, ky0, kx1, ky1 = X0 - K, Y0 - K, X0 + OW + K, Y0 + OH + K + 2      # the kerb with its front
    dx = np.maximum(np.maximum(kx0 - xx, xx - (kx1 - 1)), 0)
    dy = np.maximum(np.maximum(ky0 - yy, yy - (ky1 - 1)), 0)
    d = np.hypot(dx, dy)
    # the reach: 2 to 3 texels, wandering in 1-texel steps along the edge, and 3 bites 3 to 5 deep
    ang = np.arctan2(yy - (ky0 + ky1) / 2.0, xx - (kx0 + kx1) / 2.0)
    wander = ndi.gaussian_filter1d(rng.random(720), 6, mode='wrap')
    wander = (wander - wander.min()) / max(1e-6, wander.max() - wander.min())
    idx = ((ang + np.pi) / (2 * np.pi) * 719).astype(int)
    reach = np.round(1.6 + 1.6 * wander[idx])
    for _ in range(3):
        c = rng.uniform(-np.pi, np.pi)
        wdt = rng.uniform(0.12, 0.22)
        dang = np.abs((ang - c + np.pi) % (2 * np.pi) - np.pi)
        reach = np.maximum(reach, np.round(rng.uniform(3, 5) * np.clip(1 - dang / wdt, 0, 1)))
    ring = (d > 0) & (d <= reach) & ~drawn
    ring &= ~((yy < ky0) & (xx > X0) & (xx < X0 + OW) & (yy < Y0 - K - 3))   # not under the open lid
    shade = (yy < ky0 + 2) | (xx < kx0 + 2)
    f = ndi.zoom(rng.random((H // 2 + 2, W // 3 + 2)), (2, 3), order=0)[:H, :W]
    a[ring] = np.where(f[ring] > 0.45, C('path', 3), C('path_warm', 3))
    a[ring & shade] = np.where(f[ring & shade] > 0.5, C('earth', 3), C('earth_warm', 3))
    # crumbs of the earth's darkest tone along the outer edge (1 to 2 texels)
    outer = ring & (d > reach - 1.0)
    ys, xs = np.nonzero(outer)
    for k in rng.permutation(len(ys))[: max(4, len(ys) // 9)]:
        a[ys[k], xs[k]] = C('earth', 2)
        if xs[k] + 1 < W and outer[ys[k], xs[k] + 1]:
            a[ys[k], xs[k] + 1] = C('earth', 2)
    # the contact shade: one tone down along the south and the east of the frame
    se = ring & (d <= 1.5) & ((yy >= ky1) | (xx >= kx1))
    a[se] = C('earth', 2)
    a[ring & (d <= 1.0) & ~se & ~shade] = C('path', 2)
    # two loose stones, lit on the upper left
    for (sy, sx) in ((ky1 + 1, kx1 - 11), (ky0 + 11, kx1 + 1)):
        if sy + 2 <= H and sx + 3 <= W:
            a[sy:sy + 2, sx:sx + 3] = C('stone', 3)
            a[sy, sx:sx + 2] = C('stone', 4)
            a[sy + 1, sx + 2] = C('stone', 2)
    # tufts: 2 to 4, each its own size (2 to 5 blades), over the earth and the kerb's foot
    spots = [(ky1 - 1, int(rng.integers(kx0 + 3, kx0 + 12))), (ky1, int(rng.integers(kx1 - 14, kx1 - 4))),
             (int(rng.integers(ky0 + 6, ky1 - 6)), kx1), (int(rng.integers(ky0 + 4, ky1 - 8)), kx0 - 1)]
    for (ty, tx) in [spots[i] for i in sorted(rng.choice(4, size=int(rng.integers(2, 5)), replace=False))]:
        nbl = int(rng.integers(2, 6))
        for j in range(nbl):
            bx = tx + j - nbl // 2
            h = int(rng.integers(2, 5)) - (1 if j in (0, nbl - 1) else 0)
            for q in range(max(1, h)):
                Y = ty - q
                if 0 <= Y < H and 0 <= bx < W:
                    a[Y, bx] = C('grass', 4) if q == max(1, h) - 1 else (C('grass', 3) if j % 2 else C('grass_cool', 3))
            if 0 <= ty + 1 < H and 0 <= bx < W and a[ty + 1, bx] >= 0 and not drawn[ty + 1, bx]:
                a[ty + 1, bx] = C('grass_cool', 2)                     # its root in shade
    tidy(a, passes=1, keep=drawn & ~ring)


def closed(seed=7):
    rng = np.random.default_rng(seed)
    a = np.full((H, W), -1, np.int64)
    _kerb(a, rng)
    _planks(a, X0, Y0, OW, OH, rng)
    # the kerb's shade on the lid: two rows under the north reveal (the opening's head), one texel
    # down the west inner edge
    from scripts.art.native.palette import step
    a[Y0:Y0 + 4, X0:X0 + OW] = step(a[Y0:Y0 + 4, X0:X0 + OW], -1)
    a[Y0:Y0 + 2, X0:X0 + OW] = step(a[Y0:Y0 + 2, X0:X0 + OW], -1)
    a[Y0, X0:X0 + OW] = C('timber_cool', 1)
    a[Y0:Y0 + OH, X0] = C('timber_cool', 1)
    # two iron straps (W2-H1): a lit top row, a body, a dark bottom row, ends rounded; a nail head on
    # each board (a dark texel with a lit texel above it); a little rust where the strap meets a joint
    bnds = [X0, X0 + OW // 3, X0 + 2 * OW // 3 + (1 if OW % 3 == 2 else 0), X0 + OW]
    nails = []
    for sy in (Y0 + STRAPS[0], Y0 + OH - STRAPS[1]):
        a[sy, X0 + 2:X0 + OW - 2] = C('iron', 4)
        a[sy + 1, X0 + 1:X0 + OW - 1] = C('iron', 2)
        a[sy, X0 + 1] = C('iron', 3)                                  # the strap's rounded end
        for k in range(3):
            # a nail head on each board (W3-H1): a dark texel with a lit texel above it, kept by tidy
            nx = (bnds[k] + bnds[k + 1]) // 2 + int(rng.integers(-1, 2))
            a[sy + 1, nx] = C('iron', 0)
            a[sy, nx] = C('iron', 5)
            nails.append((sy, nx))
            nails.append((sy + 1, nx))
    # the ring pull: a plate, a ring 6 x 5 lit on its upper-left arc and dark on its lower right, the
    # boards showing through it, its shade on the boards under it
    cx, cy = X0 + OW // 2 - 3, Y0 + OH - STRAPS[1] + 2
    RING = ["..LL..",
            ".L..M.",
            "L....D",
            ".M..D.",
            "..DD.."]
    for j, row in enumerate(RING):
        for i, ch in enumerate(row):
            if ch != '.':
                y_, x_ = cy + j + 1, cx + i + 1
                a[y_, x_] = step(np.array([a[y_, x_]]), -2)[0]        # the shade, a texel down-right
    keep = np.zeros(a.shape, bool)
    for j, row in enumerate(RING):
        for i, ch in enumerate(row):
            if ch != '.':
                a[cy + j, cx + i] = {'L': C('iron', 5), 'M': C('iron', 3), 'D': C('iron', 1)}[ch]
                keep[cy + j, cx + i] = True                           # a ring is a thin line: tidy leaves it
    a[cy - 2:cy, cx + 2:cx + 4] = C('iron', 2)                         # the plate it hangs from
    a[cy - 2, cx + 2] = C('iron', 4)
    for (ny, nx) in nails:
        keep[ny, nx] = True
    _tidy(a, keep=keep)
    _outline(a)
    _ground(a, seed)
    return a


def opened(seed=7):
    """The open hatch (9 Nov audit, W-H2): the lid hinged on the north coping on two iron hinge
    leaves, thrown back to lie upside down on the turf, its edge showing as end grain lit on top and
    its shadow thrown north-east two tones down onto the coping and the turf; in the opening four stone
    steps going down, each a texel narrower, a lit tread nosing over a dark riser, the light falling
    off to near-black at the bottom (the Undercroft's falloff)."""
    from scripts.art.native.palette import step
    rng = np.random.default_rng(seed)
    a = np.full((H, W), -1, np.int64)
    _kerb(a, rng)
    # the shaft: the north wall's face in shade, then the steps from the near (south) one down
    a[Y0:Y0 + OH, X0:X0 + OW] = C('void', 0)
    face = 4
    a[Y0:Y0 + face, X0:X0 + OW] = C('stone_cool', 0)
    a[Y0 + face - 1, X0 + 1:X0 + OW - 1] = C('void', 0)
    # the side walls: the west wall faces the light a little, the east wall in shade
    a[Y0 + face:Y0 + OH, X0:X0 + 2] = C('stone_cool', 1)
    a[Y0 + face:Y0 + OH, X0 + OW - 2:X0 + OW] = C('stone_cool', 0)
    steps = [((5, 'stone', 3), 0), ((5, 'stone_cool', 2), 1), ((4, 'stone_cool', 1), 2), ((3, 'stone_cool', 0), 3)]
    y = Y0 + OH
    for ((th, f, t), k) in steps:
        y -= th
        xa, xb = X0 + 2 + k, X0 + OW - 2 - k
        a[y:y + th, xa:xb] = C(f, t)                                 # the tread
        a[y, xa:xb] = C(f, min(5, t + 1)) if k < 3 else C(f, t)      # the lit nosing
        if k == 0:
            a[y, xa:xb] = C('stone', 4)
        # W2-H2: the nosing worn, with 1 or 2 chips (a notch a tone down, a shade texel under it)
        for _ in range(int(rng.integers(1, 3))):
            cx_ = int(rng.integers(xa + 2, xb - 4))
            cw = int(rng.integers(2, 4))
            a[y, cx_:cx_ + cw] = C(f, t)
            a[y + 1, cx_:cx_ + cw] = C('stone_cool', max(0, t - 1))
        # grit at the back of the tread (its darker rear rows), in clusters
        # grit at the back of the tread (W3-H2): 2 to 4 marks at random places, in two sizes
        if th >= 4 and k < 3:
            gy = y + th - 3
            for gx in sorted(rng.choice(np.arange(xa + 1, xb - 3), size=int(rng.integers(2, 5)), replace=False)):
                if rng.random() < 0.5:
                    a[gy, gx] = C('earth', max(1, 3 - k))
                    a[gy - 1 if rng.random() < 0.5 else gy, gx + 1] = C('earth', max(1, 3 - k))
                else:
                    a[gy, gx:gx + 3] = C('earth', max(1, 3 - k))
                    a[gy - 1, gx + 1] = C('earth_warm', max(1, 4 - k))
        a[y + th - 2:y + th, xa:xb] = C('stone_cool', max(0, 1 - k // 2))   # the riser below it, dark
        a[y + th - 1, xa:xb] = C('stone_cool', 0)
        # riser joints, every 5 to 8 texels
        jx = xa + int(rng.integers(4, 8))
        while jx < xb - 3:
            a[y + th - 2, jx] = C('stone_cool', 0)
            jx += int(rng.integers(5, 9))
        a[y:y + th, xb - 1] = C('stone_cool', 0)                     # the east end in shade
        a[y + 1:y + th - 2, xa] = C(f, min(5, t + 1)) if k < 2 else a[y + 1:y + th - 2, xa]
        # the ends meet the shaft wall with a shade texel
        a[y + 1:y + th - 1, xa - 1] = C('stone_cool', 0) if xa - 1 >= X0 + 2 else a[y + 1:y + th - 1, xa - 1]
        a[y, xb] = C('stone_cool', 0)
    # the bottom beyond the last step: near-black
    a[Y0 + face:y, X0 + 2:X0 + OW - 2] = C('void', 0)
    # the lid: thrown back over the north hinge, lying upside down on the turf, its south edge
    # (the hinge side) showing three rows of end grain, lit on top, right on the coping
    ly = Y0 - K - 3 - OH
    _planks(a, X0, ly, OW, OH, rng, underside=True)
    for by in (ly + 4, ly + OH - 7):                                # the battens on its underside
        a[by:by + 3, X0 + 1:X0 + OW - 1] = C('timber_warm', 3)
        a[by, X0 + 1:X0 + OW - 1] = C('timber_warm', 4)
        a[by + 2, X0 + 1:X0 + OW - 1] = C('timber_cool', 2)
    eg = Y0 - K - 3
    a[eg, X0:X0 + OW] = C('timber_warm', 4)                         # the end grain's lit top
    a[eg + 1:eg + 3, X0:X0 + OW] = C('timber', 2)
    for gx in range(X0 + 1, X0 + OW - 1, 4):
        a[eg + 1, gx:gx + 2] = C('timber_warm', 2)                  # the ring ends in the grain, a sibling
    a[eg + 2, X0:X0 + OW] = C('timber_cool', 1)
    # the hinge leaves: iron 3 x 4, lit on top, over the end grain and onto the coping
    for hx in (X0 + 5, X0 + OW - 8):
        a[eg:eg + 4, hx:hx + 3] = C('iron', 2)
        a[eg, hx:hx + 3] = C('iron', 4)
        a[eg + 3, hx:hx + 3] = C('iron', 1)
        a[eg + 1, hx + 1] = C('iron', 5)                            # the pin
    # the lid's shadow, thrown north-east: two tones down on the coping east of the lid's foot
    # and a band of shade on the turf along its east side
    cop = (slice(Y0 - K, Y0 - K + 2), slice(X0 + OW - 4, X0 + OW + K))
    a[cop] = step(a[cop], -2)
    # W2-H2: the lid's far (top) edge as two rows of end grain, lit on top; its east side a texel of
    # thickness in shade (no strip of turf drawn beside it)
    a[ly, X0:X0 + OW] = C('timber_warm', 4)
    a[ly + 1, X0:X0 + OW] = C('timber', 2)
    for gx in range(X0 + 2, X0 + OW - 1, 5):
        a[ly + 1, gx:gx + 2] = C('timber_warm', 2)
    a[ly + 2:eg, X0 + OW - 1] = C('timber_cool', 1)
    _tidy(a)
    _outline(a)
    _ground(a, seed)
    # the lid's shadow (W3-H2): its footprint thrown a few texels south-east by the light from the
    # upper left, two tones down on the coping and the worn earth beside it (not on the lid, nor in
    # the shaft)
    lid = np.zeros(a.shape, bool)
    lid[ly:eg + 3, X0:X0 + OW] = True
    thrown = np.zeros(a.shape, bool)
    thrown[ly + 2:eg + 5, X0 + 3:X0 + OW + 3] = True
    tgt = thrown & ~lid & (a >= 0)
    tgt[Y0:Y0 + OH, X0:X0 + OW] = False
    a[tgt] = step(a[tgt], -2)
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
