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
- the hen ark, 48 wide and 47 tall, on legs, with a pop hole and a ramp;
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


def rpaint(a, m, sets, t, mix):
    """Paint mask m with float tones t (0..5) in one of several (cool, body, warm) triples chosen
    per pixel by mix (0..1): hue shifts across a material (a fleece's cream and grey, a bale's
    gold and straw), so a surface is more than one ramp."""
    t = np.clip(np.round(np.broadcast_to(np.asarray(t, float), m.shape)), 0, 5).astype(int)
    mix = np.broadcast_to(np.asarray(mix, float), m.shape)
    k = np.clip((mix * len(sets)).astype(int), 0, len(sets) - 1)
    fam = np.zeros(m.shape, int)
    for i, (cool, body, warm) in enumerate(sets):
        f = np.where(t >= 4, FI[warm], np.where(t <= 1, FI[cool], FI[body]))
        fam = np.where(k == i, f, fam)
    a[m] = (fam * 8 + t)[m]


def noise(shape, rng, sigma=1.0):
    n = ndi.gaussian_filter(rng.random(shape), sigma)
    return (n - n.min()) / max(1e-6, n.max() - n.min())


# ------------------------------------------------------------------------------------------------
# hens
# ------------------------------------------------------------------------------------------------
HENS = {
    # kind: body sets, wing sets, tail sets, face (1 east, -1 west), speckle family
    'white': ([('stone_cool', 'plaster_warm', 'plaster'), ('sand_cool', 'sand', 'snow_warm')],
              [('stone_warm', 'plaster_warm', 'plaster')], [('stone_cool', 'plaster_warm', 'snow_warm')], -1, None),
    'brown': ([('clay_cool', 'fox', 'brass_warm'), ('crag_cool', 'crag_warm', 'fox')],
              [('clay_cool', 'clay', 'fox')], [('soot', 'soot', 'sky_cool')], -1, None),
    'speckled': ([('slate_cool', 'stone', 'stone_warm'), ('stone_cool', 'ashlar', 'plaster_warm')],
                 [('stone_cool', 'stone', 'stone_warm')], [('soot', 'slate_cool', 'slate')], 1, 'soot'),
}
HEN_FRAMES = ['up', 'up', 'look', 'up', 'peck', 'peck2', 'peck', 'up']


def hen(kind, pose='up', seed=0):
    """A hen (about 22 x 26 texels): a round body lit on its upper left, its breast pale and its
    belly shaded; the folded wing a separate shape with a dark edge and two rows of feathers; the
    tail a fan of separate feathers cocked up behind, the sickles darker with a sheen; the head
    forward with a red comb lit on its crown and a wattle, a yellow beak, an amber eye with a glint;
    scaled yellow legs. `pose`: up, look (head turned back), peck, peck2 (head down at the ground)."""
    body_s, wing_s, tail_s, face, speck = HENS[kind]
    rng = np.random.default_rng(seed + 7)
    p = canvas(34, 31, 17, 28)
    a = p.a
    Y, X = grid(a)
    cx, yb = 17 - face * 1, 28
    nz = noise(a.shape, rng, 0.8)
    for dx in (-2, 2):                                          # legs: scaled, a toe forward
        x = int(cx + dx)
        a[yb - 6:yb - 1, x] = C('brass', 3)
        a[yb - 6:yb - 1:2, x] = C('brass', 4)
        a[yb - 1, x - 1:x + 2] = C('brass', 2)
        a[yb - 1, x + face * 2] = C('brass', 2)
    peck = pose in ('peck', 'peck2')
    tilt = 1.0 if peck else 0.0
    by = yb - 12 + tilt
    body = ((X - cx) / 8.6) ** 2 + ((Y - by) / 6.6) ** 2 <= 1
    lit = sphere_light(X, Y, cx, by, 8.6, 6.6)
    # the tail: four feathers fanned up and back, each its own lit blade with a dark edge
    tail = np.zeros(a.shape, bool)
    blades = []
    for i, (ang, L) in enumerate(((1.75, 9.5), (2.15, 10.5), (2.55, 9.5), (2.95, 7.5))):
        bx0, by0 = cx - face * 5.5, by - 1.0 + tilt
        tip = (bx0 - face * L * abs(math.cos(ang)), by0 - L * math.sin(ang))
        m = V.seg_mask(a.shape, bx0, by0, tip[0], tip[1], 1.45) & ~body
        tail |= m
        blades.append(m)
    rpaint(a, tail, tail_s, 3.2 + 1.3 * sphere_light(X, Y, cx - face * 8, by - 6, 6, 6), nz)
    for i, m in enumerate(blades):                              # each feather's shaded edge, so they separate
        if i % 2:
            a[m & ~ndi.binary_erosion(m) & (Y > by - 12)] = C(tail_s[0][1], 2)
    # the body
    rpaint(a, body, body_s, 2.9 + 1.7 * lit, nz)
    a[body & (Y > by + 4.0) & ~((X - cx) * face > 3)] = C(body_s[0][0], 2)        # the belly in shade
    a[body & (Y > by + 5.4)] = C(body_s[0][0], 1)
    # the breast, pale and catching the light at the front
    br = body & (((X - (cx + face * 5.0)) / 3.8) ** 2 + ((Y - (by - 0.5)) / 4.0) ** 2 <= 1)
    rpaint(a, br, body_s, 3.6 + 1.2 * lit, nz)
    # the wing: its own shape over the flank, a dark line along its top edge, two feather rows
    wx, wy = cx - face * 1.2, by + 0.6
    wing = (((X - wx) / 5.8) ** 2 + ((Y - wy) / 3.4) ** 2 <= 1) & body
    rpaint(a, wing, wing_s, 3.0 + 1.0 * sphere_light(X, Y, wx, wy - 2, 6, 4), nz)
    edge = wing & ~ndi.binary_erosion(wing) & (Y < wy + 1)
    a[edge] = C(wing_s[0][0], 2)
    sc = wing & (np.abs(Y - wy - 1.4 - 0.8 * np.cos((X - wx) * 1.4)) < 0.5)        # the flight feathers' row
    a[sc] = C(wing_s[0][0], 2)
    a[wing & (Y > wy + 2.2)] = C(wing_s[0][0], 1)                                  # the wing tips, tucked
    a[edge & (X * face < wx * face)] = C(wing_s[0][2], 4)                          # its lit top edge
    if speck:
        sp = body & (rng.random(a.shape) < 0.10) & ~wing
        a[sp] = C(speck, 2)
        a[body & (rng.random(a.shape) < 0.05) & ~wing] = C('plaster', 5)
    # the head
    if pose == 'look':
        hx, hy = cx + face * 4.2, by - 7.4
    elif peck:
        hx, hy = cx + face * 9.0, yb - (4.5 if pose == 'peck' else 3.0)
    else:
        hx, hy = cx + face * 6.8, by - 7.0
    neck = V.seg_mask(a.shape, cx + face * 3.6, by - 2.5, hx, hy + 1, 2.7)
    head = ((X - hx) / 3.2) ** 2 + ((Y - hy) / 3.1) ** 2 <= 1
    hm = (neck | head) & ~(body & (Y > by - 1))
    rpaint(a, hm, body_s, 3.5 + 1.4 * sphere_light(X, Y, hx, hy, 3.5, 3.5), nz)
    fwd = face if pose != 'look' else -face
    for k, dx in enumerate((-1.7, 0.0, 1.7)):                   # the comb, lit on its crown
        cm = ((X - (hx + dx * fwd * 0.8 - fwd * 0.4)) / 1.15) ** 2 + ((Y - (hy - 3.3 + 0.3 * abs(dx))) / 1.5) ** 2 <= 1
        a[cm] = C('berry', 3)
        a[cm & (Y < hy - 3.6 + 0.3 * abs(dx))] = C('berry', 5 if k == 1 else 4)
    wm = ((X - (hx + fwd * 1.6)) / 1.0) ** 2 + ((Y - (hy + 2.9)) / 1.7) ** 2 <= 1
    a[wm] = C('berry', 3)
    a[wm & (X * fwd < (hx + fwd * 1.6) * fwd)] = C('berry', 4)
    a[wm & (Y > hy + 3.8)] = C('berry_cool', 2)
    bx = int(round(hx + fwd * 3.0))
    by_ = int(round(hy))
    a[by_ - 1, min(bx, bx + fwd * 2):max(bx, bx + fwd * 2) + 1] = C('brass', 5)
    a[by_, min(bx, bx + fwd * 2):max(bx, bx + fwd * 2) + 1] = C('brass', 3)
    ex = int(round(hx + fwd * 0.9))
    a[by_ - 1, ex] = C('brass', 4)
    a[by_ - 1, ex + (1 if fwd > 0 else -1) * 0] = C('soot', 0)
    a[by_ - 2, ex] = C('plaster', 5)
    if pose == 'peck2':
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
WOOL = [('sand_cool', 'plaster_warm', 'plaster'), ('sand_cool', 'sand', 'snow_warm'), ('stone_warm', 'plaster_warm', 'snow_warm'),
        ('stone_warm', 'sand', 'sand_warm')]            # the last: wool yellowed with lanolin


def sheep(pose='stand', frame='a', face=1, seed=0):
    """A ewe (about 55 x 38 texels standing): a fleece built of clustered curls, each a small dome
    lit on its upper left with a cream highlight and a grey crease under it, the mass shading to a
    cool belly; a black face with a grey muzzle, an amber eye with a glint, ears out with a pink
    lining, a topknot of wool; legs black with a wool-covered thigh, a knee and a hoof (the far pair
    a step darker). Grazing her head is down at the grass; lying her legs are folded under."""
    rng = np.random.default_rng(seed)
    p = canvas(84, 56, 42, 52)
    a = p.a
    Y, X = grid(a)
    cx, yb = 42 - face * 3, 52
    lie = pose == 'lie'
    breathe = 1 if (lie and frame == 'out') else 0
    by = yb - (12 if lie else 21)
    rx, ry = 22.5, (12.5 + breathe * 0.5 if lie else 13.0)
    nz = noise(a.shape, rng, 1.0)
    if not lie:
        for lx, far in ((-12.5, True), (8.5, True), (-9.5, False), (12.0, False)):
            x = int(round(cx + face * lx))
            t = 1 if far else 2
            knee = yb - 6
            a[int(by + 6):knee, x:x + 3] = C('soot', t)                 # the thigh under the wool
            a[int(by + 6):knee, x] = C('soot', t + 2)
            a[knee:knee + 1, x - 1:x + 3] = C('soot', t + 1)            # the knee, a knob lit on its top
            a[knee, x - 1] = C('soot', t + 3)
            a[knee + 1:yb - 1, x:x + 2] = C('soot', t)                  # the shank
            a[knee + 1:yb - 1, x] = C('soot', t + 2)
            a[yb - 2:yb, x - (1 if face < 0 else 0):x + 3] = C('soot', 0)   # the hoof
            a[yb - 2, x] = C('stone_cool', 1)
    fleece = ((X - cx) / rx) ** 2 + ((Y - by) / ry) ** 2 <= 1
    t = 2.6 + 1.7 * sphere_light(X, Y, cx, by, rx, ry)
    mix = np.zeros(a.shape)
    crease = np.zeros(a.shape, bool)
    hi = np.zeros(a.shape, bool)
    curls = rng.uniform(-1, 1, (150, 2))
    curls = curls[(curls ** 2).sum(1) <= 1.08]
    cm_all = np.zeros(a.shape, bool)
    for ux, uy in sorted(curls.tolist(), key=lambda c: c[1]):
        px, py = cx + ux * (rx - 2.0), by + uy * (ry - 1.5)
        r1, r2 = rng.uniform(2.4, 3.3), rng.uniform(1.9, 2.6)
        m = ((X - px) / r1) ** 2 + ((Y - py) / r2) ** 2 <= 1
        inner = ((X - px + 0.7) / (r1 - 0.9)) ** 2 + ((Y - py + 0.7) / (r2 - 0.8)) ** 2 <= 1
        crease = (crease & ~m) | (m & ~inner & ((X - px) + (Y - py) > 0.3))
        hi = (hi & ~m) | (m & ((X - px + 1.1) ** 2 + (Y - py + 1.0) ** 2 <= 0.9))
        cm_all |= m
        mix = np.where(m, rng.random() * 0.999, mix)                   # each curl its own cream
        t = np.where(m, 2.2 + 1.25 * sphere_light(X, Y, cx, by, rx, ry) + 1.5 * sphere_light(X, Y, px, py, r1, r2), t)
    fleece = (fleece | cm_all) & (Y < yb - (0 if lie else 7))
    rpaint(a, fleece, WOOL, t, mix)
    shade = sphere_light(X, Y, cx, by, rx, ry)
    # the creases between curls: deeper where the fleece turns from the light, each curl's own hue
    cr = crease & fleece
    ct = np.where(shade < 0.15, 1, 2) + (shade > 0.55)
    cf = np.where(mix < 0.25, FI['sand_cool'], np.where(mix < 0.5, FI['stone_warm'], np.where(mix < 0.75, FI['stone_cool'], FI['sand'])))
    a[cr] = (cf * 8 + ct)[cr]
    hm_ = hi & fleece & (shade > -0.2)
    hf = np.where(mix < 0.34, FI['snow_warm'], np.where(mix < 0.67, FI['plaster'], FI['sand_warm']))
    a[hm_] = (hf * 8 + 5)[hm_]
    if lie:
        # the forelegs folded under her chest, a black knee and hoof showing, the wool pressed into
        # the grass along her underside
        for k, lx in enumerate((10.0, 15.5)):
            kx = int(round(cx + face * lx))
            ky = yb - 3
            a[ky - 1:ky + 1, min(kx, kx + face * 5):max(kx, kx + face * 5)] = C('soot', 1 + k)
            a[ky - 1, min(kx, kx + face * 5):max(kx, kx + face * 5)] = C('soot', 3)
            a[ky:ky + 1, kx + face * 5 - (1 if face > 0 else 0)] = C('soot', 0)
        a[fleece & (Y >= yb - 2)] = C('stone_warm', 1)
    belly = fleece & (Y > by + ry * 0.55)
    rpaint(a, belly, [('stone_warm', 'sand_cool', 'sand'), ('stone_cool', 'stone_warm', 'sand_cool')], 1.6 + 0.9 * (nz > 0.55), mix)
    # the head
    if pose == 'graze':
        chew = 1 if frame == 'chew' else 0
        hx, hy = cx + face * (rx + 0.5), yb - 7 + chew
        neck = V.seg_mask(a.shape, cx + face * (rx - 5), by - 1, hx, hy - 2, 4.2)
        rpaint(a, neck & ~fleece, WOOL, 2.8 + sphere_light(X, Y, hx, by, 5, 5), mix)
    elif lie:
        hx, hy = cx + face * (rx - 1.0), by - 6
    else:
        hx, hy = cx + face * (rx + 0.5), by - 8
    hface = face if frame != 'turn' else 0
    head = ((X - hx - hface * 1.2) / 4.6) ** 2 + ((Y - hy) / 5.6) ** 2 <= 1
    muzzle = ((X - hx - hface * 3.8) / 2.8) ** 2 + ((Y - hy - 2.5) / 2.8) ** 2 <= 1
    hm = head | muzzle
    rpaint(a, hm, [('soot', 'soot', 'iron')], 1.5 + 1.8 * sphere_light(X, Y, hx, hy, 5, 6), 0)
    a[muzzle & (Y > hy + 3.2)] = C('stone_cool', 1)                       # the grey muzzle
    nx_ = int(round(hx + hface * 5.6))
    a[int(round(hy + 2.4)), nx_] = C('soot', 0)                           # a nostril
    ey, ex = int(round(hy - 1.5)), int(round(hx + hface * 2.0))
    a[ey, ex] = C('brass', 4)                                             # the eye, amber, with a glint
    a[ey, ex + (1 if hface >= 0 else -1)] = C('soot', 0)
    a[ey - 1, ex] = C('plaster', 5)
    flick = frame == 'ear'
    for side in (-1, 1):
        ex0 = hx - face * 2.0 + side * 3.0
        ey0 = hy - 4.5 - (1.5 if (flick and side > 0) else 0)
        ear = ((X - (ex0 + side * 2.6)) / 3.0) ** 2 + ((Y - ey0) / 1.4) ** 2 <= 1
        a[ear & ~hm] = C('soot', 2 if side < 0 else 1)
        lining = ear & ~hm & ((X - (ex0 + side * 2.6)) ** 2 / 4.0 + (Y - ey0 - 0.3) ** 2 <= 0.5)
        a[lining] = C('berry_cool', 2)
    tk = ((X - (hx - face * 1.5)) / 3.0) ** 2 + ((Y - (hy - 5.5)) / 2.0) ** 2 <= 1
    rpaint(a, tk & ~hm, WOOL, 4.0 + sphere_light(X, Y, hx, hy - 6, 3, 2), mix)
    V.finish(p)
    return p


# ------------------------------------------------------------------------------------------------
# the coop and the shelter
# ------------------------------------------------------------------------------------------------
def coop(seed=0):
    """A hen ark (48 x 47 texels): a boarded house on four legs, its gabled shingle roof with a
    lit west slope over the south gable, a pop hole with a ramp down to the run."""
    rng = np.random.default_rng(seed)
    p = canvas(66, 56, 32, 50)
    a = p.a
    Y, X = grid(a)
    x0, x1, yb = 12, 52, 50
    wt, wb = 21, 42                     # the south gable's wall, top and foot
    nzc = noise(a.shape, rng, 1.5)
    # legs
    for lx in (x0 + 2, x1 - 6):
        V.prism(a, lx, wb - 2, lx + 4, yb, 1, 'timber', 2, side=1)
    for lx in (x0 + 8, x1 - 12):        # the far legs, in shade
        V.prism(a, lx, wb - 2, lx + 3, yb - 4, 1, 'timber_cool', 1, side=1)
    # the gable wall: vertical boards, lit at their west edge, a darker east end
    wall = (X >= x0) & (X < x1) & (Y >= wt) & (Y < wb)
    board = ((X - x0) // 6).astype(int)
    t = 3.0 + 0.4 * np.sin(board * 2.1) - 1.0 * (((X - x0) % 6) == 5) + 0.8 * (((X - x0) % 6) == 0) - 0.9 * (X > x1 - 9)
    # weathered boards: some silvered, some still brown, a stain of damp at the foot
    rpaint(a, wall, [('timber_cool', 'timber', 'timber_warm'), ('earth_cool', 'earth', 'earth_warm'), ('timber_cool', 'timber_warm', 'sand_warm')],
           t - 0.5 * (Y > wb - 4), ((board * 7) % 3) / 3.0 + 0.05)
    for k in range(12):                 # knots and nail heads
        kx, ky = int(rng.integers(x0 + 2, x1 - 2)), int(rng.integers(wt + 3, wb - 2))
        a[ky, kx] = C('timber_cool', 1)
    for bx in range(x0 + 2, x1, 6):
        a[wt + 3, bx] = C('iron', 2)
        a[wb - 3, bx] = C('iron', 2)
    a[wb - 1, x0:x1] = C('timber_cool', 0)
    # the gable's triangle and the roof: two shingle slopes meeting at the ridge over the gable
    ridge_y, eave_y, ov = 3, wt + 2, 3
    rx0, rx1 = x0 - ov, x1 + ov
    mid = (rx0 + rx1) / 2
    roof = (Y >= ridge_y) & (Y < eave_y) & (np.abs(X - mid) <= (Y - ridge_y) * (rx1 - mid) / (eave_y - ridge_y) + 1)
    west = roof & (X < mid)
    row = ((Y - ridge_y) // 4).astype(int)
    shing = ((X + 3 * (row % 2)) // 6).astype(int)
    tr = np.where(west, 3.4, 2.1) + 0.45 * np.sin(shing * 1.7 + row) - 1.6 * (((Y - ridge_y) % 4) == 3) \
        + 0.9 * (((Y - ridge_y) % 4) == 0)
    tr = tr - 1.0 * ((((X + 3 * (row % 2)) % 6) == 5) & ((Y - ridge_y) % 4 < 3))
    rpaint(a, roof, [('slate_cool', 'slate', 'slate_warm'), ('stone_cool', 'slate', 'slate_warm')], tr, nzc)
    moss = roof & (nzc > 0.72) & (((Y - ridge_y) % 4) == 3)
    a[moss] = C('leaf_cool', 2)
    a[roof & (np.abs(X - mid) < 1.0)] = C('slate_warm', 5)            # the ridge
    # the barge boards along the gable's slopes
    for side in (-1, 1):
        V.bar(a, mid, ridge_y + 1, mid + side * (rx1 - mid), eave_y, 1.2, 'timber_warm' if side < 0 else 'timber', 4 if side < 0 else 2)
    # the eave's shadow on the wall
    a[(Y >= eave_y) & (Y < eave_y + 2) & wall] = C('timber_cool', 1)
    # the pop hole and its ramp, a perch peg
    hx = int(mid - 8)
    a[wb - 11:wb - 2, hx - 3:hx + 4] = C('soot', 0)
    a[wb - 11, hx - 3:hx + 4] = C('timber_warm', 4)
    a[wb - 11:wb - 2, hx + 3] = C('timber_cool', 1)
    ramp = V.seg_mask(a.shape, hx, wb - 1, hx - 5, yb - 1, 2.2)
    V.paint(a, ramp, ('timber_cool', 'timber', 'timber_warm'), 3.6 - 0.4 * ((Y - wb) > 4))
    for k in range(3):
        ty = int(wb + 2 + k * 3)
        tx = int(hx - 2 * (ty - wb) / (yb - wb) * 3)
        a[ty, tx - 3:tx + 2] = C('timber_cool', 1)
    # straw poking from the pop hole
    for k in range(4):
        a[wb - 3, hx - 3 + 2 * k] = C('brass', 4)
    V.finish(p)
    return p


def shelter(seed=0):
    """A field shelter for the flock (108 x 92 texels): a single-pitch roof of boards on two square
    front posts falling to the south, the posts drawn with a lit west face and a shaded east side
    and standing in the ground with a dark contact line; inside, the boarded back wall in deep
    shade with a hay rack on it, straw on the floor that spills out past the front edge onto the
    grass, the floor darkest at the back under the roof."""
    rng = np.random.default_rng(seed)
    p = canvas(122, 98, 58, 86)
    a = p.a
    Y, X = grid(a)
    nz = noise(a.shape, rng, 1.2)
    x0, x1, yb = 10, 108, 86
    back_foot = yb - 26
    inside = (X >= x0) & (X < x1) & (Y >= back_foot - 34) & (Y < yb)
    wall = inside & (Y < back_foot)
    plank = ((X - x0) // 8)
    rpaint(a, wall, [('earth_cool', 'timber_cool', 'timber'), ('soot', 'earth_cool', 'earth')],
           1.6 + 0.7 * (((X - x0) % 8) == 0) - 0.6 * (((X - x0) % 8) == 7) - 0.5 * (Y > back_foot - 6) + 0.25 * np.sin(plank * 2.3)
           + 1.2 * (nz - 0.5),
           (plank % 2) * 0.6)
    floor = inside & (Y >= back_foot)
    depth = (Y - back_foot) / (yb - back_foot)                     # 0 at the back .. 1 at the front
    rpaint(a, floor, [('soot', 'earth_cool', 'earth'), ('earth_cool', 'earth', 'earth_warm')], 1.0 + 1.6 * depth + 0.4 * (nz - 0.5), depth)
    # straw: strands across the floor, in shade at the back and lit at the open front, a few
    # spilling past the front edge onto the grass
    for _ in range(260):
        sx = rng.uniform(x0 + 2, x1 - 2)
        sy = rng.uniform(back_foot + 1, yb + 5)
        ang = rng.uniform(-0.7, 0.7)
        L = rng.uniform(2, 6)
        m = V.seg_mask(a.shape, sx, sy, sx + L * math.cos(ang), sy + L * math.sin(ang), 0.5)
        m &= (floor | ((Y >= yb) & (Y < yb + 6) & (X > x0 + 4) & (X < x1 - 4)))
        d_ = (sy - back_foot) / (yb - back_foot)
        tone = (3.6 if sy > yb else 0.8 + 2.8 * d_) + rng.uniform(-0.9, 0.9)
        rpaint(a, m, STRAW, tone, rng.random())
    # a hay rack on the back wall: slats, hay pulled through them
    rk = (X >= x0 + 30) & (X < x0 + 64) & (Y >= back_foot - 24) & (Y < back_foot - 12)
    rpaint(a, rk, [('brass', 'brass_warm', 'sand_warm'), ('clay_cool', 'brass', 'brass_warm')], 2.4 + 1.0 * np.sin(X * 1.9 + Y * 0.8), nz)
    a[rk & (((X - x0) % 5) == 0)] = C('timber', 2)
    a[(Y == back_foot - 12) & (X >= x0 + 30) & (X < x0 + 64)] = C('timber', 3)
    a[(Y == back_foot - 25) & (X >= x0 + 29) & (X < x0 + 65)] = C('timber_warm', 4)
    # the roof: boards along the slope, the front edge lit, moss on the lower boards
    rt, rb = 4, 26
    rx0, rx1 = x0 - 4, x1 + 4
    roof = (X >= rx0) & (X < rx1) & (Y >= rt) & (Y < rb)
    rplank = (X - rx0) // 7
    f = (Y - rt) / (rb - rt)
    t = 3.8 - 1.4 * f + 0.5 * np.sin(rplank * 2.3) - 1.6 * (((X - rx0) % 7) == 6) + 0.8 * (((X - rx0) % 7) == 0)
    t = t + 1.4 * (nz - 0.5) - 0.8 * ((((Y * 3 + rplank * 5) % 11) == 0) & (((X - rx0) % 7) > 1))      # grain and knots
    rpaint(a, roof, [('timber_cool', 'timber', 'timber_warm'), ('earth_cool', 'timber', 'sand_warm'), ('timber_cool', 'earth_warm', 'timber_warm')],
           t, ((rplank * 5) % 3) / 3.0)
    a[roof & (nz > 0.74) & (f > 0.5)] = C('leaf_cool', 2)
    a[roof & (nz > 0.82) & (f > 0.5)] = C('leaf', 3)
    a[roof & (Y == rt)] = C('timber_warm', 5)
    a[(Y >= rb - 3) & (Y < rb) & (X >= rx0) & (X < rx1)] = C('timber', 2)        # the fascia
    a[(Y == rb - 3) & (X >= rx0) & (X < rx1)] = C('timber_warm', 4)
    for bx in range(rx0 + 3, rx1, 7):
        a[rb - 2, bx] = C('iron', 2)
    a[(Y >= rb) & (Y < rb + 3) & inside] = C('soot', 1)                            # deep shade under the eave
    # the end boards (the west lit, the east in shade) and the two square front posts: a lit west
    # face, a body, a shaded east side, a dark line where each stands in the ground
    V.prism(a, x0, rb, x0 + 5, yb, 1, 'timber', 3, side=1)
    V.prism(a, x1 - 5, rb, x1, yb, 1, 'timber_cool', 2, side=1)
    for px in (x0 + 2, x1 - 9):
        post = (X >= px) & (X < px + 7) & (Y >= rb - 1) & (Y < yb)
        tp = 3.0 + 1.6 * (X == px) + 0.6 * (X == px + 1) - 1.4 * (X >= px + 5) - 0.6 * (((Y - rb) % 9) == 0)
        rpaint(a, post, [('timber_cool', 'timber', 'timber_warm')], tp, 0)
        a[post & (X == px + 6)] = C('timber_cool', 0)
        a[yb - 1, px - 1:px + 8] = C('soot', 1)
        a[yb - 2, px - 1] = C('grass_cool', 2)
        a[yb - 3:yb - 1, px + 7] = C('grass', 3)
    a[yb - 1, x0:x1][a[yb - 1, x0:x1] >= 0] = np.minimum(a[yb - 1, x0:x1][a[yb - 1, x0:x1] >= 0], C('earth_cool', 1))
    V.finish(p)
    return p


# ------------------------------------------------------------------------------------------------
# hay
# ------------------------------------------------------------------------------------------------
STRAW = [('brass', 'brass_warm', 'sand_warm'), ('earth_warm', 'brass', 'brass_warm'), ('brass', 'sand_warm', 'sand')]


def bale(a, x0, y0, w, h, d, rng, east=True):
    """A compressed bale, rounded at its arrises: its top (d texels deep) lit and combed along its
    length, its south face the cut ends of the stalks (a stipple of light ends and dark holes), its
    east end turning into shade, two twines wrapping the volume over the top, down the front and
    round the end, loose wisps at the edges, a dark line where it rests."""
    Y, X = grid(a)
    nz = noise(a.shape, rng, 0.7)
    R = 3.0
    yt, yf, ye = y0, y0 + d, y0 + d + h
    box = (X >= x0) & (X < x0 + w) & (Y >= yt) & (Y < ye)
    cx0, cx1 = np.clip(X, x0 + R, x0 + w - 1 - R), None
    # rounded corners: distance to the inner box
    ix = np.clip(X, x0 + R, x0 + w - 1 - R)
    iy = np.clip(Y, yt + R, ye - 1 - R)
    box &= (X - ix) ** 2 + (Y - iy) ** 2 <= R * R
    top = box & (Y < yf)
    front = box & (Y >= yf)
    u = (X - x0) / max(1, w - 1)                                 # 0 west .. 1 east
    # the top: lit, combed along x, darker towards the east end and the far edge
    tt = 4.1 - 1.2 * np.clip(u - 0.65, 0, 1) * 3 - 0.6 * (Y == yt) + 0.8 * (Y == yf - 1) + 0.9 * (nz - 0.5)
    tt += 0.6 * (((Y + (X // 5)) % 3) == 0)
    rpaint(a, top, STRAW, tt, nz)
    # the cut face: stalk ends, a stipple of lit ends and dark holes, rounded into shade at the
    # foot and the east end
    ft = 3.0 + 0.6 * (Y == yf) - 1.0 * (Y >= ye - 2) - 1.3 * np.clip(u - 0.7, 0, 1) * 3 + 1.2 * (nz - 0.5)
    ends = (rng.random(a.shape) < 0.22)
    holes = (rng.random(a.shape) < 0.12)
    ft = ft + 1.2 * ends - 1.2 * holes
    rpaint(a, front, STRAW, ft, 1 - nz)
    a[front & (Y == yf)] = C('brass', 2)                         # the arris's shade under the lit top
    a[box & (Y == ye - 1)] = C('earth_cool', 1)                  # where it rests
    # two twines: over the top, down the front, a lit strand and its shade
    for tx in (x0 + w // 4, x0 + 3 * w // 4 - 1):
        tw = box & (X >= tx) & (X < tx + 2)
        a[tw] = C('clay_cool', 2)
        a[tw & (X == tx) & (Y < yf)] = C('clay', 4)
        a[tw & (X == tx) & (Y >= yf)] = C('clay', 3)
        a[box & (Y == yf - 1) & (X >= tx - 1) & (X < tx + 3)] = C('clay', 3)       # the twine bends over the arris
    # loose wisps at the top edge and the ends
    for _ in range(int(w / 3)):
        sx = rng.uniform(x0, x0 + w)
        sy = yt + rng.uniform(-0.5, 1.5)
        L = rng.uniform(2, 4)
        ang = rng.uniform(-2.6, -0.5)
        m = V.seg_mask(a.shape, sx, sy, sx + L * math.cos(ang), sy + L * math.sin(ang), 0.45) & ~box
        a[m] = C('sand_warm', 4) if rng.random() < 0.6 else C('brass_warm', 3)


def hay_bales(seed=0):
    """Three bales: two side by side, one across them on top (about 68 x 52 texels), with stalks
    fallen round their foot."""
    rng = np.random.default_rng(seed)
    p = canvas(82, 66, 41, 60)
    a = p.a
    bale(a, 6, 32, 34, 14, 12, rng)
    bale(a, 40, 32, 34, 14, 12, rng)
    bale(a, 20, 12, 38, 14, 12, rng)
    Y, X = grid(a)
    # the top bale's shade on the two below
    sh = (Y >= 38) & (Y < 40) & (X >= 22) & (X < 60) & (a >= 0)
    a[sh] = np.maximum(a[sh] - 1, (a[sh] // 8) * 8)
    for _ in range(24):
        x = rng.uniform(4, 78)
        V.bar(a, x, 59, x + rng.uniform(-5, 5), 59 - rng.uniform(0, 2), 0.5, 'brass_warm' if rng.random() < 0.5 else 'brass', 3)
    V.finish(p)
    return p


def hay_heap(seed=0):
    """Loose hay forked out for the stock (about 60 x 34 texels): a dome of tangled stalks laid in
    layers, the deep layer dark and the top layer lit on its upper left, a darker core where the
    stalks overhang it, stalks fallen round its foot."""
    rng = np.random.default_rng(seed)
    p = canvas(76, 48, 38, 42)
    a = p.a
    Y, X = grid(a)
    cx, cy, rx, ry = 38, 28, 29, 15
    rough = ndi.gaussian_filter(rng.random(a.shape), 1.2)
    m = (((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2 <= 1 + 1.6 * (rough - 0.5)) & (Y < 42)
    lit = sphere_light(X, Y, cx, cy, rx, ry)
    nz = noise(a.shape, rng, 0.9)
    rpaint(a, m, STRAW, 1.4 + 1.4 * lit + 1.4 * (nz - 0.5), nz)          # the dark core between the layers
    for layer, (n, base, fams) in enumerate(((140, 2.2, STRAW[1:2]), (150, 3.2, STRAW[:1]), (120, 4.2, STRAW[2:]))):
        for _ in range(n):
            x0, y0 = rng.uniform(cx - rx, cx + rx), rng.uniform(cy - ry, 41)
            ang = rng.uniform(-0.8, 0.8) + (math.pi if rng.random() < 0.5 else 0)
            L = rng.uniform(3, 8)
            s = V.seg_mask(a.shape, x0, y0, x0 + L * math.cos(ang), y0 + L * math.sin(ang), 0.45) & m
            if layer == 2:
                s &= lit > 0.0                                          # the top layer catches the light
            tone = base + 1.2 * lit + rng.uniform(-0.8, 0.8)
            rpaint(a, s, fams if rng.random() < 0.7 else STRAW, tone, rng.random())
    a[m & (Y >= 40)] = C('brass', 1)                                    # where it lies on the ground
    for _ in range(14):
        x = rng.uniform(cx - rx - 4, cx + rx + 4)
        V.bar(a, x, 42, x + rng.uniform(-6, 6), 42 - rng.uniform(0, 2), 0.5, 'brass', 3)
    V.finish(p)
    return p


# ------------------------------------------------------------------------------------------------
# the trough
# ------------------------------------------------------------------------------------------------
def trough(seed=0):
    """A stone stock trough (84 x 40 texels): its rim lit along the top and the west end, the inner
    north wall in shade above the water, the water dark in its depth and catching the sky in a
    pale streak and a glint near the south rim, the outer face of dressed stone in courses darker
    at the foot, mud trodden round its base and tufts of grass the hooves missed."""
    rng = np.random.default_rng(seed)
    p = canvas(96, 50, 48, 44)
    a = p.a
    Y, X = grid(a)
    nz = noise(a.shape, rng, 1.0)
    x0, x1 = 8, 88
    yt, yr, yb = 8, 28, 44                    # the rim's top, the front face's top, the foot
    # mud and trodden grass round the base (under everything else)
    mud = (((X - 48) / 42) ** 2 + ((Y - (yb - 2)) / 5.0) ** 2 <= 1 + 0.5 * (nz - 0.5)) & (Y >= yb - 6)
    rpaint(a, mud, [('earth_cool', 'earth', 'earth_warm'), ('soot', 'earth_cool', 'earth')], 1.6 + 1.2 * (nz - 0.3), nz)
    a[mud & (rng.random(a.shape) < 0.06)] = C('water_cool', 2)                     # a puddle's glint in a hoofprint
    for _ in range(8):
        tx = int(rng.uniform(x0 - 4, x1 + 4))
        for k in range(int(rng.integers(3, 6))):
            a[yb - 1 - k, tx + (k > 2)] = C('grass', 3 if k < 2 else 4)
        a[yb - 1, tx + 1] = C('grass_cool', 2)
    # the outer front face: dressed stone in two courses, lit west end, dark foot
    face = (X >= x0) & (X < x1) & (Y >= yr) & (Y < yb - 2)
    course = (Y - yr) // 6
    block = (X - x0 + 7 * (course % 2)) // 14
    tf = 3.0 + 0.5 * np.sin(block * 2.7 + course) - 1.2 * (((X - x0 + 7 * (course % 2)) % 14) == 13) \
        - 1.0 * (((Y - yr) % 6) == 5) - 0.9 * (Y >= yb - 4) + 0.9 * (X < x0 + 2) - 0.9 * (X > x1 - 4)
    rpaint(a, face, [('stone_cool', 'stone', 'stone_warm'), ('stone_cool', 'ashlar', 'ashlar_warm'), ('slate_cool', 'stone_warm', 'ashlar_warm')],
           tf + 0.9 * (nz - 0.5), np.mod((block * 2 + course) * 0.37, 1.0))
    chips = face & (rng.random(a.shape) < 0.04)
    a[chips] = C('stone_warm', 4)
    a[face & (nz > 0.78) & (Y > yb - 8)] = C('leaf_cool', 2)                       # moss at the damp foot
    # the rim: a lit top all round, the inner basin below it
    outer = (X >= x0) & (X < x1) & (Y >= yt) & (Y < yr)
    inner = (X >= x0 + 5) & (X < x1 - 5) & (Y >= yt + 3) & (Y < yr - 2)
    rim = outer & ~inner
    rpaint(a, rim, [('stone_cool', 'stone', 'stone_warm')], 4.0 + 0.8 * (Y == yt) + 0.6 * (X < x0 + 3) - 1.2 * (X > x1 - 4) - 1.0 * (Y >= yr - 2), 0)
    a[rim & (Y >= yr - 1)] = C('stone', 2)                                          # the front arris in shade
    # the inner north wall in shade, then the water: dark in its depth, a pale streak of sky and
    # a glint near the south rim, a ring where it meets the stone
    wallm = inner & (Y < yt + 6)
    rpaint(a, wallm, [('stone_cool', 'stone_cool', 'stone')], 1.4 + 0.5 * (Y - yt - 3) / 3, 0)
    water = inner & ~wallm
    dep = (Y - (yt + 6)) / max(1, (yr - 2) - (yt + 6))
    rpaint(a, water, [('water_cool', 'water', 'water_warm'), ('water_cool', 'water_cool', 'water'), ('dusk_cool', 'water_cool', 'sky')],
           1.0 + 2.0 * dep + 0.8 * (nz - 0.5), nz)
    a[water & (rng.random(a.shape) < 0.03) & (dep > 0.4)] = C('sky', 4)                 # ripples catching the sky
    a[water & (Y == yt + 6)] = C('water_cool', 0)
    streak = water & (np.abs(Y - (yr - 4)) < 0.6) & (X > x0 + 12) & (X < x0 + 40)
    a[streak] = C('sky', 4)
    a[water & (np.abs(Y - (yr - 5)) < 0.6) & (X > x0 + 48) & (X < x0 + 58)] = C('sky', 3)
    a[water & (Y == yr - 3) & ((X == x0 + 20) | (X == x0 + 21))] = C('snow', 5)
    V.finish(p)
    return p


# ------------------------------------------------------------------------------------------------
# the kitchen garden's beds
# ------------------------------------------------------------------------------------------------
CROPS = {'dug': ('cabbage', 'leek', 'lettuce'), 'dug_b': ('carrot', 'cabbage', 'beans')}


LEAF = [('leaf_cool', 'leaf', 'leaf_warm'), ('grass_cool', 'leaf', 'grass_warm'), ('leaf_cool', 'grass', 'leaf_warm')]
SOIL = [('earth_cool', 'earth', 'earth_warm'), ('path_cool', 'path', 'path_warm'), ('earth_cool', 'earth_warm', 'sand_warm')]
BURNT = [('soot', 'ash', 'ash'), ('stone_cool', 'ash', 'stone'), ('soot', 'earth_cool', 'earth'), ('slate_cool', 'stone_cool', 'ash')]


def _plant(a, crop, px, cy, rng, burnt=False, s=1.0, lean=0.0):
    """One plant on its ridge, sized `s` (0.7 .. 1.25: some came on faster) and leaning `lean`
    texels at its top, lit on its upper left with its shade east and down on the soil."""
    Y, X = grid(a)
    if burnt:
        # a charred stub: a dark stalk and a curl of black leaf, ash at its foot
        h = int(4 + 4 * s)
        a[V.seg_mask(a.shape, px, cy + 1, px + lean, cy - h, 0.7)] = C('soot', 1)
        a[V.seg_mask(a.shape, px - 0.4, cy + 1, px - 0.4 + lean, cy - h, 0.3)] = C('soot', 3)
        cm = ((X - px - lean - 1.5) / (2.0 + 1.5 * s)) ** 2 + ((Y - cy + h) / 1.5) ** 2 <= 1
        a[cm] = C('soot', 0 if rng.random() < 0.5 else 2)
        a[cm & (X < px + lean + 1) & (Y < cy - h)] = C('soot', 4)                    # a charred leaf's lit curl
        a[int(cy + 1), int(px - 2):int(px + 3)] = C('ash', 4)
        a[int(cy + 2), int(px - 1):int(px + 3)] = C('earth_cool', 1)
        if rng.random() < 0.25:
            a[int(cy), int(px + 1)] = C('lava', 3)                                   # an ember still glowing
        return
    mix = rng.random()
    if crop == 'cabbage':
        rx_, ry_ = 5.6 * s, 4.4 * s
        m = ((X - px) / rx_) ** 2 + ((Y - cy) / ry_) ** 2 <= 1 + 0.18 * np.sin(np.arctan2(Y - cy, X - px) * 6 + mix * 6)
        rpaint(a, m, LEAF, 2.6 + 1.7 * sphere_light(X, Y, px, cy, rx_, ry_), mix)
        heart = ((X - px + 0.5 - lean * 0.3) / (2.8 * s)) ** 2 + ((Y - cy + 0.8) / (2.2 * s)) ** 2 <= 1
        rpaint(a, heart, [('leaf', 'leaf_warm', 'grass_warm')], 4.0 + sphere_light(X, Y, px, cy - 1, 3, 2), 0)
        for k in range(4):                                     # the outer leaves' veins
            ang = k * math.pi / 2 + 0.6 + mix
            a[V.seg_mask(a.shape, px, cy, px + 4.5 * s * math.cos(ang), cy + 3.5 * s * math.sin(ang), 0.4) & m & ~heart] = C('leaf_cool', 2)
    elif crop == 'lettuce':
        rx_, ry_ = 4.2 * s, 3.4 * s
        m = ((X - px) / rx_) ** 2 + ((Y - cy) / ry_) ** 2 <= 1 + 0.25 * np.sin(np.arctan2(Y - cy, X - px) * 7 + mix * 5)
        rpaint(a, m, [('leaf', 'grass_warm', 'grass_warm'), ('grass', 'grass_warm', 'leaf_warm')], 3.0 + 1.6 * sphere_light(X, Y, px, cy, rx_, ry_), mix)
        a[m & (((X - px) ** 2 + (Y - cy) ** 2) < 1.2)] = C('grass_warm', 5)
    elif crop == 'leek':
        for dx, h, t in ((-1.5, 9, 3), (0.5, 11, 4), (2.0, 8, 2)):
            a[V.seg_mask(a.shape, px + dx * 0.3, cy + 1, px + dx + lean, cy + 1 - h * s, 0.8)] = C('leaf_cool', t)
        a[V.seg_mask(a.shape, px + 0.5, cy, px + 0.5 + lean, cy - 9 * s, 0.4)] = C('leaf', 4)
        a[int(cy - 1):int(cy + 2), int(px - 1):int(px + 2)] = C('plaster', 4)       # the white shank
        a[int(cy + 1), int(px - 1):int(px + 2)] = C('plaster_warm', 3)
    elif crop == 'carrot':
        for dx in (-2, 0, 2):
            a[V.seg_mask(a.shape, px, cy + 1, px + dx * s + lean, cy - (6 - abs(dx)) * s, 0.6)] = C('grass', 4 if dx < 1 else 3)
        fm = ((X - px - lean) / (3.0 * s)) ** 2 + ((Y - cy + 5 * s) / (2.0 * s)) ** 2 <= 1
        rpaint(a, fm, [('grass', 'grass_warm', 'leaf_warm')], 3.4 + 1.2 * sphere_light(X, Y, px, cy - 5, 3, 2), 0)
        a[int(cy + 1), int(px - 1):int(px + 2)] = C('clay', 4)                      # the shoulder
        a[int(cy + 1), int(px + 1)] = C('clay', 3)
    elif crop == 'beans':
        a[V.seg_mask(a.shape, px, cy + 1, px + lean, cy - 18 * s, 0.7)] = C('timber', 3)        # the cane
        a[V.seg_mask(a.shape, px - 0.5, cy + 1, px - 0.5 + lean, cy - 18 * s, 0.3)] = C('timber_warm', 4)
        for k in range(5):
            ly = cy - 3 - k * 3 * s
            lx = px + lean * (k / 5) + (2 if k % 2 else -2)
            lm = ((X - lx) / 2.0) ** 2 + ((Y - ly) / 1.5) ** 2 <= 1
            rpaint(a, lm, LEAF, 3.6 if k % 2 == 0 else 2.6, mix)
        a[int(cy - 9 * s), int(px + 2)] = C('berry', 4)                                # a flower
    # the plant's shade on the soil, east and down
    sh = ((X - px - 2.5 * s) / (4.0 * s)) ** 2 + ((Y - cy - 3.5 * s) / 1.4) ** 2 <= 1
    soil_f = [FI[f] for f in ('earth', 'earth_warm', 'path', 'path_warm', 'sand_warm')]
    a[sh & np.isin(a // 8, soil_f)] = C('earth_cool', 1)


def beds(kind='dug', seed=0):
    """A kitchen garden's beds in a dug patch (240 x 120 texels, ten cells by five): three soil
    ridges east to west with a trodden furrow between them, each ridge's crest catching the light
    and the furrow under it in shade, crumbs of soil and clods lit on their upper left, a row of
    one crop on each ridge, the plants of a row each its own size and lean with a gap where one
    failed; the patch's edge dug ragged into the turf, the grass hanging over it. `scorched`: the
    same ground burnt grey, the crops black stubs, ash drifted in the furrows, a few green shoots
    coming back."""
    burnt = kind == 'scorched'
    rng = np.random.default_rng(seed)
    W, H = 252, 136
    p = canvas(W, H, W // 2, H - 6)
    a = p.a
    Y, X = grid(a)
    x0, x1, y0, y1 = 8, W - 8, 10, H - 6
    nz = ndi.gaussian_filter(rng.random(a.shape), 2.5)
    nz = (nz - nz.mean()) / max(1e-6, nz.std())
    fine = noise(a.shape, rng, 0.8)
    d = np.minimum.reduce([X - x0, x1 - X, Y - y0, y1 - Y])
    patch = d + 2.2 * nz > 2
    sets = BURNT if burnt else SOIL
    rpaint(a, patch, sets, (2.0 if burnt else 2.2) + 0.5 * nz + 1.2 * (fine - 0.5), fine)
    # the edge: no outline; the soil a step darker where the spade cut the turf, broken by grass
    # blades hanging over it from the lawn
    edge = patch & ~ndi.binary_erosion(patch, iterations=2)
    darker = edge & (rng.random(a.shape) < 0.6)
    a[darker] = np.maximum(a[darker] - 1, (a[darker] // 8) * 8)
    ey, ex = np.nonzero(edge & (rng.random(a.shape) < 0.07))
    for y_, x_ in zip(ey, ex):
        L = int(rng.integers(2, 5))
        for k in range(L):
            yy, xx = y_ - k if y_ > H / 2 else y_ + k - 1, x_ + (k // 2) * (1 if rng.random() < 0.5 else -1)
            if 0 <= yy < H and 0 <= xx < W:
                a[yy, xx] = C('grass', 3 if k else 2) if not burnt else C('ash', 3)
    rows = 3
    pitch = (y1 - y0 - 12) / rows
    crops = CROPS.get(kind, CROPS['dug'])
    for r in range(rows):
        ry0 = y0 + 8 + r * pitch
        ry1 = ry0 + pitch - 9
        rr = 4.0
        ridge = (np.abs(X - (x0 + x1) / 2) <= (x1 - x0) / 2 - 10 + 3 * nz) & (Y >= ry0) & (Y < ry1)
        ridge &= ~((X < x0 + 14) & (Y < ry0 + rr) & ((X - x0 - 14) ** 2 + (Y - ry0 - rr) ** 2 > rr * rr))
        fr = (Y - ry0) / max(1, ry1 - ry0)
        t = 3.4 - 1.2 * fr + 0.35 * nz - 0.9 * (Y >= ry1 - 3) - 0.6 * (X > x1 - 16) + 1.0 * (fine - 0.5)
        rpaint(a, ridge, [('soot', 'ash', 'ash'), ('stone_cool', 'ash', 'stone')] if burnt else SOIL, t - (0.4 if burnt else 0), fine)
        # the crest catching the light, the furrow under the ridge in shade
        crest = ridge & (Y < ry0 + 2) & (fine > 0.25)
        a[crest] = C('ash', 4) if burnt else C('earth_warm', 4)
        a[crest & (fine > 0.7)] = C('stone', 4) if burnt else C('sand_warm', 4)
        furrow = patch & ~ridge & (Y >= ry1) & (Y < ry1 + 4)
        a[furrow] = C('soot', 1) if burnt else np.where(fine[furrow] > 0.5, C('earth_cool', 1), C('path_cool', 1))
        for _ in range(int((x1 - x0) * pitch / 12)):            # clods, lit on their upper left
            cx_, cy_ = int(rng.uniform(x0 + 12, x1 - 12)), int(rng.uniform(ry0 + 2, ry1 - 3))
            if ridge[cy_, cx_]:
                a[cy_, cx_:cx_ + 2] = C('earth_warm' if not burnt else 'ash', 4 + (rng.random() < 0.3))
                a[cy_ + 1, cx_ + 1:cx_ + 3] = C('earth_cool' if not burnt else 'soot', 1)
        crop = crops[r % len(crops)]
        step = {'cabbage': 15, 'lettuce': 11, 'leek': 8, 'carrot': 8, 'beans': 14}[crop]
        cy = ry0 + (ry1 - ry0) * 0.5
        n = int((x1 - x0 - 32) // step)
        for i in range(n + 1):
            px = x0 + 16 + (x1 - x0 - 32) * i / max(1, n) + rng.uniform(-1.5, 1.5)
            if rng.random() < (0.35 if burnt else 0.1):
                continue                                       # a gap: one that failed (or the storm took)
            _plant(a, crop, px, cy + rng.uniform(-1, 1), rng, burnt=burnt, s=rng.uniform(0.72, 1.22), lean=rng.uniform(-1.6, 1.6))
        if burnt:
            for _ in range(4):                                 # green coming back
                sx = int(rng.uniform(x0 + 20, x1 - 20))
                a[int(cy + 2):int(cy + 5), sx] = C('grass', 4)
                a[int(cy + 2), sx - 1:sx + 2] = C('grass_warm', 4)
    if burnt:
        # ash drifted along the furrows and in hollows, pale where it lies thickest
        drift = patch & (ndi.gaussian_filter(rng.random(a.shape), 1.5) > 0.6) & (nz < 0.3)
        a[drift & (a // 8 != FI['soot'])] = C('ash', 4)
        a[drift & (fine > 0.8) & (a // 8 != FI['soot'])] = C('ash', 5)
        a[drift & (fine < 0.15) & (a // 8 != FI['soot'])] = C('snow_cool', 2)
        # where the fire passed quickly the soil is only browned: patches of it showing through
        brown = patch & (nz > 0.9) & (a // 8 != FI['soot'])
        rpaint(a, brown, SOIL[:2], 1.4 + 1.6 * (fine - 0.3), fine)
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
        # each ewe keeps her own rhythm, as the hens do: the loop starts at a different beat
        shift = {'stand': 0, 'graze': 3, 'lie': 5}[pose]
        frames = frames[shift:] + frames[:shift]
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
            collision={'shape': 'rect', 'rect': [-8.0, -4.0, 16, 4]}, shadow=(18, 4),
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
        'crossroads_trough': [('trough', trough(seed=71))],
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
    'crossroads_trough': [-13.0, -8.0, 26, 8],          # the redrawn trough is 27 wide (was 20 under a 27 wide picture)
}
REDRAWN = ('crossroads_beds_dug', 'crossroads_beds_scorched', 'crossroads_hay', 'crossroads_trough')


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
