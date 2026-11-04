"""Village commons for the kit: the things a village keeps in common and the yards behind its
houses (round 3, 3 Nov; docs/vision/placement-logic.md).

    python3 -m scripts.art.kit.commons            # pictures and pieces (pieces kept unless --force)
    python3 -m scripts.art.kit.commons --check    # exit 1 if a committed picture is not what this draws

Each piece says where it belongs in data the placement audit checks (placement_audit.check_plan):

- a washing line `needs` a home within 4 cells, on its yard side (behind the house, not in front);
- a chopping block and a woodpile `need` a hearth near (a house or the smithy);
- a bench `faces` something worth facing (a feature, a view, water or the land falling away);
- a fingerpost's arms `point` along the routes that leave the junction it stands at (one piece per
  set of arms: three ways or four);
- the pump and the wayside shrine `provide` a feature to face; the notice board, the pump, the
  stalls and the washing line `avoid` wild woods.

Sizes in art px at density 3 (A, the hero, 74): the fingerpost 0.95 A to its finial, the pump 0.85 A,
a market stall 0.9 A to its awning, the shrine 0.9 A, the bench seat at 0.25 A.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

from scripts.art.kit import build as _B  # noqa: F401  (configures the density)
from scripts.art.kit import farm as FM
from scripts.art.kit.farm import C, METAL, WOOD, canvas, grid, noise, rpaint, sphere_light
from scripts.art.kit.schema import PIECES, ROOT
from scripts.art.native import village as V
from scripts.art.native.palette import FI, to_rgba

ART = os.path.join(ROOT, 'game', 'kit', 'props', 'art', 'commons')
RES = 'res://kit/props/art/commons/'

LINEN = [('stone_cool', 'plaster_warm', 'plaster'), ('sand_cool', 'plaster_warm', 'snow_warm'), ('stone_warm', 'sand', 'plaster')]
PAINT = [('stone_cool', 'plaster_warm', 'plaster'), ('slate_cool', 'stone_warm', 'plaster'), ('stone_warm', 'sand', 'plaster_warm')]
STONE = [('stone_cool', 'stone', 'stone_warm'), ('slate_cool', 'stone', 'ashlar_warm'), ('crag_cool', 'stone_warm', 'ashlar')]
IRON = [('soot', 'slate_cool', 'slate'), ('soot', 'dusk_cool', 'slate_warm')]


def _cloth(a, m, sets, x0, x1, rng, folds=3.0, base=3.0):
    """Hung cloth: lit on its upper left, folds running down it, the hem a step darker."""
    Y, X = grid(a)
    ys = np.nonzero(m.any(axis=1))[0]
    if not len(ys):
        return
    top, bot = ys.min(), ys.max()
    f = np.sin((X - x0) / max(1, x1 - x0) * math.pi * folds + 0.4)
    t = base + 0.9 * f - 0.9 * ((Y - top) / max(1, bot - top)) + 0.6 * (X < x0 + 2) - 0.8 * (X > x1 - 2) - 0.8 * (Y >= bot - 1)
    rpaint(a, m, sets, t, noise(a.shape, rng, 1.2))


def washing_line(seed=0):
    """A washing line in a back yard (100 x 76): two T posts, a line sagging between them on a
    forked prop, a sheet with a blue stripe, a shirt, a pair of socks and an apron pegged out, each
    lit on its upper left and hanging in folds."""
    rng = np.random.default_rng(seed)
    p = canvas(124, 80, 62, 76)
    a = p.a
    Y, X = grid(a)
    for px in (8, 116):
        V.prism(a, px - 2, 10, px + 2, 76, 1, 'timber', 3, side=1)
        V.bar(a, px - 6, 11, px + 6, 11, 1.2, 'timber_warm', 3)
    sag = lambda x: 13 + 8 * np.sin(np.clip((x - 8) / 108, 0, 1) * math.pi)
    for x in range(8, 117):
        a[int(round(sag(x))), x] = C('stone_warm', 4)
    V.bar(a, 62, 22, 59, 76, 0.9, 'timber', 2)                       # the prop, forked at the line
    a[20:22, 60:65:4] = C('timber_warm', 3)
    items = ((14, 34, 'sheet'), (38, 48, 'shirt'), (52, 58, 'socks'), (66, 84, 'apron'), (88, 98, 'towel'), (101, 111, 'shirt'))
    for x0, x1, kind in items:
        top = sag(np.arange(x0, x1 + 1))
        tm = int(round(top.min())) + 1
        if kind == 'sheet':                                              # a patchwork quilt airing
            m = (X >= x0) & (X <= x1) & (Y >= sag(X) + 1) & (Y < tm + 30 + np.sin(X * 0.7) * 1.5)
            patches = [LINEN, [('berry_cool', 'clay', 'sand_warm')], [('dusk_cool', 'sky_cool', 'sky')], [('leaf_cool', 'grass_warm', 'brass')],
                       [('earth_cool', 'brass', 'sand_warm')], [('crag_cool', 'fox', 'brass_warm')]]
            f = np.sin((X - x0) / max(1, x1 - x0) * math.pi * 3 + 0.4)
            for j in range(12):
                cx_, cy_ = j % 3, j // 3
                pm = m & ((X - x0) // 7 == cx_) & ((Y - tm) // 7 == cy_)
                rpaint(a, pm, patches[(j * 5 + 1) % len(patches)], 3.2 + 0.9 * f - 0.15 * (Y - tm) / 2 - 0.8 * (X > x1 - 2), 0)
            seamq = m & ((np.mod(X - x0, 7) == 6) | (np.mod(Y - tm, 7) == 6))
            a[seamq] = np.maximum(a[seamq] - 1, (a[seamq] // 8) * 8)
        elif kind == 'shirt':
            body = (X >= x0 + 2) & (X <= x1 - 2) & (Y >= sag(X) + 1) & (Y < tm + 17)
            sleeves = (Y >= sag(X) + 1) & (Y < tm + 9) & (X >= x0 - 2) & (X <= x1 + 2) & (np.abs(X - (x0 + x1) / 2) > 3)
            m = body | sleeves
            _cloth(a, m, [('crag_cool', 'clay', 'fox'), ('berry_cool', 'clay', 'crag_warm')], x0, x1, rng, 2.0, 3.0)
            a[m & (np.abs(X - (x0 + x1) / 2) < 0.6) & (np.mod(Y, 4) == 0) & (Y > tm + 2)] = C('plaster', 5)
        elif kind == 'socks':
            for sx in (x0, x0 + 4):
                m = (X >= sx) & (X <= sx + 2) & (Y >= sag(X) + 1) & (Y < tm + 10)
                m |= (X >= sx) & (X <= sx + 4) & (Y >= tm + 8) & (Y < tm + 11)
                _cloth(a, m, [('earth_cool', 'stone_warm', 'sand'), ('slate_cool', 'stone', 'plaster_warm')], sx, sx + 4, rng, 1.0, 3.0)
        elif kind == 'apron':
            m = (X >= x0) & (X <= x1) & (Y >= sag(X) + 1) & (Y < tm + 20 - 0.15 * np.abs(X - (x0 + x1) / 2))
            _cloth(a, m, [('dusk_cool', 'sky_cool', 'sky'), ('slate_cool', 'sky_cool', 'sky')], x0, x1, rng, 2.5, 3.0)
            a[m & (np.abs(Y - (tm + 4)) < 0.6)] = C('plaster_warm', 4)
        else:
            m = (X >= x0) & (X <= x1) & (Y >= sag(X) + 1) & (Y < tm + 14)
            _cloth(a, m, [('leaf_cool', 'grass_warm', 'brass'), ('grass_cool', 'leaf_warm', 'brass')], x0, x1, rng, 1.5, 3.0)
            a[m & (np.mod(X - x0, 4) == 1) & (Y > tm + 10)] = C('plaster', 4)
        for k in range(2 if kind != 'socks' else 1):                    # the pegs
            px = x0 + 1 + k * (x1 - x0 - 2)
            py = int(round(sag(px)))
            a[py - 1:py + 2, px] = C('timber_warm', 4)
            a[py + 1, px] = C('timber', 2)
    for gx in range(6, 120, 9):                                          # grass at the posts' feet
        if abs(gx - 8) < 6 or abs(gx - 116) < 6:
            a[V.seg_mask(a.shape, gx, 76, gx + rng.uniform(-1.5, 1.5), 71, 0.45)] = C('grass', 3)
    V.finish(p)
    return p


ARM_Y = {'e': 16, 'w': 22, 'n': 30, 's': 37}
OAK = [('timber_cool', 'timber', 'timber_warm'), ('slate_cool', 'timber_cool', 'stone_warm'), ('earth_cool', 'earth', 'sand_warm')]


def fingerpost(points, seed=0):
    """A fingerpost (round 4): a square oak post weathered grey-brown, lit on its west face and its
    grain running up it, a lead-capped top; its arms at different heights, oak with carved letters
    (dark grooves lit on their lower lip) and the pointing ends painted white; east and west side
    on, north behind the post, south before it; a stone and a tuft at the foot."""
    rng = np.random.default_rng(seed)
    p = canvas(76, 98, 38, 94)
    a = p.a
    Y, X = grid(a)
    cx = 38
    nz = noise(a.shape, rng, 1.0)
    sm = noise(a.shape, rng, 2.0)

    def arm(m, t0, d):
        ys, xs = np.nonzero(m)
        y0, y1 = ys.min(), ys.max()
        rpaint(a, m, OAK, t0 + 1.1 * (Y == y0) - 1.2 * (Y == y1) - 0.6 * (Y == y1 - 1) + 0.7 * (nz - 0.5)
               - 0.7 * (np.mod(X + 2 * Y, 7) == 0), sm)
        tip = m & ((X - cx) * d > (xs.max() - cx if d > 0 else cx - xs.min()) - 5) if d else m & False
        rpaint(a, tip, [('stone_cool', 'plaster_warm', 'plaster')], 3.6 + 1.0 * (Y == y0) - 1.2 * (Y == y1), 0)
        mid = (y0 + y1) // 2
        lo, hi = xs.min() + 3, xs.max() - (7 if d else 3)
        for lx in range(lo, hi, 3):                                  # carved letters
            if rng.random() < 0.8:
                hgt = 2 if rng.random() < 0.7 else 3
                g = m[mid - 1:mid - 1 + hgt, lx:lx + 2]
                a[mid - 1:mid - 1 + hgt, lx:lx + 2][g] = C('soot', 1)
                if m[mid - 1 + hgt, lx]:
                    a[mid - 1 + hgt, lx] = C('timber_warm', 4)            # the groove's lit lip
    if 'n' in points:
        m = (X >= cx - 2) & (X <= cx + 9) & (Y >= ARM_Y['n'] - 4) & (Y < ARM_Y['n'] + 1) & (Y - ARM_Y['n'] > -(X - cx) * 0.3 - 4)
        arm(m, 2.4, 0)
    post = (X >= cx - 3) & (X <= cx + 3) & (Y >= 9) & (Y < 94)
    rpaint(a, post, OAK, 3.0 + 1.3 * (X == cx - 3) + 0.4 * (X == cx - 2) - 1.4 * (X >= cx + 2) - 0.8 * (Y > 86) + 0.7 * (nz - 0.5)
           - 0.8 * (np.mod(Y * 3 + X * 5, 13) == 0), sm)
    a[post & (X == cx) & (Y > 44) & (Y < 60)] = C('soot', 1)            # a shake down the post
    a[post & (Y > 82) & (rng.random(a.shape) < 0.25)] = C('leaf_cool', 2)
    cap = (Y >= 4) & (Y < 9) & (np.abs(X - cx) <= 4 - (9 - Y) * 0.6)
    rpaint(a, cap, [('slate_cool', 'slate', 'stone')], 3.4 - 1.2 * (X > cx) + 0.8 * (X < cx - 1), 0)
    a[3, cx - 1:cx + 1] = C('stone', 4)
    for s_ in ('e', 'w'):
        if s_ in points:
            y0 = ARM_Y[s_]
            d = 1 if s_ == 'e' else -1
            L = 26
            xs_ = (X - cx) * d
            m = (xs_ >= 0) & (xs_ <= L) & (Y >= y0 - 3) & (Y <= y0 + 3) & (np.abs(Y - y0) <= 3 - np.clip(xs_ - (L - 4), 0, 4) * 0.8)
            arm(m, 3.0, d)
    if 's' in points:
        m = (X >= cx - 8) & (X <= cx + 2) & (Y >= ARM_Y['s'] - 3) & (Y < ARM_Y['s'] + 4) & (Y - ARM_Y['s'] < (cx - X) * 0.35 + 2)
        arm(m, 3.2, 0)
    V.stone_chunk(a, cx - 10, 88, 9, 6, 'stone', 3, rng)              # a stone at its foot
    for gx in (cx - 5, cx - 2, cx + 4, cx + 6, cx + 8):
        a[V.seg_mask(a.shape, gx, 94, gx + rng.uniform(-2, 2), 88, 0.45)] = C('grass' if gx < cx else 'grass_cool', 3)
    V.finish(p)
    return p


def chopping_block(seed=0):
    """A chopping block (44 x 36): a beech round, its top showing the rings and the axe's cuts,
    bark down its sides, an axe bitten into it, chips and a split log about its foot."""
    rng = np.random.default_rng(seed)
    p = canvas(52, 44, 26, 40)
    a = p.a
    Y, X = grid(a)
    cx, top, bot, r = 24, 16, 38, 11.0
    side = (np.abs(X - cx) <= r) & (Y >= top) & (Y < bot)
    u = (X - cx) / r
    rpaint(a, side, [('earth_cool', 'timber', 'timber_warm'), ('timber_cool', 'earth', 'earth_warm')],
           2.6 + 1.4 * np.exp(-((u + 0.45) / 0.35) ** 2) - 1.0 * (u > 0.4) - 0.8 * (np.mod(X * 3 + Y, 5) == 0), noise(a.shape, rng, 1.0))
    topm = ((X - cx) / r) ** 2 + ((Y - top) / 4.2) ** 2 <= 1
    d = np.hypot((X - cx) / r, (Y - top) / 4.2)
    rpaint(a, topm, [('sand_cool', 'sand', 'sand_warm'), ('earth_warm', 'sand', 'plaster_warm')],
           4.0 - 0.9 * (np.mod(d * 6, 1) < 0.25) - 0.8 * (X > cx + 5) + 0.4 * (X < cx - 4), d)
    for k in range(4):                                                   # the axe's cuts
        x0 = cx - 6 + 3 * k
        a[V.seg_mask(a.shape, x0, top - 1, x0 + 4, top + 2, 0.45) & topm] = C('earth_cool', 2)
    V.bar(a, cx + 2, top - 1, cx + 14, top - 15, 1.0, 'timber_warm', 3)        # the axe's helve
    head = (X >= cx - 2) & (X <= cx + 4) & (Y >= top - 3) & (Y <= top + 1)
    rpaint(a, head, [('soot', 'iron', 'stone')], 2.6 + 1.6 * (Y == top - 3), 0)
    a[top - 3, cx - 2:cx + 1] = C('snow_cool', 4)
    for _ in range(16):
        x0, y0 = rng.uniform(4, 48), rng.uniform(36, 42)
        a[V.seg_mask(a.shape, x0, y0, x0 + rng.uniform(-2, 2), y0 + rng.uniform(-0.5, 0.5), 0.45)] = C('sand_warm' if rng.random() < 0.5 else 'sand', 4)
    V.prism(a, 36, 31, 50, 37, 2, 'timber', 3, side=2)                   # a split log waiting
    V.finish(p)
    return p


def woodpile(seed=0):
    """A woodpile under a lean-to (84 x 62, round 4): logs stacked with their cut ends to us, each
    end a pale round with its rings, a split and a dark bark rim, the halves and quarters of split
    logs among the rounds; above the face the top of the stack, the logs' lengths running back,
    barked and lit along their tops; a board roof on two posts; a few split logs at the foot."""
    rng = np.random.default_rng(seed)
    p = canvas(88, 66, 44, 62)
    a = p.a
    Y, X = grid(a)
    nz = noise(a.shape, rng, 1.0)
    for px in (6, 80):                                                   # the lean-to's posts
        V.prism(a, px, 10, px + 4, 62, 1, 'timber', 3, side=1)
    bark = [('timber_cool', 'timber', 'timber_warm'), ('earth_cool', 'earth', 'earth_warm'), ('slate_cool', 'timber_cool', 'stone_warm')]
    ends = [('earth_warm', 'sand', 'sand_warm'), ('earth_cool', 'sand_cool', 'plaster_warm'), ('timber_cool', 'earth_warm', 'sand'),
            ('clay_cool', 'sand_warm', 'plaster_warm')]
    x0, x1, top, depth = 10, 78, 26, 8
    # the top of the stack: the top course's lengths running back, rounded and lit on the left
    for k, lx in enumerate(range(x0, x1, 9)):
        m = (X >= lx) & (X < lx + 9) & (Y >= top - depth) & (Y < top)
        u = (X - lx) / 9.0
        rpaint(a, m, bark, 2.4 + 1.8 * np.exp(-((u - 0.3) / 0.25) ** 2) - 1.2 * (u > 0.8) + 0.6 * (nz - 0.5)
               - 0.8 * (np.mod(Y + k * 3, 5) == 0), np.mod(k * 0.37, 1))
        a[m & (Y == top - depth)] = C('sand', 4)                     # the far ends, cut and pale
    back = (X >= x0) & (X < x1) & (Y >= top) & (Y < 62)
    a[back] = C('earth_cool', 1)
    # the face: rounds, halves and quarters, packed course on course
    for r in range(5):
        yc = 57 - r * 7.4
        off = 0 if r % 2 == 0 else 4.5
        for k in range(8):
            xc = x0 + 4.5 + off + k * 9 + rng.uniform(-0.6, 0.6)
            if xc > x1 - 4:
                continue
            rr = rng.uniform(4.3, 4.9)
            dd = np.hypot(X - xc, Y - yc)
            m = (dd <= rr) & back
            if rng.random() < 0.35:                                  # a split log: its flat face catches the light
                ang = rng.choice([0.4, 2.0, 3.5, 5.0])
                m &= np.cos(np.arctan2(Y - yc, X - xc) - ang) > -0.3
            d = dd / rr
            lit = sphere_light(X, Y, xc, yc, rr, rr)
            rpaint(a, m, ends, 3.5 + 0.9 * lit - 0.9 * (np.mod(d * 3.2, 1) < 0.22) - 0.5 * (X > xc + 2), rng.random())
            ring = m & ~ndi.binary_erosion(m, iterations=1)
            rpaint(a, ring, bark, 1.6 + 1.2 * ((Y < yc) & (X < xc)), rng.random())
            a[m & (dd < 0.8)] = C('earth', 2)                           # the pith
            if rng.random() < 0.5:
                ca = rng.uniform(0, math.pi)
                a[m & (np.abs((X - xc) * math.sin(ca) - (Y - yc) * math.cos(ca)) < 0.5) & (dd > 1.5) & (dd < rr - 1)] = C('earth', 2)
    # the roof: boards falling to the front, their lit edges, the shade under the eave
    roof = (X >= 2) & (X < 86) & (Y >= 4 + (86 - X) * 0.03) & (Y < 14)
    rpaint(a, roof, [('timber_cool', 'timber', 'timber_warm'), ('slate_cool', 'timber_cool', 'timber')],
           3.6 - 0.25 * (Y - 4) - 1.3 * (np.mod(X, 7) == 6) - 0.8 * (X > 80) + 0.5 * (nz - 0.5), np.mod(X // 7 * 0.41, 1))
    a[roof & (Y == 13)] = C('soot', 1)
    a[(Y >= 14) & (Y < 16) & (X >= x0) & (X < x1)] = C('soot', 1)
    # split logs at the foot
    for k, (lx, ly) in enumerate(((16, 63), (30, 64), (60, 63))):
        m = V.seg_mask(a.shape, lx, ly, lx + 10, ly - 1 + k % 2, 1.6)
        rpaint(a, m, bark if k % 2 else ends, 2.8 + 1.2 * (Y < ly - 1), 0.4)
    V.finish(p)
    return p


def bench(seed=0):
    """A village bench facing south (72 x 40): three planks to sit on, lit along their tops, a
    back rail, two stone feet; a carved slat between them."""
    rng = np.random.default_rng(seed)
    p = canvas(96, 44, 48, 40)
    a = p.a
    Y, X = grid(a)
    nz = noise(a.shape, rng, 1.0)
    for lx in (12, 76):                                                  # stone feet
        V.prism(a, lx, 24, lx + 9, 40, 3, 'stone', 3, side=2)
    for bx in (14, 80):                                                  # the back's uprights
        V.prism(a, bx, 4, bx + 3, 22, 1, 'timber', 3, side=1)
    for k, y0 in enumerate((6, 12)):
        m = (X >= 10) & (X < 88) & (Y >= y0) & (Y < y0 + 4)
        rpaint(a, m, WOOD, 3.0 + 1.3 * (Y == y0) - 1.0 * (Y == y0 + 3) - 0.8 * (X > 80) + 0.6 * (nz - 0.5), np.mod(k * 0.4 + 0.1, 1))
    seat = (X >= 6) & (X < 90) & (Y >= 18) & (Y < 26)
    plank = (Y - 18) // 3
    rpaint(a, seat, WOOD, 3.8 - 0.6 * plank - 1.2 * (np.mod(Y - 18, 3) == 2) - 0.8 * (X > 84) + 0.6 * (nz - 0.5), np.mod(plank * 0.37, 1))
    a[seat & (Y == 18) & (X < 50)] = C('sand_warm', 5)
    front = (X >= 6) & (X < 90) & (Y >= 26) & (Y < 29)
    rpaint(a, front, WOOD, 2.0 - 0.6 * (X > 84), 0.2)
    a[seat & (np.mod(X, 17) == 3)] = C('iron', 3)                        # nail heads
    V.finish(p)
    return p


def notice_board(seed=0):
    """A notice board (60 x 76): a framed board on two posts under a little pent roof of boards,
    notices pinned to it (a bill, a lost cat, a list), one corner lifting."""
    rng = np.random.default_rng(seed)
    p = canvas(64, 92, 32, 88)
    a = p.a
    Y, X = grid(a)
    for px in (8, 52):
        V.prism(a, px, 14, px + 4, 88, 1, 'timber', 3, side=1)
    frame = (X >= 6) & (X < 58) & (Y >= 18) & (Y < 50)
    rpaint(a, frame, WOOD, 3.0 + 1.0 * (Y == 18) + 0.8 * (X == 6) - 1.2 * (X >= 56) - 1.0 * (Y >= 48), 0.3)
    board = (X >= 9) & (X < 55) & (Y >= 21) & (Y < 47)
    rpaint(a, board, [('earth_cool', 'clay_cool', 'clay'), ('timber_cool', 'earth', 'earth_warm')],
           2.2 + 0.6 * (np.mod(X, 7) == 0) - 0.6 * (Y > 43) + 0.5 * (noise(a.shape, rng, 1.0) - 0.5), 0.3)
    notes = ((11, 23, 14, 12, LINEN, 0), (27, 22, 12, 15, [('sand_cool', 'sand', 'plaster_warm')], 1),
             (41, 24, 11, 10, [('stone_cool', 'sky_cool', 'sky')], 2), (14, 36, 16, 9, [('crag_cool', 'clay', 'sand_warm')], 3),
             (33, 38, 15, 8, LINEN, 4))
    for x0, y0, w, h, sets, k in notes:
        m = (X >= x0) & (X < x0 + w) & (Y >= y0) & (Y < y0 + h)
        rpaint(a, m, sets, 3.8 + 0.8 * (X == x0) - 0.8 * (X == x0 + w - 1) - 0.8 * (Y == y0 + h - 1), 0.4)
        for ly in range(y0 + 3, y0 + h - 2, 2):
            for lx in range(x0 + 2, x0 + w - 2):
                if rng.random() < 0.6:
                    a[ly, lx] = C('soot', 2) if k != 1 else C('berry_cool', 2)
        a[y0, x0 + w // 2] = C('berry', 3)                              # the pin
        if k == 1:                                                       # the lost cat
            cat = ((X - (x0 + 6)) / 3.0) ** 2 + ((Y - (y0 + 6)) / 2.5) ** 2 <= 1
            a[cat] = C('soot', 1)
            a[y0 + 3, x0 + 4] = C('soot', 1)
            a[y0 + 3, x0 + 8] = C('soot', 1)
    a[47:49, 50:54] = C('plaster', 4)                                    # a corner lifting
    roof = (X >= 2) & (X < 62) & (Y >= 10) & (Y < 18)
    rpaint(a, roof, [('timber_cool', 'timber', 'timber_warm'), ('slate_cool', 'timber_cool', 'timber')],
           3.6 - 0.3 * (Y - 10) - 1.2 * (np.mod(X, 6) == 5) - 0.8 * (X > 56), np.mod(X // 6 * 0.37, 1))
    a[roof & (Y == 10)] = C('timber_warm', 5)
    a[(Y == 18) & (X >= 6) & (X < 58)] = C('soot', 1)
    V.finish(p)
    return p


def pump(seed=0):
    """A village hand pump (50 x 80, pump scale: chest high to a person, its handle raised over
    it): a cast iron column painted dark green on a stone block, lit down its west side in one
    clean band, a fluted cap and a brass knob, the spout over a small stone basin with water in it,
    moss at the foot."""
    rng = np.random.default_rng(seed)
    p = canvas(54, 86, 27, 82)
    a = p.a
    Y, X = grid(a)
    V.prism(a, 4, 64, 50, 82, 5, 'stone', 3, side=3)                    # the basin
    bas = (X >= 4) & (X < 50) & (Y >= 64) & (Y < 82)
    front = (X >= 4) & (X < 45) & (Y >= 70) & (Y < 81)
    V.ashlar(a, 4, 70, 45, 81, rng, hd=True, where=front)              # dressed blocks, each lit on its arris
    _weather(a, bas, rng, 'ashlar_warm', 'stone_cool', 3.0)
    a[(Y >= 65) & (Y < 69) & (X >= 28) & (X < 34)] = C('water_cool', 1)   # the column's shadow on the water
    water = (X >= 7) & (X < 46) & (Y >= 65) & (Y < 69)
    rpaint(a, water, [('water_cool', 'water', 'sky')], 2.4 + 1.2 * (Y == 65) + 1.0 * ((X > 12) & (X < 18)), 0)
    a[bas & (Y > 76) & (X < 14)] = C('leaf_cool', 2)
    green = [('dusk_cool', 'leaf_cool', 'leaf')]
    col = (np.abs(X - 22) <= 6) & (Y >= 22) & (Y < 66)
    u = (X - 22) / 6.0
    rpaint(a, col, green, 2.4 + 1.6 * (u < -0.45) + 0.8 * ((u >= -0.45) & (u < 0)) - 1.0 * (u > 0.5), 0)
    for b_ in (30, 52):                                                  # the cast bands
        a[col & (np.abs(Y - b_) < 1)] = C('leaf_cool', 1)
        a[col & (Y == b_ - 1) & (u < 0)] = C('leaf', 4)
    cap = ((X - 22) / 8.5) ** 2 + ((Y - 19) / 4.0) ** 2 <= 1
    rpaint(a, cap, green, 2.6 + 1.6 * (X < 20) - 0.8 * (X > 25), 0)
    knob = ((X - 22) / 2.6) ** 2 + ((Y - 13) / 2.6) ** 2 <= 1
    rpaint(a, knob, [('brass', 'brass', 'brass_warm')], 3.0 + 1.6 * ((X < 22) & (Y < 13)), 0)
    V.bar(a, 26, 32, 48, 14, 1.4, 'iron', 3)                             # the handle, raised
    a[V.seg_mask(a.shape, 46, 15, 50, 13, 1.6)] = C('iron', 2)
    spout = (X >= 26) & (X < 38) & (Y >= 44) & (Y < 49)
    rpaint(a, spout, green, 2.8 + 1.3 * (Y == 44) - 1.0 * (X > 35), 0)
    a[49:66, 35:37] = C('water', 3)
    a[49:66, 35] = C('sky', 4)
    V.finish(p)
    return p


AWNINGS = {'produce': (('berry_cool', 'berry', 'fox'), ('sand_cool', 'plaster_warm', 'plaster')),
           'cloth': (('leaf_cool', 'leaf', 'grass_warm'), ('sand_cool', 'plaster_warm', 'plaster'))}


def stall(kind='produce', seed=0):
    """A market stall (140 x 122, stall scale): a striped awning on four poles sagging between them,
    its scalloped valance, a trestle under a cloth with an embroidered hem, price slates, and its
    goods: crates of apples, cabbages and carrots and a basket of eggs, or bolts of cloth stacked
    with a measuring rule."""
    rng = np.random.default_rng(seed)
    W, H = 144, 126
    p = canvas(W, H, W // 2, H - 4)
    a = p.a
    Y, X = grid(a)
    nz = noise(a.shape, rng, 1.0)
    L, R = 8, W - 8
    for px in (L + 8, R - 8):                                            # the back poles
        V.bar(a, px, 14, px, 80, 1.3, 'timber', 2)
    sa, sb = AWNINGS[kind]
    aw = (X >= L - 4) & (X < R + 4) & (Y >= 8) & (Y < 34) & (Y - 8 >= (np.abs(X - W / 2) - (R - L) / 2 + 4) * 0.4)
    st = np.mod((X - L) // 11, 2) == 0
    sag = np.sin(np.mod(X - L, 22) / 22 * math.pi)
    t = 3.4 - 0.08 * (Y - 8) + 0.6 * (Y < 11) - 0.8 * (X > R - 12) + 0.6 * (nz - 0.5) + 0.7 * sag - 0.8 * (np.mod(X - L, 11) == 10)
    rpaint(a, aw & st, [sa, (sa[0], sa[1], 'brass_warm')], t, nz)
    rpaint(a, aw & ~st, [sb, ('stone_warm', 'sand', 'plaster')], t + 0.4, nz)
    stain = aw & (noise(a.shape, rng, 2.2) > 0.68)                       # weather stains on the canvas
    a[stain] = np.maximum(a[stain] - 1, (a[stain] // 8) * 8)
    seam = aw & (np.mod(X - L, 11) == 5) & (np.mod(Y, 2) == 0)
    a[seam] = np.maximum(a[seam] - 1, (a[seam] // 8) * 8)
    val = (X >= L - 4) & (X < R + 4) & (Y >= 34) & (Y < 40) & (np.hypot(np.mod(X - L, 11) - 5.5, Y - 33.5) <= 5.8)
    rpaint(a, val & st, [sa], 2.4, 0)
    rpaint(a, val & ~st, [sb], 3.0, 0)
    a[(Y >= 40) & (Y < 42) & (X >= L) & (X < R)] = C('soot', 1)
    ty = 74
    table = (X >= L + 6) & (X < R - 6) & (Y >= ty) & (Y < ty + 5)
    rpaint(a, table, WOOD, 3.6 + 1.0 * (Y == ty) - 0.8 * (X > R - 14), 0.3)
    cloth = (X >= L + 6) & (X < R - 6) & (Y >= ty + 5) & (Y < H - 10 + 2 * np.sin(X * 0.5))
    cs = ([('dusk_cool', 'sky_cool', 'sky'), ('slate_cool', 'sky_cool', 'sky'), ('dusk_cool', 'dusk', 'sky')] if kind == 'produce' else
          [('crag_cool', 'clay', 'brass'), ('earth_cool', 'clay', 'brass'), ('crag_cool', 'crag_warm', 'sand_warm')])
    fold = np.sin((X - L) / (R - L) * math.pi * 12 + 0.4)
    rpaint(a, cloth, cs, 2.9 + 0.7 * fold - 0.6 * ((Y - ty) / 40) + 0.6 * (X < L + 9) - 0.9 * (X > R - 10) + 0.8 * (Y < ty + 7),
           noise(a.shape, rng, 2.0))
    if kind == 'produce':                                                # gingham: the checks fold with the cloth
        chk = cloth & ((np.mod(X - L, 8) < 4) ^ (np.mod(Y - ty, 8) < 4))
        rpaint(a, chk, [('stone_cool', 'plaster_warm', 'plaster'), ('sky_cool', 'sky', 'plaster')],
               3.2 + 0.7 * fold - 0.6 * ((Y - ty) / 40) - 0.9 * (X > R - 10), 0.5 * ((np.mod(X - L, 8) < 4) & (np.mod(Y - ty, 8) < 4)))
    else:                                                                # a striped cloth with sprigs of flowers
        band = cloth & (np.mod(X - L, 12) < 4)
        rpaint(a, band, [('earth_cool', 'brass', 'sand_warm'), ('clay_cool', 'brass', 'brass_warm')],
               3.0 + 0.7 * fold - 0.6 * ((Y - ty) / 40) - 0.9 * (X > R - 10), 0.3)
        spr = cloth & (np.mod(X - L + 3 * ((Y - ty) // 7), 9) == 0) & (np.mod(Y - ty, 7) == 3)
        a[spr] = C('plaster_warm', 4)
        a[np.roll(spr, 1, axis=1) & cloth] = C('leaf', 3)
    hem = cloth & (Y >= H - 20) & (Y < H - 16)
    rpaint(a, hem, [('brass', 'brass_warm', 'sand_warm') if kind == 'produce' else ('dusk_cool', 'sky_cool', 'sky')],
           3.0 + 1.2 * (np.mod(X, 4) == 0) - 0.8 * (Y == H - 17) + 0.5 * fold, 0)
    for px in (L, R):                                                    # the front poles
        V.prism(a, px - 2, 16, px + 2, H - 4, 1, 'timber', 3, side=1)
    if kind == 'produce':
        for x0, what in ((L + 10, 'apples'), (L + 40, 'cabbages'), (L + 70, 'carrots'), (L + 100, 'eggs')):
            if what == 'eggs':                                           # a basket of eggs
                bk = ((X - (x0 + 9)) / 10) ** 2 + ((Y - (ty - 3)) / 5) ** 2 <= 1
                rpaint(a, bk & (Y > ty - 5), FM.STRAW, 2.4 + 1.2 * (np.mod(X + Y, 3) == 0), 0.3)
                for k in range(6):
                    ex_, ey_ = x0 + 3 + 2.5 * k, ty - 6 - (k % 2)
                    a[_ell_m(X, Y, ex_, ey_, 1.6, 2.0)] = C('plaster_warm', 4 if k % 2 else 3)
                V.bar(a, x0 + 1, ty - 4, x0 + 9, ty - 14, 0.7, 'timber_warm', 3)
                V.bar(a, x0 + 9, ty - 14, x0 + 17, ty - 4, 0.7, 'timber_warm', 3)
                continue
            V.prism(a, x0, ty - 12, x0 + 26, ty, 3, 'timber', 3, side=2)
            for k in range(18):
                gx, gy = x0 + 3 + rng.uniform(0, 20), ty - 14 + rng.uniform(0, 4)
                if what == 'apples':
                    m = np.hypot(X - gx, Y - gy) <= 2.4
                    rpaint(a, m, [('berry_cool', 'berry', 'fox'), ('leaf_cool', 'grass_warm', 'brass')], 2.4 + 2.0 * sphere_light(X, Y, gx, gy, 2.4, 2.4),
                           0.0 if k % 4 else 0.9)
                elif what == 'cabbages' and k < 6:
                    m = np.hypot(X - gx, Y - gy + 1) <= 4.2
                    rpaint(a, m, [('leaf_cool', 'leaf', 'grass_warm'), ('grass_cool', 'leaf', 'leaf_warm')],
                           2.2 + 2.0 * sphere_light(X, Y, gx, gy - 1, 4.2, 4.2) - 0.9 * (np.mod(np.arctan2(Y - gy, X - gx) * 3, 1) < 0.2), 0.4)
                elif what == 'carrots':
                    a[V.seg_mask(a.shape, gx, gy + 3, gx + 4, gy - 1, 1.0)] = C('fox', 3 + k % 2)
                    a[int(gy) - 2:int(gy), int(gx) + 4] = C('leaf', 3)
    else:
        fams = (('berry_cool', 'berry', 'fox'), ('dusk_cool', 'sky_cool', 'sky'), ('leaf_cool', 'leaf', 'grass_warm'),
                ('earth_cool', 'brass', 'brass_warm'), ('dusk_cool', 'dusk', 'sky'), ('stone_cool', 'plaster_warm', 'plaster'),
                ('crag_cool', 'clay', 'sand_warm'), ('slate_cool', 'stone', 'plaster_warm'))
        for j, fam in enumerate(fams):
            x0 = L + 10 + j * 14
            for k in range(3 - j % 2):
                y0 = ty - 6 - k * 6
                m = (X >= x0 + k) & (X < x0 + 12 - k) & (Y >= y0) & (Y < y0 + 6)
                rpaint(a, m, [fam], 3.0 + 1.3 * (Y == y0) - 1.0 * (Y == y0 + 5) - 0.8 * (X >= x0 + 10 - k), 0)
                a[m & (X == x0 + 11 - k)] = C(fam[0], 2)
        V.bar(a, L + 12, ty - 2, R - 30, ty - 2, 0.6, 'brass', 4)         # the measuring rule
    for tx in (L + 20, L + 50, L + 80):                                   # price slates
        a[ty + 7:ty + 11, tx:tx + 7] = C('soot', 1)
        a[ty + 8, tx + 1:tx + 6:2] = C('plaster', 4)
    V.finish(p)
    return p


def _refam(a, m, fam):
    """The same tones in another family (weathering: a stone warmed by lichen, cooled by damp)."""
    a[m] = FI[fam] * 8 + np.mod(a[m], 8)


def _weather(a, m, rng, warm='stone_warm', cool='stone_cool', sigma=2.0):
    n = noise(a.shape, rng, sigma)
    _refam(a, m & (n > 0.66) & (a >= 0), warm)
    _refam(a, m & (n < 0.3) & (a >= 0), cool)


def _ell_m(X, Y, cx, cy, rx, ry):
    return ((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2 <= 1


def shrine(seed=0):
    """A wayside shrine (62 x 104, shrine scale): a dressed stone pillar on a step under a little
    gabled roof of slates with a stone cross, a niche with a lamp burning low and its glow on the
    stone, moss and lichen on the north side, flowers in a jar and candle stubs on the step."""
    rng = np.random.default_rng(seed)
    p = canvas(66, 110, 33, 106)
    a = p.a
    Y, X = grid(a)
    V.prism(a, 4, 92, 62, 106, 4, 'stone', 3, side=3)                   # the step
    pil = (X >= 14) & (X < 52) & (Y >= 30) & (Y < 94)
    V.ashlar(a, 14, 30, 52, 94, rng, hd=True, where=pil)
    a[pil & (X >= 47)] = np.maximum(a[pil & (X >= 47)] - 1, (a[pil & (X >= 47)] // 8) * 8)
    _weather(a, pil, rng, 'ashlar_warm', 'stone_cool', 1.6)
    damp = pil & (noise(a.shape, rng, 1.0) > 0.72) & (Y > 60)
    a[damp] = np.maximum(a[damp] - 1, (a[damp] // 8) * 8)
    _weather(a, (X >= 4) & (X < 62) & (Y >= 92), rng, 'stone_warm', 'slate_cool')
    niche = (X >= 22) & (X < 44) & (Y >= 40) & (Y < 68) & (Y >= 40 + 0.08 * (X - 33) ** 2)
    rpaint(a, niche, [('dusk_cool', 'sky_cool', 'sky'), ('soot', 'dusk_cool', 'sky_cool')], 1.4 + 0.9 * (Y < 50) - 0.8 * (X > 40), 0.3)   # painted inside
    stars = niche & (np.mod(X * 3 + Y * 5, 17) == 0) & (Y < 54)
    a[stars] = C('brass', 4)
    a[niche & (Y > 62)] = C('soot', 0)
    dist = np.hypot(X - 33, Y - 57)
    glow = niche & (dist <= 7)
    rpaint(a, glow, [('dusk_cool', 'crag_cool', 'clay'), ('crag_cool', 'clay', 'lamp')], 3.4 - 0.4 * dist, 0)
    flame = (np.abs(X - 33) <= 1) & (Y >= 53) & (Y < 58)
    a[flame] = C('lamp', 5)
    a[56:58, 32:35] = C('lamp', 4)
    a[58:64, 30:37] = C('brass', 3)
    a[58:64, 30] = C('brass_warm', 4)
    a[pil & ~niche & (np.hypot(X - 33, Y - 66) < 6) & (Y > 66)] = C('ashlar_warm', 4)     # the glow on the sill
    moss = pil & (noise(a.shape, rng, 1.2) > 0.7) & (Y > 70)
    rpaint(a, moss, [('leaf_cool', 'leaf', 'brass'), ('grass_cool', 'leaf_cool', 'leaf_warm')], 2.4 + rng.random(a.shape), rng.random(a.shape))
    for k in range(5):                                                   # ivy up the west side
        y0 = 92 - k * 11
        a[V.seg_mask(a.shape, 15, y0, 13 + (k % 2) * 3, y0 - 9, 0.5)] = C('leaf_cool', 2)
        lf = _ell_m(X, Y, 13 + (k % 2) * 4, y0 - 5, 2.0, 1.5)
        rpaint(a, lf, [('leaf_cool', 'leaf', 'leaf_warm')], 2.6 + 1.2 * (X < 14 + (k % 2) * 4), 0)
    lich = pil & (rng.random(a.shape) < 0.03) & (Y < 70)
    a[lich] = C('brass', 3)
    roof = (Y >= 12) & (Y < 34) & (np.abs(X - 33) <= 6 + (Y - 12) * 1.2)
    rpaint(a, roof, [('slate_cool', 'slate', 'slate_warm'), ('dusk_cool', 'slate', 'stone')],
           3.6 - 1.5 * (X > 33) - 1.2 * (np.mod(Y - 12, 4) == 3) + 0.4 * (np.mod(X + (Y // 4) * 3, 6) == 0), np.mod((Y // 4) * 0.4, 1))
    a[roof & (np.abs(X - 33) < 1.2)] = C('stone_warm', 4)
    a[(Y >= 32) & (Y < 35) & (X >= 12) & (X < 54)] = C('soot', 1)
    cross = ((np.abs(X - 33) <= 1) & (Y >= 1) & (Y < 13)) | ((np.abs(Y - 5) <= 1) & (np.abs(X - 33) <= 4))
    rpaint(a, cross, [('stone_cool', 'stone', 'stone_warm')], 3.4 + 1.2 * (X < 33), 0)
    V.prism(a, 8, 84, 16, 93, 1, 'clay', 3, side=1)                      # the jar and its flowers
    for k, (fx_, fam) in enumerate(((7, 'berry'), (10, 'sky'), (13, 'brass_warm'), (16, 'plaster'), (9, 'fox'))):
        a[V.seg_mask(a.shape, 12, 84, fx_, 76 - k % 2, 0.5)] = C('leaf_cool', 3)
        a[75 - k % 2:77 - k % 2, fx_ - 1:fx_ + 1] = C(fam, 4)
    for cx_ in (50, 55):                                                 # candle stubs
        a[86:93, cx_:cx_ + 3] = C('plaster', 4)
        a[86:93, cx_ + 2] = C('plaster_warm', 3)
        a[84:86, cx_ + 1] = C('lamp', 5)
    V.finish(p)
    return p


def cart(seed=0):
    """A farm cart at rest (100 x 64): a plank body on a big spoked wheel, its shafts down on the
    grass, a little hay left in it, the near side lit along its top rail."""
    rng = np.random.default_rng(seed)
    p = canvas(104, 68, 52, 64)
    a = p.a
    Y, X = grid(a)
    nz = noise(a.shape, rng, 1.0)
    V.bar(a, 64, 34, 100, 62, 1.6, 'timber', 3)                          # the shafts
    V.bar(a, 70, 30, 102, 58, 1.4, 'timber', 2)
    body = (X >= 8) & (X < 74) & (Y >= 16) & (Y < 40)
    rpaint(a, body, WOOD, 3.0 + 1.3 * (np.mod(Y - 16, 6) == 0) - 1.1 * (np.mod(Y - 16, 6) == 5) - 0.9 * (X > 68) + 0.6 * (nz - 0.5),
           np.mod((Y - 16) // 6 * 0.37, 1))
    for sx in (10, 40, 70):
        V.prism(a, sx, 14, sx + 3, 40, 1, 'timber', 3, side=1)
    hay = ((X - 40) / 30) ** 2 + ((Y - 16) / 5) ** 2 <= 1
    hay &= Y < 18
    rpaint(a, hay, FM.STRAW, 3.0 + 1.4 * (Y < 13) + 0.8 * (nz - 0.5), nz)
    a[(Y == 16) & body] = C('timber_warm', 5)
    # the wheel
    wx, wy, r = 38, 46, 16.0
    d = np.hypot(X - wx, Y - wy)
    tyre = (d <= r) & (d > r - 2)
    rpaint(a, tyre, [('soot', 'iron', 'stone')], 2.2 + 1.6 * ((X - wx) + (Y - wy) < -6), 0)
    felloe = (d <= r - 2) & (d > r - 4.5)
    rpaint(a, felloe, WOOD, 2.8 + 1.2 * ((X - wx) + (Y - wy) < 0) - 0.6 * (np.mod(np.arctan2(Y - wy, X - wx) * 6 / math.pi, 1) < 0.1), 0.2)
    for k in range(10):
        ang = k * math.pi / 5
        a[V.seg_mask(a.shape, wx + 3 * math.cos(ang), wy + 3 * math.sin(ang), wx + (r - 4) * math.cos(ang), wy + (r - 4) * math.sin(ang), 0.7)] = \
            C('timber', 3 if math.cos(ang) + math.sin(ang) < 0 else 2)
    hub = d <= 3.2
    rpaint(a, hub, [('soot', 'iron', 'stone')], 2.4 + 1.6 * sphere_light(X, Y, wx, wy, 3.2, 3.2), 0)
    V.finish(p)
    return p


# ------------------------------------------------------------------------------------------------
# pieces
# ------------------------------------------------------------------------------------------------
FINGERPOSTS = ('nes', 'esw', 'nsw', 'new', 'nesw')
WILD = ['wild_woods']


def _rel(rel, what, cells=None, note=None):
    return FM._rel(rel, what, cells, note)


def statics():
    """(piece id, picture, piece kwargs, logic) for every commons piece; logic is the placement
    data the audit checks (provides, needs, faces, avoid, points)."""
    on_edge = [_rel('at_edge', 'route', 1, 'beside the way people walk')]
    out = [
        ('commons_washing_line', washing_line(seed=3), dict(
            name='Washing line', purpose='work', role='washing_line', cells=(5, 1), fp=FM._fp(6, 1),
            collision={'shape': 'rect', 'rect': [-19.0, -1.5, 38, 1.5]}, shadow=(36, 2),
            forbids=[FM.OFF_ROUTE, FM.OFF_WATER], size_class='washing_line',
            eastward='12 and 13: the laundry strung across the lanes, cloth in folds', note='Washing pegged out in a back yard.'),
         {'needs': [{'what': 'home', 'cells': 4, 'side': 'yard', 'note': 'washing hangs in a back yard, never before the front door'}],
          'avoid': WILD}),
        ('commons_chopping_block', chopping_block(seed=5), dict(
            name='Chopping block', purpose='work', role='chopping_block', cells=(2, 1), fp=FM._fp(1, 1),
            collision={'shape': 'rect', 'rect': [-4.0, -3.0, 8, 3]}, shadow=(12, 3),
            forbids=[FM.OFF_ROUTE, FM.OFF_WATER], size_class='stump',
            eastward='17: the axe in the block by the woodshed', note='Where the kindling is split.'),
         {'needs': [{'what': 'hearth', 'cells': 6, 'note': 'wood is split near the fire it feeds'}]}),
        ('commons_woodpile', woodpile(seed=7), dict(
            name='Woodpile', purpose='store', role='store', cells=(3, 1), fp=FM._fp(3, 1),
            collision={'shape': 'rect', 'rect': [-11.0, -4.0, 22, 4]}, shadow=(26, 3),
            forbids=[FM.OFF_ROUTE, FM.OFF_WATER], size_class='woodpile',
            eastward='17 and 12: split logs stacked under the eaves, cut ends lit', note='Fuel stacked by the hearth it feeds.'),
         {'needs': [{'what': 'hearth', 'cells': 4, 'note': 'fuel is stacked against the house with the chimney'}]}),
        ('commons_bench', bench(seed=9), dict(
            name='Bench', purpose='rest', role='seat', cells=(3, 1), fp=FM._fp(3, 1),
            collision={'shape': 'rect', 'rect': [-14.0, -3.0, 28, 3]}, shadow=(32, 3),
            forbids=[FM.OFF_ROUTE, FM.OFF_WATER], size_class='bench',
            eastward='12: benches along the square, planks lit on top', note='A bench facing something worth looking at.'),
         {'faces': {'what': ['feature', 'view', 'water', 'lower'], 'cells': 6,
                    'note': 'a bench faces a green, a well, water or a view, never a blank wall'}}),
        ('commons_notice_board', notice_board(seed=11), dict(
            name='Notice board', purpose='guide', role='marker', cells=(3, 1), fp=FM._fp(2, 1),
            collision={'shape': 'rect', 'rect': [-8.0, -2.0, 16, 2]}, shadow=(20, 2), requires=on_edge,
            forbids=[FM.OFF_ROUTE, FM.OFF_WATER], size_class='sign',
            eastward='12: notices pinned to boards by the doors', note='Notices where people pass.'),
         {'avoid': WILD}),
        ('commons_pump', pump(seed=5), dict(
            name='Village pump', purpose='water', role='centrepiece', cells=(2, 1), fp=FM._fp(2, 1),
            collision={'shape': 'rect', 'rect': [-7.5, -5.0, 15, 5]}, shadow=(16, 3),
            requires=[_rel('near', 'house', 8, 'water for homes')], forbids=[FM.OFF_ROUTE, FM.OFF_WATER],
            size_class='pump', eastward='12: the square\'s ironwork painted dark, lit down one side',
            note='The pump on the green, its trough below the spout.'),
         {'provides': ['feature', 'water'], 'avoid': WILD}),
        ('commons_stall_produce', stall('produce', seed=15), dict(
            name='Market stall, produce', purpose='work', role='stall', cells=(6, 1), fp=FM._fp(6, 1),
            collision={'shape': 'rect', 'rect': [-21.0, -4.0, 42, 4]}, shadow=(44, 3), requires=on_edge,
            forbids=[FM.OFF_ROUTE, FM.OFF_WATER], size_class='stall',
            eastward='12 and 13: striped awnings, crates of produce', note='A greengrocer\'s stall at the market.'),
         {'avoid': WILD}),
        ('commons_stall_cloth', stall('cloth', seed=4), dict(
            name='Market stall, cloth', purpose='work', role='stall', cells=(6, 1), fp=FM._fp(6, 1),
            collision={'shape': 'rect', 'rect': [-21.0, -4.0, 42, 4]}, shadow=(44, 3), requires=on_edge,
            forbids=[FM.OFF_ROUTE, FM.OFF_WATER], size_class='stall',
            eastward='12 and 13: striped awnings, bolts of cloth', note='A draper\'s stall beside the greengrocer\'s.'),
         {'avoid': WILD}),
        ('commons_cart', cart(seed=19), dict(
            name='Farm cart', purpose='store', role='cart', cells=(5, 2), fp=FM._fp(4, 1),
            collision={'shape': 'rect', 'rect': [-14.0, -4.0, 30, 4]}, shadow=(36, 4), requires=on_edge,
            forbids=[FM.OFF_ROUTE, FM.OFF_WATER], size_class='handcart',
            eastward='17: the farm cart, its big wheel', note='A cart left at the road\'s edge.'),
         {}),
        ('commons_shrine', shrine(seed=3), dict(
            name='Wayside shrine', purpose='mark', role='marker', cells=(3, 1), fp=FM._fp(3, 1),
            collision={'shape': 'rect', 'rect': [-9.0, -4.0, 18, 4]}, shadow=(20, 3), requires=on_edge,
            forbids=[FM.OFF_ROUTE, FM.OFF_WATER], size_class='shrine',
            eastward='38 and 12: small stone shrines by the way, a light kept in them', note='A lamp kept at the wayside.'),
         {'provides': ['feature']}),
    ]
    for k, pts in enumerate(FINGERPOSTS):
        out.append(('commons_fingerpost_' + pts, fingerpost(pts, seed={'new': 36}.get(pts, 31 + k)), dict(
            name='Fingerpost, %s' % '-'.join(pts.upper()), purpose='guide', role='signpost', cells=(3, 1), fp=[[0, -1]],
            collision={'shape': 'rect', 'rect': [-1.5, -1.5, 3, 1.5]}, shadow=(6, 2),
            forbids=[FM.OFF_ROUTE, FM.OFF_WATER], size_class='sign',
            eastward='38: way markers at the forks, painted boards', note='A signpost at a junction, an arm along each way.'),
            {'points': list(pts)}))
    return out


def build(write=True, force=False):
    out = {}
    pieces = []
    for pid, pic, kw, logic in statics():
        pic = FM.trim([pic])[0]
        sp = os.path.join(ART, pid[len('commons_'):] + '.png')
        out[sp] = to_rgba(pic.a)
        pc = FM._base(pid, kw.pop('name'), sp, (pic.ax, pic.ay), (pic.W, pic.H), kw.pop('purpose'), kw.pop('role'), **kw)
        pc['variants'][0]['png'] = RES + os.path.basename(sp)
        pc['audit']['painter'] = {'module': 'scripts.art.kit.commons', 'fn': pid, 'args': {}}
        pc['audit']['seeded_from'] = 'scripts/art/kit/commons.py'
        pc['placement'].update(logic)
        pieces.append(pc)
    if write:
        os.makedirs(ART, exist_ok=True)
        for p, a in out.items():
            Image.fromarray(a, 'RGBA').save(p, optimize=True)
        for pc in pieces:
            path = os.path.join(PIECES, 'prop', pc['id'] + '.json')
            if force or not os.path.exists(path):
                json.dump(pc, open(path, 'w'), indent=1)
                open(path, 'a').write('\n')
    return out


def check() -> int:
    bad = []
    for p, a in build(write=False).items():
        if not os.path.exists(p) or not np.array_equal(np.asarray(Image.open(p).convert('RGBA')), a):
            bad.append(os.path.relpath(p, ROOT))
    if bad:
        print('commons: stale pictures %s (run python3 -m scripts.art.kit.commons)' % ', '.join(bad[:6]))
        return 1
    print('commons: pictures current')
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--force', action='store_true')
    a = ap.parse_args(argv)
    if a.check:
        return check()
    print('commons: %d pictures' % len(build(force=a.force)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
