"""Farmyard pieces for the kit: hens and their coop, sheep and their field shelter, hay, and the
kitchen garden's beds (docs/vision/placement-logic.md: "Keep animals in: a paddock, sheep fold,
goat pen, chicken run or pigsty, with its animals inside, plus a trough, a water source and
shelter"; docs/vision/placement-audit.md flagged the beds and the hay for a redraw and the trough
as missing its animals and pen).

    python3 -m scripts.art.kit.farm            # pictures and pieces (pieces kept unless --force)
    python3 -m scripts.art.kit.farm --check    # exit 1 if a committed picture is not what this draws

Every picture is a code canvas on the house palette (scripts/art/native/village.py's helpers),
lit from the upper left, closed with the house outline; sizes in texels at density 3 (A = 74):
- a hen 21 tall (0.28 A; size-guide 2: "cat, hen ... 5 to 12 world px", 15 to 36 texels) in white,
  brown and speckled, and her idle: she looks about and pecks (8 frames at 4 a second);
- a sheep 38 tall, 55 long (size-guide 2: 12 to 17 by 16 to 22 world px), a curly fleece and a black
  face: standing (an ear flick and a turn of the head), grazing (her head down, chewing) and
  lying (breathing);
- the hen ark, 54 wide and 62 tall, on legs, a pop hole and a ramp, a nest box on its east end;
- the field shelter, four cells wide, open to the south, a boarded back, straw inside;
- hay: three bales stacked and tied, and a heap forked out loose (size-guide "haystack");
- the kitchen garden's beds: soil ridged into rows with a crop on each, in a dug patch with its
  rough edge where the spade stopped (no boards: Matt's review read the boarded boxes as crates);
  and the same beds burnt, the crops black stubs in ash (the storm's stage).
Animals show a still (the variant's picture: frame 0) and an idle strip beside it
(rendering.animations: strip, frames, fps), played by world/loop_fx.gd only while on screen and
held on frame 0 under reduced motion.
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
from scripts.art.kit.schema import PIECES, ROOT
from scripts.art.native import village as V
from scripts.art.native.palette import FI, to_rgba

ART = os.path.join(ROOT, 'game', 'kit', 'props', 'art', 'farm')
RES = 'res://kit/props/art/farm/'


def C(fam, t):
    return FI[fam] * 8 + int(max(0, min(5, round(t))))


def canvas(w, h, ax, ay):
    return V.Pic(w, h, ax, ay)


def grid(a):
    """Texel coordinates (integers, so the courses, boards and rows can be counted with %)."""
    return np.mgrid[0:a.shape[0], 0:a.shape[1]].astype(float)


def sphere_light(X, Y, cx, cy, rx, ry):
    """Light on an ellipsoid lit from the upper left (-1 .. 1)."""
    nx, ny = (X - cx) / rx, (Y - cy) / ry
    nz = np.sqrt(np.clip(1 - nx ** 2 - ny ** 2, 0, 1))
    return -0.55 * nx - 0.65 * ny + 0.5 * nz


# ------------------------------------------------------------------------------------------------
# hens
# ------------------------------------------------------------------------------------------------
HENS = {
    # id: body (cool, body, warm), wing, tail, face (1 east, -1 west), speckles
    'white': (('plaster_warm', 'plaster', 'plaster'), 'plaster_warm', 'plaster_warm', 1, None),
    'brown': (('clay_cool', 'fox', 'fox'), 'clay', 'soot', -1, None),
    'speckled': (('stone_cool', 'stone', 'stone_warm'), 'stone_cool', 'soot', 1, 'soot'),
}
HEN_FRAMES = ['up', 'up', 'look', 'up', 'peck', 'peck2', 'peck', 'up']


def hen(kind, pose='up', seed=0):
    """A hen (21 x 26 texels): a round body lit on top, the wing folded on her flank in two rows of
    feathers, the tail cocked up behind, the head forward with its red comb and wattle, a yellow
    beak, a dark eye with a glint, yellow legs. `pose`: up, look (head turned back), peck, peck2
    (head down to the ground)."""
    body_f, wing_f, tail_f, face, speck = HENS[kind]
    rng = np.random.default_rng(seed)
    p = canvas(34, 30, 17, 27)
    a = p.a
    Y, X = grid(a)
    cx, yb = 17 - face * 1, 27
    # legs and feet (behind the body)
    for dx in (-2, 2):
        x = int(cx + dx)
        a[yb - 6:yb - 1, x:x + 1] = C('brass', 3)
        a[yb - 1, x - 1:x + 2] = C('brass', 2)
    by = yb - 11.5
    peck = pose in ('peck', 'peck2')
    tilt = 1.0 if peck else 0.0
    body = ((X - cx) / 8.2) ** 2 + ((Y - by - tilt) / 6.4) ** 2 <= 1
    tail = ((X - (cx - face * 8.0)) / 3.6) ** 2 + ((Y - (by - 5.0 + tilt * 1.5)) / 5.6) ** 2 <= 1
    tail &= (Y < by + 2)
    m = body | tail
    lit = sphere_light(X, Y, cx, by, 8.5, 7.0)
    V.paint(a, m, body_f, 3.0 + 1.6 * lit)
    # tail feathers: dark sickles over a lighter fan
    tf = tail & (((X * face + Y) % 3) == 0)
    a[tf] = C(tail_f if tail_f != 'soot' else 'soot', 2 if tail_f == 'soot' else 2)
    # the folded wing: two rows of scalloped feathers on the flank, a step darker
    wx, wy = cx - face * 1.0, by + 0.5
    wing = (((X - wx) / 5.6) ** 2 + ((Y - wy) / 3.6) ** 2 <= 1) & body
    V.paint(a, wing, (wing_f, wing_f, wing_f), 2.4 + 0.9 * sphere_light(X, Y, wx, wy - 2, 6, 4))
    for row, yy in enumerate((wy - 0.5, wy + 1.8)):
        sc = wing & (np.abs(Y - yy - 0.9 * np.cos((X - wx) * 1.2 + row)) < 0.5)
        a[sc] = C(wing_f, 1)
    if speck:
        sp = body & (rng.random(a.shape) < 0.09) & ~wing
        a[sp] = C(speck, 2)
    # belly shade and the line where she sits on the ground
    a[body & (Y > by + 4.2 + tilt)] = C(body_f[0], 1 if kind != 'white' else 2)
    # the head
    if pose == 'look':
        hx, hy = cx + face * 4.0, by - 7.5
    elif peck:
        hx, hy = cx + face * 9.0, yb - (4.5 if pose == 'peck' else 3.0)
    else:
        hx, hy = cx + face * 6.6, by - 7.0
    neck = V.seg_mask(a.shape, cx + face * 3.5, by - 2.5, hx, hy + 1, 2.6)
    head = ((X - hx) / 3.1) ** 2 + ((Y - hy) / 3.0) ** 2 <= 1
    hm = (neck | head) & ~(body & (Y > by - 1))
    V.paint(a, hm, body_f, 3.4 + 1.3 * sphere_light(X, Y, hx, hy, 3.5, 3.5))
    fwd = face if pose != 'look' else -face
    # comb (three red bumps on the crown) and wattle (under the beak)
    for k, dx in enumerate((-1.6, 0.0, 1.6)):
        cm = ((X - (hx + dx * fwd * 0.8 - fwd * 0.4)) / 1.1) ** 2 + ((Y - (hy - 3.2 + 0.3 * abs(dx))) / 1.4) ** 2 <= 1
        a[cm] = C('berry', 4 if k == 0 else 3)
    wm = ((X - (hx + fwd * 1.6)) / 1.0) ** 2 + ((Y - (hy + 2.8)) / 1.6) ** 2 <= 1
    a[wm] = C('berry', 3)
    # beak and eye
    bx = int(round(hx + fwd * 3.0))
    by_ = int(round(hy))
    a[by_ - 1:by_ + 1, min(bx, bx + fwd * 2):max(bx, bx + fwd * 2) + 1] = C('brass', 4)
    a[by_, min(bx, bx + fwd * 2):max(bx, bx + fwd * 2) + 1] = C('brass', 3)
    ex = int(round(hx + fwd * 0.9))
    a[by_ - 1, ex] = C('soot', 0)
    if pose == 'peck2':                              # a seed picked up
        a[yb - 1, int(hx + fwd * 4)] = C('brass', 5)
    V.finish(p)
    return p


# ------------------------------------------------------------------------------------------------
# sheep
# ------------------------------------------------------------------------------------------------
SHEEP_FRAMES = {
    'stand': ['a', 'a', 'a', 'ear', 'a', 'turn', 'turn', 'a'],
    'graze': ['down', 'chew', 'down', 'chew', 'down', 'down', 'ear', 'down'],
    'lie': ['in', 'in', 'out', 'out', 'in', 'in', 'out', 'ear'],
}


def sheep(pose='stand', frame='a', face=1, seed=0):
    """A ewe (55 x 38 texels standing): a fleece of curls, each lit on its upper left, shading to
    her belly and rump, a black face and ears, four black legs (the far pair a step darker); grazing
    her head is down at the grass; lying her legs are folded under and her fleece is on the ground."""
    rng = np.random.default_rng(seed)
    p = canvas(84, 56, 42, 52)
    a = p.a
    Y, X = grid(a)
    cx, yb = 42 - face * 3, 52
    lie = pose == 'lie'
    breathe = 1 if (lie and frame == 'out') else 0
    by = yb - (12 if lie else 21)
    rx, ry = 22.5, (12.5 + breathe * 0.5 if lie else 13.0)
    # legs (behind the fleece): short and thin, the far pair a step darker, a lit west edge
    if not lie:
        for lx, far in ((-12.5, True), (8.5, True), (-9.5, False), (12.0, False)):
            x = int(round(cx + face * lx))
            t = 1 if far else 2
            a[int(by + 6):yb - 1, x:x + 3] = C('soot', t)
            a[int(by + 6):yb - 1, x] = C('soot', t + 2)
            a[yb - 2:yb, x - (1 if face < 0 else 0):x + 3 + (1 if face > 0 else 0)] = C('soot', 0)
    # the fleece: the body mass and a crust of curls over it, each a little dome lit on its upper
    # left with a dark crease round its lower right
    fleece = ((X - cx) / rx) ** 2 + ((Y - by) / ry) ** 2 <= 1
    curls = rng.uniform(-1, 1, (110, 2))
    curls = curls[(curls ** 2).sum(1) <= 1.05]
    cmask = np.zeros(a.shape, bool)
    t = 2.7 + 1.6 * sphere_light(X, Y, cx, by, rx, ry)
    crease = np.zeros(a.shape, bool)
    for k, (ux, uy) in enumerate(sorted(curls.tolist(), key=lambda c: c[1])):
        px, py = cx + ux * (rx - 2.0), by + uy * (ry - 1.5)
        m = ((X - px) / 2.9) ** 2 + ((Y - py) / 2.4) ** 2 <= 1
        ring = m & ~(((X - px + 0.6) / 2.2) ** 2 + ((Y - py + 0.6) / 1.7) ** 2 <= 1)
        cmask |= m
        crease = (crease & ~m) | (ring & ((X - px) + (Y - py) > 0.4))
        t = np.where(m, 2.7 + 1.6 * sphere_light(X, Y, cx, by, rx, ry) + 0.8 * sphere_light(X, Y, px, py, 2.9, 2.4), t)
    fleece = (fleece | cmask) & (Y < yb - (0 if lie else 7))
    V.paint(a, fleece, ('sand_cool', 'plaster_warm', 'plaster'), t)
    a[crease & fleece] = np.where((Y < by)[crease & fleece], C('plaster_warm', 2), C('sand_cool', 1))
    a[fleece & (Y > by + ry * 0.6)] = C('sand_cool', 1 if not lie else 2)
    lit = sphere_light(X, Y, cx, by, rx, ry)
    # the head: black, at the front; ears out to the sides
    if pose == 'graze':
        chew = 1 if frame == 'chew' else 0
        hx, hy = cx + face * (rx + 0.5), yb - 7 + chew
        neck = V.seg_mask(a.shape, cx + face * (rx - 5), by - 1, hx, hy - 2, 4.0)
        V.paint(a, neck & ~fleece, ('sand_cool', 'plaster_warm', 'plaster'), 3.0 + sphere_light(X, Y, hx, by, 5, 5))
    elif lie:
        hx, hy = cx + face * (rx - 1.0), by - 6
    else:
        hx, hy = cx + face * (rx + 0.5), by - 8
    hface = face if frame != 'turn' else 0
    head = ((X - hx - hface * 1.2) / 4.6) ** 2 + ((Y - hy) / 5.6) ** 2 <= 1
    muzzle = ((X - hx - hface * 3.8) / 2.8) ** 2 + ((Y - hy - 2.5) / 2.8) ** 2 <= 1
    hm = (head | muzzle)
    V.paint(a, hm, ('soot', 'soot', 'soot'), 1.8 + 1.4 * sphere_light(X, Y, hx, hy, 5, 6))
    ey, ex = int(round(hy - 1.5)), int(round(hx + hface * 2.0))
    a[ey, ex] = C('plaster', 4)
    flick = frame == 'ear'
    for side in (-1, 1):
        ex0 = hx - face * 2.0 + side * 3.0
        ey0 = hy - 4.5 - (1.5 if (flick and side > 0) else 0)
        ear = ((X - (ex0 + side * 2.6)) / 3.0) ** 2 + ((Y - ey0) / 1.4) ** 2 <= 1
        a[ear & ~hm] = C('soot', 2 if side < 0 else 1)
    # a topknot of fleece on the crown
    tk = ((X - (hx - face * 1.5)) / 3.0) ** 2 + ((Y - (hy - 5.5)) / 2.0) ** 2 <= 1
    V.paint(a, tk & ~hm, ('sand_cool', 'plaster_warm', 'plaster'), 4.0 + sphere_light(X, Y, hx, hy - 6, 3, 2))
    V.finish(p)
    return p


# ------------------------------------------------------------------------------------------------
# the coop and the shelter
# ------------------------------------------------------------------------------------------------
def coop(seed=0):
    """A hen ark (54 x 62 texels): a boarded house on four legs, its gabled shingle roof with a
    lit west slope over the south gable, a pop hole with a ramp down to the run, a nest box on the
    east end under its own lid, a perch peg by the door."""
    rng = np.random.default_rng(seed)
    p = canvas(72, 72, 34, 66)
    a = p.a
    Y, X = grid(a)
    x0, x1, yb = 10, 58, 66
    wt, wb = 30, 56                     # the south gable's wall, top and foot
    # legs
    for lx in (x0 + 2, x1 - 6):
        V.prism(a, lx, wb - 2, lx + 4, yb, 1, 'timber', 2, side=1)
    for lx in (x0 + 8, x1 - 12):        # the far legs, in shade
        V.prism(a, lx, wb - 2, lx + 3, yb - 4, 1, 'timber_cool', 1, side=1)
    # the gable wall: vertical boards, lit at their west edge, a darker east end
    wall = (X >= x0) & (X < x1) & (Y >= wt) & (Y < wb)
    board = ((X - x0) // 6).astype(int)
    t = 3.0 + 0.4 * np.sin(board * 2.1) - 1.0 * (((X - x0) % 6) == 5) + 0.8 * (((X - x0) % 6) == 0) - 0.9 * (X > x1 - 9)
    V.paint(a, wall, ('timber_cool', 'timber', 'timber_warm'), t)
    for k in range(12):                 # knots and nail heads
        kx, ky = int(rng.integers(x0 + 2, x1 - 2)), int(rng.integers(wt + 3, wb - 2))
        a[ky, kx] = C('timber_cool', 1)
    for bx in range(x0 + 2, x1, 6):
        a[wt + 3, bx] = C('iron', 2)
        a[wb - 3, bx] = C('iron', 2)
    a[wb - 1, x0:x1] = C('timber_cool', 0)
    # the gable's triangle and the roof: two shingle slopes meeting at the ridge over the gable
    ridge_y, eave_y, ov = 6, wt + 2, 4
    rx0, rx1 = x0 - ov, x1 + ov
    mid = (rx0 + rx1) / 2
    roof = (Y >= ridge_y) & (Y < eave_y) & (np.abs(X - mid) <= (Y - ridge_y) * (rx1 - mid) / (eave_y - ridge_y) + 1)
    west = roof & (X < mid)
    row = ((Y - ridge_y) // 4).astype(int)
    shing = ((X + 3 * (row % 2)) // 6).astype(int)
    tr = np.where(west, 3.4, 2.1) + 0.45 * np.sin(shing * 1.7 + row) - 1.6 * (((Y - ridge_y) % 4) == 3) \
        + 0.9 * (((Y - ridge_y) % 4) == 0)
    tr = tr - 1.0 * ((((X + 3 * (row % 2)) % 6) == 5) & ((Y - ridge_y) % 4 < 3))
    V.paint(a, roof, ('slate_cool', 'slate', 'slate_warm'), tr)
    a[roof & (np.abs(X - mid) < 1.0)] = C('slate_warm', 5)            # the ridge
    # the barge boards along the gable's slopes
    for side in (-1, 1):
        V.bar(a, mid, ridge_y + 1, mid + side * (rx1 - mid), eave_y, 1.2, 'timber_warm' if side < 0 else 'timber', 4 if side < 0 else 2)
    # the eave's shadow on the wall
    a[(Y >= eave_y) & (Y < eave_y + 2) & wall] = C('timber_cool', 1)
    # the pop hole and its ramp, a perch peg
    hx = int(mid - 9)
    a[wb - 13:wb - 2, hx - 4:hx + 4] = C('soot', 0)
    a[wb - 13, hx - 4:hx + 4] = C('timber_warm', 4)
    a[wb - 13:wb - 2, hx + 3] = C('timber_cool', 1)
    ramp = V.seg_mask(a.shape, hx, wb - 1, hx - 6, yb - 1, 2.5)
    V.paint(a, ramp, ('timber_cool', 'timber', 'timber_warm'), 3.6 - 0.4 * ((Y - wb) > 4))
    for k in range(3):
        ty = int(wb + 2 + k * 3)
        tx = int(hx - 2 * (ty - wb) / (yb - wb) * 3)
        a[ty, tx - 3:tx + 2] = C('timber_cool', 1)
    # the nest box on the east end, its lid lit
    nx0, nx1 = x1 - 2, x1 + 9
    V.prism(a, nx0, wt + 12, nx1, wb - 4, 4, 'timber', 3, side=3)
    a[wt + 12:wt + 16, nx0 - 1:nx1 + 1] = C('timber_warm', 4)
    a[wt + 12, nx0 - 1:nx1 + 1] = C('timber_warm', 5)
    a[wt + 18, nx0 + 4] = C('iron', 3)                                  # the lid's hasp
    # straw poking from the pop hole
    for k in range(4):
        a[wb - 3, hx - 3 + 2 * k] = C('brass', 4)
    V.finish(p)
    return p


def shelter(seed=0):
    """A field shelter for the flock (100 x 84 texels): a single-pitch roof of boards on two front
    posts falling to the south, a boarded back wall seen inside in deep shade, straw on its floor,
    a hay rack on the back wall."""
    rng = np.random.default_rng(seed)
    p = canvas(118, 92, 58, 86)
    a = p.a
    Y, X = grid(a)
    x0, x1, yb = 10, 108, 86
    back_foot = yb - 26
    inside = (X >= x0) & (X < x1) & (Y >= back_foot - 34) & (Y < yb)
    # the back wall's inner face (in shade) and the floor
    wall = inside & (Y < back_foot)
    V.paint(a, wall, ('earth_cool', 'timber_cool', 'timber'), 1.4 + 0.6 * (((X - x0) % 8) == 0) - 0.5 * (((X - x0) % 8) == 7))
    floor = inside & (Y >= back_foot)
    V.paint(a, floor, ('earth_cool', 'earth', 'earth_warm'), 1.6 + 0.6 * np.sin(X * 0.7 + Y * 1.3))
    # straw: strands lying across the floor, brighter towards the open front
    for _ in range(140):
        sx, sy = rng.uniform(x0 + 2, x1 - 2), rng.uniform(back_foot + 1, yb - 2)
        ang = rng.uniform(-0.5, 0.5)
        L = rng.uniform(2, 5)
        m = V.seg_mask(a.shape, sx, sy, sx + L * math.cos(ang), sy + L * math.sin(ang), 0.5) & floor
        a[m] = C('brass', 3 if sy > back_foot + 12 else 2)
    # a hay rack on the back wall: a slatted frame with hay in it
    rk = (X >= x0 + 30) & (X < x0 + 64) & (Y >= back_foot - 24) & (Y < back_foot - 12)
    V.paint(a, rk, ('brass', 'brass_warm', 'sand_warm'), 2.6 + 0.8 * np.sin(X * 1.9 + Y * 0.8))
    a[rk & (((X - x0) % 5) == 0)] = C('timber', 2)
    a[(Y == back_foot - 12) & (X >= x0 + 30) & (X < x0 + 64)] = C('timber', 3)
    # the roof: boards along the slope, the front edge lit, the eave's shade under it
    rt, rb = 4, 26
    rx0, rx1 = x0 - 4, x1 + 4
    roof = (X >= rx0) & (X < rx1) & (Y >= rt) & (Y < rb)
    plank = ((X - rx0) // 7).astype(int)
    f = (Y - rt) / (rb - rt)
    t = 4.0 - 1.4 * f + 0.6 * np.sin(plank * 2.3) - 1.6 * (((X - rx0) % 7) == 6) + 0.8 * (((X - rx0) % 7) == 0)
    V.paint(a, roof, ('timber_cool', 'timber', 'timber_warm'), t)
    a[roof & (Y == rt)] = C('timber_warm', 5)
    a[(Y >= rb - 3) & (Y < rb) & (X >= rx0) & (X < rx1)] = C('timber', 2)        # the fascia
    a[(Y == rb - 3) & (X >= rx0) & (X < rx1)] = C('timber_warm', 4)
    for bx in range(rx0 + 3, rx1, 7):
        a[rb - 2, bx] = C('iron', 2)
    a[(Y >= rb) & (Y < rb + 3) & inside] = C('timber_cool', 0)                     # deep shade under the eave
    # the side boards at the west end (lit), the east end in shade, and the two front posts
    V.prism(a, x0, rb, x0 + 5, yb, 1, 'timber', 3, side=1)
    V.prism(a, x1 - 5, rb, x1, yb, 1, 'timber_cool', 2, side=1)
    for px in (x0 + 2, x1 - 7):
        V.prism(a, px, rb - 1, px + 5, yb, 1, 'timber', 3, side=2)
    V.finish(p)
    return p


# ------------------------------------------------------------------------------------------------
# hay
# ------------------------------------------------------------------------------------------------
def bale(a, x0, y0, w, h, d, rng, lit_side=True):
    """A rectangular bale seen from above the south: its top (d texels deep, lit), its south face
    (the cut stalk ends), its east end in shade, two twine bands round it."""
    Y, X = grid(a)
    top = (X >= x0) & (X < x0 + w) & (Y >= y0) & (Y < y0 + d)
    front = (X >= x0) & (X < x0 + w) & (Y >= y0 + d) & (Y < y0 + d + h)
    east = (X >= x0 + w - 4)
    nz = rng.random(a.shape)
    tt = 4.0 + 0.6 * (nz > 0.7) - 0.6 * (nz < 0.15) + 0.5 * (Y == y0) - 1.0 * east
    V.paint(a, top, ('brass', 'sand_warm', 'sand_warm'), tt)
    stalks = 3.0 + 0.8 * ((X * 3 + Y * 5) % 4 == 0) - 0.8 * ((X + Y * 2) % 5 == 0) - 1.2 * east - 0.6 * (Y > y0 + d + h - 3)
    V.paint(a, front, ('brass', 'brass_warm', 'sand_warm'), stalks)
    for tx in (x0 + w // 4, x0 + 3 * w // 4 - 1):
        a[(Y >= y0) & (Y < y0 + d + h) & (X >= tx) & (X < tx + 2) & (top | front)] = C('timber', 2)
        a[(Y >= y0) & (Y < y0 + d) & (X == tx)] = C('timber_warm', 3)
    a[front & (Y == y0 + d)] = C('brass', 2)                     # the arris under the lit top


def hay_bales(seed=0):
    """Three bales: two side by side, one across them on top (66 x 50 texels)."""
    rng = np.random.default_rng(seed)
    p = canvas(80, 64, 40, 58)
    a = p.a
    bale(a, 6, 30, 32, 14, 12, rng)
    bale(a, 38, 30, 34, 14, 12, rng)
    bale(a, 18, 10, 36, 14, 12, rng)
    Y, X = grid(a)
    for _ in range(18):                                        # loose stalks round the foot
        x = rng.uniform(4, 76)
        V.bar(a, x, 57, x + rng.uniform(-4, 4), 57 - rng.uniform(0, 2), 0.5, 'brass', 3)
    V.finish(p)
    return p


def hay_heap(seed=0):
    """Loose hay forked out for the stock (60 x 34 texels): a low dome of tangled stalks lit on its
    upper left, its east flank and foot in shade, stalks fallen round it."""
    rng = np.random.default_rng(seed)
    p = canvas(76, 48, 38, 42)
    a = p.a
    Y, X = grid(a)
    cx, cy, rx, ry = 38, 28, 29, 15
    rough = ndi.gaussian_filter(rng.random(a.shape), 1.2)
    m = (((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2 <= 1 + 1.6 * (rough - 0.5)) & (Y < 42)
    lit = sphere_light(X, Y, cx, cy, rx, ry)
    V.paint(a, m, ('brass', 'brass_warm', 'sand_warm'), 2.9 + 1.7 * lit + 1.0 * (ndi.gaussian_filter(rng.random(a.shape), 0.7) - 0.5))
    for _ in range(170):
        x0, y0 = rng.uniform(cx - rx, cx + rx), rng.uniform(cy - ry, 41)
        ang = rng.uniform(-0.7, 0.7) + (math.pi if rng.random() < 0.5 else 0)
        L = rng.uniform(3, 7)
        s = V.seg_mask(a.shape, x0, y0, x0 + L * math.cos(ang), y0 + L * math.sin(ang), 0.45) & m
        up = lit > 0.1
        a[s & up] = C('sand_warm', 5)
        a[s & ~up] = C('brass', 2)
    for _ in range(10):
        x = rng.uniform(cx - rx - 4, cx + rx + 4)
        V.bar(a, x, 42, x + rng.uniform(-5, 5), 42 - rng.uniform(0, 2), 0.5, 'brass', 3)
    V.finish(p)
    return p


# ------------------------------------------------------------------------------------------------
# the kitchen garden's beds
# ------------------------------------------------------------------------------------------------
CROPS = {'dug': ('cabbage', 'leek', 'lettuce'), 'dug_b': ('carrot', 'cabbage', 'beans')}


def _plant(a, crop, px, cy, rng, burnt=False):
    Y, X = grid(a)
    if burnt:
        # a charred stub: a dark stalk and a curl of black leaf, ash at its foot
        a[int(cy - 4):int(cy + 1), int(px):int(px) + 1] = C('soot', 1)
        cm = ((X - px - 1.5) / 2.0) ** 2 + ((Y - cy + 4) / 1.2) ** 2 <= 1
        a[cm] = C('soot', 0 if rng.random() < 0.5 else 2)
        a[int(cy + 1), int(px - 1):int(px + 3)] = C('ash', 3)
        return
    if crop == 'cabbage':
        m = ((X - px) / 5.6) ** 2 + ((Y - cy) / 4.4) ** 2 <= 1
        V.paint(a, m, ('leaf_cool', 'leaf', 'leaf_warm'), 2.8 + 1.6 * sphere_light(X, Y, px, cy, 5.6, 4.4))
        heart = ((X - px + 0.5) / 2.8) ** 2 + ((Y - cy + 0.8) / 2.2) ** 2 <= 1
        V.paint(a, heart, ('leaf', 'leaf_warm', 'grass_warm'), 4.0 + sphere_light(X, Y, px, cy - 1, 3, 2))
        for k in range(4):                                     # the outer leaves' veins
            ang = k * math.pi / 2 + 0.6
            a[V.seg_mask(a.shape, px, cy, px + 4.5 * math.cos(ang), cy + 3.5 * math.sin(ang), 0.4) & m & ~heart] = C('leaf_cool', 2)
    elif crop == 'lettuce':
        m = ((X - px) / 4.2) ** 2 + ((Y - cy) / 3.4) ** 2 <= 1 + 0.25 * np.sin(np.arctan2(Y - cy, X - px) * 7)
        V.paint(a, m, ('leaf', 'grass_warm', 'grass_warm'), 3.2 + 1.5 * sphere_light(X, Y, px, cy, 4.2, 3.4))
    elif crop == 'leek':
        for dx, h, t in ((-1.5, 9, 3), (0.5, 11, 4), (2.0, 8, 2)):
            a[V.seg_mask(a.shape, px + dx * 0.3, cy + 1, px + dx, cy + 1 - h, 0.8)] = C('leaf_cool', t)
        a[int(cy - 1):int(cy + 2), int(px - 1):int(px + 2)] = C('plaster', 4)       # the white shank
    elif crop == 'carrot':
        for dx in (-2, 0, 2):
            a[V.seg_mask(a.shape, px, cy + 1, px + dx, cy - 6 + abs(dx), 0.6)] = C('grass', 4 if dx < 1 else 3)
        fm = ((X - px) / 3.0) ** 2 + ((Y - cy + 5) / 2.0) ** 2 <= 1
        a[fm] = C('grass_warm', 4)
        a[int(cy + 1), int(px - 1):int(px + 2)] = C('clay', 4)                      # the shoulder
    elif crop == 'beans':
        a[V.seg_mask(a.shape, px, cy + 1, px, cy - 18, 0.7)] = C('timber', 3)        # the cane
        for k in range(5):
            ly = cy - 3 - k * 3
            lm = ((X - px - (2 if k % 2 else -2)) / 2.0) ** 2 + ((Y - ly) / 1.5) ** 2 <= 1
            a[lm] = C('leaf', 4 if k % 2 == 0 else 3)
        a[int(cy - 9), int(px + 2)] = C('berry', 4)                                  # a flower
    # the plant's shade on the soil, east and down
    sh = ((X - px - 2.5) / 4.0) ** 2 + ((Y - cy - 3.5) / 1.4) ** 2 <= 1
    a[sh & (a // 8 == FI['earth'])] = C('earth_cool', 1)


def beds(kind='dug', seed=0):
    """A kitchen garden's beds in a dug patch (240 x 120 texels, ten cells by five): three soil
    ridges east to west with a path of trodden earth between them, each ridge lit on its north rim
    and its south lip a step down, crumbs of soil with clods lit on their upper left, a crop in a
    row on each; the patch's edge rough where the spade stopped short of the grass. `scorched`:
    the same ground burnt grey, the crops black stubs, ash drifted in the furrows, a few green
    shoots coming back."""
    burnt = kind == 'scorched'
    rng = np.random.default_rng(seed)
    W, H = 252, 136
    p = canvas(W, H, W // 2, H - 6)
    a = p.a
    Y, X = grid(a)
    x0, x1, y0, y1 = 8, W - 8, 10, H - 6
    nz = ndi.gaussian_filter(rng.random(a.shape), 2.5)
    nz = (nz - nz.mean()) / max(1e-6, nz.std())
    d = np.minimum.reduce([X - x0, x1 - X, Y - y0, y1 - Y])
    patch = d + 2.2 * nz > 2
    soil = ('ash', 'ash', 'stone_cool') if burnt else ('earth_cool', 'earth', 'earth_warm')
    V.paint(a, patch, soil, (2.2 if burnt else 2.4) + 0.4 * nz)
    edge = patch & ~ndi.binary_erosion(patch, iterations=2)
    a[edge] = C('earth_cool' if not burnt else 'soot', 1)
    # three ridges
    rows = 3
    pitch = (y1 - y0 - 12) / rows
    crops = CROPS.get(kind, CROPS['dug'])
    for r in range(rows):
        ry0 = y0 + 8 + r * pitch
        ry1 = ry0 + pitch - 9
        rr = 4.0
        ridge = (np.abs(X - (x0 + x1) / 2) <= (x1 - x0) / 2 - 10) & (Y >= ry0) & (Y < ry1)
        ridge &= ~((X < x0 + 14) & (Y < ry0 + rr) & ((X - x0 - 14) ** 2 + (Y - ry0 - rr) ** 2 > rr * rr))
        fr = (Y - ry0) / max(1, ry1 - ry0)
        t = 3.4 - 1.2 * fr + 0.9 * (Y < ry0 + 2) + 0.35 * nz - 0.9 * (Y >= ry1 - 3) - 0.6 * (X > x1 - 16)
        if burnt:
            V.paint(a, ridge, ('soot', 'ash', 'ash'), t - 0.4)
        else:
            V.paint(a, ridge, soil, t)
        for _ in range(int((x1 - x0) * pitch / 16)):            # clods, lit on their upper left
            cx_, cy_ = int(rng.uniform(x0 + 12, x1 - 12)), int(rng.uniform(ry0 + 2, ry1 - 3))
            if ridge[cy_, cx_]:
                a[cy_, cx_:cx_ + 2] = C('earth_warm' if not burnt else 'ash', 4)
                a[cy_ + 1, cx_ + 1:cx_ + 3] = C('earth_cool' if not burnt else 'soot', 1)
        crop = crops[r % len(crops)]
        step = {'cabbage': 15, 'lettuce': 11, 'leek': 8, 'carrot': 8, 'beans': 14}[crop]
        cy = ry0 + (ry1 - ry0) * 0.5
        n = int((x1 - x0 - 32) // step)
        for i in range(n + 1):
            px = x0 + 16 + (x1 - x0 - 32) * i / max(1, n) + rng.integers(-1, 2)
            if burnt and rng.random() < 0.35:
                continue                                       # the storm took it
            _plant(a, crop, px, cy, rng, burnt=burnt)
        if burnt:
            for _ in range(3):                                 # green coming back
                sx = int(rng.uniform(x0 + 20, x1 - 20))
                a[int(cy + 2):int(cy + 5), sx] = C('grass', 4)
                a[int(cy + 2), sx - 1:sx + 2] = C('grass_warm', 4)
    if burnt:
        ash = patch & (ndi.gaussian_filter(rng.random(a.shape), 1.5) > 0.56)
        a[ash & (a // 8 != FI['soot'])] = C('ash', 4)
    V.finish(p, line=False)
    return p


def flower_border(seed=0):
    """A cottage border (72 x 40 texels, three cells by one): a strip of dark worked soil edged
    with a row of half-sunk stones, crowded with leafy clumps each crowned with its own flowers
    (foxglove spires, daisies, lavender, marigolds), lit on the upper left."""
    rng = np.random.default_rng(seed)
    p = canvas(80, 46, 40, 40)
    a = p.a
    Y, X = grid(a)
    x0, x1, y0, y1 = 4, 76, 26, 40
    soil = (X >= x0) & (X < x1) & (Y >= y0) & (Y < y1)
    soil &= ~(((X < x0 + 3) | (X >= x1 - 3)) & ((Y < y0 + 2) | (Y >= y1 - 2)))
    V.paint(a, soil, ('earth_cool', 'earth', 'earth_warm'), 2.2 + 0.5 * np.sin(X * 0.9 + Y * 1.7) - 0.8 * (Y >= y1 - 2))
    for k, sx in enumerate(range(x0 + 1, x1 - 5, 7)):            # the edging stones along the front
        V.stone_chunk(a, sx, y1 - 5, 6, 5, 'stone', 3, rng)
    kinds = ['foxglove', 'daisy', 'lavender', 'marigold']
    for i, cx in enumerate(np.linspace(x0 + 8, x1 - 8, 6)):
        kind = kinds[(i + seed) % 4]
        cy = y0 + 4 + (i % 2) * 3
        leaf = ((X - cx) / 6.5) ** 2 + ((Y - cy) / 4.5) ** 2 <= 1
        V.paint(a, leaf, ('leaf_cool', 'leaf', 'leaf_warm'), 2.6 + 1.6 * sphere_light(X, Y, cx, cy, 6.5, 4.5))
        if kind == 'foxglove':
            for j in range(6):
                fy = cy - 5 - j * 2.2
                a[int(fy), int(cx) - 1:int(cx) + 2] = C('berry', 4 if j % 2 else 3)
                a[int(fy) + 1, int(cx)] = C('berry', 2)
            a[int(cy - 18):int(cy - 4), int(cx) + 1] = C('leaf_cool', 2)
        else:
            fam, tone, n = {'daisy': ('plaster', 5, 7), 'lavender': ('dusk', 4, 9), 'marigold': ('brass', 4, 7)}[kind]
            for _ in range(n):
                fx, fy = int(cx + rng.uniform(-5, 5)), int(cy + rng.uniform(-6, 0))
                a[fy:fy + 2, fx:fx + 2] = C(fam, tone)
                a[fy, fx] = C(fam, 5)
                if kind == 'daisy':
                    a[fy + 1, fx + 1] = C('brass', 4)
    V.finish(p)
    return p


# ------------------------------------------------------------------------------------------------
# pieces
# ------------------------------------------------------------------------------------------------
def _fp(cols, rows):
    """Footprint cells (offsets from the foot cell) for a piece cols wide, rows deep."""
    xs = range(-(cols // 2), cols - cols // 2)
    return [[c, -r] for r in range(rows, 0, -1) for c in xs]


def strip(frames):
    w, h = frames[0].W, frames[0].H
    s = np.full((h, w * len(frames)), -1, np.int32)
    for k, f in enumerate(frames):
        s[:, k * w:(k + 1) * w] = f.a
    return s


def _base(pid, name, png_still, foot, size, purpose, role, *, cells, fp, collision, requires=(), forbids=(),
          enclosure=None, anim=None, shadow=(10, 3), blocks=True, biomes=('village', 'valley'), size_class=None,
          eastward=None, note=''):
    piece = {
        'schema': 'napattack.piece/1', 'id': pid, 'name': name, 'kind': 'prop', 'biomes': list(biomes), 'version': 1,
        'variants': [{'id': os.path.splitext(os.path.basename(png_still))[0], 'weight': 1.0, 'png': RES + os.path.basename(png_still),
                      'foot': list(foot)}],
        'approval': {'state': 'candidate', 'by': None, 'at': None,
                     'standard': "art-style.md (Eastward's level of detail), placement-logic.md", 'note': note},
        'geometry': {'size_px': list(size), 'size_cells': list(cells), 'z_sort': 'foot', 'height_px': size[1] - (size[1] - foot[1]),
                     'collision': collision, 'foot': list(foot), 'footprint': fp},
        'placement': {'snap': 'cell', 'purpose': purpose, 'role': role,
                      **({'requires': list(requires)} if requires else {}), **({'forbids': list(forbids)} if forbids else {}),
                      **({'enclosure': enclosure} if enclosure else {})},
        'rendering': {'cast_shadow': {'shape': 'ellipse', 'size': list(shadow), 'dir': [1, 1]} if shadow else {'shape': 'none'},
                      'contact_ao': True, **({'animations': [anim]} if anim else {})},
        'function': {}, 'story': {'owner': None},
        'gameplay': {'blocks_move': blocks, 'blocks_shots': False},
        'audit': {'size_class': size_class, 'eastward_ref': eastward,
                  'painter': {'module': 'scripts.art.kit.farm', 'fn': pid, 'args': {}},
                  'seeded_from': 'scripts/art/kit/farm.py', 'todo': []},
    }
    return piece


OFF_ROUTE = {'rel': 'on', 'what': 'route'}
OFF_WATER = {'rel': 'on', 'what': 'water'}


def _rel(rel, what, cells=None, note=None):
    r = {'rel': rel, 'what': what}
    if cells is not None:
        r['cells'] = cells
    if note:
        r['note'] = note
    return r


def animals():
    """(piece id, frames, fps, piece kwargs) for every animal."""
    out = []
    for kind, (_b, _w, _t, face, _s) in HENS.items():
        frames = [hen(kind, pose, seed=11) for pose in (HEN_FRAMES[k:] + HEN_FRAMES[:k] if False else HEN_FRAMES)]
        # each hen keeps her own rhythm: the loop starts at a different beat
        shift = {'white': 0, 'brown': 3, 'speckled': 5}[kind]
        frames = frames[shift:] + frames[:shift]
        out.append(('farm_hen_%s' % kind, frames, 4.0, dict(
            name='Hen, %s' % kind, purpose='live', role='stock', cells=(1, 1), fp=[[0, -1]],
            collision={'shape': 'none'}, blocks=False, shadow=(6, 2),
            requires=[_rel('within', 'coop', 4, 'hens live in a run with their coop (placement-logic: keep animals in)'),
                      _rel('within', 'boundary', 3, 'inside the run\'s fence')],
            forbids=[OFF_ROUTE, OFF_WATER], enclosure={'holds': ['chickens'], 'as': 'contents'},
            eastward='17: the farm\'s animals, each a readable mass with its own pose', size_class='hen (size-guide 2)',
            note='A hen pecking in her run; 8 idle frames at 4 fps.')))
    for pose, face, seed in (('stand', -1, 3), ('graze', 1, 5), ('lie', -1, 7)):
        frames = [sheep(pose, f, face, seed) for f in SHEEP_FRAMES[pose]]
        out.append(('farm_sheep' + ('' if pose == 'stand' else '_' + pose), frames, 3.0, dict(
            name='Sheep, ' + {'stand': 'standing', 'graze': 'grazing', 'lie': 'lying'}[pose], purpose='live', role='stock',
            cells=(3, 1), fp=_fp(2, 1), collision={'shape': 'rect', 'rect': [-9.0, -3.0, 18, 3]}, shadow=(18, 4),
            requires=[_rel('within', 'trough', 9, 'a fold holds its trough (placement-logic: keep animals in)'),
                      _rel('within', 'boundary', 5, 'inside the fold\'s hurdles')],
            forbids=[OFF_ROUTE, OFF_WATER], enclosure={'holds': ['sheep'], 'as': 'contents'},
            eastward='17: cows 0.9 A and pigs 0.55 A, chunky with a dark outline', size_class='sheep (size-guide 2)',
            note='A ewe in her fold; 8 idle frames at 3 fps.')))
    return out


def statics():
    """(piece id, picture, piece kwargs) for the coop, the shelter and the hay."""
    return [
        ('farm_coop', coop(seed=21), dict(
            name='Hen ark', purpose='live', role='coop', cells=(3, 2), fp=_fp(2, 1),
            collision={'shape': 'rect', 'rect': [-9.0, -5.0, 18, 5]}, shadow=(20, 4),
            requires=[_rel('within', 'boundary', 2, 'against the run\'s fence, in its back corner'),
                      _rel('near', 'stock', 4, 'its hens about it')],
            forbids=[OFF_ROUTE, OFF_WATER], enclosure={'holds': ['chickens'], 'as': 'needs'},
            size_class='hen house (size-guide 4: "shed, hen house"; this is the small ark a 3 to 4 cell run takes)',
            eastward='17: the barn\'s boarded walls, knots and nail heads', note='The hens\' house in their run.')),
        ('farm_shelter', shelter(seed=31), dict(
            name='Field shelter', purpose='live', role='shelter', cells=(5, 3), fp=_fp(4, 2),
            collision={'shape': 'rect', 'rect': [-16.0, -14.0, 32, 10]}, shadow=(34, 5),
            requires=[_rel('within', 'boundary', 2, 'its back to the fold\'s hurdles'), _rel('near', 'stock', 8, 'the flock it shelters')],
            forbids=[OFF_ROUTE, OFF_WATER], enclosure={'holds': ['sheep', 'horses'], 'as': 'needs'},
            size_class='field shelter (size-guide 4: shed row, the open front of a stable)',
            eastward='17: the barn\'s timber, its eave\'s shade', note='Shelter for the flock, its open side south.')),
        ('garden_flower_border', flower_border(seed=61), dict(
            name='Flower border', purpose='care', role='planter', cells=(3, 1), fp=_fp(3, 1),
            collision={'shape': 'none'}, blocks=False, shadow=None,
            requires=[_rel('within', 'boundary', 3, 'inside a front garden\'s fence or along a house\'s wall'),
                      _rel('near', 'house', 6, 'a home\'s garden')],
            forbids=[OFF_ROUTE, OFF_WATER], enclosure={'holds': ['flowers'], 'as': 'contents'},
            size_class='flower (size-guide: heads 4 to 8 art px, clumps 0.2 to 0.4 m)',
            eastward='12 and 13: flower clumps, heads a touch big', note='A cottage border in a front garden.')),
    ]


def build(write=True, force=False):
    out = {}
    pieces = []
    for pid, frames, fps, kw in animals():
        still = frames[0]
        sp = os.path.join(ART, pid + '.png')
        st = os.path.join(ART, pid + '_idle.png')
        out[sp] = to_rgba(still.a)
        out[st] = to_rgba(strip(frames))
        anim = {'clip': 'idle', 'loop': True, 'frames': len(frames), 'fps': fps, 'strip': RES + pid + '_idle.png',
                'frame_px': [still.W, still.H], 'reduced_motion': 'hold:0', 'on_screen_only': True}
        pieces.append(_base(pid, kw.pop('name'), sp, (still.ax, still.ay), (still.W, still.H), kw.pop('purpose'), kw.pop('role'),
                            anim=anim, **kw))
    for pid, pic, kw in statics():
        sp = os.path.join(ART, pid + '.png')
        out[sp] = to_rgba(pic.a)
        pieces.append(_base(pid, kw.pop('name'), sp, (pic.ax, pic.ay), (pic.W, pic.H), kw.pop('purpose'), kw.pop('role'), **kw))
    # the redraws of the Crossroads pieces: new pictures for the existing pieces (their story,
    # gating and stages kept)
    redraw = {
        'crossroads_hay': [('hay_bales', hay_bales(seed=41)), ('hay_heap', hay_heap(seed=43))],
        'crossroads_beds_dug': [('beds_dug', beds('dug', seed=51)), ('beds_dug_b', beds('dug_b', seed=53))],
        'crossroads_beds_scorched': [('beds_scorched', beds('scorched', seed=51))],
    }
    for pid, vs in redraw.items():
        for vid, pic in vs:
            out[os.path.join(ART, vid + '.png')] = to_rgba(pic.a)
    if write:
        os.makedirs(ART, exist_ok=True)
        for p, a in out.items():
            Image.fromarray(a, 'RGBA').save(p, optimize=True)
        for pc in pieces:
            path = os.path.join(PIECES, 'prop', pc['id'] + '.json')
            if force or not os.path.exists(path):
                json.dump(pc, open(path, 'w'), indent=1)
                open(path, 'a').write('\n')
        for pid, vs in redraw.items():
            path = os.path.join(PIECES, 'prop', pid + '.json')
            pc = json.load(open(path))
            new = [{'id': vid, 'weight': 1.0, 'png': RES + vid + '.png', 'foot': [pic.ax, pic.ay]} for vid, pic in vs]
            if pc['variants'] != new:
                pc['variants'] = new
                g = pc['geometry']
                g['size_px'] = [max(p.W for _v, p in vs), max(p.H for _v, p in vs)]
                g['size_cells'] = [math.ceil(v / 24) for v in g['size_px']]
                g['foot'] = [vs[0][1].ax, vs[0][1].ay]
                pc['version'] = pc.get('version', 1) + 1
                json.dump(pc, open(path, 'w'), indent=1)
                open(path, 'a').write('\n')
        existing_metadata()
    return out


# What the existing Crossroads pieces are to an enclosure; the source fields Claude reviewed and
# authored over the seeded source (audit.overrides: seed_props keeps them on a refresh); the
# retired straight fence.
EXISTING = {
    'crossroads_beds_dug': {'enclosure': {'holds': ['crops'], 'as': 'contents'}},
    'crossroads_beds_scorched': {'enclosure': {'holds': ['crops'], 'as': 'contents'}},
    'crossroads_trough': {'enclosure': {'holds': ['sheep', 'horses'], 'as': 'needs'}},
}
# The size-guide review of the solid boxes restored in #417 (3 Nov): boxes that disagreed with the
# art, in world px from the foot (docs/vision/placement-audit.md, "Solid boxes").
REVIEWED_BOXES = {
    'crossroads_lantern_lit': [-7.0, -5.0, 14, 5],      # was 10 x 22 deep up the post; now the plinth
    'crossroads_lantern_dark': [-7.0, -5.0, 14, 5],
    'crossroads_boulder': [-11.0, -6.0, 22, 6],         # was 12 wide under a 25 wide cluster
    'crossroads_bush': [-13.0, -6.0, 26, 6],            # was 16 wide under a 31 wide bush (woodland bushes: 85 %)
    'crossroads_well_choked': [-10.0, -16.0, 20, 16],   # was 24 x 20 round a 19 wide ring; now the well's own box
}
REDRAWN = ('crossroads_beds_dug', 'crossroads_beds_scorched', 'crossroads_hay')


def _save(path, pc):
    json.dump(pc, open(path, 'w'), indent=1)
    open(path, 'a').write('\n')


def _override(pc, field):
    ov = pc.setdefault('audit', {}).setdefault('overrides', [])
    if field not in ov:
        ov.append(field)
        ov.sort()


def existing_metadata():
    from scripts.art.kit import seed_props as SP
    for pid in set(EXISTING) | set(REVIEWED_BOXES) | set(REDRAWN) | {'crossroads_fence'}:
        path = os.path.join(PIECES, 'prop', pid + '.json')
        pc = json.load(open(path))
        before = json.dumps(pc, sort_keys=True)
        pc.setdefault('placement', {}).update(EXISTING.get(pid, {}))
        if pid in REVIEWED_BOXES:
            pc['geometry']['collision'] = {'rect': REVIEWED_BOXES[pid], 'shape': 'rect'}
            pc['geometry']['footprint'] = SP.footprint(REVIEWED_BOXES[pid])
            _override(pc, 'collision')
        if pid in REDRAWN:
            _override(pc, 'variants')
        if pid == 'crossroads_fence':
            pc['approval'].update(state='retired', note='Retired 3 Nov: a straight post-and-rail segment cannot close an enclosure. '
                                  'Use the fence cells fence_wattle_* and fence_picket_* (scripts/art/kit/fences.py).')
            _override(pc, 'approval')
        if json.dumps(pc, sort_keys=True) != before:
            _save(path, pc)


def check() -> int:
    bad = []
    for p, a in build(write=False).items():
        if not os.path.exists(p) or not np.array_equal(np.asarray(Image.open(p).convert('RGBA')), a):
            bad.append(os.path.relpath(p, ROOT))
    if bad:
        print('farm: stale pictures %s (run python3 -m scripts.art.kit.farm)' % ', '.join(bad[:6]))
        return 1
    print('farm: pictures current')
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--force', action='store_true')
    a = ap.parse_args(argv)
    if a.check:
        return check()
    print('farm: %d pictures' % len(build(force=a.force)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
